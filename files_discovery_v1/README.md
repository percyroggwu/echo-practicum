# Echo discovery_v1 data pack

A versioned synthetic data pack for Echo Discovery (plan v10, section 5). It loads into its own database, `data/echo_discovery_v1.db`, with `import_data.py --profile discovery_v1`. `files_update/`, `data_extensions/` and `data/echo.db` are not changed by this pack.

The pack holds 27 tables, all loaded:
- copies of the 11 legacy tables from `files_update/`, with added columns on `HR_recognition_feedback`, `OP_contributions` and `OP_capacity`;
- `HR_goals` and `HR_self_review_items`, copied unchanged from `data_extensions/` with their IDs;
- 14 new tables.

`QA_manifest.csv` lists every file (row counts for new tables are construction targets until the build records exact numbers). `QA_data_dictionary.csv` gives every column's type, key, reference, nullability and allowed values.

## Date windows

| Window | Dates | Contents |
| --- | --- | --- |
| History | 2024-10-01 to 2025-09-30 | Legacy tables only. Discovery does not read it |
| Analysis | 2025-10-01 to 2026-06-30 | What Discovery reads. The as-of date is 2026-06-30 |
| Follow-up | 2026-07-01 to 2026-09-30 | Records that show whether decided actions happened |

The new tables cover only 2025-10-01 to 2026-09-30; nothing is generated for the history window. Copied legacy tables keep their full horizon. The added columns on `OP_capacity` are blank before 2025-10-01, and `OP_contributions.Team_Goal_ID` is always blank there.

## Types

`DATE` is `YYYY-MM-DD`. `TIMESTAMP` is ISO 8601 (for example `2026-06-12T18:40:00`) and is used for every `*_At` column. Enum columns list their values in `Allowed_Values`, separated by `|`. List-valued columns (`Mentioned_Employee_IDs`, `Responder_Employee_IDs`) are `;`-separated.

Teams are identified by manager ID: team display names are not unique (for example, two managers lead a Data Platforms team), so new tables carry a `*_Manager_ID` next to each team name.

## IDs

New tables use a 3-letter prefix plus a zero-padded 6-digit number, like the legacy IDs (`INT000001`, `CON000001`):

| Prefix | Table |
| --- | --- |
| TGL | `OP_team_goals` |
| GOC | `OP_goal_outcomes` |
| THR | `OP_collab_threads` |
| MSG | `OP_collab_messages` |
| BLK | `OP_dependency_blockers` |
| INC | `OP_incident_handoffs` |
| MTM | `OP_meeting_mentions` |
| REC | `HR_recognition_events` |
| AWK | `OP_activity_weekly` |
| PRF | `HR_employee_performance` |
| OOO | `HR_one_on_ones` |
| RVN | `HR_review_notes` |
| TPL | `OP_team_plans` |
| COV | `OP_source_coverage` |

New feedback rows continue the legacy `INT` numbering after the last legacy ID (`INT042542`); new contributions continue the `CON` numbering after `CON077333`.

## Work anchors

A work reference is `{type, id}` with type `contribution`, `thread`, `blocker` or `incident`. Evidence rows carry their anchors as nullable columns `Contribution_ID`, `Thread_ID`, `Blocker_ID` and `Incident_ID`:

| Table | Rule |
| --- | --- |
| `HR_recognition_events` | Exactly one anchor |
| `HR_recognition_feedback` | At least one anchor |
| `OP_meeting_mentions`, `HR_review_notes` | Optional: zero or one anchor |
| `OP_collab_messages` | `Thread_ID` is required and is the anchor |
| `HR_self_review_items` | No anchor |

## Shared with the home manager

Feedback counts as shared at date *t* only if `Shared_With_Home_Manager_At` and `Share_Recorded_At` are both on or before *t*. Both are blank when the feedback was never shared. A share is never earlier than `Interaction_At`, and `Share_Recorded_At` is never earlier than `Shared_With_Home_Manager_At`. The legacy `Shared_With_Home_Manager` flag is derived from the date (Yes when the date is filled) and is never read by Discovery or follow-up; the importer rejects a flag that disagrees with the date.

`Record_Coverage` on each feedback row is `complete` or `partial`. `OP_source_coverage` declares `complete` or `partial` per source table, home team and quarter.

## No verdicts in the data

No column states an expected result. `Data_Origin` has one value per table and never marks planted rows. Expected answers live only in `files_discovery_v1_private/QA_discovery_v1_answer_key.csv`, which is never loaded into any database or put in any prompt, and is not listed in this pack's manifest.
