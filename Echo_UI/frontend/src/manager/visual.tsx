import {
  AlarmClock,
  ArrowLeftRight,
  Award,
  CircleDollarSign,
  ClipboardList,
  Clock,
  DoorOpen,
  Mail,
  Utensils,
  EyeOff,
  Handshake,
  MessagesSquare,
  RotateCcw,
  SearchX,
  Target,
  Users,
  type LucideIcon,
} from 'lucide-react'
import type { CSSProperties } from 'react'
import type { AnswerAction, Artifact, Tile, VisTone } from '../lib/api'

// Same rough sizing as the backend (offline.py): an assumed pay rate, not company data, and hours in a full-time quarter.
export const ASSUMED_HOURLY_COST = 45
export const FTE_QUARTER_HOURS = 520
export const dollars = (hours: number) => {
  const amount = hours * ASSUMED_HOURLY_COST
  return amount < 10000 ? `$${(Math.round(amount / 100) * 100).toLocaleString()}` : `$${Math.round(amount / 1000).toLocaleString()}k`
}

/** One colour per meaning, shared with the Gaps bar, so a colour always says the same thing. */
export const TONE_COLOR: Record<VisTone, string> = {
  no_praise: 'var(--vis-no-praise)',
  not_passed: 'var(--vis-not-passed)',
  unrecognized: 'var(--vis-unrecognized)',
  recognized: 'var(--vis-recognized)',
  money: 'var(--vis-money)',
  neutral: 'var(--vis-neutral)',
}

const TILE_ICON: Record<string, LucideIcon> = {
  eye: EyeOff,
  hours: Clock,
  cost: CircleDollarSign,
  award: Award,
  goal: Target,
  search: SearchX,
  late: AlarmClock,
  rework: RotateCcw,
  people: Users,
}

export const ACTION_META: Record<AnswerAction['kind'], { icon: LucideIcon; label: string }> = {
  recognize: { icon: Award, label: 'Recognize' },
  one_to_one: { icon: MessagesSquare, label: '1:1 conversation' },
  partner: { icon: Handshake, label: 'Partner team' },
  handoff: { icon: ArrowLeftRight, label: 'Handoff' },
  plan: { icon: ClipboardList, label: 'Planning' },
  goal: { icon: Target, label: 'Goals' },
  team_event: { icon: Utensils, label: 'Team event' },
  room: { icon: DoorOpen, label: 'Meeting room' },
  email: { icon: Mail, label: 'Email' },
}

const tint = (tone: VisTone) => ({ '--tone': TONE_COLOR[tone] }) as CSSProperties

/** The big numbers at the top of an answer: icon, value, one short label. */
export function Tiles({ tiles }: { tiles: Tile[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {tiles.map((tile) => {
        const Icon = TILE_ICON[tile.icon] ?? Users
        return (
          <div key={tile.label} className="tone-card rounded-2xl p-4" style={tint(tile.tone)}>
            <span className="tone-icon grid size-9 place-items-center rounded-xl">
              <Icon className="size-[18px]" />
            </span>
            <div className="tone-text mt-3 text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl">{tile.value}</div>
            <div className="mt-0.5 text-xs leading-snug text-slate-600 dark:text-slate-400">{tile.label}</div>
          </div>
        )
      })}
    </div>
  )
}

/** A small coloured icon for an action kind. */
export function ActionIcon({ action, size = 'md' }: { action: AnswerAction; size?: 'sm' | 'md' }) {
  const Icon = ACTION_META[action.kind].icon
  return (
    <span className={size === 'sm' ? 'tone-icon grid size-7 shrink-0 place-items-center rounded-lg' : 'tone-icon grid size-10 shrink-0 place-items-center rounded-xl'} style={tint(action.tone)}>
      <Icon className={size === 'sm' ? 'size-3.5' : 'size-5'} />
    </span>
  )
}

export const toneStyle = tint

/** For live answers: route a written next step to the tool that fits it. */
function kindOf(step: string): AnswerAction['kind'] {
  if (/lunch|dinner|team (event|outing|social)|celebrat|take (the|your) team/i.test(step)) return 'team_event'
  if (/email|write to|send (a|the) (note|message)|let (the|your) team know/i.test(step)) return 'email'
  if (/(book|find|reserve) a room|workshop|team (conversation|discussion|meeting)|hold a/i.test(step)) return 'room'
  if (/one-to-one|1:1/i.test(step)) return 'one_to_one'
  return 'plan'
}

/** Actions for an answer: the ones Echo wrote for it, or (for live answers) built from its examples and next steps. */
export function answerActions(artifact: Artifact | null | undefined): AnswerAction[] {
  if (!artifact) return []
  if (artifact.actions?.length) return artifact.actions
  const fromPeople: AnswerAction[] = (artifact.examples ?? []).slice(0, 3).map((e) => ({
    kind: 'recognize',
    title: `Recognize ${e.name.split(' ')[0]}`,
    why: `Helped ${e.team_helped}: ${e.outcome.replace(/\.$/, '')}.`,
    tone: e.praise_reached_you ? 'unrecognized' : 'not_passed',
    person: { id: e.employee_id, name: e.name },
    partner_team: e.team_helped,
    example_id: e.contribution_id,
  }))
  const fromSteps: AnswerAction[] = (artifact.next_steps ?? []).slice(0, 3).map((step) => ({ kind: kindOf(step), title: step.split(/[:.]/)[0], why: step, tone: 'neutral' }))
  return [...fromPeople, ...fromSteps].slice(0, 5)
}

/** What the Action Center needs to build a plan from one answer. */
export type AnswerPlan = { runId: string; question: string; headline: string; actions: AnswerAction[]; examples: NonNullable<Artifact['examples']> }

export function planFrom(runId: string, question: string, artifact: Artifact): AnswerPlan {
  const headline = artifact.headline ?? artifact.answer.replace(/\s*\[[A-Za-z]+\d*(?::[A-Za-z0-9_-]+)?\]/g, '').split(/(?<=\.)\s/)[0]
  return { runId, question, headline, actions: answerActions(artifact), examples: artifact.examples ?? [] }
}
