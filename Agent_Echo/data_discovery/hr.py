"""HR background generator for discovery_v1 (T1.3, plan v10 Ã‚Â§5.4).

Runs after ops.generate(ctx): reads OP_team_goals, OP_collab_threads/messages, OP_dependency_blockers and
OP_incident_handoffs for goal links and work anchors. Copies the legacy and extension tables, adds the new
columns, and writes the new HR tables, OP_activity_weekly and OP_source_coverage. Background rows are never
cited by stories or plants (they add their own rows), so background Record_Coverage may be partial.
"""
import re
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from . import common, text

LEGACY_UNCHANGED = ("HR_managers", "HR_employees", "HR_survey_summary", "HR_survey_comments",
                    "HR_program_participation", "OP_projects", "OP_work_requests", "OP_priority_decisions")
EXTENSION_COPIES = ("HR_goals", "HR_self_review_items")
START, END = common.ANALYSIS[0], common.FOLLOW_UP[1]
HORIZON = datetime.combine(END, time(23, 0))
WEEKS = 53  # dictionary: Week_Start 2025-09-29 to 2026-09-28, matching OP_capacity's last week
DEMO_TEAMS = ("M32", "M14")  # hand-built story teams: background keeps hidden-work signals out of them
TOPICS = ("handoff timing", "shared backlog review", "intake process", "release calendar", "escalation path",
          "reporting cadence", "on-call rotation", "capacity planning", "data refresh schedule", "review checklist")
GENERIC_WORK = ("the quarterly priorities", "the team's delivery plan", "day-to-day operations",
                "the service backlog", "process documentation")


def stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:00")


def at(day, rng):
    return datetime.combine(day, time(rng.randint(8, 17), rng.randint(0, 59)))


def day_in(rng, start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def clamp(value, low, high):
    return max(low, min(high, value))


def hours(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")


def active(employee, day):
    return employee["Hire_Date"] <= day.isoformat() and (not employee["Termination_Date"]
                                                        or employee["Termination_Date"] >= day.isoformat())


def generate(ctx):
    columns = common.dictionary()
    employees = {row["Employee_ID"]: row for row in ctx.employees}
    team_name = {row["Manager_ID"]: row["Primary_Team"] for row in ctx.managers}
    members = defaultdict(list)
    for row in ctx.employees:
        members[row["Pilot_Manager_ID"]].append(row)
    current = [row for row in ctx.employees if active(row, START)]
    pinned_perf = common.pinned_rows("HR_employee_performance")
    story = {row["Employee_ID"] for row in pinned_perf.values()}
    protected = story | {row["Employee_ID"] for row in current if row["Pilot_Manager_ID"] in DEMO_TEAMS}
    near_miss = _near_misses(members, story)

    for table in LEGACY_UNCHANGED:
        ctx.rows(table).extend(_copy(common.LEGACY / f"{table}.csv", columns[table]))
    for table in EXTENSION_COPIES:
        ctx.rows(table).extend(_copy(common.EXTENSIONS / f"{table}.csv", columns[table]))
    requests = {row["Work_Request_ID"]: row for row in ctx.rows("OP_work_requests")}

    contributions = _contributions(ctx, requests, protected)
    _feedback(ctx, employees, members, protected, near_miss, {row["Contribution_ID"]: row for row in contributions})
    capacity = common.read_csv(common.LEGACY / "OP_capacity.csv")
    weekly = _activity(ctx, members, capacity)
    _capacity(ctx, capacity, weekly)
    _performance(ctx, members, pinned_perf)
    _recognition(ctx, employees, current, contributions, protected, near_miss)
    _one_on_ones(ctx, current)
    _review_notes(ctx, current, contributions)
    _team_plans(ctx, team_name)
    _coverage(ctx, team_name)
    _check_pinned(ctx)


def _copy(path, header):
    rows = common.read_csv(path)
    if rows and set(rows[0]) != set(header):
        raise RuntimeError(f"{path.name}: legacy columns differ from the dictionary.")
    return rows


def _near_misses(members, story):
    """About 5% of each non-demo team: the background's only hidden-work profiles (unshared, unrecognized)."""
    rng, chosen = common.rng("hr:near_miss"), set()
    for manager, team in sorted(members.items()):
        pool = sorted(row["Employee_ID"] for row in team if active(row, START) and row["Employee_ID"] not in story)
        if manager not in DEMO_TEAMS and pool:
            chosen.update(rng.sample(pool, max(1, round(0.05 * len(pool)))))
    return chosen


def _contributions(ctx, requests, protected):
    rng, goals, by_name = common.rng("hr:contributions"), defaultdict(list), defaultdict(set)
    for goal in ctx.rows("OP_team_goals"):
        goals[goal["Owner_Manager_ID"], goal["Quarter"]].append(goal["Team_Goal_ID"])
    for manager in ctx.managers:
        by_name[manager["Primary_Team"]].add(manager["Manager_ID"])
    rows = common.read_csv(common.LEGACY / "OP_contributions.csv")
    for row in rows:
        request, day = requests.get(row["Work_Request_ID"]), date.fromisoformat(row["Contribution_Date"])
        if request and request["Requesting_Team"] == row["Beneficiary_Team"]:
            beneficiary = request["Requested_By_Manager_ID"]
        else:  # display names are not unique: link only when the name names one team
            names = by_name[row["Beneficiary_Team"]]
            beneficiary = next(iter(names)) if len(names) == 1 else ""
        goal = ""
        if START <= day <= END and beneficiary and rng.random() < (0.1 if row["Employee_ID"] in protected else 0.3):
            goal = rng.choice(goals.get((beneficiary, common.quarter_of(day)), [""]))
        if request and request["Assigned_Employee_ID"] == row["Employee_ID"]:
            effort = float(request["Actual_Hours"] or 0) + float(request["Rework_Hours"] or 0)
        else:
            effort = rng.randint(4, 32) / 2
        row.update(Team_Goal_ID=goal, Effort_Hours=hours(effort),
                   Request_Channel="formal" if row["Work_Request_ID"] else "informal")
    ctx.rows("OP_contributions").extend(rows)
    return rows


def _feedback(ctx, employees, members, protected, near_miss, contributions):
    rng = common.rng("hr:feedback")
    rows = common.read_csv(common.LEGACY / "HR_recognition_feedback.csv")
    for row in rows:
        written_by = row["Employee_ID"]
        quarter_end = date.fromisoformat(row["Interaction_Date"])
        done = date.fromisoformat(contributions[row["Contribution_ID"]]["Contribution_Date"])
        day = min(done + timedelta(days=rng.randint(0, 14)), quarter_end) if done <= quarter_end else done
        written = at(day, rng)
        home = row["Author_Manager_ID"] == row["Recipient_Manager_ID"]
        author_type, author_employee = ("home_manager" if home else "partner_manager"), ""
        if not home and day >= START and rng.random() < 0.3:
            pool = [person for person in members[row["Author_Manager_ID"]] if active(person, day)]
            if pool:
                person = rng.choice(pool)
                author_type, author_employee = "partner_employee", person["Employee_ID"]
                row.update(Author_Manager_ID="", Author_Name=person["Employee_Name"])
        if home:  # the home manager wrote it, so it is visible to them at once
            shared = recorded = written
        elif written_by in protected:
            shared = written + timedelta(minutes=rng.randint(5, 60))
            recorded = shared + timedelta(minutes=rng.randint(0, 10))
        elif rng.random() < (0.3 if written_by in near_miss and day >= START else 0.95):
            late = rng.random() < 0.2
            shared = written + (timedelta(days=rng.randint(7, 45)) if late else timedelta(minutes=rng.randint(10, 5760)))
            recorded = shared + (timedelta(days=rng.randint(1, 3)) if rng.random() < 0.15
                                 else timedelta(minutes=rng.randint(0, 120)))
            shared, recorded = min(shared, HORIZON), min(recorded, HORIZON)
        else:
            shared = recorded = None
        row.update(Interaction_At=stamp(written), Interaction_Date=day.isoformat(), Author_Type=author_type,
                   Author_Employee_ID=author_employee, Thread_ID="", Blocker_ID="", Incident_ID="",
                   Shared_With_Home_Manager_At=stamp(shared) if shared else "",
                   Share_Recorded_At=stamp(recorded) if recorded else "",
                   Shared_With_Home_Manager="Yes" if shared else "No",
                   Record_Coverage="partial" if rng.random() < 0.05 else "complete")
    ctx.rows("HR_recognition_feedback").extend(rows)


def _activity(ctx, members, capacity):
    rng, pinned = common.rng("hr:activity"), common.pinned_rows("OP_activity_weekly")
    scheduled = {(row["Employee_ID"], row["Week_Start"]): float(row["Scheduled_Hours"] or 0)
                 for row in capacity
                 if row["Week_Start"] >= common.WEEK_ZERO.isoformat()}
    weekly = {}
    for manager, team in sorted(members.items()):
        calm = manager == "M32"  # M32 stays well inside its range so the story weeks stand out
        after_mu = 70 if calm else rng.uniform(40, 150)
        cross_mu = 2.5 if calm else rng.uniform(1.5, 6)
        meet_mu = rng.uniform(5, 12)
        for person in team:
            factor = rng.uniform(0.85, 1.15) if calm else rng.uniform(0.7, 1.3)
            for week in range(WEEKS):
                start = common.WEEK_ZERO + timedelta(weeks=week)
                if not active(person, start + timedelta(days=6)) or not active(person, start):
                    continue
                scale = scheduled.get((person["Employee_ID"], start.isoformat()), 40) / 40
                after = max(0, rng.gauss(after_mu * factor, after_mu * 0.35)) * scale
                cross = max(0, rng.gauss(cross_mu * factor, cross_mu * 0.35)) * scale
                if calm:
                    after, cross = min(after, 200), min(cross, 5)
                elif rng.random() < 0.004:  # a few natural outlier weeks
                    after, cross = after * rng.uniform(2.5, 4), cross * rng.uniform(2.5, 3.5)
                key = common.awk_id(start, person["Employee_ID"])
                row = {"Activity_Week_ID": key, "Employee_ID": person["Employee_ID"], "Week_Start": start.isoformat(),
                       "Cross_Team_Hours": hours(round(cross * 2) / 2), "After_Hours_Minutes": str(round(after / 5) * 5),
                       "Meeting_Hours": hours(round(max(0.5, rng.gauss(meet_mu, 2)) * scale * 2) / 2),
                       "Data_Origin": "Synthetic"}
                if key in pinned:
                    facts = pinned[key]["Facts"]
                    assert pinned[key]["Employee_ID"] == person["Employee_ID"] and start.isoformat() in facts, key
                    row["After_Hours_Minutes"] = re.search(r"after-hours (\d+) minutes", facts).group(1)
                    row["Cross_Team_Hours"] = hours(float(re.search(r"cross-team hours (\d+(?:\.\d+)?)", facts).group(1)))
                weekly[person["Employee_ID"], row["Week_Start"]] = row
    ctx.rows("OP_activity_weekly").extend(sorted(weekly.values(), key=lambda row: row["Activity_Week_ID"]))
    return weekly


def _capacity(ctx, rows, weekly):
    for row in rows:
        week = weekly.get((row["Employee_ID"], row["Week_Start"]))
        row.update(After_Hours=hours(int(week["After_Hours_Minutes"]) / 60) if week else "",
                   Cross_Team_Hours=week["Cross_Team_Hours"] if week else "")
    ctx.rows("OP_capacity").extend(rows)


def _performance(ctx, members, pinned):
    rng, quarters, rows = common.rng("hr:performance"), list(common.QUARTERS), {}
    story = {row["Employee_ID"] for row in pinned.values()}
    steps = (-2, -1, -1, 0, 0, 0, 0, 0, 1, 1, 2)
    for manager, team in sorted(members.items()):
        team_mu = 2.9 if manager == "M14" else rng.uniform(3.0, 3.9)
        people = [person for person in team if active(person, START)]
        for person in people:
            pulse = clamp(round(rng.gauss(team_mu, 0.8)), 1, 5)
            for index, quarter in enumerate(quarters):
                if index:
                    pulse = clamp(pulse + rng.choice(steps), 1, 5)
                end = common.QUARTERS[quarter][1]
                if not active(person, end):
                    continue
                rows[person["Employee_ID"], quarter] = {
                    "Performance_ID": common.prf_id(quarter, person["Employee_ID"]), "Employee_ID": person["Employee_ID"],
                    "Quarter": quarter, "Pulse_Score": pulse,
                    "Engagement_Score": str(clamp(int(pulse * 16 + rng.gauss(10, 8)), 0, 100)),
                    "Performance_Rating": str(clamp(round(rng.gauss(3.3, 0.8)), 1, 5)),
                    "Goal_Attainment_Percent": f"{clamp(rng.gauss(72, 15), 0, 100):.1f}",
                    "Recorded_At": stamp(at(end - timedelta(days=rng.randint(2, 9)), rng)), "Data_Origin": "Synthetic"}
        latest = "2026-Q2"  # quarter of the as-of date 2026-06-30
        others = [rows[p["Employee_ID"], latest] for p in people
                  if p["Employee_ID"] not in story and (p["Employee_ID"], latest) in rows]
        if manager == "M32":  # story rule: every non-story M32 employee's latest pulse is 3 or higher
            for row in others:
                row["Pulse_Score"] = max(3, row["Pulse_Score"])
        if manager == "M14":  # story rule: at least 10 non-story M14 employees at 3 or lower
            for row in sorted(others, key=lambda row: (row["Pulse_Score"], row["Employee_ID"]))[:10]:
                row["Pulse_Score"] = min(3, row["Pulse_Score"])
    by_id = {row["Performance_ID"]: row for row in rows.values()}
    for key, story in pinned.items():
        quarter, recorded, pulse = re.search(r"Quarter (\S+), recorded (\d{4}-\d\d-\d\d), pulse score (\d)",
                                             story["Facts"]).groups()
        assert common.prf_id(quarter, story["Employee_ID"]) == key and key in by_id, key
        by_id[key].update(Pulse_Score=int(pulse), Recorded_At=f"{recorded}T09:00:00")
    for row in by_id.values():
        row["Pulse_Score"] = str(row["Pulse_Score"])
    ctx.rows("HR_employee_performance").extend(sorted(by_id.values(), key=lambda row: row["Performance_ID"]))


def _work_items(ctx, contributions):
    """Per employee: dated work anchors in the window (type, id, date, label), formal cross-team work first."""
    items = defaultdict(lambda: defaultdict(list))
    for row in contributions:
        day = date.fromisoformat(row["Contribution_Date"])
        if START <= day <= END and row["Home_Team"] != row["Beneficiary_Team"] and row["Work_Request_ID"]:
            items[row["Employee_ID"]]["contribution"].append(("Contribution_ID", row["Contribution_ID"], day, row["Project_Name"]))
    for row in ctx.rows("OP_dependency_blockers"):
        if row["Resolved_By_Employee_ID"] and row["Resolved_At"]:
            items[row["Resolved_By_Employee_ID"]]["other"].append(
                ("Blocker_ID", row["Blocker_ID"], date.fromisoformat(row["Resolved_At"][:10]),
                 f"the {row['Blocked_Team']} dependency"))
    for row in ctx.rows("OP_incident_handoffs"):
        for person in filter(None, row["Responder_Employee_IDs"].split(";")):
            items[person]["other"].append(("Incident_ID", row["Incident_ID"], date.fromisoformat(row["Started_At"][:10]),
                                           f"the {row['Owning_Team']} {row['Incident_Type']}"))
    threads = {row["Thread_ID"]: row for row in ctx.rows("OP_collab_threads")}
    helped = set()
    for row in ctx.rows("OP_collab_messages"):
        thread = threads.get(row["Thread_ID"])
        if thread and row["Author_Employee_ID"] and (row["Author_Employee_ID"], thread["Thread_ID"]) not in helped:
            helped.add((row["Author_Employee_ID"], thread["Thread_ID"]))
            items[row["Author_Employee_ID"]]["other"].append(
                ("Thread_ID", thread["Thread_ID"], date.fromisoformat(thread["Opened_At"][:10]), thread["Topic"]))
    return items


def _recognition(ctx, employees, current, contributions, protected, near_miss, target=4000):
    """About 4,000 events, one anchor each, mostly on visible formal cross-team work, spread so most people
    have recognized formal help; demo-team people get more, near misses get none."""
    rng, items = common.rng("hr:recognition"), _work_items(ctx, contributions)
    picks = []
    eligible = [row["Employee_ID"] for row in current if row["Employee_ID"] not in near_miss and items[row["Employee_ID"]]]
    for employee in eligible:
        pool = items[employee]["contribution"] or items[employee]["other"]
        rng.shuffle(pool)
        picks.extend((employee, item) for item in pool[:4 if employee in protected else 1])
    used = {(employee, item[1]) for employee, item in picks}
    for _ in range(50 * target):  # bounded: stops early when every item is used
        if len(picks) >= target:
            break
        employee = rng.choice(eligible)
        kind = "contribution" if items[employee]["contribution"] and rng.random() < 0.8 else "other"
        options = [item for item in items[employee][kind] if (employee, item[1]) not in used]
        if options:
            item = rng.choice(options)
            used.add((employee, item[1]))
            picks.append((employee, item))
    events = []
    for employee, (column, anchor, day, work) in picks:
        given = min(datetime.combine(day + timedelta(days=rng.randint(3, 30)), time(rng.randint(9, 17), rng.randint(0, 59))),
                    HORIZON)
        person = employees[employee]
        row = {"Employee_ID": employee, "Given_By_Manager_ID": person["Pilot_Manager_ID"],
               "Recognition_Type": rng.choices(("spot_award", "written_commendation", "public_shoutout", "bonus"),
                                               (3, 4, 4, 1))[0],
               "Visibility": rng.choices(("private", "team", "department", "company"), (2, 5, 2, 1))[0],
               "Recognized_At": stamp(given),
               "Citation_Text": text.render("recognition_citation", rng, employee=person["Employee_Name"], work=work),
               "Contribution_ID": "", "Thread_ID": "", "Blocker_ID": "", "Incident_ID": "", "Data_Origin": "Synthetic"}
        row[column] = anchor
        events.append(row)
    for row in sorted(events, key=lambda row: row["Recognized_At"]):
        ctx.rows("HR_recognition_events").append({"Recognition_ID": ctx.ids.new("REC"), **row})


def _one_on_ones(ctx, current, count=2000):
    rng, rows = common.rng("hr:one_on_ones"), []
    codes = ("workload", "career", "performance", "recognition", "other")
    for _ in range(count):
        person = rng.choice(current)
        code = rng.choices(codes, (5, 4, 5, 2, 4))[0]
        if person["Employee_ID"] == "E2156" and code == "workload":  # background exclusion for P2
            code = "career"
        rows.append({"Manager_ID": person["Pilot_Manager_ID"], "Employee_ID": person["Employee_ID"],
                     "Meeting_Date": day_in(rng, START, END).isoformat(), "Topic_Code": code,
                     "Notes": text.render("one_on_one_notes", rng, employee=person["Employee_Name"], topic_code=code),
                     "Data_Origin": "Synthetic"})
    for row in sorted(rows, key=lambda row: row["Meeting_Date"]):
        ctx.rows("HR_one_on_ones").append({"One_On_One_ID": ctx.ids.new("OOO"), **row})


def _review_notes(ctx, current, contributions, count=1000):
    rng, rows, own = common.rng("hr:review_notes"), [], defaultdict(list)
    for row in contributions:
        if START.isoformat() <= row["Contribution_Date"] <= END.isoformat():
            own[row["Employee_ID"]].append(row)
    cycles = {"2025-year-end": (date(2025, 12, 1), date(2026, 1, 31)), "2026-mid-year": (date(2026, 6, 1), date(2026, 7, 31))}
    for _ in range(count):
        person = rng.choice(current)
        cycle = rng.choice(list(cycles))
        day = day_in(rng, *cycles[cycle])
        earlier = [row for row in own[person["Employee_ID"]] if row["Contribution_Date"] <= day.isoformat()]
        anchor = rng.choice(earlier) if earlier and rng.random() < 0.6 else None
        rows.append({"Employee_ID": person["Employee_ID"], "Review_Cycle": cycle,
                     "Author_Manager_ID": person["Pilot_Manager_ID"], "Note_Date": day.isoformat(),
                     "Note_Text": text.render("review_note", rng, employee=person["Employee_Name"],
                                              work=anchor["Project_Name"] if anchor else rng.choice(GENERIC_WORK)),
                     "Contribution_ID": anchor["Contribution_ID"] if anchor else "", "Thread_ID": "", "Blocker_ID": "",
                     "Incident_ID": "", "Data_Origin": "Synthetic"})
    for row in sorted(rows, key=lambda row: row["Note_Date"]):
        ctx.rows("HR_review_notes").append({"Review_Note_ID": ctx.ids.new("RVN"), **row})


def _team_plans(ctx, team_name, count=800):
    rng, rows, managers = common.rng("hr:team_plans"), [], sorted(team_name)
    for _ in range(count):
        manager, day = rng.choice(managers), day_in(rng, START, END)
        partner = rng.choice([m for m in managers if m != manager]) if rng.random() < 0.7 else ""
        # background exclusion for P4: no M32 follow-up item naming M16 (also not its namesake team M48)
        while manager == "M32" and day >= common.FOLLOW_UP[0] and team_name.get(partner) == team_name["M16"]:
            partner = rng.choice([m for m in managers if m != manager])
        rows.append({"Planning_Team": team_name[manager], "Planning_Manager_ID": manager,
                     "Partner_Team": team_name[partner] if partner else "", "Partner_Manager_ID": partner,
                     "Item_Text": text.render("team_plan_item", rng, team=team_name[manager],
                                              partner_team=team_name[partner or manager], topic=rng.choice(TOPICS)),
                     "Plan_Date": day.isoformat(), "Data_Origin": "Synthetic"})
    for row in sorted(rows, key=lambda row: row["Plan_Date"]):
        ctx.rows("OP_team_plans").append({"Team_Plan_ID": ctx.ids.new("TPL"), **row})


def _coverage(ctx, team_name):
    for table in common.COVERAGE_TABLES:
        for manager in sorted(team_name):
            for quarter in common.QUARTERS:
                partial = (table, manager, quarter) == ("HR_recognition_feedback", "M41", "2026-Q3")  # gate 4's one test row
                ctx.rows("OP_source_coverage").append({
                    "Coverage_ID": common.cov_id(table, manager, quarter), "Source_Table": table,
                    "Home_Manager_ID": manager, "Home_Team": team_name[manager], "Quarter": quarter,
                    "Coverage_Status": "partial" if partial else "complete", "Data_Origin": "Synthetic"})


def _check_pinned(ctx):
    """Every pinned PRF/AWK/COV story row exists with the story's value."""
    checks = {"HR_employee_performance": ("Performance_ID", lambda row, facts: f"pulse score {row['Pulse_Score']}." in facts),
              "OP_activity_weekly": ("Activity_Week_ID", lambda row, facts: f"after-hours {row['After_Hours_Minutes']} minutes" in facts),
              "OP_source_coverage": ("Coverage_ID", lambda row, facts: facts.endswith(f"{row['Coverage_Status']}.")
                                     and row["Source_Table"] in facts and f"home team {row['Home_Manager_ID']}," in facts)}
    for table, (key, matches) in checks.items():
        rows = {row[key]: row for row in ctx.rows(table)}
        for row_id, story in common.pinned_rows(table).items():
            assert row_id in rows and matches(rows[row_id], story["Facts"]), f"{table} {row_id} misses the story value"
