"""The discovery_v1 importer profile, on a tiny generated pack. Offline; no model calls."""

import contextlib
import csv
from pathlib import Path
import sqlite3
import tempfile
import unittest

import import_data

DICTIONARY_HEADER = ('File', 'Column', 'Type', 'Meaning', 'Primary_Key', 'References', 'Nullable', 'Allowed_Values')
FEEDBACK = 'HR_recognition_feedback.csv'
# File, Column, Type, Meaning, PK, References, Nullable, Allowed_Values
DICTIONARY = [
    ('HR_managers.csv', 'Manager_ID', 'TEXT', 'id', 'Yes', '', 'No', ''),
    ('HR_managers.csv', 'Level', 'INTEGER', 'level', 'No', '', 'No', ''),
    ('OP_collab_threads.csv', 'Thread_ID', 'TEXT', 'id', 'Yes', '', 'No', ''),
    ('OP_collab_threads.csv', 'Manager_ID', 'TEXT', 'owner', 'No', 'HR_managers.csv.Manager_ID', 'No', ''),
    ('OP_collab_threads.csv', 'Helper_Manager_IDs', 'TEXT', 'Helpers, ;-separated.', 'No', 'HR_managers.csv.Manager_ID', 'Yes', ''),
    (FEEDBACK, 'Interaction_ID', 'TEXT', 'id', 'Yes', '', 'No', ''),
    (FEEDBACK, 'Interaction_At', 'TIMESTAMP', 'when', 'No', '', 'No', ''),
    (FEEDBACK, 'Record_Coverage', 'TEXT', 'coverage', 'No', '', 'No', 'complete|partial'),
    (FEEDBACK, 'Contribution_ID', 'TEXT', 'At least one of Contribution_ID and Thread_ID is filled.', 'No', '', 'Yes', ''),
    (FEEDBACK, 'Thread_ID', 'TEXT', 'At least one of Contribution_ID and Thread_ID is filled.', 'No',
     'OP_collab_threads.csv.Thread_ID', 'Yes', ''),
    (FEEDBACK, 'Shared_With_Home_Manager', 'TEXT', 'flag', 'No', '', 'No', 'Yes|No'),
    (FEEDBACK, 'Shared_With_Home_Manager_At', 'TIMESTAMP', 'shared', 'No', '', 'Yes', ''),
    (FEEDBACK, 'Share_Recorded_At', 'TIMESTAMP', 'recorded', 'No', '', 'Yes', ''),
]
GOOD = {
    'HR_managers.csv': [['M1', '3']],
    'OP_collab_threads.csv': [['T1', 'M1', 'M1;M1']],
    # Interaction_ID, Interaction_At, Record_Coverage, Contribution_ID, Thread_ID, flag, shared, recorded
    FEEDBACK: [['I1', '2026-01-05T09:00:00', 'complete', '', 'T1', 'Yes', '2026-01-06T09:00:00', '2026-01-07T09:00:00'],
               ['I2', '2026-01-05T09:00:00', 'partial', 'C1', '', 'No', '', '']],
}


def write_pack(folder, change=None):
    """Write the tiny pack; `change(rows)` may edit the file rows before they are written."""
    rows = {name: [list(row) for row in table] for name, table in GOOD.items()}
    if change:
        change(rows)
    headers = {}
    for definition in DICTIONARY:
        headers.setdefault(definition[0], []).append(definition[1])
    with (folder / 'QA_data_dictionary.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(DICTIONARY_HEADER)
        writer.writerows(DICTIONARY)
    with (folder / 'QA_manifest.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(('File', 'Rows', 'Primary_Key', 'Load_Into_Prototype', 'Profile'))
        for name, columns in headers.items():  # deliberately not in dependency order
            writer.writerow((name, len(rows[name]), columns[0], 'Yes', 'discovery_v1'))
        writer.writerow(('Other.csv', 1, 'Id', 'Yes', 'legacy'))
    for name, columns in headers.items():
        with (folder / name).open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(columns)
            writer.writerows(rows[name])


class DiscoveryProfileTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'pack'
        self.source.mkdir()
        self.output = Path(self.folder.name) / 'out.db'

    def build(self, change=None):
        write_pack(self.source, change)
        return import_data.build_database(self.source, self.output, profile='discovery_v1')

    def assertRejects(self, change, *parts):
        with self.assertRaises(ValueError) as caught:
            self.build(change)
        for part in parts:
            self.assertIn(part, str(caught.exception))
        self.assertFalse(self.output.exists())
        self.assertEqual([], list(self.output.parent.glob('*.build-*')))

    def test_legacy_defaults_are_unchanged(self):
        source, database = import_data.default_paths('legacy')
        self.assertEqual(import_data.HERE.parent / 'files_update', source)
        self.assertEqual(import_data.HERE / 'data' / 'echo.db', database)
        self.assertEqual(11, len(import_data.FILES))
        self.assertEqual(import_data.HERE / 'data' / 'echo_discovery_v1.db', import_data.default_paths('discovery_v1')[1])

    def test_discovery_refuses_the_legacy_database(self):
        write_pack(self.source)
        with self.assertRaisesRegex(ValueError, 'never writes data/echo.db'):
            import_data.build_database(self.source, import_data.LEGACY_DATABASE, replace=True, profile='discovery_v1')

    def test_a_good_pack_loads_with_types_and_indexes(self):
        counts = self.build()
        self.assertEqual({'HR_managers': 1, 'OP_collab_threads': 1, 'HR_recognition_feedback': 2}, counts)
        with contextlib.closing(sqlite3.connect(self.output)) as connection:
            types = {row[1]: row[2] for row in connection.execute('PRAGMA table_info(HR_managers)')}
            indexes = {row[1] for row in connection.execute("PRAGMA index_list('HR_recognition_feedback')")}
        self.assertEqual('INTEGER', types['Level'])
        self.assertIn('idx_HR_recognition_feedback_Interaction_At', indexes)
        self.assertIn('idx_HR_recognition_feedback_Thread_ID', indexes)

    def test_bad_timestamp(self):
        self.assertRejects(lambda rows: rows[FEEDBACK][0].__setitem__(1, '2026-01-05 09:00'),
                           FEEDBACK, 'line 2', 'Interaction_At')

    def test_bad_enum(self):
        self.assertRejects(lambda rows: rows[FEEDBACK][1].__setitem__(2, 'maybe'), 'line 3', 'Record_Coverage')

    def test_share_date_before_interaction(self):
        self.assertRejects(lambda rows: rows[FEEDBACK][0].__setitem__(6, '2026-01-04T09:00:00'),
                           'line 2', 'Shared_With_Home_Manager_At')

    def test_share_flag_must_match_the_date(self):
        self.assertRejects(lambda rows: rows[FEEDBACK][0].__setitem__(5, 'No'), 'Shared_With_Home_Manager')

    def test_anchor_rule(self):
        self.assertRejects(lambda rows: rows[FEEDBACK][1].__setitem__(3, ''), 'line 3', 'at least one')

    def test_unknown_reference_and_duplicate_key(self):
        self.assertRejects(lambda rows: rows['OP_collab_threads.csv'][0].__setitem__(1, 'M9'),
                           'OP_collab_threads.csv', 'line 2', 'Manager_ID')
        self.assertRejects(lambda rows: rows[FEEDBACK].append(list(rows[FEEDBACK][0])), 'duplicate primary key')

    def test_id_list_entries_are_each_checked(self):
        self.assertRejects(lambda rows: rows['OP_collab_threads.csv'][0].__setitem__(2, 'M1;M9'),
                           'Helper_Manager_IDs', "'M9'")


if __name__ == '__main__':
    unittest.main()
