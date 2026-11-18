"""Background operations tables for discovery_v1 (T1.2, plan v10 §5.4).

Fills OP_team_goals, OP_goal_outcomes, OP_collab_threads, OP_collab_messages, OP_dependency_blockers,
OP_incident_handoffs and OP_meeting_mentions for the whole organization, 2025-10-01 to 2026-09-30.

Signal rarity (plan §3.3, §5.6): ordinary background help is visible. Threads with an employee helper
always carry their formal work request; informal threads are answered by the other team's manager or
stay unanswered; meeting notes mention a team's own people; a blocker resolved by another team does not
name the blocked goal. Only "near-miss" people (about 5% per team, 2.5% in M32 and M14, never a story
person) get exactly ONE extra signal, once, in one analysis quarter: an informal help thread, a mention
in another team's notes, or the resolution of a blocker on another team's goal.
"""
from datetime import date, datetime, time, timedelta

from . import common, text

START, END = common.ANALYSIS[0], common.FOLLOW_UP[1]
END_AT = datetime.combine(END, time(23, 59))
ANALYSIS_QUARTERS = ("2025-Q4", "2026-Q1", "2026-Q2")
STORY_TEAMS = ("M32", "M14")
# Partner teams of the hand-built stories (STORIES_README "Precedence with automatic plants", rule 3):
# background in M32 and M14 sends no informal, blocker or incident help their way.
STORY_PARTNER_TEAMS = {"M29", "M31", "M03", "M16", "M30", "M22", "M18", "M13", "M15"}
NEAR_MISS_RATE = {"default": 0.05, "story_team": 0.025}
ORIGIN = "Synthetic"

# name, unit, direction, baseline range, ratio metric
METRICS = (
    ("on-time delivery rate", "percent", "increase", (68, 88), True),
    ("first-contact resolution rate", "percent", "increase", (55, 80), True),
    ("forecast accuracy", "percent", "increase", (70, 90), True),
    ("report error rate", "percent", "decrease", (4, 12), True),
    ("automated check coverage", "percent", "increase", (40, 75), True),
    ("average resolution time", "days", "decrease", (3, 10), False),
    ("handoff cycle time", "days", "decrease", (2, 8), False),
    ("open backlog items", "count", "decrease", (40, 160), False),
    ("escalations per month", "count", "decrease", (10, 45), False),
    ("customer satisfaction score", "score", "increase", (3.5, 4.3), False),
)
OUTCOMES = ("the numbers lined up", "the handoff went through", "the review went ahead", "the queue moved again",
            "the file was usable", "the customer call went fine", "the change went live", "the report went out")
GENERIC_TOPICS = ("data export question", "access to a shared report", "handoff checklist", "case routing rule",
                  "dashboard filter", "renewal list cleanup", "config change review", "weekly numbers check",
                  "integration test window", "template update", "account mapping", "release timing")


def iso(moment):
    return moment.isoformat(timespec="seconds")


def work_time(rng, day, after_hours=0.04):
    """A timestamp on a day, mostly in business hours."""
    hour = rng.choice((19, 20, 21, 22, 6, 7)) if rng.random() < after_hours else rng.randint(8, 17)
    return datetime.combine(day, time(hour, rng.randrange(0, 60, 5)))


def random_day(rng, start=START, end=END):
    return start + timedelta(days=rng.randrange((end - start).days + 1))


class People:
    """Roster lookups: active employees per team, help-propensity weights and display names."""

    def __init__(self, ctx):
        weights_rng = common.rng("ops:weights")
        self.team_name = {m["Manager_ID"]: m["Primary_Team"] for m in ctx.managers}
        self.manager_name = {m["Manager_ID"]: m["Manager_Name"] for m in ctx.managers}
        self.managers = list(self.team_name)
        self.home, self.name, self.span, self.weight = {}, {}, {}, {}
        for e in ctx.employees:
            eid = e["Employee_ID"]
            self.home[eid], self.name[eid] = e["Pilot_Manager_ID"], e["Employee_Name"]
            self.span[eid] = (date.fromisoformat(e["Hire_Date"]),
                              date.fromisoformat(e["Termination_Date"]) if e["Termination_Date"] else date.max)
            # Heavy-tailed: a few people help a lot, most a little.
            self.weight[eid] = weights_rng.lognormvariate(0, 0.9)
        self.members = {m: [eid for eid in self.home if self.home[eid] == m and self.active(eid, START, END)]
                        for m in self.managers}
        self.activity = {m: weights_rng.lognormvariate(0, 0.35) for m in self.managers}
        self.partners = {}
        for m in self.managers:
            others = [o for o in self.managers if o != m and not (m in STORY_TEAMS and o in STORY_PARTNER_TEAMS)]
            chosen = weights_rng.sample(others, 9)
            self.partners[m] = (chosen, [1 / (rank + 1) for rank in range(len(chosen))])

    def active(self, eid, first, last=None):
        hired, left = self.span[eid]
        return hired <= first and (last or first) <= left

    def pick(self, rng, manager, day, exclude=()):
        """A weighted active member of a team on a day, or None."""
        people = [eid for eid in self.members[manager] if eid not in exclude and self.active(eid, day)]
        return rng.choices(people, weights=[self.weight[eid] for eid in people])[0] if people else None

    def partner(self, rng, manager):
        chosen, weights = self.partners[manager]
        return rng.choices(chosen, weights=weights)[0]


def thread_row(thread_id, people, opened_at, requesting, responding, requester_employee, requester_manager,
               topic, work_request_id, closed_at):
    """One OP_collab_threads row; requester_employee or requester_manager is filled, not both."""
    return {"Thread_ID": thread_id, "Opened_At": iso(opened_at),
            "Requesting_Team": people.team_name[requesting], "Requesting_Manager_ID": requesting,
            "Responding_Team": people.team_name[responding], "Responding_Manager_ID": responding,
            "Requester_Employee_ID": requester_employee or "", "Requester_Manager_ID": requester_manager or "",
            "Topic": topic, "Work_Request_ID": work_request_id or "", "Closed_At": iso(closed_at) if closed_at else "",
            "Data_Origin": ORIGIN}


def message_row(message_id, people, thread_id, sent_at, author, message_text, mentioned=()):
    """One OP_collab_messages row; author is an Employee_ID (E...) or a Manager_ID (M...)."""
    is_manager = author.startswith("M")
    return {"Message_ID": message_id, "Thread_ID": thread_id, "Sent_At": iso(sent_at),
            "Author_Type": "manager" if is_manager else "employee",
            "Author_Employee_ID": "" if is_manager else author, "Author_Manager_ID": author if is_manager else "",
            "Author_Team": people.team_name[author if is_manager else people.home[author]],
            "Message_Text": message_text, "Mentioned_Employee_IDs": ";".join(mentioned), "Data_Origin": ORIGIN}


def label(people, who):
    return people.manager_name[who] if who.startswith("M") else people.name[who]


def conversation(rng, people, opened_at, requester, helper, beneficiary, topic, thanks):
    """Messages of one thread as (sent_at, author, text, mentioned); helper None means no employee answers."""
    slots = {"requester": label(people, requester), "beneficiary_team": people.team_name[beneficiary],
             "topic": topic, "helper": label(people, helper) if helper else "team"}  # unanswered threads address the team
    employee_helper = helper if helper and not helper.startswith("M") else None
    mentioned = (employee_helper,) if employee_helper else ()
    messages = [(opened_at, requester, text.render("message_request", rng, **slots), mentioned)]
    if helper:
        for turn in range(rng.choices((1, 2, 3), weights=(2, 4, 3))[0]):
            messages.append((None, helper, text.render("message_reply", rng, **slots), ()))
            if turn or rng.random() < 0.5:
                messages.append((None, requester, text.render("message_vague", rng, **{**slots, "helper": slots["requester"]}), ()))
        if thanks:
            messages.append((None, requester, text.render("message_thanks", rng, outcome=rng.choice(OUTCOMES), **slots), mentioned))
    elif rng.random() < 0.4:
        messages.append((None, requester, text.render("message_vague", rng, **{**slots, "helper": slots["requester"]}), ()))
    moment, timed = opened_at, []
    for sent_at, author, body, ments in messages:
        if sent_at is None:
            moment = work_time(rng, (moment + timedelta(hours=rng.choice((2, 5, 20, 26, 48)))).date())
            moment = max(moment, timed[-1][0] + timedelta(minutes=10))
        timed.append((sent_at or moment, author, body, ments))
    return timed


def assign_ids(ctx, rows, prefix, key, sort_key):
    """Chronological IDs, so reserved story IDs fall at their date-proportional positions."""
    rows.sort(key=sort_key)
    for row in rows:
        row[key] = ctx.ids.new(prefix)


def near_misses(people):
    """{employee: (kind, quarter)} — at most one extra signal per person, never a story person."""
    rng = common.rng("ops:near_misses")
    story_people = {row["Employee_ID"] for row in common.story_rows()}
    chosen = {}
    for m in people.managers:
        pool = [eid for eid in people.members[m] if eid not in story_people]
        rate = NEAR_MISS_RATE["story_team" if m in STORY_TEAMS else "default"]
        count = int(len(pool) * rate + rng.random())
        kinds = ["informal_help", "foreign_mention", "goal_blocker"]
        rng.shuffle(kinds)
        for index, eid in enumerate(rng.sample(pool, min(count, len(pool)))):
            chosen[eid] = (kinds[index % 3], rng.choice(ANALYSIS_QUARTERS))
    return chosen


def goals(ctx, people):
    rng = common.rng("ops:goals")
    projects = common.read_csv(common.LEGACY / "OP_projects.csv")
    reserved = {int(i[3:]) for i in ctx.ids.reserved if i.startswith("TGL")}
    goal_rows, by_team_quarter = ctx.rows("OP_team_goals"), {}
    for q_index, (quarter, (q_start, q_end)) in enumerate(common.QUARTERS.items()):
        # TGL = quarter index x 150 + position, with story goals holding their reserved positions.
        budget = 150 - sum(1 for n in reserved if q_index * 150 < n <= (q_index + 1) * 150)
        counts = {m: 2 for m in people.managers}
        for m in rng.sample(people.managers, budget - 2 * len(counts)):
            counts[m] = 3
        ctx.ids.start_after("TGL", f"TGL{q_index * 150:06d}")
        for m in people.managers:
            linked = [p["Project_ID"] for p in projects
                      if p["Project_Owner_Manager_ID"] == m and q_start <= date.fromisoformat(p["Project_Start_Date"]) <= q_end]
            for metric_name, unit, direction, (low, high), ratio in rng.sample(METRICS, counts[m]):
                baseline = round(rng.uniform(low, high), 1 if unit != "count" else 0)
                step = baseline * rng.uniform(0.08, 0.25)
                target = round(baseline + step if direction == "increase" else baseline - step, 1 if unit != "count" else 0)
                if unit == "percent":
                    target = min(target, 99.0)
                if unit == "score":
                    target = min(target, 4.9)
                row = {"Team_Goal_ID": ctx.ids.new("TGL"), "Owner_Team": people.team_name[m], "Owner_Manager_ID": m,
                       "Quarter": quarter,
                       "Goal_Text": text.render("goal_text", rng, team=people.team_name[m], metric=metric_name,
                                                target=f"{target:g} {unit}"),
                       "Metric_Name": metric_name, "Metric_Unit": unit, "Target_Direction": direction,
                       "Baseline_Value": "" if rng.random() < 0.1 else baseline, "Target_Value": target,
                       "Set_Date": (q_start + timedelta(days=rng.randint(0, 12))).isoformat(), "Due_Date": q_end.isoformat(),
                       "Linked_Project_ID": rng.choice(linked) if linked and rng.random() < 0.7 else "",
                       "Data_Origin": ORIGIN}
                goal_rows.append(row)
                by_team_quarter.setdefault((m, quarter), []).append((row, baseline, ratio))
    outcomes(ctx, rng, by_team_quarter)
    return by_team_quarter


def outcomes(ctx, rng, by_team_quarter):
    rows = ctx.rows("OP_goal_outcomes")
    for goal_list in by_team_quarter.values():
        for goal, baseline, ratio in goal_list:
            set_day, due = date.fromisoformat(goal["Set_Date"]), date.fromisoformat(goal["Due_Date"])
            target, final_share = goal["Target_Value"], rng.uniform(0.6, 1.25)  # about half the goals are met
            count = rng.choices((3, 4, 5), weights=(2, 5, 2))[0]
            for k in range(1, count + 1):
                day = min(set_day + timedelta(days=(due - set_day).days * k // count + rng.randint(-3, 0)), due)
                progress = final_share * k / count + rng.uniform(-0.08, 0.08)
                value = round(baseline + (target - baseline) * progress, 1 if goal["Metric_Unit"] != "count" else 0)
                if goal["Metric_Unit"] == "percent":
                    value = max(0.0, min(value, 100.0))
                numerator = denominator = ""
                if ratio:
                    denominator = rng.randint(120, 900)
                    numerator = round(denominator * value / 100)
                    value = round(100 * numerator / denominator, 1)
                rows.append({"Goal_Outcome_ID": "", "Team_Goal_ID": goal["Team_Goal_ID"],
                             "Measured_At": iso(work_time(rng, day, 0)), "Measured_Value": value,
                             "Numerator": numerator, "Denominator": denominator,
                             "Measurement_Note": "" if rng.random() < 0.45 else
                             text.render("goal_outcome_note", rng, metric=goal["Metric_Name"], value=f"{value:g}"),
                             "Recorded_By_Manager_ID": goal["Owner_Manager_ID"], "Data_Origin": ORIGIN})
    assign_ids(ctx, rows, "GOC", "Goal_Outcome_ID", lambda r: (r["Measured_At"], r["Team_Goal_ID"]))


def threads(ctx, people, misses, work_requests):
    """~19k formal threads sampled from cross-team work requests, ~6k informal ones, plus near-miss help."""
    rng = common.rng("ops:threads")
    built = []  # (opened_at, requesting, responding, req_emp, req_mgr, topic, wr, closed_at, messages, helper)

    def add(opened_at, requesting, responding, requester, helper, topic, wr, thanks, close_p):
        messages = conversation(rng, people, opened_at, requester, helper, requesting, topic, thanks)
        last = messages[-1][0]
        closed = last + timedelta(hours=rng.choice((1, 4, 24))) if rng.random() < close_p else None
        if closed and closed > END_AT:
            closed = None
        messages = [m for m in messages if m[0] <= END_AT]
        for _, author, _, _ in messages:
            if not author.startswith("M") and not people.active(author, opened_at.date(), messages[-1][0].date()):
                return
        built.append((opened_at, requesting, responding,
                      None if requester.startswith("M") else requester, requester if requester.startswith("M") else None,
                      topic, wr, closed, messages, helper))

    # Formal: weighted sample (Efraimidis-Spirakis) of cross-team requests, favoring each helper's propensity.
    keyed = []
    for wr in work_requests:
        helper, requesting = wr["Assigned_Employee_ID"], wr["Requested_By_Manager_ID"]
        weight = people.weight[helper] * people.activity[people.home[helper]] * (0.6 if people.home[helper] in STORY_TEAMS else 1)
        keyed.append((rng.random() ** (1 / weight), wr))
    keyed.sort(key=lambda pair: -pair[0])
    for _, wr in keyed[:19000]:
        helper, requesting = wr["Assigned_Employee_ID"], wr["Requested_By_Manager_ID"]
        day = date.fromisoformat(wr["Request_Date"])
        requester = requesting if rng.random() < 0.4 else (people.pick(rng, requesting, day) or requesting)
        add(work_time(rng, day), requesting, people.home[helper], requester, helper, wr["Work_Title"],
            wr["Work_Request_ID"], rng.random() < 0.55, 0.93)

    # Informal: the other team's manager answers, or nobody does; no employee helper.
    for _ in range(6000):
        requesting = rng.choices(people.managers, weights=[people.activity[m] * len(people.members[m]) for m in people.managers])[0]
        responding = people.partner(rng, requesting)
        if requesting in STORY_PARTNER_TEAMS and responding in STORY_TEAMS:
            continue
        day = random_day(rng)
        requester = requesting if rng.random() < 0.25 else (people.pick(rng, requesting, day) or requesting)
        answered = rng.random() < 0.6
        add(work_time(rng, day), requesting, responding, requester, responding if answered else None,
            rng.choice(GENERIC_TOPICS), None, answered and rng.random() < 0.3, 0.7 if answered else 0.3)

    # Near miss "informal_help": one closed, thanked thread with no work request, in one analysis quarter.
    for eid, (kind, quarter) in sorted(misses.items()):
        if kind != "informal_help":
            continue
        requesting = people.partner(rng, people.home[eid])
        q_start, q_end = common.QUARTERS[quarter]
        day = random_day(rng, q_start, q_end - timedelta(days=10))
        requester = people.pick(rng, requesting, day) or requesting
        add(work_time(rng, day), requesting, people.home[eid], requester, eid, rng.choice(GENERIC_TOPICS), None, True, 1.0)

    thread_rows, message_rows, index = ctx.rows("OP_collab_threads"), ctx.rows("OP_collab_messages"), []
    built.sort(key=lambda item: (item[0], item[1], item[2]))
    for opened_at, requesting, responding, req_emp, req_mgr, topic, wr, closed, messages, helper in built:
        thread_id = ctx.ids.new("THR")
        thread_rows.append(thread_row(thread_id, people, opened_at, requesting, responding, req_emp, req_mgr, topic, wr, closed))
        for sent_at, author, body, mentioned in messages:
            message_rows.append(message_row("", people, thread_id, sent_at, author, body, mentioned))
        if helper and not helper.startswith("M"):
            index.append((helper, opened_at.date(), thread_id, topic, requesting))
    assign_ids(ctx, message_rows, "MSG", "Message_ID", lambda r: (r["Sent_At"], r["Thread_ID"]))
    return index


def blockers(ctx, people, misses, goals_by_team, wr_by_pair):
    rng = common.rng("ops:blockers")
    rows, index = ctx.rows("OP_dependency_blockers"), []

    def add(raised_at, blocked, blocking, goal, resolver, days):
        goal_text = goal["Metric_Name"] if goal else "the current milestone"
        resolved_at = raised_at + timedelta(days=days, hours=rng.randint(-4, 4)) if resolver is not None else None
        if resolved_at and (resolved_at > END_AT or resolved_at <= raised_at):
            resolver, resolved_at = None, None
        if resolver and not people.active(resolver, raised_at.date(), resolved_at.date()):
            return
        requests = wr_by_pair.get((blocked, blocking), [])
        nearby = [wr for wr in requests if abs((date.fromisoformat(wr[0]) - raised_at.date()).days) <= 20]
        rows.append({"Blocker_ID": "", "Raised_At": iso(raised_at),
                     "Blocked_Team": people.team_name[blocked], "Blocked_Manager_ID": blocked,
                     "Blocked_Team_Goal_ID": goal["Team_Goal_ID"] if goal else "",
                     "Blocking_Team": people.team_name[blocking], "Blocking_Manager_ID": blocking,
                     "Blocker_Description": text.render("blocker_description", rng, blocked_team=people.team_name[blocked],
                                                        blocking_team=people.team_name[blocking], goal=goal_text),
                     "Work_Request_ID": rng.choice(nearby)[1] if nearby and rng.random() < 0.85 else "",
                     "Resolved_By_Employee_ID": resolver or "", "Resolved_At": iso(resolved_at) if resolved_at else "",
                     "Days_Blocked": (resolved_at.date() - raised_at.date()).days if resolved_at else "",
                     "Resolution_Note": text.render("blocker_resolution", rng, helper=people.name[resolver] if resolver else "the team",
                                                    days=(resolved_at.date() - raised_at.date()).days, goal=goal_text)
                     if resolved_at else "",
                     "Data_Origin": ORIGIN})
        if resolver:
            index.append((resolver, raised_at.date(), rows[-1]))

    def goal_of(team, day):
        options = goals_by_team.get((team, common.quarter_of(day)), [])
        return rng.choice(options)[0] if options else None

    for _ in range(6050):
        blocked = rng.choices(people.managers, weights=[people.activity[m] * len(people.members[m]) for m in people.managers])[0]
        blocking = people.partner(rng, blocked)
        if blocked in STORY_PARTNER_TEAMS and blocking in STORY_TEAMS:
            continue
        raised_at = work_time(rng, random_day(rng))
        days = min(int(rng.expovariate(1 / 4)) + 1, 40)
        roll = rng.random()
        if roll < 0.55:    # resolved by the blocking team: ordinary cross-team help, no goal named
            resolver, goal = people.pick(rng, blocking, raised_at.date()), None
        elif roll < 0.75:  # resolved inside the blocked team: may name its goal
            resolver = people.pick(rng, blocked, raised_at.date())
            goal = goal_of(blocked, raised_at.date()) if rng.random() < 0.5 else None
        elif roll < 0.80:  # third team, ordinary
            third = people.partner(rng, blocking)
            resolver = people.pick(rng, third, raised_at.date()) if third != blocked else None
            goal = None
        else:              # still open, or nobody recorded: may name the goal
            resolver, goal = None, goal_of(blocked, raised_at.date()) if rng.random() < 0.5 else None
        add(raised_at, blocked, blocking, goal, resolver, days)

    # Near miss "goal_blocker": resolves one blocker that delayed another team's goal.
    for eid, (kind, quarter) in sorted(misses.items()):
        if kind != "goal_blocker":
            continue
        blocked = people.partner(rng, people.home[eid])
        q_start, q_end = common.QUARTERS[quarter]
        raised_at = work_time(rng, random_day(rng, q_start + timedelta(days=12), q_end - timedelta(days=15)))
        add(raised_at, blocked, people.home[eid], goal_of(blocked, raised_at.date()), eid, rng.randint(2, 9))
    assign_ids(ctx, rows, "BLK", "Blocker_ID", lambda r: (r["Raised_At"], r["Blocked_Manager_ID"]))
    return [(eid, day, row["Blocker_ID"]) for eid, day, row in index]


def incidents(ctx, people):
    rng = common.rng("ops:incidents")
    rows, index = ctx.rows("OP_incident_handoffs"), []
    while len(rows) < 3000:
        owner = rng.choices(people.managers, weights=[people.activity[m] * len(people.members[m]) for m in people.managers])[0]
        kind = "handoff" if rng.random() < 0.25 else "incident"
        severity = rng.choices(("sev1", "sev2", "sev3", "sev4"), weights=(3, 12, 45, 40))[0]
        hour = rng.randint(0, 23) if rng.random() < 0.3 else rng.randint(8, 18)
        started = datetime.combine(random_day(rng), time(hour, rng.randrange(0, 60, 5)))
        ended = None if rng.random() < 0.03 else started + timedelta(minutes=rng.randint(20, 60 * (30 if kind == "incident" else 10)))
        if ended and ended > END_AT:
            ended = None
        responders = []
        for _ in range(rng.choices((1, 2, 3, 4), weights=(4, 4, 2, 1))[0]):
            person = people.pick(rng, owner, started.date(), responders)
            if person:
                responders.append(person)
        if rng.random() < 0.15:  # a responder from a partner team: ordinary cross-team help
            helping = people.partner(rng, owner)
            if not (owner in STORY_PARTNER_TEAMS and helping in STORY_TEAMS):
                person = people.pick(rng, helping, started.date())
                if person:
                    responders.append(person)
        last = (ended or END_AT).date()
        responders = [r for r in responders if people.active(r, started.date(), min(last, END))]
        if not responders:
            continue
        rows.append({"Incident_ID": "", "Incident_Type": kind, "Severity": severity,
                     "Owning_Team": people.team_name[owner], "Owning_Manager_ID": owner, "Started_At": iso(started),
                     "Ended_At": iso(ended) if ended else "", "Responder_Employee_IDs": ";".join(responders),
                     "Incident_Notes": text.render("incident_notes", rng, responders=", ".join(people.name[r] for r in responders),
                                                   owning_team=people.team_name[owner], severity=severity),
                     "Data_Origin": ORIGIN})
    assign_ids(ctx, rows, "INC", "Incident_ID", lambda r: (r["Started_At"], r["Owning_Manager_ID"]))
    return [(r, date.fromisoformat(row["Started_At"][:10]), row["Incident_ID"], row["Owning_Manager_ID"])
            for row in rows for r in row["Responder_Employee_IDs"].split(";")]


def mentions(ctx, people, misses, thread_index, blocker_index, incident_index):
    """Own-team meeting notes; only near misses appear in another team's notes (once)."""
    rng = common.rng("ops:mentions")
    anchors = {}  # employee -> list of (day, column, id, topic, other team)
    for eid, day, thread_id, topic, requesting in thread_index:
        anchors.setdefault(eid, []).append((day, "Thread_ID", thread_id, topic, requesting))
    for eid, day, blocker_id in blocker_index:
        anchors.setdefault(eid, []).append((day, "Blocker_ID", blocker_id, "a blocker", None))
    for eid, day, incident_id, owner in incident_index:
        anchors.setdefault(eid, []).append((day, "Incident_ID", incident_id, "an incident", owner))
    for row in common.read_csv(common.LEGACY / "OP_contributions.csv"):
        if START <= date.fromisoformat(row["Contribution_Date"]) <= END and row["Employee_ID"] in people.home:
            anchors.setdefault(row["Employee_ID"], []).append(
                (date.fromisoformat(row["Contribution_Date"]), "Contribution_ID", row["Contribution_ID"], row["Project_Name"], None))
    meeting_day = {m: rng.randrange(5) for m in people.managers}
    weeks = (END - common.WEEK_ZERO).days // 7 + 1
    rows = ctx.rows("OP_meeting_mentions")

    def add(team, day, eid, anchor):
        row = {"Mention_ID": "", "Meeting_Date": day.isoformat(), "Meeting_Team": people.team_name[team],
               "Meeting_Manager_ID": team, "Mentioned_Employee_ID": eid,
               "Note_Text": text.render("meeting_mention", rng, helper=people.name[eid], meeting_team=people.team_name[team],
                                        topic=anchor[3] if anchor else rng.choice(GENERIC_TOPICS)),
               "Contribution_ID": "", "Thread_ID": "", "Blocker_ID": "", "Incident_ID": "", "Data_Origin": ORIGIN}
        if anchor:
            row[anchor[1]] = anchor[2]
        rows.append(row)

    team_weights = [people.activity[m] * len(people.members[m]) for m in people.managers]
    while len(rows) < 14900:
        team = rng.choices(people.managers, weights=team_weights)[0]
        day = common.WEEK_ZERO + timedelta(days=7 * rng.randrange(weeks) + meeting_day[team])
        if not START <= day <= END:
            continue
        eid = people.pick(rng, team, day)
        if not eid:
            continue
        recent = [a for a in anchors.get(eid, ()) if 0 <= (day - a[0]).days <= 30]
        add(team, day, eid, rng.choice(recent) if recent and rng.random() < 0.7 else None)

    # Near miss "foreign_mention": one line in a partner team's notes, tied to a formal thread when one exists.
    for eid, (kind, quarter) in sorted(misses.items()):
        if kind != "foreign_mention":
            continue
        q_start, q_end = common.QUARTERS[quarter]
        helped = [a for a in anchors.get(eid, ()) if a[1] == "Thread_ID" and q_start <= a[0] <= q_end - timedelta(days=7)]
        anchor = rng.choice(helped) if helped else None
        team = anchor[4] if anchor else people.partner(rng, people.home[eid])
        first = anchor[0] + timedelta(days=1) if anchor else q_start
        day = first + timedelta(days=(meeting_day[team] - first.weekday()) % 7)
        add(team, min(day, q_end), eid, anchor)
    assign_ids(ctx, rows, "MTM", "Mention_ID", lambda r: (r["Meeting_Date"], r["Meeting_Manager_ID"], r["Mentioned_Employee_ID"]))


def generate(ctx):
    people = People(ctx)
    misses = near_misses(people)
    work_requests = [wr for wr in common.read_csv(common.LEGACY / "OP_work_requests.csv")
                     if START <= date.fromisoformat(wr["Request_Date"]) <= END - timedelta(days=3)
                     and wr["Assigned_Employee_ID"] in people.home
                     and people.home[wr["Assigned_Employee_ID"]] != wr["Requested_By_Manager_ID"]]
    wr_by_pair = {}
    for wr in work_requests:
        wr_by_pair.setdefault((wr["Requested_By_Manager_ID"], people.home[wr["Assigned_Employee_ID"]]), []).append(
            (wr["Request_Date"], wr["Work_Request_ID"]))
    goals_by_team = goals(ctx, people)
    thread_index = threads(ctx, people, misses, work_requests)
    blocker_index = blockers(ctx, people, misses, goals_by_team, wr_by_pair)
    incident_index = incidents(ctx, people)
    mentions(ctx, people, misses, thread_index, blocker_index, incident_index)
    ctx.ops_near_misses = misses  # for QA only; never written to the pack


def _self_check():
    import time as clock
    from collections import Counter
    began = clock.perf_counter()
    ctx = common.load_context()
    generate(ctx)
    elapsed = clock.perf_counter() - began
    columns, reserved = common.dictionary(), ctx.ids.reserved
    key_of = {"OP_team_goals": "Team_Goal_ID", "OP_goal_outcomes": "Goal_Outcome_ID", "OP_collab_threads": "Thread_ID",
              "OP_collab_messages": "Message_ID", "OP_dependency_blockers": "Blocker_ID",
              "OP_incident_handoffs": "Incident_ID", "OP_meeting_mentions": "Mention_ID"}
    date_cols = ("Set_Date", "Due_Date", "Measured_At", "Opened_At", "Closed_At", "Sent_At", "Raised_At", "Resolved_At",
                 "Started_At", "Ended_At", "Meeting_Date")
    for table, key in key_of.items():
        rows = ctx.tables[table]
        ids = [r[key] for r in rows]
        assert len(set(ids)) == len(ids), table
        assert not set(ids) & reserved, table
        for r in rows:
            assert set(r) == set(columns[table]), table
            for col in date_cols:
                if r.get(col):
                    assert START.isoformat() <= r[col][:10] <= END.isoformat(), (table, col, r[col])
    goal_ids = {r["Team_Goal_ID"] for r in ctx.tables["OP_team_goals"]}
    threads_by_id = {r["Thread_ID"]: r for r in ctx.tables["OP_collab_threads"]}
    assert all(r["Team_Goal_ID"] in goal_ids for r in ctx.tables["OP_goal_outcomes"])
    assert all(r["Blocked_Team_Goal_ID"] in goal_ids for r in ctx.tables["OP_dependency_blockers"] if r["Blocked_Team_Goal_ID"])
    assert all(r["Thread_ID"] in threads_by_id and r["Sent_At"] >= threads_by_id[r["Thread_ID"]]["Opened_At"]
               for r in ctx.tables["OP_collab_messages"])
    assert all(r["Thread_ID"] in threads_by_id for r in ctx.tables["OP_meeting_mentions"] if r["Thread_ID"])
    assert all(sum(bool(r[c]) for c in ("Contribution_ID", "Thread_ID", "Blocker_ID", "Incident_ID")) <= 1
               for r in ctx.tables["OP_meeting_mentions"])
    people = People(ctx)
    # Rarity: count the extra hidden-work signals per employee.
    signals = Counter()
    helpers_informal = {m["Author_Employee_ID"] for m in ctx.tables["OP_collab_messages"]
                        if m["Author_Employee_ID"] and not threads_by_id[m["Thread_ID"]]["Work_Request_ID"]
                        and people.home[m["Author_Employee_ID"]] == threads_by_id[m["Thread_ID"]]["Responding_Manager_ID"]}
    foreign = {r["Mentioned_Employee_ID"] for r in ctx.tables["OP_meeting_mentions"]
               if people.home[r["Mentioned_Employee_ID"]] != r["Meeting_Manager_ID"]}
    goal_help = {r["Resolved_By_Employee_ID"] for r in ctx.tables["OP_dependency_blockers"]
                 if r["Blocked_Team_Goal_ID"] and r["Resolved_By_Employee_ID"]
                 and people.home[r["Resolved_By_Employee_ID"]] != r["Blocked_Manager_ID"]}
    for group in (helpers_informal, foreign, goal_help):
        signals.update(group)
    assert max(signals.values()) == 1, "someone has two extra signals"
    per_team = Counter(people.home[e] for e in signals)
    helped = Counter(m["Author_Employee_ID"] for m in ctx.tables["OP_collab_messages"] if m["Author_Employee_ID"])
    counts = sorted(helped.get(e, 0) for e in people.home)
    print({t: len(ctx.tables[t]) for t in key_of})
    print(f"runtime {elapsed:.1f}s; extra-signal people {len(signals)} "
          f"(M32 {per_team['M32']}, M14 {per_team['M14']}, max team share "
          f"{max(per_team[m] / len(people.members[m]) for m in people.managers):.1%}); "
          f"messages per employee p10/p50/p90/max {counts[250]}/{counts[1250]}/{counts[2250]}/{counts[-1]}")


if __name__ == "__main__":
    _self_check()
