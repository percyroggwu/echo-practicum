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
    return answer, findings, [chart], ["Compares the first and last survey within the last 12 months of the period."]


def _tone(percent, good=70, fair=50):
    return "good" if percent >= good else "fair" if percent >= fair else "poor"


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
        (f"In {_quarter(end)} your team made {total} contributions to other teams; {praised} drew written praise from the team "
         f"they helped, but only {w['Recognized']} ({recognized_pct:.0f}%) were recognized by a manager.", [c1]),
    ]
    if own_pct is not None:
        findings.append((f"Work for your own team was recognized {own_pct:.0f}% of the time, so cross-team help is "
                         f"{'less' if recognized_pct < own_pct else 'not less'} likely to be recognized.", [c1]))
    if praised:
        findings.append((f"{w['Praised_Not_Recognized']} praised contributions have no recognition, and "
                         f"{w['Praise_Shared_With_You']} of the praise notes were sent to you.", [c1]))
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
    q.extra["next_steps"] = [
        f"Start with the {w['Praise_Shared_With_You']} praise notes already sent to you: recognize the work specifically, naming the team it helped.",
        "Ask the managers your team helps most to copy you on partner feedback.",
        "Check again after next quarter's review using the measures below.",
    ]
    q.extra["watch"] = [
        {"metric": "Cross-team work recognized by a manager", "baseline": f"{recognized_pct:.0f}%", "goal": "above 50%"},
        {"metric": "Praised cross-team work left unrecognized", "baseline": str(w["Praised_Not_Recognized"]), "goal": "fewer each quarter"},
        {"metric": "Recognition survey favorable", "baseline": f"{favorable:.0f}%" if favorable is not None else "n/a", "goal": "hold steady"},
    ]
    chart_rows = [{"Stage": "Helped another team", "Contributions": total},
                  {"Stage": "Praised by that team", "Contributions": praised},
                  {"Stage": "Praise reached you", "Contributions": w["Praise_Shared_With_You"] or 0},
                  {"Stage": "Recognized by a manager", "Contributions": w["Recognized"] or 0}]
    q.evidence.append({"citation_id": f"SQL{len(q.evidence) + 1}", "producer": "Cherry", "sql": f"-- reshaped from {c1} for charting",
                       "rows": chart_rows, "truncated": False, "scope": q.scope.__dict__, "parameters": []})
    chart = {"source_id": q.evidence[-1]["citation_id"], "kind": "bar", "x": "Stage", "y": "Contributions",
             "title": f"Where cross-team work drops out of sight ({_quarter(end)})", "x_label": "Stage", "y_label": "Contributions",
             "unit": "contributions"}
    limits = ["Recognition records cover formal feedback logged at quarterly reviews; informal thanks may be unrecorded.",
              "The survey covers everyone surveyed in the team, which can include people outside your pilot roster.",
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
             "summary": f"Suggested focus: {focus['topic']}, part of Gallup's {focus['level'].lower()} level. Owners are agreed in the room." if focus else
                        "Choose the area the team believes matters most.",
             "focus": focus["topic"] if focus else None, "questions": DISCUSSION.get(focus["topic"], []) if focus else [],
             "actions": ACTIONS.get(focus["topic"], []) if focus else []},
            {"title": "Review and recalibrate",
             "summary": "Check in every few weeks: did we do what we said, and did it make a difference?",
             "items": ["Did we complete the actions we agreed?", "Did they make a difference to the focus area?",
                       "Recheck the focus area's favorability at the next survey."]},
        ],
        "note": "Echo's survey topics map approximately onto Gallup's engagement hierarchy; they are not Q12 items.",
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
    ("how is recognition trending", recognition_trend),
    ("this quarter s recognition metrics", this_quarter_recognition),
    ("recognition over eight quarters", recognition_eight_quarters),
    ("weeks exceed available project hours", over_capacity_weeks),
    ("contributions lack a recognition note", contributions_without_recognition),
    ("survey area changed most", biggest_survey_change),
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
