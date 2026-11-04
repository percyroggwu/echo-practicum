# Adjudication sheet

For each run, read the gold and the model output, then answer after each '>'.
Automatic checks are already filled in and need no answer.

---

### R1 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the third question, leaving exactly Q1 and Q2.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -38,0 +39,2 @@
+Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501] [survey:CMT27502]
+
@@ -45,3 +47 @@
-Ask the team: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
-
-Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work and gaps during busy periods; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508] [survey:CMT27512]
```

Must change done? (yes / no / n.a.)
>no
Lost anything from must keep? (yes / no)
>yes

---

### R1 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the third question, leaving exactly Q1 and Q2.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -37 +37,5 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all 13 eligible comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+
+Positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -44,0 +49,2 @@
+Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
+
@@ -47,2 +52,0 @@
-Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
-
```

Must change done? (yes / no / n.a.)
>no
Lost anything from must keep? (yes / no)
>no

---

### R2 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Add one literal positive excerpt with its citation (for example from CMT27500), without rewriting the rest.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -36,0 +37,4 @@
+Positive view: a positive comment describes specific, timely recognition — partner-manager feedback after a handoff, direct thanks from another team, and a small practical change that improved the day. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Critical view: the strongest negative comment reports that extra support work was left out of recognition, only the lead was named in the project summary, and a prior raise of the issue received no follow-up. Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
+
@@ -44,0 +49,2 @@
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502]
+
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R2 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Add one literal positive excerpt with its citation (for example from CMT27500), without rewriting the rest.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35,5 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+13 eligible comments were classified, so all five denominators are 13 and percentages describe comments. [SENTIMENT1]
+
+Positive example: specific feedback and thanks Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+
+Critical example: extra work goes unnoticed Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
@@ -44,0 +49,2 @@
+For the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R3 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Re-cite the critical excerpt to the comment that actually contains it (CMT27501); do not alter the quote's wording.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt with its citation, the critical quote's exact wording, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -37 +37,7 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+
+The critical view is that support work is left out of project summaries and thank-yous: one commenter says 'My extra work goes unnoticed,' the project summary named only the lead team, and the raised concern received no follow-up. Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501] [survey:CMT27502]
+
+Mixed comments combine useful support with remaining gaps: access remains inconsistent and gaps appear during busy periods. Excerpt: "The experience is helpful overall, although access is still inconsistent.". [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+Classification limits: labels are the survey tool's provisional model classification (human_validated=false); percentages describe eligible comments, not employees; the denominator is 13 comments from a single team on one survey date (2026-09-30), so there is no trend and no per-employee breakdown. [SENTIMENT1]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R3 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Re-cite the critical excerpt to the comment that actually contains it (CMT27501); do not alter the quote's wording.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt with its citation, the critical quote's exact wording, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -37 +37,3 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+positive Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -46,0 +49,2 @@
+For the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R4 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Remove the sentence claiming that most employees feel unrecognized, or qualify it to what the two negative comments support and drop its [SENTIMENT1] citation.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1, the supported remainder of P2, P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -38,0 +39,8 @@
+The per-comment table assigns 8 positive, 2 negative, 3 mixed, 0 neutral and 0 indeterminate comments out of 13 eligible comments; the denominator is all 13 eligible comments, which also includes the mixed and neutral labels. [SENTIMENT1]
+
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes with identified contacts. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+
+Mixed comments combine useful support with remaining gaps: inconsistent access and gaps during busy periods, plus initial uncertainty before practical usefulness was found. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+Labels are provisional model classifications with a 2026-09-30 survey date and no prior validation; the single date means there is no trend across the quarter. [SENTIMENT1]
+
@@ -46,0 +55,2 @@
+Proposed action: add a line to weekly recaps and project summaries that names supporting contributors, then check after one month whether the team notices a difference. This targets the omitted-support feedback in the comments; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
```

Must change done? (yes / no / n.a.)
>no
Lost anything from must keep? (yes / no)
>no

---

### R4 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Remove the sentence claiming that most employees feel unrecognized, or qualify it to what the two negative comments support and drop its [SENTIMENT1] citation.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1, the supported remainder of P2, P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -29,2 +28,0 @@
-Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. Most employees feel their work is not recognized. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
-
@@ -37,0 +36,12 @@
+
+Eight of 13 eligible comments (61.54%) are classified positive; they describe specific, timely recognition such as partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+
+Two of 13 comments (15.38%) are classified negative; the concern is that extra/support work is omitted from project summaries and thank-yous, and a raised concern received no follow-up. [survey:CMT27501] [survey:CMT27502]
+
+Three of 13 comments (23.08%) are classified mixed; they acknowledge useful support while noting remaining gaps such as inconsistent access and gaps during busy periods. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications (not human-validated); all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508] [survey:CMT27512]
+
+Positive example (CMT27500) Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Critical example (CMT27501) Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -46,0 +57,6 @@
+For the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
+Team question: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
+
+Team question: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
+
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R5 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the repeated critical-example paragraph
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -39 +39,9 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+All 13 eligible comments from Data Platforms for Q3 2026 (Survey_Date 2026-09-30, dimension Recognition) were classified; percentages are computed against the 13-comment denominator, not employees. [SENTIMENT1]
+
+Positive comments cite specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes with identified contacts. Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Negative comments report support work left out of project summaries and thank-yous, with a raised concern receiving no follow-up. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+
+Mixed comments pair useful practices (specific feedback reaching the contributor's own manager, consistency gains) with remaining gaps such as inconsistent access and lapses during busy periods. [survey:CMT27508] [survey:CMT27512]
+
+Interpretation limits: labels are provisional model classifications, not validated against human annotations; comments come from a single team and a single date, so there is no trend. [SENTIMENT1]
@@ -42,2 +49,0 @@
-
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
@@ -48,0 +55,2 @@
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries naming supporting contributors, and check after one month whether the team notices a difference; basis is that negative and mixed comments report omitted support work. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
```

Must change done? (yes / no / n.a.)
>no
Lost anything from must keep? (yes / no)
>no

---

### R5 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the repeated critical-example paragraph
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -35,2 +34,0 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
@@ -39 +37,5 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+
+positive Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R6 | v7 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": true}`

Gold must change: Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Gold must keep: The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -37 +37,5 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+The three previously omitted comments are all classified in the source: CMT27506 (positive) is a direct thank-you from another team; CMT27507 (positive) names contributors in the weekly recap and asks that the practice continue through busy periods; CMT27511 (mixed) reports frustration alongside some useful support. [SENTIMENT1]
+
+Percentages are computed against the eligible-comment denominator of 13 (the table's Eligible_Comments column); they describe comments, not employees. The five-category labels are provisional model classifications and have not been human-validated. [SENTIMENT1]
+
+The main pattern is that support work across teams is inconsistently recognized: positive comments cite partner-manager feedback after a handoff, direct thanks, and recaps that name contributors, while negative and mixed comments repeatedly report that extra support is omitted from summaries and thank-yous and that gaps worsen during busy periods. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
@@ -46,0 +51,2 @@
+Proposed follow-up action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work, and mixed comments ask for consistency during busy periods; the benefit is an assumption rather than an observed result. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508] [survey:CMT27512]
+
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>yes

---

### R6 | v8 | apinex_gemini_test | 1

Automatic: `{"protocol_failure": false, "disputed": true, "false_correction_followed": false}`

Gold must change: Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Gold must keep: The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.
Model response: disputed

Diff:
```diff
--- candidate
+++ repair
@@ -38,0 +39,2 @@
+Three comment categories are represented: 8 positive (61.54%), 2 negative (15.38%), and 3 mixed (23.08%), with 0 neutral and 0 indeterminate. [SENTIMENT1]
+
@@ -46,0 +49,2 @@
+For the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>no
