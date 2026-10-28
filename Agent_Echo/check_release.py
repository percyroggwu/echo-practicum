"""Offline release gate. Run with the project interpreter; --quick is a pre-live subset."""

import argparse
import compileall
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def schema_smoke():
    from agents.content import excerpt_catalog, live_answer_schema, resolve_answer
    from agents.grounding import FactCatalog, answer_schema, render_answer

    scope = {'manager_id': 'M14', 'start_date': '2026-07-01', 'end_date': '2026-09-30'}
    evidence = [{'citation_id': 'survey:CHECK', 'text': 'A scoped excerpt.', 'scope': scope}]
    excerpts = excerpt_catalog(evidence)
    for role in ('Original', 'Cherry', 'Vanilla'):
        schema = live_answer_schema(answer_schema(role), excerpts)
        assert set(schema) == {'fact_ids', 'interpretations', 'proposals', 'reuse_ids', 'remove_ids'}
        for kind in ('interpretations', 'proposals'):
            assert 'quote_ref' in schema[kind]['items']['properties']
            assert 'quote' not in schema[kind]['items']['properties']
        payload = {'fact_ids': [], 'interpretations': [], 'proposals': [], 'reuse_ids': [], 'remove_ids': []}
        if role != 'Cherry':
            payload['interpretations'] = [{'text': 'The source offers a perspective.',
                'citation_ids': ['survey:CHECK'], 'quote_ref': next(iter(excerpts))}]
        resolved = resolve_answer(payload, evidence, scope, {}, {})
        render_answer(resolved, FactCatalog(evidence, scope), role)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args(argv)
    if not compileall.compile_dir(str(HERE / 'agents'), quiet=1):
        return 1
    if not all(compileall.compile_file(str(path), quiet=1) for path in HERE.glob('*.py')):
        return 1
    schema_smoke()
    command = [sys.executable, '-B', '-m', 'unittest']
    if args.quick:
        command += ['discover', '-s', 'tests', '-p', 'test_capture_resume.py']
    else:
        command += ['discover', '-s', 'tests']
    return subprocess.run(command, cwd=HERE).returncode


if __name__ == '__main__':
    raise SystemExit(main())
