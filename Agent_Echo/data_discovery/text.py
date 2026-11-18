"""Text templates for the discovery_v1 generator (T1.4 fills TEMPLATES).

Contract for callers (T1.2, T1.3, T1.5, T1.6): call render(family, rng, **slots) with every slot
listed in SLOTS[family]; extra slots are ignored. Family names and slots are fixed by the lead.
"""

import re
from pathlib import Path
from string import Formatter

SLOTS = {
    "thread_topic": ("beneficiary_team", "topic"),
    "message_request": ("requester", "helper", "beneficiary_team", "topic"),
    "message_reply": ("helper", "requester", "topic"),
    "message_thanks": ("helper", "beneficiary_team", "topic", "outcome"),
    "message_vague": ("helper", "topic"),
    "blocker_description": ("blocked_team", "blocking_team", "goal"),
    "blocker_resolution": ("helper", "days", "goal"),
    "incident_notes": ("responders", "owning_team", "severity"),
    "meeting_mention": ("helper", "meeting_team", "topic"),
    "recognition_citation": ("employee", "work"),
    "feedback_partner": ("employee", "beneficiary_team", "work", "outcome"),
    "feedback_vague": ("employee", "beneficiary_team"),
    "goal_text": ("team", "metric", "target"),
    "goal_outcome_note": ("metric", "value"),
    "one_on_one_notes": ("employee", "topic_code"),
    "review_note": ("employee", "work"),
    "team_plan_item": ("team", "partner_team", "topic"),
    "contribution_summary": ("employee", "beneficiary_team", "topic"),
}

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load(family):
    # One template per line in templates/<family>.txt; blank lines and "#" comments are skipped.
    lines = (_TEMPLATE_DIR / f"{family}.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


TEMPLATES = {family: _load(family) for family in SLOTS}

# Words that would announce the hidden answer or make a claim the plan forbids (plan 3.3-3.5, 6.2).
VERDICT_TERMS = (
    "hidden", "hidden work", "invisible", "invisible work", "unrecognized", "unrecognised",
    "not recognized", "never recognized", "unrecognized work", "unacknowledged", "unnoticed",
    "overlooked", "unsung", "unseen", "undervalued", "underappreciated", "unappreciated",
    "under the radar", "behind the scenes", "without credit", "no credit", "deserves recognition",
    "deserves credit", "should be recognized", "should be promoted", "promotion", "promote",
    "burnout", "burned out", "burnt out", "overworked", "overloaded", "exhausted",
    "retention", "flight risk", "attrition", "engagement", "disengaged", "productivity",
    "not shared", "unshared", "never shared", "not visible", "visibility gap",
    "outside their goals", "outside their role", "not their job", "off the books",
    "on their own time", "after hours", "after-hours", "formally assessed", "low performer",
    "high performer", "underperforming",
)
_VERDICT_RES = [
    (term, re.compile(r"(?<!\w)" + r"[\s-]+".join(map(re.escape, re.split(r"[\s-]+", term))) + r"(?!\w)", re.I))
    for term in VERDICT_TERMS
]


def scan(text):
    """Return the verdict terms found in text (case-insensitive, whole words)."""
    return [term for term, pattern in _VERDICT_RES if pattern.search(text)]


def render(family, rng, **slots):
    missing = [slot for slot in SLOTS[family] if slot not in slots]
    if missing:
        raise KeyError(f"{family}: missing slots {missing}")
    return rng.choice(TEMPLATES[family]).format(**slots)


def check_templates():
    import random
    assert set(TEMPLATES) == set(SLOTS), "template families differ from SLOTS"
    for family, templates in TEMPLATES.items():
        assert len(templates) >= 60, f"{family}: only {len(templates)} templates"
        assert len(set(templates)) == len(templates), f"{family}: duplicate templates"
        dummy = {slot: f"<{slot}>" for slot in SLOTS[family]}
        for template in templates:
            fields = {name for _, name, _, _ in Formatter().parse(template) if name is not None}
            assert fields <= set(SLOTS[family]), f"{family}: unknown slots {fields - set(SLOTS[family])} in {template!r}"
            template.format(**dummy)
            assert not scan(template), f"{family}: verdict terms {scan(template)} in {template!r}"
    rng_a, rng_b = random.Random(7), random.Random(7)
    for family in SLOTS:
        dummy = {slot: f"<{slot}>" for slot in SLOTS[family]}
        assert render(family, rng_a, **dummy) == render(family, rng_b, **dummy), f"{family}: not deterministic"
    assert scan("Work went Unrecognized; risk of burn-out? No: burnout.") == ["unrecognized", "burnout"]
    assert scan("We promoted the change") == [] and scan("engagements") == []
    return {family: len(templates) for family, templates in TEMPLATES.items()}


if __name__ == "__main__":
    for family, count in check_templates().items():
        print(f"{family}: {count}")
    print("check_templates: OK")
