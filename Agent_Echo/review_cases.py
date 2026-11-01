"""Controlled review cases with declared defects; not human sentiment ground truth.

The annotations are authored independently of the model under test. They concern
explicit deliverables, source identity and fidelity to a supplied label map.
"""

from copy import deepcopy
import hashlib
import json

VERSION = 'review-cases-v1'
REQUIREMENTS = ('counts', 'percentages', 'denominator', 'positive_example',
                'critical_example', 'citation_binding', 'label_fidelity', 'team_questions')
QUESTION = ('Within authorized M14/Q3 scope, classify each of the five eligible Recognition comments, '
    'show counts and percentages for all five categories with the denominator, include short literal '
    'positive and critical examples with citations, and ask two follow-up questions for the team.')
SOURCES = {'survey:TEST1': 'My work is appreciated.', 'survey:TEST2': 'Recognition is fair.',
    'survey:TEST3': 'My work is ignored.', 'survey:TEST4': 'The process was announced.',
    'survey:TEST5': 'Praise is welcome, but uneven.'}
LABELS = dict(zip(SOURCES, ('positive', 'positive', 'negative', 'neutral', 'mixed')))


def cases():
    sections = {
        'counts': 'Category counts: positive 2; negative 1; neutral 1; mixed 1; indeterminate 0.',
        'percentages': 'Category percentages: positive 40%; negative 20%; neutral 20%; mixed 20%; indeterminate 0%.',
        'denominator': 'Denominator: 5 eligible comments in the authorized scope; these are comment percentages, not employee percentages.',
        'positive_example': 'Positive example: "My work is appreciated." [survey:TEST1]',
        'critical_example': 'Critical example: "My work is ignored." [survey:TEST3]',
        'label_fidelity': 'Per-comment labels: ' + '; '.join(k + ' = ' + v for k, v in LABELS.items()) + '.',
        'team_questions': 'Ask the team: What recognition has helped you? Ask the team: What would make recognition fairer?',
        'limits': 'These provisional text labels describe these comments only. No respondent identities are inferred.'}
    variants = [('complete', None), *[('missing_' + key, key) for key in REQUIREMENTS[:5]],
        ('wrong_citation', 'citation_binding'), ('swapped_labels', 'label_fidelity'),
        ('wrong_question_audience', 'team_questions')]
    result = []
    for name, defect in variants:
        current = deepcopy(sections)
        if name.startswith('missing_'):
            current.pop(defect)
        elif name == 'wrong_citation':
            current['positive_example'] = current['positive_example'].replace('[survey:TEST1]', '[survey:TEST3]')
        elif name == 'swapped_labels':
            current['label_fidelity'] = current['label_fidelity'].replace('survey:TEST2 = positive', 'survey:TEST2 = mixed').replace('survey:TEST5 = mixed', 'survey:TEST5 = positive')
        elif name == 'wrong_question_audience':
            current['team_questions'] = 'Ask the team: What recognition has helped you? Ask the reviewers: Is the evidence format clear?'
        result.append({'case_id': name, 'question': QUESTION, 'candidate_answer': '\n\n'.join(current.values()),
            'authorized_scope': {'manager_id': 'M14', 'start_date': '2026-07-01', 'end_date': '2026-09-30'},
            'sources': SOURCES, 'retained_labels': LABELS, 'expected_defects': [defect] if defect else []})
    return result


def corpus_identity():
    return hashlib.sha256(json.dumps(cases(), sort_keys=True).encode()).hexdigest()


def score(judgments):
    """Score explicit annotated objections, never infer correctness from wording.

    Judgments must cover all cases and list defect IDs from REQUIREMENTS. A human
    maps production objections to these IDs and retains their quoted evidence.
    """
    expected = {c['case_id']: set(c['expected_defects']) for c in cases()}
    if not isinstance(judgments, list) or len(judgments) != len(expected):
        raise ValueError('Every fixed case must have exactly one annotated judgment.')
    found, tp, fp, fn, tn = set(), 0, 0, 0, 0
    for item in judgments:
        key, defects = item['case_id'], item['defect_ids']
        if key not in expected or key in found or not isinstance(defects, list) or len(defects) != len(set(defects)) or set(defects) - set(REQUIREMENTS):
            raise ValueError('Use unique known cases and defect IDs.')
        found.add(key)
        actual, gold = set(defects), expected[key]
        tp += len(actual & gold)
        fp += len(actual - gold)
        fn += len(gold - actual)
        tn += len(set(REQUIREMENTS) - actual - gold)
    return {'case_count': len(expected), 'true_positives': tp, 'false_positives': fp,
        'false_negatives': fn, 'true_negatives': tn, 'false_positive_rate': fp / (fp + tn),
        'recall': tp / (tp + fn), 'passes_controlled_threshold': fp == 0 and fn == 0,
        'corpus_version': VERSION, 'corpus_hash': corpus_identity(),
        'scope': 'Controlled explicit defects only; no general semantic-accuracy claim.'}
