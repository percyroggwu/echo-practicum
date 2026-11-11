# Real candidates for gold cases B14-B16

Answers that Echo actually produced in runs 51/52, copied unchanged from the saved reports. Read one, then answer its case in GOLD_CASEBOOK_DRAFT.md (Part B). Data is the synthetic Echo dataset.

---

## B14 - Gemini 51, reviewed candidate (`d053d88c9283b536`)

```text
Source rows (provisional sentiment aggregation) [SENTIMENT1]

| Team | Survey_Date | Dimension | Eligible_Comments | positive_count | positive_percent | negative_count | negative_percent | neutral_count | neutral_percent | mixed_count | mixed_percent | indeterminate_count | indeterminate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Platforms | 2026-09-30 | Recognition | 13 | 8 | 61.54 | 2 | 15.38 | 0 | 0.0 | 3 | 23.08 | 0 | 0.0 |

Per-comment classifications (provisional model labels) [SENTIMENT1]

| Comment source | Classification |
| --- | --- |
| survey:CMT27500 | positive |
| survey:CMT27501 | negative |
| survey:CMT27502 | negative |
| survey:CMT27503 | positive |
| survey:CMT27504 | positive |
| survey:CMT27505 | positive |
| survey:CMT27506 | positive |
| survey:CMT27507 | positive |
| survey:CMT27508 | mixed |
| survey:CMT27509 | positive |
| survey:CMT27510 | positive |
| survey:CMT27511 | mixed |
| survey:CMT27512 | mixed |

Provisional interpretation:

All 13 eligible anonymous Recognition comments are from the Data Platforms team, dated 2026-09-30, within the Q3 2026 window for manager M14. Denominator = 13 eligible comments; 13 were classified (0 suppressed, 0 indeterminate). No respondents are identifiable. [SENTIMENT1]

Positive comments cluster around specific partner feedback, direct thanks, weekly recaps that name contributors, clear processes/contacts, and appreciation for cross-team support. Survey:CMT27510 additionally asks that the practice appear in ordinary work, not just presentations. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507] [survey:CMT27510]

Negative comments describe extra/understated support going unnoticed: project summaries naming only the lead, thank-yous omitting contributors, issues raised without follow-up, and the problem worsening during busy periods. [survey:CMT27501] [survey:CMT27502]

Mixed comments report helpful experiences plus caveats: inconsistent access, occasional gaps in busy periods, lingering frustration alongside useful support, and requests for reminders, regular check-ins, and continuity across busy periods. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]

Interpretation limits: percentages describe comments, not employees; labels are provisional unvalidated model classifications; all records share the same date (2026-09-30), so the split is not a quarterly time trend; short comments may understate complexity. [SENTIMENT1]

Follow-up questions: (1) How can we keep the weekly recap and partner-manager feedback consistent during the busiest weeks, including for people on different schedules? (2) Which single change would most improve follow-up on under-recognized support work? [survey:CMT27507] [survey:CMT27512]

Illustrative positive view: specific partner feedback after handoff, a direct thank-you, and a small practical change made the experience supportive. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]

Illustrative critical view: extra work went unnoticed, the project summary named only the lead, and a prior raised concern had no follow-up. Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]

Scope and completeness: all 13 eligible anonymous Recognition comments for Data Platforms (manager M14, Q3 2026) were retrieved and classified — no groups were suppressed and 0 were indeterminate. The denominator is 13 eligible comments; percentages are therefore computed against 13 and describe comments, not employees. [SENTIMENT1]

Illustrative critical view: a contributor reports that extra support went unrecognized — the project summary named only the lead and a previously raised concern received no follow-up. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]

Illustrative positive view: specific partner feedback after handoff, a direct thank-you from the other team, and one small practical change together made the experience supportive. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]

Proposed actions / questions (for manager review, not observed outcomes):

Ask the team: (1) What would make weekly recaps and partner-manager feedback consistent during the busiest weeks, including for people on different schedules? and (2) Which single change would most improve follow-up on under-recognized support work? [survey:CMT27507] [survey:CMT27512]

Ask the team whether brief weekly reminders plus a standing check-in (mentioned as helpful by contributors) are feasible for the team's busiest weeks, to reduce the access gaps and follow-through uncertainty the feedback flags. [survey:CMT27508] [survey:CMT27512]

Results describe the supplied records within the authorized scope. Sentiment labels are provisional and human validation is pending; counts describe comments, not employees. [SENTIMENT1] [survey:CMT27500] [survey:CMT27501] [survey:CMT27502] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507] [survey:CMT27508] [survey:CMT27510] [survey:CMT27511] [survey:CMT27512]
```

---

## B15 - Luna 52, first candidate (`4c74944788596bbb`)

```text
Source rows (provisional sentiment aggregation) [SENTIMENT1]

| Team | Survey_Date | Dimension | Eligible_Comments | positive_count | positive_percent | negative_count | negative_percent | neutral_count | neutral_percent | mixed_count | mixed_percent | indeterminate_count | indeterminate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Platforms | 2026-09-30 | Recognition | 13 | 9 | 69.23 | 2 | 15.38 | 0 | 0.0 | 2 | 15.38 | 0 | 0.0 |

Per-comment classifications (provisional model labels) [SENTIMENT1]

| Comment source | Classification |
| --- | --- |
| survey:CMT27500 | positive |
| survey:CMT27501 | negative |
| survey:CMT27502 | negative |
| survey:CMT27503 | positive |
| survey:CMT27504 | positive |
| survey:CMT27505 | positive |
| survey:CMT27506 | positive |
| survey:CMT27507 | positive |
| survey:CMT27508 | mixed |
| survey:CMT27509 | positive |
| survey:CMT27510 | positive |
| survey:CMT27511 | mixed |
| survey:CMT27512 | positive |

Provisional interpretation:

Positive responses share a pattern of specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, out-of-role support being acknowledged, and a clear process that tells people who to contact. CMT27500, CMT27504, CMT27505 and CMT27509 are all labelled positive on this basis. [survey:CMT27500] [survey:CMT27504] [survey:CMT27505] [survey:CMT27509]

The negative and mixed responses converge on the same underlying gap: extra or support work is omitted from project summaries and thank-yous. CMT27501 and CMT27502 are negative because the omission went unacknowledged with no follow-up, while CMT27508 is mixed because it combines a positive outcome (specific feedback reaching the manager before review) with a complaint that access is still inconsistent. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]

The mixed comments are the most detailed and explicitly recommend concrete improvements rather than just reporting a problem: a reminder or regular check-in cadence, continued review of the practice across schedules and busy periods, and onboarding new colleagues so they can see how it works. [survey:CMT27508] [survey:CMT27510] [survey:CMT27512]

Limitations: the five labels are provisional model classifications from the survey-sentiment-v3 rubric, not human-validated measures and not derived from numerical survey ratings. Percentages are shares of the 13 eligible comments, not shares of employees. The data covers one team (Data Platforms) and one survey date (2026-09-30, the only date in the Q3 2026 window), so findings do not generalize beyond this population. [SENTIMENT1]

Proposed actions / questions (for manager review, not observed outcomes):

Follow-up question 1: How can partner-team thank-yous and project summaries reliably name supporting contributors, not just leads, especially during busy periods? [survey:CMT27501] [survey:CMT27502]

Follow-up question 2: What reminder or check-in cadence would keep consistent recognition in place when workloads increase, so new colleagues can see how it works? [survey:CMT27508] [survey:CMT27512]

Results describe the supplied records within the authorized scope. Sentiment labels are provisional and human validation is pending; counts describe comments, not employees. [SENTIMENT1] [survey:CMT27500] [survey:CMT27501] [survey:CMT27502] [survey:CMT27504] [survey:CMT27505] [survey:CMT27508] [survey:CMT27509] [survey:CMT27510] [survey:CMT27512]
```

---

## B16 - Luna 52, second candidate (`a14a1a0b6c26f9b0`)

```text
Source rows (provisional sentiment aggregation) [SENTIMENT1]

| Team | Survey_Date | Dimension | Eligible_Comments | positive_count | positive_percent | negative_count | negative_percent | neutral_count | neutral_percent | mixed_count | mixed_percent | indeterminate_count | indeterminate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Platforms | 2026-09-30 | Recognition | 13 | 9 | 69.23 | 2 | 15.38 | 0 | 0.0 | 2 | 15.38 | 0 | 0.0 |

Per-comment classifications (provisional model labels) [SENTIMENT1]

| Comment source | Classification |
| --- | --- |
| survey:CMT27500 | positive |
| survey:CMT27501 | negative |
| survey:CMT27502 | negative |
| survey:CMT27503 | positive |
| survey:CMT27504 | positive |
| survey:CMT27505 | positive |
| survey:CMT27506 | positive |
| survey:CMT27507 | positive |
| survey:CMT27508 | mixed |
| survey:CMT27509 | positive |
| survey:CMT27510 | positive |
| survey:CMT27511 | mixed |
| survey:CMT27512 | positive |

Provisional interpretation:

Positive responses share a pattern of specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, out-of-role support being acknowledged, and a clear process that tells people who to contact. CMT27500, CMT27504, CMT27505 and CMT27509 are all labelled positive on this basis. [survey:CMT27500] [survey:CMT27504] [survey:CMT27505] [survey:CMT27509]

The negative and mixed responses converge on the same underlying gap: extra or support work is omitted from project summaries and thank-yous. CMT27501 and CMT27502 are negative because the omission went unacknowledged with no follow-up, while CMT27508 is mixed because it combines a positive outcome (specific feedback reaching the manager before review) with a complaint that access is still inconsistent. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]

The mixed comments are the most detailed and explicitly recommend concrete improvements rather than just reporting a problem: a reminder or regular check-in cadence, continued review of the practice across schedules and busy periods, and onboarding new colleagues so they can see how it works. [survey:CMT27508] [survey:CMT27510] [survey:CMT27512]

Limitations: the five labels are provisional model classifications from the survey-sentiment-v3 rubric, not human-validated measures and not derived from numerical survey ratings. Percentages are shares of the 13 eligible comments, not shares of employees. The data covers one team (Data Platforms) and one survey date (2026-09-30, the only date in the Q3 2026 window), so findings do not generalize beyond this population. [SENTIMENT1]

Positive responses share a pattern of specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, out-of-role support being acknowledged, and a clear process that tells people who to contact. CMT27500, CMT27504, CMT27505 and CMT27509 are all labelled positive on this basis. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500] [survey:CMT27504] [survey:CMT27505] [survey:CMT27509]

Limitations: the five labels are provisional model classifications from the survey-sentiment-v3 rubric, not human-validated measures and not derived from numerical survey ratings. Percentages are shares of the 13 eligible comments, not shares of employees. The data covers one team (Data Platforms) and one survey date (2026-09-30, the only date in the Q3 2026 window), so findings do not generalize beyond this population. [SENTIMENT1] [survey:CMT27508] [survey:CMT27510] [survey:CMT27512]

Proposed actions / questions (for manager review, not observed outcomes):

Follow-up question 1: How can partner-team thank-yous and project summaries reliably name supporting contributors, not just leads, especially during busy periods? [survey:CMT27501] [survey:CMT27502]

Follow-up question 2: What reminder or check-in cadence would keep consistent recognition in place when workloads increase, so new colleagues can see how it works? [survey:CMT27508] [survey:CMT27512]

Ask the team how partner-team thank-yous and project summaries can reliably name supporting contributors, not just leads, especially during busy periods. [survey:CMT27501] [survey:CMT27502]

Ask what reminder or check-in cadence would keep consistent recognition in place when workloads increase, so new colleagues can see how it works. [survey:CMT27508] [survey:CMT27512]

Results describe the supplied records within the authorized scope. Sentiment labels are provisional and human validation is pending; counts describe comments, not employees. [SENTIMENT1] [survey:CMT27500] [survey:CMT27501] [survey:CMT27502] [survey:CMT27504] [survey:CMT27505] [survey:CMT27508] [survey:CMT27509] [survey:CMT27510] [survey:CMT27512]
```
