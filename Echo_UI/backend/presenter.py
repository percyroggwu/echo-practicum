"""Answer card for Live answers: story fields built only from numbers and findings Echo already produced.

Sources: Cherry's `cross_team_contributions` (v2) and `survey_trend` (Recognition) metric evidence, cited by at
least one finding with status "supported"; Vanilla's sentiment counts; Discovery's code-checked findings.
The UI only reorders and does arithmetic on these numbers; it never queries the database. A missing source
omits its fields. Wording is a fixed template, never model output, so Demo and Live cards look alike.
"""

from datetime import date, timedelta

from offline import ASSUMED_HOURLY_COST as COST, FTE_QUARTER_HOURS, _dollars, _quarter, _tile, _tone

RECOGNITION_GAP_POINTS = 5  # smaller cross-team vs own-team gaps read as "about as often"


def _evidence(artifact):
    return list(artifact.get("evidence") or []) + [e for d in artifact.get("delegations") or [] for e in d.get("evidence") or []]


def _metric(artifact, metric_id, supported):
    """First evidence item of that metric cited by a supported finding."""
    return next((e for e in _evidence(artifact) if e.get("metric_id") == metric_id and e.get("metric_version") == 2
                 and e.get("citation_id") in supported and e.get("rows")), None)


def _num(row, key):
    value = row.get(key)
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _period(scope):
    """(label, phrase): 'Q2 2026' / 'in Q2 2026' for a whole calendar quarter, else the plain date range."""
    try:
        start, end = date.fromisoformat(scope["start_date"]), date.fromisoformat(scope["end_date"])
    except (KeyError, TypeError, ValueError):
        return "this period", "in this period"
    if start.day == 1 and start.month % 3 == 1 and end.month % 3 == 0 and (end + timedelta(1)).day == 1 and _quarter(start.isoformat()) == _quarter(end.isoformat()):
        return _quarter(end.isoformat()), "in " + _quarter(end.isoformat())
    return f"{start} to {end}", f"between {start} and {end}"


def _survey(artifact, supported, team):
    """In-scope Recognition favorable percents for the manager's team, oldest first: [(Survey_Date, percent)]."""
    item = _metric(artifact, "survey_trend", supported)
    if not item or str((item.get("metric_arguments") or {}).get("dimension", "")).casefold() != "recognition":
        return []
    scope = artifact.get("scope") or {}
    rows = [r for r in item["rows"] if isinstance(r.get("Survey_Date"), str) and _num(r, "Favorable_Percent") is not None
            and scope.get("start_date", "") <= r["Survey_Date"] <= scope.get("end_date", "9999")]
    if len({r.get("Team") for r in rows}) > 1:
        rows = [r for r in rows if r.get("Team") == team]
    by_date = {}
    for r in rows:
        by_date.setdefault(r["Survey_Date"], []).append(r["Favorable_Percent"])
    return [(d, values[0]) for d, values in sorted(by_date.items()) if len(values) == 1]


def _voice(artifact, supported):
    """Vanilla's counts for the latest group (Recognition preferred), only from a report a supported finding cites."""
    rows = [r for cid, report in (artifact.get("sentiment") or {}).items() if cid in supported and isinstance(report, dict)
            for r in report.get("rows") or [] if _num(r, "Eligible_Comments") and _num(r, "positive_percent") is not None
            and _num(r, "negative_percent") is not None]
    if not rows:
        return None
    rows.sort(key=lambda r: (str(r.get("Dimension", "")).casefold() == "recognition", r.get("Survey_Date", ""), r["Eligible_Comments"]))
    r = rows[-1]
    return {"topic": r.get("Dimension") or "Survey comments", "responses": r["Eligible_Comments"],
            "positive": round(r["positive_percent"]), "negative": round(r["negative_percent"])}


def _possessive(name):
    return name + ("'" if name.endswith("s") else "'s")


def live_story(artifact):
    """Story fields for the answer card, or {} when Echo's evidence supports none. Adds story_source 'echo'."""
    findings = artifact.get("findings") or []
    supported = {c for f in findings if f.get("status") == "supported" for c in f.get("citation_ids") or []}
    discovery = artifact.get("discovery") or {}
    team = (discovery.get("subject") or {}).get("team")
    story = {}

    people = [f for f in discovery.get("findings") or [] if f.get("kind") == "person" and f.get("recognition_state") != "recognized"
              and f.get("employee_ids") and f.get("employee_names")][:3]
    examples = []
    for f in people:
        example = {"employee_id": f["employee_ids"][0], "name": f["employee_names"][0], "team_helped": f.get("beneficiary_team"),
                   "outcome": f.get("work_summary"), "date": f.get("contribution_date"), "contribution_id": f.get("contribution_id"),
                   "praise_reached_you": f.get("visibility_state") == "shared"}
        examples.append({k: v for k, v in example.items() if v is not None})
    if examples:
        story["examples"] = examples
    found = None
    if examples and examples[0].get("team_helped"):
        e = examples[0]
        found = (f"Discovery found {_possessive(e['name'])} help to {e['team_helped']}"
                 f"{', not yet recognized' if people[0].get('recognition_state') == 'not_recognized' else ''}.")

    # Decision 0.2: the recognize action carries the Discovery A1 action id so Demo and Live share one backend record.
    actions = []
    for f, e in zip(people, examples):
        a1 = next((a for a in f.get("actions") or [] if a.get("action_type") == "A1" and a.get("action_id")), None)
        if a1 and e.get("team_helped"):
            action = {"kind": "recognize", "title": f"Recognize {e['name'].split()[0]}",
                      "why": f"Helped {e['team_helped']}" + (f": {e['outcome'].rstrip('.')}." if e.get("outcome") else "."),
                      "person": {"id": e["employee_id"], "name": e["name"]}, "partner_team": e["team_helped"],
                      "tone": "unrecognized" if e["praise_reached_you"] else "not_passed", "discovery_action_id": a1["action_id"]}
            if e.get("contribution_id"):
                action["example_id"] = e["contribution_id"]
            actions.append(action)

    item = _metric(artifact, "cross_team_contributions", supported)
    row = item["rows"][0] if item else {}
    if (_num(row, "Total_Contributions") or 0) > 0 and _num(row, "Unnoticed_Contributions") is not None:
        total, unnoticed = row["Total_Contributions"], row["Unnoticed_Contributions"]
        label, in_label = _period(artifact.get("scope"))
        recognized = _num(row, "With_Manager_Recognition")
        recognized_pct = 100 * recognized / total if recognized is not None else None
        hours = _num(row, "Unnoticed_Hours")
        praised_not = _num(row, "Praised_Not_Recognized")
        story["headline"] = f"{unnoticed} of {total} pieces of help your team gave other teams went unnoticed {in_label}."
        tiles = [_tile(f"{unnoticed}", "pieces of help nobody saw", "eye", "no_praise")]
        if hours is not None:
            tiles += [_tile(f"{hours:,.0f} h", f"of unnoticed work, about {hours / FTE_QUARTER_HOURS:.1f} people's quarter", "hours", "not_passed"),
                      _tile(_dollars(hours), f"of work off the books (at ${COST}/h, assumed)", "cost", "money")]
        if praised_not is not None:
            tiles.append(_tile(f"{praised_not}", "praised, but never recognized", "award", "unrecognized"))
        story["tiles"] = tiles

        steps = [("Helped another team", total), ("Praised by that team", _num(row, "With_Partner_Feedback")),
                 ("Praise reached you", _num(row, "Praise_Reached_Manager")), ("Recognized by a manager", recognized)]
        if all(v is not None for _, v in steps):
            story["journey"] = {"quarter": label, "steps": [{"label": k, "value": v} for k, v in steps]}

        impact = []
        if hours is not None:
            impact.append(f"About {hours:,.0f} hours of cross-team work went unnoticed {in_label}, roughly {hours / FTE_QUARTER_HOURS:.1f} "
                          f"full-time people's quarter. At an assumed ${COST} an hour that is about {_dollars(hours)}: the size of the blind spot, not a saving.")
        own = _num(row, "Own_Team_Recognized_Percent")
        if recognized_pct is not None and own is not None:
            # A conclusion only on a clear gap: 17% vs 18.5% (M14 Q2) is "about as often", not a signal.
            impact.append(f"Help given to other teams is recognized about as often as own-team work ({recognized_pct:.0f}% vs {own:.0f}%)."
                          if abs(recognized_pct - own) < RECOGNITION_GAP_POINTS else
                          f"Help given to other teams is recognized {recognized_pct:.0f}% of the time versus {own:.0f}% for own-team work"
                          + (", so the current signal to employees is that helping elsewhere does not count." if recognized_pct < own else "."))
        if found:
            impact.append(found)
        if impact:
            story["impact"] = impact

        trend = _survey(artifact, supported, team)
        favorable = trend[-1][1] if trend else None
        not_passed, no_praise, people_count = _num(row, "Praise_Not_Passed_On"), _num(row, "No_Praise"), _num(row, "Unnoticed_People")
        meaning = []
        if None not in (recognized, praised_not, not_passed, no_praise):
            meaning.append(f"Of {total} pieces of help to other teams {in_label}, {recognized} were recognized by a manager, "
                           f"{praised_not} were praised and the praise reached you but were not recognized, {not_passed} were praised "
                           f"without the praise reaching you, and {no_praise} got no feedback at all.")
        if hours is not None and people_count:
            top3 = _num(row, "Top3_Unnoticed_Share_Percent")
            meaning.append(f"The unnoticed work took {hours:,.0f} hours across {people_count} people"
                           + (f"; the 3 people with the most unnoticed work did {top3:.0f}% of it." if top3 is not None else "."))
        if trend:
            meaning.append(f"The Recognition survey was {favorable:.0f}% favorable on {trend[-1][0]}"
                           + (f", {'up' if favorable > trend[-2][1] else 'down' if favorable < trend[-2][1] else 'unchanged'} from "
                              f"{trend[-2][1]:.0f}% on {trend[-2][0]}." if len(trend) > 1 else "."))
        if meaning:
            story["meaning"] = meaning
        if recognized_pct is not None and favorable is not None:
            feedback_tone, voice_tone = _tone(recognized_pct, 50, 25), _tone(favorable)
            conflict = (voice_tone == "good") != (feedback_tone == "good")
            note = (f"The records and the survey disagree: {recognized_pct:.0f}% of cross-team work is recognized by a manager, "
                    f"yet the Recognition survey is {favorable:.0f}% favorable." if conflict else
                    f"The records and the survey point the same way: {recognized_pct:.0f}% recognized by a manager, "
                    f"{favorable:.0f}% favorable in the Recognition survey.")
            story["triangle"] = {
                "work": {"value": str(total), "label": "contributions to other teams", "tone": "neutral", "agent": "Cherry"},
                "feedback": {"value": f"{recognized_pct:.0f}%", "label": "of that work recognized by a manager", "tone": feedback_tone, "agent": "Cherry"},
                "voice": {"value": f"{favorable:.0f}%", "label": "say recognition is good", "tone": voice_tone, "agent": "Cherry"},
                "agreement": "conflict" if conflict else "aligned", "note": f"{note} {found}" if found else note}

        watch = [{"metric": "Cross-team work unnoticed", "baseline": f"{100 * unnoticed / total:.0f}%", "goal": "lower each quarter"}]
        if recognized_pct is not None:
            watch.insert(0, {"metric": "Cross-team work recognized by a manager", "baseline": f"{recognized_pct:.0f}%", "goal": "above 50%"})
        if favorable is not None:
            watch.append({"metric": "Recognition survey favorable", "baseline": f"{favorable:.0f}%", "goal": "hold steady"})
        story["watch"] = watch

        if _num(row, "Total_Hours") is not None:
            actions.append({"kind": "plan", "title": "Put cross-team hours in next quarter's plan", "tone": "money",
                            "why": f"{row['Total_Hours']:,.0f} hours went to other teams {in_label}, and goals and plans follow the org chart."})
        # Echo's next_steps on a partial answer are repair notes, not manager steps; the template replaces them.
        story["next_steps"] = (
            ([f"Start with the {praised_not} pieces of praised work you already heard about: recognize the work specifically, naming the team it helped."]
             if praised_not else []) +
            (["Ask the managers your team helps most to copy you on partner feedback."] if not_passed else []) +
            ["Check again after next quarter's review using the measures below."])

    voice = _voice(artifact, supported)
    if voice:
        story["voice"] = voice
    if actions:
        story["actions"] = actions
    return {**story, "story_source": "echo"} if story else {}
