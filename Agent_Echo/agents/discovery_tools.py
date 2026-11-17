from datetime import date, timedelta
from difflib import get_close_matches
import re
import unicodedata


def _key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold()) if not unicodedata.combining(c)).strip()


def _period(scope, hint):
    start, end = date.fromisoformat(scope.start_date), date.fromisoformat(scope.end_date)
    requested_start, requested_end = start, end
    text = _key(hint)
    if text:
        quarter = re.fullmatch(r'(?:this|current|last|previous) quarter', text)
        q = re.fullmatch(r'(?:([12]\d{3})[- ]?q([1-4])|q([1-4])\s+([12]\d{3}))', text)
        since = re.fullmatch(r'since\s+(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+([12]\d{3}))?', text)
        dates = re.fullmatch(r'([12]\d{3}-\d\d-\d\d)\s*(?:to|through|–|—)\s*([12]\d{3}-\d\d-\d\d)', text)
        try:
            if quarter or q:
                if q:
                    year, month = (int(q[1]), 3 * int(q[2]) - 2) if q[1] else (int(q[4]), 3 * int(q[3]) - 2)
                else:
                    year, month = end.year, 3 * ((end.month - 1) // 3) + 1
                    if text.startswith(('last', 'previous')):
                        month -= 3
                        if month < 1:
                            year, month = year - 1, month + 12
                requested_start = date(year, month, 1)
                requested_end = date(year + (month == 10), (month + 2) % 12 + 1, 1) - timedelta(days=1)
            elif since:
                months = 'january february march april may june july august september october november december'.split()
                requested_start = date(int(since[2] or end.year), months.index(since[1]) + 1, 1)
            elif dates:
                requested_start, requested_end = map(date.fromisoformat, dates.groups())
            else:
                return None
        except ValueError:
            return None
    actual_start, actual_end = max(start, requested_start), min(end, requested_end)
    if actual_start > actual_end:
        return False
    return {'start': actual_start.isoformat(), 'end': actual_end.isoformat(), 'as_of': end.isoformat(),
            'narrowed_from_hint': actual_start != requested_start or actual_end != requested_end}


def _clarify(name, people, message=None):
    return {'status': 'clarification', 'missing_field': 'subject', 'request_excerpt': name,
            'message': message or 'Please clarify who you mean.',
            'clarification_candidates': [{'employee_id': p['Employee_ID'], 'name': p['Employee_Name'],
                                          'team': p['Team_Display_Name'], 'manager_id': p.get('Pilot_Manager_ID')} for p in people]}


def resolve_subject(data, plan, clarification=None):
    """Resolve a plan against the authorized roster without reading evidence."""
    roster = data.roster()
    by_id = {p['Employee_ID']: p for p in roster}
    manager_id = data.scope.manager_id
    team = data.manager['Primary_Team']
    names = plan.get('subject_names') or []
    if isinstance(names, str):
        names = [names]
    names = [n for n in names if n and str(n).strip()]
    kind = plan.get('subject_kind') or 'team'
    def declined(detail):
        # detail is the name as the manager wrote it; it never comes from the roster.
        return {'status': 'declined', 'reason_code': 'subject_out_of_scope',
                'message': "Echo answers only about your own team.", 'detail': detail}
    if kind == 'other_team':
        return declined(', '.join(map(str, names)) or 'another team')
    choice = (clarification or {}).get('employee_id')
    if choice and choice not in by_id:
        return declined('the selected person')
    if len(names) > 5:
        return _clarify('', [], 'Please ask about the whole team or up to five people.')
    selected, pending = [], []
    for name in names:
        if choice and len(names) == 1 and kind in ('person', 'people'):
            selected.append(choice)
            continue
        teams = data.resolve_team(name)
        if teams:
            if len(teams) > 1:
                return {'status': 'clarification', 'missing_field': 'subject', 'request_excerpt': name,
                        'message': 'Please identify the team by manager ID.', 'team_candidates': teams}
            if not teams[0]['own_team']:
                return declined(name)
            continue
        result = data.resolve_person(name)
        matches = result['own_matches']
        if not matches:
            key = _key(name)
            matches = [p for p in roster if _key(p['Employee_Name']).split(' ')[0] == key]
        if result['outside_match'] and not matches:
            return declined(name)
        if len(matches) == 1:
            selected.append(matches[0]['Employee_ID'])
        else:
            pending.append((name, matches))
    if choice and len(names) > 1:
        ambiguous = [i for i, (_, matches) in enumerate(pending) if len(matches) > 1 and choice in {p['Employee_ID'] for p in matches}]
        if len(ambiguous) == 1:
            selected.append(choice)
            pending.pop(ambiguous[0])
    if pending:
        name, matches = pending[0]
        if not matches:
            lookup = {_key(p['Employee_Name']): p for p in roster}
            matches = [lookup[k] for k in get_close_matches(_key(name), lookup, n=5, cutoff=0.55)]
        return _clarify(name, matches)
    if choice and not names and kind in ('person', 'people'):
        selected.append(choice)
    if kind in ('person', 'people') and not selected:
        return _clarify('', [])
    period = _period(data.scope, plan.get('period_hint'))
    if period is False:
        return {'status': 'clarification', 'missing_field': 'period', 'message': 'That period is outside the authorized dates.'}
    if period is None:
        return {'status': 'clarification', 'missing_field': 'period', 'message': 'Please clarify the requested period.'}
    selected = list(dict.fromkeys(selected))
    subject = {'kind': 'person' if len(selected) == 1 else 'people' if selected else 'team',
               'employee_ids': selected if selected else [p['Employee_ID'] for p in roster],
               'manager_id': manager_id, 'team': team}
    output = {'status': 'process', 'subject': subject, 'period': period}
    focus = plan.get('focus_hint')
    if focus:
        value = focus.get('manager_id') or focus.get('team') if isinstance(focus, dict) else focus
        candidates = data.resolve_team(value)
        if len(candidates) != 1:
            return {'status': 'clarification', 'missing_field': 'focus_hint', 'request_excerpt': str(value),
                    'message': 'Please identify the beneficiary team by manager ID.', 'team_candidates': candidates}
        output['focus_hint'] = {'manager_id': candidates[0]['manager_id'], 'team': candidates[0]['team']}
    return output


def lowest_satisfaction(data, n=5):
    """Return internal selection records using the latest visible quarterly pulse."""
    own = {person['Employee_ID'] for person in data.roster()}
    start, end = data.scope.start_date, data.scope.end_date
    quarters = {}
    for row in data.evidence().get('HR_employee_performance', []):
        employee = row.get('Employee_ID')
        quarter = row.get('Quarter')
        recorded_at = row.get('recorded_date') or row.get('Recorded_At') or ''
        recorded = recorded_at[:10]
        event = (row.get('event_date') or recorded)[:10]
        if (employee not in own or not recorded or not event or
                not start <= recorded <= end or not start <= event <= end or
                not re.fullmatch(r'\d{4}-Q[1-4]', str(quarter or '')) or
                quarter > f"{end[:4]}-Q{(int(end[5:7]) - 1) // 3 + 1}" or
                row.get('Pulse_Score') is None):
            continue
        key = (employee, quarter)
        rank = (recorded_at, str(row.get('record_id') or row.get('Performance_ID') or ''))
        if key not in quarters or rank > quarters[key][0]:
            quarters[key] = (rank, row)
    result = []
    for employee in own:
        available = [quarter for person, quarter in quarters if person == employee]
        if not available:
            continue
        quarter = max(available)
        year, number = int(quarter[:4]), int(quarter[-1])
        previous_quarter = f'{year - 1}-Q4' if number == 1 else f'{year}-Q{number - 1}'
        row = quarters[(employee, quarter)][1]
        prior = quarters.get((employee, previous_quarter))
        score = row['Pulse_Score']
        previous = prior[1]['Pulse_Score'] if prior else None
        result.append({'employee_id': employee, 'pulse_score': score, 'previous_score': previous,
                       'change': score - previous if previous is not None else None, 'quarter': quarter})
    # Unknown changes sort after known changes for equal scores; they are never inferred.
    result.sort(key=lambda item: (item['pulse_score'], item['change'] is None,
                                  item['change'] if item['change'] is not None else 0,
                                  item['employee_id']))
    return result[:max(0, n)]


SIGNAL_RULES_VERSION = 'discovery-signals-v1'


def _signal_window(data, period=None):
    period = period or {}
    return (max(data.scope.start_date, period.get('start', data.scope.start_date)),
            min(data.scope.end_date, period.get('end', data.scope.end_date)))


def _signal_rows(data, period=None):
    start, end = _signal_window(data, period)
    return {table: [r for r in rows if r.get('event_date') and r.get('recorded_date')
                    and start <= r['event_date'][:10] <= end
                    and r['recorded_date'][:10] <= data.scope.end_date]
            for table, rows in data.evidence().items()}


def workload_baseline(data, period=None):
    """Team employee-quarter averages, median and interquartile spread; analysis only."""
    from statistics import median, quantiles
    own = {p['Employee_ID'] for p in data.roster()}
    rows = _signal_rows(data, period).get('OP_activity_weekly', [])
    metrics = {}
    for field in ('Cross_Team_Hours', 'After_Hours_Minutes'):
        totals = {}
        for row in rows:
            if row.get('Employee_ID') in own and row.get(field) is not None:
                key = (row['Employee_ID'], row['quarter'])
                totals.setdefault(key, []).append(float(row[field]))
        averages = {key: sum(values) / len(values) for key, values in totals.items()}
        values = list(averages.values())
        center = median(values) if values else 0
        spread = (quantiles(values, n=4)[2] - quantiles(values, n=4)[0]) if len(values) > 1 else 0
        metrics[field] = {'median': center, 'spread': spread, 'upper': center + 1.5 * spread,
                          'employee_quarters': averages}
    return metrics


def signal_records(data, focus_hint=None, period=None):
    """Versioned typed-row selection leads, with original evidence and signal provenance.

    Returns employee_id -> [{signal_type, source, record_id, event_date,
    beneficiary_manager_id, work_refs, evidence}]. These are internal leads, not findings.
    """
    roster = {p['Employee_ID']: p for p in data.roster()}
    own = set(roster)
    rows = _signal_rows(data, period)
    focus = focus_hint.get('manager_id') if isinstance(focus_hint, dict) else focus_hint
    if focus and not re.fullmatch(r'M\d+', str(focus)):
        raise ValueError('Beneficiary focus requires a resolved manager ID.')
    records = {person: [] for person in own}
    closing_rows = _signal_rows(data)
    recognized = {(row.get('Employee_ID'), ref['type'], ref['id'])
                  for row in closing_rows.get('HR_recognition_events', [])
                  for ref in row.get('work_refs', [])}
    threads = {r['record_id']: r for r in rows.get('OP_collab_threads', [])}
    anchors = {(ref['type'], ref['id']): r for table in ('OP_contributions', 'OP_collab_threads', 'OP_dependency_blockers', 'OP_incident_handoffs')
               for r in rows.get(table, []) for ref in r.get('work_refs', [])}
    requests = {r['record_id']: r for r in rows.get('OP_work_requests', [])}
    shared_refs = {(ref['type'], ref['id']) for r in closing_rows.get('HR_recognition_feedback', [])
                   if r.get('shared_as_of') for ref in r.get('work_refs', [])}
    def add(employee, kind, row):
        records[employee].append({'signal_type': kind, 'source': row['source'],
            'record_id': row['record_id'], 'event_date': row['event_date'],
            'beneficiary_manager_id': row.get('beneficiary_manager_id'),
            'work_refs': row.get('work_refs', []), 'evidence': row})
    work_tables = {'OP_contributions', 'OP_collab_threads', 'OP_collab_messages',
                   'OP_dependency_blockers', 'OP_incident_handoffs', 'OP_meeting_mentions',
                   'HR_recognition_feedback', 'OP_work_requests'}
    for table in sorted(work_tables):
        for row in rows.get(table, []):
            beneficiary = row.get('beneficiary_manager_id')
            if table == 'HR_recognition_feedback':
                linked = {anchors[(ref['type'], ref['id'])].get('beneficiary_manager_id')
                          for ref in row.get('work_refs', []) if (ref['type'], ref['id']) in anchors}
                linked.discard(None)
                if len(linked) == 1:
                    beneficiary = linked.pop()
                    row = dict(row, beneficiary_manager_id=beneficiary)
            if beneficiary == data.scope.manager_id or (focus and beneficiary != focus):
                continue
            # Unknown beneficiary identity is never guessed from a repeated display name.
            if not beneficiary:
                continue
            if table == 'OP_dependency_blockers' and not row.get('Resolved_At'):
                continue
            for employee in set(row.get('employee_ids', [])) & own:
                add(employee, 'cross_team_help', row)
                parent = threads.get(row.get('Thread_ID'), {})
                informal = table in {'OP_contributions', 'OP_collab_threads', 'OP_dependency_blockers'} and not row.get('Work_Request_ID')
                informal = informal or (table == 'OP_collab_messages' and parent and not parent.get('Work_Request_ID'))
                unshared = table == 'HR_recognition_feedback' and not row.get('shared_as_of', False)
                linked_work = [anchors[(ref['type'], ref['id'])] for ref in row.get('work_refs', [])
                               if (ref['type'], ref['id']) in anchors]
                owners = {r.get('Employee_ID') for r in linked_work if r.get('Employee_ID')}
                request_id = row.get('Work_Request_ID') or parent.get('Work_Request_ID')
                request = requests.get(request_id, {})
                if request.get('Assigned_Employee_ID'):
                    owners.add(request['Assigned_Employee_ID'])
                if table == 'HR_recognition_feedback' and row.get('Employee_ID'):
                    owners = {row['Employee_ID']}
                other_attribution = bool(owners and employee not in owners)
                refs = {(r['type'], r['id']) for r in row.get('work_refs', [])}
                formal = request_id or any(r.get('Work_Request_ID') for r in linked_work)
                notes_only = table == 'OP_meeting_mentions' and not refs & shared_refs and not formal
                if informal or unshared or other_attribution or notes_only:
                    add(employee, 'visibility_gap', row)
                if row.get('Team_Goal_ID') or row.get('Blocked_Team_Goal_ID'):
                    add(employee, 'importance', row)
                refs = {(r['type'], r['id']) for r in row.get('work_refs', [])}
                if not any((employee, kind, key) in recognized for kind, key in refs):
                    add(employee, 'recognition_gap', row)
                named_in_other_text = other_attribution
                if table == 'OP_collab_messages':
                    person = roster[employee]
                    mentions = set(str(row.get('Mentioned_Employee_IDs') or '').split(';'))
                    name = _key(person.get('Employee_Name'))
                    text = _key(row.get('Message_Text'))
                    mentioned = employee in mentions or bool(name and re.search(
                        r'(?<!\w)' + re.escape(name) + r'(?!\w)', text))
                    named_in_other_text = (other_attribution and mentioned
                                           and row.get('Author_Employee_ID') != employee)
                if table in {'OP_collab_messages', 'HR_recognition_feedback', 'OP_meeting_mentions'} and named_in_other_text:
                    add(employee, 'name_in_other_text', row)
    # A self-review is a lead, never corroboration on its own. Resolve its
    # beneficiary explicitly in focus mode; an unanchored initiative has no focus.
    stopwords = {'the', 'a', 'and', 'for', 'to', 'of', 'my', 'our', 'with', 'in'}
    matching_tokens = {}
    if not focus:
        for table, field in (('HR_goals', 'Goal_Text'), ('OP_contributions', 'Contribution_Summary')):
            for other in rows.get(table, []):
                tokens = set(re.findall(r'\w+', _key(other.get(field)))) - stopwords
                matching_tokens.setdefault(other.get('Employee_ID'), []).append(tokens)
    for row in rows.get('HR_self_review_items', []):
        employee = row.get('Employee_ID')
        if employee not in own:
            continue
        team = row.get('Team_Helped')
        teams = data.resolve_team(team) if team and hasattr(data, 'resolve_team') else []
        cross_team = bool(teams and all(t['manager_id'] != data.scope.manager_id for t in teams))
        if focus:
            if len(teams) == 1 and teams[0]['manager_id'] == focus and cross_team:
                add(employee, 'self_review', dict(row, beneficiary_manager_id=focus))
            continue
        tokens = set(re.findall(r'\w+', _key(row.get('Item_Text')))) - stopwords
        matched = any(len(tokens & other) >= 3 and
                      len(tokens & other) / max(1, min(len(tokens), len(other))) >= 0.6
                      for other in matching_tokens.get(employee, []))
        if cross_team or (tokens and not row.get('Claimed_Goal_ID') and not matched):
            add(employee, 'self_review', row)
    if not focus:
        baselines = workload_baseline(data, period)
        for row in rows.get('OP_activity_weekly', []):
            employee = row.get('Employee_ID')
            if employee in own and any(row.get(field) is not None and
                    baseline['employee_quarters'].get((employee, row['quarter']), 0) > baseline['upper']
                    for field, baseline in baselines.items()):
                add(employee, 'workload', row)
    for employee, leads in records.items():
        hidden = [r for r in leads if r['signal_type'] == 'visibility_gap']
        quarters = {r['evidence']['quarter'] for r in hidden}
        if len(quarters) >= 2:
            for lead in hidden:
                add(employee, 'repetition', lead['evidence'])
    return records


def team_summary(data, focus_hint=None, period=None):
    """Factual selection lines only; slot metadata must never enter a model prompt."""
    roster = sorted(p['Employee_ID'] for p in data.roster())
    focus = focus_hint.get('manager_id') if isinstance(focus_hint, dict) else focus_hint
    if focus and not re.fullmatch(r'M\d+', str(focus)):
        raise ValueError('Beneficiary focus requires a resolved manager ID.')
    if not focus and len(roster) <= 10:
        return {'lines': [], 'lowest': [], 'whole_team': roster, 'selection_count': 0}
    lowest = [] if focus else [r['employee_id'] for r in lowest_satisfaction(data)]
    records = signal_records(data, focus_hint, period)
    rows = _signal_rows(data, period)
    baselines = workload_baseline(data, period) if not focus else {}
    lines = []
    kinds = {'OP_contributions': 'contribution', 'OP_collab_threads': 'thread_answered',
             'OP_dependency_blockers': 'blocker_resolved', 'OP_incident_handoffs': 'incident_handoff'}
    for employee in roster:
        if employee in lowest:
            continue
        leads = records[employee]
        help_rows = {(r['source'], r['record_id']): r['evidence'] for r in leads
                     if r['signal_type'] == 'cross_team_help'}
        if focus and not help_rows:
            continue
        beneficiaries = []
        for manager in sorted({r['beneficiary_manager_id'] for r in help_rows.values()}):
            work = [r for r in help_rows.values() if r['beneficiary_manager_id'] == manager]
            teams = data.resolve_team(manager)
            facts = {'manager_id': manager, 'team': teams[0]['team'] if len(teams) == 1 else 'Other team',
                     **{kind: sum(r['source'] == table for r in work) for table, kind in kinds.items()},
                     'help_records': len(work),
                     'informal_threads': sum(r['source'] == 'OP_collab_threads' and not r.get('Work_Request_ID') for r in work),
                     'partner_feedback': sum(r['source'] == 'HR_recognition_feedback' for r in work),
                     'shared_feedback': sum(r['source'] == 'HR_recognition_feedback' and bool(r.get('shared_as_of')) for r in work),
                     'other_text_mentions': len({(r['source'], r['record_id']) for r in leads
                         if r['signal_type'] == 'name_in_other_text' and r['beneficiary_manager_id'] == manager}),
                     'linked_goals': len({r.get('Team_Goal_ID') or r.get('Blocked_Team_Goal_ID') for r in work
                         if r.get('Team_Goal_ID') or r.get('Blocked_Team_Goal_ID')}),
                     'linked_blockers': len({r['record_id'] for r in work if r['source'] == 'OP_dependency_blockers'})}
            beneficiaries.append(facts)
        refs = {(ref['type'], ref['id']) for r in help_rows.values() for ref in r.get('work_refs', [])}
        reviews = {r['record_id']: r['evidence'] for r in leads if r['signal_type'] == 'self_review'}
        cross_reviews = 0
        for review in reviews.values():
            teams = data.resolve_team(review.get('Team_Helped')) if review.get('Team_Helped') else []
            if teams and all(t['manager_id'] != data.scope.manager_id for t in teams):
                cross_reviews += 1
        weeks = {r.get('Week_Start') or r['event_date'] for r in rows.get('OP_activity_weekly', [])
                 if r.get('Employee_ID') == employee and any(r.get(field) is not None and
                     float(r[field]) > baseline['upper'] for field, baseline in baselines.items())}
        recognition = {(r['source'], r['record_id']) for r in rows.get('HR_recognition_events', [])
                       if r.get('Employee_ID') == employee and (not focus or refs &
                           {(ref['type'], ref['id']) for ref in r.get('work_refs', [])})}
        lines.append({'employee_id': employee, 'beneficiaries': beneficiaries,
                      'help_records': len(help_rows), 'recognition_events': len(recognition),
                      'quarters_with_help': len({r['quarter'] for r in help_rows.values()}),
                      'self_review_cross_team': cross_reviews,
                      'self_review_unmatched_initiative': len(reviews) - cross_reviews,
                      'above_baseline_weeks': len(weeks)})
    whole = [line['employee_id'] for line in lines] if focus and len(lines) <= 10 else []
    return {'lines': lines, 'lowest': lowest, 'whole_team': whole,
            'selection_count': 0 if whole else min(10 if focus else 5, len(lines))}


PREFILTER_VERSION = 'discovery-prefilter-v2'
# These prioritize work anchors inside a selected person's bounded evidence;
# they never rank people or decide who enters the pool.
_QUALIFYING_SIGNALS = {'visibility_gap', 'importance', 'repetition', 'name_in_other_text', 'self_review'}
_TEXT_FIELDS = ('Contribution_Summary', 'Business_Outcome', 'Evidence_Description',
    'Message', 'Message_Text', 'Note_Text', 'Topic', 'Blocker_Description',
    'Resolution_Note', 'Incident_Notes', 'Item_Text', 'Goal_Text', 'Measurement_Note',
    'Citation_Text', 'Goal_Outcome', 'Quantified_Result', 'Description')


def _validated_subject(data, resolution):
    # Validate the complete payload before any evidence read, even for a team request.
    if resolution.get('status') != 'process':
        raise ValueError('A resolved process subject is required.')
    subject = resolution.get('subject') or {}
    roster = {p['Employee_ID']: p for p in data.roster()}
    ids = subject.get('employee_ids')
    kind = subject.get('kind')
    if (subject.get('manager_id') != data.scope.manager_id or
            kind not in ('team', 'person', 'people') or not isinstance(ids, list) or
            not ids or len(set(ids)) != len(ids) or any(e not in roster for e in ids) or
            (kind == 'person' and len(ids) != 1) or
            (kind == 'people' and not 2 <= len(ids) <= 5) or
            (kind == 'team' and set(ids) != set(roster))):
        raise ValueError('Subject does not match the authorized roster.')
    period = resolution.get('period') or {}
    if not (data.scope.start_date <= period.get('start', '') <= period.get('end', '') <= data.scope.end_date
            and period.get('as_of') == data.scope.end_date):
        raise ValueError('Period does not match the authorized analysis window.')
    focus = resolution.get('focus_hint')
    if focus and (not isinstance(focus, dict) or not re.fullmatch(r'M\d+', str(focus.get('manager_id', '')))):
        raise ValueError('Beneficiary focus requires a resolved manager ID.')
    return subject, roster


def selection_audit(data, resolution, selected_employee_ids=None):
    """Internal entry slots; never put pulse scores or selection reasons in the model pool."""
    subject, roster = _validated_subject(data, resolution)
    if subject['kind'] != 'team':
        if selected_employee_ids is not None and selected_employee_ids != []:
            raise ValueError('Named subjects do not accept a selection.')
        return {'selected': list(subject['employee_ids']), 'whole_team': [], 'lowest': [], 'selection': []}
    summary = team_summary(data, resolution.get('focus_hint'), resolution['period'])
    lowest, whole = summary['lowest'], summary['whole_team']
    selection = []
    if selected_employee_ids is not None:
        allowed = {line['employee_id'] for line in summary['lines']}
        if (not isinstance(selected_employee_ids, list) or
                any(not isinstance(e, str) for e in selected_employee_ids) or
                len(selected_employee_ids) != summary['selection_count'] or
                len(set(selected_employee_ids)) != len(selected_employee_ids) or
                not set(selected_employee_ids) <= allowed or
                set(selected_employee_ids) & set(lowest)):
            raise ValueError('Selection must contain exactly the requested distinct summary IDs.')
        selection = list(selected_employee_ids)
    return {'selected': list(whole or lowest + selection), 'whole_team': list(whole),
            'lowest': list(lowest), 'selection': selection}


def _refs(row):
    return {(r['type'], r['id']) for r in row.get('work_refs', [])}


def _excerpt(text, person, limit=300):
    """Keep the relevant sentence, including names near the end of long notes."""
    text = ' '.join(str(text or '').split())
    needles = [str(person.get('Employee_Name') or ''), person['Employee_ID']]
    positions = [text.casefold().find(n.casefold()) for n in needles if n]
    positions = [p for p in positions if p >= 0]
    at = min(positions) if positions else 0
    start = max(text.rfind('. ', 0, at) + 2, text.rfind('! ', 0, at) + 2, 0) if at else 0
    if at - start > limit - 60:
        start = max(0, at - 60)
    return text[start:start + limit]


def _compact(row, person):
    text = ' '.join(str(row[field]) for field in _TEXT_FIELDS if row.get(field))
    item = {key: row.get(key) for key in ('source', 'record_id', 'event_date', 'recorded_date', 'beneficiary_manager_id')}
    item['work_refs'] = [dict(ref) for ref in row.get('work_refs', [])]
    item['text'] = _excerpt(text, person)
    return item


def _person_items(data, employee, person, rows, all_rows, cap, focus=None, leads=None):
    """Bounded work records with their contradicting closing context before source text."""
    excluded = {'HR_employee_performance', 'OP_source_coverage', 'OP_activity_weekly', 'OP_capacity',
                'OP_team_goals', 'OP_goal_outcomes', 'HR_recognition_events', 'OP_team_plans'}
    candidates = [r for table, values in rows.items() if table not in excluded
                  for r in values if employee in r.get('employee_ids', [])]
    # Most specific work and attribution first, then recent corroboration.
    priority = {'HR_recognition_feedback': 0, 'OP_dependency_blockers': 1,
                'OP_incident_handoffs': 2, 'OP_contributions': 3,
                'OP_collab_messages': 4, 'OP_meeting_mentions': 5,
                'OP_collab_threads': 6, 'HR_self_review_items': 7}
    candidates.sort(key=lambda r: (r.get('event_date', ''), r['record_id']), reverse=True)
    candidates.sort(key=lambda r: priority.get(r['source'], 8))
    if focus:
        candidates.sort(key=lambda r: r.get('beneficiary_manager_id') != focus)
    # First round covers distinct work anchors; second supplies corroborating records.
    chosen, deferred, seen = [], [], set()
    for row in candidates:
        refs = _refs(row)
        if refs and refs <= seen:
            deferred.append(row)
        else:
            chosen.append(row)
            seen.update(refs)
    candidates = chosen + deferred
    if focus:
        candidates.sort(key=lambda r: r.get('beneficiary_manager_id') != focus)
    # Use the same typed leads as subject selection. Ordinary formal work can
    # have many source rows and goals without supplying hidden-work evidence.
    if leads is None:
        leads = signal_records(data, {'manager_id': focus} if focus else None).get(employee, [])
    lead_types, lead_sources = {}, {}
    for lead in leads:
        evidence = lead['evidence']
        keys = _refs(evidence) or {('unanchored', evidence['record_id'])}
        for key in keys:
            lead_types.setdefault(key, set()).add(lead['signal_type'])
            lead_sources.setdefault(key, set()).add(lead['source'])
    lead_rows = {(lead['source'], lead['record_id']): lead['evidence'] for lead in leads
                 if lead['source'] not in excluded}
    candidate_map = {(r['source'], r['record_id']): r for r in candidates}
    candidate_map.update(lead_rows)
    candidates = list(candidate_map.values())
    clusters = {}
    for row in candidates:
        for key in _refs(row) or {('unanchored', row['record_id'])}:
            clusters.setdefault(key, []).append(row)
    def cluster_rank(pair):
        key, records = pair
        types = lead_types.get(key, set())
        qualifying = types & _QUALIFYING_SIGNALS
        focused = any(r.get('beneficiary_manager_id') == focus for r in records) if focus else True
        corroboration = len(lead_sources.get(key, set()) - {'HR_self_review_items'})
        return (focused, bool(qualifying), len(qualifying), len(types), corroboration,
                len({r['source'] for r in records}), max(r['event_date'] for r in records))
    ranked = sorted(clusters.items(), key=cluster_rank, reverse=True)
    anchor_keys = {key for key, _ in ranked[:2]}
    selected_work = [r for _, records in ranked[:2] for r in records]
    linked = [r for values in all_rows.values() for r in values
              if r.get('source') != 'HR_employee_performance' and anchor_keys & _refs(r)]
    goal_ids = {r.get('Team_Goal_ID') or r.get('Blocked_Team_Goal_ID') for r in linked} - {None, ''}
    linked += [r for r in all_rows.get('OP_team_goals', []) if r.get('Team_Goal_ID') in goal_ids]
    linked += [r for r in all_rows.get('OP_goal_outcomes', []) if r.get('Team_Goal_ID') in goal_ids]
    def closing_priority(row):
        if row['source'] == 'HR_recognition_events' and row.get('Employee_ID') == employee:
            return 0
        if row.get('shared_as_of'):
            return 1
        if row.get('Employee_ID') and set(row.get('employee_ids', [])) - {row['Employee_ID']}:
            return 2
        if row['source'] in ('OP_team_goals', 'OP_goal_outcomes', 'OP_dependency_blockers', 'OP_work_requests'):
            return 3
        return 4
    merged = {(r['source'], r['record_id']): r for r in selected_work + linked
              if r.get('source') != 'HR_recognition_events' or r.get('Employee_ID') == employee}
    ordered = list(merged.values())
    ordered.sort(key=lambda r: (r.get('event_date', ''), r['record_id']), reverse=True)
    ordered.sort(key=lambda r: (closing_priority(r), priority.get(r['source'], 8)))
    if focus:
        ordered.sort(key=lambda r: r.get('beneficiary_manager_id') != focus)
    # Repeated closure rows for one work item must not consume every slot.
    # Keep the most recent record of each closing kind first, then independent
    # source support, followed by additional records within the same strict cap.
    first, remaining, groups = [], [], set()
    for row in ordered:
        group = (closing_priority(row), row['source'],
                 tuple(sorted(_refs(row))) or row.get('Team_Goal_ID'))
        if group in groups:
            remaining.append(row)
        else:
            groups.add(group)
            first.append(row)
    seen_records = set(merged)
    candidates = first + remaining + [r for r in candidates if (r['source'], r['record_id']) not in seen_records]
    review_leads = [lead['evidence'] for lead in leads if lead['signal_type'] == 'self_review']
    if review_leads:
        review = max(review_leads, key=lambda r: (r['event_date'], r['record_id']))
        review_key = (review['source'], review['record_id'])
        candidates = [r for r in candidates if (r['source'], r['record_id']) != review_key]
        candidates.insert(min(cap - 1, len(candidates)), review)
    # Workload facts must reach judgment even when ordinary work fills the cap.
    # One source row occupies an existing slot; aggregate context is added below.
    activity = [r for r in rows.get('OP_activity_weekly', []) if r.get('Employee_ID') == employee]
    if activity and not focus:
        workload_leads = [lead['evidence'] for lead in leads if lead['signal_type'] == 'workload']
        activity_row = max(workload_leads or activity, key=lambda r: (r['event_date'], r['record_id']))
        candidates.insert(min(cap - 2, len(candidates)), activity_row)
        if review_leads:
            candidates.remove(review)
            candidates.insert(min(cap - 1, len(candidates)), review)
    coverage = all_rows.get('OP_source_coverage', [])
    as_of_by_ref = {}
    for values in all_rows.values():
        for record in values:
            for ref in _refs(record):
                as_of_by_ref.setdefault(ref, {})[(record['source'], record['record_id'])] = record
    output = []
    for row in candidates[:cap]:
        refs = _refs(row)
        related = {(r['source'], r['record_id']): r for ref in refs
                   for r in as_of_by_ref.get(ref, {}).values()}.values()
        recognition = any(r['source'] == 'HR_recognition_events' and r.get('Employee_ID') == employee for r in related)
        quarters = {r.get('quarter') for r in related if r['source'] != 'HR_recognition_events'}
        complete = bool(quarters) and all(any(c.get('Source_Table') == 'HR_recognition_events'
            and c.get('Quarter') == q and c.get('Coverage_Status') == 'complete'
            for c in coverage) for q in quarters)
        complete = complete and all(r.get('Record_Coverage') == 'complete'
            for r in related if r['source'] == 'HR_recognition_feedback')
        item = _compact(row, person)
        # Computed state has no extra source rows or hidden source text.
        item['closing_context'] = {'recognition_state': 'recorded' if recognition else 'no_recognition_event_recorded',
                                   'absence_coverage': 'complete' if complete else 'unknown'}
        item['details'] = {k: row[k] for k in ('Employee_ID', 'Assigned_Employee_ID', 'Resolved_By_Employee_ID',
            'Mentioned_Employee_ID', 'Mentioned_Employee_IDs', 'Responder_Employee_IDs', 'shared_as_of',
            'Record_Coverage', 'Status', 'Resolved_At', 'Completion_Date', 'Accepted_At',
            'Measured_Value', 'Numerator', 'Denominator', 'Team_Goal_ID', 'Blocked_Team_Goal_ID',
            'Target_Value', 'Target_Direction', 'Baseline_Value', 'Metric_Name', 'Metric_Unit', 'Due_Date') if k in row}
        item['details'].update({k: row[k] for k in ('Week_Start', 'Cross_Team_Hours',
            'After_Hours_Minutes', 'Total_Hours', 'Work_Request_ID', 'Thread_ID', 'quarter') if k in row})
        output.append(item)
    return output, len(candidates) >= cap, sum(closing_priority(r) < 4 for r in candidates[cap:])



def _person_context(employee, rows, leads, baselines, period):
    """Scoped facts for judgment, independent of how the person entered the pool."""
    workload = {}
    activity = [r for r in rows.get('OP_activity_weekly', []) if r.get('Employee_ID') == employee]
    for field, baseline in baselines.items():
        records = [r for r in activity if r.get(field) is not None]
        quarters = []
        for quarter in sorted({r['quarter'] for r in records}):
            values = [float(r[field]) for r in records if r['quarter'] == quarter]
            quarters.append({'quarter': quarter, 'weekly_records': len(values),
                             'mean': sum(values) / len(values), 'minimum': min(values), 'maximum': max(values),
                             'weeks_above_team_range': sum(v > baseline['upper'] for v in values)})
        workload[field] = {'unit': 'minutes' if field == 'After_Hours_Minutes' else 'hours',
            'team_median': baseline['median'], 'team_spread': baseline['spread'],
            'team_upper': baseline['upper'], 'quarters': quarters,
            'provenance': {'source': 'OP_activity_weekly', 'record_count': len(records),
                           'start': period['start'], 'end': period['end'],
                           'baseline_method': 'team employee-quarter means; median + 1.5 * interquartile spread'}}
    help_rows = {(lead['source'], lead['record_id']): lead['evidence'] for lead in leads
                 if lead['signal_type'] == 'cross_team_help'}
    beneficiaries = []
    for beneficiary in sorted({r['beneficiary_manager_id'] for r in help_rows.values()}):
        records = [r for r in help_rows.values() if r['beneficiary_manager_id'] == beneficiary]
        beneficiaries.append({'beneficiary_manager_id': beneficiary,
            'quarters': [{'quarter': q, 'help_records': sum(r['quarter'] == q for r in records),
                          'source_counts': {source: sum(r['quarter'] == q and r['source'] == source for r in records)
                                            for source in sorted({r['source'] for r in records if r['quarter'] == q})}}
                         for q in sorted({r['quarter'] for r in records})]})
    return {'workload': workload, 'help_by_beneficiary': beneficiaries,
            'period': dict(period)}


def prefilter(data, resolution, selected_employee_ids=None):
    """Build a serializable model pool; public evidence only, no selection diagnostics."""
    subject, roster = _validated_subject(data, resolution)
    slots = selection_audit(data, resolution, selected_employee_ids)
    rows = _signal_rows(data, resolution['period'])
    # Closing state is as of the fixed cutoff, including later recognition of earlier work.
    all_rows = _signal_rows(data)
    all_rows['OP_source_coverage'] = data.evidence().get('OP_source_coverage', [])
    cap = 8 if subject['kind'] == 'team' else 25 if subject['kind'] == 'person' else 10
    focus = (resolution.get('focus_hint') or {}).get('manager_id')
    leads = signal_records(data, resolution.get('focus_hint'), resolution['period'])
    baselines = workload_baseline(data, resolution['period'])
    people, caps = [], []
    for employee in slots['selected']:
        items, reached, omitted_closing = _person_items(data, employee, roster[employee], rows, all_rows, cap, focus, leads.get(employee, []))
        people.append({'employee_id': employee, 'name': roster[employee].get('Employee_Name', employee), 'items': items,
                       'context': _person_context(employee, rows, leads.get(employee, []), baselines, resolution['period'])})
        if reached:
            caps.append({'employee_id': employee, 'item_cap': cap, 'unselected_closing_records': omitted_closing})
    patterns = {}
    for employee, records in leads.items():
        for lead in records:
            beneficiary = lead['beneficiary_manager_id']
            if lead['signal_type'] == 'visibility_gap' and beneficiary and (not focus or beneficiary == focus):
                patterns.setdefault(beneficiary, {}).setdefault(employee, {})[(lead['source'], lead['record_id'])] = lead
    by_person = {p['employee_id']: p for p in people}
    pattern_leads = []
    for beneficiary, involved in sorted(patterns.items()):
        samples = []
        for employee in sorted(involved):
            # Samples reference existing bounded items, never add an uncapped second pool.
            items = by_person.get(employee, {}).get('items', [])
            samples.extend({'employee_id': employee, 'source': r['source'], 'record_id': r['record_id']}
                for r in [r for r in items if r.get('beneficiary_manager_id') == beneficiary][:2])
        pattern_leads.append({'beneficiary_manager_id': beneficiary, 'people_count': len(involved),
                              'work_count': len({key for records in involved.values() for key in records}),
                              'sampled_people': len({r['employee_id'] for r in samples}),
                              'sample_coverage': 'complete' if set(involved) <= {r['employee_id'] for r in samples} else 'partial',
                              'samples': samples})
    return {'rules_version': PREFILTER_VERSION, 'subject': {**subject, 'employee_ids': slots['selected']}, 'period': dict(resolution['period']),
            'focus_hint': dict(resolution['focus_hint']) if resolution.get('focus_hint') else None,
            'people': people, 'coverage': [dict(r) for r in all_rows['OP_source_coverage']
                                        if r.get('Source_Table') == 'HR_recognition_events'],
            'caps_hit': {'people': len(people) >= 10 if subject['kind'] == 'team' else False,
                         'items': caps}, 'team_pattern_leads': pattern_leads}
