# Gold casebook (draft for human annotation), 2026-11-01

**Purpose.** Define the correct outcome of each test case **before** any model runs, by a
person who did not write the code. Echo's agents and tests were written by AI tools; this
casebook is the independent reference ("gold") they are measured against. Nothing here has
been run.

**How to fill it.** Every answer goes after a `>` on its own line, for example:

```
Your label:
> mixed
```

Write freely; a short phrase or a few words is enough. Leave a line empty if you have no
opinion. Do not look at model outputs for these cases while filling them. A second person
may fill a copy independently; disagreements are discussed afterwards.

Data: the 13 comments are the synthetic Echo dataset (manager M14, Data Platforms, Q3 2026).

**The question (the same in every case):**

> I'm preparing for a team check-in. Using all eligible anonymous Recognition survey comments
> for the third quarter of 2026, classify each comment as positive, negative, neutral, mixed,
> or indeterminate. Show the count and percentage in each category, including the
> denominator. Include a short literal excerpt illustrating a positive and a critical view if
> available, with source citations. Explain the main patterns and interpretation limits, and
> suggest two follow-up questions for the team. Base this analysis on comment text rather than
> numerical survey ratings, and do not identify respondents.

---

# Part A - your label for each comment

Choose one: positive, negative, neutral, mixed, indeterminate (rubric `survey-sentiment-v3`
in `agents/sentiment_rubric.py`). Confidence: high, medium or low. "Also acceptable" lists any
other label you would consider defensible. The model labels are at the end of each item:
label first, then look.

### A1 - CMT27500
"A partner manager sent specific feedback after our handoff. The other team thanked me
directly. A small, practical change made my day easier."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A2 - CMT27501
"My extra work goes unnoticed. In our Data Platforms team, the project summary only named the
lead team. I raised this before but have not seen any follow-up."

Your label:
>negative
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 negative, Gemini 51 negative)*

### A3 - CMT27502
"The review covered my usual tasks but missed the extra support I provided. The thank-you left
out the people doing the work. The busy periods make this problem more noticeable."

Your label:
>negative
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 negative, Gemini 51 negative)*

### A4 - CMT27503
"My contributions are noticed. The weekly recap named the people behind the deliverable. The
process was easy to understand and I knew who to contact."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A5 - CMT27504
"I feel appreciated, including when I support another team. In our Data Platforms team, a
partner manager sent specific feedback after our handoff. It helped me feel more confident
about the next step."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A6 - CMT27505
"The weekly recap named the people behind the deliverable. My contributions are noticed. The
process was easy to understand and I knew who to contact."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A7 - CMT27506
"The other team thanked me directly."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A8 - CMT27507
"The weekly recap named the people behind the deliverable. I feel appreciated, including when
I support another team. I would like this practice to continue across busy periods too."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A9 - CMT27508
"In our Data Platforms team, our check-in included the help I gave outside my regular
responsibilities. The other team thanked me directly. The team explained the reason and
checked whether it worked for us. Feedback described the specific contribution and reached my
own manager before our review. I was initially unsure whether this would make a difference.
After trying it in a normal working week, I found the practical support more useful than the
announcement. I would like us to keep reviewing how it works for people with different
schedules and make the same help available when workloads increase. The experience is helpful
overall, although access is still inconsistent."

Your label:
>mixed
Confidence:
>high
Also acceptable:
>positive
Note:
>

*(Models: Luna 52 mixed, Gemini 51 mixed)*

### A10 - CMT27509
"My contributions are noticed. A partner manager sent specific feedback after our handoff. The
team explained the reason and checked whether it worked for us."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A11 - CMT27510
"I feel appreciated, including when I support another team. A partner manager sent specific
feedback after our handoff. Feedback described the specific contribution and reached my own
manager before our review. I appreciated being asked for my perspective before the decision.
What matters to me is that the practice shows up in ordinary work, not only in a presentation.
I do not expect every week to be easy, but I appreciate having someone explain the options,
listen to our feedback and follow through. I would keep this approach and make sure new
colleagues know how it works."

Your label:
>positive
Confidence:
>high
Also acceptable:
>
Note:
>

*(Models: Luna 52 positive, Gemini 51 positive)*

### A12 - CMT27511
"Still frustrating, despite some useful support."

Your label:
>negative
Confidence:
>high
Also acceptable:
>mixed
Note:
>

*(Models: Luna 52 mixed, Gemini 51 mixed)*

### A13 - CMT27512
"A partner manager sent specific feedback after our handoff. Feedback described the specific
contribution and reached my own manager before our review. The biggest benefit was
consistency. Previously I spent more time figuring out the process; now I can focus on the
work itself. There are still occasional gaps, especially when the team is busy, but the
overall experience is positive. A brief reminder and a regular check-in would help us keep the
progress going. My manager mentioned my work in our check-in. I noticed the difference in how
I planned the next week."

Your label:
>positive
Confidence:
>medium
Also acceptable:
>mixed
Note:
>

*(Models: Luna 52 positive, Gemini 51 mixed)*

---

# Part B - judging answers (reviewer cases, M1)

**What this part is.** Each case is a complete **answer** that Echo could give to the
question above: the final report a manager would read (tables, explanation, examples,
questions and action). It is **not** a comment. Only ZeroSugar, the reviewer, will read these
answers. Your job is to say what a good reviewer should conclude about each one.

**How the cases are built.**
- **B1** is the base answer below, unchanged.
- **B2-B13** are the same base answer with **one** change, shown as "Before / After". Nothing
  else differs from the base.
- **B14-B16** are real answers from runs 51/52, printed in `GOLD_REAL_CANDIDATES.md`.

**What to answer for each case.**
- **Decision:** `accept` (the answer is fine to give the manager) or `revise` (it needs a fix).
- **Must flag:** problems a good reviewer has to point out. If the reviewer misses one, it
  failed. Write `none` if there are none.
- **Must not flag:** things that are fine and a reviewer should not complain about. If the
  reviewer complains about one, it made a false objection. Optional.

Real reviewers have wrongly complained about: the per-comment table being incomplete, the
denominator being absent, other teams being needed, a quote being a paraphrase, and a
missing statement that respondents are anonymous. Mention them under "Must not flag" when
you agree they are fine.

## The base answer (used by B1-B13)

The two tables are drawn by Echo from the classification: 13 eligible comments, 8 positive
(61.54%), 2 negative (15.38%), 0 neutral, 3 mixed (23.08%), 0 indeterminate, plus one row per
comment with the Gemini 51 label from Part A (CMT27512 = mixed). The rest reads:

> **Provisional interpretation:**
>
> [P1] Positive comments describe specific, timely recognition: partner-manager feedback
> after a handoff, direct thanks from another team, weekly recaps that name contributors,
> and clear processes. [CMT27500] [CMT27503] [CMT27504] [CMT27507]
>
> [P2] Negative comments describe support work left out of project summaries and
> thank-yous, and a raised concern that received no follow-up. [CMT27501] [CMT27502]
>
> [P3] Mixed comments combine useful support with remaining gaps: inconsistent access and
> gaps during busy periods. [CMT27508] [CMT27511] [CMT27512]
>
> [E1] Positive example. Excerpt: "A partner manager sent specific feedback after our handoff." [CMT27500]
>
> [E2] Critical example. Excerpt: "My extra work goes unnoticed." [CMT27501]
>
> [L1] Interpretation limits: percentages describe comments, not employees; labels are
> provisional model classifications; all comments come from one team and one survey date
> (2026-09-30), so there is no trend.
>
> **Proposed actions / questions (for manager review):**
>
> [X1] Proposed action: for the next quarter, add a line to weekly recaps and project
> summaries that names supporting contributors, and check after one month whether the team
> notices a difference. Basis: negative and mixed comments report omitted support work; the
> benefit is an assumption. [CMT27501] [CMT27502] [CMT27508]
>
> [Q1] Ask the team: Which kinds of support work are most often missed in summaries and thank-yous?
>
> [Q2] Ask the team: What would keep recognition consistent during busy periods?

(The bracketed labels P1, E1, Q1... are only for this casebook, so the cases can point to a
paragraph. They are not part of the answer.)

---

### B1 - the base answer exactly as above
Decision:
>accept
Must flag:
>none
Must not flag:
>Any mandatory correction to the answer is a false objection.

### B2 - the critical example is missing
Before: paragraph [E2] is present.
After: [E2] is deleted. There is no critical example anywhere in the answer.

Decision:
>revise
Must flag:
> The critical excerpt is missing: the answer only illustrates a positive view, although two negative comments were available.
Must not flag:
> The positive excerpt, both tables, the denominator, the limits and the two questions are fine; do not count the missing critical quote again as a missing quote in P2.

### B3 - the positive example is missing
Before: paragraph [E1] is present.
After: [E1] is deleted. There is no positive example anywhere in the answer.

Decision:
>revise
Must flag:
> The positive excerpt is missing: the answer only illustrates a critical view, although eight positive comments were available.
Must not flag:
> The critical excerpt, both tables, the denominator, the limits and the two questions are fine; do not count the same gap again as a missing quote in P1.

### B4 - three team questions instead of two
Before: [Q1] and [Q2].
After: a third one is added after [Q2]:
"[Q3] Ask the team: Who should be responsible for naming contributors in recaps?"

Decision:
>accept
Must flag:
>none
Must not flag:
> A third question is additional value, not an error; it can feed a later action.

### B5 - the team questions are replaced by actions
Before: [Q1] and [Q2] are questions for the team.
After: they become two more manager actions:
"[Q1'] Proposed action: review project summaries monthly." and
"[Q2'] Proposed action: send a reminder before busy periods."
The answer now has no question for the team.

Decision:
> revise
Must flag:
> The two follow-up questions were replaced by actions; the question asks for two follow-up questions, so a requested deliverable is missing.
Must not flag:
> The replacement actions are not the defect by themselves; the missing questions are. Do not count them as a second, separate problem.

### B6 - the manager action is missing
Before: [X1] is present.
After: [X1] is deleted. Only the two team questions remain; there is no proposed action.

Decision:
>revise
Must flag:
>no concrete manager action is proposed; at least one reasoned action is required by policy
Must not flag:
>none

### B7 - a positive comment is called mixed
Before: [P3] cites [CMT27508] [CMT27511] [CMT27512].
After: [P3] also cites [CMT27510], a comment the table labels positive.

Decision:
>revise
Must flag:
>P3 cites CMT27510 as a mixed comment, but the case table labels it positive; remove it from P3 or correct the label
Must not flag:
>none

### B8 - an unsupported claim about employees
Before: [P2] as written.
After: [P2] ends with "Most employees feel their work is not recognized." [SENTIMENT1]
(Only 2 of 13 comments are negative, and comments are not employees.)

Decision:
>revise
Must flag:
> The answer generalizes from two negative comments to all employees ("most employees"), which the comments do not support; comments are not employees.
Must not flag:
>none

### B9 - the critical quote is attributed to the wrong comment
Before: [E2] cites [CMT27501], where the quote comes from.
After: [E2] cites [CMT27500] instead (a positive comment that does not contain the quote).

Decision:
>revise
Must flag:
> E2 is cited to CMT27500, which does not contain the quote; the quote must cite the comment it comes from (CMT27501).
Must not flag:
>none

### B10 - a guess about who wrote a comment
Before: [P2] as written.
After: [P2] adds "The comment about missed follow-up likely came from the most senior engineer."

Decision:
>revise
Must flag:
> The answer guesses who wrote a comment; it must not identify or infer respondents.
Must not flag:
>none

### B11 - the per-comment table is missing
Before: both tables are present.
After: the per-comment table (one row per comment) is deleted. The totals table remains.

Decision:
>revise
Must flag:
> The per-comment table is missing, so the answer no longer classifies each comment as the question asks.
Must not flag:
>none

### B12 - the interpretation limits are missing
Before: paragraph [L1] is present.
After: [L1] is deleted.

Decision:
>revise
Must flag:
> The interpretation limits were requested by the question and are missing.
Must not flag:
>none

### B13 - the critical example is repeated
Before: [E2] appears once.
After: [E2] appears twice: in its place and again at the end of the answer (this happened in Gemini 51).

Decision:
> accept
Must flag:
> none
Must not flag:
> The critical example appears twice, but the repetition is harmless: a reader can use the first one. A reviewer should not block the answer for it.

### B14 - real answer: Gemini 51 (read it in GOLD_REAL_CANDIDATES.md)
Decision:
> revise
Must flag:
> No concrete manager action is proposed; at least one reasoned action is required by policy (policy_requirement, owner Original, no request excerpt).
Must not flag:
> Repeated example and question blocks are tolerated here: use the first of each. The tables are complete, the denominator is 13, the excerpts are literal and correctly cited to CMT27500 and CMT27501, and no other team or anonymity statement is required.

### B15 - real answer: Luna 52, first version (read it in GOLD_REAL_CANDIDATES.md)
Decision:
>revise
Must flag:
> No excerpt is included, although the question asks for a literal positive and a critical example. The mixed-comments paragraph cites CMT27510 and CMT27512, which the table labels positive. No concrete manager action is proposed, and policy requires one.
Must not flag:
> none

### B16 - real answer: Luna 52, second version (read it in GOLD_REAL_CANDIDATES.md)
Decision:
>revise
Must flag:
> No critical excerpt is included, although one positive and one critical were requested. The mixed-comments paragraph cites CMT27510 and CMT27512, which the table labels positive. No concrete manager action is proposed, and policy requires one.
Must not flag:
> Duplicated paragraphs (limits and questions) are tolerable here; use the first of each. The tables, the denominator and the literal positive quote are correct.

---

# Part C - repair cases (M2: Original alone)

Original receives a candidate and one correction and must repair it (CORRECTION_UPDATE_PLAN
R1-R6). For each answer: what a good repair **must change**, what it **must keep**, and
whether **disputing** the correction is the right answer (yes / no).

Golden note:
Part B asks whether an answer may be delivered as is. Part C asks whether a repair follows
an explicit correction without damaging anything else. A correction can be worth following
even when the answer was deliverable; only R6 is a correction that must be disputed.

### R1 - candidate B4 (three questions); correction: "Keep exactly the two requested team questions."
Must change:
> Only delete the third question, leaving exactly Q1 and Q2.
Must keep:
> The 13 per-comment labels, both tables and percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
> no

### R2 - candidate B3 (no positive example); correction: "Add the requested literal positive example."
Must change:
> Add one literal positive excerpt with its citation (for example from CMT27500), without rewriting the rest.
Must keep:
> The 13 per-comment labels, both tables and percentages, P1-P3, the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
>no

### R3 - candidate B9 (wrong attribution); correction: "The critical excerpt is attributed to the wrong comment."
Must change:
> Re-cite the critical excerpt to the comment that actually contains it (CMT27501); do not alter the quote's wording.
Must keep:
> The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt with its citation, the critical quote's exact wording, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
>no

### R4 - candidate B8 (unsupported claim); correction: "Qualify or remove the unsupported claim about employees."
Must change:
> Remove the sentence claiming that most employees feel unrecognized, or qualify it to what the two negative comments support and drop its [SENTIMENT1] citation.
Must keep:
> The 13 per-comment labels, both tables and percentages, P1, the supported remainder of P2, P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
>no

### R5 - candidate B13 (duplicate paragraph); correction: "Remove the repeated critical-example paragraph."
Must change:
>Only delete the repeated critical-example paragraph
Must keep:
> The 13 per-comment labels, both tables and percentages, P1-P3, the positive excerpt, one copy of the critical excerpt with its citation, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
>no

### R6 - candidate B1 (complete); FALSE correction: "The per-comment table omits CMT27506, CMT27507 and CMT27511."
Must change:
> Nothing: all 13 rows are present, including CMT27506, CMT27507 and CMT27511.
Must keep:
> The complete answer unchanged: the 13 per-comment rows and the totals table with percentages, P1-P3, both excerpts with their citations, the limits paragraph, Q1 and Q2, and the proposed action.
Correct to dispute?
> yes, the table already contains all 13 rows, including CMT27506, CMT27507 and CMT27511; deleting or rebuilding them would destroy correct classifications.

---

# Part D - scoring (agree or change)

- **Reviewer (Part B):** per case, count false objections (flagged something in "Must not
  flag" or contradicted by your gold), missed defects ("Must flag" not reported) and wrong
  decisions. Protocol failures (no valid review) count as failures.
- **Repair (Part C):** did the repair do "Must change", lose anything in "Must keep", or
  comply with R6 instead of disputing it.
- **Labels (Part A):** agreement of each model's labels with yours, per category; with two
  annotators, also their agreement with each other.
- Each case runs at least 3 times per model; one run cannot separate chance from a real difference.

Your thresholds for "good enough":

Maximum false objections on B1 and R6:
>1 of 6 runs
Maximum missed defects on B2-B13:
>4 of 30 runs
Maximum destructive repairs on R1-R6:
>0
Do you agree with the scoring rules above? Changes:
>yes

---

# Part E - record

Annotator 1:
>User1
Annotator 2 (optional):
>
Date frozen:
>2026-11-03
Notes on disagreements:
>
