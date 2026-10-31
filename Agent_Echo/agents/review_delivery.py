"""Mechanical delivery identity and observable review policy; never infer truth."""

from copy import deepcopy
import hashlib
import json
import re


def submission_identity(submitted, code, field):
    value = json.dumps([code, field, submitted], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]


def safety_gate(ratings, issues, indices):
    """Only an explicitly linked issue can activate the new global safety veto.

    A low unexplained score remains a quality limitation, never approval. Invalid
    links are observable but cause no additional review submission rejection.
    """
    valid, invalid = [], []
    for index in indices if isinstance(indices, list) else []:
        if type(index) is int and 0 <= index < len(issues) and isinstance(issues[index], str) and issues[index].strip():
            if index not in valid:
                valid.append(index)
        else:
            invalid.append(index if type(index) is int else None)
    low = ratings['Safety / Appropriateness']['score'] < 3
    return {'policy': 'issue-linked-safety-v1', 'active': low and bool(valid),
            'issue_indices': valid, 'issues': [issues[i] for i in valid],
            'unexplained_low_score': low and not valid, 'invalid_link_count': len(invalid)}


def veto_active(verdict):
    gate = getattr(verdict, 'release_gate', None)
    if gate is not None:
        return bool(gate['active'])
    # Old saved reviews retain their original release semantics.
    return verdict.ratings['Safety / Appropriateness']['score'] < 3


def assertion_alignment(claim, text):
    """Observational only: vocabulary overlap cannot prove or disprove meaning."""
    words = lambda value: set(re.findall(r'\w+', value.casefold()))
    a, b = words(claim), words(text)
    return {'metric': 'claim-block-word-overlap-v1', 'shared_words': len(a & b),
            'claim_words': len(a), 'zero_overlap': bool(a) and not bool(a & b),
            'literal_anchor_found': claim in text, 'semantic_alignment_verified': False}


def obligation_groups(corrections):
    """Group explicit identity aliases only, never guess equivalence from wording."""
    groups = {}
    for item in corrections:
        key = item.get('obligation_id') or item.get('correction_id')
        if key is None:
            key = 'unbound-' + str(len(groups))
        group = groups.setdefault(key, {'obligation_id': key, 'correction_ids': [], 'phases': []})
        for ref in [item.get('correction_id'), *item.get('alias_correction_ids', [])]:
            if ref and ref not in group['correction_ids']:
                group['correction_ids'].append(ref)
        for phase in item.get('detected_phases', []):
            if phase not in group['phases']:
                group['phases'].append(phase)
    return list(groups.values())


def reconcile_corrections(corrections):
    """Coalesce explicit same-ID refinements, preserving all original records."""
    result, lookup = [], {}
    for original in corrections:
        item = deepcopy(original)
        key = item.get('obligation_id') or item.get('correction_id')
        if key is None or key not in lookup:
            result.append(item)
            if key:
                lookup[key] = item
            continue
        prior = lookup[key]
        prior.setdefault('provenance_records', []).append(item)
        prior['detected_phases'] = list(dict.fromkeys(prior.get('detected_phases', []) + item.get('detected_phases', [])))
        prior['alias_correction_ids'] = list(dict.fromkeys(prior.get('alias_correction_ids', []) + [item['correction_id']]))
    return result


def quote_fallback(submitted, evidence):
    """Remove only invalid selected quotes; never invent a source or grant release."""
    from .content import excerpt_catalog
    catalog = excerpt_catalog(evidence)
    revised, removed = deepcopy(submitted), []
    for kind in ('interpretations', 'proposals'):
        items = revised.get(kind, [])
        if not isinstance(items, list):
            continue  # Leave unrelated invalid fields for the normal validator.
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            ref = item.get('quote_ref')
            if ref is not None and (not isinstance(ref, str) or ref not in catalog or catalog[ref]['source_id'] not in item.get('citation_ids', [])):
                item['quote_ref'] = None
                removed.append({'field': kind, 'item_index': index})
    return revised, removed
