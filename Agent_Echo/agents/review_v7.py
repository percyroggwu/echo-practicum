"""Review delivery contracts, not semantic truth heuristics."""

from copy import deepcopy
import json


def explanation_schema(dimensions, references):
    return {'type': 'object', 'properties': {d: {'type': 'object', 'properties': {
        'dimension': {'type': 'string', 'enum': [d]},
        'evidence_refs': {'type': 'array', 'minItems': 1, 'maxItems': 8,
            'items': {'type': 'string', 'enum': list(references)}},
        'observation': {'type': 'string', 'minLength': 2, 'maxLength': 400,
            'description': 'Explain the concrete shortcoming for a low score, or what satisfies this dimension. Not a letter/code.'}},
        'required': ['dimension', 'evidence_refs', 'observation'], 'additionalProperties': False}
        for d in dimensions}, 'required': list(dimensions), 'additionalProperties': False}


def explanation_errors(value, dimensions, references):
    errors = []
    for d in dimensions:
        item = value.get(d) if isinstance(value, dict) else None
        if (not isinstance(item, dict) or set(item) != {'dimension', 'evidence_refs', 'observation'}
                or item.get('dimension') != d or not isinstance(item.get('observation'), str)
                or not 2 <= len(item['observation'].strip()) <= 400
                or not isinstance(item.get('evidence_refs'), list)
                or not 1 <= len(item['evidence_refs']) <= 8
                or any(not isinstance(r, str) or r not in references for r in item['evidence_refs'])):
            errors.append(d)
    return errors


def equivalent_calls(turn, expected):
    """Only collapse identical parsed assessments, never competing decisions."""
    if len(turn.calls) < 2 or any(c.name != expected for c in turn.calls):
        return turn, []
    try:
        values = [json.dumps(json.loads(c.arguments), sort_keys=True) for c in turn.calls]
    except (ValueError, TypeError):
        return turn, []
    if len(set(values)) != 1 or len({c.call_id for c in turn.calls}) != len(turn.calls):
        return turn, []
    result = deepcopy(turn)
    result.calls = result.calls[:1]
    return result, turn.calls[1:]
