"""Cross-team metric v2 on the Discovery database (M14, Q2 2026) and its replay."""
from pathlib import Path
import unittest

from agents import AccessScope
from agents.data_access import ScopedData
from agents.metrics import MetricCatalog
from agents.tools import SQLReader

DB = Path(__file__).resolve().parents[1] / "data" / "echo_discovery_v1.db"
SCOPE = AccessScope("M14", "2026-04-01", "2026-06-30")
V1 = ["Total_Contributions", "With_Manager_Recognition", "Without_Manager_Recognition",
      "With_Partner_Feedback", "Without_Any_Feedback"]


@unittest.skipUnless(DB.exists(), "discovery_v1 database has not been imported")
class CrossTeamMetricV2Tests(unittest.TestCase):
    def test_columns_values_and_replay(self):
        backend = ScopedData(DB, SCOPE)
        try:
            tables = backend.structured_tables()
        finally:
            backend.close()
        self.assertTrue({"Effort_Hours", "Team_Goal_ID"} <= set(tables["contributions"][0]))
        reader = SQLReader(tables, SCOPE)
        try:
            result = MetricCatalog(reader).run("cross_team_contributions")
            self.assertEqual(result["metric_version"], 2)
            row = result["rows"][0]
            self.assertEqual(list(row)[:5], V1)
            self.assertEqual(len(row), 16)
            expected = {"Total_Contributions": 174, "With_Manager_Recognition": 30, "With_Partner_Feedback": 60,
                        "Praise_Reached_Manager": 60, "Unnoticed_Contributions": 104, "Unnoticed_Hours": 1183.0,
                        "Unnoticed_People": 31, "Own_Team_Contributions": 27}
            for key, value in expected.items():
                self.assertEqual(row[key], value, key)
            self.assertEqual(row["No_Praise"] + row["Praise_Not_Passed_On"], row["Unnoticed_Contributions"])
            self.assertEqual(row["Without_Manager_Recognition"],
                             row["Unnoticed_Contributions"] + row["Praised_Not_Recognized"])
            self.assertEqual(round(row["Own_Team_Recognized_Percent"] * 27 / 100), 5)
            self.assertTrue(0 < row["Top3_Unnoticed_Share_Percent"] <= 100)
            self.assertGreater(row["Total_Hours"], row["Unnoticed_Hours"])
            replay = MetricCatalog(reader, actor="ZeroSugar").run("cross_team_contributions")
            self.assertEqual({k: replay[k] for k in ("rows", "sql", "metric_version", "metric_definition")},
                             {k: result[k] for k in ("rows", "sql", "metric_version", "metric_definition")})
        finally:
            reader.close()

    def test_empty_population_has_zero_counts_and_null_percentages(self):
        tables = {"contributions": (["Contribution_ID", "Employee_ID", "Home_Team", "Beneficiary_Team", "Effort_Hours"], []),
                  "recognition_feedback": (["Contribution_ID", "Interaction_Type", "Shared_With_Home_Manager"], [])}
        reader = SQLReader(tables, SCOPE)
        try:
            row = MetricCatalog(reader).run("cross_team_contributions")["rows"][0]
        finally:
            reader.close()
        self.assertEqual(row["Total_Contributions"], 0)
        self.assertEqual(row["Unnoticed_Hours"], 0)
        self.assertIsNone(row["Top3_Unnoticed_Share_Percent"])
        self.assertIsNone(row["Own_Team_Recognized_Percent"])


if __name__ == "__main__":
    unittest.main()
