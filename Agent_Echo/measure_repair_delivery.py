"""Offline four-draft delivery measurement from immutable local review snapshots.

No provider client, retrieval or live model is constructed. Selections are scripted
historical candidates, not new reasoning. Source text stays in the local input only.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from agents.capture import digest, source_versions
from agents.content import excerpt_catalog
from agents.data_access import AccessScope
from agents.delivery_diagnostics import request_size
from agents.model import ModelTurn, ToolCall
from agents.original import INSTRUCTIONS
from agents.runtime import Specialist, RunBudget


class MeasurementModel:
    profile = 'offline-scripted-repair'

    def __init__(self):
        self.selection = None
        self.measurements = []
        self.prior_answer = None

    def respond(self, instructions, history, tools, require_tool=False):
        sizes = request_size(instructions, history, tools)
        duplicated = deepcopy(history)
        if self.prior_answer:
            duplicated.insert(1, {'role': 'assistant', 'content': self.prior_answer})
        projection = request_size(instructions, duplicated, tools)
        self.measurements.append({'sections': sizes, 'with_duplicate_answer_projection': projection,
            'request_characters': sum(value['characters'] for value in sizes.values()),
            'provider_input_tokens': None, 'provider_output_tokens': None,
            'token_target': 15000, 'token_target_verified': False})
        call = ToolCall('scripted-delivery', 'submit_grounded_answer', json.dumps(self.selection))
        return ModelTurn(calls=[call], output_items=[{'type': 'function_call', 'call_id': call.call_id,
            'name': call.name, 'arguments': call.arguments}])


def measure(artifact):
    artifact = Path(artifact).resolve()
    saved = json.loads(artifact.read_text(encoding='utf-8'))
    reviews = []
    for path in saved['capture']['checkpoints']:
        point = json.loads(Path(path).read_text(encoding='utf-8'))
        if point['kind'] != 'review':
            continue
        if point['scope'] != saved['scope'] or point['code_versions'] != saved['capture']['code_versions']:
            raise ValueError('Review snapshot scope/source implementation identity differs from the parent artifact.')
        if point['payload_hash'] != digest(point['payload']) or point['checkpoint_hash'] != digest({k: v for k, v in point.items() if k != 'checkpoint_hash'}):
            raise ValueError('The historical review snapshot changed.')
        reviews.append(point)
    if len(reviews) != 4:
        raise ValueError('Select a historical artifact with exactly four saved review drafts.')
    model = MeasurementModel()
    scope = AccessScope(**saved['scope'])
    # Exercise the actual source-bound live delivery path with an in-process scripted
    # model. No ConnectionRegistry or provider client exists in this program.
    agent = Specialist('Original', INSTRUCTIONS, model, scope, [], {}, 'live')
    agent.source_grounding = True
    agent.budget = RunBudget(model_limit=32, seconds=1000)
    results = []
    for index, point in enumerate(reviews, 1):
        payload = point['payload']
        selection = deepcopy(payload['arguments']['grounding']['payload'])
        excerpts = excerpt_catalog(payload['evidence'])
        for kind in ('interpretations', 'proposals'):
            for item in selection[kind]:
                quote = item.pop('quote')
                item['quote_ref'] = None if quote is None else next(key for key, value in excerpts.items()
                    if value['source_id'] in item['citation_ids'] and value['text'] == quote)
        selection.update(reuse_ids=[], remove_ids=list(agent.draft_blocks), removal_reasons=[
            {'block_id': key, 'reason': 'Controlled historical candidate replacement for offline measurement only.'}
            for key in agent.draft_blocks])
        model.selection = selection
        agent.repair_round = index
        context = [{'role': 'user', 'content': json.dumps({'pending_corrections': payload['arguments'].get('previous_corrections', [])})}]
        result = agent.run(payload['question'], payload['evidence'], context)
        model.measurements[-1]['draft'] = index
        results.append({'draft': index, 'claim_count': len(result.claims),
            'removed_quotes': sum(item['removed_quotes'] for item in result.diagnostics.get('answer_edits', []))})
        model.prior_answer = result.answer
    return {'kind': 'offline-four-draft-delivery', 'parent_artifact': str(artifact),
        'parent_run_id': saved['capture']['run_id'], 'source_versions': source_versions(),
        'provider_calls': 0, 'semantic_quality_measured': False,
        'comparison': 'Controlled projection adding one duplicate prior answer to the same current request. Not an exact old-code execution or provider token measurement.',
        'measurements': model.measurements, 'drafts': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.artifact)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print('Recorded four offline drafts; provider calls: 0. The token target remains unverified.')


if __name__ == '__main__':
    main()
