"""Shared review and workflow fixtures for the offline tests."""

from copy import deepcopy
from agents import AccessScope
from agents.zero_sugar import ZeroSugarAgent, DIMENSIONS
from test_agents import live_fixture, completeness_turn, tool_turn, assertion_reviews
from agents.vanilla import sentiment_summary
import json
import hashlib


SCOPE = AccessScope('M14', '2026-07-01', '2026-09-30')


SOURCE = {'citation_id': 'survey:CMT1', 'text': 'My contributions are noticed.', 'scope': SCOPE.__dict__}


class PhaseModel:
    def __init__(self, completeness=None, support=None):
        self.completeness = iter(completeness or [completeness_turn()])
        self.support = support
        self.calls = []

    def respond(self, instructions, history, tools, require_tool=False):
        context = json.loads(history[0]['content'])
        self.calls.append((tools[0]['name'], deepcopy(context), deepcopy(tools)))
        if tools[0]['name'] == 'submit_rating_explanations':
            return tool_turn('submit_rating_explanations', {'rating_explanations': {
                d: {'dimension': d, 'evidence_refs': ['candidate'], 'observation': r['rationale']}
                for d, r in context['frozen_ratings'].items()}})
        if tools[0]['name'] == 'submit_completeness_review':
            turn = next(self.completeness)
            if isinstance(turn, BaseException):
                raise turn
            return live_fixture(turn, instructions, history, tools)
        if isinstance(self.support, BaseException):
            raise self.support
        if callable(self.support):
            return live_fixture(self.support(context), instructions, history, tools)
        return live_fixture(support_turn(context), instructions, history, tools)


def support_turn(context, issues=(), finding_decision='supported', correction_reviews=None):
    if correction_reviews is None:
        correction_reviews = [{'correction_id': c['correction_id'], 'status': 'resolved',
                               'reason': 'Controlled resolved-correction judgment.'} for c in context.get('previous_corrections', [])]
    return tool_turn('submit_review', {
        'decision': 'accept',
        'ratings': {d: {'score': 3, 'rationale': 'Controlled source-review fixture.'} for d in DIMENSIONS},
        'issues': list(issues), 'suggestions': [], 'uncertainty': 'Not measured semantic quality.',
        'finding_reviews': [{'finding_id': b['finding_id'], 'decision': finding_decision,
                             'reason': 'Controlled source judgment.', 'assertions': assertion_reviews(b, evidence=context.get('evidence'))} for b in context['findings']],
        'repair_targets': ['Original'] if issues else [], 'clarification_question': None,
        'correction_reviews': list(correction_reviews),
    })


def visible(issues=(), request_excerpt='Explain.'):
    return tool_turn('submit_completeness_review', {
        'decision': 'revise' if issues else 'accept', 'score': 2 if issues else 3,
        'rationale': 'Controlled visible-answer assessment.',
        'corrections': [{'issue': issue, 'requested_change': 'Address: ' + issue,
                         'request_excerpt': request_excerpt} for issue in issues],
        'suggestions': [],
    })


def current_support(context, statuses=None, corrections=(), numeric='not_required'):
    report = json.loads(support_turn(context).calls[0].arguments)
    report.pop('issues')
    report.pop('repair_targets')
    report['corrections'] = [{'request_excerpt': context['question'][:400]
                              if item['kind'] == 'missing_deliverable' else None, **item}
                             for item in corrections]
    report['correction_reviews'] = [{
        'correction_id': item['correction_id'],
        'status': (statuses or {}).get(item['correction_id'], 'unresolved'),
        'reason': 'Controlled reassessment against the request and visible draft.',
        'replacement_id': None,
    } for item in context.get('review_obligations', [])]
    report['numeric_reviews'] = [{'request_id': item['request_id'], 'decision': numeric,
                                 'reason': 'Controlled metric relevance judgment.'}
                                for item in context.get('pending_numeric_requests', [])]
    return report


def reviewer(model):
    return ZeroSugarAgent(SCOPE, model, 'live', document_lookup={SOURCE['citation_id']: SOURCE})


def support(context, judgments=None):
    report = current_support(context)
    report.pop('correction_reviews')
    if context.get('review_obligations'):
        report['correction_judgments'] = judgments if judgments is not None else {
            item['correction_id']: {'mandatory': True, 'addressed': False, 'reason': 'Visible requested content is missing.'}
            for item in context['review_obligations']}
    return report


def classification_fixture(n=13):
    docs = [{'citation_id': f'survey:CMT{i}', 'source': 'HR_survey_comments', 'team': 'Data Platforms',
        'date': '2026-09-01', 'dimension': 'Recognition', 'response_text': f'Comment number {i}.'} for i in range(n)]
    labels = [{'citation_id': d['citation_id'], 'label': 'mixed' if i in (8, 11, 12) else 'negative' if i in (1, 2) else 'positive',
        'quote': d['response_text'], 'reason': 'Scripted label, not a semantic annotation.'} for i, d in enumerate(docs)]
    report = {'citation_id': 'SENTIMENT1', 'scope': SCOPE.__dict__, 'dimension': 'Recognition', 'mode': 'live',
        'rubric_version': 'survey-sentiment-v3', 'source_facts_version': 'source-facts-v7', 'labels': labels,
        'source_hashes': {d['citation_id']: hashlib.sha256(d['response_text'].encode()).hexdigest() for d in docs}}
    summary = sentiment_summary(report, docs)
    evidence = [summary, *[{'citation_id': d['citation_id'], 'text': d['response_text'], 'scope': SCOPE.__dict__} for d in docs]]
    return report, docs, evidence
