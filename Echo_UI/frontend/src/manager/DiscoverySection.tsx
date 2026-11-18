import { Compass, PenLine } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge, Button } from '../components/ui'
import { api, type ActionDecision, type ActionType, type DiscoveryAction, type DiscoveryFinding, type DiscoverySection as Section, type DiscoveryView, type Example, type FollowUp } from '../lib/api'
import Fold from './Fold'

export const ACTION_NAMES: Record<ActionType, string> = {
  A1: 'Recognize a contribution',
  A2: 'Request feedback from the benefited team',
  A3: 'Workload conversation',
  A4: 'Ask for visibility',
  A5: 'Performance-review note',
  A6: 'Team process change',
}

const FOLLOW_UP: Record<FollowUp['status'], { text: string; tone: 'green' | 'amber' | 'slate' | 'blue' }> = {
  observed: { text: 'Observed', tone: 'green' },
  not_yet: { text: 'Not yet', tone: 'amber' },
  unknown: { text: 'Unknown', tone: 'slate' },
  pending_decision: { text: 'Pending decision', tone: 'blue' },
  dismissed: { text: 'Dismissed', tone: 'slate' },
}

const refKey = (ref: { type: string; id: string }) => `${ref.type}:${ref.id}`
const FIELD = 'w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900'

export function ActionCard({ action, followUp, onDecide }: { action: DiscoveryAction; followUp?: FollowUp; onDecide: (decision: ActionDecision) => Promise<void> }) {
  const { current } = action
  const [mode, setMode] = useState<'view' | 'edit' | 'dismiss'>('view')
  const [text, setText] = useState(current.draft_text)
  const [type, setType] = useState<ActionType>(current.action_type)
  const [refs, setRefs] = useState(() => new Set(current.work_refs.map(refKey)))
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (decision: ActionDecision) => {
    setBusy(true)
    try {
      await onDecide(decision)
      setMode('view')
    } finally {
      setBusy(false)
    }
  }
  const changed = text.trim() !== current.draft_text || type !== current.action_type || refs.size !== current.work_refs.length
  const follow = FOLLOW_UP[followUp?.status ?? (action.state === 'proposed' ? 'pending_decision' : 'unknown')]
  const id = action.action_id

  return (
    <li className="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold">
          {current.action_type} · {ACTION_NAMES[current.action_type]}
        </span>
        <Badge tone={action.state === 'dismissed' ? 'slate' : action.state === 'proposed' ? 'amber' : 'green'}>{action.state}</Badge>
        <span title={followUp?.reason}>
          <Badge tone={follow.tone}>Follow-up: {follow.text}</Badge>
        </span>
      </div>
      <div className="mt-1 text-xs text-slate-500">
        For {action.subject_id} ({action.subject_kind}) · beneficiary team {action.beneficiary_team}
      </div>
      {mode === 'edit' ? (
        <div className="mt-3 space-y-3">
          <label className="block text-xs font-medium" htmlFor={`${id}-type`}>
            Action type
            <select id={`${id}-type`} className={`${FIELD} mt-1`} value={type} onChange={(e) => setType(e.target.value as ActionType)}>
              {(Object.keys(ACTION_NAMES) as ActionType[]).map((t) => (
                <option key={t} value={t}>
                  {t} · {ACTION_NAMES[t]}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-xs font-medium" htmlFor={`${id}-text`}>
            Draft
            <textarea id={`${id}-text`} className={`${FIELD} mt-1`} rows={5} value={text} onChange={(e) => setText(e.target.value)} />
          </label>
          {action.allowed_work_refs.length > 0 && (
            <fieldset className="text-xs">
              <legend className="font-medium">Work references (uncheck to remove)</legend>
              {action.allowed_work_refs.map((ref) => (
                <label key={refKey(ref)} className="mr-4 inline-flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={refs.has(refKey(ref))}
                    onChange={() => setRefs((s) => { const n = new Set(s); if (!n.delete(refKey(ref))) n.add(refKey(ref)); return n })}
                  />
                  {ref.type} {ref.id}
                </label>
              ))}
            </fieldset>
          )}
          <div className="flex gap-2">
            <Button
              variant="primary"
              loading={busy}
              disabled={!changed || !text.trim()}
              onClick={() => submit({ state: 'edited', draft_text: text.trim(), action_type: type, work_refs: action.allowed_work_refs.filter((r) => refs.has(refKey(r))) })}
            >
              Save edit
            </Button>
            <Button onClick={() => setMode('view')}>Cancel</Button>
          </div>
        </div>
      ) : (
        <p className="mt-3 whitespace-pre-line rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/50">{current.draft_text}</p>
      )}
      {current.reason && <p className="mt-2 text-xs text-slate-500">Reason: {current.reason}</p>}
      {mode === 'dismiss' && (
        <div className="mt-3 space-y-2">
          <label className="block text-xs font-medium" htmlFor={`${id}-reason`}>
            Why are you dismissing this? (required)
            <input id={`${id}-reason`} className={`${FIELD} mt-1`} value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
          <div className="flex gap-2">
            <Button variant="danger" loading={busy} disabled={!reason.trim()} onClick={() => submit({ state: 'dismissed', reason: reason.trim() })}>
              Confirm dismiss
            </Button>
            <Button onClick={() => setMode('view')}>Cancel</Button>
          </div>
        </div>
      )}
      {mode === 'view' && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="primary" loading={busy} disabled={action.state === 'accepted'} onClick={() => submit({ state: 'accepted' })}>
            Accept
          </Button>
          <Button onClick={() => setMode('edit')}>Edit</Button>
          <Button disabled={action.state === 'dismissed'} onClick={() => setMode('dismiss')}>
            Dismiss
          </Button>
        </div>
      )}
    </li>
  )
}

/** The backend action records of one run (registering is idempotent), so every place that shows a Discovery action reads and decides the same record. */
function useRunActions(managerId: string, runId: string, enabled: boolean) {
  const [actions, setActions] = useState<DiscoveryAction[]>([])
  const [followUps, setFollowUps] = useState<Record<string, FollowUp>>({})
  const [error, setError] = useState('')
  const refreshFollowUps = () => api.actionFollowUp(managerId).then((r) => setFollowUps(r.results)).catch(() => undefined)

  useEffect(() => {
    if (!enabled) return
    let live = true
    api
      .registerActions(managerId, runId)
      .then((r) => live && setActions(r.actions.filter((a) => a.run_id === runId)))
      .then(refreshFollowUps)
      .catch((e: Error) => live && setError(e.message))
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [managerId, runId, enabled])

  const decide = async (action: DiscoveryAction, decision: ActionDecision) => {
    setError('')
    try {
      const updated = await api.decideAction(managerId, action.action_id, decision)
      setActions((all) => all.map((a) => (a.action_id === updated.action_id ? updated : a)))
      await refreshFollowUps()
    } catch (e) {
      setError((e as Error).message)
      throw e
    }
  }
  return { actions, followUps, error, decide }
}

/** The Action Center's view of one Discovery action: the same backend record as the person card, so a decision made in either place shows in both. */
export function DiscoveryDecision({ managerId, runId, sourceActionId }: { managerId: string; runId: string; sourceActionId: string }) {
  const { actions, followUps, error, decide } = useRunActions(managerId, runId, true)
  const [open, setOpen] = useState(false)
  const action = actions.find((a) => a.source_action_id === sourceActionId)
  if (!action) return error ? <p role="alert" className="mt-2 text-xs text-rose-600">{error}</p> : null
  return (
    <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={action.state === 'dismissed' ? 'slate' : action.state === 'proposed' ? 'amber' : 'green'}>Discovery action: {action.state}</Badge>
        <Button onClick={() => setOpen(!open)} aria-expanded={open}>{open ? 'Hide draft' : 'Review and decide'}</Button>
      </div>
      {open && (
        <ul className="mt-3">
          <ActionCard action={action} followUp={followUps[action.action_id]} onDecide={(d) => decide(action, d)} />
        </ul>
      )}
      {error && <p role="alert" className="mt-2 text-xs text-rose-600">{error}</p>}
    </div>
  )
}

const VISIBILITY: Record<DiscoveryFinding['visibility_state'], { text: string; tone: 'green' | 'amber' | 'red' }> = {
  shared: { text: 'Praise reached you', tone: 'green' },
  praise_not_shared: { text: 'Praise not passed on', tone: 'amber' },
  no_feedback: { text: 'No praise', tone: 'red' },
}
const RECOGNITION: Record<DiscoveryFinding['recognition_state'], { text: string; tone: 'green' | 'amber' | 'slate' }> = {
  recognized: { text: 'Recognized', tone: 'green' },
  not_recognized: { text: 'Not yet recognized', tone: 'amber' },
  unknown: { text: 'Recognition unknown', tone: 'slate' },
}

function PersonCard({ finding, actions, followUps, example, onDraft, onDecide }: {
  finding: DiscoveryFinding
  actions: DiscoveryAction[]
  followUps: Record<string, FollowUp>
  example?: Example
  onDraft?: (example: Example) => void
  onDecide: (action: DiscoveryAction, decision: ActionDecision) => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const visibility = VISIBILITY[finding.visibility_state]
  const recognition = RECOGNITION[finding.recognition_state]
  return (
    <li className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <div className="min-w-0 flex-1 text-sm font-medium">
          {finding.employee_names.join(', ') || finding.employee_ids.join(', ')} <span className="font-normal text-slate-500">helped {finding.beneficiary_team}</span>
        </div>
        {finding.contribution_date && <span className="text-xs text-slate-500">{finding.contribution_date}</span>}
      </div>
      <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{finding.work_summary}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {visibility && <Badge tone={visibility.tone}>{visibility.text}</Badge>}
        {recognition && <Badge tone={recognition.tone}>{recognition.text}</Badge>}
        {example && onDraft && (
          <button onClick={() => onDraft(example)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:hover:border-indigo-500">
            <PenLine className="size-3.5" /> Draft note
          </button>
        )}
        {actions.length > 0 && (
          <button onClick={() => setOpen(!open)} aria-expanded={open} className="ml-auto text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">
            {open ? 'Hide' : 'Drafted actions'} ({actions.length})
          </button>
        )}
      </div>
      {open && (
        <ul className="mt-3 space-y-3">
          {actions.map((action) => (
            <ActionCard key={action.action_id} action={action} followUp={followUps[action.action_id]} onDecide={(d) => onDecide(action, d)} />
          ))}
        </ul>
      )}
    </li>
  )
}

/** The Discovery section: separate from Original's answer, built and checked by code, with decidable action cards.
 *  With structured findings it shows one compact card per person; without them it falls back to the rendered text. */
export default function DiscoverySection({ managerId, runId, section, discovery, examples = [], onDraft }: {
  managerId: string
  runId: string
  section?: Section
  discovery?: DiscoveryView
  examples?: Example[]
  onDraft?: (example: Example) => void
}) {
  const findings = discovery?.findings ?? []
  const cards = findings.length > 0
  const { actions, followUps, error, decide } = useRunActions(managerId, runId, cards || (section?.finding_ids.length ?? 0) > 0)
  const exampleFor = (f: DiscoveryFinding) => examples.find((e) => e.contribution_id === f.contribution_id) ?? examples.find((e) => f.employee_ids.includes(e.employee_id))

  return (
    <section className="rounded-2xl border border-teal-200 bg-white p-5 shadow-sm dark:border-teal-500/30 dark:bg-slate-900" aria-labelledby={`${runId}-discovery`}>
      <div className="flex flex-wrap items-center gap-2">
        <Compass className="size-4" style={{ color: 'var(--color-discovery)' }} />
        <h3 id={`${runId}-discovery`} className="text-sm font-semibold">Discovery</h3>
        <Badge tone="blue">Found by the Discovery agent · facts checked by code</Badge>
      </div>
      {cards ? (
        <>
          <ul className="mt-3 space-y-2">
            {findings.map((f) => (
              <PersonCard
                key={f.finding_id}
                finding={f}
                actions={actions.filter((a) => a.finding_id === f.finding_id)}
                followUps={followUps}
                example={exampleFor(f)}
                onDraft={onDraft}
                onDecide={decide}
              />
            ))}
          </ul>
          {actions.length > 0 && <p className="mt-3 text-xs text-slate-500">Simulation: observed means a record exists in the synthetic data</p>}
          <Fold title="Details" defaultOpen={false} className="mt-3 rounded-xl border border-slate-100 dark:border-slate-800">
            <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
              {discovery?.period?.start && (
                <li>
                  Period: {discovery.period.start} to {discovery.period.end}
                  {discovery.period.hint_not_applied && ' (the period in your question was not recognized, so all dates were reviewed)'}
                </li>
              )}
              {discovery?.coverage?.people_reviewed !== undefined && <li>People reviewed: {discovery.coverage.people_reviewed} of {discovery.coverage.team_size}</li>}
            </ul>
            {/* Structured fields only: the rendered text repeats the cards and carries partner quotes. */}
            <dl className="mt-3 space-y-2.5 text-sm">
              {findings.map((f) => (
                <div key={f.finding_id}>
                  <dt className="font-medium">{f.employee_names?.join(', ') || f.beneficiary_team}</dt>
                  <dd className="text-slate-600 dark:text-slate-300">{f.why_it_matters}</dd>
                  {f.evidence_ids.length > 0 && <dd className="text-xs text-slate-500">Records: {f.evidence_ids.join(', ')}</dd>}
                </div>
              ))}
            </dl>
          </Fold>
        </>
      ) : (
        <>
          <p className="mt-3 whitespace-pre-line text-sm leading-6">{section?.rendered}</p>
          {actions.length > 0 && (
            <div className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-800">
              <p className="mb-3 text-xs text-slate-500">Simulation: observed means a record exists in the synthetic data</p>
              <ul className="space-y-3">
                {actions.map((action) => (
                  <ActionCard key={action.action_id} action={action} followUp={followUps[action.action_id]} onDecide={(d) => decide(action, d)} />
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      {error && <p role="alert" className="mt-3 text-sm text-rose-600">{error}</p>}
    </section>
  )
}
