"""Offline delivery checks for Original v8 and ZeroSugar v8; scripted judgments are not accuracy evidence."""

import json
import unittest

from agents.grounding import FactCatalog, render_answer, GROUNDING_VERSION
from agents.model import ModelTurn
from agents.content import excerpt_catalog
from agents.original import OriginalAgent, PLANNING_INSTRUCTIONS, INSTRUCTIONS
from agents.runtime import RunBudget, Specialist
from agents.zero_sugar import DIMENSIONS
from agents.zero_sugar import ZeroSugarAgent, SUPPORT_INSTRUCTIONS, COMPLETENESS_INSTRUCTIONS
from test_agents import DATABASE, tool_turn
from fixtures import SCOPE
from fixtures import classification_fixture

QUESTION = ("Classify every eligible Recognition comment, show counts and percentages, include one literal "
            "critical example, and propose one manager action.")


class Scripted:
    """Returns one scripted argument object per call, built from the request it receives."""

    def __init__(self, **queues):
        self.queues = {name: list(items) for name, items in queues.items()}
        self.calls = []

    def respond(self, instructions, history, tools, require_tool=False):
        name = tools[-1]["name"]
        self.calls.append({"name": name, "history": history, "tool": tools[-1], "instructions": instructions})
        context = next(json.loads(h["content"].split("\n", 1)[1]) for h in history
                       if isinstance(h.get("content"), str) and h["content"].startswith("WORKSPACE")) \
            if name == "submit_answer" else json.loads(history[0]["content"])
        value = self.queues[name].pop(0)(context, tools[-1])
        if isinstance(value, tuple):
            # Several calls in one turn, as Gemini sent in runs 86, 98 and medium 1/3.
            turns = [tool_turn(name, item, identifier=f"call-{len(self.calls)}-{i}") for i, item in enumerate(value)]
            return ModelTurn(calls=[t.calls[0] for t in turns], output_items=[t.output_items[0] for t in turns])
        return tool_turn(name, value, identifier=f"call-{len(self.calls)}")


def accept_completeness(context, tool):
    return {"decision": "accept", "score": 3, "rationale": "Every requested part is visible.", "missing": [], "suggestions": []}


def pending(tool, name):
    """Finding IDs the support tool still asks for under assertions or label_disputes."""
    return tool["parameters"]["properties"][name]["items"]["properties"]["finding_id"].get("enum", [])


def supported(context, tool, **changes):
    properties = tool["parameters"]["properties"]
    blocks = {f["finding_id"]: f for f in context["findings"]}
    assertions = [{"finding_id": key, "claim": "Main claim of " + key,
                   "kind": "proposal" if blocks[key].get("kind") == "proposal" else "factual",
                   "citation_ids": blocks[key]["citation_ids"][:1], "assessment": "supported", "problem": None}
                  for key in pending(tool, "assertions")]
    value = {"assertions": assertions, "label_disputes": [], "new_issues": [], "safety_issue_index": None,
             "clarification_question": None,
             "ratings": {d: {"score": 3, "note": "Satisfactory."} for d in DIMENSIONS}}
    if "obligations" in properties:
        value["obligations"] = {key: {"status": "satisfied", "note": "Visible now."} for key in properties["obligations"]["properties"]}
    if "proposal_types" in properties:
        ids = properties["proposal_types"]["items"]["properties"]["finding_id"].get("enum", [])
        value["proposal_types"] = [{"finding_id": key, "type": "action"} for key in ids]
    if "category_claims" in properties:
        value["category_claims"] = []
    value.update(changes)
    return value


def new_issue(tool, **values):
    """One support new_issue with exactly the fields this schema declares."""
    fields = tool["parameters"]["properties"]["new_issues"]["items"]["properties"]
    base = {"kind": "unsupported_claim", "owner": "Original", "issue": "Overstates the cause.",
            "requested_change": "State the limitation.", "request_ref": None, "finding_ids": [], "citation_ids": [],
            "missing_source_ids": [], "obligation_ref": None}
    return {k: v for k, v in {**base, **values}.items() if k in fields}


def candidate(evidence):
    catalog = FactCatalog(evidence, SCOPE.__dict__)
    payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
        {"text": "Most comments describe recognition favorably.", "citation_ids": ["SENTIMENT1"], "quote": None}],
        "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
        "Original")
    text, claims = render_answer(payload, catalog, "Original")
    return text, claims, {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}


def reviewer(model, report, docs, evidence):
    return ZeroSugarAgent(SCOPE, model, "live", budget=RunBudget(), sentiment_reports={"SENTIMENT1": report},
                            sentiment_documents=docs, document_lookup={e["citation_id"]: e for e in evidence[1:]},
                            authorized_teams=["Data Platforms"])


class ZeroSugarContractTests(unittest.TestCase):
    def setUp(self):
        self.report, self.docs, self.evidence = classification_fixture()
        self.answer, self.claims, self.grounding = candidate(self.evidence)

    def review(self, model, **kwargs):
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding, **kwargs)
        return agent, result

    @staticmethod
    def revise(context, tool, missing=True, ref_index=0):
        ref = list(context["question_excerpts"])[ref_index]
        return {"decision": "revise", "score": 2, "rationale": "A requested part is absent.", "suggestions": [],
                "missing": [{"request_ref": ref, "issue": "The action is absent.", "requested_change": "Add it."}] * missing}

    def test_a_valid_revise_survives_an_invalid_accept_in_the_same_turn(self):
        # Synthetic shape of medium Gemini 3: a valid revise plus an accept without rationale.
        fragment = {"decision": "accept", "score": 3, "missing": [], "suggestions": []}
        model = Scripted(submit_completeness_review=[lambda c, t: (self.revise(c, t), fragment)],
                         submit_support_review=[supported])
        agent, result = self.review(model)
        self.assertEqual(agent.diagnostics["completeness_review"]["decision"], "revise")
        self.assertEqual([c["name"] for c in model.calls], ["submit_completeness_review", "submit_support_review"])
        [reduced] = [n for n in agent.diagnostics["delivery_normalizations"] if n["code"] == "review_calls_reduced"]
        self.assertEqual((reduced["policy"], reduced["dropped_count"]), ("single_valid", 1))
        self.assertFalse(any(e.get("phase") == "completeness" for e in agent.diagnostics["rejected_attempts"]))

    def test_an_invalid_revise_blocks_a_valid_accept_and_names_the_conflict(self):
        def broken(context, tool):
            return {**self.revise(context, tool), "rationale": ""}
        model = Scripted(submit_completeness_review=[lambda c, t: (accept_completeness(c, t), broken(c, t)),
                                                     accept_completeness],
                         submit_support_review=[supported])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        [rejection] = [e for e in agent.diagnostics["rejected_attempts"] if e.get("phase") == "completeness"]
        self.assertEqual(rejection["validation_code"], "tool_call_count")
        feedback = json.loads(json.loads(model.calls[1]["history"][-1]["output"])["error"])
        self.assertIn("disagree (accept, revise)", feedback["errors"][0]["message"])

    def test_two_valid_calls_with_one_decision_keep_the_first_and_count_what_is_dropped(self):
        model = Scripted(submit_completeness_review=[lambda c, t: (self.revise(c, t), self.revise(c, t, ref_index=1))],
                         submit_support_review=[supported])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        agent.review(QUESTION + " Also suggest one team question.", self.answer, self.evidence,
                     claims=self.claims, grounding=self.grounding)
        self.assertEqual(len(agent.diagnostics["completeness_review"]["corrections"]), 1)
        [reduced] = [n for n in agent.diagnostics["delivery_normalizations"] if n["code"] == "review_calls_reduced"]
        self.assertEqual((reduced["policy"], reduced["dropped_unique_missing"]), ("same_decision", 1))

    def test_a_revise_without_items_cannot_outvote_one_with_an_omission(self):
        # A revise without items is normalized to accept, so keeping it would drop the real omission.
        model = Scripted(submit_completeness_review=[lambda c, t: (self.revise(c, t, False), self.revise(c, t)),
                                                     accept_completeness],
                         submit_support_review=[supported])
        agent, result = self.review(model)
        [rejection] = [e for e in agent.diagnostics["rejected_attempts"] if e.get("phase") == "completeness"]
        self.assertEqual(rejection["validation_code"], "tool_call_count")

    def test_two_different_valid_support_calls_are_rejected(self):
        def objecting(context, tool):
            value = supported(context, tool)
            value["assertions"][0].update(assessment="contradicted", problem="The source says otherwise.")
            return value
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[lambda c, t: (supported(c, t), objecting(c, t)), supported])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        [rejection] = [e for e in agent.diagnostics["rejected_attempts"] if e.get("phase") == "support"]
        self.assertEqual(rejection["validation_code"], "tool_call_count")

    def test_absence_naming_rendered_comments_is_annotated_never_dropped(self):
        # Smoke run 2026-11-03: the named IDs meant "quote these comments", so a table row cannot settle it.
        def absence(context, tool):
            return {"decision": "revise", "score": 2, "rationale": "A critical example is missing.", "suggestions": [], "missing": [{
                "request_ref": next(iter(context["question_excerpts"])), "issue": "No critical excerpt is shown.",
                "requested_change": "Quote a critical comment.", "missing_source_ids": ["survey:CMT1", "survey:CMT2"]}]}
        model = Scripted(submit_completeness_review=[absence], submit_support_review=[
            lambda context, tool: supported(context, tool, obligations={key: {"status": "open", "note": "No critical quote."}
                for key in tool["parameters"]["properties"]["obligations"]["properties"]})])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "revise")
        self.assertEqual(len(agent.diagnostics["absence_annotations"]), 1)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertIn("survey:CMT1, survey:CMT2", sent["code_note"])
        self.assertEqual(result.corrections[0]["missing_source_ids"], ["survey:CMT1", "survey:CMT2"])
        self.assertEqual(model.calls[0]["history"][0]["content"].count("per_comment_classifications"), 1)

    def test_support_schema_is_flat_and_a_stringified_list_is_rejected(self):
        def stringified(context, tool):
            value = supported(context, tool)
            value["assertions"] = json.dumps(value["assertions"])
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[stringified, supported])
        agent, result = self.review(model)
        properties = model.calls[1]["tool"]["parameters"]["properties"]
        self.assertNotIn("findings", properties)
        self.assertEqual(properties["assertions"]["type"], "array")
        self.assertIn("type", agent.diagnostics["rejected_attempts"][0]["codes"])
        self.assertEqual(result.decision, "accept")

    def test_all_errors_reported_together_and_retry_sends_only_latest_attempt(self):
        def broken(context, tool):
            value = supported(context, tool)
            first, second = value["assertions"][0]["finding_id"], value["assertions"][1]["finding_id"]
            value["assertions"] = [a for a in value["assertions"] if a["finding_id"] != first]
            value["assertions"][0].update(assessment="insufficient_evidence", problem=None)
            self.assertEqual(value["assertions"][0]["finding_id"], second)
            value["safety_issue_index"] = 3
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[broken, supported])
        agent, result = self.review(model)
        rejection = agent.diagnostics["rejected_attempts"][0]
        self.assertEqual(set(rejection["codes"]), {"finding_missing", "problem_required", "safety_index"})
        self.assertEqual(rejection["resolution"], "accepted_review_submission")
        retry = model.calls[2]
        self.assertEqual(len(retry["history"]), 3)
        self.assertEqual(len(pending(retry["tool"], "assertions")), 2)
        self.assertEqual(pending(retry["tool"], "label_disputes"), [])
        self.assertEqual(result.decision, "accept")

    def test_label_dispute_withholds_only_the_table_and_routes_to_vanilla(self):
        def dispute(context, tool):
            value = supported(context, tool)
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT8",
                                        "proposed_label": "positive", "stored_label_defensible": False,
                                        "problem": "The comment states no current criticism."}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[dispute])
        _, result = self.review(model)
        withheld = [f for f in result.findings if f["status"] != "supported"]
        self.assertEqual([f["kind"] for f in withheld], ["table"])
        self.assertEqual(result.decision, "revise")
        self.assertEqual([c["owner"] for c in result.corrections], ["Vanilla"])

    def test_label_objection_outside_label_disputes_is_dropped(self):
        # Luna 67: a label called defensible came back as a Vanilla new issue; Original could not relabel it.
        # Luna 72: the same objection linked as the safety issue while safety was rated 3.
        for owner, kind, safety, kept in (("Vanilla", "unsupported_claim", 3, False), ("Original", "unsupported_claim", 3, True),
                                          ("Vanilla", "missing_deliverable", 3, True), ("Vanilla", "unsupported_claim", 1, True)):
            with self.subTest(owner=owner, kind=kind, safety=safety):
                def objection(context, tool):
                    value = supported(context, tool, safety_issue_index=0, new_issues=[{"kind": kind, "owner": owner,
                        "request_ref": next(iter(context["question_excerpts"])), "issue": "CMT8 could also be mixed.",
                        "requested_change": "Re-examine the CMT8 label.", "finding_ids": pending(tool, "label_disputes"),
                        "citation_ids": ["SENTIMENT1", "survey:CMT8"], "missing_source_ids": []}])
                    value["ratings"]["Safety / Appropriateness"]["score"] = safety
                    return value
                model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[objection])
                agent, result = self.review(model)
                codes = {n["code"] for n in agent.diagnostics.get("delivery_normalizations", [])}
                self.assertEqual("label_issue_outside_disputes_dropped" in codes, not kept)
                self.assertEqual([c["owner"] for c in result.corrections], [owner] if kept else [])
                self.assertEqual(result.decision, "revise" if kept else "accept")

    def test_excess_assertions_are_truncated_only_when_all_supported(self):
        # Gemini 68: 43 supported near-copies for one finding failed the last support attempt.
        for flagged in (False, True):
            with self.subTest(flagged=flagged):
                def repeated(context, tool):
                    value = supported(context, tool)
                    extra = [dict(value["assertions"][0]) for _ in range(13)]
                    if flagged:
                        extra[-1].update(assessment="insufficient_evidence", problem="Not in the cited source.")
                    value["assertions"] += extra
                    return value
                model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[repeated, supported])
                agent, result = self.review(model)
                codes = {n["code"] for n in agent.diagnostics.get("delivery_normalizations", [])}
                rejected = [code for r in agent.diagnostics["rejected_attempts"] for code in r["codes"]]
                self.assertEqual("supported_assertions_truncated" in codes, not flagged)
                self.assertEqual(rejected, ["assertion_coverage"] if flagged else [])
                self.assertEqual(result.decision, "accept")

    def test_resent_supported_assertions_for_settled_findings_are_ignored(self):
        # Luna 74: the retry re-sent supported assertions for findings already accepted and the review failed.
        for flagged in (False, True):
            with self.subTest(flagged=flagged):
                def partial(context, tool):
                    value = supported(context, tool)
                    value["assertions"] = value["assertions"][1:]
                    return value
                def resend(context, tool):
                    value = supported(context, tool)
                    pending_ids = {a["finding_id"] for a in value["assertions"]}
                    for finding in context["findings"]:
                        if finding["finding_id"] not in pending_ids:
                            value["assertions"].append({"finding_id": finding["finding_id"], "claim": "Restated.",
                                "kind": "factual", "citation_ids": finding["citation_ids"][:1],
                                "assessment": "supported", "problem": None})
                    if flagged:
                        value["assertions"][-1].update(assessment="contradicted", problem="Now judged wrong.")
                    return value
                model = Scripted(submit_completeness_review=[accept_completeness],
                                 submit_support_review=[partial, resend, supported])
                agent, result = self.review(model)
                codes = {n["code"] for n in agent.diagnostics.get("delivery_normalizations", [])}
                rejected = [code for r in agent.diagnostics["rejected_attempts"] for code in r["codes"]]
                self.assertIn("assertion_outside_pending_dropped", codes)
                self.assertEqual(rejected, ["finding_missing"] + (["finding_identity"] if flagged else []))
                self.assertEqual(result.decision, "accept")

    def test_one_truncation_per_phase_is_free_and_a_second_earns_the_spare_attempt(self):
        # Luna 81: two truncations and one rejection failed with the spare unused. Gemini 108: the spare went
        # to the first truncating phase, and the next support phase failed with none left.
        from agents.validation import OutputTokenLimit
        def truncated(context, tool):
            raise OutputTokenLimit("Model output token budget exhausted before completion.")
        def partial(context, tool):   # a second error code: never a free progress attempt
            value = supported(context, tool)
            value["assertions"] = value["assertions"][1:]
            value["safety_issue_index"] = 99
            return value
        for script, expected in (([truncated, partial, partial, supported], (4, None)),
                                 ([truncated, truncated, partial, supported], (4, None)),
                                 ([truncated, truncated, partial, partial, supported], (5, True))):
            with self.subTest(attempts=len(script)):
                model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=script)
                agent, result = self.review(model)
                support = next(p for p in agent.diagnostics["review_phases"] if p["phase"] == "support")
                self.assertEqual((support["model_attempts"], support.get("extra_protocol_attempt")), expected)
                self.assertEqual(agent.budget.review_protocol_repairs, int(bool(expected[1])))
                self.assertEqual(result.decision, "accept")
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[partial, partial, partial, supported])
        with self.assertRaisesRegex(RuntimeError, "review delivery protocol exhausted"):
            self.review(model)
        self.assertEqual(len(model.queues["submit_support_review"]), 1)

    def test_one_rejection_that_only_misses_findings_after_accepting_others_is_free(self):
        # Runs 70-113: 5 of 6 failed support phases began with such a rejection.
        def partial(context, tool):   # drops the first pending finding, accepts the rest
            value = supported(context, tool)
            value["assertions"] = value["assertions"][1:]
            return value
        def partial_and_invalid(context, tool):
            return {**partial(context, tool), "safety_issue_index": 99}
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[partial, partial, partial, supported])
        agent, result = self.review(model)
        support = next(p for p in agent.diagnostics["review_phases"] if p["phase"] == "support")
        self.assertEqual((support["model_attempts"], support["progress_attempts"], support.get("extra_protocol_attempt")),
                         (4, 1, None))
        self.assertEqual(agent.budget.review_protocol_repairs, 0)
        self.assertEqual(result.decision, "accept")
        # Another error in the same call, or nothing newly accepted, still counts.
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[partial_and_invalid, partial, partial, supported])
        with self.assertRaisesRegex(RuntimeError, "review delivery protocol exhausted"):
            self.review(model)
        self.assertEqual(len(model.queues["submit_support_review"]), 1)
        agent = reviewer(Scripted(), self.report, self.docs, self.evidence)
        phase, attempts = {"phase": "support", "candidate_id": "C", "progress_attempts": 0}, []
        for attempt in agent.phase_attempts(agent.budget, phase):
            attempts.append(attempt)
            phase["progress_attempts"] = 2
        self.assertEqual(len(attempts), 4)   # three delivered attempts plus one progress attempt, never two

    def test_a_finding_named_by_an_unsupported_claim_issue_is_withheld(self):
        # Medium Gemini 6 released F26 although the reviewer's unsupported_claim issue named it.
        def objecting(context, tool):
            key = next(f["finding_id"] for f in context["findings"] if f["kind"] == "interpretation")
            return supported(context, tool, new_issues=[new_issue(tool, finding_ids=[key])])
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[objecting])
        _, result = self.review(model)
        [flagged] = [f for f in result.findings if f["release_blockers"]]
        self.assertEqual(flagged["release_blockers"], ["reviewer_unsupported_claim"])
        self.assertEqual((flagged["status"], flagged["evidence_status"]), ("withheld", "supported"))
        self.assertTrue(all(f["status"] == "supported" for f in result.findings if f is not flagged))
        self.assertEqual(result.decision, "revise")

    def test_a_restated_obligation_keeps_its_correction_id_and_counts_the_repeat(self):
        # Medium Gemini 6: one open obligation came back under four new correction IDs.
        prior = [{"correction_id": "C_0123456789abcdef_support_1", "kind": "unsupported_claim", "owner": "Original",
                  "issue": "The finding diagnoses the cause.", "requested_change": "State the limitation instead.",
                  "request_excerpt": None, "citation_ids": []}]
        cid = prior[0]["correction_id"]
        def restate(status):
            def build(context, tool):
                key = next(f["finding_id"] for f in context["findings"] if f["kind"] == "interpretation")
                return supported(context, tool, obligations={cid: {"status": status, "note": "Moved, not fixed."}},
                                 new_issues=[new_issue(tool, finding_ids=[key], obligation_ref=cid)])
            return build
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[restate("satisfied"), restate("open")])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                              previous_corrections=prior)
        rejected = [code for r in agent.diagnostics["rejected_attempts"] for code in r["codes"]]
        self.assertEqual(rejected, ["obligation_ref_status"])
        [kept] = result.corrections
        self.assertEqual((kept["correction_id"], kept["obligation_ref"], kept["raised_count"], kept["issue"], kept["reviewer_note"]),
                         (cid, cid, 2, "Overstates the cause.", "Moved, not fixed."))

    def test_obligations_take_one_status_and_see_original_disputes(self):
        prior = [{"correction_id": "C_0123456789abcdef_visible_1", "kind": "missing_deliverable", "owner": "Original",
                  "issue": "Team questions are missing.", "requested_change": "Add two team questions.",
                  "request_excerpt": None, "citation_ids": []}]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, obligations={prior[0]["correction_id"]: {
                "status": "open", "note": "Still absent from the visible answer."}})])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        agent.original_responses = {prior[0]["correction_id"]: {"response": "disputed", "note": "The question asked for none."}}
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                              previous_corrections=prior)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertEqual(sent["original_response"]["response"], "disputed")
        self.assertEqual(result.correction_reviews[0]["status"], "unresolved")
        self.assertEqual(result.corrections[0]["reviewer_note"], "Still absent from the visible answer.")
        self.assertEqual(result.decision, "revise")

    def test_completeness_restatement_keeps_the_earlier_correction_id(self):
        # Runs 70-113: completeness re-reported earlier omissions under new IDs because it never saw them.
        prior = [{"correction_id": "C_0123456789abcdef_visible_1", "kind": "missing_deliverable", "owner": "Original",
                  "issue": "Team questions are missing.", "requested_change": "Add two team questions.",
                  "request_excerpt": None, "citation_ids": [], "raised_count": 2},
                 {"correction_id": "C_0123456789abcdef_support_1", "kind": "unsupported_claim", "owner": "Original",
                  "issue": "Overstates the cause.", "requested_change": "State the limitation.",
                  "request_excerpt": None, "citation_ids": []}]
        cid = prior[0]["correction_id"]
        def restate(ref):
            def build(context, tool):
                value = self.revise(context, tool)
                value["missing"] = [{**value["missing"][0], "obligation_ref": ref}]
                return value
            return build
        model = Scripted(submit_completeness_review=[restate("C_unknown"), restate(cid)], submit_support_review=[
            lambda context, tool: supported(context, tool, obligations={key: {"status": "open" if key == cid else "satisfied",
                "note": "Still absent."} for key in tool["parameters"]["properties"]["obligations"]["properties"]})])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                              previous_corrections=prior)
        sent = json.loads(model.calls[0]["history"][0]["content"])
        self.assertEqual([c["correction_id"] for c in sent["earlier_corrections"]], [cid])
        self.assertEqual([code for r in agent.diagnostics["rejected_attempts"] for code in r["codes"]], ["obligation_ref"])
        [kept] = [c for c in result.corrections if c["kind"] == "missing_deliverable"]
        self.assertEqual((kept["correction_id"], kept["obligation_ref"], kept["raised_count"], kept["detected_phases"]),
                         (cid, cid, 3, ["completeness"]))
        self.assertEqual(result.decision, "revise")

    def test_mechanical_delivery_slips_are_normalized_instead_of_rejected(self):
        # Smoke run 2026-11-03: these four slips exhausted the support attempts of B2 and B15.
        def slips(context, tool):
            value = supported(context, tool)
            interpretation = next(a for a in value["assertions"] if a["finding_id"] == "F2")
            interpretation["citation_ids"] = ["SENTIMENT1", "survey:CMT3"]   # CMT3 belongs to no finding here
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT8",
                                        "proposed_label": "mixed", "stored_label_defensible": False, "problem": "Mixed fits the comment."}]
            value["new_issues"] = [{"kind": "policy_requirement", "owner": "Cherry",
                                    "request_ref": next(iter(context["question_excerpts"])), "issue": "No action.",
                                    "requested_change": "Add one action.", "finding_ids": [], "citation_ids": [],
                                    "missing_source_ids": []}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[slips])
        agent, result = self.review(model, require_actionable=True)
        self.assertEqual(agent.diagnostics["rejected_attempts"], [])
        self.assertEqual({n["code"] for n in agent.diagnostics["delivery_normalizations"]},
                         {"assertion_citations_outside_finding", "dispute_same_label_dropped", "policy_requirement_fields_fixed"})
        boundary = next(f for f in result.findings if f["kind"] == "limitation")
        self.assertNotIn(boundary["finding_id"], pending(model.calls[1]["tool"], "assertions"))
        self.assertEqual(boundary["status"], "supported")
        self.assertEqual(next(f for f in result.findings if f["kind"] == "table")["label_disputes"], [])
        policy = next(c for c in result.corrections if c["kind"] == "policy_requirement")
        self.assertEqual((policy["owner"], policy["request_excerpt"]), ("Original", None))
        self.assertEqual(result.decision, "revise")

    def test_empty_manager_action_list_records_the_policy_gap_in_code(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, proposal_types=[
                {"finding_id": key, "type": "team_question"} for key in
                tool["parameters"]["properties"]["proposal_types"]["items"]["properties"]["finding_id"]["enum"]])])
        _, result = self.review(model, require_actionable=True)
        policy = [c for c in result.corrections if c["kind"] == "policy_requirement"]
        self.assertEqual([(c["owner"], c["request_excerpt"]) for c in policy], [("Original", None)])
        self.assertEqual(result.decision, "revise")

    def test_untyped_answer_never_gets_a_code_derived_policy_correction(self):
        # Without rendered claims there are no proposal findings, so an empty list would mean nothing.
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, "Most comments describe recognition favorably. [SENTIMENT1]", self.evidence,
                              require_actionable=True)
        self.assertNotIn("proposal_types", model.calls[1]["tool"]["parameters"]["properties"])
        self.assertIn("add one new issue of kind policy_requirement", model.calls[1]["instructions"])
        self.assertFalse(any(c["correction_id"].endswith("_policy_action") for c in result.corrections))

    def test_listed_action_satisfies_the_policy_without_a_correction(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        _, result = self.review(model, require_actionable=True)
        self.assertEqual(result.decision, "accept")

    def test_category_claim_is_checked_against_stored_labels(self):
        # B7/B15 pattern: prose about mixed comments that cites a comment stored as positive.
        catalog = FactCatalog(self.evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
            {"text": "Mixed comments combine support with gaps.", "citation_ids": ["survey:CMT8", "survey:CMT3"], "quote": None}],
            "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
            "Original")
        answer, claims = render_answer(payload, catalog, "Original")
        grounding = {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}
        prose = next(c for c in claims if c["kind"] == "interpretation")["finding_id"]
        claim = lambda labels: lambda context, tool: supported(context, tool, category_claims=[{"finding_id": prose, "labels": labels}])
        # Run 118 F12: a partial match goes back once too; the resent claim is the judgment.
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[claim(["mixed"]), claim(["mixed"])])
        result = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
        feedback = json.loads(json.loads(model.calls[2]["history"][-1]["output"])["error"])
        self.assertEqual(feedback["errors"][0]["code"], "category_claim_conflict")
        self.assertNotIn("positive", json.dumps(feedback["errors"][0]))
        finding = next(f for f in result.findings if f["finding_id"] == prose)
        self.assertEqual(finding["status"], "withheld")
        self.assertIn("survey:CMT3 (stored positive)", finding["deterministic_issues"][-1])
        self.assertEqual(next(c for c in result.corrections if c["correction_id"].endswith("_category"))["citation_ids"],
                         ["survey:CMT3"])
        model = Scripted(submit_completeness_review=[accept_completeness],
                         submit_support_review=[claim(["mixed"]), claim(["mixed", "positive"])])
        result = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
        self.assertEqual(result.decision, "accept")

    def test_category_claim_matching_no_stored_label_goes_back_once(self):
        # Run 115 F10: the claim belonged to the neighbouring finding; a repeated claim is still the judgment.
        catalog = FactCatalog(self.evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
            {"text": "One mixed comment combines support with gaps.", "citation_ids": ["survey:CMT8"], "quote": None}],
            "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
            "Original")
        answer, claims = render_answer(payload, catalog, "Original")
        grounding = {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}
        prose = next(c for c in claims if c["kind"] == "interpretation")["finding_id"]
        claim = lambda labels: lambda context, tool: supported(context, tool, category_claims=[{"finding_id": prose, "labels": labels}])
        for second, decision in ((["mixed"], "accept"), (["negative"], "revise")):
            model = Scripted(submit_completeness_review=[accept_completeness],
                             submit_support_review=[claim(["negative"]), claim(second)])
            result = reviewer(model, self.report, self.docs, self.evidence).review(
                QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
            self.assertEqual(len(model.calls), 3)
            self.assertEqual(result.decision, decision)
            self.assertEqual(any(c["correction_id"].endswith("_category") for c in result.corrections), decision == "revise")

    def test_category_claim_with_several_labels_accepts_comments_of_each(self):
        # Luna/Gemini B15 F4: one paragraph about negative and mixed comments.
        catalog = FactCatalog(self.evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
            {"text": "Negative and mixed comments share one gap.", "citation_ids": ["survey:CMT1", "survey:CMT8"], "quote": None}],
            "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
            "Original")
        answer, claims = render_answer(payload, catalog, "Original")
        grounding = {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}
        prose = next(c for c in claims if c["kind"] == "interpretation")["finding_id"]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, category_claims=[{"finding_id": prose, "labels": ["negative", "mixed"]}])])
        result = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
        self.assertEqual(result.decision, "accept")

    def test_supported_factual_claim_without_citations_gets_its_finding_sources(self):
        def uncited(context, tool):
            value = supported(context, tool)
            factual = next(a for a in value["assertions"] if a["kind"] == "factual")
            factual["citation_ids"] = []
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[uncited])
        agent, result = self.review(model)
        self.assertEqual(agent.diagnostics["rejected_attempts"], [])
        self.assertIn("supported_assertion_citations_defaulted", {n["code"] for n in agent.diagnostics["delivery_normalizations"]})
        self.assertEqual(result.decision, "accept")

    def test_dispute_marked_defensible_is_dropped(self):
        def defensible(context, tool):
            value = supported(context, tool)
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT12",
                                        "proposed_label": "positive", "stored_label_defensible": True,
                                        "problem": "Mixed is defensible; positive is also possible."}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[defensible])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        self.assertIn("dispute_defensible_label_dropped", {n["code"] for n in agent.diagnostics["delivery_normalizations"]})

    def test_production_original_reviews_with_v8(self):
        # A fresh interpreter: test_agents pins the review-v7 fixtures for the older workflow tests.
        import subprocess, sys
        from pathlib import Path
        code = ("from agents.original import OriginalAgent; from agents.zero_sugar import ZeroSugarAgent; "
                "import run_agent; assert OriginalAgent.reviewer_class is ZeroSugarAgent; "
                "assert run_agent.ZeroSugarAgent is ZeroSugarAgent; "
                "from agents.original import OriginalAgent; assert run_agent.OriginalAgent is OriginalAgent")
        subprocess.run([sys.executable, "-B", "-c", code], cwd=Path(__file__).resolve().parents[1], check=True)

    def test_original_v7_challenge_reaches_v8_as_a_dispute(self):
        prior = [{"correction_id": "C_0123456789abcdef_visible_1", "kind": "missing_deliverable", "owner": "Original",
                  "issue": "Team questions are missing.", "requested_change": "Add two team questions.",
                  "request_excerpt": None, "citation_ids": []}]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        agent.correction_challenges = [{"correction_ids": [prior[0]["correction_id"]], "finding_ids": [],
                                        "reason": "Two questions are already visible."}]
        agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                     previous_corrections=prior)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertEqual(sent["original_response"], {"response": "disputed", "note": "Two questions are already visible."})

    def test_low_score_without_item_is_recorded_not_a_revision(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, ratings={d: {"score": 2 if d == "Clarity" else 3, "note": "Fine."}
                                                                    for d in DIMENSIONS})])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        self.assertEqual(agent.diagnostics["unexplained_low_scores"], ["Clarity"])


def original_agent(model):
    agent = OriginalAgent(DATABASE, SCOPE, lambda name: model, "live")
    agent.budget = RunBudget()
    agent.set_delegations([])
    agent.numeric_requested = False
    agent.reusable_blocks, agent.draft_blocks, agent.draft_texts = {}, {}, {}
    return agent


def answer(context, tool, **changes):
    critical = next(ref for ref, source, _ in context["excerpts"] if source == "survey:CMT1")
    value = {"fact_ids": [], "interpretations": [], "reuse_ids": [], "removals": [],
             "examples": [{"excerpt_ref": critical, "label": "Critical example", "label_group": "negative"}],
             "proposals": [{"text": "Discuss uneven recognition with the team.", "citation_ids": ["SENTIMENT1"]}]}
    if "correction_responses" in tool["parameters"]["properties"]:
        value["correction_responses"] = {key: {"response": "fixed", "note": "Added."}
                                         for key in tool["parameters"]["properties"]["correction_responses"]["properties"]}
    value.update(changes)
    return value


class OriginalContractTests(unittest.TestCase):
    def setUp(self):
        self.report, self.docs, self.evidence = classification_fixture()

    def test_example_citation_is_derived_from_its_excerpt_and_replays_in_review(self):
        model = Scripted(submit_answer=[answer], submit_completeness_review=[accept_completeness],
                         submit_support_review=[supported])
        agent = original_agent(model)
        result = Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        example = next(c for c in result.claims if c.get("quote"))
        self.assertEqual((example["quote"], example["citation_ids"]), ("Comment number 1.", ["survey:CMT1"]))
        self.assertTrue(any(c["kind"] == "table" and c["operation"].get("type") == "sentiment_classifications"
                            for c in result.claims))
        verdict = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, result.answer, result.evidence, claims=result.claims, grounding=result.grounding)
        self.assertEqual(verdict.deterministic_issues, [])
        self.assertEqual(verdict.decision, "accept")

    def test_an_empty_workspace_tells_original_to_delegate_instead_of_citing(self):
        # Medium Luna 6: five submissions cited "N/A" and no feedback said that the workspace was empty.
        from agents.runtime import AgentRunError
        def unsourced(context, tool):
            return {"fact_ids": [], "interpretations": [{"text": "No data was supplied.", "citation_ids": ["N/A"]}],
                    "examples": [], "proposals": [], "reuse_ids": [], "removals": []}
        for delegations, hinted in ((["Cherry"], True), ([], False)):
            with self.subTest(delegations=delegations):
                model = Scripted(submit_answer=[unsourced] * 3)
                agent = original_agent(model)
                agent.set_delegations(delegations)
                with self.assertRaises(AgentRunError):
                    Specialist.run(agent, QUESTION, initial_evidence=[])
                feedback = json.loads(json.loads(model.calls[1]["history"][-1]["output"])["error"])
                self.assertEqual(feedback["errors"][0]["code"] == "evidence_required", hinted)
                self.assertEqual("ask_cherry" in feedback["instruction"], hinted)

    def test_every_delivery_error_is_reported_once_and_retry_drops_older_attempts(self):
        def broken(context, tool):
            return answer(context, tool, removals=[{"block_id": "BLOCK_0000000000000000", "reason": "Old."}],
                          interpretations=[{"text": "Positive comments.", "citation_ids": ["survey:CMT1"], "label_group": "positive"},
                                           {"text": "Unknown.", "citation_ids": ["survey:NOPE"], "label_group": None}])
        model = Scripted(submit_answer=[broken, broken, answer])
        agent = original_agent(model)
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        rejection = agent.last_result.diagnostics["rejected_attempts"][0]
        self.assertEqual(set(rejection["codes"]), {"removal_unknown", "label_group_mismatch", "source_unknown"})
        self.assertEqual(len(model.calls), 3)
        # question + retained evidence + workspace + the latest rejected call and its feedback
        self.assertEqual(len(model.calls[2]["history"]), 5)

    def test_a_second_narrative_overflow_is_trimmed_instead_of_rejected_again(self):
        # Live 93/99: Original resent more than 12 interpretations until agent_turn_limit.
        words = ("Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliett",
                 "Kilo", "Lima", "Mike", "November")
        def oversized(context, tool):
            return answer(context, tool, interpretations=[{"text": w + " theme.", "citation_ids": ["survey:CMT1"],
                                                           "label_group": None} for w in words])
        # Runs 118, medium Luna 13: in a repair draft the first overflow is already trimmed.
        for repair_round, calls in ((0, 2), (1, 1)):
            with self.subTest(repair_round=repair_round):
                model = Scripted(submit_answer=[oversized, oversized])
                agent = original_agent(model)
                agent.repair_round = repair_round
                result = Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
                self.assertEqual(len(model.calls), calls)
                rejected = agent.last_result.diagnostics.get("rejected_attempts", [])
                self.assertEqual([r["validation_code"] for r in rejected], ["narrative_count"] * (calls - 1))
                [entry] = result.diagnostics["answer_truncations"]
                self.assertEqual((entry["field"], entry["kept_count"]), ("interpretations", 12))
                self.assertEqual(len(result.grounding["payload"]["interpretations"]), 12)

    def test_a_mislabeled_example_is_retried_once_then_dropped(self):
        # Medium Gemini 4: seven label_group_mismatch rejections on examples[0], then agent_turn_limit.
        def mislabeled(context, tool):
            value = answer(context, tool)
            value["examples"][0]["label_group"] = "positive"
            return value
        model = Scripted(submit_answer=[mislabeled, mislabeled])
        agent = original_agent(model)
        result = Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        self.assertEqual(len(model.calls), 2)
        feedback = json.loads(json.loads(model.calls[1]["history"][-1]["output"])["error"])
        self.assertEqual(feedback["errors"][0]["stored_labels"], {"survey:CMT1": "negative"})
        self.assertFalse(any(c.get("quote") for c in result.claims))

    def test_label_group_without_cited_comments_is_normalized_without_a_retry(self):
        # Run 64 spent five retries on label_group_sources; label_group is validation-only, so it is dropped.
        def aggregate_group(context, tool):
            return answer(context, tool, interpretations=[
                {"text": "Negative comments are a minority.", "citation_ids": ["SENTIMENT1"], "label_group": "negative"}])
        model = Scripted(submit_answer=[aggregate_group])
        agent = original_agent(model)
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(agent.last_result.diagnostics.get("rejected_attempts", []), [])

    def test_only_a_requested_chart_blocks_completion(self):
        from types import SimpleNamespace
        agent = original_agent(Scripted())
        failure = {"error_category": "task_declined"}
        candidate = SimpleNamespace(visualization={"charts": [], "tool_trace": []})
        self.assertIsNone(agent.chart_blocks("Summarize recognition comments.", candidate, failure))
        self.assertIn("No chart was requested", candidate.visualization["reason"])
        self.assertEqual(agent.chart_blocks("Show a chart of recognition scores.", candidate, failure), failure)

    def test_repair_answers_each_open_correction_and_keeps_disputes(self):
        def silent(context, tool):
            value = answer(context, tool)
            value.pop("correction_responses")
            return value
        disputed = lambda context, tool: answer(context, tool, correction_responses={
            "C_0123456789abcdef_visible_1": {"response": "disputed", "note": "The question asks for one action only."}})
        model = Scripted(submit_answer=[silent, disputed])
        agent = original_agent(model)
        agent.open_corrections = [{"correction_id": "C_0123456789abcdef_visible_1", "owner": "Original",
                                   "kind": "missing_deliverable", "issue": "A second action is missing.",
                                   "requested_change": "Add a second action."}]
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        self.assertEqual(agent.last_result.diagnostics["rejected_attempts"][0]["codes"], ["fields"])
        self.assertEqual(agent.correction_responses["C_0123456789abcdef_visible_1"]["response"], "disputed")

    def test_prompts_do_not_name_the_single_test_case(self):
        for text in (PLANNING_INSTRUCTIONS, INSTRUCTIONS, SUPPORT_INSTRUCTIONS, COMPLETENESS_INSTRUCTIONS):
            self.assertNotIn("Recognition", text)


class AcceptedAnswerTests(unittest.TestCase):
    def test_only_a_planned_specialist_failure_blocks_an_accepted_answer(self):
        # Gemini 71: the plan needed no numbers; an extra Cherry recheck truncated and the accepted run ended partial.
        from types import SimpleNamespace
        from unittest import mock
        from agents.runtime import AgentResult
        failed = {"agent": "Cherry", "status": "failed", "failure": {"error_category": "output_token_limit"},
                  "task_outcome": {"status": "incomplete", "evidence_retained": False}}
        for planned, blocked in (({"Vanilla"}, False), ({"Vanilla", "Cherry"}, True)):
            with self.subTest(planned=planned):
                agent = OriginalAgent(DATABASE, SCOPE, lambda role: None, "live")
                self.addCleanup(agent.close)
                agent.budget, agent.planned_roles = RunBudget(), planned
                agent.child_results = [{"agent": "Vanilla", "status": "completed"}, failed]
                verdict = SimpleNamespace(candidate_id="c", release_gate=None, findings=[], repair_targets=[])
                candidate = AgentResult("Original", QUESTION, "answer", SCOPE.__dict__, mode="live")
                with mock.patch.object(OriginalAgent, "incomplete", return_value="incomplete") as incomplete:
                    result = agent.accept(candidate, verdict, [], [], [])
                self.assertEqual(incomplete.called, blocked)
                self.assertEqual(result == "incomplete", blocked)
                if not blocked:
                    self.assertEqual(result.status, "complete")


if __name__ == "__main__":
    unittest.main()
