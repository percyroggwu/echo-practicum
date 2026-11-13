import clsx from 'clsx'
import { ArrowRight, Award, CalendarCheck, ChevronDown, ChevronUp, Gauge, GraduationCap, Handshake, History, LogOut, MessagesSquare, Moon, Newspaper, PanelLeft, Search, ShieldAlert, ShieldCheck, Sparkles, Square, Sun, Trash2, Users, WandSparkles, Wrench, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTheme } from '../components/Layout'
import { AGENTS } from '../lib/agents'
import { api, type Artifact, type Manager, type Meta } from '../lib/api'
import { agentStates, useRunEvents } from '../lib/events'
import { useAsync } from '../lib/useAsync'
import AgentStage from './AgentStage'
import ActionCenter from './ActionCenter'
import type { SchedulerPrefill } from './actionTypes'
import { agentActivity } from './AgentStrip'
import Brief, { BriefPending } from './Brief'
import Presenter from './Presenter'
import RecognitionQueue from './RecognitionQueue'
import Trust from './Trust'
import TeamPulse from './TeamPulse'
import { loadConversations, loadDone, loadManagerCode, loadWatch, saveConversations, saveDone, saveManagerCode, saveWatch, type Conversation, type Message, type Watched } from './store'

const SUGGESTED = [
  "Is my team's cross-team work being recognized?",
  'How is recognition trending for my team?',
  "What do this quarter's recognition metrics suggest?",
  'Show Recognition over eight quarters.',
  'Which weeks exceed available project hours?',
  'How many cross-team contributions lack a recognition note?',
  'Which survey area changed most over the last year?',
]

const GUARDRAIL_EXAMPLE = 'Who complained about recognition in the last survey?'

const PERIODS = [
  { id: 'all', label: 'All data (Oct 2024 – Sep 2026)', start: '2024-10-01', end: '2026-09-30' },
  { id: 'year', label: 'Last 12 months', start: '2025-10-01', end: '2026-09-30' },
  { id: 'quarter', label: 'Last quarter (Jul – Sep 2026)', start: '2026-07-01', end: '2026-09-30' },
]

function ThemeButton() {
  const [dark, setDark] = useTheme()
  return (
    <button onClick={() => setDark(!dark)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Toggle light or dark mode">
      {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  )
}

/* ---------------- entry ---------------- */

function Entry({ onEnter }: { onEnter: (manager: Manager) => void }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [checking, setChecking] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!code.trim()) return
    setChecking(true)
    setError('')
    try {
      onEnter(await api.lookupManager(code))
    } catch {
      setError("We couldn't find that manager code. Codes look like M14.")
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="relative grid min-h-full place-items-center overflow-hidden px-4 py-12">
      <div className="pointer-events-none absolute -top-40 left-1/2 size-[640px] -translate-x-1/2 rounded-full bg-indigo-500/15 blur-3xl" />
      <div className="absolute right-4 top-4"><ThemeButton /></div>
      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <img src="/favicon.svg" alt="" className="mx-auto size-14" />
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">Echo</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Ask questions about your team's recognition, workload and survey results — answered by five cooperating agents and checked before you see them.</p>
        </div>
        <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-900/5 dark:border-slate-800 dark:bg-slate-900">
          <label htmlFor="code" className="text-sm font-medium">Manager code</label>
          <div className="mt-2 flex gap-2">
            <input
              id="code"
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="e.g. M14"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 font-mono text-lg tracking-wider outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950"
            />
            <button disabled={checking || !code.trim()} className="inline-flex items-center gap-1 rounded-xl bg-indigo-600 px-4 font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50">
              <ArrowRight className="size-5" />
            </button>
          </div>
          {error && <p className="mt-2 text-sm text-rose-600 dark:text-rose-400">{error}</p>}
          <p className="mt-4 text-xs text-slate-500">Prototype access: the code selects which team's data Echo may use. It is not a secure login.</p>
        </form>
        <p className="mt-6 text-center text-xs text-slate-400">
          Echo supports human review and does not make personnel decisions
        </p>
      </div>
    </div>
  )
}

/* ---------------- newsroom ---------------- */

function liveConnection(meta: Meta | null) {
  if (meta?.local_split) return { use_local_split: true, profile: null }
  const profile = meta?.profiles.find((p) => p.key_configured)
  return profile ? { use_local_split: false, profile: profile.name } : null
}

const keyOf = (q: string) => q.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

function loadStageOpen() {
  try {
    return localStorage.getItem('echo-stage') !== 'closed'
  } catch {
    return true
  }
}

/** Collapsed newsroom: five dots that still light up, one click to open the full stage. */
function StageBar({ states, busy, status, onOpen }: { states: ReturnType<typeof agentStates>; busy: boolean; status: string; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="flex w-full items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition hover:border-indigo-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-500"
    >
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">The newsroom</span>
      <span className="flex items-center gap-3">
        {AGENTS.map((agent) => {
          const state = states[agent.name].status
          return (
            <span key={agent.name} className="flex items-center gap-1.5" title={agent.name}>
              <span
                className={clsx('size-3 rounded-full transition', state === 'active' && 'pulse-ring scale-125', busy && state === 'idle' && 'opacity-30')}
                style={{ background: agent.color, color: agent.color }}
              />
              <span className="hidden text-xs text-slate-600 md:inline dark:text-slate-300">{agent.name}</span>
            </span>
          )
        })}
      </span>
      <span className="ml-auto hidden truncate text-xs text-slate-500 sm:block">{busy ? status : 'Show the agents'}</span>
      <ChevronDown className="size-4 shrink-0 text-slate-400" />
    </button>
  )
}

function MeetingPrep({ partners, queueCount, onAsk, onQueue }: { partners: { Team: string; Contributions: number }[]; queueCount: number | null; onAsk: (q: string) => void; onQueue: () => void }) {
  const [partner, setPartner] = useState('')
  const chosen = partner || partners[0]?.Team || ''
  const card = 'flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-500'
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Prepare for a meeting</h2>
        <p className="mt-1 text-sm text-slate-500">Pick the meeting you're walking into. The newsroom builds a brief you can read now or present on your iPad.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <button onClick={() => onAsk('Prepare me for a team meeting')} className={clsx(card, 'text-left')}>
          <Users className="size-6 text-indigo-500" />
          <div className="mt-3 font-semibold">State of the Team</div>
          <p className="mt-1 flex-1 text-sm text-slate-500">Gallup's team conversation, prepared: a goal, strengths and opportunities, one focus area with actions, and how to review it.</p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 dark:text-indigo-400">
            Build brief <ArrowRight className="size-4" />
          </span>
        </button>
        <div className={card}>
          <Handshake className="size-6 text-[var(--color-cherry)]" />
          <div className="mt-3 font-semibold">Meeting with a partner team</div>
          <p className="mt-1 text-sm text-slate-500">What your people did for them, the feedback they gave, and what's still unrecognized.</p>
          <select
            value={chosen}
            onChange={(e) => setPartner(e.target.value)}
            className="mt-3 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950"
            aria-label="Partner team"
          >
            {partners.map((p) => (
              <option key={p.Team} value={p.Team}>
                {p.Team} ({p.Contributions})
              </option>
            ))}
          </select>
          <button disabled={!chosen} onClick={() => onAsk(`Prepare me for a meeting with ${chosen}`)} className="mt-3 inline-flex items-center gap-1 self-start text-sm font-medium text-indigo-600 disabled:opacity-40 dark:text-indigo-400">
            Build brief <ArrowRight className="size-4" />
          </button>
        </div>
        <button onClick={() => onAsk('Prepare me for my quarterly review')} className={clsx(card, 'text-left')}>
          <CalendarCheck className="size-6 text-[var(--color-lime)]" />
          <div className="mt-3 font-semibold">Quarterly review</div>
          <p className="mt-1 flex-1 text-sm text-slate-500">This quarter against the last on the measures that matter: is cross-team work being seen?</p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 dark:text-indigo-400">
            Build brief <ArrowRight className="size-4" />
          </span>
        </button>
      </div>
      {queueCount !== null && queueCount > 0 && (
        <button onClick={onQueue} className="flex w-full items-center gap-4 rounded-2xl border border-amber-200 bg-amber-50/60 p-4 text-left transition hover:border-amber-300 dark:border-amber-500/20 dark:bg-amber-500/5">
          <Award className="size-6 shrink-0 text-amber-500" />
          <div className="flex-1">
            <div className="font-semibold">
              {queueCount} piece{queueCount === 1 ? '' : 's'} of praised work waiting for recognition
            </div>
            <div className="text-sm text-slate-500">Help your team gave other teams that drew praise but hasn't been recognized yet.</div>
          </div>
          <span className="inline-flex items-center gap-1 text-sm font-medium text-amber-700 dark:text-amber-300">
            Open queue <ArrowRight className="size-4" />
          </span>
        </button>
      )}
    </section>
  )
}

type View = 'home' | 'investigate' | 'investigation' | 'queue' | 'actions' | 'tracking' | 'trust'

// Gallup's manager loop, used as Echo's navigation: each step is a place in the app.
const LOOP = [
  { step: 'Measure', label: 'Team pulse', icon: Gauge, hint: 'What the survey says' },
  { step: 'Diagnose', label: 'Investigate', icon: Search, hint: 'The story behind the numbers' },
  { step: 'Discuss', label: 'Meeting prep', icon: Users, hint: 'State of the Team and partners' },
  { step: 'Act', label: 'Recognition queue', icon: Award, hint: 'Close the loop on praised work' },
  { step: 'Monitor', label: 'Tracking', icon: CalendarCheck, hint: 'Measures you chose to watch' },
  { step: 'Learn', label: 'Quarterly review', icon: GraduationCap, hint: 'Did it make a difference?' },
] as const

/** Home overview of Gallup's loop: Measure → Diagnose → Discuss → Act → Monitor → Learn. */
function LoopStrip({ onStep, queueOpen, watching }: { onStep: (step: (typeof LOOP)[number]['step']) => void; queueOpen: number | null; watching: number }) {
  return (
    <section>
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">The manager loop</h2>
        <span className="text-xs text-slate-500">Data informs the conversation; it doesn't replace it.</span>
      </div>
      <ol className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {LOOP.map((item, i) => (
          <li key={item.step}>
            <button
              onClick={() => onStep(item.step)}
              className="group relative flex h-full w-full flex-col rounded-2xl border border-slate-200 bg-white p-3 text-left transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-500"
            >
              <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                {i + 1} · {item.step}
              </span>
              <span className="mt-2 flex items-center gap-2 text-sm font-semibold">
                <item.icon className="size-4 text-slate-400 group-hover:text-indigo-500" /> {item.label}
              </span>
              <span className="mt-1 text-xs text-slate-500">
                {item.step === 'Act' && queueOpen ? `${queueOpen} waiting` : item.step === 'Monitor' && watching ? `${watching} measures` : item.hint}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}

function Tracking({ watch, onRemove, onReview }: { watch: Watched[]; onRemove: (question: string) => void; onReview: () => void }) {
  const groups = [...new Set(watch.map((w) => w.question))]
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <CalendarCheck className="size-5 text-indigo-500" /> Tracking
          </h2>
          <p className="mt-1 text-sm text-slate-500">The measures you chose to watch. Compare them at the next quarterly review.</p>
        </div>
        <button onClick={onReview} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
          <GraduationCap className="size-4" /> Run quarterly review
        </button>
      </div>
      {groups.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500 dark:border-slate-800">
          Nothing tracked yet. Use “Track next quarter” on any brief.
        </p>
      ) : (
        groups.map((question) => {
          const items = watch.filter((w) => w.question === question)
          return (
            <div key={question} className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-semibold">{question}</div>
                  <div className="text-xs text-slate-500">Saved {new Date(items[0].savedAt).toLocaleDateString()}</div>
                </div>
                <button onClick={() => onRemove(question)} className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10" aria-label="Stop tracking">
                  <Trash2 className="size-4" />
                </button>
              </div>
              <table className="mt-3 w-full text-left text-sm">
                <thead className="text-xs text-slate-500">
                  <tr>
                    <th className="py-1 font-medium">Measure</th>
                    <th className="py-1 font-medium">When saved</th>
                    <th className="py-1 font-medium">Aim</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((w) => (
                    <tr key={w.metric} className="border-t border-slate-100 dark:border-slate-800">
                      <td className="py-1.5">{w.metric}</td>
                      <td className="py-1.5 font-medium tabular-nums">{w.baseline}</td>
                      <td className="py-1.5 text-slate-500">{w.goal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        })
      )}
    </section>
  )
}


function Workspace({ manager, onLeave }: { manager: Manager; onLeave: () => void }) {
  const meta = useAsync(api.meta)
  const [conversations, setConversations] = useState<Conversation[]>(() => loadConversations(manager.Manager_ID))
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [view, setView] = useState<View>('home')
  const [question, setQuestion] = useState('')
  const [period, setPeriod] = useState('all')
  const [mode, setMode] = useState<'demo' | 'live'>('demo')
  const [activeRun, setActiveRun] = useState<string | null>(null)
  const [activePace, setActivePace] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const [error, setError] = useState('')
  const [sidebar, setSidebar] = useState(false)
  const [pulseOpen, setPulseOpen] = useState(false)
  const [presenting, setPresenting] = useState(false)
  const [stageOpen, setStageOpenState] = useState(loadStageOpen)
  const [watch, setWatch] = useState<Watched[]>(() => loadWatch(manager.Manager_ID))
  const [done, setDone] = useState<string[]>(() => loadDone(manager.Manager_ID))
  const [actionLaunch, setActionLaunch] = useState<{ token: number; prefill: SchedulerPrefill } | null>(null)
  const [actionViewKey, setActionViewKey] = useState(0)
  const range = PERIODS.find((p) => p.id === period)!
  const saved = useAsync(() => api.savedAnswers(manager.Manager_ID, range.start, range.end), [period, refreshKey])
  const partners = useAsync(() => api.partners(manager.Manager_ID, range.start, range.end), [period])
  const queue = useAsync(() => api.recognitionQueue(manager.Manager_ID, range.start, range.end), [period])
  const savedSet = new Set((saved.data ?? []).map((s) => keyOf(s.question)))
  const queueOpen = queue.data ? queue.data.filter((i) => !done.includes(i.contribution_id)).length : null

  const current = view === 'investigation' ? conversations.find((c) => c.id === currentId) ?? null : null
  const message = current?.messages.at(-1) ?? null
  const viewRunId = message?.runId
  // The stage replays the active investigation step by step, or shows the finished state of the one being read.
  const stream = useRunEvents(activeRun ?? viewRunId, activeRun ? activePace : 0, 0)
  const states = useMemo(() => agentStates(stream.events), [stream.events])
  const activity = useMemo(() => agentActivity(stream.events), [stream.events])
  const busy = activeRun !== null
  const run = useAsync(() => (viewRunId ? api.managerRun(viewRunId) : Promise.resolve(null)), [viewRunId, refreshKey])
  const connection = liveConnection(meta.data)
  const tracked = !!message && watch.some((w) => w.question === message.question)

  const lastAgent = [...stream.events].reverse().find((e) => e.agent && e.agent !== 'original')?.agent
  const named = (Object.keys(activity) as (keyof typeof activity)[]).find((a) => a.toLowerCase() === (lastAgent ?? '').toLowerCase())
  const status = named ? `${named}: ${activity[named] ?? 'working'}…` : 'The editor is planning the investigation…'

  function setStageOpen(open: boolean) {
    setStageOpenState(open)
    try {
      localStorage.setItem('echo-stage', open ? 'open' : 'closed')
    } catch {
      /* storage unavailable */
    }
  }

  useEffect(() => {
    saveConversations(manager.Manager_ID, conversations)
  }, [conversations, manager.Manager_ID])
  useEffect(() => {
    if (stream.done && activeRun) {
      setActiveRun(null)
      setRefreshKey((k) => k + 1)
    }
  }, [stream.done, activeRun])

  async function ask(text: string) {
    const q = text.trim()
    if (!q || busy) return
    if (mode === 'live' && !connection) return setError('No live model is configured. Use Demo mode, or add a key in the technical view.')
    setError('')
    try {
      const started = await api.startRun({
        manager_id: manager.Manager_ID,
        start_date: range.start,
        end_date: range.end,
        question: q,
        mode,
        ...(mode === 'live' ? connection : {}),
      })
      const entry: Message = { question: q, runId: started.id, mode, askedAt: new Date().toISOString() }
      setConversations((all) => [{ id: started.id, title: q, createdAt: entry.askedAt, messages: [entry] }, ...all])
      setCurrentId(started.id)
      setView('investigation')
      setQuestion('')
      setActivePace(started.mode === 'offline' ? 280 : started.mode === 'replay' ? 80 : started.mode === 'demo' ? 70 : 0)
      setActiveRun(started.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function track(items: NonNullable<Artifact['watch']>) {
    if (!message) return
    const next = [...watch.filter((w) => w.question !== message.question), ...items.map((i) => ({ ...i, savedAt: new Date().toISOString(), question: message.question }))]
    setWatch(next)
    saveWatch(manager.Manager_ID, next)
  }

  function toggleDone(id: string) {
    const next = done.includes(id) ? done.filter((d) => d !== id) : [...done, id]
    setDone(next)
    saveDone(manager.Manager_ID, next)
  }

  function goStep(step: (typeof LOOP)[number]['step']) {
    setSidebar(false)
    if (step === 'Measure') setPulseOpen(true)
    else if (step === 'Diagnose') setView('investigate')
    else if (step === 'Discuss') setView('home')
    else if (step === 'Act') setView('queue')
    else if (step === 'Monitor') setView('tracking')
    else ask('Prepare me for my quarterly review')
  }
  const stepActive = (step: string) =>
    (step === 'Diagnose' && (view === 'investigate' || view === 'investigation')) ||
    (step === 'Discuss' && view === 'home') ||
    (step === 'Act' && view === 'queue') ||
    (step === 'Monitor' && view === 'tracking')

  const navButton = (active: boolean) =>
    clsx(
      'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition',
      active ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
    )

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <img src="/favicon.svg" alt="" className="size-8" />
        <div>
          <div className="text-base font-semibold leading-tight tracking-tight">Echo</div>
          <div className="text-[11px] text-slate-500">Your team's newsroom</div>
        </div>
        <button className="ml-auto rounded-lg p-1.5 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800" onClick={() => setSidebar(false)} aria-label="Close menu">
          <X className="size-4" />
        </button>
      </div>
      <nav className="space-y-0.5 px-3">
        <div className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">The manager loop</div>
        {LOOP.map((item, i) => (
          <button key={item.step} onClick={() => goStep(item.step)} className={navButton(stepActive(item.step))} title={item.hint}>
            <span className="w-4 text-center text-[11px] font-semibold text-slate-400">{i + 1}</span>
            <item.icon className="size-4" />
            <span className="min-w-0 flex-1 text-left">
              <span className="block truncate">{item.label}</span>
              <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">{item.step}</span>
            </span>
            {item.step === 'Act' && queueOpen !== null && queueOpen > 0 && (
              <span className="rounded-full bg-amber-100 px-1.5 text-[11px] font-semibold text-amber-800 dark:bg-amber-500/20 dark:text-amber-300">{queueOpen}</span>
            )}
            {item.step === 'Monitor' && watch.length > 0 && <span className="rounded-full bg-slate-100 px-1.5 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{watch.length}</span>}
          </button>
        ))}
        <button onClick={() => { setActionLaunch(null); setActionViewKey((key) => key + 1); setView('actions'); setSidebar(false) }} className={clsx(navButton(view === 'actions'), 'mt-2')}>
          <span className="w-4" />
          <WandSparkles className="size-4" />
          <span className="min-w-0 flex-1 text-left">
            <span className="block truncate">Action Center</span>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">Plan & approve</span>
          </span>
        </button>
        <button onClick={() => (setView('trust'), setSidebar(false))} className={clsx(navButton(view === 'trust'), 'mt-2')}>
          <span className="w-4" />
          <ShieldCheck className="size-4" /> Trust & evaluation
        </button>
      </nav>
      <div className="mt-4 flex-1 overflow-y-auto px-3">
        <div className="mb-1.5 px-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Briefs</div>
        {conversations.length === 0 && <p className="px-2 text-xs text-slate-500">Your briefs will appear here.</p>}
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => {
              setCurrentId(c.id)
              setView('investigation')
              setSidebar(false)
            }}
            className={clsx(
              'block w-full truncate rounded-lg px-2 py-1.5 text-left text-sm transition',
              view === 'investigation' && c.id === currentId ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
            )}
          >
            {c.messages.at(-1)?.question ?? c.title}
          </button>
        ))}
      </div>
      <p className="px-4 pb-4 text-[11px] leading-relaxed text-slate-500">
        <ShieldAlert className="mr-1 inline size-3" />
        Synthetic data · supports human review, never personnel decisions
      </p>
    </div>
  )

  const showWork = view === 'home' || view === 'investigate' || view === 'investigation'
  const initials = manager.Manager_Name.split(' ').map((n) => n[0]).join('')

  return (
    <div className="chat-shell flex h-full">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block dark:border-slate-800 dark:bg-slate-900/60">{sidebarContent}</aside>
      {sidebar && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/40" onClick={() => setSidebar(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white dark:bg-slate-900">{sidebarContent}</aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white/80 px-4 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-3">
            <button className="rounded-lg p-1.5 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800" onClick={() => setSidebar(true)} aria-label="Open menu">
              <PanelLeft className="size-5" />
            </button>
            <span className="grid size-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-base font-semibold text-white shadow-sm">{initials}</span>
            <div className="min-w-0">
              <div className="truncate text-lg font-semibold leading-tight">{manager.Manager_Name}</div>
              <div className="truncate text-sm text-slate-500">
                Manager · {manager.Primary_Team} · {manager.Pilot_Assigned_Employees} people <span className="short-hide">· {manager.Manager_ID}</span>
              </div>
            </div>
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                disabled={busy}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                aria-label="Time period"
              >
                {PERIODS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setPulseOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:text-slate-200 dark:hover:border-indigo-500"
                title="What your team is saying in surveys"
              >
                <MessagesSquare className="size-3.5" /> Team pulse
              </button>
              <ThemeButton />
              <Link to="/console" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" title="Technical view: runs, evidence, connections" aria-label="Technical view">
                <Wrench className="size-4" />
              </Link>
              <button onClick={onLeave} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" title="Switch manager" aria-label="Switch manager">
                <LogOut className="size-4" />
              </button>
            </div>
          </div>
        </header>

        <main className="min-h-48 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl space-y-5 px-4 py-6">
            {showWork && (<>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                ask(question)
              }}
              className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 pl-4 shadow-sm transition focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-900"
            >
              <Newspaper className="size-5 shrink-0 text-indigo-500" />
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={busy}
                placeholder={busy ? 'The newsroom is working…' : mode === 'demo' ? 'Ask the newsroom to investigate… (Demo: pick a suggestion)' : 'Ask the newsroom to investigate…'}
                className="min-w-0 flex-1 bg-transparent py-2 text-[15px] outline-none placeholder:text-slate-400"
              />
              <div className="hidden rounded-lg bg-slate-100 p-0.5 text-[11px] sm:flex dark:bg-slate-800">
                {(['demo', 'live'] as const).map((m) => (
                  <button
                    type="button"
                    key={m}
                    onClick={() => setMode(m)}
                    disabled={busy}
                    className={clsx('rounded-md px-2.5 py-1 font-medium', mode === m ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white' : 'text-slate-500')}
                  >
                    {m === 'demo' ? 'Demo' : 'Live AI'}
                  </button>
                ))}
              </div>
              {busy ? (
                <button type="button" onClick={() => api.cancelRun(activeRun!).catch(() => undefined)} className="grid size-10 place-items-center rounded-xl bg-slate-900 text-white dark:bg-white dark:text-slate-900" aria-label="Stop">
                  <Square className="size-4" fill="currentColor" />
                </button>
              ) : (
                <button disabled={!question.trim()} className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-500 disabled:opacity-40" aria-label="Investigate">
                  <ArrowRight className="size-5" />
                </button>
              )}
            </form>
            </>)}
            {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}
            {!busy && showWork && (
              <div className="flex flex-wrap gap-2">
                {SUGGESTED.map((q, i) => (
                  <button
                    key={q}
                    onClick={() => ask(q)}
                    className={clsx(
                      'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs transition',
                      i === 0
                        ? 'border-indigo-300 bg-indigo-50 font-medium text-indigo-700 hover:bg-indigo-100 dark:border-indigo-500/40 dark:bg-indigo-500/10 dark:text-indigo-300'
                        : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:text-slate-300 dark:hover:border-indigo-500',
                    )}
                  >
                    {mode === 'demo' && savedSet.has(keyOf(q)) && <History className="size-3 text-indigo-500" />}
                    {i === 0 && <Sparkles className="size-3" />}
                    {q}
                  </button>
                ))}
                <button
                  onClick={() => ask(GUARDRAIL_EXAMPLE)}
                  className="inline-flex items-center gap-1 rounded-full border border-dashed border-rose-300 px-3 py-1 text-xs text-rose-700 transition hover:bg-rose-50 dark:border-rose-500/40 dark:text-rose-300 dark:hover:bg-rose-500/10"
                  title="See how Echo protects anonymous responses"
                >
                  <ShieldAlert className="size-3" /> Try one Echo won't answer
                </button>
              </div>
            )}

            {view === 'home' && <LoopStrip onStep={goStep} queueOpen={queueOpen} watching={watch.length} />}

            {showWork &&
              (stageOpen || busy ? (
                <div className="relative">
                  <AgentStage
                    states={states}
                    activity={activity}
                    busy={busy}
                    headline={busy ? status : current ? 'Brief ready — read it below' : 'Ask a question or prepare for a meeting, and watch the newsroom work'}
                  />
                  {!busy && (
                    <button
                      onClick={() => setStageOpen(false)}
                      className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-lg bg-white/80 px-2 py-1 text-xs text-slate-500 backdrop-blur hover:text-slate-800 dark:bg-slate-900/80 dark:hover:text-slate-200"
                    >
                      <ChevronUp className="size-3.5" /> Minimize
                    </button>
                  )}
                </div>
              ) : (
                <StageBar states={states} busy={busy} status={status} onOpen={() => setStageOpen(true)} />
              ))}

            {view === 'trust' ? (
              <Trust />
            ) : view === 'actions' ? (
              <ActionCenter key={actionViewKey} managerId={manager.Manager_ID} teamName={manager.Primary_Team} teamSize={manager.Pilot_Assigned_Employees} launch={actionLaunch} />
            ) : view === 'tracking' ? (
              <Tracking watch={watch} onRemove={(q) => {
                const next = watch.filter((w) => w.question !== q)
                setWatch(next)
                saveWatch(manager.Manager_ID, next)
              }} onReview={() => ask('Prepare me for my quarterly review')} />
            ) : view === 'investigate' ? (
              <section className="rounded-2xl border border-dashed border-slate-200 p-6 text-sm text-slate-500 dark:border-slate-800">
                <div className="font-semibold text-slate-700 dark:text-slate-200">Find the story behind the numbers</div>
                Ask your own question above, or start from a suggestion. The newsroom checks the records, listens to the survey as themes, and flags when the two disagree.
              </section>
            ) : view === 'queue' ? (
              <RecognitionQueue
                items={queue.data ?? []}
                done={done}
                loading={queue.loading}
                onToggle={toggleDone}
                periodLabel={range.label}
                onSchedule={(item) => {
                  setActionLaunch((currentLaunch) => ({
                    token: (currentLaunch?.token ?? 0) + 1,
                    prefill: {
                      title: `Recognition discussion with ${item.name}`,
                      purpose: 'Recognition discussion',
                      description: `${item.name} helped ${item.team_helped}: ${item.outcome}. Confirm whether recognition has already occurred; the missing linked record is not proof that it did not.`,
                      origin: { kind: 'existing-evidence', label: 'Opened from Recognition queue', insightId: item.contribution_id },
                    },
                  }))
                  setActionViewKey((key) => key + 1)
                  setView('actions')
                }}
              />
            ) : view === 'home' || !current ? (
              <MeetingPrep partners={partners.data ?? []} queueCount={queueOpen} onAsk={ask} onQueue={() => setView('queue')} />
            ) : (
              <section className="space-y-4">
                <h2 className="text-xl font-semibold tracking-tight">{message?.question}</h2>
                {busy || run.loading || run.data?.meta.state === 'running' ? (
                  <BriefPending activity={activity} />
                ) : run.data ? (
                  <Brief
                    meta={run.data.meta}
                    artifact={run.data.artifact}
                    managerId={manager.Manager_ID}
                    onOpenPulse={() => setPulseOpen(true)}
                    onTrack={track}
                    tracked={tracked}
                    onPresent={() => setPresenting(true)}
                  />
                ) : (
                  <p className="text-sm text-slate-500">This brief is no longer available.</p>
                )}
              </section>
            )}
          </div>
        </main>
      </div>
      {pulseOpen && <TeamPulse managerId={manager.Manager_ID} start={range.start} end={range.end} periodLabel={range.label} onClose={() => setPulseOpen(false)} />}
      {presenting && run.data?.artifact && (
        <Presenter meta={run.data.meta} artifact={run.data.artifact} manager={manager} period={PERIODS.find((p) => p.start === run.data!.meta.start_date && p.end === run.data!.meta.end_date)?.label ?? `${run.data.meta.start_date} – ${run.data.meta.end_date}`} onClose={() => setPresenting(false)} />
      )}
    </div>
  )
}

export default function ManagerApp() {
  const [manager, setManager] = useState<Manager | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const saved = loadManagerCode()
    if (!saved) return setChecking(false)
    api
      .lookupManager(saved)
      .then(setManager)
      .catch(() => saveManagerCode(null))
      .finally(() => setChecking(false))
  }, [])

  if (checking) return null
  if (!manager)
    return (
      <Entry
        onEnter={(m) => {
          saveManagerCode(m.Manager_ID)
          setManager(m)
        }}
      />
    )
  return (
    <Workspace
      key={manager.Manager_ID}
      manager={manager}
      onLeave={() => {
        saveManagerCode(null)
        setManager(null)
      }}
    />
  )
}
