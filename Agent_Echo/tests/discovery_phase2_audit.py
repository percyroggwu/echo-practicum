"""Read-only offline all-team acceptance measurement; private expectations stay here."""
import csv
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def offline(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)) and Path(args[0]).name in ('.env', 'connections.private.json'):
        raise PermissionError('Credentials forbidden in offline evaluation')
    if event in ('socket.connect', 'socket.getaddrinfo'):
        raise RuntimeError('Network forbidden in offline evaluation')


sys.addaudithook(offline)
from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import prefilter, resolve_subject, selection_audit, team_summary


def split(value):
    return [v.strip() for v in re.split(r'[;|]', value or '') if v.strip()]


def token_count(text):
    # tiktoken can download missing vocabularies. Never invoke it without a cache.
    import importlib.util
    import os
    import tempfile
    import hashlib
    cache = Path(os.environ.get('TIKTOKEN_CACHE_DIR') or Path(tempfile.gettempdir()) / 'data-gym-cache')
    vocabulary = hashlib.sha1(b'https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken').hexdigest()
    if importlib.util.find_spec('tiktoken') and (cache / vocabulary).is_file():
        try:
            import tiktoken
            return len(tiktoken.get_encoding('o200k_base').encode(text)), 'offline_cached_o200k_base'
        except Exception:
            pass
    return (len(text) + 3) // 4, 'estimate_chars_divided_by_4; cached provider tokenizer unavailable'


def main():
    import argparse
    from collections import Counter
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--managers', nargs='+')
    parser.add_argument('--key-summary', action='store_true')
    options = parser.parse_args()
    with (ROOT.parent / 'files_discovery_v1_private' / 'QA_discovery_v1_answer_key.csv').open(encoding='utf-8-sig', newline='') as stream:
        cases = list(csv.DictReader(stream))
    if options.key_summary:
        print(json.dumps(dict(Counter(f"{c['Origin']}:{c['Kind']}" for c in cases))))
        return 0
    db = ROOT / 'data' / 'echo_discovery_v1.db'
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as source:
        managers = [r[0] for r in source.execute('SELECT Manager_ID FROM HR_managers ORDER BY Manager_ID')]
        all_people = list(source.execute('SELECT Employee_ID,Employee_Name FROM HR_employees'))
        manager_names = list(source.execute('SELECT Manager_ID,Manager_Name FROM HR_managers'))
    if options.managers:
        managers = [m for m in managers if m in options.managers]
    totals = Counter(teams=0, summary_positive_people=0, summary_positive_reached=0,
                     automatic_positive_cases=0, automatic_positive_reached=0, automatic_decoy_cases=0,
                     automatic_code_slot=0, automatic_selection_slot=0,
                     handbuilt_positive_people=0, handbuilt_positive_reached=0,
                     privacy=0, inactive=0, caps=0, dates=0, small_team_pool=0,
                     summary_order=0, summary_forbidden=0, beneficiary_missing=0)
    small, demos, source_recall = [], {}, {'positive': {}, 'decoy': {}}
    began = time.monotonic()
    for manager in managers:
        data = DiscoveryData(db, DiscoveryScope(manager, '2025-10-01', '2026-06-30'))
        try:
            resolution = resolve_subject(data, {'subject_kind': 'team'})
            summary = team_summary(data)
            lines = {line['employee_id']: line for line in summary['lines']}
            code = set(summary['lowest']) | set(summary['whole_team'])
            roster = {r['Employee_ID'] for r in data.roster()}
            totals['teams'] += 1
            totals['summary_order'] += list(lines) != sorted(lines)
            encoded_summary = json.dumps(summary['lines'], ensure_ascii=False)
            totals['summary_forbidden'] += any(word in encoded_summary.lower() for word in
                ('pulse_score', 'satisfaction', 'weight', 'strength', 'source_text'))
            external = [(e,n) for e,n in all_people if e not in roster]
            external += [(m,n) for m,n in manager_names if m != manager]
            def privacy(encoded):
                return sum(bool(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', encoded))
                           for _,name in external if name) + len(set(re.findall(r'(?<!\w)E\d{4}(?!\w)', encoded)) - roster)
            totals['privacy'] += privacy(encoded_summary)
            def choices(required):
                chosen = sorted(set(required) - code)
                chosen += [e for e in lines if e not in chosen][:max(0, summary['selection_count'] - len(chosen))]
                if len(chosen) > summary['selection_count']:
                    raise AssertionError('Conditional fixture cannot exceed the approved selection cap')
                return chosen if summary['selection_count'] else None
            def pool_for(required=()):
                pool = prefilter(data, resolution, selected_employee_ids=choices(required))
                people = {p['employee_id'] for p in pool['people']}
                totals['inactive'] += len(people - roster)
                totals['caps'] += int(len(people)>10) + sum(len(p['items'])>8 for p in pool['people'])
                totals['dates'] += sum(not('2025-10-01'<=i['event_date'][:10]<='2026-06-30' and i['recorded_date'][:10]<='2026-06-30') for p in pool['people'] for i in p['items'])
                totals['privacy'] += privacy(json.dumps(pool,ensure_ascii=False))
                return pool
            baseline = pool_for()
            if len(roster)<=10:
                small.append(manager)
                totals['small_team_pool'] += {p['employee_id'] for p in baseline['people']} != roster
            rows = [r for values in data.evidence().values() for r in values]
            by_id = {r['record_id']:r for r in rows if r.get('record_id')}
            local_cases = [c for c in cases if c['Manager_ID']==manager]
            # P5's other authorized home teams are evaluated by the same conditional rule.
            extra = {'M46':['E0046'], 'M31':['E0051','E0066'], 'M01':['E0074','E0085']}.get(manager, [])
            for employee in extra:
                totals['handbuilt_positive_people'] += 1
                pool = pool_for([employee])
                items = [i for p in pool['people'] if p['employee_id']==employee for i in p['items']]
                totals['handbuilt_positive_reached'] += bool(items and any(i['source']=='HR_self_review_items' for i in items))
            for case in local_cases:
                positive = case['Kind']=='case'
                employees = set(split(case['Employee_IDs'])) & roster
                expected = set(split(case['Evidence_IDs']))
                # Known later records are excluded; unknown IDs stay in the denominator.
                expected = {e for e in expected if e not in by_id or
                    ('2025-10-01' <= by_id[e].get('event_date','')[:10] <= '2026-06-30' and by_id[e].get('recorded_date','')[:10] <= '2026-06-30')}
                if case['Origin']=='automatic':
                    totals['automatic_positive_cases' if positive else 'automatic_decoy_cases'] += 1
                    if positive:
                        totals['automatic_code_slot'] += bool(employees <= code)
                        totals['automatic_selection_slot'] += not employees <= code
                if positive:
                    for employee in employees-code:
                        totals['summary_positive_people'] += 1
                        totals['summary_positive_reached'] += employee in lines
                        targets = {by_id[e].get('beneficiary_manager_id') for e in expected if e in by_id
                                   and employee in by_id[e].get('employee_ids',[])} - {None,manager}
                        facts = {b['manager_id'] for b in lines.get(employee,{}).get('beneficiaries',[]) if b['help_records']>0}
                        totals['beneficiary_missing'] += bool(targets and not targets & facts)
                # One fixture per subject avoids turning six M32 positives into six model slots.
                reached_case = False
                for employee in employees:
                    pool = pool_for([employee])
                    records = {i['record_id'] for p in pool['people'] if p['employee_id']==employee for i in p['items']}
                    reached = bool(records & expected)
                    reached_case |= reached
                    if positive and case['Origin']=='hand_built':
                        totals['handbuilt_positive_people'] += 1
                        totals['handbuilt_positive_reached'] += reached
                    for source_id in expected:
                        source = by_id.get(source_id,{}).get('source','unavailable_or_unknown')
                        counts = source_recall['positive' if positive else 'decoy'].setdefault(source,{'expected':0,'reached':0})
                        counts['expected'] += 1
                        counts['reached'] += source_id in records
                if positive and case['Origin']=='automatic':
                    totals['automatic_positive_reached'] += reached_case
            if manager in ('M32','M14'):
                # Measure what the model receives: the compact summary table and the judgment people.
                from agents.discovery import DiscoveryAgent, judgment_people, summary_table
                prompt_pool = pool_for([e for e in lines][:summary['selection_count']])
                teams = DiscoveryAgent(data, None, None)._team_names(prompt_pool)
                encoded = json.dumps({'people': judgment_people(prompt_pool, teams), 'beneficiary_teams': teams,
                                      'team_pattern_leads': prompt_pool['team_pattern_leads']}, ensure_ascii=False)
                pool_tokens, method = token_count(encoded)
                summary_tokens, summary_method = token_count(summary_table(summary['lines']))
                demos[manager] = {'code_slot':summary['lowest'], 'pool_size':len(prompt_pool['people']),
                    'pool_characters':len(encoded),'pool_tokens':pool_tokens,'pool_token_method':method,
                    'summary_lines':len(lines),'summary_characters':len(summary_table(summary['lines'])),
                    'summary_tokens':summary_tokens,'summary_token_method':summary_method}
                if manager=='M32':
                    focus = resolve_subject(data,{'subject_kind':'team','focus_hint':'M16'})
                    fs = team_summary(data,focus_hint=focus['focus_hint'])
                    fids = {x['employee_id'] for x in fs['lines']}
                    required = {'E1401','E1586','E0561'}
                    demos[manager]['focus_summary_pass'] = required <= fids and all(any(b['manager_id']=='M16' and b['help_records']>0 for b in x['beneficiaries']) for x in fs['lines'] if x['employee_id'] in required)
                    fp = prefilter(data,focus,selected_employee_ids=[x['employee_id'] for x in fs['lines']][:10] if fs['selection_count'] else None)
                    demos[manager]['focus_pool_pass'] = fs['selection_count']>0 or required <= {p['employee_id'] for p in fp['people']}
                    demos[manager]['focus_selection_count'] = fs['selection_count']
                    demos[manager]['p6_mentions'] = sum(b['other_text_mentions'] for b in lines['E0970']['beneficiaries'])
                else:
                    demos[manager]['p5_self_review'] = lines['E0001']['self_review_cross_team'] + lines['E0001']['self_review_unmatched_initiative']
            print(f'{manager}: audited ({totals["teams"]}/60)',flush=True)
        finally:
            data.close()
    expected_slots = {'M32':['E2198','E0010','E1748','E2156','E1401'], 'M14':['E1183','E1209','E0450','E0885','E1088']}
    gates = {'all_60_teams':totals['teams']==60,
        'automatic_populations':totals['automatic_positive_cases']==120 and totals['automatic_decoy_cases']==60,
        'current_code_selection_split':totals['automatic_code_slot']==47 and totals['automatic_selection_slot']==73,
        'exact_satisfaction':all(demos.get(m,{}).get('code_slot')==ids for m,ids in expected_slots.items()),
        'small_whole_teams':small==['M41','M42','M49','M58','M59'] and not totals['small_team_pool'],
        'summary_positive_recall':totals['summary_positive_reached']==totals['summary_positive_people'] and not totals['beneficiary_missing'],
        'handbuilt_conditional_prefilter':totals['handbuilt_positive_reached']==totals['handbuilt_positive_people'],
        'automatic_conditional_prefilter':totals['automatic_positive_reached']>=.95*totals['automatic_positive_cases'],
        'distinctive_facts':demos.get('M32',{}).get('p6_mentions',0)>0 and demos.get('M14',{}).get('p5_self_review',0)>0,
        'focus':demos.get('M32',{}).get('focus_summary_pass',False) and demos.get('M32',{}).get('focus_pool_pass',False),
        'privacy_scope_caps_dates_order':not any(totals[k] for k in ('privacy','inactive','caps','dates','summary_order','summary_forbidden'))}
    report = {'rules_version':'discovery-5plus5-offline-audit-v2','elapsed_seconds':round(time.monotonic()-began,2),
        'totals':dict(totals),'gates':gates,'gate_counts':{'pass':sum(gates.values()),'fail':sum(not v for v in gates.values())},
        'demos':demos,'small_whole_team_manager_ids':small,'source_evidence_recall':source_recall,
        'selection_quality':'Not measured: conditional recorded selections test evidence retention only.',
        'm32_limit':'Six positive model-only candidates compete for five slots; separate conditional fixtures do not imply one-run complete recall.',
        'acceptance_pass':all(gates.values())}
    (ROOT/'data'/'discovery_phase2_metrics.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'totals':dict(totals),'gates':gates,'acceptance_pass':report['acceptance_pass']}))
    return 0 if report['acceptance_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
