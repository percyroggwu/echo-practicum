"""Export fixed inputs or score explicitly annotated reviews; no API calls."""

import argparse
import json
from pathlib import Path
from review_cases import cases, score, VERSION, corpus_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--judgments', type=Path, help='JSON with reviewer_id, annotation_method and judgments covering all cases.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.judgments:
        data = json.loads(args.judgments.read_text(encoding='utf-8-sig'))
        if not data.get('reviewer_id') or not data.get('annotation_method') or data.get('corpus_hash') != corpus_identity():
            raise ValueError('Record reviewer identity, annotation method and exact corpus hash.')
        result = {**score(data['judgments']), 'reviewer_id': data['reviewer_id'], 'annotation_method': data['annotation_method']}
    else:
        result = {'version': VERSION, 'corpus_hash': corpus_identity(), 'cases': cases(),
            'model_evaluated': False, 'annotation_origin': 'Agent-authored controlled fixtures, not an independent human benchmark.',
            'acceptance': {'false_positives': 0, 'false_negatives': 0}, 'baseline': None}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'output': str(args.output), 'case_count': len(cases()), 'model_evaluated': bool(args.judgments)}))


if __name__ == '__main__':
    main()
