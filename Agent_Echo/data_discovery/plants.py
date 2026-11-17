"""Automatic plants and decoys for discovery_v1 (T1.6, plan v10 §5.7).

Runs after ops, hr and stories. Every manager's team gets 2 hidden-help cases and 1 decoy:
- teams with 15 or fewer active employees at the as-of date: both cases in the low-satisfaction slot;
- M32 and M14 (hand-built stories hold the low slot): both cases in the strong-signals slot;
- every other team: one case in each slot.
A case is help to another team: partner praise never shared with the home manager, a corroborating thread or
blocker anchored to the same work, and no recognition event. Strong-slot cases carry three work items in three
quarters (informal contribution, blocker on a beneficiary goal, informal thread plus a mention in the
beneficiary's notes) so they rank in the top 5 by stories._signal_proxy among people outside the 10 lowest.
A decoy is the same shape of help already recognized (praise shared, recognition event before the as-of date)
or help inside the home team. Expected answers go to ctx.answer_key only (Origin = automatic).

Run `python -m data_discovery.plants` from Agent_Echo for the self-check (ops + hr + stories + plants in memory).
"""
import csv
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from . import common, hr, ops, stories, text
from .ops import GENERIC_TOPICS, OUTCOMES, People, conversation, iso, message_row, thread_row, work_time

ORIGIN = "Synthetic"
AS_OF = common.AS_OF
AS_OF_END = datetime.combine(AS_OF, time(23, 59, 59))
START = common.ANALYSIS[0]
SMALL_TEAM = 15
STRONG_ONLY = ("M32", "M14")
# Partner directions the hand-built stories already use: no plant in M32 or M14 helps these teams (plus M32/M14 never benefit).
AVOID = {"M32": {"M29", "M31", "M03", "M16", "M30", "M22", "M18", "M13"} | ops.STORY_PARTNER_TEAMS,
         "M14": {"M31", "M46", "M01"} | ops.STORY_PARTNER_TEAMS}
QUARTER_DAYS = {"2025-Q4": (date(2025, 10, 6), date(2025, 12, 5)), "2026-Q1": (date(2026, 1, 6), date(2026, 3, 5)),
                "2026-Q2": (date(2026, 4, 1), date(2026, 5, 15))}  # leaves room for the replies, praise and notes before 2026-06-30
BUSINESS_OUTCOMES = ("The receiving team used the result in its own work.", "The receiving team used the answer for its next step.",
                     "The receiving team kept the result in its working notes.")
ANCHOR = {"contribution": "Contribution_ID", "thread": "Thread_ID", "blocker": "Blocker_ID"}
PROHIBITED = {"case": "That partner praise reached the home manager by 2026-06-30; that the work was already recognized "
                      "at the as-of date; any engagement, retention or productivity effect",
              "recognized": "That the work is not recognized or that the praise was not shared",
              "own_team": "Calling own-team help a cross-team contribution"}


def _hours(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _active(employee):
    return employee["Hire_Date"] <= AS_OF.isoformat() and (not employee["Termination_Date"] or employee["Termination_Date"] >= AS_OF.isoformat())


class _Builder:
    def __init__(self, ctx):
        self.ctx, self.people = ctx, People(ctx)
        self.columns = common.dictionary()
        self.team_name, self.manager_name = self.people.team_name, self.people.manager_name
        reserved = ctx.ids.reserved
        self.goals = defaultdict(list)
        for row in ctx.rows("OP_team_goals"):
            if row["Team_Goal_ID"] not in reserved:
                self.goals[row["Owner_Manager_ID"], row["Quarter"]].append(row)
        self.prf = {(r["Employee_ID"], r["Quarter"]): r for r in ctx.rows("HR_employee_performance")}
        self.pinned = set(common.pinned_rows("HR_employee_performance"))
        self.story_people = set(stories.known_people(common.story_rows()))
        members = defaultdict(list)
        for row in ctx.employees:
            members[row["Pilot_Manager_ID"]].append(row)
        self.near_miss = set(ctx.ops_near_misses) | hr._near_misses(members, {r["Employee_ID"] for r in common.pinned_rows(
            "HR_employee_performance").values()})
        self.active = {m: [e for e in team if _active(e)] for m, team in members.items()}
        self.touched = defaultdict(list)  # table -> row IDs added here, for QA

    # ---- rows ---------------------------------------------------------------------------------------------------
    def add(self, table, row):
        assert set(row) == set(self.columns[table]), (table, sorted(set(row) ^ set(self.columns[table])))
        self.ctx.rows(table).append(row)
        self.touched[table].append(row[self.columns[table][0]])

    def say(self, rng, family, need=(), **slots):
        """Render until the text carries every needed name; every planted text passes text.scan."""
        for _ in range(1000):
            out = text.render(family, rng, **slots).strip()
            out = stories._sentences(out)  # templates keep the outcome slot lowercase after a full stop
            if all(n in out for n in need) and not text.scan(out):
                return out
        raise RuntimeError(f"no {family} template carries {need}")

    def clean(self, value):
        assert not text.scan(value), value
        return value

    # ---- work items ---------------------------------------------------------------------------------------------
    def thread(self, rng, helper, home, beneficiary, day, topic):
        """An informal thread (no work request) in which `helper` answers `beneficiary`'s request."""
        people = self.people
        for _ in range(200):
            requester = (people.pick(rng, beneficiary, day, exclude=(helper,)) or beneficiary)
            opened = work_time(rng, day, 0)
            messages = conversation(rng, people, opened, requester, helper, beneficiary, topic, True)
            last = messages[-1][0]
            if (last <= AS_OF_END and people.name[helper] in messages[0][2]
                    and (requester.startswith("M") or people.active(requester, day, last.date()))):
                break
        else:
            raise RuntimeError("no thread fits the window")
        thread_id = self.ctx.ids.new("THR")
        closed = min(last + timedelta(hours=4), AS_OF_END)
        self.add("OP_collab_threads", thread_row(
            thread_id, people, opened, beneficiary, home, "" if requester.startswith("M") else requester,
            requester if requester.startswith("M") else "", self.clean(topic), None, closed))
        ids = [thread_id]
        for sent_at, author, body, mentioned in messages:
            mentioned = tuple(e for e in mentioned if people.name[e] in body)
            row = message_row(self.ctx.ids.new("MSG"), people, thread_id, sent_at, author, self.clean(body), mentioned)
            self.add("OP_collab_messages", row)
            ids.append(row["Message_ID"])
        return {"kind": "thread", "id": thread_id, "end": last.date(), "topic": topic, "ids": ids}

    def blocker(self, rng, helper, home, beneficiary, day, topic, with_goal):
        people = self.people
        goals = self.goals.get((beneficiary, common.quarter_of(day)))
        goal = rng.choice(goals) if with_goal and goals else None
        raised = work_time(rng, day, 0)
        resolved = raised + timedelta(days=rng.randint(3, 9), hours=rng.randint(-3, 3))
        assert resolved.date() <= AS_OF
        goal_text = goal["Metric_Name"] if goal else "the current milestone"
        days = (resolved.date() - raised.date()).days
        row = {"Blocker_ID": self.ctx.ids.new("BLK"), "Raised_At": iso(raised),
               "Blocked_Team": self.team_name[beneficiary], "Blocked_Manager_ID": beneficiary,
               "Blocked_Team_Goal_ID": goal["Team_Goal_ID"] if goal else "",
               "Blocking_Team": self.team_name[home], "Blocking_Manager_ID": home,
               "Blocker_Description": self.say(rng, "blocker_description", blocked_team=self.team_name[beneficiary],
                                               blocking_team=self.team_name[home], goal=goal_text),
               "Work_Request_ID": "", "Resolved_By_Employee_ID": helper, "Resolved_At": iso(resolved), "Days_Blocked": days,
               "Resolution_Note": self.say(rng, "blocker_resolution", need=(people.name[helper],),
                                           helper=people.name[helper], days=days, goal=goal_text),
               "Data_Origin": ORIGIN}
        self.add("OP_dependency_blockers", row)
        ids = [row["Blocker_ID"]] + ([goal["Team_Goal_ID"]] if goal else [])
        return {"kind": "blocker", "id": row["Blocker_ID"], "end": resolved.date(), "topic": topic, "ids": ids}

    def contribution(self, rng, helper, home, beneficiary, day, topic):
        people, quarter = self.people, common.quarter_of(day)
        goals = self.goals.get((beneficiary, quarter))
        goal = rng.choice(goals) if goals else None
        row = {"Contribution_ID": self.ctx.ids.new("CON"), "Work_Request_ID": "",
               "Project_Name": self.clean(f"{topic.capitalize()} - {self.team_name[beneficiary]}"),
               "Employee_ID": helper, "Employee_Name": people.name[helper], "Home_Team": self.team_name[home],
               "Beneficiary_Team": self.team_name[beneficiary], "Contribution_Date": day.isoformat(),
               "Contribution_Summary": self.say(rng, "contribution_summary", employee=people.name[helper],
                                                beneficiary_team=self.team_name[beneficiary], topic=topic),
               "Business_Outcome": rng.choice(BUSINESS_OUTCOMES),
               "Evidence_Description": self.clean(f"Accepted a short written summary of the {topic} in the review on "
                                                  f"{day.isoformat()}; no external document is attached."),
               "Team_Goal_ID": goal["Team_Goal_ID"] if goal else "", "Effort_Hours": _hours(rng.randint(4, 24) / 2),
               "Request_Channel": "informal", "Data_Origin": ORIGIN}
        self.add("OP_contributions", row)
        ids = [row["Contribution_ID"]] + ([goal["Team_Goal_ID"]] if goal else [])
        return {"kind": "contribution", "id": row["Contribution_ID"], "end": day, "topic": topic, "ids": ids}

    # ---- evidence about a work item -----------------------------------------------------------------------------
    def feedback(self, rng, helper, home, author_team, item, day, shared=False):
        """Partner praise from author_team about the item (home manager's own note when author_team == home)."""
        people = self.people
        own = author_team == home
        employee_author = None if own or rng.random() < 0.6 else people.pick(rng, author_team, day)
        written = hr.at(day, rng)
        row = {"Interaction_ID": self.ctx.ids.new("INT"), "Interaction_At": hr.stamp(written),
               "Interaction_Type": "Partner feedback",
               "Author_Type": "home_manager" if own else "partner_employee" if employee_author else "partner_manager",
               "Contribution_ID": "", "Thread_ID": "", "Blocker_ID": "", "Incident_ID": "", "Work_Request_ID": "",
               "Employee_ID": helper, "Employee_Name": people.name[helper],
               "Author_Manager_ID": "" if employee_author else author_team,
               "Author_Employee_ID": employee_author or "",
               "Author_Name": people.name[employee_author] if employee_author else people.manager_name[author_team],
               "Author_Team": self.team_name[author_team], "Recipient_Manager_ID": home,
               "Recipient_Manager_Name": people.manager_name[home], "Interaction_Date": day.isoformat(),
               "Channel": "Quarterly partner review",
               "Message": self.say(rng, "feedback_partner", need=(people.name[helper],), employee=people.name[helper],
                                   beneficiary_team=self.team_name[author_team], work=f"the {item['topic']}",
                                   outcome=rng.choice(OUTCOMES)),
               "Shared_With_Home_Manager": "No", "Shared_With_Home_Manager_At": "", "Share_Recorded_At": "",
               "Record_Coverage": "complete", "Data_Origin": ORIGIN}
        row[ANCHOR[item["kind"]]] = item["id"]
        if shared:
            at = written if own else min(written + timedelta(days=rng.randint(1, 3), minutes=rng.randint(0, 50)), AS_OF_END)
            row.update(Shared_With_Home_Manager="Yes", Shared_With_Home_Manager_At=hr.stamp(at),
                       Share_Recorded_At=hr.stamp(min(at + timedelta(minutes=rng.randint(0, 20)), AS_OF_END)))
        self.add("HR_recognition_feedback", row)
        return row["Interaction_ID"]

    def mention(self, rng, helper, beneficiary, item, day):
        row = {"Mention_ID": self.ctx.ids.new("MTM"), "Meeting_Date": day.isoformat(), "Meeting_Team": self.team_name[beneficiary],
               "Meeting_Manager_ID": beneficiary, "Mentioned_Employee_ID": helper,
               "Note_Text": self.say(rng, "meeting_mention", need=(self.people.name[helper],), helper=self.people.name[helper],
                                     meeting_team=self.team_name[beneficiary], topic=item["topic"]),
               "Contribution_ID": "", "Thread_ID": "", "Blocker_ID": "", "Incident_ID": "", "Data_Origin": ORIGIN}
        row[ANCHOR[item["kind"]]] = item["id"]
        self.add("OP_meeting_mentions", row)
        return row["Mention_ID"]

    def recognition(self, rng, helper, home, item, day):
        row = {"Recognition_ID": self.ctx.ids.new("REC"), "Employee_ID": helper, "Given_By_Manager_ID": home,
               "Recognition_Type": rng.choice(("written_commendation", "public_shoutout", "spot_award")), "Visibility": "team",
               "Recognized_At": hr.stamp(datetime.combine(day, time(rng.randint(9, 17), rng.randint(0, 59)))),
               "Citation_Text": self.say(rng, "recognition_citation", employee=self.people.name[helper], work=f"the {item['topic']}"),
               "Contribution_ID": "", "Thread_ID": "", "Blocker_ID": "", "Incident_ID": "", "Data_Origin": ORIGIN}
        row[ANCHOR[item["kind"]]] = item["id"]
        self.add("HR_recognition_events", row)
        return row["Recognition_ID"]

    # ---- people and pulse ---------------------------------------------------------------------------------------
    def pulse(self, eid):
        return int(self.prf[eid, "2026-Q2"]["Pulse_Score"])

    def set_pulse(self, eid, value):
        row = self.prf[eid, "2026-Q2"]
        assert row["Performance_ID"] not in self.pinned, row["Performance_ID"]
        row["Pulse_Score"] = str(value)

    def eligible(self, m):
        """Active, hired before the window, no story or near-miss role, with a 2026-Q2 pulse row."""
        return sorted(e["Employee_ID"] for e in self.active[m] if e["Hire_Date"] <= START.isoformat()
                      and e["Employee_ID"] not in self.story_people and e["Employee_ID"] not in self.near_miss
                      and (e["Employee_ID"], "2026-Q2") in self.prf)

    def force_low(self, m, eid):
        """Lower only this person's latest pulse until they are among the 10 lowest, without displacing a story person."""
        before = set(stories.lowest_satisfaction(self.ctx, m)) & self.story_people
        old = self.prf[eid, "2026-Q2"]["Pulse_Score"]
        for value in (2, 1):
            self.set_pulse(eid, value)
            low = stories.lowest_satisfaction(self.ctx, m)
            if eid in low and before <= set(low):
                return True
        self.prf[eid, "2026-Q2"]["Pulse_Score"] = old
        return False

    def beneficiaries(self, rng, home, count):
        pool = sorted(m for m in self.team_name if m != home and m not in STRONG_ONLY and self.team_name[m] != self.team_name[home]
                      and m not in AVOID.get(home, ()))
        return rng.sample(pool, count)


# ---- Building ------------------------------------------------------------------------------------------------------

def _slots(manager, size):
    if manager in STRONG_ONLY:
        return ["strong_signals", "strong_signals"]
    return ["low_satisfaction"] * 2 if size <= SMALL_TEAM else ["low_satisfaction", "strong_signals"]


def _choose(b, rng, m, slots):
    """People for the slots plus the decoy; edits only the chosen person's latest pulse when needed."""
    taken, chosen = set(), []
    low = lambda: set(stories.lowest_satisfaction(b.ctx, m))
    floor = 4 if m == "M14" else 3
    for slot in sorted(slots, key=lambda s: s != "strong_signals"):
        pool, ten = [e for e in b.eligible(m) if e not in taken], low()
        if slot == "strong_signals":
            options = [e for e in pool if e not in ten and b.pulse(e) >= floor] or [e for e in pool if e not in ten]
            eid = rng.choice(options)
            if b.pulse(eid) < floor:
                b.set_pulse(eid, floor)  # raised from outside the 10 lowest, so the 10 lowest do not change
        else:
            options = [e for e in pool if e in ten]
            if options:
                eid = rng.choice(options)
            else:
                shuffled = list(pool)
                rng.shuffle(shuffled)
                eid = next((e for e in shuffled if b.force_low(m, e)), None)
                assert eid, f"{m}: nobody can enter the 10 lowest"
        taken.add(eid)
        chosen.append((slot, eid))
    pool, ten = [e for e in b.eligible(m) if e not in taken], low()
    decoy = rng.choice([e for e in pool if e in ten] or pool)
    return chosen, decoy


def _case(b, rng, m, k, slot, eid, beneficiary):
    """Build one case; returns the answer-key row (Entry_Slot as placed)."""
    people, ctx = b.people, b.ctx
    topics = rng.sample(GENERIC_TOPICS, 3)
    if slot == "strong_signals":
        quarters = list(QUARTER_DAYS)
        rng.shuffle(quarters)
        plan = list(zip(("contribution", "blocker", "thread"), quarters))
    else:
        plan = [(rng.choice(("blocker", "thread")), rng.choice(list(QUARTER_DAYS)))]
    items, evidence = [], []
    for (kind, quarter), topic in zip(plan, topics):
        first, last = QUARTER_DAYS[quarter]
        day = first + timedelta(days=rng.randrange((last - first).days + 1))
        if kind == "thread":
            item = b.thread(rng, eid, m, beneficiary, day, topic)
        elif kind == "blocker":
            item = b.blocker(rng, eid, m, beneficiary, day, topic, with_goal=slot == "strong_signals" or rng.random() < 0.5)
        else:
            item = b.contribution(rng, eid, m, beneficiary, day, topic)
        praise = item["end"] + timedelta(days=rng.randint(2, 9))
        evidence += item["ids"] + [b.feedback(rng, eid, m, beneficiary, item, praise)]
        if slot == "low_satisfaction":  # a second praise for the same work
            evidence.append(b.feedback(rng, eid, m, beneficiary, item, min(praise + timedelta(days=rng.randint(10, 25)), AS_OF)))
        elif kind == "thread":
            evidence.append(b.mention(rng, eid, beneficiary, item, item["end"] + timedelta(days=rng.randint(5, 14))))
        items.append(item)
    followup = "A1:not_yet;A4:unknown" if m == "M41" else "A1:not_yet;A4:not_yet"  # gate 4: M41's partial 2026-Q3 feedback coverage
    return {"Case_ID": f"PL-{m}-{k}", "Origin": "automatic", "Kind": "case", "Manager_ID": m, "Subject_Kind": "person",
            "Employee_IDs": eid, "Beneficiary_Team": beneficiary, "Entry_Slot": slot, "Evidence_IDs": ";".join(evidence),
            "Work_Refs": ";".join(f"{i['kind']}:{i['id']}" for i in items), "Expected_Result": "found",
            "Expected_Actions": "A1;A4", "Expected_Followup": followup, "Prohibited_Claim": PROHIBITED["case"],
            "Notes": f"{len(items)} work item(s) for {beneficiary}; praise never shared; no recognition event; latest pulse {b.pulse(eid)}."
                     + (" Gate 4: an accepted A4 reads unknown against the partial M41 HR_recognition_feedback 2026-Q3 row."
                        if m == "M41" else "")}


def _decoy(b, rng, m, eid, beneficiary, own_team):
    ctx = b.ctx
    quarter = rng.choice(list(QUARTER_DAYS))
    first, last = QUARTER_DAYS[quarter]
    day = first + timedelta(days=rng.randrange((last - first).days + 1))
    topic = rng.choice(GENERIC_TOPICS)
    if own_team:
        item = b.thread(rng, eid, m, m, day, topic)
        evidence = item["ids"] + [b.feedback(rng, eid, m, m, item, item["end"] + timedelta(days=rng.randint(2, 9)), shared=True)]
        claim, result, kind = PROHIBITED["own_team"], "not_found", "own-team help"
        beneficiary = m
    else:
        item = (b.thread if rng.random() < 0.5 else lambda *a: b.blocker(*a, with_goal=False))(rng, eid, m, beneficiary, day, topic)
        praise = item["end"] + timedelta(days=rng.randint(2, 6))
        evidence = item["ids"] + [b.feedback(rng, eid, m, beneficiary, item, praise + timedelta(days=n), shared=True)
                                  for n in range(rng.randint(1, 2))]
        evidence.append(b.recognition(rng, eid, m, item, praise + timedelta(days=rng.randint(4, 9))))
        claim, kind = PROHIBITED["recognized"], "recognized help"
    return {"Case_ID": f"PD-{m}", "Origin": "automatic", "Kind": "decoy", "Manager_ID": m, "Subject_Kind": "person",
            "Employee_IDs": eid, "Beneficiary_Team": beneficiary, "Entry_Slot": "", "Evidence_IDs": ";".join(evidence),
            "Work_Refs": f"{item['kind']}:{item['id']}", "Expected_Result": "not_found", "Expected_Actions": "",
            "Expected_Followup": "", "Prohibited_Claim": claim,
            "Notes": f"Decoy: {kind}, {item['kind']} work; praise shared with the home manager"
                     + ("; recognition event before 2026-07-01." if not own_team else ".")}


def signal_key(types, tables, hidden, eid):
    """The proxy's sort key (stories._signal_proxy): more types, then tables, then items, then the latest date."""
    return (-len(types[eid]), -len(tables[eid]), -len(hidden[eid]),
            -int(max((d for d, _ in hidden[eid]), default="0000-00-00").replace("-", "")))


def apply(ctx):
    b = _Builder(ctx)
    header = None
    with (common.PRIVATE / "QA_discovery_v1_answer_key.csv").open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream))
    decoys, ctx.plant_info = {}, []
    for manager in sorted(b.team_name):
        rng = common.rng(f"plants:{manager}")
        slots = _slots(manager, len(b.active[manager]))
        chosen, decoy = _choose(b, rng, manager, slots)
        targets = b.beneficiaries(rng, manager, 3)
        for k, (slot, eid) in enumerate(chosen, 1):
            row = _case(b, rng, manager, k, slot, eid, targets[k - 1])
            ctx.answer_key.append({column: row[column] for column in header})
            ctx.plant_info.append(row)
        row = _decoy(b, rng, manager, decoy, targets[2], own_team=manager in STRONG_ONLY or rng.random() < 0.4)
        decoys[manager] = row
        ctx.plant_info.append(row)
    # Decoy slots as placed: the 10 lowest, else the proxy's top 5, else a direct question only (whole team in small teams).
    for manager, row in decoys.items():
        eid = row["Employee_IDs"]
        if len(b.active[manager]) <= SMALL_TEAM or eid in stories.lowest_satisfaction(ctx, manager):
            row["Entry_Slot"] = "low_satisfaction"
        else:
            ranked = stories._signal_proxy(ctx, manager)[0]
            row["Entry_Slot"] = "strong_signals" if eid in ranked[:5] else "direct_question_only"
        ctx.answer_key.append({column: row[column] for column in header})
    ctx.plant_touched = dict(b.touched)  # QA only; never written


# ---- Self-check ----------------------------------------------------------------------------------------------------

def _self_check():
    import time as clock
    began = clock.perf_counter()
    ctx = common.load_context()
    ops.generate(ctx)
    hr.generate(ctx)
    stories.apply(ctx)
    pool_before = {}  # protected story people in each team's pool before the plants
    protected = set(stories.known_people(common.story_rows()))
    managers = sorted(m["Manager_ID"] for m in ctx.managers)
    for m in managers:
        low = set(stories.lowest_satisfaction(ctx, m))
        pool_before[m] = (low | set(stories._signal_proxy(ctx, m)[0][:5])) & protected
    built = clock.perf_counter()
    apply(ctx)
    elapsed = clock.perf_counter() - built
    t, columns = ctx.tables, common.dictionary()
    keys = {"OP_collab_threads": "Thread_ID", "OP_collab_messages": "Message_ID", "OP_dependency_blockers": "Blocker_ID",
            "OP_contributions": "Contribution_ID", "HR_recognition_feedback": "Interaction_ID", "HR_recognition_events": "Recognition_ID",
            "OP_meeting_mentions": "Mention_ID", "OP_team_goals": "Team_Goal_ID"}
    info = ctx.plant_info
    cases, decoys = [r for r in info if r["Kind"] == "case"], [r for r in info if r["Kind"] == "decoy"]
    assert len(cases) == 120 and len(decoys) == 60, (len(cases), len(decoys))
    assert len(ctx.answer_key) == 14 + 180 and Counter(r["Origin"] for r in ctx.answer_key) == {"hand_built": 14, "automatic": 180}
    for m in managers:
        assert sum(r["Manager_ID"] == m for r in cases) == 2 and sum(r["Manager_ID"] == m for r in decoys) == 1, m

    # Columns, unique IDs, reserved IDs, text and dates of every row added here.
    added = {table: set(ids) for table, ids in ctx.plant_touched.items()}
    for table, key in keys.items():
        ids = [r[key] for r in t[table]]
        assert len(ids) == len(set(ids)), table
        assert all(set(r) == set(columns[table]) for r in t[table]), table
        assert not (added.get(table, set()) & ctx.ids.reserved), table
    by_id = {table: {r[key]: r for r in t[table]} for table, key in keys.items()}
    window = ("2025-10-01", f"{AS_OF.isoformat()}T23:59:59")
    date_columns = {"OP_collab_threads": ("Opened_At", "Closed_At"), "OP_collab_messages": ("Sent_At",),
                    "OP_dependency_blockers": ("Raised_At", "Resolved_At"), "OP_contributions": ("Contribution_Date",),
                    "HR_recognition_feedback": ("Interaction_At", "Interaction_Date", "Shared_With_Home_Manager_At", "Share_Recorded_At"),
                    "HR_recognition_events": ("Recognized_At",), "OP_meeting_mentions": ("Meeting_Date",)}
    for table, ids in added.items():
        for row_id in ids:
            r = by_id[table][row_id]
            for column in date_columns.get(table, ()):
                assert not r[column] or window[0] <= r[column] <= window[1], (table, row_id, column, r[column])
            for column in stories.TEXT_COLUMNS.get(table, ()):
                assert not text.scan(str(r[column])), (table, row_id, column)
            for column in ("Team_Goal_ID", "Blocked_Team_Goal_ID"):
                assert not r.get(column) or r[column] in by_id["OP_team_goals"], (row_id, column)
    anchor_tables = {"Contribution_ID": by_id["OP_contributions"], "Thread_ID": by_id["OP_collab_threads"],
                     "Blocker_ID": by_id["OP_dependency_blockers"]}
    for table in ("HR_recognition_feedback", "HR_recognition_events", "OP_meeting_mentions"):
        for row_id in added[table]:
            r = by_id[table][row_id]
            filled = [c for c in (*anchor_tables, "Incident_ID") if r[c]]
            assert len(filled) == 1 and filled[0] in anchor_tables and r[filled[0]] in anchor_tables[filled[0]], (table, row_id)
    for row_id in added["OP_collab_messages"]:
        r = by_id["OP_collab_messages"][row_id]
        thread = by_id["OP_collab_threads"][r["Thread_ID"]]
        assert thread["Opened_At"] <= r["Sent_At"] <= thread["Closed_At"] and not thread["Work_Request_ID"], row_id
        for eid in filter(None, r["Mentioned_Employee_IDs"].split(";")):
            assert ctx.employee(eid)["Employee_Name"] in r["Message_Text"], row_id

    # Share and coverage rules; no recognition for case work before 2026-07-01.
    events = t["HR_recognition_events"]
    recognized = {(r["Employee_ID"], ref) for r in events for ref in stories._work_refs(r)}
    feedback_added = [by_id["HR_recognition_feedback"][i] for i in added["HR_recognition_feedback"]]
    assert all(r["Record_Coverage"] == "complete" for r in feedback_added)
    for r in feedback_added:
        shared, recorded = r["Shared_With_Home_Manager_At"], r["Share_Recorded_At"]
        assert bool(shared) == bool(recorded) and r["Shared_With_Home_Manager"] == ("Yes" if shared else "No")
        assert not shared or r["Interaction_At"] <= shared <= recorded <= window[1], r["Interaction_ID"]
    ids_of = {"case": set(), "decoy": set()}
    for row in info:
        refs = {tuple(ref.split(":")) for ref in row["Work_Refs"].split(";")}
        evidence = set(row["Evidence_IDs"].split(";"))
        assert refs and all(ref[1] in {i for i in evidence} for ref in refs), row["Case_ID"]
        feedback = [by_id["HR_recognition_feedback"][e] for e in evidence if e in by_id["HR_recognition_feedback"]]
        assert feedback and all(f["Employee_ID"] == row["Employee_IDs"] and f["Record_Coverage"] == "complete" for f in feedback)
        mine = {(row["Employee_IDs"], ref) for ref in refs}
        if row["Kind"] == "case":
            assert not (mine & recognized), row["Case_ID"]
            assert all(not f["Shared_With_Home_Manager_At"] or f["Shared_With_Home_Manager_At"] > window[1] for f in feedback)
            assert all(f["Author_Type"] != "home_manager" and f["Author_Manager_ID"] != f["Recipient_Manager_ID"] for f in feedback)
            assert row["Beneficiary_Team"] != row["Manager_ID"] and row["Entry_Slot"] in ("low_satisfaction", "strong_signals")
        else:
            own = row["Beneficiary_Team"] == row["Manager_ID"]
            assert all(f["Shared_With_Home_Manager_At"] for f in feedback)
            assert own or mine <= recognized and all(r["Recognized_At"] < "2026-07-01" for r in events
                                                     if r["Recognition_ID"] in evidence)
            assert own or any(e in {r["Recognition_ID"] for r in events} for e in evidence)
    # Gate 4: an M41 plant with praise never shared through 2026-09-30, against the one partial coverage row.
    partial = [(r["Source_Table"], r["Home_Manager_ID"], r["Quarter"]) for r in t["OP_source_coverage"] if r["Coverage_Status"] != "complete"]
    assert partial == [("HR_recognition_feedback", "M41", "2026-Q3")]
    m41 = [r for r in cases if r["Manager_ID"] == "M41"]
    assert m41 and all(r["Expected_Followup"] == "A1:not_yet;A4:unknown" for r in m41)
    assert all(not by_id["HR_recognition_feedback"][e]["Shared_With_Home_Manager_At"]
               for r in m41 for e in r["Evidence_IDs"].split(";") if e in by_id["HR_recognition_feedback"])

    # Slots: small-team split, M32 and M14, pulses, pool membership.
    size = {m: sum(_active(e) for e in ctx.team(m)) for m in managers}
    split = Counter(r["Entry_Slot"] for r in cases)
    for m in managers:
        slots = sorted(r["Entry_Slot"] for r in cases if r["Manager_ID"] == m)
        want = ["strong_signals"] * 2 if m in STRONG_ONLY else ["low_satisfaction"] * 2 if size[m] <= SMALL_TEAM else \
            ["low_satisfaction", "strong_signals"]
        assert slots == sorted(want), (m, slots)
    pulse = {(r["Employee_ID"], r["Quarter"]): int(r["Pulse_Score"]) for r in t["HR_employee_performance"]}
    story_people = set(stories.known_people(common.story_rows()))
    near = set(ctx.ops_near_misses)
    failures, ranks, low_ok, strong_ok, strong_top = [], [], 0, 0, 0
    proxy = {m: stories._signal_proxy(ctx, m) for m in managers}
    for r in cases + decoys:
        eid, m = r["Employee_IDs"], r["Manager_ID"]
        employee = ctx.employee(eid)
        assert _active(employee) and eid not in story_people and eid not in near, (r["Case_ID"], eid)
        if r["Kind"] == "case":
            team_names = {x["Manager_ID"]: x["Primary_Team"] for x in ctx.managers}
            assert team_names[r["Beneficiary_Team"]] != team_names[m], r["Case_ID"]
            assert m not in STRONG_ONLY or r["Beneficiary_Team"] not in AVOID[m] | set(STRONG_ONLY), r["Case_ID"]
    for r in cases:
        eid, m, slot = r["Employee_IDs"], r["Manager_ID"], r["Entry_Slot"]
        low, (ranked, types, tables, hidden) = stories.lowest_satisfaction(ctx, m), proxy[m]
        if slot == "low_satisfaction":
            if eid in low:
                low_ok += 1
            else:
                failures.append((r["Case_ID"], "not in the 10 lowest"))
            if m == "M32":
                failures.append((r["Case_ID"], "M32 low slot"))
        else:
            assert pulse[eid, "2026-Q2"] >= (4 if m == "M14" else 3), (r["Case_ID"], pulse[eid, "2026-Q2"])
            assert eid not in low, r["Case_ID"]
            assert len(types[eid]) >= 2 and len({tbl for tbl in tables[eid]}) >= 2, r["Case_ID"]
            rank = ranked.index(eid) + 1 if eid in ranked else None
            ranks.append(rank)
            if rank and rank <= 5:
                strong_ok += 1
            else:
                failures.append((r["Case_ID"], f"strong rank {rank}"))
    for r in decoys:  # a decoy never outranks the weakest strong plant in its team
        m, eid = r["Manager_ID"], r["Employee_IDs"]
        ranked, types, tables, hidden = proxy[m]
        strong = [c["Employee_IDs"] for c in cases if c["Manager_ID"] == m and c["Entry_Slot"] == "strong_signals"]
        if strong and eid in ranked:
            assert all(signal_key(types, tables, hidden, s) < signal_key(types, tables, hidden, eid) for s in strong), r["Case_ID"]
    # M32 and M14 strong slots; story alignment; P5 and story people keep their pools.
    plants = lambda m: {r["Employee_IDs"] for r in cases if r["Manager_ID"] == m}
    ranked32, types32, tables32, hidden32 = proxy["M32"]
    assert set(ranked32[:5]) == {"E0970", "E0107", "E0561"} | plants("M32"), ranked32[:7]
    assert not {"E0815", "E0776"} & set(ranked32[:5])
    ranked14 = proxy["M14"][0]
    assert set(ranked14[:3]) == {"E0001"} | plants("M14"), ranked14[:5]
    assert set(stories.lowest_satisfaction(ctx, "M32")) == {"E0010", "E2156", "E0728", "E1401", "E1586", "E1748", "E1333", "E2233", "E1383", "E2198"}
    assert "E0001" not in stories.lowest_satisfaction(ctx, "M14") and pulse["E0001", "2026-Q2"] == 4
    story32 = {e["Employee_ID"] for e in ctx.team("M32") if _active(e)} - story_people - plants("M32")
    assert all(pulse[e, "2026-Q2"] >= 3 for e in story32 | plants("M32"))
    others14 = [e for e in (x["Employee_ID"] for x in ctx.team("M14") if _active(x)) if e != "E0001" and e not in plants("M14")]
    assert sum(pulse[e, "2026-Q2"] <= 3 for e in others14) >= 10
    for m in managers:
        now = (set(stories.lowest_satisfaction(ctx, m)) | set(proxy[m][0][:5])) & protected
        if not pool_before[m] <= now:
            failures.append((m, f"story people left the pool: {sorted(pool_before[m] - now)}"))
    print(f"runtime: plants {elapsed:.1f}s; ops+hr+stories+plants+checks {clock.perf_counter() - began:.1f}s")
    print(f"cases {len(cases)}, decoys {len(decoys)}; split {dict(split)}")
    print(f"small teams ({sum(s <= SMALL_TEAM for s in size.values())}): "
          f"{sorted(m for m in managers if size[m] <= SMALL_TEAM)}")
    print(f"low plants in the 10 lowest: {low_ok}/{split['low_satisfaction']}; "
          f"strong plants in the proxy top 5 outside the 10 lowest: {strong_ok}/{split['strong_signals']}; ranks {dict(sorted(Counter(ranks).items(), key=lambda kv: (kv[0] is None, kv[0] or 0)))}")
    print("decoy types:", dict(Counter(r["Notes"].split(",")[0] for r in decoys)),
          "| slots:", dict(Counter(r["Entry_Slot"] for r in decoys)))
    print("failures:", failures or "none")
    assert not failures, failures
    print("plants self-check: OK")


if __name__ == "__main__":
    _self_check()
