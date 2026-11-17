"""Shared constants and helpers for the discovery_v1 generator (plan v10 §5).

Every module receives one Context, adds rows to ctx.tables and never writes files itself.
"""
import csv
import random
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

FINAL = Path(__file__).resolve().parents[2]
LEGACY = FINAL / "files_update"
EXTENSIONS = FINAL / "data_extensions"
PACK = FINAL / "files_discovery_v1"
PRIVATE = FINAL / "files_discovery_v1_private"

SEED = 20261115
ANALYSIS = (date(2025, 10, 1), date(2026, 6, 30))
FOLLOW_UP = (date(2026, 7, 1), date(2026, 9, 30))
AS_OF = ANALYSIS[1]
DECISION_DATE = FOLLOW_UP[0]
QUARTERS = {
    "2025-Q4": (date(2025, 10, 1), date(2025, 12, 31)),
    "2026-Q1": (date(2026, 1, 1), date(2026, 3, 31)),
    "2026-Q2": (date(2026, 4, 1), date(2026, 6, 30)),
    "2026-Q3": (date(2026, 7, 1), date(2026, 9, 30)),
}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def rng(name):
    """An independent, reproducible random stream per purpose, so modules do not shift each other."""
    return random.Random(f"{SEED}:{name}")


def quarter_of(day):
    return next(key for key, (start, end) in QUARTERS.items() if start <= day <= end)


def dictionary():
    """Column order per table (file name without .csv), from the frozen data dictionary."""
    columns = {}
    for row in read_csv(PACK / "QA_data_dictionary.csv"):
        columns.setdefault(row["File"].removesuffix(".csv"), []).append(row["Column"])
    return columns


STORY_ROWS = PRIVATE / "QA_discovery_v1_story_rows.csv"
# Pinned tables use formula IDs (below): the background row for that person, week or declaration
# is the story row, so these IDs are written by the background generator with the story's values.
PINNED_PREFIXES = ("PRF", "AWK", "COV")
COVERAGE_TABLES = ("HR_recognition_feedback", "HR_recognition_events", "HR_one_on_ones", "HR_review_notes",
                   "OP_team_plans", "OP_meeting_mentions", "OP_collab_messages")
WEEK_ZERO = date(2025, 9, 29)  # Monday; week index 0 of OP_activity_weekly (53 week starts, to 2026-09-28)


def story_rows():
    return read_csv(STORY_ROWS) if STORY_ROWS.exists() else []


def reserved_ids():
    """Story-only IDs (T0.3) that background rows must never use."""
    return {row["Row_ID"] for row in story_rows()
            if row["Row_ID"] not in ("", "NONE") and not row["Row_ID"].startswith(PINNED_PREFIXES)}


def pinned_rows(table):
    """Story values for pinned background rows of one table, keyed by their formula ID."""
    return {row["Row_ID"]: row for row in story_rows() if row["Table"] == table and row["Row_ID"].startswith(PINNED_PREFIXES)}


def employee_number(employee_id):
    return int(employee_id.removeprefix("E"))


def prf_id(quarter, employee_id):
    return f"PRF{list(QUARTERS).index(quarter) * 2500 + employee_number(employee_id):06d}"


def awk_id(week_start, employee_id):
    return f"AWK{(week_start - WEEK_ZERO).days // 7 * 2500 + employee_number(employee_id):06d}"


def cov_id(source_table, manager_id, quarter):
    index = COVERAGE_TABLES.index(source_table) * 240 + (int(manager_id.removeprefix("M")) - 1) * 4
    return f"COV{index + list(QUARTERS).index(quarter) + 1:06d}"


class Ids:
    """Allocates PREFIX + 6-digit IDs in order, skipping reserved ones."""

    def __init__(self, reserved):
        self.reserved, self.next = set(reserved), {}

    def start_after(self, prefix, last_id):
        self.next[prefix] = int(last_id.removeprefix(prefix)) + 1

    def new(self, prefix):
        number = self.next.get(prefix, 1)
        while f"{prefix}{number:06d}" in self.reserved:
            number += 1
        self.next[prefix] = number + 1
        return f"{prefix}{number:06d}"


@dataclass
class Context:
    employees: list
    managers: list
    ids: Ids
    tables: dict = field(default_factory=dict)
    answer_key: list = field(default_factory=list)

    def team(self, manager_id):
        return [row for row in self.employees if row["Pilot_Manager_ID"] == manager_id]

    def employee(self, employee_id):
        return next(row for row in self.employees if row["Employee_ID"] == employee_id)

    def manager(self, manager_id):
        return next(row for row in self.managers if row["Manager_ID"] == manager_id)

    def rows(self, table):
        return self.tables.setdefault(table, [])


def load_context():
    ids = Ids(reserved_ids())
    ids.start_after("INT", read_csv(LEGACY / "HR_recognition_feedback.csv")[-1]["Interaction_ID"])
    ids.start_after("CON", read_csv(LEGACY / "OP_contributions.csv")[-1]["Contribution_ID"])
    return Context(read_csv(LEGACY / "HR_employees.csv"), read_csv(LEGACY / "HR_managers.csv"), ids)


def write_pack(ctx):
    """Write every manifest table with the dictionary's exact columns; fail on any missing or extra column."""
    columns = dictionary()
    for entry in read_csv(PACK / "QA_manifest.csv"):
        table = entry["File"].removesuffix(".csv")
        rows, header = ctx.tables.get(table), columns[table]
        if rows is None:
            raise RuntimeError(f"No module produced {table}.")
        for row in rows:
            if set(row) != set(header):
                raise RuntimeError(f"{table} row {row.get(header[0])}: columns differ from the dictionary "
                                   f"(missing {sorted(set(header) - set(row))}, extra {sorted(set(row) - set(header))}).")
        with (PACK / entry["File"]).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)


def write_answer_key(ctx):
    path = PRIVATE / "QA_discovery_v1_answer_key.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=header)
        writer.writeheader()
        writer.writerows(ctx.answer_key)
