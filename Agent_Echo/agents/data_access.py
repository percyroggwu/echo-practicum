"""Build physically scoped data copies before any model-generated query runs."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class AccessScope:
    """Trusted caller scope; a CLI manager selection is only a demo, not login."""

    manager_id: str
    start_date: str = "2024-10-01"
    end_date: str = "2026-09-30"

    def __post_init__(self):
        start, end = date.fromisoformat(self.start_date), date.fromisoformat(self.end_date)
        if not date(2024, 10, 1) <= start <= end <= date(2026, 9, 30):
            raise ValueError("Scope must be within 2024-10-01 through 2026-09-30.")
        if not self.manager_id or len(self.manager_id) > 40:
            raise ValueError("A valid manager ID is required.")


def open_source(path):
    path = Path(path).resolve()
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


class ScopedData:
    """Only this backend reads the full database; neither agent receives it."""

    def __init__(self, database, scope):
        self.source = open_source(database)
        self.scope = scope
        self.params = (scope.manager_id, scope.end_date, scope.start_date)
        self.employee_filter = """
            SELECT Employee_ID FROM HR_employees
            WHERE Pilot_Manager_ID = ? AND Hire_Date <= ?
              AND (Termination_Date IS NULL OR Termination_Date >= ?)
        """
        try:
            manager = self.source.execute(
                "SELECT Manager_ID, Manager_Name FROM HR_managers WHERE Manager_ID = ?",
                (scope.manager_id,),
            ).fetchone()
            if manager is None:
                raise ValueError("Unknown manager ID.")
            self.manager = dict(manager)
            self.teams = [row[0] for row in self.source.execute(
                f"SELECT DISTINCT Team_Display_Name FROM HR_employees WHERE Employee_ID IN ({self.employee_filter})",
                self.params,
            )]
        except Exception:
            self.source.close()
            raise

    def close(self):
        self.source.close()

    def employee_rows(self, table, employee_column, date_column=None, fields="*"):
        # Table/column identifiers here are developer constants, never model input.
        query = f"SELECT {fields} FROM {table} WHERE {employee_column} IN ({self.employee_filter})"
        params = self.params
        if date_column:
            query += f" AND {date_column} BETWEEN ? AND ?"
            params += (self.scope.start_date, self.scope.end_date)
        cursor = self.source.execute(query, params)
        return [col[0] for col in cursor.description], cursor.fetchall()

    def survey_rows(self, comments=False):
        placeholders = ",".join("?" for _ in self.teams) or "NULL"
        if comments:
            query = """SELECT c.Comment_ID, c.Survey_ID, c.Survey_Date, c.Department,
                c.Team, c.Dimension, c.Response_Score, c.Open_Text_Question, c.Response_Text
                FROM HR_survey_comments c JOIN HR_survey_summary s ON c.Survey_ID = s.Survey_ID
                WHERE c.Team IN ({}) AND c.Survey_Date BETWEEN ? AND ? AND s.Responses >= 5"""
        else:
            query = """SELECT * FROM HR_survey_summary WHERE Team IN ({})
                AND Survey_Date BETWEEN ? AND ? AND Responses >= 5"""
        cursor = self.source.execute(query.format(placeholders),
            (*self.teams, self.scope.start_date, self.scope.end_date))
        return [col[0] for col in cursor.description], cursor.fetchall()

    def structured_tables(self):
        """Approved fields only: no raw comments, tokens, contact details or QA."""
        tables = {}
        tables["employees"] = self.employee_rows(
            "HR_employees", "Employee_ID", fields="Employee_ID, Employee_Name, Department, Team_Display_Name, Job_Title, Job_Level, Hire_Date, Termination_Date")
        tables["survey_summary"] = self.survey_rows()
        # Older databases (data/echo.db) lack these two contribution columns.
        have = {r[1] for r in self.source.execute("PRAGMA table_info(OP_contributions)")}
        optional = "".join(", " + c for c in ("Team_Goal_ID", "Effort_Hours") if c in have)
        for name, table, employee, event_date, fields in (
            ("contributions", "OP_contributions", "Employee_ID", "Contribution_Date",
             "Contribution_ID, Work_Request_ID, Employee_ID, Employee_Name, Home_Team, Beneficiary_Team, Contribution_Date" + optional),
            ("recognition_feedback", "HR_recognition_feedback", "Employee_ID", "Interaction_Date",
             "Interaction_ID, Interaction_Type, Contribution_ID, Work_Request_ID, Employee_ID, Recipient_Manager_ID, Interaction_Date, Shared_With_Home_Manager, Record_Coverage"),
            ("capacity", "OP_capacity", "Employee_ID", "Week_Start", "*"),
            ("work_requests", "OP_work_requests", "Assigned_Employee_ID", "Week_Start",
             "Work_Request_ID, Project_ID, Project_Name, Requested_By_Manager_ID, Requesting_Team, Assigned_Employee_ID, Assigned_Employee_Name, Assigned_Employee_Team, Request_Date, Week_Start, Original_Due_Date, Current_Due_Date, Original_Priority, Current_Priority, Original_Estimated_Hours, Current_Estimated_Hours, Actual_Hours, Rework_Hours, Status, Work_Title, Completion_Date"),
        ):
            tables[name] = self.employee_rows(table, employee, event_date, fields)
        decision_query = f"""SELECT Decision_ID, Work_Request_ID, Related_Work_Request_ID,
            Decision_Date, Decision_Maker_ID, Decision_Type, Previous_Due_Date, Revised_Due_Date,
            Previous_Priority, Revised_Priority, Previous_Estimated_Hours, Revised_Estimated_Hours,
            Status_After_Decision FROM OP_priority_decisions
            WHERE Work_Request_ID IN (SELECT Work_Request_ID FROM OP_work_requests
                WHERE Assigned_Employee_ID IN ({self.employee_filter}))
              AND Decision_Date BETWEEN ? AND ?"""
        cursor = self.source.execute(decision_query,
            (*self.params, self.scope.start_date, self.scope.end_date))
        tables["priority_decisions"] = ([col[0] for col in cursor.description], cursor.fetchall())
        cursor = self.source.execute(f"""SELECT Project_ID, Project_Name, Sponsoring_Department,
            Sponsoring_Team, Project_Start_Date, Target_End_Date FROM OP_projects
            WHERE Project_ID IN (SELECT Project_ID FROM OP_work_requests
                WHERE Assigned_Employee_ID IN ({self.employee_filter}) AND Week_Start BETWEEN ? AND ?)""",
            (*self.params, self.scope.start_date, self.scope.end_date))
        tables["projects"] = ([col[0] for col in cursor.description], cursor.fetchall())
        # Participation is aggregated by team; no individual benefit-use history is exposed.
        cursor = self.source.execute(f"""SELECT Department, Team, Program_ID, Program_Type,
            Program_Name, Reporting_Period, Period_Start_Date, Period_End_Date,
            COUNT(*) AS Eligible_Records, COUNT(DISTINCT Employee_ID) AS Eligible_Employees,
            SUM(CASE WHEN Participation_Status IN ('Used','Completed','In progress') THEN 1 ELSE 0 END) AS Participating_Records,
            SUM(CASE WHEN Participation_Status = 'Completed' THEN 1 ELSE 0 END) AS Completed_Records,
            SUM(Use_Count) AS Total_Uses, SUM(Participation_Hours) AS Total_Participation_Hours,
            AVG(Usefulness_Score) AS Mean_Usefulness_Score
            FROM HR_program_participation WHERE Employee_ID IN ({self.employee_filter})
              AND Period_Start_Date <= ? AND Period_End_Date >= ?
            GROUP BY Department, Team, Program_ID, Program_Type, Program_Name,
                     Reporting_Period, Period_Start_Date, Period_End_Date
            HAVING COUNT(DISTINCT Employee_ID) >= 5""",
            (*self.params, self.scope.end_date, self.scope.start_date))
        tables["program_summary"] = ([col[0] for col in cursor.description], cursor.fetchall())
        return tables

    def sentiment_documents(self):
        """Full authorized responses without tokens, employee identity or numeric ratings."""
        _, rows = self.survey_rows(comments=True)
        return [{"citation_id": "survey:" + row["Comment_ID"], "source": "HR_survey_comments",
            "record_id": row["Comment_ID"], "team": row["Team"], "date": row["Survey_Date"],
            "dimension": row["Dimension"], "anonymous": True,
            "question": row["Open_Text_Question"] or "", "response_text": row["Response_Text"] or ""}
            for row in rows]

    def text_documents(self):
        """Every passage keeps its record ID, source, team, date and anonymity."""
        _, rows = self.survey_rows(comments=True)
        documents = []
        for row in rows:
            documents.append({
                "citation_id": "survey:" + row["Comment_ID"], "source": "HR_survey_comments",
                "record_id": row["Comment_ID"], "team": row["Team"],
                "date": row["Survey_Date"], "dimension": row["Dimension"],
                "anonymous": True, "text": row["Open_Text_Question"] + "\n" + row["Response_Text"],
            })
        for source, key, employee, event_date, team, text_columns in (
            ("HR_recognition_feedback", "Interaction_ID", "Employee_ID", "Interaction_Date", "Author_Team", ("Message",)),
            ("OP_contributions", "Contribution_ID", "Employee_ID", "Contribution_Date", "Home_Team", ("Project_Name", "Contribution_Summary", "Business_Outcome", "Evidence_Description")),
            ("OP_work_requests", "Work_Request_ID", "Assigned_Employee_ID", "Request_Date", "Assigned_Employee_Team", ("Project_Name", "Work_Title", "Work_Description", "Expected_Deliverable", "Dependency_Description")),
        ):
            _, rows = self.employee_rows(source, employee, event_date)
            for row in rows:
                documents.append({
                    "citation_id": source + ":" + row[key], "source": source,
                    "record_id": row[key], "team": row[team], "date": row[event_date],
                    "dimension": "", "anonymous": False,
                    "text": "\n".join(str(row[col]) for col in text_columns if row[col]),
                })
        cursor = self.source.execute(f"""SELECT d.*, w.Assigned_Employee_Team FROM OP_priority_decisions d
            JOIN OP_work_requests w ON d.Work_Request_ID = w.Work_Request_ID
            WHERE w.Assigned_Employee_ID IN ({self.employee_filter}) AND d.Decision_Date BETWEEN ? AND ?""",
            (*self.params, self.scope.start_date, self.scope.end_date))
        for row in cursor:
            documents.append({
                "citation_id": "OP_priority_decisions:" + row["Decision_ID"],
                "source": "OP_priority_decisions", "record_id": row["Decision_ID"],
                "team": row["Assigned_Employee_Team"], "date": row["Decision_Date"],
                "dimension": "", "anonymous": False,
                "text": "\n".join(str(row[col]) for col in ("Decision_Type", "Decision_Explanation", "Tradeoff") if row[col]),
            })
        return documents

# Discovery is deliberately separate from the legacy access contract above.
_DISCOVERY_START = "2025-10-01"
_DISCOVERY_END = "2026-06-30"
_FOLLOWUP_END = "2026-09-30"
_ANCHORS = {"Contribution_ID": "contribution", "Thread_ID": "thread",
            "Blocker_ID": "blocker", "Incident_ID": "incident"}


DISCOVERY_RANGE = (_DISCOVERY_START, _DISCOVERY_END)


def is_discovery_database(path):
    """True for a discovery_v1 import (it has the collaboration tables); a missing file is not one."""
    try:
        if not Path(path).is_file():
            return False
        connection = open_source(path)
        try:
            return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='OP_collab_threads'").fetchone() is not None
        finally:
            connection.close()
    except (sqlite3.Error, OSError, TypeError):
        return False


@dataclass(frozen=True)
class DiscoveryScope:
    manager_id: str
    start_date: str
    end_date: str

    def __post_init__(self):
        if not self.manager_id or len(self.manager_id) > 40:
            raise ValueError("A valid manager ID is required.")
        if (self.start_date, self.end_date) != (_DISCOVERY_START, _DISCOVERY_END):
            raise ValueError("Discovery requires 2025-10-01 through 2026-06-30.")


@dataclass(frozen=True)
class FollowUpScope:
    manager_id: str
    start_date: str
    end_date: str
    employee_ids: tuple
    work_refs: tuple
    beneficiary_manager_ids: tuple = ()

    def __post_init__(self):
        if not self.manager_id or len(self.manager_id) > 40:
            raise ValueError("A valid manager ID is required.")
        if not (_DISCOVERY_END < self.start_date <= self.end_date <= _FOLLOWUP_END):
            raise ValueError("Follow-up dates must be within July through September 2026.")
        date.fromisoformat(self.start_date)
        date.fromisoformat(self.end_date)
        if not self.employee_ids:
            raise ValueError("Saved action employees are required.")
        if any(not isinstance(ref, dict) or set(ref) != {"type", "id"}
               or ref["type"] not in _ANCHORS.values() or not ref["id"]
               for ref in self.work_refs):
            raise ValueError("Invalid saved work reference.")


def _normalize(value):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", str(value).casefold())
                   if not unicodedata.combining(c)).strip()


def _in_window(value, start, end):
    return bool(value) and start <= str(value)[:10] <= end


def _quarter(value):
    d = date.fromisoformat(str(value)[:10])
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


class DiscoveryData:
    """Read-only discovery projections; callers never receive outside identities."""

    def __init__(self, database, scope):
        if not isinstance(scope, DiscoveryScope):
            raise TypeError("DiscoveryScope is required.")
        path = Path(database).resolve()
        if ('files_discovery_v1_private' in {part.casefold() for part in path.parts}
                or path.name.casefold() in {'.env', 'connections.private.json'}):
            raise ValueError("Private QA and credentials are not Discovery sources.")
        self.scope = scope
        self._source = open_source(database)
        try:
            manager = self._source.execute("SELECT Manager_ID, Manager_Name, Primary_Team FROM HR_managers WHERE Manager_ID = ?", (scope.manager_id,)).fetchone()
            if manager is None:
                raise ValueError("Unknown manager ID.")
            self.manager = dict(manager)
            self._people = [dict(r) for r in self._source.execute(
                "SELECT Employee_ID, Employee_Name, Team_Display_Name, Pilot_Manager_ID, Hire_Date, Termination_Date, Department, Job_Title, Job_Level FROM HR_employees")]
            self._person_managers = {p['Employee_ID']: p['Pilot_Manager_ID'] for p in self._people}
            self._managers = [dict(r) for r in self._source.execute(
                "SELECT Manager_ID, Manager_Name, Primary_Team FROM HR_managers")]
            self._roster = [p for p in self._people if p['Pilot_Manager_ID'] == scope.manager_id
                            and p['Hire_Date'] <= scope.end_date
                            and (not p['Termination_Date'] or p['Termination_Date'] >= scope.end_date)]
            self._own = {p['Employee_ID'] for p in self._roster}
            self._replacements = self._make_replacements()
            import re
            self._replacement_tokens = {}
            for original, replacement in self._replacements:
                token = re.search(r"\w+", original)
                if token:
                    pattern = re.compile(r"(?<!\w)" + re.escape(original) + r"(?!\w)", re.I)
                    self._replacement_tokens.setdefault(token.group().casefold(), []).append((pattern, replacement))
        except Exception:
            self._source.close()
            raise

    def close(self):
        self._source.close()

    def roster(self):
        return [dict(p) for p in self._roster]

    def resolve_person(self, name_or_id):
        key = _normalize(name_or_id)
        matches = [p for p in self._people if key and key in (_normalize(p['Employee_ID']), _normalize(p['Employee_Name']))]
        return {"own_matches": [dict(p) for p in matches if p['Employee_ID'] in self._own],
                "outside_match": any(p['Employee_ID'] not in self._own for p in matches)}

    def resolve_team(self, name_or_id):
        key = _normalize(name_or_id)
        matches = [m for m in self._managers if key and key in (_normalize(m['Manager_ID']), _normalize(m['Primary_Team']))]
        return [{"manager_id": m['Manager_ID'], "team": m['Primary_Team'],
                 "own_team": m['Manager_ID'] == self.scope.manager_id} for m in matches]

    def team_manager(self, manager_id):
        """A partner team's manager, used only as the recipient of an A2/A4 draft."""
        match = next((m for m in self._managers if m['Manager_ID'] == manager_id), None)
        return {"manager_id": manager_id, "manager_name": match['Manager_Name'], "team": match['Primary_Team']} if match else None

    def _make_replacements(self):
        # Stable within the organization, even when only some people appear in evidence.
        groups = {}
        replacements = []
        for p in sorted(self._people, key=lambda p: p['Employee_ID']):
            if p['Employee_ID'] in self._own:
                continue
            team = p['Team_Display_Name'] or 'Other team'
            groups[team] = groups.get(team, 0) + 1
            placeholder = f"[{team} colleague {groups[team]}]"
            replacements.extend((v, placeholder) for v in (p['Employee_Name'], p['Employee_ID']) if v)
        for m in sorted(self._managers, key=lambda m: m['Manager_ID']):
            if m['Manager_ID'] != self.scope.manager_id:
                replacements.extend((v, f"[{m['Primary_Team']} manager]") for v in (m['Manager_Name'], m['Manager_ID']) if v)
        return sorted(replacements, key=lambda item: -len(item[0]))

    def sanitize(self, value):
        import re
        if not isinstance(value, str):
            return value
        tokens = set(re.findall(r"\w+", value.casefold()))
        for token in tokens:
            for pattern, replacement in self._replacement_tokens.get(token, ()):
                value = pattern.sub(lambda m: replacement, value)
        return value

    def _project(self, table, row, event_field, people, beneficiary=None, as_of=None):
        raw = dict(row)
        as_of = as_of or self.scope.end_date
        event = raw.get(event_field)
        record_id = next(iter(raw.values()))
        refs = [{"type": kind, "id": raw[col]} for col, kind in _ANCHORS.items() if raw.get(col)]
        # Work records themselves are anchors even when they do not repeat their key.
        own_anchor = {"OP_contributions": "contribution", "OP_collab_threads": "thread",
                      "OP_dependency_blockers": "blocker", "OP_incident_handoffs": "incident"}.get(table)
        if own_anchor and not any(r['type'] == own_anchor and r['id'] == record_id for r in refs):
            refs.append({"type": own_anchor, "id": record_id})
        projected = {}
        for key, value in raw.items():
            if key in ('Data_Origin', 'Shared_With_Home_Manager'):
                continue
            if key.endswith('_At') or key.endswith('_Date'):
                if value and str(value)[:10] > as_of:
                    value = None
            if key in ('Author_Employee_ID', 'Requester_Employee_ID', 'Resolved_By_Employee_ID', 'Mentioned_Employee_ID', 'Employee_ID', 'Assigned_Employee_ID') and value and value not in self._own:
                value = self.sanitize(value)
            elif key in ('Mentioned_Employee_IDs', 'Responder_Employee_IDs') and value:
                value = ';'.join(self.sanitize(v) for v in value.split(';'))
            elif (key == 'Manager_ID' or key.endswith('_Manager_ID')) and value and value != self.scope.manager_id:
                # Beneficiary IDs are retained separately, not as person identifiers.
                value = f"[{next((m['Primary_Team'] for m in self._managers if m['Manager_ID'] == value), 'Other team')} manager]"
            else:
                value = self.sanitize(value)
            projected[key] = value
        if table == 'HR_recognition_feedback':
            projected['shared_as_of'] = bool(raw.get('Shared_With_Home_Manager_At') and raw.get('Share_Recorded_At')
                and raw['Shared_With_Home_Manager_At'][:10] <= as_of
                and raw['Share_Recorded_At'][:10] <= as_of)
        # A later resolution is not known as of the analysis date.
        if table == 'OP_dependency_blockers' and raw.get('Resolved_At') and raw['Resolved_At'][:10] > as_of:
            people = set(people) - {raw.get('Resolved_By_Employee_ID')}
        for date_field, fields in (('Resolved_At', ('Days_Blocked', 'Resolution_Note', 'Resolved_By_Employee_ID')),
                                   ('Ended_At', ()), ('Closed_At', ()),
                                   ('Completion_Date', ('Status', 'Actual_Hours', 'Rework_Hours'))):
            if raw.get(date_field) and raw[date_field][:10] > as_of:
                for field in fields:
                    projected[field] = None
        projected.update(source=table, record_id=record_id, event_date=event,
                         recorded_date=raw.get('Recorded_At') or event,
                         quarter=_quarter(event), employee_ids=sorted(set(people) & self._own),
                         work_refs=refs, beneficiary_manager_id=beneficiary)
        return projected

    def evidence(self):
        """Return scoped table-keyed rows, including own names mentioned in others' records."""
        if hasattr(self, '_evidence_cache'):
            return self._evidence_cache
        start, end = self.scope.start_date, self.scope.end_date
        own = self._own
        output = {}
        specs = {
            'OP_contributions': ('Contribution_Date', ('Employee_ID',)),
            'HR_recognition_feedback': ('Interaction_At', ('Employee_ID',)),
            'OP_collab_threads': ('Opened_At', ('Requester_Employee_ID',)),
            'OP_collab_messages': ('Sent_At', ('Author_Employee_ID', 'Mentioned_Employee_IDs')),
            'OP_dependency_blockers': ('Raised_At', ('Resolved_By_Employee_ID',)),
            'OP_incident_handoffs': ('Started_At', ('Responder_Employee_IDs',)),
            'OP_meeting_mentions': ('Meeting_Date', ('Mentioned_Employee_ID',)),
            'HR_recognition_events': ('Recognized_At', ('Employee_ID',)),
            'OP_activity_weekly': ('Week_Start', ('Employee_ID',)),
            'OP_capacity': ('Week_Start', ('Employee_ID',)),
            'HR_employee_performance': ('Recorded_At', ('Employee_ID',)),
            'HR_goals': ('Set_Date', ('Employee_ID',)),
            'HR_self_review_items': ('Submitted_Date', ('Employee_ID',)),
            'HR_one_on_ones': ('Meeting_Date', ('Employee_ID',)),
            'HR_review_notes': ('Note_Date', ('Employee_ID',)),
            'OP_work_requests': ('Request_Date', ('Assigned_Employee_ID',)),
        }
        # Restrict organization-wide text matching to name/ID occurrences of own active staff.
        import re
        name_ids = {}
        for person in self._roster:
            if person['Employee_Name']:
                name_ids.setdefault(person['Employee_Name'].casefold(), set()).add(person['Employee_ID'])
        name_pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(n) for n in sorted(name_ids, key=len, reverse=True)) + r')(?!\w)', re.I) if name_ids else None
        threads = {}
        for table, (event, person_fields) in specs.items():
            output[table] = []
            query = f"SELECT * FROM {table} WHERE substr({event},1,10) BETWEEN ? AND ?"
            params = [start, end]
            if table not in ('HR_recognition_feedback', 'OP_collab_messages', 'OP_meeting_mentions', 'OP_incident_handoffs'):
                marks = ','.join('?' for _ in own) or 'NULL'
                query += ' AND (' + ' OR '.join(f"{field} IN ({marks})" for field in person_fields) + ')'
                for _ in person_fields:
                    params.extend(sorted(own))
            for row in self._source.execute(query, params):
                raw = dict(row)
                if raw.get('Recorded_At') and raw['Recorded_At'][:10] > end:
                    continue
                if table == 'HR_employee_performance' and raw['Quarter'] not in ('2025-Q4', '2026-Q1', '2026-Q2'):
                    continue
                people = {v for field in person_fields for v in str(raw.get(field) or '').split(';') if v in own}
                if table == 'OP_dependency_blockers' and raw.get('Resolved_At') and raw['Resolved_At'][:10] > end:
                    people.discard(raw.get('Resolved_By_Employee_ID'))
                if table in ('HR_recognition_feedback', 'OP_collab_messages', 'OP_meeting_mentions'):
                    content = ' '.join(str(raw.get(k) or '') for k in ('Message', 'Message_Text', 'Note_Text'))
                    if name_pattern:
                        for match in name_pattern.finditer(content):
                            people.update(name_ids[match.group().casefold()])
                if not people:
                    continue
                beneficiary = None
                if table == 'OP_contributions' and raw.get('Work_Request_ID'):
                    request = self._source.execute('SELECT Requested_By_Manager_ID FROM OP_work_requests WHERE Work_Request_ID=? AND substr(Request_Date,1,10) BETWEEN ? AND ?', (raw['Work_Request_ID'], start, end)).fetchone()
                    if request:
                        beneficiary = request[0]
                elif table == 'OP_collab_threads':
                    # The requesting team receives the help; a scoped requester is not a helper.
                    beneficiary = raw['Requesting_Manager_ID']
                    threads[raw['Thread_ID']] = beneficiary
                elif table == 'OP_dependency_blockers':
                    beneficiary = raw['Blocked_Manager_ID']
                elif table == 'OP_incident_handoffs':
                    beneficiary = raw['Owning_Manager_ID']
                elif table == 'OP_meeting_mentions':
                    beneficiary = raw['Meeting_Manager_ID']
                elif table == 'OP_work_requests':
                    beneficiary = raw['Requested_By_Manager_ID']
                elif table == 'OP_collab_messages':
                    thread = self._source.execute('SELECT Requesting_Manager_ID, Responding_Manager_ID FROM OP_collab_threads WHERE Thread_ID=? AND substr(Opened_At,1,10) BETWEEN ? AND ?', (raw['Thread_ID'], start, end)).fetchone()
                    if thread:
                        beneficiary = thread['Requesting_Manager_ID']
                elif table == 'HR_recognition_feedback':
                    beneficiary = raw['Author_Manager_ID'] or self._person_managers.get(raw.get('Author_Employee_ID'))
                output[table].append(self._project(table, row, event, people, beneficiary))
        # Include parent threads and linked beneficiary goals only for scoped evidence.
        existing_threads = {r['record_id'] for r in output['OP_collab_threads']}
        for message in output['OP_collab_messages']:
            thread_id = message['Thread_ID']
            if thread_id in existing_threads:
                continue
            row = self._source.execute("SELECT * FROM OP_collab_threads WHERE Thread_ID=? AND substr(Opened_At,1,10) BETWEEN ? AND ?", (thread_id, start, end)).fetchone()
            if row:
                beneficiary = row['Requesting_Manager_ID']
                output['OP_collab_threads'].append(self._project('OP_collab_threads', row, 'Opened_At', message['employee_ids'], beneficiary))
                existing_threads.add(thread_id)
        goals = set()
        for table in ('OP_contributions', 'OP_dependency_blockers'):
            for item in output[table]:
                goal_id = item.get('Team_Goal_ID') or item.get('Blocked_Team_Goal_ID')
                if goal_id:
                    goals.add(goal_id)
                    goal = self._source.execute('SELECT Owner_Manager_ID FROM OP_team_goals WHERE Team_Goal_ID=? AND substr(Set_Date,1,10) BETWEEN ? AND ?', (goal_id, start, end)).fetchone()
                    if goal:
                        item['beneficiary_manager_id'] = goal[0]
        output['OP_team_goals'], output['OP_goal_outcomes'] = [], []
        for goal_id in sorted(goals):
            goal = self._source.execute('SELECT * FROM OP_team_goals WHERE Team_Goal_ID=? AND substr(Set_Date,1,10) BETWEEN ? AND ?', (goal_id, start, end)).fetchone()
            if not goal:
                continue
            output['OP_team_goals'].append(self._project('OP_team_goals', goal, 'Set_Date', (), goal['Owner_Manager_ID']))
            for outcome in self._source.execute('SELECT * FROM OP_goal_outcomes WHERE Team_Goal_ID=? AND substr(Measured_At,1,10) BETWEEN ? AND ?', (goal_id, start, end)):
                output['OP_goal_outcomes'].append(self._project('OP_goal_outcomes', outcome, 'Measured_At', (), goal['Owner_Manager_ID']))
        output['OP_team_plans'] = []
        for row in self._source.execute('SELECT * FROM OP_team_plans WHERE Planning_Manager_ID=? AND Plan_Date BETWEEN ? AND ?', (self.scope.manager_id, start, end)):
            output['OP_team_plans'].append(self._project('OP_team_plans', row, 'Plan_Date', (), row['Partner_Manager_ID']))
        # Team coverage is restricted by manager identity, never the display name.
        output['OP_source_coverage'] = []
        for row in self._source.execute("SELECT * FROM OP_source_coverage WHERE Home_Manager_ID=? AND Quarter IN ('2025-Q4','2026-Q1','2026-Q2')", (self.scope.manager_id,)):
            item = dict(row)
            item.pop('Data_Origin', None)
            output['OP_source_coverage'].append(item)
        self._evidence_cache = output
        return output

class FollowUpData:
    """Later observations limited to the people and anchors in saved actions."""

    def __init__(self, database, scope):
        if not isinstance(scope, FollowUpScope):
            raise TypeError("FollowUpScope is required.")
        self.scope = scope
        self._analysis = DiscoveryData(database, DiscoveryScope(scope.manager_id, _DISCOVERY_START, _DISCOVERY_END))
        if not set(scope.employee_ids) <= self._analysis._own:
            self.close()
            raise ValueError("Follow-up employees must belong to the frozen roster.")
        self._employee_ids = frozenset(scope.employee_ids)
        self._work_refs = frozenset((ref['type'], ref['id']) for ref in scope.work_refs)
        self._beneficiary_manager_ids = frozenset(scope.beneficiary_manager_ids)

    def close(self):
        self._analysis.close()

    def evidence(self):
        source = self._analysis._source
        refs = self._work_refs
        output = {}
        specs = {'HR_recognition_events': 'Recognized_At',
                 'HR_recognition_feedback': 'Interaction_At',
                 'HR_review_notes': 'Note_Date', 'HR_one_on_ones': 'Meeting_Date'}
        employees = self._employee_ids
        for table, event in specs.items():
            output[table] = []
            if table == 'HR_recognition_feedback':
                query = ("SELECT * FROM HR_recognition_feedback WHERE substr(Interaction_At,1,10) <= ? AND "
                         "(substr(Interaction_At,1,10) BETWEEN ? AND ? OR "
                         "(substr(Shared_With_Home_Manager_At,1,10) <= ? AND substr(Share_Recorded_At,1,10) BETWEEN ? AND ?))")
                params = (self.scope.end_date, self.scope.start_date, self.scope.end_date,
                          self.scope.end_date, self.scope.start_date, self.scope.end_date)
            else:
                query = f"SELECT * FROM {table} WHERE substr({event},1,10) BETWEEN ? AND ?"
                params = (self.scope.start_date, self.scope.end_date)
            for row in source.execute(query, params):
                raw = dict(row)
                if raw.get('Recorded_At') and raw['Recorded_At'][:10] > self.scope.end_date:
                    continue
                if raw.get('Employee_ID') not in employees:
                    continue
                row_refs = {(kind, raw[col]) for col, kind in _ANCHORS.items() if raw.get(col)}
                if table != 'HR_one_on_ones' and not row_refs.intersection(refs):
                    continue
                # Same beneficiary rule as DiscoveryData.evidence: the author's manager, kept apart from the masked fields.
                beneficiary = (raw['Author_Manager_ID'] or self._analysis._person_managers.get(raw.get('Author_Employee_ID'))
                               if table == 'HR_recognition_feedback' else None)
                projected = self._analysis._project(table, row, event, {raw['Employee_ID']}, beneficiary, as_of=self.scope.end_date)
                if table == 'HR_recognition_feedback':
                    projected['shared_event_date'] = raw.get('Shared_With_Home_Manager_At') if projected['shared_as_of'] else None
                output[table].append(projected)
        output['OP_team_plans'] = []
        for partner in self._beneficiary_manager_ids:
            if partner == self.scope.manager_id:
                continue
            for row in source.execute("SELECT * FROM OP_team_plans WHERE Planning_Manager_ID=? AND Partner_Manager_ID=? AND Plan_Date BETWEEN ? AND ?", (self.scope.manager_id, partner, self.scope.start_date, self.scope.end_date)):
                output['OP_team_plans'].append(self._analysis._project('OP_team_plans', row, 'Plan_Date', (), partner, as_of=self.scope.end_date))
        output['OP_source_coverage'] = []
        for row in source.execute("SELECT * FROM OP_source_coverage WHERE Home_Manager_ID=? AND Quarter='2026-Q3'", (self.scope.manager_id,)):
            item = dict(row)
            item.pop('Data_Origin', None)
            output['OP_source_coverage'].append(item)
        return output
