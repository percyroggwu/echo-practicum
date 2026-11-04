# Adjudication sheet

For each run, read the gold and the model output, then answer after each '>'.
Automatic checks are already filled in and need no answer.

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
@@ -27 +27 @@
-Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications with no human validation; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive excerpt Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical excerpt Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -40,0 +41,2 @@
+Ask the team: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
+
@@ -42,2 +43,0 @@
-
-Ask the team: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
```

Must change done? (yes / no / n.a.)
>no
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
@@ -35 +35 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Positive example - specific feedback, direct thanks, practical change Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>yes

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
+Interpretation limits: percentages describe eligible comments, not employees; labels are provisional model classifications; all 13 comments come from one team and one survey date (2026-09-30), so this is a snapshot with no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+positive Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
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
@@ -29 +29 @@
-Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. Most employees feel their work is not recognized. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
+Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
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
@@ -33,4 +32,0 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
-
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
@@ -39 +35,3 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

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
@@ -26,0 +27,2 @@
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+
@@ -33 +35 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Positive example Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -35,3 +37 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical example Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>no

---

### R1 | v8 | apinex_gemini_test | 2

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
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications with human validation = false; all comments come from one team (Data Platforms) and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive view Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical view Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -47,2 +46,0 @@
-Ask the team: Who should be responsible for naming contributors in recaps? [survey:CMT27501] [survey:CMT27503]
-
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R2 | v8 | apinex_gemini_test | 2

Automatic: `{"protocol_failure": false, "disputed": true, "false_correction_followed": false}`

Gold must change: Add one literal positive excerpt with its citation (for example from CMT27500), without rewriting the rest.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: disputed

Diff:
```diff
--- candidate
+++ repair
@@ -33 +33 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35,3 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+positive excerpt Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical excerpt Excerpt: "The review covered my usual tasks but missed the extra support I provided. The thank-you left out the people doing the work. The busy periods make this problem more noticeable.". [survey:CMT27502]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>yes

---

### R3 | v8 | apinex_gemini_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Re-cite the critical excerpt to the comment that actually contains it (CMT27501); do not alter the quote's wording.
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt with its citation, the critical quote's exact wording, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -27 +27 @@
-Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
+Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps naming contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all 13 comments come from one team (Data Platforms) on one survey date (2026-09-30), so there is no trend and no baseline for comparison. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27500]
+Positive example (specific feedback, direct thanks, practical change) Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -37 +37 @@
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+Critical example (unnoticed extra work, no follow-up) Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -41 +41 @@
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+Proposed manager action: add a line to weekly recaps and project summaries that names supporting contributors, then check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
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

### R4 | v8 | apinex_gemini_test | 2

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
+Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. [SENTIMENT1] [survey:CMT27501] [survey:CMT27502]
@@ -33 +33 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications (not human-validated); all comments come from one team on a single survey date (2026-09-30), so there is no trend. [SENTIMENT1]
@@ -35 +35 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
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

### R5 | v8 | apinex_gemini_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": false}`

Gold must change: Only delete the repeated critical-example paragraph
Gold must keep: The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: no
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -27,10 +26,0 @@
-Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct thanks from another team, weekly recaps that name contributors, and clear processes. [survey:CMT27500] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507]
-
-Negative comments describe support work left out of project summaries and thank-yous, and a raised concern that received no follow-up. [survey:CMT27501] [survey:CMT27502]
-
-Mixed comments combine useful support with remaining gaps: inconsistent access and gaps during busy periods. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
-
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
-
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
@@ -39 +29,11 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
+Positive comments describe specific, timely recognition: partner-manager feedback after handoffs, direct thanks from another team, weekly recaps naming contributors, and clear processes. [SENTIMENT1]
+
+Negative comments describe support work left out of project summaries and thank-yous, plus a raised concern that received no follow-up. [survey:CMT27501] [survey:CMT27502]
+
+Mixed comments combine useful support with remaining gaps: inconsistent access, occasional gaps during busy periods, and a generally positive-but-improvable experience. [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications validated against no human annotations; all 13 comments are from one team (Data Platforms) on a single date (2026-09-30), so no trend can be inferred. [SENTIMENT1]
+
+positive example (specific feedback, direct thanks, practical change) Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
+
+critical example (work unnoticed, no follow-up) Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
@@ -43 +43 @@
-Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and check after one month whether the team notices a difference. Basis: negative and mixed comments report omitted support work; the benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
+Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names supporting contributors, and follow up after one month to check whether the team notices a difference. Basis: negative and mixed comments report omitted support work; benefit is an assumption. [survey:CMT27501] [survey:CMT27502] [survey:CMT27508]
@@ -45 +45 @@
-Ask the team: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
+Team question: Which kinds of support work are most often missed in summaries and thank-yous? [survey:CMT27501] [survey:CMT27502]
@@ -47 +47 @@
-Ask the team: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
+Team question: What would keep recognition consistent during busy periods? [survey:CMT27508] [survey:CMT27512]
@@ -49 +49 @@
-Results describe the supplied records within the authorized scope. Sentiment labels are provisional and human validation is pending; counts describe comments, not employees. [SENTIMENT1] [survey:CMT27500] [survey:CMT27501] [survey:CMT27502] [survey:CMT27503] [survey:CMT27504] [survey:CMT27507] [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
+Results describe the supplied records within the authorized scope. Sentiment labels are provisional and human validation is pending; counts describe comments, not employees. [SENTIMENT1] [survey:CMT27500] [survey:CMT27501] [survey:CMT27502] [survey:CMT27508] [survey:CMT27511] [survey:CMT27512]
```

Must change done? (yes / no / n.a.)
>yes
Lost anything from must keep? (yes / no)
>no

---

### R6 | v8 | apinex_gemini_test | 2

Automatic: `{"protocol_failure": false, "disputed": false, "false_correction_followed": true}`

Gold must change: Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Gold must keep: The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Gold dispute: yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.
Model response: fixed

Diff:
```diff
--- candidate
+++ repair
@@ -26,0 +27,2 @@
+Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+
@@ -33 +35 @@
-Positive example. Excerpt: "A partner manager sent specific feedback after our handoff.". [survey:CMT27500]
+positive Excerpt: "A partner manager sent specific feedback after our handoff. The other team thanked me directly. A small, practical change made my day easier.". [survey:CMT27500]
@@ -35,3 +37 @@
-Critical example. Excerpt: "My extra work goes unnoticed.". [survey:CMT27501]
-
-Interpretation limits: percentages describe comments, not employees; labels are provisional model classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend. [SENTIMENT1]
+critical Excerpt: "My extra work goes unnoticed. In our Data Platforms team, the project summary only named the lead team. I raised this before but have not seen any follow-up.". [survey:CMT27501]
```

Must change done? (yes / no / n.a.)
>n.a.
Lost anything from must keep? (yes / no)
>no
