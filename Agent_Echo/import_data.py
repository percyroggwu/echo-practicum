"""Load Echo's public prototype datasets into a validated SQLite database.

--profile legacy (default) loads the eleven files_update datasets into data/echo.db.
--profile discovery_v1 loads the manifest's discovery_v1 pack into data/echo_discovery_v1.db.
Uses Python's standard library. Private QA datasets are never imported.
"""
import argparse
import csv
from datetime import date, datetime
import itertools
from pathlib import Path
import re
import sqlite3
import sys
import uuid


HERE = Path(__file__).resolve().parent
FILES = (
    'HR_managers.csv',
    'HR_employees.csv',
    'OP_projects.csv',
    'OP_work_requests.csv',
    'OP_capacity.csv',
    'OP_priority_decisions.csv',
    'OP_contributions.csv',
    'HR_recognition_feedback.csv',
    'HR_survey_summary.csv',
    'HR_survey_comments.csv',
    'HR_program_participation.csv',
)
INTEGER_COLUMNS = {
    'Employees_In_Original_Source', 'Pilot_Assigned_Employees',
    'Eligible_Employees', 'Responses', 'Scale_Min', 'Scale_Max',
    'Favorable_Responses', 'Promoters', 'Passives', 'Detractors',
    'Response_Score', 'Use_Count', 'Usefulness_Score',
}
REAL_COLUMNS = {
    'Favorable_Percent', 'Mean_Score', 'eNPS_Score', 'Participation_Hours',
    'Scheduled_Hours', 'Leave_Hours', 'Routine_Hours', 'Available_Project_Hours',
    'Original_Estimated_Hours', 'Current_Estimated_Hours', 'Actual_Hours',
    'Rework_Hours', 'Previous_Estimated_Hours', 'Revised_Estimated_Hours',
}
LEGACY_DATABASE = HERE / 'data' / 'echo.db'
TIMESTAMP_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?')
# Anchor rules are read from the dictionary Meaning, e.g. "Exactly one of A, B and C is filled".
RULE_PATTERN = re.compile(r'(exactly one|at least one|at most one) of ([\w, ]+?) is filled', re.IGNORECASE)


def default_paths(profile):
    if profile == 'discovery_v1':
        return HERE.parent / 'files_discovery_v1', HERE / 'data' / 'echo_discovery_v1.db'
    return HERE.parent / 'files_update', LEGACY_DATABASE


def quote_identifier(name):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        raise ValueError(f'Unsupported database identifier: {name!r}')
    return '"' + name + '"'


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def column_type(column):
    return 'INTEGER' if column in INTEGER_COLUMNS else 'REAL' if column in REAL_COLUMNS else 'TEXT'


def is_id_list(definition):
    """A ';'-separated list of IDs: each entry is checked, but SQLite cannot declare it as a foreign key."""
    return ';-separated' in definition.get('Meaning', '')


def load_order(schemas):
    order = []

    def visit(filename, path=()):
        if filename in order:
            return
        if filename in path:
            raise ValueError(f'Circular references involving {filename}')
        columns, definitions, _ = schemas[filename]
        for column in columns:
            if definitions[column]['References']:
                visit(definitions[column]['References'].rsplit('.', 1)[0], path + (filename,))
        order.append(filename)

    for filename in schemas:
        visit(filename)
    return {filename: schemas[filename] for filename in order}


def prepare_schema(source, discovery=False):
    rows = read_csv(source / 'QA_manifest.csv')
    if discovery:
        manifest = {row['File']: row for row in rows
                    if row.get('Profile') == 'discovery_v1' and row['Load_Into_Prototype'] == 'Yes'}
        files = tuple(manifest)
        if not files:
            raise ValueError('The manifest lists no discovery_v1 files to load.')
    else:
        manifest = {row['File']: row for row in rows}
        allowed = {name for name, row in manifest.items() if row['Load_Into_Prototype'] == 'Yes'}
        if allowed != set(FILES):
            raise ValueError('Manifest application files differ from the eleven approved datasets.')
        files = FILES
    definitions = {}
    for row in read_csv(source / 'QA_data_dictionary.csv'):
        if row['File'] in files:
            if discovery and row['Type'] not in ('TEXT', 'INTEGER', 'REAL', 'DATE', 'TIMESTAMP'):
                raise ValueError(f'Unsupported type in the dictionary: {row["File"]}.{row["Column"]}')
            definitions.setdefault(row['File'], {})[row['Column']] = row
    schemas = {}
    for filename in files:
        with (source / filename).open(encoding='utf-8-sig', newline='') as stream:
            columns = next(csv.reader(stream))
        if discovery:  # the dictionary order is the header order
            matches = columns == list(definitions.get(filename, {}))
        else:
            matches = set(columns) == set(definitions.get(filename, {})) and len(columns) == len(set(columns))
        if not matches:
            raise ValueError(f'CSV headers do not match the dictionary: {filename}')
        key = manifest[filename]['Primary_Key']
        if [col for col in columns if definitions[filename][col]['Primary_Key'] == 'Yes'] != [key]:
            raise ValueError(f'Primary key definition does not match: {filename}')
        clauses = []
        for column in columns:
            definition = definitions[filename][column]
            sql_type = (definition['Type'] if definition['Type'] in ('INTEGER', 'REAL') else 'TEXT') if discovery else column_type(column)
            clause = f'{quote_identifier(column)} {sql_type}'
            if definition['Nullable'] == 'No' or column == key:
                clause += ' NOT NULL'
            if column == key:
                clause += ' PRIMARY KEY'
            if definition['References']:
                target_file, target_column = definition['References'].rsplit('.', 1)
                if target_file not in files or target_column not in definitions[target_file]:
                    raise ValueError(f'Unapproved foreign-key target in {filename}.{column}')
                if not (discovery and is_id_list(definition)):
                    clause += f' REFERENCES {quote_identifier(Path(target_file).stem)} ({quote_identifier(target_column)})'
            clauses.append(clause)
        schemas[filename] = (columns, definitions[filename], clauses)
    return manifest, (load_order(schemas) if discovery else schemas)


def converted_rows(reader, filename, columns, definitions):
    for line_number, row in enumerate(reader, start=2):
        if None in row or any(row.get(col) is None for col in columns):
            raise ValueError(f'Invalid CSV row width in {filename}, line {line_number}')
        values = []
        for column in columns:
            value = row[column]
            if value == '':
                if definitions[column]['Nullable'] != 'Yes':
                    raise ValueError(f'Missing required field in {filename}, line {line_number}: {column}')
                values.append(None)
                continue
            try:
                if column in INTEGER_COLUMNS:
                    value = int(value)
                elif column in REAL_COLUMNS:
                    value = float(value)
                elif column.endswith('_Date') or column == 'Week_Start':
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError('Date is not ISO formatted')
            except ValueError:
                raise ValueError(f'Invalid value in {filename}, line {line_number}: {column}') from None
            values.append(value)
        yield tuple(values)


def moment(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def invalid(filename, line_number, column, reason):
    raise ValueError(f'Invalid value in {filename}, line {line_number}: {column} ({reason})')


def share_problem(row):
    """Return (column, reason) when a feedback row breaks the share-date rules."""
    shared, recorded = row['Shared_With_Home_Manager_At'], row['Share_Recorded_At']
    if bool(shared) != bool(recorded):
        return 'Share_Recorded_At', 'must be blank exactly when Shared_With_Home_Manager_At is blank'
    if row['Shared_With_Home_Manager'] != ('Yes' if shared else 'No'):
        return 'Shared_With_Home_Manager', 'disagrees with Shared_With_Home_Manager_At'
    if shared and moment(shared) < moment(row['Interaction_At']):
        return 'Shared_With_Home_Manager_At', 'earlier than Interaction_At'
    if shared and moment(recorded) < moment(shared):
        return 'Share_Recorded_At', 'earlier than Shared_With_Home_Manager_At'


def discovery_rows(reader, filename, columns, definitions):
    rules = set()
    for definition in definitions.values():
        for kind, names in RULE_PATTERN.findall(definition['Meaning']):
            names = tuple(re.split(r',\s*|\s+and\s+', names.strip()))
            if not set(names) <= set(columns):
                raise ValueError(f'Dictionary rule names an unknown column in {filename}: {names}')
            rules.add((kind.lower(), names))
    key = next(column for column in columns if definitions[column]['Primary_Key'] == 'Yes')
    seen = set()
    for line_number, row in enumerate(reader, start=2):
        if None in row or any(row.get(col) is None for col in columns):
            raise ValueError(f'Invalid CSV row width in {filename}, line {line_number}')
        values = []
        for column in columns:
            value, definition = row[column], definitions[column]
            if value == '':
                if definition['Nullable'] != 'Yes':
                    raise ValueError(f'Missing required field in {filename}, line {line_number}: {column}')
                values.append(None)
                continue
            try:
                if definition['Type'] == 'INTEGER':
                    value = int(value)
                elif definition['Type'] == 'REAL':
                    value = float(value)
                elif definition['Type'] == 'DATE':
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError
                elif definition['Type'] == 'TIMESTAMP':
                    if not TIMESTAMP_PATTERN.fullmatch(value):
                        raise ValueError
                    moment(value)
            except ValueError:
                invalid(filename, line_number, column, f'not a valid {definition["Type"]}')
            if definition['Allowed_Values'] and row[column] not in definition['Allowed_Values'].split('|'):
                invalid(filename, line_number, column, 'not an allowed value')
            values.append(value)
        if row[key] in seen:
            invalid(filename, line_number, key, 'duplicate primary key')
        seen.add(row[key])
        for kind, names in rules:
            filled = sum(1 for name in names if row[name])
            if not {'exactly one': filled == 1, 'at least one': filled >= 1, 'at most one': filled <= 1}[kind]:
                invalid(filename, line_number, names[0], f'{kind} of {", ".join(names)} must be filled')
        if filename == 'HR_recognition_feedback.csv':
            try:
                problem = share_problem(row)
            except TypeError:
                problem = ('Shared_With_Home_Manager_At', 'mixes timestamps with and without a time zone')
            if problem:
                invalid(filename, line_number, *problem)
        yield tuple(values)


def build_database(source, output, replace=False, profile='legacy'):
    discovery = profile == 'discovery_v1'
    if discovery and output.resolve() == LEGACY_DATABASE.resolve():
        raise ValueError('The discovery_v1 profile never writes data/echo.db; choose another --output.')
    if output.exists() and not replace:
        raise FileExistsError('The database already exists. Use --replace to rebuild it explicitly.')
    manifest, schemas = prepare_schema(source, discovery)
    files = tuple(schemas)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f'{output.stem}.build-{uuid.uuid4().hex}.db')
    connection = None
    counts = {}
    try:
        connection = sqlite3.connect(temporary)
        # discovery_v1 checks references itself below, so errors can name file, line and column.
        connection.execute(f'PRAGMA foreign_keys = {"OFF" if discovery else "ON"}')
        connection.execute('BEGIN')
        for filename in files:
            columns, definitions, clauses = schemas[filename]
            table = Path(filename).stem
            connection.execute(f'CREATE TABLE {quote_identifier(table)} ({", ".join(clauses)})')
            sql = f'INSERT INTO {quote_identifier(table)} ({", ".join(map(quote_identifier, columns))}) VALUES ({", ".join("?" for _ in columns)})'
            count = 0
            with (source / filename).open(encoding='utf-8-sig', newline='') as stream:
                rows = (discovery_rows if discovery else converted_rows)(csv.DictReader(stream), filename, columns, definitions)
                while batch := list(itertools.islice(rows, 2000)):
                    connection.executemany(sql, batch)
                    count += len(batch)
            if discovery and not count:
                raise ValueError(f'No rows in {filename}')
            if not discovery and count != int(manifest[filename]['Rows']):
                raise ValueError(f'Row count differs from the manifest: {filename}')
            counts[table] = count
            note = f' (manifest: {manifest[filename]["Rows"]})' if discovery else ''
            print(f'{table}: {count:,} rows{note}', flush=True)
        if discovery:
            for filename, (columns, definitions, _) in schemas.items():
                for column in columns:
                    reference = definitions[column]['References']
                    if reference and is_id_list(definitions[column]):
                        target_file, target_column = reference.rsplit('.', 1)
                        known = {value for (value,) in connection.execute(
                            f'SELECT {quote_identifier(target_column)} FROM {quote_identifier(Path(target_file).stem)}')}
                        for rowid, value in connection.execute(
                                f'SELECT rowid, {quote_identifier(column)} FROM {quote_identifier(Path(filename).stem)} '
                                f'WHERE {quote_identifier(column)} IS NOT NULL'):
                            unknown = [item for item in value.split(';') if item and item not in known]
                            if unknown:
                                raise ValueError(f'Unknown reference in {filename}, line {rowid + 1}: {column} entry {unknown[0]!r} is not in {reference}')
                    elif reference:
                        target_file, target_column = reference.rsplit('.', 1)
                        bad = connection.execute(
                            f'SELECT rowid, {quote_identifier(column)} FROM {quote_identifier(Path(filename).stem)} '
                            f'WHERE {quote_identifier(column)} IS NOT NULL AND {quote_identifier(column)} NOT IN '
                            f'(SELECT {quote_identifier(target_column)} FROM {quote_identifier(Path(target_file).stem)}) LIMIT 1').fetchone()
                        if bad:
                            raise ValueError(f'Unknown reference in {filename}, line {bad[0] + 1}: {column} = {bad[1]!r} is not in {reference}')
        for filename, (columns, definitions, _) in schemas.items():
            table = Path(filename).stem
            for column in columns:
                if (definitions[column]['References'] and not (discovery and is_id_list(definitions[column]))) or (discovery and (
                        definitions[column]['Type'] in ('DATE', 'TIMESTAMP') or column == 'Quarter')):
                    index = f'idx_{table}_{column}'
                    connection.execute(f'CREATE INDEX {quote_identifier(index)} ON {quote_identifier(table)} ({quote_identifier(column)})')
        for table, columns in ({} if discovery else {
            'HR_survey_summary': ('Team', 'Survey_Date'),
            'HR_program_participation': ('Team', 'Period_Start_Date'),
            'HR_recognition_feedback': ('Employee_ID', 'Interaction_Date'),
            'OP_capacity': ('Employee_ID', 'Week_Start'),
            'OP_contributions': ('Employee_ID', 'Contribution_Date'),
            'OP_work_requests': ('Assigned_Employee_ID', 'Week_Start'),
        }).items():
            connection.execute(f'CREATE INDEX {quote_identifier("idx_" + table + "_period")} ON {quote_identifier(table)} ({", ".join(map(quote_identifier, columns))})')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Database foreign-key validation failed.')
        connection.commit()
        if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('SQLite integrity validation failed.')
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if tables != {Path(name).stem for name in files}:
            raise ValueError('Database contains an unexpected table.')
        if any(connection.execute(f'SELECT COUNT(*) FROM {quote_identifier(table)}').fetchone()[0] != count for table, count in counts.items()):
            raise ValueError('Saved table counts do not match imported rows.')
        connection.close()
        connection = None
        temporary.replace(output)
    except Exception:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)
        temporary.with_name(temporary.name + '-journal').unlink(missing_ok=True)
        raise
    print(f'Imported {sum(counts.values()):,} rows into {output}', flush=True)
    if discovery:
        print(f'Validation: {len(files)} tables, valid values and anchors, valid references, SQLite integrity OK.')
    else:
        print('Validation: eleven tables, matching row counts, valid references, SQLite integrity OK.')
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('legacy', 'discovery_v1'), default='legacy')
    parser.add_argument('--source', type=Path, help='Default: files_update (legacy) or files_discovery_v1.')
    parser.add_argument('--database', '--output', dest='database', type=Path,
                        help='Default: data/echo.db (legacy) or data/echo_discovery_v1.db.')
    parser.add_argument('--replace', action='store_true', help='Replace an existing database only after the new import validates.')
    args = parser.parse_args()
    try:
        source, database = default_paths(args.profile)
        build_database((args.source or source).resolve(), (args.database or database).resolve(), args.replace, args.profile)
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f'Import failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
