"""Continue retained workflows; keep explicit legacy phase retries diagnostic."""

from dataclasses import asdict
import json
from pathlib import Path
import re

from .capture import database_identity, source_versions, trace, digest, checkpoint, checkpoint_progress
from .data_access import AccessScope, ScopedData
from .runtime import AgentResult, RunBudget, Specialist
from .original import OriginalAgent
from .cherry import CherryAgent
from .vanilla import VanillaAgent
from .lime import LimeAgent
from .zero_sugar import ZeroSugarAgent
from .tools import SQLReader
from .sentiment_rubric import SENTIMENT_RUBRIC_VERSION


def resume_phase(saved, registry, database, model_limit=32, seconds=300):
    if saved['kind'] == 'workflow':
        return resume_workflow(saved, registry, database, model_limit, seconds)
    scope = AccessScope(**saved['scope'])
    payload, kind, role = saved['payload'], saved['kind'], saved['role']
    if payload.get('mode') != 'live':
        raise ValueError('Only a live checkpoint can be resumed with live models.')
    expected = payload.get('database_hash')
    if expected is not None and database_identity(database) != expected:
        raise ValueError('The source database changed. Retained work cannot be silently reused against different sources.')
    profile = payload.get('profile')
    if profile and registry.profile_for(role) != profile:
        raise ValueError('Resume must preserve the failed phase model profile; use a separate full test to change models.')
    connection = payload.get('connection')
    if connection:
        current = registry.describe()[role]
        fields = ('provider', 'api', 'endpoint', 'model', 'max_output_tokens', 'timeout_seconds',
                  'max_retries', 'request_interval_seconds', 'rate_limit_retries', 'reasoning_effort', 'clear_thinking')
        if any(current.get(key) != connection.get(key) for key in fields):
            raise ValueError('The retained model/transport configuration changed. Use a separate test rather than mixing checkpoints.')
    budget = RunBudget(model_limit=model_limit, tool_limit=48 + 2 * max(0, model_limit - 32), seconds=seconds)
    question = payload.get('question', 'Resume the retained sentiment classification phase.')
    trace('phase_resume', parent_run_id=saved['run_id'], source_checkpoint=saved['source_path'],
          kind=kind, role=role, prior_code_versions=saved['code_versions'], code_versions=source_versions(),
          model_call_limit=model_limit, run_seconds=seconds)
    agent = None
    try:
        if kind == 'review':
            if role != 'ZeroSugar':
                raise ValueError('Review checkpoints belong to ZeroSugar.')
            backend = ScopedData(database, scope)
            try:
                reader = SQLReader(backend.structured_tables(), scope)
                documents = {doc['citation_id']: doc for doc in backend.text_documents()}
                sentiment_documents, teams = backend.sentiment_documents(), list(backend.teams)
            finally:
                backend.close()
            agent = ZeroSugarAgent(scope, registry.get(role), 'live', budget=budget, sql_reader=reader,
                document_lookup=documents, database=database, sentiment_reports=payload['sentiment_reports'],
                sentiment_documents=sentiment_documents, authorized_teams=teams)
            agent.owned_reader = reader
            review = agent.review(question, payload['answer'], payload['evidence'], **payload['arguments'],
                resume_completeness=saved['progress'].get('completed_completeness'))
            result = AgentResult(role, question, 'Review decision: ' + review.decision,
                scope.__dict__, evidence=payload['evidence'], mode='live',
                verification={**asdict(review), 'status': 'completed'},
                status='unverified' if review.decision == 'accept' else 'partial',
                findings=review.findings, diagnostics={'verification': agent.diagnostics,
                    'phase_only': True, 'candidate_answer': payload['answer'], 'candidate_claims': payload['arguments'].get('claims'),
                    'note': 'Only review was resumed. No Original/Vanilla calls or automatic correction loop ran.'},
                sentiment=payload['sentiment_reports'])
            return result
        if kind == 'planning':
            if role != 'Original':
                raise ValueError('Planning checkpoints belong to Original.')
            agent = OriginalAgent(database, scope, registry.get, 'live', model_call_limit=model_limit, run_seconds=seconds)
            agent.budget = budget
            plan = agent.plan(question)
            return AgentResult(role, question, 'Planning phase completed; no analytical answer was released.',
                scope.__dict__, mode='live', diagnostics={'phase_only': True, 'plan': plan})
        if kind == 'visual':
            if role != 'Lime':
                raise ValueError('Visualization checkpoints belong to Lime.')
            agent = LimeAgent(scope, registry.get(role), 'live', budget)
            result = agent.plan(question, payload['answer'], payload['evidence'], payload.get('feedback'))
            return AgentResult(role, question, 'Visualization phase completed; independent review is still required.',
                scope.__dict__, evidence=payload['evidence'], mode='live', visualization=asdict(result),
                diagnostics={'phase_only': True})
        if role == 'Vanilla':
            agent = VanillaAgent(database, scope, registry.get(role), 'live', budget=budget)
            agent.workflow_reuse = True
            agent.sentiment_reports = payload.get('sentiment_reports', {})
            agent.sentiment_counter = max([int(key[9:]) for key in agent.sentiment_reports if re.fullmatch(r'SENTIMENT\d+', key)] or [0])
        elif role == 'Cherry' and kind == 'specialist':
            agent = CherryAgent(database, scope, registry.get(role), 'live', budget=budget)
        elif role == 'Original' and kind == 'specialist':
            agent = OriginalAgent(database, scope, registry.get, 'live', model_call_limit=model_limit, run_seconds=seconds)
            agent.set_delegations(set())
            agent.handlers = {}  # A focused synthesis retry cannot delegate again.
            agent.budget = budget
        else:
            raise ValueError('Unsupported role for this retained phase.')
        if kind == 'sentiment':
            if role != 'Vanilla' or payload['rubric_version'] != SENTIMENT_RUBRIC_VERSION:
                raise ValueError('Retained classification rubric/role differs; existing labels cannot be silently reused.')
            agent.resume_sentiment = saved['progress'].get('sentiment_state', payload['state'])
            summary = agent.analyze_sentiment(payload['dimension'])
            evidence = [summary] if summary.get('complete') else []
            return AgentResult(role, question, 'Classification phase completed; independent review is still required.'
                if summary.get('complete') else 'Classification remains incomplete; no partial percentages released.',
                scope.__dict__, evidence=evidence, mode='live', sentiment=agent.sentiment_reports,
                status='unverified' if summary.get('complete') else 'incomplete',
                diagnostics={'phase_only': True, 'sentiment_progress': summary})
        agent.resume_state = payload
        if role == 'Vanilla':
            agent.retained_sentiment_progress = list(payload.get('sentiment_progress', {}).values())
        if role == 'Cherry':
            agent.required_metrics = payload.get('required_metrics', [])
            agent.metric_cache = {tuple(item['key']): item['result'] for item in payload.get('metric_cache', [])}
            agent.metric_errors = {tuple(key) for key in payload.get('metric_errors', [])}
            agent.reader.counter = max([int(item['citation_id'][3:]) for item in payload['evidence']
                if re.fullmatch(r'SQL\d+', item.get('citation_id', ''))] or [0])
        raw = Specialist.run(agent, question, diagnostics=payload.get('diagnostics'))
        if role == 'Vanilla':
            agent.attach_sentiment(raw)
        return AgentResult(role, question, 'Retained generation phase completed; independent review is still required.',
            scope.__dict__, evidence=raw.evidence, mode='live', sentiment=raw.sentiment,
            status=raw.status, diagnostics={'phase_only': True, 'phase_result': asdict(raw)})
    finally:
        if agent and hasattr(agent, 'close'):
            agent.close()


def retained_point(path, scope, role):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('scope') != scope or data.get('role') != role:
        raise ValueError('A nested checkpoint differs from the retained role or scope.')
    if data.get('payload_hash') != digest(data.get('payload')) or data.get('checkpoint_hash') != digest(
            {key: value for key, value in data.items() if key != 'checkpoint_hash'}):
        raise ValueError('A nested checkpoint changed; retained work cannot be trusted.')
    if data.get('code_versions') != source_versions():
        raise ValueError('The implementation changed since this workflow checkpoint; an explicit migration is required.')
    return data


def restore_agent(agent, state, points, workflow_state, resume_pending=True):
    for key in ('reusable_blocks', 'draft_blocks', 'draft_texts', 'draft_question', 'sentiment_reports', 'sentiment_counter', 'numeric_requested', 'presentation_fallback_used'):
        if key in state:
            setattr(agent, key, state[key])
    if hasattr(agent, 'metric_cache'):
        agent.metric_cache = {tuple(item['key']): item['result'] for item in state.get('metric_cache', [])}
        agent.metric_errors = {tuple(key) for key in state.get('metric_errors', [])}
        agent.required_metrics = state.get('required_metrics', [])
        agent.reader.counter = state.get('reader_counter', 0)
    point = points.get(agent.name + ':specialist')
    if point and (agent.name != 'Original' or workflow_state.get('phase') == 'coordination'):
        if agent.name != 'Original' or point.get('attempt') == workflow_state.get('attempt', 0):
            saved = retained_point(point['path'], agent.scope.__dict__, agent.name)
            payload = {**saved['payload'], **saved['progress'].get('continuation', {})}
            if ('continuation' not in saved['progress'] and not payload.get('pending_turn') and
                    saved['progress'].get('last_model_output')):
                turn = saved['progress']['last_model_output']
                payload['pending_turn'] = turn
                payload['history'] = [*payload['history'], *turn.get('output_items', [])]
            if resume_pending and saved['progress'].get('status') == 'completed' and saved['progress'].get('result'):
                agent.resume_completed_result = saved['progress']['result']
            elif resume_pending:
                agent.resume_state = payload
            agent.reusable_blocks = saved['progress'].get('reusable_blocks', payload.get('reusable_blocks', agent.reusable_blocks))
            agent.draft_blocks = saved['progress'].get('draft_blocks', payload.get('draft_blocks', agent.draft_blocks))
            agent.draft_texts.update(saved['progress'].get('draft_texts', payload.get('draft_texts', {})))
            agent.draft_question = payload.get('draft_question', payload.get('question'))
            if hasattr(agent, 'metric_cache'):
                agent.metric_cache.update({tuple(item['key']): item['result'] for item in payload.get('metric_cache', [])})
                agent.metric_errors = {tuple(key) for key in payload.get('metric_errors', [])}
                agent.reader.counter = max(agent.reader.counter, payload.get('reader_counter', 0))
            if agent.name == 'Vanilla':
                agent.sentiment_reports.update(payload.get('sentiment_reports', {}))
                state = {**state, 'sentiment_progress': payload.get('sentiment_progress', state.get('sentiment_progress', {}))}
    if agent.name == 'Vanilla':
        progress = list(state.get('sentiment_progress', {}).values())
        point = points.get('Vanilla:sentiment')
        if point:
            saved = retained_point(point['path'], agent.scope.__dict__, 'Vanilla')
            agent.sentiment_reports.update(saved['progress'].get('sentiment_reports', {}))
            value = saved['progress'].get('sentiment_state', saved['payload']['state'])
            progress = [item for item in progress if (item['dimension'], item['ids']) != (value['dimension'], value['ids'])]
            progress.append(value)
        for item in progress:
            # Explicit continuation opens a new delivery window only for pending records.
            item['attempts'] = {}
        agent.retained_sentiment_progress = progress
        agent.sentiment_counter = max([int(key[9:]) for key in agent.sentiment_reports if re.fullmatch(r'SENTIMENT\d+', key)] or [0])


def resume_workflow(saved, registry, database, model_limit=32, seconds=300):
    """Restore the coordinator stack, then continue the exact unfinished phase."""
    payload, progress = saved['payload'], saved['progress']
    if payload.get('mode') != 'live' or saved.get('code_versions') != source_versions():
        raise ValueError('Full continuation requires matching live workflow code; old phase-only checkpoints need an explicit migration.')
    if payload.get('database_hash') != database_identity(database):
        raise ValueError('The source database changed; the retained workflow cannot be silently reused.')
    current = registry.describe()
    fields = ('profile', 'provider', 'api', 'endpoint', 'model', 'max_output_tokens', 'timeout_seconds',
              'max_retries', 'request_interval_seconds', 'rate_limit_retries', 'reasoning_effort', 'clear_thinking')
    for role, previous in payload.get('connections', {}).items():
        if role not in current or any(current[role].get(key) != previous.get(key) for key in fields):
            raise ValueError('Full continuation must preserve every role model and transport configuration.')
    state = progress.get('state', {})
    if not state:
        raise ValueError('This workflow has no saved coordinator state.')
    scope = AccessScope(**saved['scope'])
    retrieval = payload.get('retrieval', 'lexical')
    embedding = registry.embeddings(payload.get('embedding_profile')) if retrieval != 'lexical' else None
    agent = OriginalAgent(database, scope, registry.get, 'live', retrieval=retrieval,
                          embedding_model=embedding,
                          cache_root=Path(payload['cache_root']) if payload.get('cache_root') else Path(database).parent / 'rag_cache',
                          connections=current, model_call_limit=model_limit, run_seconds=seconds)
    try:
        prior = progress['budget']
        spent = payload['run_seconds'] - prior['remaining_seconds']
        remaining = seconds - spent
        if remaining <= 0 or prior['models'] >= model_limit:
            raise ValueError('The retained workflow budget is exhausted; explicitly increase its limits to continue.')
        agent.budget = RunBudget(model_limit=model_limit, tool_limit=48 + 2 * max(0, model_limit - 32), seconds=remaining)
        agent.budget.models, agent.budget.tools = prior['models'], prior['tools']
        agent.budget.embeddings = prior.get('embeddings', 0)
        agent.original_request = payload['question']
        agent.workflow_state, agent.resume_workflow_state = state, state
        agent.planning_history, agent.planning_diagnostics = progress.get('planning_history', []), []
        agent.child_results = progress.get('child_results', [])
        agent.reviewed_candidate = progress.get('reviewed_candidate')
        agent.attempt_reviews = progress.get('attempt_reviews', [])
        agent.review_history = progress.get('review_history', [])
        agent.planned_metrics = progress.get('planned_metrics', [])
        agent.prepared_metrics = {tuple(item['key']): item['result'] for item in progress.get('prepared_metrics', [])}
        agent.declined_requests = {tuple(item['key']): item['result'] for item in progress.get('declined_requests', [])}
        agent.last_result, agent.last_verdict = None, None
        if agent.attempt_reviews:
            from .zero_sugar import VerificationResult
            agent.last_verdict = VerificationResult(**agent.attempt_reviews[-1])
        agent.drafts = state.get('candidates', [])
        agent.coordinator_diagnostics, agent.verification_diagnostics = {}, {}
        agent.active_stage = state.get('phase', 'planning')
        agent.active_reviewer, agent.challenge_result = None, None
        agent.challenge_result = progress.get('challenge_result')
        agent.challenged_candidates = set(progress.get('challenged_candidates', []))
        agent.restored_delegations = progress.get('allowed_delegations', ['Cherry', 'Vanilla'])
        points = progress.get('phase_points', {})
        planning_point = points.get('Original:planning')
        if not state.get('plan') and planning_point:
            planning = retained_point(planning_point['path'], saved['scope'], 'Original')
            if planning['progress'].get('status') == 'completed' and planning['progress'].get('result'):
                state['plan'] = planning['progress']['result']
        restore_agent(agent, progress.get('coordinator', {}), points, state)
        pending_children = {}
        for call in ((getattr(agent, 'resume_state', None) or {}).get('pending_turn') or {}).get('calls', []):
            if call.get('name') in {'ask_cherry', 'ask_vanilla'}:
                pending_children[{'ask_cherry': 'Cherry', 'ask_vanilla': 'Vanilla'}[call['name']]] = json.loads(call['arguments']).get('question')
        child_names = set(progress.get('children', {})) | {key.split(':')[0] for key in points if key.startswith(('Vanilla:', 'Cherry:'))}
        for name in child_names:
            child = agent.specialist(name)
            child_point = points.get(name + ':specialist')
            child_saved = retained_point(child_point['path'], saved['scope'], name) if child_point else None
            pending_same_request = name in pending_children and child_saved and child_saved['payload'].get('question') == pending_children[name]
            restore_agent(child, progress.get('children', {}).get(name, {}), points, state, bool(pending_same_request))
            if child_point:
                completed = child_saved['progress'].get('result')
                if completed and name not in pending_children and not any(
                        previous.get('agent') == name and previous.get('question') == completed['question'] and
                        previous.get('answer') == completed['answer'] for previous in agent.child_results):
                    completed['sentiment'] = getattr(child, 'sentiment_reports', {})
                    agent.child_results.append(completed)
        visual_point = points.get('Lime:visual')
        if state.get('phase') == 'chart_planning' and visual_point and visual_point.get('attempt') == state.get('attempt', 0):
            visual = retained_point(visual_point['path'], saved['scope'], 'Lime')
            candidate = state.get('candidate', {})
            if visual['payload'].get('answer') != candidate.get('answer') or visual['payload'].get('evidence') != candidate.get('evidence'):
                raise ValueError('The retained chart plan belongs to a different candidate.')
            if visual['progress'].get('status') == 'completed' and visual['progress'].get('result'):
                candidate['visualization'] = visual['progress']['result']
                state['prior_visuals'] = visual['progress']['result']
                state['phase'], state['chart_failure'] = 'verification', None
        review_point = points.get('ZeroSugar:review')
        if (state.get('phase') == 'verification' and review_point and
                review_point.get('attempt') == state.get('attempt', 0) and review_point.get('phase') == 'verification'):
            review_saved = retained_point(review_point['path'], saved['scope'], 'ZeroSugar')
            retained_candidate = state.get('candidate', {})
            if (review_saved['payload'].get('answer') != retained_candidate.get('answer') or
                    review_saved['payload'].get('evidence') != retained_candidate.get('evidence') or
                    review_saved['payload'].get('question') != payload['question']):
                raise ValueError('The retained review does not belong to the interrupted candidate.')
            if review_saved['progress'].get('status') == 'completed' and review_saved['progress'].get('result'):
                state['phase'], state['verdict'] = 'reviewed', review_saved['progress']['result']
            else:
                agent.resume_review_progress = review_saved['progress']
        elif state.get('phase') == 'coordination' and review_point and review_point.get('phase') == 'coordination':
            agent.resume_challenge_review_progress = retained_point(review_point['path'], saved['scope'], 'ZeroSugar')['progress']
        agent.workflow_checkpoint = checkpoint('workflow', 'Original', saved['scope'], {
            **payload, 'model_call_limit': model_limit, 'run_seconds': seconds,
            'parent_run_id': saved['run_id'], 'source_checkpoint': saved['source_path']})
        checkpoint_progress(agent.workflow_checkpoint, **{**progress, 'status': 'started'})
        trace('workflow_resume', parent_run_id=saved['run_id'], source_checkpoint=saved['source_path'],
              phase=state.get('phase'), prior_used_models=prior['models'], remaining_seconds=remaining)
        return agent.run(payload['question'])
    finally:
        agent.close()
