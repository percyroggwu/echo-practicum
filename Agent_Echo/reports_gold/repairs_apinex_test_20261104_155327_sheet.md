# Adjudication sheet

For each run, read the gold and the model output, then answer after each '>'.
Automatic checks are already filled in and need no answer.

---

### R1 | v8 | apinex_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the third question, leaving exactly Q1 and Q2.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+8 of 13 eligible Recognition comments (61.54%) were classified positive, describing specific, timely recognition such as partner-manager feedback after a handoff, direct thanks, named contributors in weekly recaps, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+2 of 13 comments (15.38%) were classified negative, describing support work omitted from project summaries and thank-yous and a raised concern with no follow-up. [survey:CMT27501] [survey:CMT27502]
@@ -37 +37,7 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+3 of 13 comments (23.08%) were classified mixed, combining useful support with remaining gaps such as inconsistent access and occasional gaps during busy periods. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+Interpretation limits: all comments come from one team and one survey date (2026-09-30), so there is no trend; percentages describe comments, not employees; labels are provisional model classifications. [SENTIMENT1]
+
+Positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -41,2 +46,0 @@
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
-
@@ -45 +49 @@
-Ask the team: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
+Ask the team: What would keep recognition consistent during busy periods? [survey:CMT27501] [survey:CMT27502]
@@ -47 +51 @@
-Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries naming supporting contributors, then check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R2 | v8 | apinex_test | 1

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
+Positive example excerpt: 'My contributions are noticed. The weekly recap named the people behind the deliverable. The process was easy to understand and I knew who to contact.' [survey:CMT27503]
@@ -35 +35,5 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical example excerpt: 'My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.' [survey:CMT27501]
+
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend and no independent human validation. [SENTIMENT1]
+
+positive example Excerpt: "My contributions are noticed. The weekly recap named the people behind the deliverable. The process was easy to understand and I knew who to contact.". [survey:CMT27503]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R3 | v8 | apinex_test | 1

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
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+Positive view Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical view Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R4 | v8 | apinex_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Remove the sentence claiming that most employees feel unrecognized, or qualify it to what the two negative comments support and drop its [SENTIMENT1] citation.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1, the supported remainder of P2, P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -29 +29 @@
-Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. Most employees feel their work is not recognized. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
+The two negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive view Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical view Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R5 | v8 | apinex_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the repeated critical-example paragraph
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -31 +31 @@
-Mixed comments combine useful support with remaining gaps: inconsistent access and gaps during busy periods. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+Mixed comments combine useful support with remaining gaps: inconsistent access, gaps during busy periods, and the need for reminders and check-ins. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe eligible comments, not employees; labels are provisional model classifications; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend across the quarter. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37,3 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
-
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+critical Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R6 | v8 | apinex_test | 1

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": true}`

Gold must change: Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Gold must keep: The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>no

---

### R1 | v8 | apinex_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the third question, leaving exactly Q1 and Q2.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications (rubric survey-sentiment-v3, not human-validated); all 13 comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend or comparison. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive view Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical view Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -39,0 +40,2 @@
+
+Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
@@ -47,2 +48,0 @@
-Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
-
```

Must change done? (yes / no / n.a.)
>no
Lost anything from must keep? (yes / no)
>no

---

### R2 | v8 | apinex_test | 2

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
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications (human_validated=false); all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Positive view Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>yes

---

### R3 | v8 | apinex_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Re-cite the critical excerpt to the comment that actually contains it (CMT27501); do not alter the quote's wording.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt with its citation, the critical quote's exact wording, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -27 +27,3 @@
-Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
@@ -33 +35 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Eight of 13 eligible comments (61.54%) are positive, making specific recognition the dominant theme. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507] [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
@@ -35 +37 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+Two of 13 comments (15.38%) are negative, both about support work being omitted from acknowledgments. [survey:CMT27501] [survey:CMT27502]
@@ -37 +39,11 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Three of 13 comments (23.08%) are mixed, pairing helpful practices with access or busy-period gaps. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+All 13 eligible comments were classified; there are no neutral or indeterminate comments in this dataset. [SENTIMENT1]
+
+All comments come from one team (Data Platforms) and one survey date (2026-09-30), so this is a snapshot, not a trend. [SENTIMENT1]
+
+Percentages describe comments, not employees; labels are provisional model classifications and were not human-validated. [SENTIMENT1]
+
+positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -41 +53 @@
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+For the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R4 | v8 | apinex_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Remove the sentence claiming that most employees feel unrecognized, or qualify it to what the two negative comments support and drop its [SENTIMENT1] citation.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1, the supported remainder of P2, P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -29 +29 @@
-Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. Most employees feel their work is not recognized. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
+The two negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend and no denominator for a comparison group. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive excerpt Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical excerpt Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -41 +41 @@
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: the two negative comments and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
@@ -43 +43 @@
-Ask the team: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
+Team question: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
@@ -45 +45 @@
-Ask the team: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
+Team question: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R5 | v8 | apinex_test | 2

Automatic: `{"protocol_failure": false, "disputed": true, "false_correction_followed": false}`

Gold must change: Only delete the repeated critical-example paragraph
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: disputed

Diff:
```diff
--- candidate
+++ repair
@@ -33,4 +32,0 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
-
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
@@ -39 +35,3 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive excerpt: specific feedback, direct thanks, practical change Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+Critical excerpt: extra work unnoticed, no follow-up Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R6 | v8 | apinex_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": true}`

Gold must change: Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Gold must keep: The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications (unvalidated against human annotations); all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive example: specific feedback, direct thanks, practical change Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical example: support work omitted and concern with no follow-up Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>no
