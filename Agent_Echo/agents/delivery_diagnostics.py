"""Delivery observations; none of these measurements changes review judgment."""

from copy import deepcopy
import json
import re


def duplication(text):
    words = []
    for index, paragraph in enumerate(re.split(r'\n\s*\n', text), 1):
        clean = re.sub(r'\[[A-Za-z0-9_:-]+\]', '', paragraph).strip()
        if len(clean) >= 60:
            words.append((index, set(re.findall(r'\w+', clean.lower()))))
    pairs = []
    for i, (left, a) in enumerate(words):
        for right, b in words[i + 1:]:
            score = len(a & b) / len(a | b) if a | b else 0
            if score >= .9:
                pairs.append({'paragraphs': [left, right], 'score': score})
    return {'metric': 'paragraph-word-jaccard-v1', 'threshold': .9,
            'minimum_characters': 60, 'pair_count': len(pairs), 'pairs': pairs}


def request_size(instructions, history, tools):
    sections = {name: json.dumps(value, ensure_ascii=False) for name, value in
                [('instructions', instructions), ('history', history), ('tools', tools)]}
    return {name: {'characters': len(value), 'utf8_bytes': len(value.encode('utf-8'))}
            for name, value in sections.items()}


def repair_context(corrections, blocks):
    result = deepcopy(corrections)
    for item in result:
        key = item.get('origin_block_id')
        if key:
            item['origin_block_still_saved'] = key in blocks
    return result


def bind_corrections(corrections, findings, blocks, candidate_id):
    """Bind exact source/text identity only; a finding number never selects an old block."""
    lookup = {item['finding_id']: item for item in findings}
    for correction in corrections:
        if correction.get('origin_candidate_id') != candidate_id:
            continue
        finding = lookup.get(correction.get('origin_finding_id'))
        if not finding:
            continue
        matches = [key for key, block in blocks.items()
                   if isinstance(block.get('value'), dict) and block['value'].get('text')
                   and block['value']['text'] in finding.get('text', '')
                   and set(block['value'].get('citation_ids', [])) == set(finding.get('citation_ids', []))]
        if len(matches) == 1:
            correction['origin_block_id'] = matches[0]
