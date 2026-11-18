import { CalendarCheck, Check, CheckCircle2, DoorOpen, Mail, MessageCircleQuestion, PenLine, Sparkles, Utensils } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { AnswerAction, Example } from '../lib/api'
import type { ActionOrigin, EchoAction, MeetingPurpose, MeetingRecord, Participant, SchedulerPrefill, TimeSlot } from './actionTypes'
import { DiscoveryDecision } from './DiscoverySection'
import { DraftNoteDialog, OWN_WORDS_MIN, OwnWords, SendButtons, withOwnWords } from './Brief'
import { agendaFor } from './MeetingScheduler'
import { ROOMS } from './mockActionData'
import { formatDate, formatTime, isRoomFree, overlaps, suggestedSlots, weekDates } from './schedulingUtils'
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
  const [own, setOwn] = useState('')
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <div className="absolute inset-0 bg-slate-950/40" onClick={onClose} />
      <div className="slide-in relative max-h-[calc(100%-2rem)] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5 shadow-2xl dark:bg-slate-900">
        <div className="flex items-center gap-2 text-base font-semibold">
          <Mail className="size-4 text-indigo-500" /> {subject}
        </div>
        <p className="mt-1 text-xs text-slate-500">Edit anything, then send it from your own email. Echo never sends anything.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} className="mt-3 w-full resize-y rounded-xl border border-slate-200 bg-white p-3 text-sm leading-relaxed outline-none focus:border-indigo-400 dark:border-slate-700 dark:bg-slate-950" />
        <OwnWords id="own-words-email" value={own} onChange={setOwn} />
        <div className="mt-3 flex flex-wrap justify-end gap-2">
          <button onClick={onClose} className="rounded-xl px-3.5 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            Close
          </button>
          <SendButtons ready={own.trim().length >= OWN_WORDS_MIN} text={withOwnWords(text, own)} to={to ?? ''} subject={subject} onSent={onSent} />
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

/** A meeting Echo lined up but hasn't saved: the manager confirms the whole set, or picks each one by hand. */
export type ProposedMeeting = Omit<MeetingRecord, 'id' | 'createdAt'> & { person: string }

// The week the demo calendars cover (the scheduler opens on the same week).
const PLAN_WEEK = '2026-11-16'

/** Lines up each open 1:1 from the answer at the first time everyone is free, in the smallest free room that fits. */
function proposeMeetings(plan: AnswerPlan, managerId: string, actions: EchoAction[], isDone: (index: number) => boolean): ProposedMeeting[] {
  const taken: EchoAction[] = [...actions]
  const out: ProposedMeeting[] = []
  plan.actions.forEach((action, index) => {
    if (!action.person || isDone(index) || !(action.kind === 'recognize' || action.kind === 'one_to_one')) return
    const prefill = prefillFor(plan, action, index, managerId)
    const people = prefill.participantIds ?? []
    for (const slot of suggestedSlots(people, weekDates(PLAN_WEEK), 30, taken, 80)) {
      // The manager is in every one of these meetings, so none may overlap another meeting of theirs.
      if (taken.some((a) => a.status !== 'Cancelled' && overlaps(a.slot, slot))) continue
      const room = ROOMS.filter((r) => r.capacity >= people.length + 1 && isRoomFree(r.id, slot, taken)).sort((a, b) => a.capacity - b.capacity)[0]
      if (!room) continue
      const first = action.person.name.split(' ')[0]
      const purpose = prefill.purpose ?? 'Recognition discussion'
      const meeting: ProposedMeeting = {
        kind: 'meeting',
        managerId,
        person: action.person.name,
        title: action.title,
        purpose,
        description: prefill.description ?? action.why,
        participantIds: people,
        slot,
        duration: 30,
        location: { type: 'room', roomId: room.id, label: room.name },
        agenda: agendaFor(purpose, action.title, prefill.description ?? action.why, first),
        status: 'Planned',
        origin: prefill.origin!,
      }
      out.push(meeting)
      // Later proposals must not land on the same time or room.
      taken.push({ ...meeting, id: `proposal-${index}`, createdAt: '' })
      break
    }
  })
  return out
}

const when = (slot: TimeSlot) => `${formatDate(slot.date)}, ${formatTime(slot.start)}`

/** "Do it for me": Echo sets up every open 1:1, shows the list, and saves only when the manager confirms. */
function DoItForMe({ proposals, onConfirm }: { proposals: ProposedMeeting[]; onConfirm: (meetings: ProposedMeeting[]) => void }) {
  const [open, setOpen] = useState(false)
  if (!proposals.length) return null
  return (
    <div className="mt-4 rounded-2xl border border-indigo-200 bg-indigo-50/70 p-4 dark:border-indigo-500/30 dark:bg-indigo-500/10">
      {!open ? (
        <div className="flex flex-wrap items-center gap-3">
          <Sparkles className="size-5 shrink-0 text-indigo-600 dark:text-indigo-300" />
          <p className="min-w-0 flex-1 text-sm">
            <b>Short on time?</b> Echo can line up {proposals.length === 1 ? 'the 1:1' : `all ${proposals.length} 1:1s`} for you. You check them before anything is saved.
          </p>
          <button onClick={() => setOpen(true)} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500">
            <Sparkles className="size-3.5" /> Do it for me
          </button>
        </div>
      ) : (
        <>
          <h3 className="flex items-center gap-2 font-semibold">
            <Sparkles className="size-4 text-indigo-600 dark:text-indigo-300" /> Here's what Echo lined up. Agree?
          </h3>
          <ul className="mt-3 divide-y divide-indigo-100 rounded-xl bg-white dark:divide-slate-800 dark:bg-slate-900">
            {proposals.map((m) => (
              <li key={m.origin.insightId} className="flex flex-wrap items-center gap-x-3 gap-y-0.5 px-3 py-2.5 text-sm">
                <CalendarCheck className="size-4 shrink-0 text-indigo-500" />
                <span className="min-w-0 flex-1 font-medium">1:1 with {m.person}</span>
                <span className="text-slate-600 dark:text-slate-300">{when(m.slot)}</span>
                <span className="text-xs text-slate-500">{m.location.label}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-500">Each one gets a room and an agenda written from the answer.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button onClick={() => onConfirm(proposals)} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-indigo-500">
              <Check className="size-4" /> Yes, save {proposals.length === 1 ? 'it' : 'all'}
            </button>
            <button onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900">
              No, I'll pick each one
            </button>
          </div>
        </>
      )}
    </div>
  )
}

/** The Action Center's plan for one answer: one card per action, each opening the right tool already filled in. */
export default function AnswerPlanSection({
  plan,
  managerId,
  actions,
  onSchedule,
  onEvent,
  onRoom,
  onConfirmAll,
}: {
  plan: AnswerPlan
  managerId: string
  actions: EchoAction[]
  onSchedule: (prefill: SchedulerPrefill) => void
  onEvent: (prefill: EventPrefill) => void
  onRoom: (prefill: RoomPrefill) => void
  /** Saves the meetings Echo lined up, once the manager agrees. */
  onConfirmAll: (meetings: ProposedMeeting[]) => void
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
  const proposals = useMemo(
    () => proposeMeetings(plan, managerId, actions, (i) => !!scheduled(i)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [plan, managerId, actions],
  )
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

      <DoItForMe key={proposals.map((p) => p.origin.insightId).join()} proposals={proposals} onConfirm={onConfirmAll} />

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
              {action.discovery_action_id && <DiscoveryDecision managerId={managerId} runId={plan.runId} sourceActionId={action.discovery_action_id} />}
            </article>
          )
        })}
      </div>
      <p className="mt-3 text-xs text-slate-500">Built from the answer. Nothing happens without your approval.</p>
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
