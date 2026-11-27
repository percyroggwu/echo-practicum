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

// The agents sit on the Echo logo: three large hexagons down the spine, three smaller ones at the arm tips
// (the middle arm is shorter). Coordinates are the logo's own (a 1024 square), cropped with room for labels.
const VIEW = { x: -60, y: 100, w: 1210, h: 820 }
const NODES: Record<AgentName, { x: number; y: number; big: boolean; side: 'left' | 'right' }> = {
  Discovery: { x: 300, y: 210, big: true, side: 'left' },
  Original: { x: 300, y: 512, big: true, side: 'left' },
  ZeroSugar: { x: 300, y: 815, big: true, side: 'left' },
  Cherry: { x: 790, y: 210, big: false, side: 'right' },
  Vanilla: { x: 690, y: 512, big: false, side: 'right' },
  Lime: { x: 790, y: 815, big: false, side: 'right' },
}
const S = { top: NODES.Discovery, mid: NODES.Original, bot: NODES.ZeroSugar }
const T = { top: NODES.Cherry, mid: NODES.Vanilla, bot: NODES.Lime }
type P = { x: number; y: number }

const pctX = (x: number) => ((x - VIEW.x) / VIEW.w) * 100
const pctY = (y: number) => ((y - VIEW.y) / VIEW.h) * 100

/** A pointy-top hexagon, as in the logo. */
function hex(c: P, r: number) {
  return Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 90)
    return `${(c.x + r * Math.cos(a)).toFixed(1)},${(c.y + r * Math.sin(a)).toFixed(1)}`
  }).join(' ')
}

/** The logo's fine crossing lines: a bundle of gentle curves from one hexagon to another. */
function fibers(a: P, b: P, n: number, spread: number, bend: number) {
  const mx = (a.x + b.x) / 2
  const my = (a.y + b.y) / 2
  const len = Math.hypot(b.x - a.x, b.y - a.y)
  const nx = -(b.y - a.y) / len
  const ny = (b.x - a.x) / len
  return Array.from({ length: n }, (_, i) => {
    const k = n === 1 ? 0 : i / (n - 1) - 0.5
    const off = bend + k * spread
    return `M${a.x} ${a.y} Q${(mx + nx * off).toFixed(1)} ${(my + ny * off).toFixed(1)} ${b.x} ${b.y}`
  })
}

// Each agent's link back to the Coordinator: the spine for Discovery and the Reviewer, the middle arm for
// the Text analyst, and the crossing lines for Text-to-SQL and the Chart builder (as drawn in the logo).
const LINK: Partial<Record<AgentName, string>> = {
  Discovery: `M${S.mid.x} ${S.mid.y} L${S.top.x} ${S.top.y}`,
  ZeroSugar: `M${S.mid.x} ${S.mid.y} L${S.bot.x} ${S.bot.y}`,
  Vanilla: `M${S.mid.x} ${S.mid.y} L${T.mid.x} ${T.mid.y}`,
  Cherry: fibers(S.mid, T.top, 1, 0, 6)[0],
  Lime: fibers(S.mid, T.bot, 1, 0, -6)[0],
}

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
  const agents = visibleAgents(states)
  const shown = new Set(agents.map((a) => a.name))
  // The amber hexagon is whoever is working now (the logo's accent); at rest it is the Text analyst, as in the logo.
  const hot: AgentName = running ?? 'Vanilla'

  return (
    <div className="echo-e relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-white to-[#f3f6ee] px-3 pb-10 pt-6 dark:border-slate-800 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900">
      <div className="relative mx-auto aspect-[1210/820] w-full max-w-[860px]">
        <svg className="absolute inset-0 size-full" viewBox={`${VIEW.x} ${VIEW.y} ${VIEW.w} ${VIEW.h}`} aria-hidden>
          {/* the crossing lines of the logo */}
          <g fill="none" stroke="var(--e-fiber)" strokeWidth={1.6} strokeLinecap="round">
            {fibers(S.top, T.mid, 12, 110, 40).map((d, i) => <path key={`a${i}`} d={d} />)}
            {fibers(S.mid, T.top, 6, 18, 6).map((d, i) => <path key={`b${i}`} d={d} />)}
            {fibers(S.mid, T.bot, 12, 110, -40).map((d, i) => <path key={`c${i}`} d={d} />)}
            {fibers(S.bot, T.mid, 6, 18, -6).map((d, i) => <path key={`d${i}`} d={d} />)}
          </g>
          {/* the E: spine and three arms */}
          <g stroke="var(--e-bar)" strokeWidth={40}>
            <line x1={S.top.x} y1={S.top.y} x2={S.bot.x} y2={S.bot.y} />
            <line x1={S.top.x} y1={S.top.y} x2={T.top.x} y2={T.top.y} />
            <line x1={S.mid.x} y1={S.mid.y} x2={T.mid.x} y2={T.mid.y} />
            <line x1={S.bot.x} y1={S.bot.y} x2={T.bot.x} y2={T.bot.y} />
          </g>
          {/* each agent's link: flowing while it works, tinted once it is done */}
          {agents.map((agent) => {
            const d = LINK[agent.name]
            const done = states[agent.name].status === 'done'
            const working = running === agent.name
            if (!d || (!done && !working)) return null
            return (
              <path
                key={agent.name}
                d={d}
                fill="none"
                stroke={working ? 'var(--e-hot)' : 'var(--e-done)'}
                strokeWidth={working ? 12 : 8}
                strokeLinecap="round"
                strokeDasharray={working ? '26 22' : undefined}
                className={working ? 'flow-dash-e' : undefined}
              />
            )
          })}
          {/* the hexagons */}
          {(Object.keys(NODES) as AgentName[]).map((name) => {
            const n = NODES[name]
            const R = n.big ? 92 : 74
            const isHot = name === hot
            const on = shown.has(name)
            const dim = !on || (busy && running !== name && states[name].status === 'idle')
            return (
              <g key={name} opacity={dim ? 0.4 : 1} className="transition-opacity duration-500">
                {isHot && busy && <polygon points={hex(n, R + 26)} fill="var(--e-hot)" opacity={0.18} className="animate-pulse" />}
                <polygon points={hex(n, R)} fill={isHot ? 'var(--e-hot)' : n.big ? 'var(--e-spine)' : 'var(--e-tip)'} />
                <polygon points={hex(n, R / 2)} fill={isHot ? 'var(--e-hot-in)' : n.big ? 'var(--e-spine-in)' : 'var(--e-tip-in)'} />
              </g>
            )
          })}
        </svg>

        {/* icons on the hexagons, and each agent's name beside its hexagon */}
        {agents.map((agent) => {
          const n = NODES[agent.name]
          const state = states[agent.name]
          const isHot = agent.name === hot
          const active = state.status === 'active' && busy && (agent.name === running || (agent.name === 'Original' && !running))
          const dim = busy && running !== agent.name && state.status === 'idle'
          const status = busy
            ? activity[agent.name] ?? (state.status === 'waiting' ? 'Waiting' : state.status === 'done' ? 'Done' : 'Standing by')
            : outcomes?.[agent.name] ?? ROLES[agent.name].line
          const gap = (n.big ? 92 : 74) + 22
          return (
            <div key={agent.name} className={clsx('transition-opacity duration-500', dim && 'opacity-45')}>
              <span
                className={clsx('absolute grid -translate-x-1/2 -translate-y-1/2 place-items-center', isHot || !n.big ? 'text-[#26331f]' : 'text-white')}
                style={{ left: `${pctX(n.x)}%`, top: `${pctY(n.y)}%` }}
              >
                <agent.icon className={n.big ? 'size-[18px] sm:size-5' : 'size-4 sm:size-[18px]'} />
                {state.status === 'done' && (
                  <span className="absolute -right-5 -top-5 grid size-4 place-items-center rounded-full bg-[#4f5d2f] text-white ring-2 ring-white sm:-right-6 sm:-top-6 sm:size-5 dark:ring-slate-900">
                    <Check className="size-2.5 sm:size-3" strokeWidth={3} />
                  </span>
                )}
                {state.status === 'failed' && (
                  <span className="absolute -right-5 -top-5 grid size-4 place-items-center rounded-full bg-rose-500 text-white ring-2 ring-white sm:size-5 dark:ring-slate-900">
                    <AlertTriangle className="size-2.5 sm:size-3" strokeWidth={3} />
                  </span>
                )}
              </span>
              <div
                className={clsx('absolute w-[30%] -translate-y-1/2', n.side === 'left' ? 'text-right' : 'text-left')}
                style={n.side === 'left' ? { right: `${100 - pctX(n.x - gap)}%`, top: `${pctY(n.y)}%` } : { left: `${pctX(n.x + gap)}%`, top: `${pctY(n.y)}%` }}
              >
                {active && <div className="mb-0.5 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800 dark:bg-amber-500/15 dark:text-amber-200">Working now</div>}
                <div className={clsx('font-semibold leading-tight', active ? 'text-sm sm:text-base' : 'text-xs sm:text-sm')}>{agent.label}</div>
                <div className="text-[10.5px] text-slate-500 sm:text-[11px] dark:text-slate-400">{ROLES[agent.name].title}</div>
                <div className={clsx('mt-0.5 hidden text-xs leading-snug sm:block', active ? 'font-medium text-slate-700 dark:text-slate-200' : 'text-slate-500 dark:text-slate-400')}>{status}</div>
              </div>
            </div>
          )
        })}
      </div>

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
