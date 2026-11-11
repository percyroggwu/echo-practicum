# Goals and year-end self-reviews (synthetic extension)

Two HR tables that add what employees plan at the start of the year and what they report at the end. Comparing the two shows work that was in no goal; checking that work against the existing records shows what went unnoticed. The design and its reasoning are in the team doc "Echo: goals and year-end self-review data".

This folder sits beside Percy's `files_update` data and `import_data.py` and changes neither. It reads the built database, writes the CSVs here, and adds two tables to `Agent_Echo/data/echo.db`. The eleven existing tables are not touched, and Echo's agents don't read the new tables until someone adds them to their scope.

## Rebuild

```bash
Agent_Echo/.venv/bin/python data_extensions/generate_goal_reviews.py --load
```

The output is seeded, so every run produces the same rows. Rebuilding the main database with `import_data.py --replace` drops these two tables; run the command above again afterwards.

## Files

| File | Rows | Loaded into echo.db | What one row is |
| --- | --- | --- | --- |
| `HR_goals.csv` | 12,670 | Yes | One goal agreed in January, review years 2025 and 2026 (1,901 employees each year) |
| `HR_self_review_items.csv` | 12,129 | Yes | One thing an employee reported in their December 2025 self-review |
| `QA_discovery_answer_key.csv` | 12,129 | **No** | What each self-review item really is, for testing; the judge must never see it |

2026 has goals only: its self-reviews would fall after the data ends on 30 September 2026.

## How the rows are made

- **Goals:** 2 or 3 delivery goals from the objectives of projects the employee's team sponsored that year, plus one development goal. About half the delivery goals carry a number.
- **Self-review items on goals:** one per goal, with an outcome of Met, Partly met or Missed.
- **Items from records:** the employee's own cross-team contributions in 2025 from `OP_contributions`, rewritten in the first person.
- **Items with no record:** about 1 employee in 5 reports one piece of cross-team work that no record captures.
- **Unplanned work in the own team:** some employees report covering for a colleague or onboarding someone.
- **Writing styles:** detailed, standard, brief (vague, fewer items, no numbers) and overstated (claims goal links that aren't there).
- **The planted side project:** six employees, two each in Data Platforms, Customer Renewals and Customer Care, describe the same unassigned renewal-risk early-warning tool. It is in no goal and no record. One of them, Jonah Meyer (E0001), is on M14's team.

## Assumptions to agree as a team

| Assumption | Value |
| --- | --- |
| Goal outcomes | Met 55%, Partly met 30%, Missed 15% |
| Writing styles | Detailed 30%, standard 40%, brief 20%, overstated 10% |
| Employees reporting work with no record | 20% |
| Planted project | Renewal-risk early-warning tool, 6 employees in 3 teams |

The answer key's `Kind` column is one of `goal_report`, `recorded_cross_team` (with its `Source_Contribution_ID`), `unrecorded_cross_team`, `unplanned_own_team` or `planted`.
