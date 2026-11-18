"""Build a separate, offline Discovery lookup index from a read-only source database.

Every indexed row carries both event and recorded dates. Consumers must apply
both date bounds for their as-of query; this index deliberately keeps future rows.
"""
import argparse
from contextlib import closing
import os
from pathlib import Path
import re
import sqlite3
import unicodedata
import uuid

HERE = Path(__file__).resolve().parent.parent
ANCHORS = ('Contribution_ID', 'Thread_ID', 'Blocker_ID', 'Incident_ID')
TEXT_SOURCES = {
    'HR_recognition_feedback': ('Interaction_ID', 'Interaction_At', 'Message', None),
    'OP_collab_messages': ('Message_ID', 'Sent_At', 'Message_Text', 'Mentioned_Employee_IDs'),
    'OP_meeting_mentions': ('Mention_ID', 'Meeting_Date', 'Note_Text', 'Mentioned_Employee_ID'),
    'HR_self_review_items': ('Item_ID', 'Submitted_Date', 'Item_Text', None),
    'OP_team_plans': ('Team_Plan_ID', 'Plan_Date', 'Item_Text', None),
    'HR_review_notes': ('Review_Note_ID', 'Note_Date', 'Note_Text', None),
    'HR_recognition_events': ('Recognition_ID', 'Recognized_At', 'Citation_Text', None),
}


def _normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold())
                   if not unicodedata.combining(c))


def _quarter(value):
    if not value:
        return None
    return f'{value[:4]}-Q{(int(value[5:7]) - 1) // 3 + 1}'


def build_discovery_index(source_db, index_db):
    """Atomically build an index; source and protected legacy data remain unchanged."""
    source, output = Path(source_db).resolve(), Path(index_db).resolve()
    protected = (HERE / 'data' / 'echo.db').resolve()
    protected_dirs = [(HERE.parent / name).resolve() for name in
                      ('files_update', 'data_extensions', 'files_discovery_v1', 'files_discovery_v1_private')]
    if any(output == directory or directory in output.parents for directory in protected_dirs):
        raise ValueError('The index cannot be written inside a protected data directory.')
    protected_files = (source, protected, (HERE / 'data' / 'echo_discovery_v1.db').resolve())
    if output in protected_files or (output.exists() and any(
            path.exists() and os.path.samefile(output, path) for path in protected_files)):
        raise ValueError('The index must be separate from the source and legacy databases.')
    if source.name.lower() in ('.env', 'connections.private.json'):
        raise ValueError('Credentials cannot be used as a runtime source.')
    if (HERE.parent / 'files_discovery_v1_private').resolve() in source.parents:
        raise ValueError('Private QA data cannot be used as a runtime source.')
    if not source.is_file():
        raise FileNotFoundError(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f'{output.name}.build-{uuid.uuid4().hex}')
    try:
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src, closing(sqlite3.connect(temporary)) as dst:
            src.row_factory = sqlite3.Row
            dst.executescript('''
                CREATE TABLE visibility_events (source_table TEXT NOT NULL, source_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL, event_type TEXT NOT NULL, event_date TEXT NOT NULL, recorded_date TEXT NOT NULL, quarter TEXT NOT NULL);
                CREATE INDEX visibility_lookup ON visibility_events(employee_id, event_date, recorded_date);
                CREATE TABLE visibility_event_anchors (source_table TEXT NOT NULL, source_id TEXT NOT NULL, event_type TEXT NOT NULL, anchor_type TEXT NOT NULL, anchor_id TEXT NOT NULL, event_date TEXT NOT NULL, recorded_date TEXT NOT NULL, quarter TEXT NOT NULL);
                CREATE INDEX visibility_anchor_lookup ON visibility_event_anchors(anchor_type, anchor_id);
                CREATE TABLE name_mentions (source_table TEXT NOT NULL, source_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL, event_date TEXT NOT NULL, recorded_date TEXT NOT NULL,
                    quarter TEXT NOT NULL, match_type TEXT NOT NULL,
                    PRIMARY KEY(source_table, source_id, employee_id, match_type));
                CREATE INDEX mention_lookup ON name_mentions(employee_id, event_date, recorded_date);
                CREATE TABLE quarter_keys (source_table TEXT NOT NULL, source_id TEXT NOT NULL,
                    event_date TEXT NOT NULL, recorded_date TEXT NOT NULL, quarter TEXT NOT NULL);
                CREATE INDEX quarter_lookup ON quarter_keys(source_table, quarter, event_date, recorded_date);
            ''')
            for table, key, date, kind in (
                ('HR_recognition_feedback', 'Interaction_ID', 'Interaction_At', 'praised'),
                ('HR_recognition_events', 'Recognition_ID', 'Recognized_At', 'recognized'),
            ):
                for row in src.execute(f'SELECT * FROM {table}'):
                    anchors = [(a.removesuffix('_ID').lower(), row[a]) for a in ANCHORS if row[a]]
                    recorded = row['Recorded_At'] if 'Recorded_At' in row.keys() else row[date]
                    events = [(kind, row[date], recorded)]
                    if table == 'HR_recognition_feedback' and row['Shared_With_Home_Manager_At']:
                        events.append(('shared', row['Shared_With_Home_Manager_At'], row['Share_Recorded_At']))
                    for event_type, event_date, recorded in events:
                        if not recorded:
                            raise ValueError(f'Missing recorded date: {table} {row[key]}')
                        dst.execute('INSERT INTO visibility_events VALUES (?,?,?,?,?,?,?)',
                                    (table, row[key], row['Employee_ID'], event_type, event_date, recorded, _quarter(event_date)))
                        dst.executemany('INSERT INTO visibility_event_anchors VALUES (?,?,?,?,?,?,?,?)',
                                        ((table, row[key], event_type, anchor_type, anchor_id, event_date, recorded, _quarter(event_date))
                                         for anchor_type, anchor_id in anchors))
            names = {}
            for row in src.execute('SELECT Employee_ID, Employee_Name FROM HR_employees'):
                name = _normalize(row['Employee_Name']).strip()
                if name:
                    names.setdefault(name, []).append(row['Employee_ID'])
            by_first = {}
            for name in names:
                first = re.match(r'\w+', name)
                if first:
                    by_first.setdefault(first.group(), []).append(name)
            patterns = {first: re.compile(r'(?:' + '|'.join(re.escape(n) for n in sorted(group, key=len, reverse=True)) + r')(?!\w)')
                        for first, group in by_first.items()}
            for table, (key, date, column, ids) in TEXT_SOURCES.items():
                for row in src.execute(f'SELECT * FROM {table}'):
                    event_date = row[date]
                    if not event_date:
                        continue
                    recorded = row['Recorded_At'] if 'Recorded_At' in row.keys() else event_date
                    if not recorded:
                        raise ValueError(f'Missing recorded date: {table} {row[key]}')
                    found = set()
                    if ids and row[ids]:
                        found.update((employee.strip(), 'id') for employee in row[ids].split(';') if employee.strip())
                    if row[column]:
                        normalized = _normalize(row[column])
                        for token in re.finditer(r'\w+', normalized):
                            pattern = patterns.get(token.group())
                            match = pattern.match(normalized, token.start()) if pattern else None
                            if match:
                                found.update((employee, 'name') for employee in names[match.group()])
                    dst.executemany('INSERT OR IGNORE INTO name_mentions VALUES (?,?,?,?,?,?,?)',
                                    ((table, row[key], employee, event_date, recorded, _quarter(event_date), kind)
                                     for employee, kind in found))
            # Index each source row with its declared calendar date (or recorded date when
            # that is the only timestamp); retain quarter-only records with their recorded date.
            for table_row in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
                table = table_row['name']
                columns = src.execute(f'PRAGMA table_info("{table}")').fetchall()
                key = next((r['name'] for r in columns if r['pk']), None)
                cols = {r['name'] for r in columns}
                dates = [r['name'] for r in columns if r['name'].endswith(('_Date', '_At'))]
                date = next((d for d in dates if d not in ('Recorded_At', 'Share_Recorded_At', 'As_Of_Date', 'Coverage_Start_Date', 'Coverage_End_Date')), None)
                date = date or ('Recorded_At' if 'Recorded_At' in cols else None)
                if not key or not date:
                    continue
                recorded = 'Recorded_At' if 'Recorded_At' in cols else date
                quarter = '"Quarter"' if 'Quarter' in cols else 'NULL'
                query = f'SELECT "{key}", "{date}", "{recorded}", {quarter} FROM "{table}" WHERE "{date}" IS NOT NULL'
                dst.executemany('INSERT INTO quarter_keys VALUES (?,?,?,?,?)',
                                ((table, r[0], r[1], r[2] or r[1], r[3] or _quarter(r[1])) for r in src.execute(query)))
            dst.commit()
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build_discovery_index(args.database, args.output)


if __name__ == '__main__':
    main()


