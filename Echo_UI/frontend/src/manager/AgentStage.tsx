import clsx from 'clsx'
import { AlertTriangle, Check, Maximize2, Minimize2 } from 'lucide-react'
import type { CSSProperties } from 'react'
import { ALL_AGENTS, agentLabel, type AgentName } from '../lib/agents'
import { visibleAgents, type AgentState } from '../lib/events'

/** Plain roles: how the agents are introduced to managers (the name itself comes from agentLabel). */
export const ROLES: Record<AgentName, { title: string; line: string }> = {
  Original: { title: 'The brief', line: 'Plans the answer and writes your brief' },
  Cherry: { title: 'Work records', line: 'Finds the work and feedback in the records' },
  Vanilla: { title: 'Survey results', line: 'Reads what the team says, as themes only' },
  Lime: { title: 'Charts', line: 'Shows the evidence as a chart' },
  ZeroSugar: { title: 'Fact-check', line: 'Re-checks every claim and flags conflicts' },
  Discovery: { title: 'Hidden work', line: 'Finds work that crosses teams, checked by code' },
}

// The agents sit on the Echo E (percent of the stage box): the spine on the left, three arms to the right.
const SPINE = 20
const TIP = 78
const ROWS = [16, 48, 80]
const SEATS: Record<AgentName, { x: number; y: number }> = {
  Discovery: { x: SPINE, y: ROWS[0] },
  Original: { x: SPINE, y: ROWS[1] },
  ZeroSugar: { x: SPINE, y: ROWS[2] },
  Cherry: { x: TIP, y: ROWS[0] },
  Vanilla: { x: TIP, y: ROWS[1] },
  Lime: { x: TIP, y: ROWS[2] },
}
// The stretch of the E that joins each agent to the coordinator in the middle of the spine.
const LINKS: Partial<Record<AgentName, [number, number, number, number]>> = {
  Cherry: [SPINE, ROWS[0], TIP, ROWS[0]],
  Vanilla: [SPINE, ROWS[1], TIP, ROWS[1]],
  Lime: [SPINE, ROWS[2], TIP, ROWS[2]],
  Discovery: [SPINE, ROWS[1], SPINE, ROWS[0]],
  ZeroSugar: [SPINE, ROWS[1], SPINE, ROWS[2]],
}
const E_STROKES: [number, number, number, number][] = [
  [SPINE, ROWS[0], SPINE, ROWS[2]],
  [SPINE, ROWS[0], TIP, ROWS[0]],
  [SPINE, ROWS[1], TIP, ROWS[1]],
  [SPINE, ROWS[2], TIP, ROWS[2]],
]

/** Which agent is working right now: a specialist if one is active, otherwise the coordinator. */
function runningAgent(states: Record<AgentName, AgentState>): AgentName | null {
  const active = ALL_AGENTS.filter((a) => states[a.name].status === 'active').map((a) => a.name)
  return active.find((name) => name !== 'Original') ?? active[0] ?? null
}

export default function AgentStage({
  states,
  activity,
  busy,
  headline,
  outcomes,
  onMinimize,
}: {
  states: Record<AgentName, AgentState>
  activity: Partial<Record<AgentName, string>>
  busy: boolean
  headline?: string
  /** What each agent contributed to the finished answer, shown once the run is over. */
  outcomes?: Partial<Record<AgentName, string>>
  onMinimize?: () => void
}) {
  const running = busy ? runningAgent(states) : null
  const focus: AgentName = running ?? 'Original'
  const agents = visibleAgents(states)
  const color = (name: AgentName) => ALL_AGENTS.find((a) => a.name === name)!.color

  return (
    <div className="relative h-[520px] overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-white to-indigo-50/70 sm:h-[560px] dark:border-slate-800 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900">
      {/* one soft wash behind the agent working now, in its colour */}
      <div
        className="pointer-events-none absolute size-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60 blur-3xl transition-all duration-700 dark:opacity-25"
        style={{ left: `${SEATS[focus].x}%`, top: `${SEATS[focus].y}%`, background: `color-mix(in srgb, ${color(focus)} 22%, transparent)` }}
      />

      {/* The E itself, then each agent's stretch of it: tinted when done, flowing while it works */}
      <svg className="absolute inset-0 size-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
        {E_STROKES.map(([x1, y1, x2, y2], i) => (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth={14} strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        ))}
        {agents.map((agent) => {
          const link = LINKS[agent.name]
          if (!link) return null
          const done = states[agent.name].status === 'done'
          const working = running === agent.name
          if (!done && !working) return null
          const [x1, y1, x2, y2] = link
          return (
            <line
              key={agent.name}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={agent.color}
              strokeWidth={working ? 3 : 2.5}
              strokeOpacity={working ? 0.95 : 0.6}
              strokeDasharray={working ? '6 8' : undefined}
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
              className={working ? 'flow-dash' : undefined}
            />
          )
        })}
      </svg>

      {agents.map((agent) => {
        const state = states[agent.name]
        const p = SEATS[agent.name]
        const lead = agent.name === focus
        const active = state.status === 'active' && busy && (agent.name === running || (agent.name === 'Original' && !running))
        const dim = busy && !lead && state.status === 'idle'
        const status = busy
          ? activity[agent.name] ?? (state.status === 'waiting' ? 'Waiting' : state.status === 'done' ? 'Done' : 'Standing by')
          : outcomes?.[agent.name] ?? ROLES[agent.name].line
        return (
          <div
            key={agent.name}
            className={clsx(
              'absolute flex -translate-x-1/2 flex-col items-center text-center transition-all duration-700 ease-in-out',
              // shift up by half the circle, so the circle (not the whole block) is centred on its seat
              lead ? 'z-10 w-40 -translate-y-8 sm:w-52 sm:-translate-y-9' : 'w-32 -translate-y-6 sm:w-44 sm:-translate-y-7',
              dim && 'opacity-45',
            )}
            style={{ left: `${p.x}%`, top: `${p.y}%` }}
          >
            <div
              className={clsx(
                'agent-tint relative grid place-items-center rounded-full ring-[6px] ring-white transition-all duration-700 dark:ring-slate-900',
                lead ? 'size-16 sm:size-[72px]' : 'size-12 sm:size-14',
              )}
              style={{ '--agent': agent.color, boxShadow: active ? `0 0 0 10px color-mix(in srgb, ${agent.color} 18%, transparent)` : undefined } as CSSProperties}
            >
              {active && <span className="absolute inset-0 animate-ping rounded-full opacity-20" style={{ background: agent.color }} />}
              <agent.icon className={clsx('transition-all duration-700', lead ? 'size-7 sm:size-8' : 'size-5 sm:size-6')} />
              {state.status === 'done' && (
                <span className="absolute -right-0.5 -top-0.5 grid size-5 place-items-center rounded-full bg-indigo-500 text-white ring-2 ring-white dark:ring-slate-900">
                  <Check className="size-3" strokeWidth={3} />
                </span>
              )}
              {state.status === 'failed' && (
                <span className="absolute -right-0.5 -top-0.5 grid size-5 place-items-center rounded-full bg-rose-400 text-white ring-2 ring-white dark:ring-slate-900">
                  <AlertTriangle className="size-3" strokeWidth={3} />
                </span>
              )}
            </div>
            <div className="mt-1.5 flex flex-col items-center rounded-xl bg-white/85 px-2 pb-0.5 backdrop-blur-[2px] dark:bg-slate-900/85">
            {active && <div className="mt-1 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-200">Working now</div>}
            <div className={clsx('font-semibold leading-tight', active ? 'mt-1 text-base' : 'mt-0.5 text-sm')}>{agent.label}</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">{ROLES[agent.name].title}</div>
            <div
              className={clsx('mt-1 hidden min-h-8 text-xs leading-snug sm:block', active ? 'font-medium text-slate-700 dark:text-slate-200' : 'text-slate-500 dark:text-slate-400')}
            >
              {status}
            </div>
            </div>
          </div>
        )
      })}

      {onMinimize && (
        <button
          onClick={onMinimize}
          className="absolute right-3 top-3 z-20 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white/90 px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur transition hover:border-indigo-300 hover:text-indigo-800 dark:border-slate-700 dark:bg-slate-900/90 dark:text-slate-300"
          aria-label="Minimize the agent view"
        >
          <Minimize2 className="size-3.5" /> Minimize
        </button>
      )}

      {headline && (
        <div className="absolute inset-x-0 bottom-3 text-center text-xs text-slate-500 dark:text-slate-400" aria-live="polite">
          {headline}
        </div>
      )}
    </div>
  )
}

/** The agents folded into one line: small agents, the one working now highlighted. */
export function AgentStageMini({
  states,
  activity,
  busy,
  headline,
  onExpand,
}: {
  states: Record<AgentName, AgentState>
  activity: Partial<Record<AgentName, string>>
  busy: boolean
  headline?: string
  onExpand: () => void
}) {
  const running = busy ? runningAgent(states) : null
  const agents = visibleAgents(states)
  const line = running ? `${agentLabel(running)}: ${activity[running] ?? ROLES[running].title}` : headline
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-gradient-to-r from-white to-indigo-50/60 px-3 py-2.5 sm:px-4 dark:border-slate-800 dark:from-slate-900 dark:to-slate-900">
      <div className="flex shrink-0 -space-x-1.5">
        {agents.map((agent) => {
          const state = states[agent.name]
          const on = agent.name === running
          return (
            <div
              key={agent.name}
              title={`${agent.label} · ${ROLES[agent.name].title}`}
              className={clsx(
                'agent-tint relative grid place-items-center rounded-full ring-2 ring-white transition-all duration-500 dark:ring-slate-900',
                on ? 'z-10 size-9' : 'size-7',
                busy && !on && state.status === 'idle' && 'opacity-45',
              )}
              style={{ '--agent': agent.color } as CSSProperties}
            >
              {on && <span className="absolute inset-0 animate-ping rounded-full opacity-25" style={{ background: agent.color }} />}
              <agent.icon className={on ? 'size-4' : 'size-3.5'} />
              {state.status === 'done' && (
                <span className="absolute -bottom-0.5 -right-0.5 grid size-3 place-items-center rounded-full bg-indigo-500 text-white ring-1 ring-white dark:ring-slate-900">
                  <Check className="size-2" strokeWidth={3.5} />
                </span>
              )}
            </div>
          )
        })}
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-xs font-semibold text-slate-700 dark:text-slate-200">{agents.length > 5 ? 'Six' : 'Five'} agents</div>
        <div className="truncate text-xs text-slate-500 dark:text-slate-400" aria-live="polite">{line}</div>
      </div>
      <button
        onClick={onExpand}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:border-indigo-300 hover:text-indigo-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
        aria-label="Expand the agent view"
      >
        <Maximize2 className="size-3.5" /> Expand
      </button>
    </div>
  )
}
