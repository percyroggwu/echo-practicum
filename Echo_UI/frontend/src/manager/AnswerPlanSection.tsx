import { CalendarCheck, Check, CheckCircle2, DoorOpen, FileText, Mail, MessageCircleQuestion, PenLine, Utensils } from 'lucide-react'
import { useState } from 'react'
import type { AnswerAction, Example } from '../lib/api'
import type { ActionOrigin, EchoAction, MeetingPurpose, Participant, SchedulerPrefill } from './actionTypes'
import { DraftNoteDialog } from './Brief'
import { mailtoUrl } from './PartnerActions'
import { ACTION_META, ActionIcon, toneStyle, type AnswerPlan } from './visual'

const PURPOSE: Record<AnswerAction['kind'], MeetingPurpose> = {
  recognize: 'Recognition discussion',
  one_to_one: 'Recognition discussion',
  partner: 'Cross-team coordination',
  handoff: 'Cross-team coordination',
  plan: 'Workload check-in',
  goal: 'General team meeting',
  team_event: 'Team engagement',
  room: 'Team engagement',
  email: 'Team engagement',
}

export type EventPrefill = { title?: string; invitation?: string; origin: ActionOrigin }
export type RoomPrefill = { title: string; agenda: string; description: string; origin: ActionOrigin }

const originFor = (plan: AnswerPlan, action: AnswerAction, index: number): ActionOrigin => ({
  kind: 'existing-evidence',
  label: `From your question · ${ACTION_META[action.kind].label}`,
  insightId: `${plan.runId}:${index}`,
})

/** An editable email draft. Echo never sends it: the manager's email app opens with it. */
function EmailDialog({ subject, body, to, onClose, onSent }: { subject: string; body: string; to?: string; onClose: () => void; onSent: () => void }) {
  const [text, setText] = useState(body)
  const [copied, setCopied] = useState(false)
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-slate-950/40" onClick={onClose} />
      <div className="slide-in relative w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl dark:bg-slate-900">
        <div className="flex items-center gap-2 text-base font-semibold">
          <Mail className="size-4 text-indigo-500" /> {subject}
        </div>
        <p className="mt-1 text-xs text-slate-500">Edit it in your own words. Echo never sends anything: your email app opens, and you choose the recipients and press send.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={10} className="mt-3 w-full resize-y rounded-xl border border-slate-200 bg-white p-3 text-sm leading-relaxed outline-none focus:border-indigo-400 dark:border-slate-700 dark:bg-slate-950" />
        <div className="mt-3 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-xl px-3.5 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            Close
          </button>
          <button
            onClick={() => {
              navigator.clipboard?.writeText(text)
              setCopied(true)
            }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3.5 py-2 text-sm font-medium hover:border-indigo-300 dark:border-slate-700"
          >
            {copied ? <Check className="size-4" /> : <FileText className="size-4" />} {copied ? 'Copied' : 'Copy'}
          </button>
          <a href={mailtoUrl(to ?? '', subject, text)} onClick={onSent} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-500">
            <Mail className="size-4" /> Open in email
          </a>
        </div>
      </div>
    </div>
  )
}

const initials = (name: string) =>
  name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)

/** Participant ids for real people. The trailing -pN borrows one of the prototype calendars, so they have realistic busy times. */
const personId = (managerId: string, employeeId: string) => `${managerId.toLowerCase()}-${employeeId.toLowerCase()}-p${(Number(employeeId.replace(/\D/g, '')) % 12) + 1}`
const partnerId = (managerId: string, team: string) => `${managerId.toLowerCase()}-partner-${team.toLowerCase().replace(/\W+/g, '-')}`

/** The people an answer names (team members and partner-team managers), as scheduler participants. */
export function planParticipants(plan: AnswerPlan, managerId: string, teamName: string): Participant[] {
  const people = new Map<string, Participant>()
  for (const action of plan.actions) {
    if (action.person)
      people.set(personId(managerId, action.person.id), {
        id: personId(managerId, action.person.id),
        name: action.person.name,
        role: 'Your team',
        team: teamName,
        initials: initials(action.person.name),
      })
    const team = action.partner?.team ?? (action.kind === 'partner' || action.kind === 'handoff' ? action.partner_team : undefined)
    if (team) {
      const name = action.partner?.name ?? `${team} manager`
      people.set(partnerId(managerId, team), { id: partnerId(managerId, team), name, role: `Manager · ${team}`, team, initials: initials(name) })
    }
  }
  return [...people.values()]
}

function prefillFor(plan: AnswerPlan, action: AnswerAction, index: number, managerId: string): SchedulerPrefill {
  const ids: string[] = []
  if (action.person) ids.push(personId(managerId, action.person.id))
  const team = action.partner?.team ?? (action.kind === 'partner' || action.kind === 'handoff' ? action.partner_team : undefined)
  if (team) ids.push(partnerId(managerId, team))
  if (action.kind === 'goal') for (const a of plan.actions) if (a.person) ids.push(personId(managerId, a.person.id))
  return {
    title: action.title,
    purpose: PURPOSE[action.kind],
    description: `${action.why}\n\nFrom Echo's answer to: "${plan.question}"`,
    participantIds: [...new Set(ids)],
    origin: originFor(plan, action, index),
  }
}

/** The Action Center's plan for one answer: one card per action, each opening the right tool already filled in. */
export default function AnswerPlanSection({
  plan,
  managerId,
  actions,
  onSchedule,
  onEvent,
  onRoom,
}: {
  plan: AnswerPlan
  managerId: string
  actions: EchoAction[]
  onSchedule: (prefill: SchedulerPrefill) => void
  onEvent: (prefill: EventPrefill) => void
  onRoom: (prefill: RoomPrefill) => void
}) {
  const [draft, setDraft] = useState<Example | null>(null)
  const [mail, setMail] = useState<number | null>(null)
  // Emails opened are remembered in this browser, since nothing is saved for them in the Action Center.
  const mailedKey = `echo-mailed-${plan.runId}`
  const [mailed, setMailed] = useState<number[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(mailedKey) ?? '[]')
    } catch {
      return []
    }
  })
  const markMailed = (index: number) => {
    const next = [...new Set([...mailed, index])]
    setMailed(next)
    try {
      localStorage.setItem(mailedKey, JSON.stringify(next))
    } catch {
      /* storage unavailable: the tick lasts for this visit */
    }
  }
  const scheduled = (index: number) => actions.find((a) => a.origin.insightId === `${plan.runId}:${index}` && a.status !== 'Cancelled')
  const done = plan.actions.filter((_, i) => scheduled(i) || mailed.includes(i)).length
  const mailAction = mail !== null ? plan.actions[mail] : null
  return (
    <section>
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-indigo-700 dark:text-indigo-300">
          <MessageCircleQuestion className="size-3.5" /> Plan for your question
        </div>
        <div className="mt-1 text-sm text-slate-500">{plan.question}</div>
        <p className="mt-2 text-lg font-semibold leading-snug tracking-tight">{plan.headline}</p>
        <div className="mt-3 flex items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div className="h-full rounded-full bg-indigo-500 transition-all duration-500" style={{ width: `${(100 * done) / Math.max(plan.actions.length, 1)}%` }} />
          </div>
          <span className="text-xs font-medium tabular-nums text-slate-500">
            {done} of {plan.actions.length} planned
          </span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {plan.actions.map((action, index) => {
          const saved = scheduled(index)
          const example = action.example_id ? plan.examples.find((e) => e.contribution_id === action.example_id) : undefined
          const email = action.partner?.email
          return (
            <article key={action.title} className="tone-bar flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900" style={toneStyle(action.tone)}>
              <div className="flex items-start gap-3">
                <ActionIcon action={action} />
                <div className="min-w-0 flex-1">
                  <div className="tone-text text-[11px] font-semibold uppercase tracking-wider" style={toneStyle(action.tone)}>
                    {ACTION_META[action.kind].label}
                  </div>
                  <h3 className="text-base font-semibold leading-snug">{action.title}</h3>
                  <p className="mt-1 line-clamp-3 text-sm text-slate-600 dark:text-slate-300">{action.why}</p>
                </div>
              </div>
              <div className="mt-auto flex flex-wrap items-center gap-2 pt-4">
                {saved ? (
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200">
                    <CheckCircle2 className="size-3.5" /> Planned for {saved.slot.date} · {saved.slot.start}
                  </span>
                ) : action.kind === 'email' ? (
                  <button onClick={() => setMail(index)} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500">
                    {mailed.includes(index) ? <CheckCircle2 className="size-3.5" /> : <Mail className="size-3.5" />} {mailed.includes(index) ? 'Opened in email · draft again' : 'Draft email'}
                  </button>
                ) : action.kind === 'team_event' ? (
                  <button
                    onClick={() => onEvent({ title: action.event?.title, invitation: action.event?.invitation, origin: originFor(plan, action, index) })}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
                  >
                    <Utensils className="size-3.5" /> Plan the lunch
                  </button>
                ) : action.kind === 'room' ? (
                  <button
                    onClick={() =>
                      onRoom({
                        title: action.room?.title ?? action.title,
                        agenda: action.room?.agenda ?? action.why,
                        description: `${action.why}\n\nFrom Echo's answer to: "${plan.question}"`,
                        origin: originFor(plan, action, index),
                      })
                    }
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
                  >
                    <DoorOpen className="size-3.5" /> Find a room
                  </button>
                ) : (
                  <button
                    onClick={() => onSchedule(prefillFor(plan, action, index, managerId))}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
                  >
                    <CalendarCheck className="size-3.5" /> {action.kind === 'recognize' || action.kind === 'one_to_one' ? 'Schedule 1:1' : action.kind === 'plan' || action.kind === 'goal' ? 'Schedule session' : 'Schedule meeting'}
                  </button>
                )}
                {example && (
                  <button
                    onClick={() => setDraft(example)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium hover:border-indigo-300 dark:border-slate-700"
                  >
                    <PenLine className="size-3.5" /> Draft note
                  </button>
                )}
                {email && (
                  <a
                    href={mailtoUrl(email, action.title, `${action.why}\n\n`)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium hover:border-indigo-300 dark:border-slate-700"
                  >
                    <Mail className="size-3.5" /> Email {action.partner?.name?.split(' ')[0]}
                  </a>
                )}
              </div>
            </article>
          )
        })}
      </div>
      <p className="mt-3 text-xs text-slate-500">Built from the answer. Nothing is sent or booked until you choose; meetings are saved in this prototype only.</p>
      {draft && <DraftNoteDialog example={draft} onClose={() => setDraft(null)} />}
      {mailAction && mail !== null && (
        <EmailDialog
          subject={mailAction.email?.subject ?? mailAction.title}
          body={mailAction.email?.body ?? `${mailAction.why}\n\n`}
          to={mailAction.email?.to ?? mailAction.partner?.email ?? undefined}
          onClose={() => setMail(null)}
          onSent={() => markMailed(mail)}
        />
      )}
    </section>
  )
}
