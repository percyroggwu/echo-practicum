"""Offline demo answers: real numbers for the suggested questions, computed without any AI.

Each handler runs read-only SQL inside the manager's scope (the same team and date rules as Echo's
ScopedData), writes a short templated answer with [SQLn] citations, an optional chart spec, and
recomputes its headline numbers as a deterministic check. The wording is fixed templates, not model
output, and the UI says so.
"""

import re
import sqlite3
from datetime import date, datetime, timedelta, timezone

SURVEY_MIN_RESPONSES = 5


def _key(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _quarter(iso):
    d = date.fromisoformat(iso)
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


def _signed(value, digits=2):
    return f"{value:+.{digits}f}"


class Query:
    """Runs scoped SQL and keeps a readable copy of each query as citable evidence."""

    def __init__(self, database, scope):
        self.db = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        self.db.row_factory = sqlite3.Row
        self.scope = scope
        self.evidence = []
        self.extra = {}  # story fields: triangle, examples, watch, next_steps, voice
        self.team_filter = ("SELECT Employee_ID FROM HR_employees WHERE Pilot_Manager_ID = :manager "
                            "AND Hire_Date <= :end AND (Termination_Date IS NULL OR Termination_Date >= :start)")
        self.params = {"manager": scope.manager_id, "start": scope.start_date, "end": scope.end_date}
        self.teams = [r[0] for r in self.db.execute(
            f"SELECT DISTINCT Team_Display_Name FROM HR_employees WHERE Employee_ID IN ({self.team_filter})", self.params)]

    def run(self, sql, extra=None):
        params = {**self.params, **(extra or {})}
        rows = [dict(r) for r in self.db.execute(sql, params)]
        readable = sql
        for name, value in sorted(params.items(), key=lambda item: -len(item[0])):
            readable = readable.replace(f":{name}", f"'{value}'" if isinstance(value, str) else str(value))
        citation = f"SQL{len(self.evidence) + 1}"
        self.evidence.append({"citation_id": citation, "producer": "Cherry", "sql": " ".join(readable.split()),
                              "rows": rows, "truncated": False, "scope": self.scope.__dict__, "parameters": []})
        return citation, rows

    def team_in(self):
        return "(" + ",".join(f"'{t}'" for t in self.teams) + ")" if self.teams else "(NULL)"

    def close(self):
        self.db.close()


# ---------------------------------------------------------------- handlers
# Each returns (answer, findings, charts, limitations); findings are (text, [citations]).

def survey_trend(q, dimension="Recognition", last=None):
    cite, rows = q.run(f"""SELECT Survey_Date, Team, Responses, Mean_Score, Favorable_Percent FROM HR_survey_summary
        WHERE Dimension = :dim AND Team IN {q.team_in()} AND Survey_Date BETWEEN :start AND :end
        AND Responses >= {SURVEY_MIN_RESPONSES} ORDER BY Survey_Date""", {"dim": dimension})
    if last:
        dates = sorted({r["Survey_Date"] for r in rows})[-last:]
        rows = [r for r in rows if r["Survey_Date"] in dates]
        q.evidence[-1]["rows"] = rows
    return cite, rows


def recognition_trend(q):
    cite, rows = survey_trend(q)
    if not rows:
        return f"No Recognition survey results meet the minimum response count in this period [{cite}].", [], [], []
    if len(rows) == 1:
        only = rows[0]
        text = (f"This period has a single Recognition survey ({_quarter(only['Survey_Date'])}): {only['Mean_Score']:.2f} out of 5, "
                f"{only['Favorable_Percent']:.0f}% favorable from {only['Responses']} responses. Choose a longer period to see a trend.")
        return f"{text} [{cite}]", [(text, [cite])], [], []
    first, prev, latest = rows[0], rows[-2], rows[-1]
    high = max(rows, key=lambda r: r["Mean_Score"])
    low = min(rows, key=lambda r: r["Mean_Score"])
    direction = "up" if latest["Mean_Score"] > prev["Mean_Score"] else "down" if latest["Mean_Score"] < prev["Mean_Score"] else "flat"
    findings = [
        (f"Recognition was {latest['Mean_Score']:.2f} out of 5 in {_quarter(latest['Survey_Date'])} "
         f"({latest['Favorable_Percent']:.0f}% favorable, {latest['Responses']} responses), {direction} from "
         f"{prev['Mean_Score']:.2f} the quarter before.", [cite]),
        (f"Across the period it moved from {first['Mean_Score']:.2f} ({_quarter(first['Survey_Date'])}) to "
         f"{latest['Mean_Score']:.2f} ({_signed(latest['Mean_Score'] - first['Mean_Score'])}), ranging from "
         f"{low['Mean_Score']:.2f} in {_quarter(low['Survey_Date'])} to {high['Mean_Score']:.2f} in {_quarter(high['Survey_Date'])}.", [cite]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    chart = {"source_id": cite, "kind": "line", "x": "Survey_Date", "y": "Mean_Score", "series": "Team",
             "title": "Recognition score by quarter", "x_label": "Survey date", "y_label": "Mean recognition score",
             "unit": "Score (1-5)", "denominator": "Responses"}
    limits = ["Survey scores are team averages for everyone surveyed in the team, which can include people outside your pilot roster.",
              "Quarter-to-quarter changes of a few tenths can reflect who responded, not a real change."]
    change = latest["Mean_Score"] - first["Mean_Score"]
    best = max(rows, key=lambda r: r["Favorable_Percent"])
    q.extra["impact"] = [
        (f"Recognition is {'below' if change < 0 else 'above' if change > 0 else 'level with'} where it started this period "
         f"({_signed(change)} on the 1-5 scale). Recognition is closely tied to engagement, so a sustained decline is an early "
         f"people risk worth acting on before it shows up in turnover." if change < 0 else
         f"Recognition has held or improved this period ({_signed(change)} on the 1-5 scale). Protecting what works is cheaper than "
         f"rebuilding trust after a decline."),
        f"Your best quarter reached {best['Favorable_Percent']:.0f}% favorable ({_quarter(best['Survey_Date'])}), so the team has "
        f"already shown what good looks like; the gap to close is {max(0, best['Favorable_Percent'] - latest['Favorable_Percent']):.0f} points.",
    ]
    q.extra["next_steps"] = [
        "Make recognition a standing item: name one specific contribution in each team meeting this month.",
        f"Ask the team what changed around {_quarter(best['Survey_Date'])}, the best quarter, and repeat the practices that worked.",
        "Review the trend again after the next survey before investing in a larger programme.",
    ]
    q.extra["watch"] = [{"metric": "Recognition survey favorable", "baseline": f"{latest['Favorable_Percent']:.0f}%",
                         "goal": f"above {min(100, round(best['Favorable_Percent']))}%"}]
    return answer, findings, [chart], limits


def recognition_eight_quarters(q):
    cite, rows = survey_trend(q, last=8)
    if not rows:
        return f"No Recognition survey results meet the minimum response count in this period [{cite}].", [], [], []
    if len(rows) == 1:
        only = rows[0]
        text = (f"This period contains one Recognition survey ({_quarter(only['Survey_Date'])}): {only['Favorable_Percent']:.0f}% favorable, "
                f"mean {only['Mean_Score']:.2f}. Choose \"All data\" to see eight quarters.")
        return f"{text} [{cite}]", [(text, [cite])], [], []
    favorable = [r["Favorable_Percent"] for r in rows]
    above4 = sum(r["Mean_Score"] >= 4 for r in rows)
    findings = [
        (f"Over the last {len(rows)} quarters in this period, Recognition favorability ranged from {min(favorable):.0f}% to "
         f"{max(favorable):.0f}%, and the mean score reached 4.0 or higher in {above4} of {len(rows)} quarters.", [cite]),
        (f"The latest quarter ({_quarter(rows[-1]['Survey_Date'])}) scored {rows[-1]['Mean_Score']:.2f} with "
         f"{rows[-1]['Favorable_Percent']:.0f}% favorable from {rows[-1]['Responses']} responses.", [cite]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    chart = {"source_id": cite, "kind": "line", "x": "Survey_Date", "y": "Favorable_Percent", "series": "Team",
             "title": "Recognition favorability, last eight quarters", "x_label": "Survey date",
             "y_label": "Favorable responses", "unit": "%", "denominator": "Responses"}
    latest = rows[-1]
    q.extra["impact"] = [
        f"Recognition favorability has swung by {max(favorable) - min(favorable):.0f} points across these quarters. Large swings make "
        "it hard for people to trust that good work will be noticed, which weakens discretionary effort.",
        f"The current {latest['Favorable_Percent']:.0f}% is {'at the low end' if latest['Favorable_Percent'] <= min(favorable) + 2 else 'within the range'} "
        "of what this team has seen, so a steady routine matters more than a one-off campaign.",
    ]
    q.extra["next_steps"] = [
        "Build a light, regular recognition habit (for example, a monthly shout-out round) instead of occasional big gestures.",
        "Check which quarters dipped and whether they lined up with deadlines or reorganisations, and plan recognition around those periods.",
    ]
    q.extra["watch"] = [{"metric": "Recognition survey favorable", "baseline": f"{latest['Favorable_Percent']:.0f}%", "goal": "hold steady"}]
    return answer, findings, [chart], ["Favorable % counts 4s and 5s; it is not the same metric as the mean score."]


def quarter_window(q):
    """The latest survey quarter inside the scope (three months ending on the latest survey date)."""
    latest = q.db.execute(f"""SELECT MAX(Survey_Date) FROM HR_survey_summary WHERE Team IN {q.team_in()}
        AND Survey_Date BETWEEN :start AND :end""", q.params).fetchone()[0]
    if not latest:
        return None, None
    end = date.fromisoformat(latest)
    start = (end.replace(day=1) - timedelta(days=62)).replace(day=1)
    return max(start.isoformat(), q.scope.start_date), latest


def this_quarter_recognition(q):
    start, end = quarter_window(q)
    if not end:
        return "There are no survey results in this period.", [], [], []
    c1, rows = q.run(f"""SELECT Survey_Date, Responses, Mean_Score, Favorable_Percent FROM HR_survey_summary
        WHERE Dimension = 'Recognition' AND Team IN {q.team_in()} AND Survey_Date <= :qend
        AND Survey_Date >= max(:start, date(:qend, '-6 months')) AND Responses >= {SURVEY_MIN_RESPONSES} ORDER BY Survey_Date""", {"qend": end})
    c2, work = q.run(f"""SELECT COUNT(*) AS Cross_Team_Contributions,
          SUM(EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID
              AND f.Interaction_Type = 'Partner feedback')) AS With_Partner_Feedback,
          SUM(EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID
              AND f.Interaction_Type = 'Manager recognition')) AS With_Manager_Recognition
        FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team
        AND c.Contribution_Date BETWEEN :qstart AND :qend""", {"qstart": start, "qend": end})
    findings = []
    if rows:
        latest = rows[-1]
        text = (f"In {_quarter(latest['Survey_Date'])}, Recognition scored {latest['Mean_Score']:.2f} out of 5 "
                f"({latest['Favorable_Percent']:.0f}% favorable, {latest['Responses']} responses)")
        if len(rows) > 1:
            text += f", {_signed(latest['Mean_Score'] - rows[-2]['Mean_Score'])} versus the previous quarter"
        findings.append((text + ".", [c1]))
    w = work[0]
    total = w["Cross_Team_Contributions"] or 0
    if total:
        praised, recognized = w["With_Partner_Feedback"] or 0, w["With_Manager_Recognition"] or 0
        findings.append((f"The team made {total} contributions to other teams that quarter; {praised} "
                         f"({100 * praised / total:.0f}%) have recorded partner feedback and {recognized} "
                         f"({100 * recognized / total:.0f}%) have a recorded manager recognition.", [c2]))
        if rows and rows[-1]["Favorable_Percent"] >= 70 and recognized / total < 0.5:
            findings.append(("Survey sentiment and recorded recognition point in different directions: people "
                             "report feeling recognized, but much cross-team work has no recognition record.", [c1, c2]))
    answer = " ".join(f"{text} " + " ".join(f"[{c}]" for c in cites) for text, cites in findings)
    chart_rows = [{"Measure": "Cross-team contributions", "Count": total},
                  {"Measure": "With partner feedback", "Count": w["With_Partner_Feedback"] or 0},
                  {"Measure": "With manager recognition", "Count": w["With_Manager_Recognition"] or 0}]
    q.evidence.append({"citation_id": "SQL3", "producer": "Cherry", "sql": f"-- reshaped from {c2} for charting",
                       "rows": chart_rows, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    chart = {"source_id": "SQL3", "kind": "bar", "x": "Measure", "y": "Count", "title": "Cross-team work this quarter",
             "x_label": "Measure", "y_label": "Contributions", "unit": "contributions"}
    limits = ["Recognition records cover formal feedback only; other conversations may be unrecorded.",
              "A missing record is not proof that the work went unrecognized."]
    if total:
        praised, recognized = w["With_Partner_Feedback"] or 0, w["With_Manager_Recognition"] or 0
        q.extra["impact"] = [
            f"Other teams praised {praised} of {total} contributions this quarter, but only {recognized} were recognized by a manager. "
            "That gap means the people other teams rely on are the least likely to hear it from their own manager, so work that "
            "crosses the org chart stays out of sight in reviews and planning.",
            "Closing the gap costs little: the praise already exists, it just has not been passed on.",
        ]
        q.extra["next_steps"] = [
            "Turn this quarter's partner praise into recognition: forward it with a personal note (see Gaps in the Your team panel).",
            "Agree with the managers whose teams you help most that partner feedback is copied to you.",
            "Set a simple target for next quarter: recognize at least half of the praised cross-team work.",
        ]
        q.extra["watch"] = [{"metric": "Cross-team work recognized by a manager", "baseline": f"{100 * recognized / total:.0f}%", "goal": "above 50%"}]
    return answer, findings, [chart], limits


def over_capacity_weeks(q):
    cite, rows = q.run(f"""WITH demand AS (
            SELECT Assigned_Employee_ID AS e, Week_Start AS w, SUM(Current_Estimated_Hours) AS h FROM OP_work_requests
            WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :start AND :end GROUP BY 1, 2),
        cap AS (
            SELECT Employee_ID AS e, Week_Start AS w, Available_Project_Hours AS a FROM OP_capacity
            WHERE Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :start AND :end AND Available_Project_Hours IS NOT NULL)
        SELECT d.w AS Week_Start, COUNT(*) AS People_With_Requests, SUM(d.h > c.a) AS People_Over_Capacity,
            ROUND(SUM(d.h), 1) AS Requested_Hours, ROUND(SUM(c.a), 1) AS Available_Hours
        FROM demand d JOIN cap c ON c.e = d.e AND c.w = d.w GROUP BY d.w ORDER BY d.w""")
    if not rows:
        return f"No weeks in this period have both requested and available hours recorded [{cite}].", [], [], []
    team_over = [r for r in rows if r["Requested_Hours"] > r["Available_Hours"]]
    any_over = [r for r in rows if r["People_Over_Capacity"]]
    worst = sorted(rows, key=lambda r: (-r["People_Over_Capacity"], r["Week_Start"]))[:3]
    findings = [
        (f"Across {len(rows)} weeks, the team as a whole was over its available project hours in {len(team_over)} week"
         f"{'' if len(team_over) == 1 else 's'}.", [cite]),
        (f"But individual overload is common: in {len(any_over)} of {len(rows)} weeks at least one person had more requested "
         f"hours than available hours, peaking at {worst[0]['People_Over_Capacity']} people in the week of {worst[0]['Week_Start']}.", [cite]),
        ("The busiest weeks were " + ", ".join(f"{r['Week_Start']} ({r['People_Over_Capacity']} people)" for r in worst)
         + ", which suggests work is unevenly spread rather than the team being short of hours.", [cite]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    chart = {"source_id": cite, "kind": "bar", "x": "Week_Start", "y": "People_Over_Capacity",
             "title": "People with more requested than available hours, by week", "x_label": "Week starting",
             "y_label": "People over capacity", "unit": "people"}
    limits = ["Weeks where leave or routine hours were not recorded are excluded; missing is not zero.",
              "Requested hours are current estimates, not hours actually worked."]
    excess = q.db.execute(f"""WITH demand AS (
            SELECT Assigned_Employee_ID AS e, Week_Start AS w, SUM(Current_Estimated_Hours) AS h FROM OP_work_requests
            WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :start AND :end GROUP BY 1, 2),
        cap AS (
            SELECT Employee_ID AS e, Week_Start AS w, Available_Project_Hours AS a FROM OP_capacity
            WHERE Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :start AND :end AND Available_Project_Hours IS NOT NULL)
        SELECT COALESCE(SUM(MAX(d.h - c.a, 0)), 0) AS over_hours, AVG(c.a) AS avg_available
        FROM demand d JOIN cap c ON c.e = d.e AND c.w = d.w""", q.params).fetchone()
    over_hours, per_week = excess["over_hours"] or 0, excess["avg_available"] or 0
    impact = [f"In {len(any_over)} of {len(rows)} weeks someone was asked for more hours than they had. Repeated overload "
              "is a delivery risk (missed dates, rework) and a burnout risk for the people carrying it."]
    if over_hours and per_week:
        impact.append(f"Requests exceeded individual capacity by about {over_hours:,.0f} hours in total, roughly "
                      f"{over_hours / per_week:,.0f} person-weeks of work at this team's average available hours. That is "
                      "unplanned work being absorbed rather than scheduled.")
    impact.append("Because the team as a whole was over capacity in only "
                  f"{len(team_over)} week{'' if len(team_over) == 1 else 's'}, much of this could be addressed by rebalancing work before adding headcount.")
    q.extra["impact"] = impact
    q.extra["next_steps"] = [
        f"Rebalance work in the busiest weeks first ({', '.join(r['Week_Start'] for r in worst[:2])}): move requests to people with spare hours.",
        "Agree an intake rule with requesting managers: new requests above a person's available hours need your sign-off.",
        "Use the weeks with spare capacity for the work that keeps slipping.",
    ]
    start, end = quarter_window(q)
    if end:
        weeks, over = _weeks_over(q, start, end)
        q.extra["watch"] = [{"metric": "Weeks with someone over project hours", "baseline": str(len(over)), "goal": "fewer each quarter"}]
    return answer, findings, [chart], limits


def contributions_without_recognition(q):
    cite, rows = q.run(f"""SELECT c.Beneficiary_Team AS Team_Helped, COUNT(*) AS Contributions,
          SUM(NOT EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID
              AND f.Interaction_Type = 'Manager recognition')) AS Without_Recognition_Note
        FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team
        AND c.Contribution_Date BETWEEN :start AND :end GROUP BY 1 ORDER BY Contributions DESC""")
    total = sum(r["Contributions"] for r in rows)
    if not total:
        return f"Your team recorded no cross-team contributions in this period [{cite}].", [], [], []
    missing = sum(r["Without_Recognition_Note"] for r in rows)
    top = rows[:3]
    findings = [
        (f"Of {total} contributions your team made to other teams, {missing} ({100 * missing / total:.0f}%) have no "
         f"recorded manager-recognition note.", [cite]),
        ("The teams helped most were " + ", ".join(f"{r['Team_Helped']} ({r['Contributions']}, {r['Without_Recognition_Note']} without a note)"
                                                   for r in top) + ".", [cite]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    q.evidence[-1]["rows"] = rows[:12]
    chart = {"source_id": cite, "kind": "bar", "x": "Team_Helped", "y": "Without_Recognition_Note",
             "title": "Cross-team contributions without a recognition note", "x_label": "Team helped",
             "y_label": "Contributions without a note", "unit": "contributions"}
    limits = ["An absent note is not proof that recognition never happened; it may have been given informally.",
              "Chart shows the 12 teams helped most."]
    q.extra["impact"] = [
        f"{100 * missing / total:.0f}% of your team's help to other teams has no recognition on record. Help that goes "
        "unrecognized can stop being volunteered, and cross-team help is what keeps shared projects moving.",
        f"{top[0]['Team_Helped']} relies on your team most ({top[0]['Contributions']} contributions); that relationship is "
        "where recognition, or its absence, is most visible.",
    ]
    q.extra["next_steps"] = [
        f"Start with {top[0]['Team_Helped']}: recognize the most recent help your team gave them and copy their manager.",
        "Ask the managers of the teams you help most to send partner feedback to you as well as to the person.",
        "Review the unrecognized list monthly in the Gaps tab of the Your team panel.",
    ]
    start, end = quarter_window(q)
    if end:
        work = _work_counts(q, start, end)
        if work["Cross_Team"]:
            q.extra["watch"] = [{"metric": "Cross-team work recognized by a manager",
                                 "baseline": f"{100 * work['Recognized'] / work['Cross_Team']:.0f}%", "goal": "above 50%"}]
    return answer, findings, [chart], limits


def biggest_survey_change(q):
    latest = q.db.execute(f"""SELECT MAX(Survey_Date) FROM HR_survey_summary WHERE Team IN {q.team_in()}
        AND Survey_Date BETWEEN :start AND :end""", q.params).fetchone()[0]
    if not latest:
        return "There are no survey results in this period.", [], [], []
    earlier = (date.fromisoformat(latest) - timedelta(days=370)).isoformat()
    cite, rows = q.run(f"""SELECT Dimension, Survey_Date, Mean_Score, Favorable_Percent, Responses FROM HR_survey_summary
        WHERE Team IN {q.team_in()} AND Dimension <> 'eNPS' AND Responses >= {SURVEY_MIN_RESPONSES}
        AND Survey_Date BETWEEN max(:start, :earlier) AND :latest ORDER BY Dimension, Survey_Date""",
        {"earlier": earlier, "latest": latest})
    by_dim = {}
    for r in rows:
        by_dim.setdefault(r["Dimension"], []).append(r)
    changes = [{"Dimension": d, "From": v[0]["Survey_Date"], "To": v[-1]["Survey_Date"],
                "Change": round(v[-1]["Mean_Score"] - v[0]["Mean_Score"], 2)} for d, v in by_dim.items() if len(v) >= 2]
    if not changes:
        return f"There is less than a year of comparable survey results in this period [{cite}].", [], [], []
    changes.sort(key=lambda c: c["Change"])
    up, down = changes[-1], changes[0]
    q.evidence.append({"citation_id": "SQL2", "producer": "Cherry", "sql": f"-- change per dimension computed from {cite}",
                       "rows": changes, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    findings = [
        (f"The biggest improvement was {up['Dimension']} ({_signed(up['Change'])} points between "
         f"{_quarter(up['From'])} and {_quarter(up['To'])}).", ["SQL2"]),
        (f"The biggest decline was {down['Dimension']} ({_signed(down['Change'])} points over the same window)." if down["Change"] < 0 else
         f"No area declined; the smallest gain was {down['Dimension']} ({_signed(down['Change'])} points).", ["SQL2"]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    chart = {"source_id": "SQL2", "kind": "bar", "x": "Dimension", "y": "Change",
             "title": "Change in mean survey score over the last year", "x_label": "Survey area",
             "y_label": "Change in mean score", "unit": "points"}
    current = _favorable_by_dimension(q, latest)
    impact = []
    if down["Change"] < 0:
        impact.append(f"{down['Dimension']} declined the most ({_signed(down['Change'])} on the 1-5 scale). A falling area is often where "
                      "disengagement shows up first, so it is the cheapest place to intervene now.")
    impact.append(f"{up['Dimension']} improved the most ({_signed(up['Change'])} on the 1-5 scale); whatever changed there is a practice "
                  "worth keeping and spreading.")
    q.extra["impact"] = impact
    q.extra["next_steps"] = [
        (f"Hold a short team conversation on {down['Dimension'].lower()}: what got harder this year, and one thing to change."
         if down["Change"] < 0 else "Ask the team which recent changes they value most, and protect them."),
        f"Keep doing what lifted {up['Dimension'].lower()}, and say so explicitly to the team.",
        "Re-check after the next survey to see whether the change holds.",
    ]
    q.extra["actions"] = _survey_actions(q, {c["Dimension"]: c["Change"] for c in changes}, q.teams[0] if len(q.teams) == 1 else "your", unit="mean")
    if down["Change"] < 0 and down["Dimension"] in current:
        q.extra["watch"] = [{"metric": f"{down['Dimension']} survey favorable", "baseline": f"{current[down['Dimension']][0]:.0f}%", "goal": "back above " +
                             f"{current[down['Dimension']][0] + 5:.0f}%"}]
    return answer, findings, [chart], ["Compares the first and last survey within the last 12 months of the period."]


def _tone(percent, good=70, fair=50):
    return "good" if percent >= good else "fair" if percent >= fair else "poor"


# Rough sizing only: hours in a full-time quarter, and a pay rate that is an assumption, not company data.
FTE_QUARTER_HOURS = 520
ASSUMED_HOURLY_COST = 45


def _visibility_sql(q):
    """Sorts each cross-team contribution into one group, by how far word of it travelled (needs :wstart, :wend)."""
    return f"""WITH c AS (
            SELECT w.Actual_Hours AS hours,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback') AS praised,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback' AND f.Shared_With_Home_Manager = 'Yes') AS shared,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition') AS recognized
            FROM OP_contributions c JOIN OP_work_requests w ON w.Work_Request_ID = c.Work_Request_ID
            WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :wstart AND :wend)
        SELECT COUNT(*) AS Cross_Team, COALESCE(SUM(hours), 0) AS Cross_Team_Hours,
          COALESCE(SUM(praised), 0) AS Praised, COALESCE(SUM(shared), 0) AS Praise_Reached,
          COALESCE(SUM(NOT recognized AND NOT praised), 0) AS No_Praise,
          COALESCE(SUM(NOT recognized AND praised AND NOT shared), 0) AS Praise_Not_Passed_On,
          COALESCE(SUM(NOT recognized AND shared), 0) AS Unrecognized,
          COALESCE(SUM(recognized), 0) AS Recognized,
          COALESCE(SUM(CASE WHEN NOT recognized AND NOT shared THEN hours END), 0) AS Unnoticed_Hours FROM c"""


def _unnoticed(v):
    return v["No_Praise"] + v["Praise_Not_Passed_On"]


# The answer card: one headline, a few number tiles, and actions the Action Center opens already filled in.
# Tile tones reuse the Gaps colours (no_praise, not_passed, unrecognized, recognized), plus money and neutral.
def _dollars(hours):
    return f"${round(hours * ASSUMED_HOURLY_COST, -2):,.0f}" if hours * ASSUMED_HOURLY_COST < 10000 else f"${round(hours * ASSUMED_HOURLY_COST / 1000):,.0f}k"


def _tile(value, label, icon, tone="neutral"):
    return {"value": value, "label": label, "icon": icon, "tone": tone}


def _person(example):
    return {"id": example["employee_id"], "name": example["name"]}


def _partner_contact(q, team=None):
    """The manager who requests most work from that team (or from the top partner team), for a pre-filled meeting."""
    for p in partner_actions(q, 10):
        if (team is None or p["Team"] == team) and p["Contact_Name"]:
            return {"team": p["Team"], "name": p["Contact_Name"], "email": p["Contact_Email"]}
    return {"team": team, "name": None, "email": None} if team else None


def org_overview(db, start, end):
    """Leadership view: department totals only, never a person's name. Not reachable through a manager's scope."""
    window = {"wstart": start, "wend": end}
    base = """WITH c AS (
            SELECT e.Department, w.Actual_Hours AS hours,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback') AS praised,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback' AND f.Shared_With_Home_Manager = 'Yes') AS shared,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition') AS recognized
            FROM OP_contributions c JOIN OP_work_requests w ON w.Work_Request_ID = c.Work_Request_ID JOIN HR_employees e ON e.Employee_ID = c.Employee_ID
            WHERE c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :wstart AND :wend)
        SELECT Department, COUNT(*) AS Cross_Team, COALESCE(SUM(hours), 0) AS Cross_Team_Hours,
          COALESCE(SUM(NOT recognized AND NOT praised), 0) AS No_Praise,
          COALESCE(SUM(NOT recognized AND praised AND NOT shared), 0) AS Praise_Not_Passed_On,
          COALESCE(SUM(NOT recognized AND shared), 0) AS Unrecognized,
          COALESCE(SUM(recognized), 0) AS Recognized,
          COALESCE(SUM(CASE WHEN NOT recognized AND NOT shared THEN hours END), 0) AS Unnoticed_Hours FROM c GROUP BY Department"""
    all_hours = {r["Department"]: r["Hours"] for r in db.execute("""SELECT e.Department, SUM(w.Actual_Hours) AS Hours FROM OP_work_requests w
        JOIN HR_employees e ON e.Employee_ID = w.Assigned_Employee_ID WHERE w.Week_Start BETWEEN :wstart AND :wend GROUP BY 1""", window)}
    departments = [{**dict(r), "All_Hours": all_hours.get(r["Department"], 0)} for r in db.execute(base, window)]
    departments.sort(key=lambda d: d["Unnoticed_Hours"], reverse=True)
    keys = ["Cross_Team", "Cross_Team_Hours", "No_Praise", "Praise_Not_Passed_On", "Unrecognized", "Recognized", "Unnoticed_Hours", "All_Hours"]
    totals = {k: sum(d[k] for d in departments) for k in keys}
    dependencies = [dict(r) for r in db.execute("""WITH teams AS (SELECT DISTINCT Team_Display_Name AS Team, Department FROM HR_employees)
        SELECT e.Department AS Helper, t.Department AS Helped, COUNT(*) AS Contributions, ROUND(SUM(w.Actual_Hours)) AS Hours
        FROM OP_contributions c JOIN HR_employees e ON e.Employee_ID = c.Employee_ID JOIN teams t ON t.Team = c.Beneficiary_Team
          JOIN OP_work_requests w ON w.Work_Request_ID = c.Work_Request_ID
        WHERE t.Department <> e.Department AND c.Contribution_Date BETWEEN :wstart AND :wend
        GROUP BY 1, 2 ORDER BY Hours DESC LIMIT 8""", window)]
    late = {r["Kind"]: r["Late_Percent"] for r in db.execute("""SELECT CASE WHEN Requesting_Team = Assigned_Employee_Team THEN 'inside' ELSE 'crossing' END AS Kind,
          ROUND(100.0 * AVG(Completion_Date > Original_Due_Date), 1) AS Late_Percent FROM OP_work_requests
        WHERE Week_Start BETWEEN :wstart AND :wend GROUP BY 1""", window)}
    return {"start": start, "end": end, "totals": totals, "departments": departments, "dependencies": dependencies,
            "late": late, "hours_per_fte": FTE_QUARTER_HOURS * 4, "assumed_hourly_cost": ASSUMED_HOURLY_COST}


def executive_summary(q):
    """The deck's opening slide for a meeting with executives. Team totals only, no names. "doing" and "need" are editable starting points."""
    start, end = quarter_window(q)
    if not end:
        return None
    v = dict(q.db.execute(_visibility_sql(q), {**q.params, "wstart": start, "wend": end}).fetchone())
    if not v["Cross_Team"]:
        return None
    unnoticed, hours = _unnoticed(v), v["Unnoticed_Hours"]
    return {
        "quarter": _quarter(end),
        "problem": f"{unnoticed} of {v['Cross_Team']} pieces of cross-team work went unnoticed, and {v['Unrecognized']} more went unrecognized.",
        "size": f"About {hours:,.0f} unnoticed hours, roughly {hours / FTE_QUARTER_HOURS:.1f} full-time people "
                f"(about ${round(hours * ASSUMED_HOURLY_COST, -3):,.0f} at an assumed ${ASSUMED_HOURLY_COST} an hour).",
        "doing": f"Recognizing the {v['Unrecognized']} pieces of praised work we already know about, and asking partner teams to share feedback with us.",
        "need": "Count cross-team hours in next quarter's plan.",
        "report": f"The unnoticed share next quarter (now {100 * unnoticed / v['Cross_Team']:.0f}%).",
        "note": "Synthetic data. The dollar figure uses an assumed rate and shows the size of the blind spot, not a saving.",
    }


def work_outside_goals(q):
    """Self-reviews against goals and records: work employees reported that was in no goal, and whether any record shows it."""
    if not q.db.execute("SELECT 1 FROM sqlite_master WHERE name = 'HR_self_review_items'").fetchone():
        return "Goals and self-reviews aren't loaded yet. Run data_extensions/generate_goal_reviews.py --load.", [], [], []
    base = f"""WITH items AS (
            SELECT i.*, e.Employee_Name, e.Team_Display_Name AS Home_Team,
              CASE WHEN i.Goal_Outcome IS NOT NULL OR i.Claimed_Goal_ID IS NOT NULL THEN 'In a goal'
                   WHEN i.Team_Helped = e.Team_Display_Name THEN 'Outside goals, own team'
                   WHEN EXISTS(SELECT 1 FROM OP_contributions c WHERE c.Employee_ID = i.Employee_ID AND c.Beneficiary_Team = i.Team_Helped
                               AND c.Contribution_Date BETWEEN '2025-01-01' AND '2025-12-31') THEN 'Outside goals, other team, on record'
                   ELSE 'Outside goals, other team, no record' END AS Grp
            FROM HR_self_review_items i JOIN HR_employees e ON e.Employee_ID = i.Employee_ID
            WHERE i.Employee_ID IN ({q.team_filter}) AND i.Review_Year = 2025)"""
    c1, groups = q.run(base + """ SELECT Grp AS Group_Name, COUNT(*) AS Items, COUNT(DISTINCT Employee_ID) AS People FROM items GROUP BY Grp ORDER BY Grp""")
    c2, unrecorded = q.run(base + """ SELECT Item_ID, Employee_ID, Employee_Name, Team_Helped, Item_Text, Submitted_Date FROM items
        WHERE Grp = 'Outside goals, other team, no record' ORDER BY Employee_ID""")
    by = {g["Group_Name"]: g for g in groups}
    total = sum(g["Items"] for g in groups)
    if not total:
        return f"Your team has no self-review items for 2025 [{c1}].", [], [], []
    planned = by.get("In a goal", {}).get("Items", 0)
    on_record = by.get("Outside goals, other team, on record", {}).get("Items", 0)
    no_record = by.get("Outside goals, other team, no record", {}).get("Items", 0)
    own = by.get("Outside goals, own team", {}).get("Items", 0)
    outside = total - planned
    findings = [
        (f"In their 2025 self-reviews your team reported {total} pieces of work; {outside} of them were in no goal.", [c1]),
        (f"{on_record + no_record} of those helped other teams, and {no_record} have no work or feedback record anywhere, so nobody would see them without the self-review.", [c1]),
    ]
    if own:
        findings.append((f"Another {own} were unplanned work inside your own team, such as covering for a colleague.", [c1]))
    answer = " ".join(f"{text} [{', '.join(c)}]" for text, c in findings)
    q.extra["examples"] = [{"contribution_id": r["Item_ID"], "employee_id": r["Employee_ID"], "name": r["Employee_Name"],
                            "team_helped": r["Team_Helped"], "date": r["Submitted_Date"], "outcome": r["Item_Text"],
                            "praise_reached_you": False, "self_review": True} for r in unrecorded[:5]]
    q.extra["examples_note"] = "Reported in their own self-review, with no work or feedback record anywhere."
    q.extra["impact"] = [
        f"{outside} of {total} reported pieces of work ({100 * outside / total:.0f}%) sit outside anyone's goals, so they are invisible to a goal-based review.",
        f"The {no_record} with no record exist only in the employee's own words: without this check they would never reach planning or recognition.",
    ]
    _, hours_rows = q.run(f"""SELECT COALESCE(ROUND(SUM(w.Actual_Hours)), 0) AS Hours FROM OP_contributions c
        JOIN OP_work_requests w ON w.Work_Request_ID = c.Work_Request_ID
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN '2025-01-01' AND '2025-12-31'""")
    hours = hours_rows[0]["Hours"]
    q.extra["headline"] = (f"{outside} of {total} things your team did in 2025 were in no goal, and {no_record} "
                           f"{'appears' if no_record == 1 else 'appear'} nowhere but the employee's own self-review.")
    q.extra["tiles"] = [
        _tile(f"{outside}", "pieces of work in no goal", "goal", "not_passed"),
        _tile(f"{no_record}", "found only in a self-review", "search", "no_praise"),
        _tile(f"{hours:,.0f} h", "of 2025 help to other teams on record", "hours", "unrecognized"),
        _tile(_dollars(hours), f"of that help (at ${ASSUMED_HOURLY_COST}/h, assumed)", "cost", "money"),
    ]
    actions = []
    for e in q.extra["examples"][:3]:
        first = e["name"].split()[0]
        actions.append({"kind": "one_to_one", "title": f"Ask {first} about it in your 1:1", "why": f"{e['outcome'].rstrip('.')}. In no goal, no record.",
                        "person": _person(e), "partner_team": e["team_helped"], "tone": "no_praise", "example_id": e["contribution_id"]})
    if q.extra["examples"]:
        e = q.extra["examples"][0]
        contact = _partner_contact(q, e["team_helped"])
        actions.append({"kind": "partner", "title": f"Tell {e['team_helped']} what {e['name'].split()[0]} did",
                        "why": "They benefit from the work, so they can confirm it and recognize it too.",
                        "partner": contact, "person": _person(e), "partner_team": e["team_helped"], "tone": "unrecognized"})
    actions.append({"kind": "goal", "title": "Add this work to next year's goals",
                    "why": f"{outside} pieces of work sat outside goals, so no review would have counted them.", "tone": "recognized"})
    q.extra["actions"] = actions
    q.extra["next_steps"] = [
        "Read the items with no record before reviews, and ask each person about the work in your one-to-one.",
        "Where the work matters, add it to next year's goals so it is planned and measured.",
        "Tell the teams who benefited, so the work is recognized on both sides.",
    ]
    rows = [{"Group": "In a goal", "Items": planned}, {"Group": "Outside goals, own team", "Items": own},
            {"Group": "Other team, on record", "Items": on_record}, {"Group": "Other team, no record", "Items": no_record}]
    q.evidence.append({"citation_id": f"SQL{len(q.evidence) + 1}", "producer": "Cherry", "sql": f"-- reshaped from {c1} for charting",
                       "rows": rows, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    chart = {"source_id": q.evidence[-1]["citation_id"], "kind": "bar", "x": "Group", "y": "Items",
             "title": "What your team reported in 2025 self-reviews", "x_label": "Where the work sits", "y_label": "Items", "unit": "items"}
    limits = ["Self-reviews are the employee's own account; an item with no record is reported, not confirmed.",
              "Matching is by employee, team helped and year, so a record about different work for the same team counts as a match.",
              "Goals and self-reviews are synthetic, generated to agree with the existing records."]
    return answer, findings, [chart], limits


def cross_team_slippage(q):
    """The business side of the same blind spot: what happens to requests that cross team lines?"""
    c1, rows = q.run(f"""SELECT CASE WHEN Requesting_Team = Assigned_Employee_Team THEN 'Inside your team' ELSE 'From another team' END AS Work_Type,
          COUNT(*) AS Requests, ROUND(SUM(Actual_Hours)) AS Hours,
          ROUND(100.0 * AVG(Completion_Date > Original_Due_Date), 1) AS Late_Percent,
          ROUND(100.0 * AVG(Current_Due_Date <> Original_Due_Date), 1) AS Date_Moved_Percent,
          ROUND(100.0 * AVG(Current_Priority <> Original_Priority), 1) AS Priority_Changed_Percent,
          ROUND(SUM(COALESCE(Rework_Hours, 0))) AS Rework_Hours
        FROM OP_work_requests WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :start AND :end
        GROUP BY 1 ORDER BY 1 DESC""")
    by_type = {r["Work_Type"]: r for r in rows}
    inside, crossing = by_type.get("Inside your team"), by_type.get("From another team")
    if not inside or not crossing:
        return f"There is not enough work on both sides of the team line to compare in this period [{c1}].", [], [], []
    share = 100 * crossing["Hours"] / (crossing["Hours"] + inside["Hours"])
    findings = [
        (f"{share:.0f}% of your team's hours ({crossing['Hours']:,.0f} of {crossing['Hours'] + inside['Hours']:,.0f}) went to requests from other teams.", [c1]),
        (f"{crossing['Late_Percent']:.1f}% of those requests finished after their original due date, against {inside['Late_Percent']:.1f}% of requests from inside your team.", [c1]),
        (f"Due dates moved on {crossing['Date_Moved_Percent']:.1f}% of them against {inside['Date_Moved_Percent']:.1f}%, and priorities changed on "
         f"{crossing['Priority_Changed_Percent']:.1f}% against {inside['Priority_Changed_Percent']:.1f}%.", [c1]),
    ]
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    q.extra["impact"] = [
        "Goals and reviews follow the org chart, but this work doesn't. Requests that cross it are where plans slip, and it is the same kind of work that goes unnoticed.",
    ]
    q.extra["headline"] = (f"Requests from other teams finish late {crossing['Late_Percent']:.0f}% of the time, "
                           f"against {inside['Late_Percent']:.0f}% inside your team.")
    q.extra["tiles"] = [
        _tile(f"{share:.0f}%", "of your team's hours go to other teams", "hours", "neutral"),
        _tile(f"{crossing['Late_Percent']:.0f}%", "of those requests finish late", "late", "no_praise"),
        _tile(f"{crossing['Rework_Hours']:,.0f} h", "of rework on other teams' requests", "rework", "unrecognized"),
        _tile(_dollars(crossing["Rework_Hours"]), f"of rework (at ${ASSUMED_HOURLY_COST}/h, assumed)", "cost", "money"),
    ]
    contact = _partner_contact(q)
    actions = []
    if contact:
        actions.append({"kind": "handoff", "title": f"Agree dates up front with {contact['team']}",
                        "why": f"Due dates moved on {crossing['Date_Moved_Percent']:.0f}% of requests from other teams.",
                        "partner": contact, "partner_team": contact["team"], "tone": "no_praise"})
    actions.append({"kind": "plan", "title": "Reserve capacity for other teams' requests",
                    "why": f"{crossing['Hours']:,.0f} hours went to them this period.", "tone": "money"})
    q.extra["actions"] = actions
    q.extra["next_steps"] = [
        "Agree due dates and priorities with the requesting manager when the request is made, not when it slips.",
        "Count cross-team requests when planning your team's capacity for next quarter.",
    ]
    chart = {"source_id": c1, "kind": "bar", "x": "Work_Type", "y": "Late_Percent", "title": "Requests finished after their original due date",
             "x_label": "Where the request came from", "y_label": "Late requests", "unit": "%"}
    limits = ["This shows that cross-team work slips more often, not that crossing teams is the cause.",
              "Echo's data is synthetic and almost no same-team request runs late in it, so the size of this gap comes from how the data was generated. Real data would need to confirm it."]
    return answer, findings, [chart], limits


def invisible_work(q):
    """The project's anchor story: is help given to other teams seen and recognized?"""
    start, end = quarter_window(q)
    if not end:
        return "There are no survey results in this period to anchor a quarter.", [], [], []
    window = {"qstart": start, "qend": end}
    c1, work = q.run(f"""WITH c AS (
            SELECT c.Contribution_ID, c.Home_Team <> c.Beneficiary_Team AS cross_team,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback') AS praised,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback' AND f.Shared_With_Home_Manager = 'Yes') AS shared,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition') AS recognized
            FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Contribution_Date BETWEEN :qstart AND :qend)
        SELECT SUM(cross_team) AS Cross_Team, SUM(cross_team AND praised) AS Praised, SUM(cross_team AND shared) AS Praise_Shared_With_You,
          SUM(cross_team AND recognized) AS Recognized, SUM(cross_team AND praised AND NOT recognized) AS Praised_Not_Recognized,
          SUM(NOT cross_team) AS Own_Team, SUM(NOT cross_team AND recognized) AS Own_Team_Recognized FROM c""", window)
    c2, survey = q.run(f"""SELECT Survey_Date, Responses, Mean_Score, Favorable_Percent FROM HR_survey_summary
        WHERE Dimension = 'Recognition' AND Team IN {q.team_in()} AND Survey_Date = :qend AND Responses >= {SURVEY_MIN_RESPONSES}""", window)
    c_groups, groups = q.run(_visibility_sql(q), {"wstart": start, "wend": end})
    v = groups[0]
    c3, voice = q.run(f"""SELECT COUNT(*) AS Responses, ROUND(100.0 * AVG(c.Response_Score >= 4)) AS Positive_Percent,
          ROUND(100.0 * AVG(c.Response_Score <= 2)) AS Negative_Percent
        FROM HR_survey_comments c JOIN HR_survey_summary s ON c.Survey_ID = s.Survey_ID
        WHERE c.Dimension = 'Recognition' AND c.Team IN {q.team_in()} AND c.Survey_Date = :qend AND s.Responses >= {SURVEY_MIN_RESPONSES}
        HAVING COUNT(*) >= {SURVEY_MIN_RESPONSES}""", window)
    c4, examples = q.run(f"""SELECT c.Contribution_ID, c.Employee_ID, c.Employee_Name, c.Beneficiary_Team AS Team_Helped, c.Contribution_Date,
          c.Business_Outcome, MAX(f.Shared_With_Home_Manager = 'Yes') AS Praise_Shared_With_You
        FROM OP_contributions c JOIN HR_recognition_feedback f ON f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback'
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :qstart AND :qend
          AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback r WHERE r.Contribution_ID = c.Contribution_ID AND r.Interaction_Type = 'Manager recognition')
        GROUP BY c.Contribution_ID ORDER BY Praise_Shared_With_You DESC, c.Contribution_Date LIMIT 3""", window)
    w = work[0]
    total = w["Cross_Team"] or 0
    if not total:
        return f"Your team recorded no cross-team contributions in {_quarter(end)} [{c1}].", [], [], []
    recognized_pct = 100 * (w["Recognized"] or 0) / total
    own_pct = 100 * (w["Own_Team_Recognized"] or 0) / w["Own_Team"] if w["Own_Team"] else None
    praised = w["Praised"] or 0
    favorable = survey[0]["Favorable_Percent"] if survey else None
    findings = [
        (f"In {_quarter(end)}, {_unnoticed(v)} of your team's {total} contributions to other teams went unnoticed: {v['No_Praise']} drew no praise, "
         f"and praise for {v['Praise_Not_Passed_On']} never reached you.", [c_groups]),
        (f"Another {v['Unrecognized']} reached you but have no recognition, and {w['Recognized']} ({recognized_pct:.0f}%) were recognized by a manager.", [c_groups]),
    ]
    if own_pct is not None:
        findings.append((f"Work for your own team was recognized {own_pct:.0f}% of the time, so cross-team help is "
                         f"{'less' if recognized_pct < own_pct else 'not less'} likely to be recognized.", [c1]))
    if favorable is not None:
        findings.append((f"Yet the team's Recognition survey is {favorable:.0f}% favorable "
                         f"({survey[0]['Mean_Score']:.2f} out of 5), so most people feel recognized overall.", [c2]))
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)

    feedback_tone = _tone(recognized_pct, 50, 25)
    voice_tone = _tone(favorable) if favorable is not None else None
    conflict = voice_tone is not None and (voice_tone == "good") != (feedback_tone == "good")
    q.extra["triangle"] = {
        "work": {"value": str(total), "label": "contributions to other teams", "tone": "neutral", "agent": "Cherry"},
        "feedback": {"value": f"{recognized_pct:.0f}%", "label": "of that work recognized by a manager", "tone": feedback_tone, "agent": "Cherry"},
        "voice": {"value": f"{favorable:.0f}%" if favorable is not None else "n/a",
                  "label": "say recognition is good" if favorable is not None else "not enough survey responses",
                  "tone": voice_tone or "neutral", "agent": "Vanilla"},
        "agreement": "conflict" if conflict else "aligned",
        "note": ("The records and the survey disagree: people feel recognized overall, but most help given to other teams "
                 "has no recognition record. Both can be true: informal thanks may be unrecorded, or the people doing the "
                 "most cross-team work may be a minority of respondents.") if conflict else
                "The records and the survey point the same way.",
    }
    if voice:
        q.extra["voice"] = {"topic": "Recognition", "responses": voice[0]["Responses"],
                            "positive": voice[0]["Positive_Percent"], "negative": voice[0]["Negative_Percent"]}
    q.extra["examples"] = [{"contribution_id": e["Contribution_ID"], "employee_id": e["Employee_ID"], "name": e["Employee_Name"],
                            "team_helped": e["Team_Helped"], "date": e["Contribution_Date"], "outcome": e["Business_Outcome"],
                            "praise_reached_you": bool(e["Praise_Shared_With_You"])} for e in examples]
    q.extra["impact"] = [
        f"{w['Praised_Not_Recognized']} pieces of cross-team work were praised by the team they helped but never recognized by a "
        "manager. The people other teams depend on are the ones going unrecognized, and their work stays out of reviews and planning.",
        f"About {v['Unnoticed_Hours']:,.0f} hours of cross-team work went unnoticed this quarter, roughly {v['Unnoticed_Hours'] / FTE_QUARTER_HOURS:.1f} full-time "
        f"people. At an assumed ${ASSUMED_HOURLY_COST} an hour that is about ${round(v['Unnoticed_Hours'] * ASSUMED_HOURLY_COST, -3):,.0f}: the size of the blind spot, not a saving.",
        (f"Help given to other teams is recognized {recognized_pct:.0f}% of the time versus {own_pct:.0f}% for own-team work, so "
         "the current signal to employees is that helping elsewhere does not count." if own_pct is not None and recognized_pct < own_pct else
         f"Only {recognized_pct:.0f}% of help given to other teams is recognized, so most of it is invisible in reviews."),
    ]
    q.extra["headline"] = f"{_unnoticed(v)} of {total} pieces of help your team gave other teams went unnoticed in {_quarter(end)}."
    q.extra["tiles"] = [
        _tile(f"{_unnoticed(v)}", "pieces of help nobody saw", "eye", "no_praise"),
        _tile(f"{v['Unnoticed_Hours']:,.0f} h", f"of unnoticed work, about {v['Unnoticed_Hours'] / FTE_QUARTER_HOURS:.1f} people's quarter", "hours", "not_passed"),
        _tile(_dollars(v["Unnoticed_Hours"]), f"of work off the books (at ${ASSUMED_HOURLY_COST}/h, assumed)", "cost", "money"),
        _tile(f"{v['Unrecognized']}", "praised, but never recognized", "award", "unrecognized"),
    ]
    actions = [{"kind": "recognize", "title": f"Recognize {e['name'].split()[0]}",
                "why": f"Helped {e['team_helped']}: {e['outcome'].rstrip('.')}.", "person": _person(e), "partner_team": e["team_helped"],
                "tone": "unrecognized" if e["praise_reached_you"] else "not_passed", "example_id": e["contribution_id"]}
               for e in q.extra["examples"]]
    contact = _partner_contact(q)
    if contact and v["Praise_Not_Passed_On"]:
        actions.append({"kind": "partner", "title": f"Ask {contact['team']} to copy you on feedback",
                        "why": f"Praise for {v['Praise_Not_Passed_On']} pieces of your team's work never reached you.",
                        "partner": contact, "partner_team": contact["team"], "tone": "not_passed"})
    actions.append({"kind": "plan", "title": "Put cross-team hours in next quarter's plan",
                    "why": f"{v['Cross_Team_Hours']:,.0f} hours went to other teams this quarter, and goals and plans follow the org chart.", "tone": "money"})
    q.extra["actions"] = actions
    q.extra["next_steps"] = [
        f"Start with the {v['Unrecognized']} pieces of praised work you already heard about: recognize the work specifically, naming the team it helped.",
        "Ask the managers your team helps most to copy you on partner feedback.",
        "Check again after next quarter's review using the measures below.",
    ]
    q.extra["journey"] = {"quarter": _quarter(end), "steps": [
        {"label": "Helped another team", "value": v["Cross_Team"]},
        {"label": "Praised by that team", "value": v["Praised"]},
        {"label": "Praise reached you", "value": v["Praise_Reached"]},
        {"label": "Recognized by a manager", "value": v["Recognized"]},
    ]}
    q.extra["watch"] = [
        {"metric": "Cross-team work recognized by a manager", "baseline": f"{recognized_pct:.0f}%", "goal": "above 50%"},
        {"metric": "Cross-team work unnoticed", "baseline": f"{100 * _unnoticed(v) / v['Cross_Team']:.0f}%" if v["Cross_Team"] else "n/a", "goal": "lower each quarter"},
        {"metric": "Recognition survey favorable", "baseline": f"{favorable:.0f}%" if favorable is not None else "n/a", "goal": "hold steady"},
    ]
    chart_rows = [{"Stage": "No praise", "Contributions": v["No_Praise"]},
                  {"Stage": "Praise not passed on", "Contributions": v["Praise_Not_Passed_On"]},
                  {"Stage": "Praised, not recognized", "Contributions": v["Unrecognized"]},
                  {"Stage": "Recognized", "Contributions": v["Recognized"]}]
    q.evidence.append({"citation_id": f"SQL{len(q.evidence) + 1}", "producer": "Cherry", "sql": f"-- reshaped from {c1} for charting",
                       "rows": chart_rows, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    chart = {"source_id": q.evidence[-1]["citation_id"], "kind": "bar", "x": "Stage", "y": "Contributions",
             "title": f"How far your team's cross-team work was seen ({_quarter(end)})", "x_label": "Stage", "y_label": "Contributions",
             "unit": "contributions"}
    limits = ["Recognition records cover formal feedback logged at quarterly reviews; informal thanks may be unrecorded.",
              "The survey covers everyone surveyed in the team, which can include people outside your pilot roster.",
              "Dollar figures use an assumed hourly rate, and Echo's data is synthetic.",
              "Use the examples to start a conversation, not to rate individuals."]
    return answer, findings, [chart], limits


# ---------------------------------------------------------------- meeting prep
# Briefs a manager opens right before a meeting. Same rules: scoped SQL, cited numbers, no AI.

QUARTER_SQL = "strftime('%Y', c.Contribution_Date) || '-Q' || ((CAST(strftime('%m', c.Contribution_Date) AS INTEGER) + 2) / 3)"


def _survey_dates(q):
    return [r[0] for r in q.db.execute(f"""SELECT DISTINCT Survey_Date FROM HR_survey_summary WHERE Team IN {q.team_in()}
        AND Survey_Date BETWEEN :start AND :end ORDER BY 1""", q.params)]


def _quarter_bounds(q, end_iso):
    end = date.fromisoformat(end_iso)
    start = (end.replace(day=1) - timedelta(days=62)).replace(day=1).isoformat()
    return max(start, q.scope.start_date), end_iso


def _cross_team(q, start, end, partner=None):
    """Cross-team contribution counts for a window, optionally for one partner team."""
    partner_filter = " AND c.Beneficiary_Team = :partner" if partner else ""
    return q.run(f"""WITH c AS (
            SELECT c.Employee_ID,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback') AS praised,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback' AND f.Shared_With_Home_Manager = 'Yes') AS shared,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition') AS recognized
            FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team
              AND c.Contribution_Date BETWEEN :wstart AND :wend{partner_filter})
        SELECT COUNT(*) AS Contributions, COUNT(DISTINCT Employee_ID) AS People, SUM(praised) AS Praised,
          SUM(shared) AS Praise_Shared_With_You, SUM(recognized) AS Recognized, SUM(praised AND NOT recognized) AS Praised_Not_Recognized FROM c""",
        {"wstart": start, "wend": end, **({"partner": partner} if partner else {})})


def _pct(part, whole):
    return 100 * (part or 0) / whole if whole else 0


def _change(now, before, unit=" pts", digits=0):
    if before is None:
        return None
    diff = now - before
    return f"{diff:+.{digits}f}{unit}" if round(diff, digits) else "no change"


def _praised_unrecognized(q, start, end, partner=None, limit=3):
    partner_filter = " AND c.Beneficiary_Team = :partner" if partner else ""
    _, rows = q.run(f"""SELECT c.Contribution_ID, c.Employee_ID, c.Employee_Name, c.Beneficiary_Team AS Team_Helped, c.Contribution_Date,
          c.Business_Outcome, MAX(f.Shared_With_Home_Manager = 'Yes') AS Praise_Shared_With_You
        FROM OP_contributions c JOIN HR_recognition_feedback f ON f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback'
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :wstart AND :wend{partner_filter}
          AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback r WHERE r.Contribution_ID = c.Contribution_ID AND r.Interaction_Type = 'Manager recognition')
        GROUP BY c.Contribution_ID ORDER BY Praise_Shared_With_You DESC, c.Contribution_Date LIMIT {int(limit)}""",
        {"wstart": start, "wend": end, **({"partner": partner} if partner else {})})
    return [{"contribution_id": e["Contribution_ID"], "employee_id": e["Employee_ID"], "name": e["Employee_Name"],
             "team_helped": e["Team_Helped"], "date": e["Contribution_Date"], "outcome": e["Business_Outcome"],
             "praise_reached_you": bool(e["Praise_Shared_With_You"])} for e in rows]


def team_meeting(q):
    dates = _survey_dates(q)
    if not dates:
        return "There are no survey results in this period to prepare from.", [], [], []
    latest, prev = dates[-1], (dates[-2] if len(dates) > 1 else None)
    start, end = _quarter_bounds(q, latest)
    c1, rows = q.run(f"""SELECT Dimension, Survey_Date, Favorable_Percent, Mean_Score, Responses FROM HR_survey_summary
        WHERE Team IN {q.team_in()} AND Dimension <> 'eNPS' AND Responses >= {SURVEY_MIN_RESPONSES}
        AND Survey_Date IN (:latest, :prev) ORDER BY Dimension, Survey_Date""", {"latest": latest, "prev": prev or latest})
    by_dim = {}
    for r in rows:
        by_dim.setdefault(r["Dimension"], {})[r["Survey_Date"]] = r
    changes = []
    for dim, v in sorted(by_dim.items()):
        if latest in v:
            before = v[prev]["Favorable_Percent"] if prev and prev in v else None
            changes.append({"Dimension": dim, "Favorable_Now": v[latest]["Favorable_Percent"],
                            "Change": round(v[latest]["Favorable_Percent"] - before, 1) if before is not None else None})
    c2, work = _cross_team(q, start, end)
    c3, load = q.run(f"""WITH demand AS (
            SELECT Assigned_Employee_ID AS e, Week_Start AS w, SUM(Current_Estimated_Hours) AS h FROM OP_work_requests
            WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :wstart AND :wend GROUP BY 1, 2),
        cap AS (SELECT Employee_ID AS e, Week_Start AS w, Available_Project_Hours AS a FROM OP_capacity
            WHERE Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :wstart AND :wend AND Available_Project_Hours IS NOT NULL)
        SELECT COUNT(*) AS Weeks, SUM(over > 0) AS Weeks_With_Overload, MAX(over) AS Peak_People_Over FROM (
            SELECT d.w, SUM(d.h > c.a) AS over FROM demand d JOIN cap c ON c.e = d.e AND c.w = d.w GROUP BY d.w)""",
        {"wstart": start, "wend": end})

    lookup = {c["Dimension"]: c for c in changes}
    metrics = []
    for dim in ("Engagement", "Recognition", "Workload", "Manager support"):
        if dim in lookup:
            c = lookup[dim]
            metrics.append({"label": f"{dim} (favorable)", "value": f"{c['Favorable_Now']:.0f}%",
                            "change": None if c["Change"] is None else (f"{c['Change']:+.0f} pts" if round(c["Change"]) else "no change"),
                            "tone": "neutral" if c["Change"] is None else "good" if c["Change"] > 0 else "poor" if c["Change"] < 0 else "neutral"})
    w = work[0]
    if w["Contributions"]:
        metrics.append({"label": "Cross-team help recognized", "value": f"{_pct(w['Recognized'], w['Contributions']):.0f}%",
                        "change": None, "tone": _tone(_pct(w["Recognized"], w["Contributions"]), 50, 25)})
    q.extra["metrics"] = metrics

    findings = []
    ranked = sorted([c for c in changes if c["Change"] is not None], key=lambda c: c["Change"])
    if ranked:
        up, down = ranked[-1], ranked[0]
        findings.append((f"Since the last survey, {up['Dimension']} improved most ({up['Change']:+.0f} points favorable, now {up['Favorable_Now']:.0f}%).", [c1]))
        if down["Change"] < 0:
            findings.append((f"{down['Dimension']} fell most ({down['Change']:+.0f} points, now {down['Favorable_Now']:.0f}%).", [c1]))
    if w["Contributions"]:
        findings.append((f"The team helped other teams {w['Contributions']} times this quarter ({w['People']} people); "
                         f"{w['Praised_Not_Recognized']} praised pieces of that work have no recognition yet.", [c2]))
    lw = load[0]
    if lw["Weeks"]:
        findings.append((f"Someone was booked beyond their available project hours in {lw['Weeks_With_Overload']} of {lw['Weeks']} weeks, "
                         f"peaking at {lw['Peak_People_Over']} people in one week.", [c3]))
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)

    talking = []
    if ranked:
        talking.append(f"Open with what's working: {ranked[-1]['Dimension']} is up {abs(ranked[-1]['Change']):.0f} points.")
        if ranked[0]["Change"] < 0:
            talking.append(f"Ask the team what's behind the drop in {ranked[0]['Dimension']}; listen before proposing fixes.")
    if w["Praised_Not_Recognized"]:
        talking.append(f"Call out help given to other teams: {w['Praised_Not_Recognized']} praised pieces of work are waiting for recognition.")
    if lw["Weeks_With_Overload"]:
        talking.append("Check how work is spread: the team has enough hours overall, but some people are regularly overbooked.")
    q.extra["next_steps"] = talking
    if ranked and ranked[0]["Change"] < 0:
        dim = ranked[0]["Dimension"]
        _, mood = q.run(f"""SELECT COUNT(*) AS Responses, ROUND(100.0 * AVG(c.Response_Score >= 4)) AS Positive_Percent,
              ROUND(100.0 * AVG(c.Response_Score <= 2)) AS Negative_Percent
            FROM HR_survey_comments c JOIN HR_survey_summary s ON c.Survey_ID = s.Survey_ID
            WHERE c.Dimension = :dim AND c.Team IN {q.team_in()} AND c.Survey_Date = :latest AND s.Responses >= {SURVEY_MIN_RESPONSES}
            HAVING COUNT(*) >= {SURVEY_MIN_RESPONSES}""", {"dim": dim, "latest": latest})
        if mood:
            q.extra["voice"] = {"topic": dim, "responses": mood[0]["Responses"], "positive": mood[0]["Positive_Percent"],
                                "negative": mood[0]["Negative_Percent"]}
    chart_rows = [{"Survey_Area": c["Dimension"], "Change": c["Change"]} for c in changes if c["Change"] is not None]
    charts = []
    if chart_rows:
        q.evidence.append({"citation_id": f"SQL{len(q.evidence) + 1}", "producer": "Cherry", "sql": f"-- change since last survey, from {c1}",
                           "rows": chart_rows, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
        charts.append({"source_id": q.evidence[-1]["citation_id"], "kind": "bar", "x": "Survey_Area", "y": "Change",
                       "title": f"Change in favorable % since the last survey ({_quarter(latest)})", "x_label": "Survey area",
                       "y_label": "Change", "unit": "points"})
    return answer, findings, charts, ["Survey results cover everyone surveyed in the team.",
                                      "Workload uses current estimates and skips weeks without recorded leave or routine hours."]


# Gallup's engagement hierarchy, as a "maps to" guide: Echo's survey topics resemble, but are not, Q12 items.
GALLUP_LEVEL = {
    "Role clarity": ("Basic needs", 1, "knowing what is expected"),
    "Workload": ("Basic needs", 1, "having what you need to do the work"),
    "Recognition": ("Individual", 2, "recognition or praise for good work"),
    "Manager support": ("Individual", 2, "someone who cares about you"),
    "Development": ("Growth", 4, "opportunities to learn and grow"),
    "Team climate": ("Teamwork", 3, "trusted relationships and quality work"),
    "Engagement": ("Overall", 0, "overall engagement"),
    "Benefits": ("Overall", 0, "satisfaction with programs and benefits"),
}

# Echo's own discussion prompts (written for Echo, not taken from Gallup materials).
DISCUSSION = {
    "Role clarity": ["Where are our priorities unclear right now?", "What would help us agree on what \"done\" looks like?"],
    "Workload": ["Which weeks felt unmanageable, and what caused them?", "What could we stop, delay or share?"],
    "Recognition": ["What recent work deserved more credit than it got?", "How should help we give other teams be made visible?"],
    "Manager support": ["What support would make the biggest difference this quarter?", "How often should we check in, and how?"],
    "Development": ["What skill would you like to build next?", "Where could a stretch assignment come from?"],
    "Team climate": ["When does this team work best together?", "What gets in the way of trust or collaboration?"],
    "Engagement": ["What makes this team a good place to work?", "What would make next quarter better?"],
    "Benefits": ["Which programs do people value, and which go unused? Why?"],
}

ACTIONS = {
    "Role clarity": ["Agree the top three priorities for the quarter in writing", "Add a weekly five-minute priorities check"],
    "Workload": ["Rebalance requests for the people most often overbooked", "Agree what the team can say no to"],
    "Recognition": ["Recognize praised cross-team work within a week", "Ask partner managers to copy you on feedback"],
    "Manager support": ["Schedule regular one-to-ones", "Ask each person what support helps them most"],
    "Development": ["Pair each person with one learning goal", "Rotate a stretch task each month"],
    "Team climate": ["Start meetings with a quick win from someone else", "Make handoffs between people explicit"],
    "Engagement": ["Pick one focus area as a team and review it monthly"],
    "Benefits": ["Share how to use the programs people value most"],
}


def state_of_the_team(q):
    """Team meeting prep that follows Gallup's State of the Team flow: goal, results, focus, review."""
    answer, findings, charts, limits = team_meeting(q)
    if not q.evidence or not q.evidence[0]["rows"]:
        return answer, findings, charts, limits
    rows = q.evidence[0]["rows"]
    dates = sorted({r["Survey_Date"] for r in rows})
    latest, prev = dates[-1], (dates[-2] if len(dates) > 1 else None)
    topics = {}
    for r in rows:
        topics.setdefault(r["Dimension"], {})[r["Survey_Date"]] = r["Favorable_Percent"]
    table = []
    for dim, by_date in topics.items():
        if latest not in by_date:
            continue
        level, rank, meaning = GALLUP_LEVEL.get(dim, ("Overall", 0, dim.lower()))
        change = round(by_date[latest] - by_date[prev], 1) if prev and prev in by_date else None
        table.append({"topic": dim, "favorable": by_date[latest], "change": change, "level": level, "rank": rank, "meaning": meaning})
    elements = [t for t in table if t["rank"] > 0] or table
    strengths = sorted(elements, key=lambda t: -t["favorable"])[:2]
    # Gallup advises building from the foundation up: weigh low scores and drops, favouring lower hierarchy levels.
    def need(t):
        return (100 - t["favorable"]) + (-t["change"] if t["change"] and t["change"] < 0 else 0) + (4 - t["rank"]) * 3
    opportunities = sorted([t for t in elements if t not in strengths], key=need, reverse=True)[:2]
    focus = opportunities[0] if opportunities else None
    metrics = {m["label"]: m for m in q.extra.get("metrics", [])}
    goals = []
    if "Cross-team help recognized" in metrics:
        goals.append("Make sure help given to other teams is seen and recognized")
    if any("overbooked" in step for step in q.extra.get("next_steps", [])):
        goals.append("Spread work so nobody is regularly overbooked")
    if focus:
        goals.append(f"Improve {focus['topic'].lower()} ({focus['meaning']})")
    q.extra["state_of_team"] = {
        "survey": _quarter(latest),
        "steps": [
            {"title": "Agree a team performance goal", "summary": "Candidate goals from the data. The team chooses one.", "items": goals[:3]},
            {"title": "Review the survey results together",
             "summary": "Start with strengths, then opportunities. Ask what surprised people.",
             "strengths": strengths, "opportunities": opportunities},
            {"title": "Choose one focus area and actions",
             "summary": f"Suggested focus: {focus['topic']}, part of the {focus['level'].lower()} level. Owners are agreed in the room." if focus else
                        "Choose the area the team believes matters most.",
             "focus": focus["topic"] if focus else None, "questions": DISCUSSION.get(focus["topic"], []) if focus else [],
             "actions": ACTIONS.get(focus["topic"], []) if focus else []},
            {"title": "Review and recalibrate",
             "summary": "Check in every few weeks: did we do what we said, and did it make a difference?",
             "items": ["Did we complete the actions we agreed?", "Did they make a difference to the focus area?",
                       "Recheck the focus area's favorability at the next survey."]},
        ],
        "note": "This guide draws loosely on Gallup's published team-engagement ideas. Echo's survey topics are not Gallup Q12 items, and Echo isn't affiliated with Gallup.",
    }
    if focus:
        q.extra["watch"] = [
            {"metric": f"{focus['topic']} favorable", "baseline": f"{focus['favorable']:.0f}%", "goal": "up at the next survey"},
            {"metric": "Agreed actions completed", "baseline": "0", "goal": "all by the next check-in"},
        ]
    return answer, findings, charts, limits


def partner_teams(q):
    return [dict(r) for r in q.db.execute(f"""SELECT c.Beneficiary_Team AS Team, COUNT(*) AS Contributions FROM OP_contributions c
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :start AND :end
        GROUP BY 1 ORDER BY 2 DESC""", q.params)]


def partner_actions(q, limit=10):
    """The partner picker: top teams helped, how much praise was lost, and who asked for the work (for a drafted email or invite)."""
    teams = [dict(r) for r in q.db.execute(f"""SELECT c.Beneficiary_Team AS Team, COUNT(*) AS Contributions,
          SUM(EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback')
              AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback' AND f.Shared_With_Home_Manager = 'Yes')
              AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition')) AS Praise_Not_Passed_On
        FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :start AND :end
        GROUP BY 1 ORDER BY 2 DESC LIMIT {int(limit)}""", q.params)]
    contacts = {}
    for r in q.db.execute(f"""SELECT w.Requesting_Team AS Team, m.Manager_Name, m.Contact_Email, COUNT(*) AS Requests
        FROM OP_work_requests w JOIN HR_managers m ON m.Manager_ID = w.Requested_By_Manager_ID
        WHERE w.Assigned_Employee_ID IN ({q.team_filter}) AND w.Week_Start BETWEEN :start AND :end AND m.Manager_ID <> :manager
        GROUP BY 1, 2 ORDER BY Requests DESC""", {**q.params, "manager": q.scope.manager_id}):
        contacts.setdefault(r["Team"], r)
    for team in teams:
        contact = contacts.get(team["Team"])
        team["Contact_Name"] = contact["Manager_Name"] if contact else None
        team["Contact_Email"] = contact["Contact_Email"] if contact else None
    return teams


def partner_meeting(q, question):
    teams = partner_teams(q)
    key = _key(question)
    match = next((t["Team"] for t in sorted(teams, key=lambda t: -len(t["Team"])) if _key(t["Team"]) in key), None)
    if not match:
        names = ", ".join(t["Team"] for t in teams[:5])
        return f"Your team didn't help a team by that name in this period. The teams helped most were {names}.", [], [], []
    c1, by_quarter = q.run(f"""SELECT {QUARTER_SQL} AS Quarter, COUNT(*) AS Contributions,
          SUM(EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback')) AS Praised
        FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Beneficiary_Team = :partner
          AND c.Contribution_Date BETWEEN :start AND :end GROUP BY 1 ORDER BY 1""", {"partner": match})
    c2, totals = _cross_team(q, q.scope.start_date, q.scope.end_date, match)
    t = totals[0]
    n = t["Contributions"] or 0
    q.extra["metrics"] = [
        {"label": f"Times your team helped {match}", "value": str(n), "change": None, "tone": "neutral"},
        {"label": "People involved", "value": str(t["People"]), "change": None, "tone": "neutral"},
        {"label": f"Praised by {match}", "value": f"{_pct(t['Praised'], n):.0f}%", "change": None, "tone": "neutral"},
        {"label": "Of that praise, reached you", "value": f"{_pct(t['Praise_Shared_With_You'], t['Praised']):.0f}%", "change": None,
         "tone": _tone(_pct(t["Praise_Shared_With_You"], t["Praised"]), 75, 50)},
        {"label": "Recognized by a manager", "value": f"{_pct(t['Recognized'], n):.0f}%", "change": None,
         "tone": _tone(_pct(t["Recognized"], n), 50, 25)},
    ]
    q.extra["examples"] = _praised_unrecognized(q, q.scope.start_date, q.scope.end_date, match)
    findings = [
        (f"Your team helped {match} {n} times in this period, involving {t['People']} people.", [c2]),
        (f"{match} sent written praise for {t['Praised']} of those; {t['Praise_Shared_With_You']} of the praise notes reached you, "
         f"and {t['Recognized']} pieces of work were recognized by a manager.", [c2]),
    ]
    if by_quarter:
        busiest = max(by_quarter, key=lambda r: r["Contributions"])
        findings.append((f"The busiest quarter for this partnership was {busiest['Quarter']} ({busiest['Contributions']} contributions).", [c1]))
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    missed = (t["Praised"] or 0) - (t["Praise_Shared_With_You"] or 0)
    q.extra["next_steps"] = [s for s in [
        f"Thank {match} for the feedback they gave on {t['Praised']} pieces of work." if t["Praised"] else None,
        f"Ask them to copy you on feedback: {missed} of their praise notes never reached you." if missed > 0 else None,
        f"Agree what's coming next quarter so your team can plan the help ({n} contributions so far)." if n else None,
        "Recognize the work listed below before or after the meeting." if q.extra["examples"] else None,
    ] if s]
    chart = {"source_id": c1, "kind": "bar", "x": "Quarter", "y": "Contributions", "title": f"Help given to {match}, by quarter",
             "x_label": "Quarter", "y_label": "Contributions", "unit": "contributions"}
    return answer, findings, [chart] if by_quarter else [], ["Recognition records cover formal feedback; informal thanks may be unrecorded."]


def quarterly_review(q):
    dates = _survey_dates(q)
    if len(dates) < 2:
        return "A quarterly review needs at least two quarters in the chosen period. Choose \"All data\" or \"Last 12 months\".", [], [], []
    now_start, now_end = _quarter_bounds(q, dates[-1])
    was_start, was_end = _quarter_bounds(q, dates[-2])
    c1, now = _cross_team(q, now_start, now_end)
    c2, was = _cross_team(q, was_start, was_end)
    c3, fav = q.run(f"""SELECT Survey_Date, Favorable_Percent FROM HR_survey_summary WHERE Dimension = 'Recognition'
        AND Team IN {q.team_in()} AND Survey_Date IN (:now, :was) AND Responses >= {SURVEY_MIN_RESPONSES} ORDER BY Survey_Date""",
        {"now": dates[-1], "was": dates[-2]})
    n, w = now[0], was[0]
    rec_now, rec_was = _pct(n["Recognized"], n["Contributions"]), _pct(w["Recognized"], w["Contributions"])
    reach_now, reach_was = _pct(n["Praise_Shared_With_You"], n["Praised"]), _pct(w["Praise_Shared_With_You"], w["Praised"])
    fav_by = {r["Survey_Date"]: r["Favorable_Percent"] for r in fav}
    metrics = [
        {"label": "Cross-team work recognized", "value": f"{rec_now:.0f}%", "change": _change(rec_now, rec_was),
         "tone": "good" if rec_now > rec_was else "poor" if rec_now < rec_was else "neutral"},
        {"label": "Praised work left unrecognized", "value": str(n["Praised_Not_Recognized"]),
         "change": _change(n["Praised_Not_Recognized"], w["Praised_Not_Recognized"], ""),
         "tone": "good" if n["Praised_Not_Recognized"] < w["Praised_Not_Recognized"] else "poor" if n["Praised_Not_Recognized"] > w["Praised_Not_Recognized"] else "neutral"},
        {"label": "Partner praise that reached you", "value": f"{reach_now:.0f}%", "change": _change(reach_now, reach_was),
         "tone": "good" if reach_now > reach_was else "poor" if reach_now < reach_was else "neutral"},
    ]
    if dates[-1] in fav_by:
        before = fav_by.get(dates[-2])
        metrics.append({"label": "Recognition survey (favorable)", "value": f"{fav_by[dates[-1]]:.0f}%",
                        "change": _change(fav_by[dates[-1]], before), "tone": "neutral"})
    q.extra["metrics"] = metrics
    findings = [
        (f"In {_quarter(dates[-1])}, {rec_now:.0f}% of your team's cross-team work was recognized by a manager, "
         f"compared with {rec_was:.0f}% in {_quarter(dates[-2])}.", [c1, c2]),
        (f"Praised work left unrecognized went from {w['Praised_Not_Recognized']} to {n['Praised_Not_Recognized']}.", [c1, c2]),
        (f"{reach_now:.0f}% of partner praise reached you, versus {reach_was:.0f}% the quarter before.", [c1, c2]),
    ]
    if dates[-1] in fav_by and dates[-2] in fav_by:
        findings.append((f"Recognition survey favorability moved from {fav_by[dates[-2]]:.0f}% to {fav_by[dates[-1]]:.0f}%.", [c3]))
    answer = " ".join(f"{text} " + " ".join(f"[{c}]" for c in cites) for text, cites in findings)
    c4, trend = q.run(f"""SELECT {QUARTER_SQL} AS Quarter, ROUND(100.0 * AVG(EXISTS(SELECT 1 FROM HR_recognition_feedback f
            WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition')), 1) AS Recognized_Percent
        FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team
          AND c.Contribution_Date BETWEEN :start AND :end GROUP BY 1 ORDER BY 1""")
    q.evidence[-1]["rows"] = trend[-6:]
    q.extra["next_steps"] = [
        "Keep what worked: share specific recognition for help given to other teams." if rec_now >= rec_was else
        "Recognition of cross-team help slipped; start with the praised work still waiting for recognition.",
        "Review the recognition queue together with your notes from last quarter.",
        "Decide whether the measures you track are still the right ones.",
    ]
    q.extra["examples"] = _praised_unrecognized(q, now_start, now_end)
    chart = {"source_id": c4, "kind": "line", "x": "Quarter", "y": "Recognized_Percent", "title": "Cross-team work recognized, by quarter",
             "x_label": "Quarter", "y_label": "Recognized", "unit": "%"}
    return answer, findings, [chart], ["Each quarter is compared using the same rules; recent work may still receive feedback at the next review."]

def _previous_window(q, start):
    """The three months before a quarter window, clipped to the scope; None when the scope has no earlier data."""
    end = date.fromisoformat(start) - timedelta(days=1)
    if end.isoformat() < q.scope.start_date:
        return None, None
    year, month = (end.year, end.month - 2) if end.month > 2 else (end.year - 1, end.month + 10)
    return max(date(year, month, 1).isoformat(), q.scope.start_date), end.isoformat()


def _favorable_by_dimension(q, survey_date):
    rows = q.db.execute(f"""SELECT Dimension, SUM(Favorable_Responses) * 100.0 / SUM(Responses) AS Favorable, SUM(Responses) AS Responses
        FROM HR_survey_summary WHERE Team IN {q.team_in()} AND Survey_Date = :d AND Dimension <> 'eNPS'
        AND Responses >= {SURVEY_MIN_RESPONSES} GROUP BY Dimension""", {"d": survey_date}).fetchall()
    return {r["Dimension"]: (r["Favorable"], r["Responses"]) for r in rows if r["Favorable"] is not None}


def _work_counts(q, start, end):
    """Cross-team contributions, praised ones, recognized ones and praised-but-unrecognized ones in a window."""
    row = q.db.execute(f"""WITH c AS (
            SELECT c.Home_Team <> c.Beneficiary_Team AS cross_team,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback') AS praised,
              EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition') AS recognized
            FROM OP_contributions c WHERE c.Employee_ID IN ({q.team_filter}) AND c.Contribution_Date BETWEEN :wstart AND :wend)
        SELECT COALESCE(SUM(cross_team), 0) AS Cross_Team, COALESCE(SUM(cross_team AND recognized), 0) AS Recognized,
          COALESCE(SUM(cross_team AND praised AND NOT recognized), 0) AS Praised_Not_Recognized FROM c""",
        {**q.params, "wstart": start, "wend": end}).fetchone()
    return dict(row)


def _weeks_over(q, start, end):
    rows = q.db.execute(f"""WITH demand AS (
            SELECT Assigned_Employee_ID AS e, Week_Start AS w, SUM(Current_Estimated_Hours) AS h FROM OP_work_requests
            WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :wstart AND :wend GROUP BY 1, 2),
        cap AS (
            SELECT Employee_ID AS e, Week_Start AS w, Available_Project_Hours AS a FROM OP_capacity
            WHERE Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN :wstart AND :wend AND Available_Project_Hours IS NOT NULL)
        SELECT d.w AS Week_Start, SUM(d.h > c.a) AS People_Over FROM demand d JOIN cap c ON c.e = d.e AND c.w = d.w
        GROUP BY d.w ORDER BY d.w""", {**q.params, "wstart": start, "wend": end}).fetchall()
    return len(rows), [r["Week_Start"] for r in rows if r["People_Over"]]


MORALE_AREAS = ("Engagement", "Team climate", "Workload", "Manager support")


def _overloaded(q, limit=2):
    """Team members most often over their available hours in the last 13 weeks of the period."""
    rows = q.db.execute(f"""WITH demand AS (
            SELECT Assigned_Employee_ID AS e, Week_Start AS w, SUM(Current_Estimated_Hours) AS h FROM OP_work_requests
            WHERE Assigned_Employee_ID IN ({q.team_filter}) AND Week_Start BETWEEN date(:end, '-91 days') AND :end GROUP BY 1, 2)
        SELECT c.Employee_ID AS id, c.Employee_Name AS name, SUM(d.h > c.Available_Project_Hours) AS weeks
        FROM demand d JOIN OP_capacity c ON c.Employee_ID = d.e AND c.Week_Start = d.w
        GROUP BY 1, 2 HAVING weeks > 0 ORDER BY weeks DESC, name LIMIT {int(limit)}""", q.params).fetchall()
    return [dict(r) for r in rows]


def _unthanked_helpers(q, limit=2):
    """Team members with the most cross-team help in the last quarter and no manager recognition for it."""
    rows = q.db.execute(f"""SELECT c.Employee_ID AS id, c.Employee_Name AS name, COUNT(*) AS pieces FROM OP_contributions c
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN date(:end, '-91 days') AND :end
          AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback f WHERE f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Manager recognition')
        GROUP BY 1, 2 ORDER BY pieces DESC, name LIMIT {int(limit)}""", q.params).fetchall()
    return [dict(r) for r in rows]


def _room(title, why, agenda, tone):
    return {"kind": "room", "title": title, "why": why, "tone": tone, "room": {"title": title.replace("Book a room for ", "").capitalize(), "agenda": agenda}}


def _email(title, why, subject, body, tone, to=None):
    return {"kind": "email", "title": title, "why": why, "tone": tone, "email": {"subject": subject, "body": body, **({"to": to} if to else {})}}


def _event(title, why, invitation, tone, team):
    return {"kind": "team_event", "title": title, "why": why, "tone": tone, "event": {"title": f"{team} {title.split()[-1].lower()}", "invitation": invitation}}


def _playbook(q, area, change, team, unit="pts"):
    """What a manager can do about one survey area, using the team's own records where they name someone.
    Each entry opens a tool: a 1:1 or meeting (scheduler), a room, a team event, or an email draft."""
    pts = f"{abs(change):.0f} points" if unit == "pts" else f"{abs(change):.2f} on the 1-5 scale"
    lead = f"{area} fell {pts}." if change <= -(5 if unit == "pts" else 0.2) else f"{area} is the team's lowest area."
    if area == "Workload":
        acts = [{"kind": "one_to_one", "title": f"Check workload with {p['name'].split()[0]}",
                 "why": f"Over their available hours in {p['weeks']} of the last 13 weeks.", "person": {"id": p["id"], "name": p["name"]}, "tone": "no_praise"}
                for p in _overloaded(q)]
        contact = _partner_contact(q)
        if contact:
            acts.append({"kind": "handoff", "title": f"Agree priorities with {contact['team']}",
                         "why": f"They send your team the most requests; agree what can wait before the next one lands.",
                         "partner": contact, "partner_team": contact["team"], "tone": "not_passed"})
        acts.append(_room("Book a room for a planning session", f"{lead} Pick one piece of work to drop or delay.",
                          "List what's on the team's plate, and agree one thing to drop or push back.", "unrecognized"))
        return acts
    if area == "Manager support":
        return [
            {"kind": "plan", "title": "Hold regular 1:1s", "why": f"{lead} Short, regular 1:1s are the most direct fix.", "tone": "no_praise"},
            _room("Book a room for open office hours", "A fixed weekly time anyone can drop in, without needing a reason.",
                  "Open office hours: bring anything that's blocking you.", "unrecognized"),
            _email("Ask the team what support they need", "Ask directly, and say what you'll change.", "What would help you most?",
                   "Hi all,\n\nThe survey says I could support you better, and I want to fix that. What is one thing I could do differently that would help you most?\n\nReply to me directly, or bring it to my office hours.\n\nThank you.", "not_passed"),
        ]
    if area == "Team climate":
        return [
            _event("Take the team out for lunch", f"{lead} Unstructured time together helps people reconnect.",
                   f"I'd like to take the {team} team out for lunch. It's optional and there's no agenda, just time together. Let me know about any dietary or accessibility needs.", "unrecognized", team),
            _room("Book a room for a team retro", "Ask what's making it harder to work together, and agree one change.",
                  "Team retro: what's working, what's getting in the way, one thing we change.", "no_praise"),
        ]
    if area == "Engagement":
        return [
            _room("Book a room for a team conversation", f"{lead} Ask what would make the work more worthwhile.",
                  "What gives you energy at work, what drains it, and one thing we change.", "no_praise"),
            {"kind": "plan", "title": "Give each person one piece of work they choose", "why": "Choice over some of the work is a cheap engagement lever.", "tone": "recognized"},
        ]
    if area == "Recognition":
        acts = [{"kind": "recognize", "title": f"Recognize {p['name'].split()[0]}",
                 "why": f"{p['pieces']} pieces of help to other teams last quarter, none recognized.", "person": {"id": p["id"], "name": p["name"]}, "tone": "unrecognized"}
                for p in _unthanked_helpers(q)]
        contact = _partner_contact(q)
        if contact:
            acts.append(_email(f"Ask {contact['team']} to share feedback", "Praise from partner teams often never reaches you.",
                               "Feedback on my team's work", f"Hi {contact['name'] or 'there'},\n\nMy team does a fair amount of work for yours. When it goes well (or doesn't), could you copy me in? I'd like to make sure the people involved hear it.\n\nThank you.", "not_passed", contact["email"]))
        return acts
    if area == "Development":
        return [
            {"kind": "plan", "title": "Hold a growth conversation with each person", "why": f"{lead} Ask what each person wants to learn next.", "tone": "no_praise"},
            {"kind": "goal", "title": "Add one development goal per person", "why": "Put growth in next year's goals so it gets time and is reviewed.", "tone": "recognized"},
        ]
    if area == "Role clarity":
        return [
            _room("Book a room to map who owns what", f"{lead} Agree owners for the work people are unsure about.",
                  "Walk through current work and agree one owner for each piece.", "no_praise"),
            _email("Send the team the agreed owners", "Write down what you agree, so it doesn't drift.", "Who owns what",
                   "Hi all,\n\nThanks for today. Here's who owns what, as we agreed:\n\n- \n\nIf anything is missing, tell me.", "not_passed"),
        ]
    return [_room(f"Book a room to talk about {area.lower()}", f"{area} {'fell' if change < 0 else 'changed'} by {pts}.", f"What's behind the change in {area.lower()}.", "neutral")]


def _thanks(team, area):
    return _email("Thank the team", f"{area} improved the most. Say you noticed.", "Thank you: our survey results",
                  f"Hi all,\n\nOur survey results improved this quarter, especially {area.lower()}. Thank you for the part each of you played.\n\nThank you.", "recognized")


def _survey_actions(q, changes, team, unit="pts"):
    """Actions for a survey answer: the playbook for the area that fell most, a second falling area if any, and a thank-you if one rose."""
    order = sorted(changes, key=changes.get)
    step = 5 if unit == "pts" else 0.2  # smaller moves are within survey noise
    falling = [a for a in order if changes[a] <= -step]
    acts = []
    if falling:
        acts += _playbook(q, falling[0], changes[falling[0]], team, unit)[:3]
        if len(falling) > 1:
            acts += _playbook(q, falling[1], changes[falling[1]], team, unit)[:1]
    else:
        lowest = order[0]
        acts += _playbook(q, lowest, changes[lowest], team, unit)[:2]
    best = order[-1]
    if changes[best] >= step:
        acts.append(_thanks(team, best))
    return acts[:4]


def team_morale(q):
    """How the team feels: engagement, team climate, workload and manager support, latest survey against the one before."""
    dates = [r[0] for r in q.db.execute(f"""SELECT DISTINCT Survey_Date FROM HR_survey_summary WHERE Team IN {q.team_in()}
        AND Survey_Date BETWEEN :start AND :end AND Responses >= {SURVEY_MIN_RESPONSES} ORDER BY 1 DESC LIMIT 2""", q.params)]
    if len(dates) < 2:
        return "There are not two surveys in this period to compare.", [], [], []
    latest, previous = dates
    areas = ", ".join(f"'{a}'" for a in MORALE_AREAS)
    cite, rows = q.run(f"""SELECT Survey_Date, Dimension, SUM(Responses) AS Responses,
          ROUND(SUM(Favorable_Percent * Responses) / SUM(Responses), 1) AS Favorable_Percent,
          ROUND(SUM(eNPS_Score * Responses) / SUM(Responses)) AS eNPS
        FROM HR_survey_summary WHERE Team IN {q.team_in()} AND Survey_Date IN (:latest, :previous) AND Responses >= {SURVEY_MIN_RESPONSES}
          AND Dimension IN ({areas}, 'eNPS') GROUP BY 1, 2 ORDER BY 2, 1""", {"latest": latest, "previous": previous})
    now = {r["Dimension"]: r for r in rows if r["Survey_Date"] == latest}
    before = {r["Dimension"]: r for r in rows if r["Survey_Date"] == previous}
    changes = {a: now[a]["Favorable_Percent"] - before[a]["Favorable_Percent"] for a in MORALE_AREAS if a in now and a in before}
    if not changes:
        return f"There are not enough survey responses to compare [{cite}].", [], [], []
    weakest = min((a for a in MORALE_AREAS if a in now), key=lambda a: now[a]["Favorable_Percent"])
    worst = min(changes, key=changes.get)
    falling = changes[worst] <= -5  # a smaller move is within survey noise
    focus = worst if falling else weakest
    average = sum(changes.values()) / len(changes)
    q_now, q_before = _quarter(latest), _quarter(previous)
    findings = [(f"Between {q_before} and {q_now}, {sum(c < 0 for c in changes.values())} of {len(changes)} morale areas fell: "
                 + ", ".join(f"{a} {now[a]['Favorable_Percent']:.0f}% favorable ({_signed(changes[a], 0)} pts)" for a in changes) + ".", [cite])]
    if "eNPS" in now and "eNPS" in before and now["eNPS"]["eNPS"] is not None:
        findings.append((f"eNPS moved from {before['eNPS']['eNPS']:.0f} to {now['eNPS']['eNPS']:.0f}.", [cite]))
    answer = " ".join(f"{text} [{c[0]}]" for text, c in findings)
    q.extra["headline"] = (f"Morale fell in {q_now}: {worst} is down {abs(changes[worst]):.0f} points." if falling else
                           f"Morale {'rose' if average >= 2 else 'held steady'} in {q_now}; {weakest} is the area with the most room to grow.")
    tiles = [_tile(f"{now[a]['Favorable_Percent']:.0f}%", f"{a} favorable ({_signed(changes[a], 0)} pts)", "people",
                   "no_praise" if changes[a] < -2 else "recognized" if changes[a] > 2 else "neutral") for a in dict.fromkeys([focus, "Engagement", "Team climate", "Workload"]) if a in changes][:3]
    if "eNPS" in now and now["eNPS"]["eNPS"] is not None:
        tiles.append(_tile(f"{now['eNPS']['eNPS']:.0f}", f"eNPS ({_signed(now['eNPS']['eNPS'] - before['eNPS']['eNPS'], 0)} since {q_before})" if "eNPS" in before else "eNPS",
                           "award", "recognized" if "eNPS" in before and now["eNPS"]["eNPS"] >= before["eNPS"]["eNPS"] else "no_praise"))
    q.extra["tiles"] = tiles[:4]
    team = q.teams[0] if len(q.teams) == 1 else "your"
    q.extra["actions"] = _survey_actions(q, changes, team)
    q.extra["impact"] = [("A falling survey area is often where disengagement shows up first, so it is the cheapest place to act now."
                          if falling else f"Morale moved {average:+.0f} points on average. Keeping it there costs less than winning it back.")]
    q.extra["next_steps"] = [a["title"] + "." for a in q.extra["actions"]]
    q.evidence.append({"citation_id": f"SQL{len(q.evidence) + 1}", "producer": "Cherry", "sql": f"-- reshaped from {cite} for charting",
                       "rows": [{"Area": a, "Change": round(c, 1)} for a, c in changes.items()], "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    chart = {"source_id": q.evidence[-1]["citation_id"], "kind": "bar", "x": "Area", "y": "Change",
             "title": f"Change in favorable answers, {q_before} to {q_now}", "x_label": "Survey area", "y_label": "Change", "unit": "pts"}
    limits = ["Survey results are team totals with at least five responses; no individual answer is shown.",
              "A change between two surveys can be noise; check whether it holds next quarter.",
              "A team lunch is an optional gesture, not a proven fix for morale."]
    return answer, findings, [chart], limits


def team_updates(q):
    """The manager's side panel: what changed in the latest survey quarter, recognition gaps, and goal measures.

    Team-level counts and record-level work items only; survey comment text is never read here. No model calls.
    """
    start, end = quarter_window(q)
    empty = {"quarter": None, "previous_quarter": None, "as_of": None, "updates": [], "gaps": [], "gaps_total": 0, "measures": {}, "visibility": None}
    if not end:
        return empty
    prev_start, prev_end = _previous_window(q, start)
    updates = []

    dates = [r[0] for r in q.db.execute(f"""SELECT DISTINCT Survey_Date FROM HR_survey_summary WHERE Team IN {q.team_in()}
        AND Survey_Date BETWEEN :start AND :end ORDER BY Survey_Date DESC LIMIT 2""", q.params)]
    if len(dates) == 2:
        now, before = _favorable_by_dimension(q, dates[0]), _favorable_by_dimension(q, dates[1])
        if "Recognition" in now and "Recognition" in before:
            (n, responses), (b, _) = now["Recognition"], before["Recognition"]
            verb = "fell" if n <= b - 1 else "rose" if n >= b + 1 else "held steady"
            updates.append({"id": "recognition", "tone": "down" if verb == "fell" else "up" if verb == "rose" else "flat",
                            "title": f"Recognition favorable {verb} {'at' if verb == 'held steady' else 'to'} {n:.0f}%",
                            "detail": f"Was {b:.0f}% in {_quarter(dates[1])} · survey, {responses} responses",
                            "question": "How is recognition trending for my team?"})
        moves = [(d, now[d][0] - before[d][0], before[d][0], now[d][0]) for d in now if d in before and d != "Recognition"]
        if moves:
            dim, change, b, n = max(moves, key=lambda m: abs(m[1]))
            if abs(change) >= 3:
                updates.append({"id": "survey-area", "tone": "up" if change > 0 else "down",
                                "title": f"{dim} favorable {'rose' if change > 0 else 'fell'} {abs(change):.0f} points",
                                "detail": f"{b:.0f}% → {n:.0f}% since {_quarter(dates[1])} · survey",
                                "question": "Which survey area changed most over the last year?"})

    weeks, over = _weeks_over(q, start, end)
    if weeks:
        before_over = len(_weeks_over(q, prev_start, prev_end)[1]) if prev_start else None
        updates.append({"id": "capacity", "tone": "warn" if over else "up",
                        "title": f"{len(over)} week{'' if len(over) == 1 else 's'} had someone over project hours" if over else
                                 "No one went over project hours",
                        "detail": f"Out of {weeks} weeks in {_quarter(end)}" + (f" · {before_over} the quarter before" if before_over is not None else ""),
                        "question": "Which weeks exceed available project hours?"})

    work = _work_counts(q, start, end)
    if work["Cross_Team"]:
        before = _work_counts(q, prev_start, prev_end)["Cross_Team"] if prev_start else None
        trend = "" if before is None else (f" · up from {before}" if work["Cross_Team"] > before else
                                           f" · down from {before}" if work["Cross_Team"] < before else " · same as")
        updates.append({"id": "cross-team", "tone": "up" if before is not None and work["Cross_Team"] > before else "flat",
                        "title": f"{work['Cross_Team']} pieces of cross-team work in {_quarter(end)}",
                        "detail": f"Work records{trend}{' the quarter before' if before is not None else ''}",
                        "question": "Is my team's cross-team work being recognized?"})

    gaps = [dict(r) for r in q.db.execute(f"""SELECT c.Contribution_ID, c.Employee_ID, c.Employee_Name, c.Beneficiary_Team AS Team_Helped,
          c.Contribution_Date, c.Business_Outcome, MAX(f.Shared_With_Home_Manager = 'Yes') AS Praise_Shared_With_You
        FROM OP_contributions c JOIN HR_recognition_feedback f ON f.Contribution_ID = c.Contribution_ID AND f.Interaction_Type = 'Partner feedback'
        WHERE c.Employee_ID IN ({q.team_filter}) AND c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN :qstart AND :qend
          AND NOT EXISTS(SELECT 1 FROM HR_recognition_feedback r WHERE r.Contribution_ID = c.Contribution_ID AND r.Interaction_Type = 'Manager recognition')
        GROUP BY c.Contribution_ID ORDER BY c.Contribution_Date LIMIT 50""", {**q.params, "qstart": start, "qend": end})]
    as_of = date.fromisoformat(end)
    gap_items = [{"contribution_id": g["Contribution_ID"], "employee_id": g["Employee_ID"], "name": g["Employee_Name"],
                  "team_helped": g["Team_Helped"], "date": g["Contribution_Date"], "outcome": g["Business_Outcome"],
                  "praise_reached_you": bool(g["Praise_Shared_With_You"]),
                  "age_days": (as_of - date.fromisoformat(g["Contribution_Date"])).days} for g in gaps]
    if work["Praised_Not_Recognized"]:
        updates.append({"id": "gaps", "tone": "todo",
                        "title": f"{work['Praised_Not_Recognized']} praised contribution{'' if work['Praised_Not_Recognized'] == 1 else 's'} not yet recognized",
                        "detail": f"Oldest from {gap_items[0]['date']} · see Gaps" if gap_items else "See Gaps",
                        "action": "gaps"})

    # Same definitions as the "How you'll know it helped" measures in the recognition brief, so saved goals can be compared.
    survey = q.db.execute(f"""SELECT Favorable_Percent FROM HR_survey_summary WHERE Dimension = 'Recognition' AND Team IN {q.team_in()}
        AND Survey_Date = :qend AND Responses >= {SURVEY_MIN_RESPONSES}""", {"qend": end}).fetchone()
    measures = {"Praised cross-team work left unrecognized": str(work["Praised_Not_Recognized"]),
                "Weeks with someone over project hours": str(len(over)) if weeks else None}
    if dates:
        for dim, (fav, _) in _favorable_by_dimension(q, dates[0]).items():
            measures[f"{dim} survey favorable"] = f"{fav:.0f}%"
    measures = {k: v for k, v in measures.items() if v is not None}
    visibility = dict(q.db.execute(_visibility_sql(q), {**q.params, "wstart": start, "wend": end}).fetchone())
    if visibility["Cross_Team"]:
        measures["Cross-team work unnoticed"] = f"{100 * _unnoticed(visibility) / visibility['Cross_Team']:.0f}%"
    if work["Cross_Team"]:
        measures["Cross-team work recognized by a manager"] = f"{100 * work['Recognized'] / work['Cross_Team']:.0f}%"
    if survey:
        measures["Recognition survey favorable"] = f"{survey['Favorable_Percent']:.0f}%"
    return {"quarter": _quarter(end), "previous_quarter": _quarter(prev_end) if prev_end else None, "as_of": end,
            "updates": updates, "gaps": gap_items, "gaps_total": work["Praised_Not_Recognized"], "measures": measures,
            "visibility": visibility if visibility["Cross_Team"] else None}


GUARDRAIL = re.compile(r"\b(who (said|wrote|complained|posted|is unhappy|feels|thinks|answered)|which (employee|person|people|colleague)s? "
                       r"(said|wrote|complained|feel|answered)|identify|de-?anonymi[sz]e|name the (person|people|employee)|which comment)\b")


def guarded(question):
    return bool(GUARDRAIL.search(question.lower()))


def declined(scope, question):
    answer = ("Echo can't identify who wrote a survey response. Responses are anonymous by design, and using Echo to "
              "trace them back to people would break the trust the survey depends on. I can show what the team is saying "
              "as overall themes, or look at recorded work and feedback, which are not anonymous.")
    artifact = {"agent": "Original", "question": question, "answer": answer, "scope": scope.__dict__, "evidence": [],
                "mode": "offline-demo", "status": "declined", "verification": {"decision": "declined", "drafts_checked": 1},
                "delegations": [], "visualization": {"charts": []}, "rag": {}, "execution": {}, "sentiment": {}, "findings": [],
                "limitations": [], "next_steps": ["Open Team pulse to see themes from the survey without individual responses.",
                                                  "Ask \"Is my team's cross-team work being recognized?\" to look at recorded work instead."],
                "clarification_questions": [], "failure": {},
                "guardrail": {"rule": "No re-identification of anonymous survey responses",
                              "checked_by": "ZeroSugar", "detail": "Requests to find out who said something are declined before any data is read."}}
    return artifact, events(scope, 0, False, 0, declined=True)


HANDLERS = [
    ("prepare me for a team meeting", state_of_the_team),
    ("prepare me for my quarterly review", quarterly_review),
    ("cross team work being recognized", invisible_work),
    ("cross team work goes unnoticed", invisible_work),
    ("work that crosses team lines", cross_team_slippage),
    ("wasn t in their goals", work_outside_goals),
    ("how is recognition trending", recognition_trend),
    ("this quarter s recognition metrics", this_quarter_recognition),
    ("recognition over eight quarters", recognition_eight_quarters),
    ("weeks exceed available project hours", over_capacity_weeks),
    ("contributions lack a recognition note", contributions_without_recognition),
    ("survey area changed most", biggest_survey_change),
    ("team s morale", team_morale),
]


def supported(question):
    key = _key(question)
    return next((handler for phrase, handler in HANDLERS if phrase in key), None)


def build(database, scope, question):
    """Returns (artifact, events) for a supported question, or None."""
    if guarded(question):
        return declined(scope, question)
    handler = supported(question)
    partner = "prepare me for a meeting with" in _key(question)
    if handler is None and not partner:
        return None
    q = Query(database, scope)
    try:
        answer, findings, charts, limits = partner_meeting(q, question) if partner else handler(q)
        # Deterministic check: replay each cited query as shown and confirm every cited row comes back.
        replay_ok = True
        for item in q.evidence:
            if item["sql"].startswith("--"):
                continue
            replayed = [dict(r) for r in q.db.execute(item["sql"])]
            replay_ok &= all(row in replayed for row in item["rows"])
    finally:
        q.close()
    finding_items = [{"finding_id": f"F{i + 1}", "text": text, "citation_ids": cites, "status": "supported",
                      "reason": "Numbers recomputed from the cited query.", "deterministic_issues": []}
                     for i, (text, cites) in enumerate(findings)]
    artifact = {
        "agent": "Original", "question": question, "answer": answer or "No answer.", "scope": scope.__dict__,
        "evidence": q.evidence, "tool_trace": [], "mode": "offline-demo", "status": "complete",
        "verification": {"decision": "accept" if replay_ok else "revise", "reviews": [], "drafts_checked": 1},
        "delegations": [{"agent": "Cherry", "question": question, "answer": "Ran scoped SQL for the requested metrics.",
                         "scope": scope.__dict__, "evidence": q.evidence}],
        "connections": {}, "visualization": {"charts": charts, "reason": "Chart chosen by a fixed offline rule." if charts else
                                              "No chart for this question.", "mode": "offline-demo", "tool_trace": [], "files": []},
        "rag": {}, "execution": {"generation_api_calls": 0, "successful_generation_api_calls": 0,
                                 "note": "Offline demo: templated answer computed from the data, no AI."},
        "sentiment": {}, "findings": finding_items, "limitations": limits, "next_steps": [],
        "clarification_questions": [], "failure": {}, "diagnostics": {},
    }
    artifact.update(q.extra)
    return artifact, events(scope, len([e for e in q.evidence if not e["sql"].startswith("--")]), bool(charts),
                            len(finding_items), voice="voice" in q.extra)


def unsupported(scope, question):
    answer = ("The offline demo can answer the suggested questions using your team's real data. "
              "For other questions, switch to Live AI.")
    artifact = {"agent": "Original", "question": question, "answer": answer, "scope": scope.__dict__, "evidence": [],
                "mode": "offline-demo", "status": "needs_clarification", "verification": {}, "delegations": [],
                "visualization": {"charts": []}, "rag": {}, "execution": {}, "sentiment": {}, "findings": [],
                "limitations": [], "next_steps": [], "clarification_questions": [], "failure": {}}
    return artifact, events(scope, 0, False, 0, plan_only=True)


def events(scope, queries, chart, findings, plan_only=False, voice=False, declined=False):
    """An execution log in Echo's format, so the agent strip lights up the same way as a live run."""
    run_id = "offline_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    clock = [0.0]
    log = []

    def add(event, step=0.4, **fields):
        clock[0] += step
        log.append({"time_utc": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                    "elapsed_seconds": round(clock[0], 2), "event": event, **fields})

    add("run_started", 0, agent="original", mode="offline_demo")
    add("scope_ready", **scope.__dict__)
    add("model_started", agent="Original", profile="offline_fixture")
    add("model_finished", agent="Original", profile="offline_fixture", tools=["submit_plan"])
    add("workflow_plan", agent="Original", needs_numbers=not (plan_only or declined), needs_text=voice, include_chart=chart,
        needs_clarification=plan_only)
    if declined:
        add("model_started", agent="ZeroSugar", profile="offline_fixture", step=0.6)
        add("model_finished", agent="ZeroSugar", profile="offline_fixture", tools=["submit_review"])
        add("verification_finished", agent="ZeroSugar", decision="declined", step=0.6)
        add("response_finished", status="declined")
        add("run_finished", status="declined")
        return log
    if plan_only:
        add("response_finished", status="needs_clarification")
        add("run_finished", status="needs_clarification")
        return log
    add("tool_started", agent="Original", tool="ask_cherry")
    add("agent_started", agent="Cherry")
    add("tool_started", agent="Cherry", tool="describe_schema")
    add("tool_finished", agent="Cherry", tool="describe_schema")
    for _ in range(max(1, queries)):
        add("tool_started", agent="Cherry", tool="execute_sql")
        add("tool_finished", agent="Cherry", tool="execute_sql", step=0.6)
    add("agent_finished", agent="Cherry")
    add("tool_finished", agent="Original", tool="ask_cherry")
    if voice:
        add("tool_started", agent="Original", tool="ask_vanilla")
        add("agent_started", agent="Vanilla")
        add("tool_started", agent="Vanilla", tool="summarize_voice", step=0.6)
        add("tool_finished", agent="Vanilla", tool="summarize_voice", step=0.9)
        add("agent_finished", agent="Vanilla")
        add("tool_finished", agent="Original", tool="ask_vanilla")
    add("model_started", agent="Original", profile="offline_fixture")
    add("model_finished", agent="Original", profile="offline_fixture", step=0.6)
    add("model_started", agent="Lime", profile="offline_fixture")
    add("model_finished", agent="Lime", profile="offline_fixture", tools=["submit_visuals"])
    add("visual_plan_validated", agent="Lime", charts=1 if chart else 0)
    add("model_started", agent="ZeroSugar", profile="offline_fixture")
    add("model_finished", agent="ZeroSugar", profile="offline_fixture", tools=["submit_review"])
    for i in range(findings):
        add("finding_reviewed", agent="ZeroSugar", finding_id=f"F{i + 1}", status="supported", step=0.3)
    add("verification_finished", agent="ZeroSugar", decision="accept")
    add("response_finished", status="complete")
    add("run_finished", status="complete")
    return log
