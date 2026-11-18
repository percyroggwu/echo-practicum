"""Versioned, read-only metrics over the existing physically scoped SQL copy."""

from .execution_log import record

METRICS = ("cross_team_contributions", "survey_trend")


class MetricCatalog:
    def __init__(self, reader, actor="Cherry"):
        self.reader = reader
        self.actor = actor

    def run(self, metric, dimension=None):
        if metric not in METRICS:
            raise ValueError("Unknown metric. Use cross_team_contributions or survey_trend.")
        version = 2
        if metric == "cross_team_contributions":
            if isinstance(dimension, str) and dimension.strip().casefold() in {"none", "null", "n/a", ""}:
                dimension = None
            if dimension is not None:
                raise ValueError("Cross-team contribution metrics require dimension=null.")
            sql = """WITH eligible AS (
                SELECT Contribution_ID, MIN(Employee_ID) AS Employee_ID, {hours} AS Hours,
                  MAX(CASE WHEN Home_Team <> Beneficiary_Team THEN 1 ELSE 0 END) AS cross_team
                FROM contributions GROUP BY Contribution_ID
            ), flags AS (
                SELECT c.Contribution_ID, c.Employee_ID, c.Hours, c.cross_team,
                  EXISTS(SELECT 1 FROM recognition_feedback f WHERE f.Contribution_ID=c.Contribution_ID
                    AND f.Interaction_Type='Manager recognition') AS manager_note,
                  EXISTS(SELECT 1 FROM recognition_feedback f WHERE f.Contribution_ID=c.Contribution_ID
                    AND f.Interaction_Type='Partner feedback') AS partner_note,
                  EXISTS(SELECT 1 FROM recognition_feedback f WHERE f.Contribution_ID=c.Contribution_ID
                    AND f.Interaction_Type='Partner feedback' AND f.Shared_With_Home_Manager='Yes') AS shared_note,
                  EXISTS(SELECT 1 FROM recognition_feedback f WHERE f.Contribution_ID=c.Contribution_ID) AS any_note
                FROM eligible c
            ), cross_flags AS (
                SELECT *, CASE WHEN manager_note=0 AND (partner_note=0 OR shared_note=0) THEN 1 ELSE 0 END AS unnoticed
                FROM flags WHERE cross_team=1
            ), person_stats AS (
                SELECT COUNT(*) AS people, ROUND(100.0*SUM(CASE WHEN rank_no<=3 THEN n END)/SUM(n),1) AS top3 FROM (
                    SELECT n, row_number() OVER (ORDER BY n DESC) AS rank_no FROM (
                        SELECT COUNT(*) AS n FROM cross_flags WHERE unnoticed=1 GROUP BY Employee_ID))
            ) SELECT COUNT(*) AS Total_Contributions,
                COALESCE(SUM(manager_note),0) AS With_Manager_Recognition,
                COALESCE(SUM(1-manager_note),0) AS Without_Manager_Recognition,
                COALESCE(SUM(partner_note),0) AS With_Partner_Feedback,
                COALESCE(SUM(1-any_note),0) AS Without_Any_Feedback,
                COALESCE(SUM(shared_note),0) AS Praise_Reached_Manager,
                COALESCE(SUM(CASE WHEN manager_note=0 AND partner_note=0 THEN 1 ELSE 0 END),0) AS No_Praise,
                COALESCE(SUM(CASE WHEN manager_note=0 AND partner_note=1 AND shared_note=0 THEN 1 ELSE 0 END),0) AS Praise_Not_Passed_On,
                COALESCE(SUM(CASE WHEN manager_note=0 AND shared_note=1 THEN 1 ELSE 0 END),0) AS Praised_Not_Recognized,
                COALESCE(SUM(unnoticed),0) AS Unnoticed_Contributions,
                {total_hours} AS Total_Hours,
                {unnoticed_hours} AS Unnoticed_Hours,
                (SELECT people FROM person_stats) AS Unnoticed_People,
                (SELECT top3 FROM person_stats) AS Top3_Unnoticed_Share_Percent,
                (SELECT COUNT(*) FROM flags WHERE cross_team=0) AS Own_Team_Contributions,
                (SELECT ROUND(100.0*SUM(manager_note)/COUNT(*),1) FROM flags WHERE cross_team=0) AS Own_Team_Recognized_Percent
                FROM cross_flags"""
            # Legacy databases have no Effort_Hours: report hours as NULL, never 0.
            if "Effort_Hours" in self.reader.schema.get("contributions", {}):
                sql = sql.format(hours="MAX(Effort_Hours)", total_hours="ROUND(COALESCE(SUM(Hours),0),1)",
                    unnoticed_hours="ROUND(COALESCE(SUM(CASE WHEN unnoticed=1 THEN Hours END),0),1)")
            else:
                sql = sql.format(hours="NULL", total_hours="NULL", unnoticed_hours="NULL")
            parameters = []
            definition = ("Distinct cross-team Contribution_ID in the authorized roster and contribution period. "
                "Manager recognition, partner feedback and absence of any feedback are separate counts. "
                "Praise_Reached_Manager: partner feedback shared with the home manager. Unnoticed_Contributions: "
                "no manager recognition and either no partner feedback or none shared with the home manager "
                "(No_Praise + Praise_Not_Passed_On); Praised_Not_Recognized has shared praise but no manager recognition. "
                "Hours sum Effort_Hours; Unnoticed_People are distinct employees with unnoticed work; "
                "Top3_Unnoticed_Share_Percent is the share done by the three people with the most. "
                "Own_Team_* compare work for the contributor's own team (Home_Team = Beneficiary_Team). "
                "Feedback is restricted to the selected interaction period; missing notes do not prove "
                "absent recognition or unfair treatment. Recorded coverage may be incomplete.")
        else:
            if not isinstance(dimension, str) or not 1 <= len(dimension.strip()) <= 100:
                raise ValueError("survey_trend requires one exact survey dimension.")
            dimension = dimension.strip()
            sql = """SELECT Team, Survey_Date, Responses, Mean_Score, Favorable_Percent
                FROM survey_summary WHERE Dimension = ? COLLATE NOCASE ORDER BY Survey_Date, Team"""
            parameters = [dimension]
            definition = ("Recorded team/date survey aggregates for the exact dimension, preserving Responses "
                          "as denominator. Dimension matching ignores letter case and surrounding input whitespace, "
                          "without fuzzy or partial matching. Rows are not employee-level sentiment labels or causal effects.")
        result = self.reader.execute(sql, parameters)
        result.update(metric_id=metric, metric_version=version, metric_arguments={"dimension": dimension},
                      metric_definition=definition)
        record("metric_replayed" if self.actor == "ZeroSugar" else "metric_executed", agent=self.actor, metric_id=metric, metric_version=version,
               rows=len(result["rows"]), truncated=result["truncated"])
        return result
