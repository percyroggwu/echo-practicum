import clsx from 'clsx'
import { ArrowRight, Check, PanelLeftClose, PanelLeftOpen, CalendarCheck, ChevronDown, ChevronUp, CalendarPlus, Handshake, House, WandSparkles, History, Mail, MessagesSquare, Plus, Presentation, LogOut, Moon, Newspaper, PanelLeft, ShieldAlert, Sparkles, Square, Sun, Trash2, Users, Wrench, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTheme } from '../components/Layout'
import { api, type Artifact, type Manager, type Meta, type Partner, type Visibility } from '../lib/api'
import PartnerActionDialog, { type PartnerAction } from './PartnerActions'
import ActionCenter from './ActionCenter'
import type { SchedulerPrefill } from './actionTypes'
import WorkJourney, { journeySteps } from './WorkJourney'
import { Skeleton } from './motion'
import { runOutcomes } from './sources'
import { agentStates, useRunEvents, type AgentState } from '../lib/events'
import { AGENTS, SERIES_COLORS, type AgentName } from '../lib/agents'
import { useAsync } from '../lib/useAsync'
import AgentStage from './AgentStage'
import { agentActivity } from './AgentStrip'
import Brief, { BriefPending } from './Brief'
import { ASSUMED_HOURLY_COST, FTE_QUARTER_HOURS, Tiles, dollars, planFrom, type AnswerPlan } from './visual'
import TeamPulse, { type PanelTab } from './TeamPulse'
import HomeDashboard from './HomeDashboard'
import { loadConversations, loadManagerCode, loadSeen, loadThanked, loadWatch, saveConversations, saveManagerCode, saveSeen, saveThanked, saveWatch, type Conversation, type Message, type Watched } from './store'

// How many suggestions stay visible when the rest are hidden.
const SUGGESTED_SHORT = 4

const SUGGESTED = [
  "How much of my team's cross-team work goes unnoticed or unrecognized?",
  "What did my team do this year that wasn't in their goals?",
  'What happens to work that crosses team lines?',
  "How is my team's morale?",
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

/** Concentric arcs spreading from a point: the "echo" motif on the sign-in panel. */
function Ripples({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 600 600" className={className} aria-hidden fill="none">
      {[60, 115, 175, 240, 310, 385].map((r, i) => (
        <circle key={r} cx="300" cy="300" r={r} stroke="currentColor" strokeWidth={i === 0 ? 1.6 : 1} strokeOpacity={0.55 - i * 0.075} className="echo-ripple" style={{ animationDelay: `${i * 140}ms` }} />
      ))}
    </svg>
  )
}

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

  // Two steps: the green opening page, then the white page with the manager code.
  const [step, setStep] = useState<'intro' | 'code'>('intro')
  useEffect(() => {
    if (step !== 'intro') return
    const key = (event: KeyboardEvent) => event.key === 'Enter' && setStep('code')
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [step])

  return (
    <div className="relative h-full min-h-[560px] overflow-hidden">
      {/* 1. Opening page: a laptop opens on Echo, moves aside, and the word writes itself in */}
      <section
        aria-hidden={step !== 'intro'}
        className={clsx(
          'ei-intro ei-slide absolute inset-0 flex flex-col items-center justify-center overflow-y-auto overflow-x-hidden px-6 py-16 text-white',
          step !== 'intro' && '-translate-x-full',
        )}
      >
        <img src="/favicon.svg" alt="Echo" className="absolute left-6 top-6 size-10 rounded-xl ring-1 ring-white/20 sm:left-12 sm:top-10" />
        {/* The laptop and the word share a fixed-height box, so the text and Next below always sit in the page's flow. */}
        <div className="ei-stagebox relative w-full shrink-0">
        <div className="ei-stage">
          <div className="ei-ring" />
          <div className="ei-ring" />
          <div className="ei-ring" />
          <div className="ei-laptop-wrap" aria-hidden>
            <div className="ei-laptop">
              <div className="ei-base">
                <div className="ei-keys" />
                <div className="ei-pad" />
              </div>
              <div className="ei-lid">
                <div className="ei-face ei-outside">
                  <img src="/favicon.svg" alt="" />
                </div>
                <div className="ei-face ei-inside">
                  <div className="ei-screen">
                    <img src="/favicon.svg" alt="" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <h1 className="ei-word font-display font-semibold" aria-label="Echo">
            {['E', 'c', 'h', 'o'].map((letter) => (
              <span key={letter} data-l={letter} aria-hidden>
                {letter}
              </span>
            ))}
          </h1>
          <div className="ei-tag text-[15px] uppercase tracking-[0.22em] text-[#c8d3a8]">Work across the org chart</div>
        </div>
        </div>
        <div className="relative w-[min(760px,100%)] shrink-0 text-center">
          <p className="ei-rise font-display text-xl font-medium leading-snug sm:text-3xl" style={{ animationDelay: '4.8s' }}>
            See the work your team does that you don't always hear about.
          </p>
          <p className="ei-rise mt-3 text-sm leading-relaxed text-white/75 sm:mt-3.5 sm:text-base" style={{ animationDelay: '5.1s' }}>
            Performance gets measured along the org chart. Echo finds the work that crosses it, so it gets seen, recognized and planned for. Five agents
            use only your team's data, check each other's work, and hand you a brief you can act on.
          </p>
        </div>
        <button
          onClick={() => setStep('code')}
          tabIndex={step === 'intro' ? 0 : -1}
          className="ei-next relative mt-10 inline-flex shrink-0 items-center gap-3 rounded-full px-5 py-3 text-[17px] font-semibold uppercase tracking-[0.14em] text-white transition hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-white/60"
        >
          Next
          <ArrowRight className="size-5" />
        </button>
      </section>

      {/* 2. Sign-in: the manager code, on a clean white page */}
      <section
        aria-hidden={step !== 'code'}
        className={clsx('ei-slide absolute inset-0 flex items-center justify-center bg-slate-50 px-6 py-12 sm:px-12 dark:bg-slate-950', step !== 'code' && 'translate-x-full')}
      >
        <div className="absolute left-6 top-6 flex items-center gap-3 sm:left-12 sm:top-10">
          <img src="/favicon.svg" alt="" className="size-9 rounded-xl" />
          <span className="text-lg font-semibold text-slate-900 dark:text-white">Echo</span>
        </div>
        <div className="absolute right-4 top-4">
          <ThemeButton />
        </div>
        <button
          onClick={() => setStep('intro')}
          tabIndex={step === 'code' ? 0 : -1}
          className="absolute bottom-8 left-6 text-sm font-medium text-slate-500 transition hover:text-slate-800 sm:left-12 dark:text-slate-400 dark:hover:text-slate-200"
        >
          ← Back
        </button>
        <div className="w-full max-w-sm">
          <h2 className="font-display text-4xl font-semibold tracking-tight text-slate-900 dark:text-white">Welcome back</h2>
          <p className="mt-2 text-[15px] text-slate-600 dark:text-slate-400">Enter your manager code to see your team's work.</p>

          <form onSubmit={submit} className="mt-8">
            <label htmlFor="code" className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Manager code
            </label>
            <input
              id="code"
              key={step}
              autoFocus={step === 'code'}
              tabIndex={step === 'code' ? 0 : -1}
              autoComplete="off"
              spellCheck={false}
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="M14"
              aria-invalid={!!error}
              aria-describedby={error ? 'code-error' : 'code-note'}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 font-mono text-2xl tracking-[0.2em] text-slate-900 shadow-sm outline-none transition placeholder:text-slate-300 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-400/20 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:placeholder:text-slate-600"
            />
            {error && (
              <p id="code-error" className="mt-2 text-sm text-rose-600 dark:text-rose-400">
                {error}
              </p>
            )}
            <button
              disabled={checking || !code.trim()}
              tabIndex={step === 'code' ? 0 : -1}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3.5 text-[15px] font-semibold text-white shadow-[0_10px_24px_-12px_rgb(65_74_40/0.7)] transition hover:bg-indigo-700 disabled:bg-indigo-300/70 disabled:shadow-none dark:disabled:bg-indigo-900/50 dark:disabled:text-indigo-200/50"
            >
              {checking ? 'Opening…' : 'Open Echo'}
              {!checking && <ArrowRight className="size-4" />}
            </button>
          </form>

          <div id="code-note" className="mt-8 space-y-2 border-t border-slate-200 pt-6 text-xs leading-relaxed text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <p>Prototype access: the code selects which team's data Echo may use. It is not a secure login.</p>
            <p>Echo supports human review and does not make personnel decisions.</p>
          </div>
        </div>
      </section>
    </div>
  )
}

/* ---------------- workspace ---------------- */

function liveConnection(meta: Meta | null) {
  if (meta?.local_split) return { use_local_split: true, profile: null }
  const profile = meta?.profiles.find((p) => p.key_configured)
  return profile ? { use_local_split: false, profile: profile.name } : null
}

const keyOf = (q: string) => q.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

/** A small on/off preference remembered in this browser (layout choices only). */
function usePref(key: string, initial: boolean) {
  const [value, setValue] = useState(() => {
    try {
      const saved = localStorage.getItem(key)
      return saved === null ? initial : saved === '1'
    } catch {
      return initial
    }
  })
  const update = (next: boolean) => {
    setValue(next)
    try {
      localStorage.setItem(key, next ? '1' : '0')
    } catch {
      /* storage unavailable */
    }
  }
  return [value, update] as const
}

function MeetingPrep({ managerName, partners, gapCount, visibility, loading, quarter, onAsk, onGaps }: { managerName: string; loading: boolean; partners: Partner[]; gapCount: number | null; visibility: Visibility | null; quarter: string | null; onAsk: (q: string) => void; onGaps: () => void }) {
  const [partner, setPartner] = useState('')
  const chosen = partner || partners[0]?.Team || ''
  const chosenPartner = partners.find((p) => p.Team === chosen)
  const [action, setAction] = useState<PartnerAction | null>(null)
  return (
    <section className="space-y-4">
      {loading && <Skeleton className="h-[190px] rounded-2xl" />}
      {visibility && (
        <button onClick={onGaps} className="block w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-500">
          <div className="flex items-center gap-3">
            <h2 className="flex-1 text-xl font-semibold tracking-tight">Help your team gave other teams{quarter ? ` in ${quarter}` : ''}</h2>
            <span className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 dark:text-indigo-400">
              See gaps <ArrowRight className="size-4" />
            </span>
          </div>
          <div className="mt-4">
            <Tiles
              tiles={[
                { value: `${visibility.No_Praise + visibility.Praise_Not_Passed_On} of ${visibility.Cross_Team}`, label: 'pieces of help went unnoticed', icon: 'eye', tone: 'no_praise' },
                { value: `${Math.round(visibility.Unnoticed_Hours).toLocaleString()} h`, label: `of unnoticed work, about ${(visibility.Unnoticed_Hours / FTE_QUARTER_HOURS).toFixed(1)} people's quarter`, icon: 'hours', tone: 'not_passed' },
                { value: dollars(visibility.Unnoticed_Hours), label: `of work off the books (at $${ASSUMED_HOURLY_COST}/h, assumed)`, icon: 'cost', tone: 'money' },
                { value: `${visibility.Unrecognized}`, label: gapCount ? 'praised and ready to recognize' : 'praised, but not recognized', icon: 'award', tone: 'unrecognized' },
              ]}
            />
          </div>
        </button>
      )}
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 pt-2">
        <h2 className="font-display text-[22px] font-semibold tracking-tight">Prepare for a meeting</h2>
        <span className="text-sm text-slate-500">A one-page brief, built from your team's records</span>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="meet-card" style={{ '--c': 'var(--color-lime)' } as React.CSSProperties}>
          <div className="flex items-center gap-3">
            <span className="meet-icon"><Users className="size-5" /></span>
            <span className="meet-num">01</span>
          </div>
          <div className="mt-3.5 font-semibold sm:text-[16.5px]">Team meeting</div>
          <p className="meet-text">How the team is doing and what to talk about, filled in with your data.</p>
          <div className="meet-foot">
            <span className="min-w-0 flex-1 truncate text-xs text-slate-500">Survey + work records</span>
            <button onClick={() => onAsk('Prepare me for a team meeting')} className="meet-btn">
              Build brief <ArrowRight className="size-3.5" />
            </button>
          </div>
        </div>
        <div className="meet-card" style={{ '--c': 'var(--color-cherry)' } as React.CSSProperties}>
          <div className="flex items-center gap-1.5">
            <span className="meet-icon mr-auto"><Handshake className="size-5" /></span>
            {chosenPartner && (
              <>
                <button onClick={() => setAction('feedback')} className="meet-mini" title="Ask for feedback" aria-label={`Ask ${chosen} for feedback`}>
                  <Mail className="size-3.5" />
                </button>
                <button onClick={() => setAction('meeting')} className="meet-mini" title="Schedule meeting" aria-label={`Schedule a meeting with ${chosen}`}>
                  <CalendarPlus className="size-3.5" />
                </button>
              </>
            )}
            <span className="meet-num ml-1.5">02</span>
          </div>
          <div className="mt-3.5 font-semibold sm:text-[16.5px]">Meeting with a partner team</div>
          <p className="meet-text">What your people did for them and how it was received.</p>
          <div className="meet-foot">
            <select
              value={chosen}
              onChange={(e) => setPartner(e.target.value)}
              className="min-w-0 flex-1 truncate rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-950"
              aria-label="Partner team"
            >
              {partners.map((p) => (
                <option key={p.Team} value={p.Team}>
                  {p.Team} ({p.Contributions})
                </option>
              ))}
            </select>
            <button disabled={!chosen} onClick={() => onAsk(`Prepare me for a meeting with ${chosen}`)} className="meet-btn">
              Build brief <ArrowRight className="size-3.5" />
            </button>
          </div>
        </div>
        <div className="meet-card" style={{ '--c': 'var(--color-original)' } as React.CSSProperties}>
          <div className="flex items-center gap-3">
            <span className="meet-icon"><CalendarCheck className="size-5" /></span>
            <span className="meet-num">03</span>
          </div>
          <div className="mt-3.5 font-semibold sm:text-[16.5px]">Quarterly review</div>
          <p className="meet-text">This quarter against the last. Did anything change?</p>
          <div className="meet-foot">
            <span className="min-w-0 flex-1 truncate text-xs text-slate-500">Against last quarter</span>
            <button onClick={() => onAsk('Prepare me for my quarterly review')} className="meet-btn">
              Build brief <ArrowRight className="size-3.5" />
            </button>
          </div>
        </div>
      </div>
      {action && chosenPartner && <PartnerActionDialog action={action} partner={chosenPartner} managerName={managerName} onClose={() => setAction(null)} />}
    </section>
  )
}


const AGENT_JOBS: Record<string, string> = { Original: 'Coordinator', Cherry: 'Data', Vanilla: 'Comments', Lime: 'Charts', ZeroSugar: 'Reviewer' }

/** The Ask Echo start page: a calm green banner with the Echo ripple, holding the question box and suggestions. */
function AskHero({ on, firstName, team, children }: { on: boolean; firstName: string; team: string; children: React.ReactNode }) {
  if (!on) return <div className="space-y-5">{children}</div>
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  return (
    <section className="ask-hero relative overflow-hidden rounded-[28px] px-5 pb-8 pt-10 text-center text-white sm:px-12 sm:pt-12">
      {[260, 420, 600, 800, 1020, 1260].map((w) => (
        <span key={w} className="ask-ring" style={{ width: w, height: w }} aria-hidden />
      ))}
      <h1 className="relative font-display text-3xl font-semibold tracking-tight sm:text-[40px] sm:leading-tight">
        {greeting}, {firstName}. What should Echo look into?
      </h1>
      <p className="relative mt-2 text-[15px] text-[#dfe6cf]">Answers come from {team.endsWith('s') ? `${team}'` : `${team}'s`} own records, and every number is cited.</p>
      <div className="relative mx-auto mt-7 max-w-[820px] space-y-5 text-left">{children}</div>
      <div className="relative mt-6 flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs text-[#dfe6cf]">
        {AGENTS.map((a) => (
          <span key={a.name} className="inline-flex items-center gap-1.5" title={a.detail}>
            <span className="grid size-[22px] place-items-center rounded-full border-[1.5px] border-white/60 text-[11px] font-bold text-white" style={{ background: a.color }}>
              {a.name[0]}
            </span>
            {a.name} · {AGENT_JOBS[a.name] ?? a.role}
          </span>
        ))}
      </div>
    </section>
  )
}

/** Answer pages: the question in a green banner, the agents' progress while Echo works, and the follow-up box once it's done. */
function AnswerBand({
  team, question, index, total, busy, headline, states, activity, mapOpen, onMap, onNew, onPresent, onStop, tipsOpen, onTips, children,
}: {
  team: string
  question: string
  index: number
  total: number
  busy: boolean
  headline: string
  states: Record<AgentName, AgentState>
  activity: Partial<Record<AgentName, string>>
  mapOpen: boolean
  onMap: () => void
  onNew: () => void
  onPresent: () => void
  onStop: () => void
  tipsOpen: boolean
  onTips: () => void
  children: React.ReactNode
}) {
  const finished = AGENTS.filter((a) => states[a.name].status === 'done').length
  const reached = Math.max(0, ...AGENTS.map((a, i) => (states[a.name].status === 'idle' ? -1 : i)))
  const light = 'inline-flex items-center gap-1.5 rounded-xl border border-white/30 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/10 disabled:opacity-50'
  return (
    <section className="ask-hero relative overflow-hidden rounded-3xl px-5 pb-5 pt-5 text-white sm:px-7 sm:pt-6">
      {[200, 360, 540, 760].map((w) => (
        <span key={w} className="ask-ring ask-ring-left" style={{ width: w, height: w }} aria-hidden />
      ))}
      <div className="relative flex flex-col gap-3 md:flex-row md:items-start">
        <div className="min-w-0 flex-1">
          <div className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-[#c8d3a8]">
            Question {index} of {total} · {team}
          </div>
          <h1 className="mt-1.5 max-w-4xl font-display text-2xl font-semibold leading-tight tracking-tight sm:text-[28px]">{question}</h1>
        </div>
        <div className="order-last flex shrink-0 flex-wrap gap-2 md:order-none">
          {busy ? (
            <button onClick={onStop} className={light}>
              <Square className="size-3" fill="currentColor" /> Stop
            </button>
          ) : (
            <>
              <button onClick={onNew} className={light}>
                <Plus className="size-3.5" /> New question
              </button>
              <button onClick={onPresent} title="Open all results for this question as a presentation in a new tab" className="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 text-xs font-semibold text-indigo-700 shadow-sm transition hover:bg-indigo-50 dark:bg-slate-900 dark:text-indigo-200">
                <Presentation className="size-3.5" /> Executive deck
              </button>
            </>
          )}
        </div>
      </div>
      <div className="relative mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-[12.5px] text-[#dfe6cf]">
        {busy ? (
          <span className="rounded-full border border-white/25 bg-white/15 px-2.5 py-0.5 font-semibold text-white">Working · {finished} of 5 agents done</span>
        ) : (
          <span className="flex gap-1" aria-hidden>
            {AGENTS.map((a) => (
              <span key={a.name} className="size-2.5 rounded-full ring-1 ring-white/50" style={{ background: a.color }} />
            ))}
          </span>
        )}
        <span aria-live="polite">{headline}</span>
        <span className="ml-auto flex gap-3">
          {!busy && (
            <button onClick={onTips} aria-expanded={tipsOpen} className="inline-flex items-center gap-1 font-medium text-white/90 hover:text-white">
              Suggested questions {tipsOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
            </button>
          )}
          <button onClick={onMap} aria-expanded={mapOpen} className="inline-flex items-center gap-1 font-medium text-white/90 hover:text-white">
            {mapOpen ? 'Hide agent map' : 'Agent map'}
          </button>
        </span>
      </div>
      {busy ? (
        <div className="relative mt-5 hidden justify-between px-2 sm:flex">
          <span className="absolute left-[10%] right-[10%] top-[19px] h-[3px] rounded-full bg-white/20" aria-hidden />
          <span className="absolute left-[10%] top-[19px] h-[3px] rounded-full bg-[#e8efd6] transition-[width] duration-700" style={{ width: `${reached * 20}%` }} aria-hidden />
          {AGENTS.map((a) => {
            const st = states[a.name].status
            return (
              <div key={a.name} className={clsx('relative w-1/5 text-center text-xs text-[#dfe6cf] transition-opacity', st === 'idle' && 'opacity-45')}>
                <span
                  className={clsx('relative mx-auto mb-1.5 grid size-10 place-items-center rounded-full border-2 border-white/70 text-sm font-bold text-white', st === 'active' && 'agent-glow')}
                  style={{ background: a.color }}
                >
                  {a.name[0]}
                  {st === 'done' && (
                    <span className="absolute -bottom-0.5 -right-0.5 grid size-4 place-items-center rounded-full bg-white text-[#4f5d2f]">
                      <Check className="size-3" strokeWidth={3} />
                    </span>
                  )}
                </span>
                <b className="block text-[12.5px] text-white">{a.name}</b>
                <span className="block truncate px-1 text-[11px] opacity-90">
                  {st === 'idle' ? 'Standing by' : st === 'done' ? 'Done' : st === 'failed' ? 'Hit a problem' : st === 'waiting' ? 'Waiting on the others' : activity[a.name] ?? 'Working'}
                </span>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="relative mt-4 space-y-3">{children}</div>
      )}
    </section>
  )
}

type View = 'home' | 'ask' | 'actions'

function Workspace({ manager, onLeave }: { manager: Manager; onLeave: () => void }) {
  // The suggestions start short; that choice is remembered.
  const [stageChoice, setStageChoice] = useState<boolean | null>(null)
  const [tipsHidden, setTipsHidden] = usePref('echo-tips-hidden', true)
  const meta = useAsync(api.meta)
  const [conversations, setConversations] = useState<Conversation[]>(() => loadConversations(manager.Manager_ID))
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [view, setView] = useState<View>('home')
  // Aaron's Action Center: opened from the sidebar, or from a Gaps card with the meeting details filled in.
  const [actionLaunch, setActionLaunch] = useState<{ token: number; prefill: SchedulerPrefill } | null>(null)
  const [actionViewKey, setActionViewKey] = useState(0)
  const [actionPlan, setActionPlan] = useState<AnswerPlan | null>(null)
  // The actions from the answers read most recently, so the Action Center tab opens on the latest one.
  const plansKey = `echo-plans-v2-${manager.Manager_ID}`
  const [recentPlans, setRecentPlans] = useState<AnswerPlan[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(plansKey) ?? '[]') as AnswerPlan[]
    } catch {
      return []
    }
  })
  const rememberPlan = useCallback(
    (plan: AnswerPlan) => {
      if (!plan.actions.length) return
      setRecentPlans((all) => {
        if (all[0]?.runId === plan.runId) return all
        const next = [plan, ...all.filter((p) => p.runId !== plan.runId && p.question.trim().toLowerCase() !== plan.question.trim().toLowerCase())].slice(0, 6)
        try {
          localStorage.setItem(plansKey, JSON.stringify(next))
        } catch {
          /* storage unavailable */
        }
        return next
      })
    },
    [plansKey],
  )
  function openActions(prefill?: SchedulerPrefill, plan: AnswerPlan | null = null) {
    if (plan) rememberPlan(plan)
    setActionPlan(plan)
    setActionLaunch((current) => (prefill ? { token: (current?.token ?? 0) + 1, prefill } : null))
    setActionViewKey((key) => key + 1)
    setView('actions')
  }
  const [question, setQuestion] = useState('')
  const [period, setPeriod] = useState('all')
  const [mode, setMode] = useState<'demo' | 'live'>('demo')
  const [activeRun, setActiveRun] = useState<string | null>(null)
  const [activePace, setActivePace] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const [error, setError] = useState('')
  const [sidebar, setSidebar] = useState(false)
  // On wide screens the sidebar can be minimized to icons; the choice is remembered in this browser.
  const [mini, setMiniState] = useState(() => {
    try {
      return localStorage.getItem('echo-sidebar-mini') === '1'
    } catch {
      return false
    }
  })
  const setMini = (next: boolean) => {
    setMiniState(next)
    try {
      localStorage.setItem('echo-sidebar-mini', next ? '1' : '0')
    } catch {
      /* storage unavailable */
    }
  }
  const [panel, setPanel] = useState<PanelTab | null>(null)
  const [thanked, setThanked] = useState<Record<string, string>>(() => loadThanked(manager.Manager_ID))
  const [seen, setSeen] = useState(() => loadSeen(manager.Manager_ID))
  const [watch, setWatch] = useState<Watched[]>(() => loadWatch(manager.Manager_ID))
  const range = PERIODS.find((p) => p.id === period)!
  const saved = useAsync(() => api.savedAnswers(manager.Manager_ID, range.start, range.end), [period, refreshKey])
  const savedSet = new Set((saved.data ?? []).map((s) => keyOf(s.question)))
  const updates = useAsync(() => api.teamUpdates(manager.Manager_ID, range.start, range.end), [period])
  const seenKey = updates.data ? `${period}|${updates.data.as_of}` : ''
  const unseen = updates.data && seen !== seenKey ? updates.data.updates.length : 0
  const openGaps = updates.data ? Math.max(0, updates.data.gaps_total - updates.data.gaps.filter((g) => thanked[g.contribution_id]).length) : 0
  const partners = useAsync(() => api.partners(manager.Manager_ID, range.start, range.end), [period])
  const overview = useAsync(() => api.overview(manager.Manager_ID, range.start, range.end), [period])

  const current = view === 'ask' ? conversations.find((c) => c.id === currentId) ?? null : null
  const message = current?.messages.at(-1) ?? null
  const viewRunId = message?.runId
  // The stage replays the active investigation step by step, or shows the finished state of the one being read.
  const stream = useRunEvents(activeRun ?? (message?.stopped ? undefined : viewRunId), activeRun ? activePace : 0, 0)
  const states = useMemo(() => agentStates(stream.events), [stream.events])
  const activity = useMemo(() => agentActivity(stream.events), [stream.events])
  const busy = activeRun !== null
  // The start page (no question open yet) gets the green banner; answers keep the plain layout.
  const landing = !current && !busy
  // The question box sits on green on the start page and in the answer banner.
  const onDark = true
  const [tipsOpen, setTipsOpen] = useState(false)
  // Close the suggestions once a new question starts.
  useEffect(() => {
    if (busy) setTipsOpen(false)
  }, [busy])
  // The agent view opens while a question runs and closes after; the manager's own choice wins until the next change.
  useEffect(() => setStageChoice(null), [busy])
  const run = useAsync(() => (viewRunId ? api.managerRun(viewRunId) : Promise.resolve(null)), [viewRunId, refreshKey])
  const connection = liveConnection(meta.data)
  const outcomes = !busy && !message?.stopped && run.data?.artifact && run.data.meta.state !== 'running' ? runOutcomes(run.data.meta, run.data.artifact) : null
  const tracked = !!message && watch.some((w) => w.question === message.question)
  // Every finished answer with suggested actions becomes available in the Action Center.
  useEffect(() => {
    if (!busy && run.data?.artifact && run.data.meta.state !== 'running') rememberPlan(planFrom(run.data.meta.id, run.data.meta.question, run.data.artifact))
  }, [busy, run.data, rememberPlan])

  const lastAgent = [...stream.events].reverse().find((e) => e.agent && e.agent !== 'original')?.agent
  const named = (Object.keys(activity) as (keyof typeof activity)[]).find((a) => a.toLowerCase() === (lastAgent ?? '').toLowerCase())
  const status = named ? `${named}: ${activity[named] ?? 'working'}…` : 'The coordinator is planning the answer…'

  useEffect(() => {
    saveConversations(manager.Manager_ID, conversations)
  }, [conversations, manager.Manager_ID])
  // Deleting chats removes them from this list (and this browser) right away, with a few seconds to undo.
  // The answers stay on the server, so a deleted question can still be asked again or found under Technical.
  const [removed, setRemoved] = useState<{ before: Conversation[]; count: number; token: number } | null>(null)
  function removeChats(ids: string[]) {
    const drop = new Set(ids)
    setRemoved({ before: conversations, count: ids.length, token: Date.now() })
    setConversations((all) => all.filter((c) => !drop.has(c.id)))
    if (currentId && drop.has(currentId)) setCurrentId(null)
  }
  function undoRemove() {
    if (removed) setConversations(removed.before)
    setRemoved(null)
  }
  useEffect(() => {
    if (!removed) return
    const timer = window.setTimeout(() => setRemoved(null), 6000)
    return () => window.clearTimeout(timer)
  }, [removed])
  // Opening "What changed" counts as having seen this quarter's updates.
  useEffect(() => {
    if (panel === 'changed' && seenKey && seen !== seenKey) {
      setSeen(seenKey)
      saveSeen(manager.Manager_ID, seenKey)
    }
  }, [panel, seenKey, seen, manager.Manager_ID])
  const closePanel = useCallback(() => setPanel(null), [])

  function thank(id: string, done: boolean) {
    const next = { ...thanked }
    if (done) next[id] = new Date().toISOString()
    else delete next[id]
    setThanked(next)
    saveThanked(manager.Manager_ID, next)
  }
  useEffect(() => {
    // Only a finish signal from the run in progress ends it; the previous brief's stream can still report "done"
    // for a moment after a new question starts, which would otherwise skip the new run's animation.
    if (stream.done && activeRun && stream.done.id === activeRun) {
      setActiveRun(null)
      setRefreshKey((k) => k + 1)
    }
  }, [stream.done, activeRun])

  // A live run has a process to stop. A demo answer is already computed, so stopping ends its playback here.
  function stop() {
    const id = activeRun
    if (!id) return
    if (message?.mode === 'live') {
      api.cancelRun(id).catch((e) => setError(e instanceof Error ? e.message : String(e)))
      return
    }
    setConversations((all) => all.map((c) => ({ ...c, messages: c.messages.map((m) => (m.runId === id ? { ...m, stopped: true } : m)) })))
    setActiveRun(null)
  }

  async function ask(text: string, fresh = false) {
    const q = text.trim()
    if (!q || busy) return
    setView('ask')
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
      if (current && !fresh) {
        // A question asked inside an open investigation is added to it, and the investigation moves to the top.
        const id = current.id
        setConversations((all) => {
          const found = all.find((c) => c.id === id)
          if (!found) return [{ id: started.id, title: q, createdAt: entry.askedAt, messages: [entry] }, ...all]
          return [{ ...found, messages: [...found.messages, entry] }, ...all.filter((c) => c.id !== id)]
        })
      } else {
        // "New investigation" (or the start page): this question opens a fresh one.
        setConversations((all) => [{ id: started.id, title: q, createdAt: entry.askedAt, messages: [entry] }, ...all])
        setCurrentId(started.id)
      }
      setView('ask')
      setQuestion('')
      setActivePace(started.mode === 'offline' ? 280 : started.mode === 'replay' ? 80 : started.mode === 'demo' ? 70 : 0)
      setActiveRun(started.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  function track(items: NonNullable<Artifact['watch']>, question = message?.question) {
    if (!question) return
    const next = [...watch.filter((w) => w.question !== question), ...items.map((i) => ({ ...i, savedAt: new Date().toISOString(), question }))]
    setWatch(next)
    saveWatch(manager.Manager_ID, next)
  }

  // A fresh investigation: back to the start page, with an empty question box and the page scrolled to the top.
  function startNew() {
    if (busy) return
    setCurrentId(null)
    setView('ask')
    setQuestion('')
    setError('')
    document.getElementById('echo-main')?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // "Ask Echo" in the sidebar always leads to the start page, so a new question can be asked at any time.
  // While Echo is still answering, it shows that answer instead; past answers stay under "Your questions".
  function goAsk() {
    if (busy) {
      setView('ask')
      document.getElementById('echo-main')?.scrollTo({ top: 0 })
    } else startNew()
  }

  // The deck reads the investigation from this browser's saved list, so it opens in a new tab of the same app.
  function present() {
    if (current) window.open(`/present/${encodeURIComponent(current.id)}`, '_blank', 'noopener')
  }


  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <img src="/favicon.svg" alt="" className="size-8" />
        <div>
          <div className="text-base font-semibold leading-tight tracking-tight">Echo</div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">Work across the org chart</div>
        </div>
        <button className="ml-auto rounded-lg p-1.5 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800" onClick={() => setSidebar(false)} aria-label="Close menu">
          <X className="size-4" />
        </button>
        <button
          className="ml-auto hidden size-8 place-items-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:text-slate-800 lg:grid dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
          onClick={() => setMini(true)}
          title="Minimize sidebar"
          aria-label="Minimize sidebar"
        >
          <PanelLeftClose className="size-4" />
        </button>
      </div>
      <nav className="space-y-1 px-3" aria-label="Main">
        <button
          onClick={() => {
            // Just navigates: a question still running keeps going and stays in the list below.
            setView('home')
            setSidebar(false)
            document.getElementById('echo-main')?.scrollTo({ top: 0 })
          }}
          aria-current={view === 'home' ? 'page' : undefined}
          className={clsx(
            'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm transition',
            view === 'home' ? 'bg-indigo-50 font-medium text-indigo-800 dark:bg-indigo-500/10 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
          )}
        >
          <House className="size-4" />
          <span className="min-w-0 flex-1 text-left">
            <span className="block truncate">Home</span>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">Your team at a glance</span>
          </span>
        </button>
        <button
          onClick={() => {
            goAsk()
            setSidebar(false)
          }}
          aria-current={view === 'ask' ? 'page' : undefined}
          className={clsx(
            'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm transition',
            view === 'ask' ? 'bg-indigo-50 font-medium text-indigo-800 dark:bg-indigo-500/10 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
          )}
        >
          <MessagesSquare className="size-4" />
          <span className="min-w-0 flex-1 text-left">
            <span className="block truncate">Ask Echo</span>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">Questions & answers</span>
          </span>
          {busy && <span className="size-2 animate-pulse rounded-full bg-indigo-500" title="Echo is answering" />}
        </button>
        <button
          onClick={() => {
            openActions(undefined, view === 'ask' && message ? recentPlans.find((p) => p.runId === message.runId) ?? recentPlans[0] ?? null : recentPlans[0] ?? null)
            setSidebar(false)
          }}
          aria-current={view === 'actions' ? 'page' : undefined}
          className={clsx(
            'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm transition',
            view === 'actions' ? 'bg-indigo-50 font-medium text-indigo-800 dark:bg-indigo-500/10 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
          )}
        >
          <WandSparkles className="size-4" />
          <span className="min-w-0 flex-1 text-left">
            <span className="block truncate">Action Center</span>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">Plan & approve</span>
          </span>
        </button>
      </nav>
      <div className="mt-5 flex-1 overflow-y-auto border-t border-slate-200/70 px-3 pt-4 dark:border-slate-800">
        <div className="mb-1.5 flex items-center gap-2 px-2">
          <span className="flex-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Your questions</span>
          {conversations.length > 1 && (
            <button onClick={() => removeChats(conversations.map((c) => c.id))} className="text-[11px] text-slate-400 hover:text-rose-600 dark:hover:text-rose-400">
              Clear all
            </button>
          )}
          <button
            onClick={() => {
              startNew()
              setSidebar(false)
            }}
            disabled={busy}
            title={busy ? 'Wait for Echo to finish this question' : 'Start a new question'}
            className="inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-[11px] font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 dark:text-indigo-300 dark:hover:bg-indigo-500/10"
          >
            <Plus className="size-3" /> New
          </button>
        </div>
        {conversations.length === 0 && <p className="px-2 text-xs text-slate-500">Your questions will appear here.</p>}
        {conversations.map((c) => (
          <div key={c.id} className="group relative">
            <button
              onClick={() => {
                setCurrentId(c.id)
                setView('ask')
                setSidebar(false)
              }}
              className={clsx(
                'block w-full truncate rounded-lg py-1.5 pl-2 pr-8 text-left text-sm transition',
                view === 'ask' && c.id === currentId ? 'bg-indigo-50 font-medium text-indigo-800 dark:bg-indigo-500/10 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
              )}
            >
              <span className="block truncate">{c.messages[0]?.question ?? c.title}</span>
              {c.messages.length > 1 && <span className="block text-[11px] font-normal text-slate-400">{c.messages.length} results</span>}
            </button>
            <button
              onClick={() => removeChats([c.id])}
              title="Delete this chat"
              aria-label={`Delete chat: ${c.messages[0]?.question ?? c.title}`}
              className="absolute right-1 top-1 grid size-7 place-items-center rounded-md text-slate-400 opacity-0 transition hover:bg-rose-50 hover:text-rose-600 focus-visible:opacity-100 group-hover:opacity-100 dark:hover:bg-rose-500/10 dark:hover:text-rose-400"
            >
              <Trash2 className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
      {removed && (
        <div role="status" className="slide-in mx-3 mb-2 flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-xs text-white shadow-lg dark:bg-slate-700">
          <span className="flex-1">{removed.count === 1 ? 'Chat deleted' : `${removed.count} chats deleted`}</span>
          <button onClick={undoRemove} className="font-semibold text-indigo-300 hover:text-indigo-200">
            Undo
          </button>
        </div>
      )}
      <div className="border-t border-slate-200 p-3 dark:border-slate-800">
        <div className="flex items-center gap-1">
          <button onClick={onLeave} className="flex flex-1 items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            <LogOut className="size-3.5" /> Switch manager
          </button>
          <Link to="/console" className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" title="Runs, evidence, connections">
            <Wrench className="size-3.5" /> Technical
          </Link>
        </div>
      </div>
    </div>
  )

  // The minimized sidebar: icons only, with the name shown on hover.
  const railItem = (label: string, icon: React.ReactNode, onClick: () => void, active = false, extra?: React.ReactNode) => (
    <button
      onClick={onClick}
      aria-label={label}
      aria-current={active ? 'page' : undefined}
      className={clsx(
        'group relative grid size-11 place-items-center rounded-xl transition',
        active ? 'bg-white text-indigo-700 shadow-sm dark:bg-indigo-500/15 dark:text-indigo-200' : 'text-slate-500 hover:bg-white/70 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200',
      )}
    >
      {icon}
      {extra}
      <span className="pointer-events-none absolute left-full top-1/2 z-50 ml-3 -translate-y-1/2 whitespace-nowrap rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition group-hover:opacity-100 group-focus-visible:opacity-100 dark:bg-slate-700">
        {label}
      </span>
    </button>
  )
  const railContent = (
    <div className="flex h-full flex-col items-center gap-1.5 py-4">
      <img src="/favicon.svg" alt="Echo" className="mb-2 size-9" />
      {railItem('Expand sidebar', <PanelLeftOpen className="size-[18px]" />, () => setMini(false))}
      <div className="my-2 h-px w-8 bg-slate-200 dark:bg-slate-800" />
      {railItem('Home', <House className="size-5" />, () => {
        setView('home')
        document.getElementById('echo-main')?.scrollTo({ top: 0 })
      }, view === 'home')}
      {railItem('Ask Echo', <MessagesSquare className="size-5" />, goAsk, view === 'ask', busy ? <span className="absolute right-2 top-2 size-2 animate-pulse rounded-full bg-indigo-500" /> : undefined)}
      {railItem('Action Center', <WandSparkles className="size-5" />, () =>
        openActions(undefined, view === 'ask' && message ? recentPlans.find((p) => p.runId === message.runId) ?? recentPlans[0] ?? null : recentPlans[0] ?? null),
      view === 'actions')}
      <div className="my-2 h-px w-8 bg-slate-200 dark:bg-slate-800" />
      {railItem('New question', <Plus className="size-5" />, () => {
        if (!busy) startNew()
      })}
      <div className="mt-auto flex flex-col items-center gap-1.5">
        {railItem('Switch manager', <LogOut className="size-[18px]" />, onLeave)}
        <Link to="/console" aria-label="Technical" className="group relative grid size-11 place-items-center rounded-xl text-slate-500 transition hover:bg-white/70 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800">
          <Wrench className="size-[18px]" />
          <span className="pointer-events-none absolute left-full top-1/2 z-50 ml-3 -translate-y-1/2 whitespace-nowrap rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition group-hover:opacity-100 dark:bg-slate-700">
            Technical
          </span>
        </Link>
      </div>
    </div>
  )

  return (
    <div className="chat-shell echo-wash flex h-full">
      <aside
        className={clsx(
          'relative z-30 hidden shrink-0 border-r border-slate-200 bg-indigo-50/50 transition-[width] duration-300 ease-out lg:block dark:border-slate-800 dark:bg-slate-900/60',
          mini ? 'w-[76px]' : 'w-64',
        )}
      >
        {mini ? railContent : sidebarContent}
      </aside>
      {sidebar && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/40" onClick={() => setSidebar(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-indigo-50 dark:bg-slate-900">{sidebarContent}</aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="relative border-b border-slate-200 bg-white/75 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
          <div className="echo-ribbon absolute inset-x-0 bottom-0 h-0.5 opacity-70" aria-hidden />
          <div className={clsx('mx-auto flex items-center gap-3 transition-[max-width] duration-300', view === 'ask' && current ? 'max-w-7xl' : mini ? 'max-w-6xl' : 'max-w-5xl')}>
            <button className="rounded-lg p-1.5 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800" onClick={() => setSidebar(true)} aria-label="Open menu">
              <PanelLeft className="size-5" />
            </button>
            <div className="flex shrink-0 items-center gap-2 sm:min-w-0 sm:shrink" title={`${manager.Manager_Name}, manager code ${manager.Manager_ID}`}>
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-800 dark:bg-indigo-500/20 dark:text-indigo-200">
                {manager.Manager_Name.split(' ').map((n) => n[0]).join('')}
              </span>
              <div className="hidden min-w-0 sm:block">
                <div className="truncate text-sm font-semibold">{manager.Manager_Name}</div>
                <div className="short-hide truncate text-xs text-slate-500">{manager.Manager_ID}</div>
              </div>
            </div>
            <div className="hidden h-8 w-px bg-slate-200 sm:block dark:bg-slate-700" />
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{manager.Primary_Team}</div>
              <div className="short-hide truncate text-xs text-slate-500">
                {manager.Primary_Department} · {manager.Pilot_Assigned_Employees} people
              </div>
            </div>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              disabled={busy}
              className="ml-auto max-w-[30%] rounded-lg sm:max-w-[40%] border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              aria-label="Time period"
            >
              {PERIODS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => setPanel(unseen ? 'changed' : openGaps ? 'gaps' : 'changed')}
              className="relative inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white shadow-sm transition hover:bg-indigo-700"
              title="What changed, goals, recognition gaps and team pulse"
              aria-label={unseen ? `Your team, ${unseen} updates` : 'Your team'}
            >
              <Users className="size-3.5" /> <span className="hidden sm:inline">Your team</span>
              {unseen > 0 && <span className="rounded-full bg-white px-1.5 text-[10px] font-semibold leading-4 text-indigo-800">{unseen}</span>}
            </button>
            <ThemeButton />
          </div>
        </header>

        <main id="echo-main" className="min-h-48 flex-1 overflow-y-auto">
          <div className={clsx('mx-auto space-y-5 px-4 py-6 transition-[max-width] duration-300', view === 'ask' && current ? 'max-w-7xl' : mini ? 'max-w-6xl' : 'max-w-5xl')}>
            {view === 'home' ? (
              <HomeDashboard
                manager={manager}
                updates={updates.data ?? null}
                updatesLoading={updates.loading}
                survey={overview.data?.survey ?? null}
                surveyLoading={overview.loading}
                latestPlan={recentPlans[0] ?? null}
                onAsk={(q) => {
                  setCurrentId(null)
                  ask(q, true)
                }}
                onGaps={() => setPanel('gaps')}
                onActions={(plan) => openActions(undefined, plan)}
                thanked={thanked}
                onRecognize={(g) =>
                  openActions({
                    title: `Recognition discussion with ${g.name}`,
                    purpose: 'Recognition discussion',
                    description: `${g.name} helped ${g.team_helped}: ${g.outcome.replace(/\.+$/, '')}. Confirm whether recognition has already occurred; the missing linked record is not proof that it did not.`,
                    origin: { kind: 'existing-evidence', label: 'Opened from Home', insightId: g.contribution_id },
                  })
                }
              />
            ) : view === 'actions' ? (
              <>
                {/* The Action Center follows the answers: pick which answer's actions to work on, or the general tools. */}
                {!actionLaunch && (recentPlans.length > 0 || actionPlan) && (
                  <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white/80 px-4 py-2.5 text-sm dark:border-slate-800 dark:bg-slate-900/80">
                    <WandSparkles className="size-4 shrink-0 text-indigo-500" />
                    <label htmlFor="plan-pick" className="shrink-0 font-medium">
                      Actions for
                    </label>
                    <select
                      id="plan-pick"
                      value={actionPlan?.runId ?? ''}
                      onChange={(e) => openActions(undefined, recentPlans.find((p) => p.runId === e.target.value) ?? null)}
                      className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950"
                    >
                      {recentPlans.map((p) => (
                        <option key={p.runId} value={p.runId}>
                          {p.question}
                        </option>
                      ))}
                      <option value="">General tools (not tied to an answer)</option>
                    </select>
                  </div>
                )}
                <ActionCenter key={actionViewKey} managerId={manager.Manager_ID} teamName={manager.Primary_Team} teamSize={manager.Pilot_Assigned_Employees} launch={actionLaunch} plan={actionPlan} />
              </>
            ) : (<>
            {(() => { const askBox = (<>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                ask(question)
              }}
              className={clsx(
                'flex items-center gap-2 rounded-2xl border bg-white p-2 pl-4 transition dark:bg-slate-900',
                onDark
                  ? 'border-transparent text-slate-900 shadow-[0_18px_50px_rgb(0_0_0/0.25)] ring-[6px] ring-white/15 focus-within:ring-white/30 dark:text-white'
                  : 'border-slate-200 shadow-[0_6px_24px_-14px_rgb(63_76_93/0.35)] focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-400/15 dark:border-slate-700',
              )}
            >
              <Newspaper className="size-5 shrink-0 text-indigo-400" />
              <input
                id="ask"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={busy}
                placeholder={
                  busy
                    ? 'Following the work…'
                    : current
                      ? mode === 'demo' ? 'Ask a follow-up (Demo: pick a suggestion)' : 'Ask a follow-up'
                      : mode === 'demo' ? "What do you want to find out about your team's work? (Demo: pick a suggestion)" : "What do you want to find out about your team's work?"
                }
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
                <button type="button" onClick={stop} className="grid size-10 place-items-center rounded-xl bg-slate-900 text-white dark:bg-white dark:text-slate-900" aria-label="Stop">
                  <Square className="size-4" fill="currentColor" />
                </button>
              ) : (
                <button disabled={!question.trim()} className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:bg-indigo-200 dark:disabled:bg-indigo-500/20" aria-label="Ask">
                  <ArrowRight className="size-5" />
                </button>
              )}
            </form>
            {error && <p className={clsx('text-sm', onDark ? 'text-center text-rose-100' : 'text-rose-600 dark:text-rose-400')}>{error}</p>}
            {!busy && (landing || tipsOpen) && (
              <div className={clsx('flex flex-wrap items-center gap-2', landing && 'justify-center')}>
                {(tipsHidden ? SUGGESTED.slice(0, SUGGESTED_SHORT) : SUGGESTED).map((q, i) => (
                  <button
                    key={q}
                    onClick={() => ask(q)}
                    className={clsx(
                      'inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs transition',
                      onDark
                        ? clsx('border-white/25 bg-white/12 text-[#f3f6ec] hover:bg-white/20', i === 0 && 'font-medium')
                        : i === 0
                        ? 'border-indigo-200 bg-indigo-50 font-medium text-indigo-800 hover:bg-indigo-100 dark:border-indigo-500/40 dark:bg-indigo-500/10 dark:text-indigo-200'
                        : 'border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-300 hover:text-indigo-800 dark:border-slate-700 dark:bg-transparent dark:text-slate-300 dark:hover:border-indigo-500',
                    )}
                  >
                    {mode === 'demo' && savedSet.has(keyOf(q)) && <History className={clsx('size-3', onDark ? 'text-white/80' : 'text-indigo-600')} />}
                    {i === 0 ? <Sparkles className="size-3" /> : <span className="size-1.5 shrink-0 rounded-full" style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }} />}
                    {q}
                  </button>
                ))}
                {!tipsHidden && (
                  <button
                    onClick={() => ask(GUARDRAIL_EXAMPLE)}
                    className={clsx(
                      'inline-flex items-center gap-1 rounded-full border border-dashed px-3 py-1 text-xs transition',
                      onDark ? 'border-rose-200/60 text-rose-100 hover:bg-white/10' : 'border-rose-200 text-rose-600 hover:bg-rose-50 dark:border-rose-500/40 dark:text-rose-300 dark:hover:bg-rose-500/10',
                    )}
                    title="See how Echo protects anonymous responses"
                  >
                    <ShieldAlert className="size-3" /> Try one Echo won't answer
                  </button>
                )}
                {/* Only offered when there are more suggestions than the short list shows. */}
                {SUGGESTED.length > SUGGESTED_SHORT && (
                  <button
                    onClick={() => setTipsHidden(!tipsHidden)}
                    aria-expanded={!tipsHidden}
                    className={clsx(
                      'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium transition',
                      onDark ? 'border border-white/25 bg-white/12 px-3 text-white hover:bg-white/20' : 'text-indigo-700 hover:bg-indigo-50 dark:text-indigo-300 dark:hover:bg-indigo-500/10',
                    )}
                  >
                    {tipsHidden ? (
                      <>
                        More questions <ChevronDown className="size-3.5" />
                      </>
                    ) : (
                      <>
                        Fewer <ChevronUp className="size-3.5" />
                      </>
                    )}
                  </button>
                )}
              </div>
            )}
            </>)
            return landing ? (
              <AskHero on firstName={manager.Manager_Name.split(' ')[0]} team={manager.Primary_Team}>{askBox}</AskHero>
            ) : current || busy ? (
              <AnswerBand
                team={manager.Primary_Team}
                question={message?.question ?? current?.title ?? ''}
                index={Math.max(1, current?.messages.length ?? 1)}
                total={Math.max(1, current?.messages.length ?? 1)}
                busy={busy}
                headline={busy ? status : message?.stopped ? 'You stopped this question' : outcomes ? outcomes.headline : 'Done. Read the brief below'}
                states={states}
                activity={activity}
                mapOpen={stageChoice === true}
                onMap={() => setStageChoice(stageChoice === true ? false : true)}
                onNew={startNew}
                onPresent={present}
                onStop={stop}
                tipsOpen={tipsOpen}
                onTips={() => setTipsOpen(!tipsOpen)}
              >
                {askBox}
              </AnswerBand>
            ) : (
              <div className="space-y-5">{askBox}</div>
            ) })()}

            {!landing && stageChoice === true && (
              <AgentStage
                states={states}
                activity={activity}
                busy={busy}
                headline={busy ? status : message?.stopped ? 'You stopped this question' : outcomes ? outcomes.headline : current ? 'Done. Read the brief below' : 'Ask a question to see how Echo finds the answer'}
                outcomes={outcomes?.agents}
                onMinimize={() => setStageChoice(false)}
              />
            )}

            {!current ? (
              <MeetingPrep managerName={manager.Manager_Name} partners={partners.data ?? []} gapCount={updates.data ? openGaps : null} visibility={null} loading={false} quarter={updates.data?.quarter ?? null} onAsk={ask} onGaps={() => setPanel('gaps')} />
            ) : (
              <>
                <section className="space-y-4">
                  {current.messages.length > 1 && (
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-700 dark:text-indigo-300">
                      Result {current.messages.length} of {current.messages.length} · latest
                    </div>
                  )}
                  {!message?.stopped && (busy || run.loading || run.data?.meta.state === 'running') ? (
                    <>
                      {busy && mode === 'demo' && updates.data?.visibility && /unnoticed|being recognized/i.test(message?.question ?? '') && (
                        <WorkJourney key={activeRun} steps={journeySteps(updates.data.visibility)} quarter={updates.data.quarter} animate />
                      )}
                      {!(busy && stageChoice === true) && <BriefPending activity={activity} />}
                    </>
                  ) : message?.stopped ? (
                    <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">You stopped this question. Ask it again above when you're ready.</p>
                  ) : run.data ? (
                    <Brief
                      meta={run.data.meta}
                      artifact={run.data.artifact}
                      managerId={manager.Manager_ID}
                      onOpenPulse={() => setPanel('pulse')}
                      onTrack={track}
                      tracked={tracked}
                      rail
                      onAct={run.data.artifact ? () => openActions(undefined, planFrom(run.data!.meta.id, run.data!.meta.question, run.data!.artifact!)) : undefined}
                    />
                  ) : (
                    <p className="text-sm text-slate-500">This answer is no longer available.</p>
                  )}
                </section>

                {current.messages.length > 1 && (
                  <section className="space-y-2.5">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Earlier results</div>
                    {current.messages
                      .slice(0, -1)
                      .map((m, i) => ({ m, n: i + 1 }))
                      .reverse()
                      .map(({ m, n }) => (
                        <EarlierResult
                          key={m.runId}
                          message={m}
                          number={n}
                          total={current.messages.length}
                          managerId={manager.Manager_ID}
                          onOpenPulse={() => setPanel('pulse')}
                          onTrack={(items) => track(items, m.question)}
                          tracked={watch.some((w) => w.question === m.question)}
                        />
                      ))}
                  </section>
                )}
              </>
            )}
            <p className="flex items-center justify-center gap-1 pb-2 text-center text-[11px] text-slate-400">
              <ShieldAlert className="size-3" /> Synthetic data · supports human review, never personnel decisions
            </p>
            </>)}
          </div>
        </main>
      </div>
      {panel && (
        <TeamPulse
          managerId={manager.Manager_ID}
          teamName={manager.Primary_Team}
          start={range.start}
          end={range.end}
          periodLabel={range.label}
          tab={panel}
          onTab={setPanel}
          onClose={closePanel}
          updates={updates.data}
          updatesError={updates.error}
          unseen={unseen}
          busy={busy}
          onAsk={(q) => {
            setPanel(null)
            ask(q)
          }}
          watch={watch}
          thanked={thanked}
          onThank={thank}
          onSchedule={(g) => {
            setPanel(null)
            openActions({
              title: `Recognition discussion with ${g.name}`,
              purpose: 'Recognition discussion',
              description: `${g.name} helped ${g.team_helped}: ${g.outcome.replace(/\.+$/, '')}. Confirm whether recognition has already occurred; the missing linked record is not proof that it did not.`,
              origin: { kind: 'existing-evidence', label: 'Opened from Gaps', insightId: g.contribution_id },
            })
          }}
        />
      )}
    </div>
  )
}

/** An earlier result in the investigation: folded to its question and first line, opens to the full brief. */
function EarlierResult({
  message,
  number,
  total,
  managerId,
  onOpenPulse,
  onTrack,
  tracked,
}: {
  message: Message
  number: number
  total: number
  managerId: string
  onOpenPulse: () => void
  onTrack: (items: NonNullable<Artifact['watch']>) => void
  tracked: boolean
}) {
  const [open, setOpen] = useState(false)
  const run = useAsync(() => api.managerRun(message.runId), [message.runId])
  const firstLine = (run.data?.artifact?.answer ?? '').replace(/\s*\[[A-Za-z]+\d*(?::[A-Za-z0-9_-]+)?\]/g, '').split(/(?<=\.)\s/)[0]
  return (
    <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-start gap-3 px-4 py-3 text-left">
        <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-indigo-50 text-[11px] font-semibold text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-200">{number}</span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold">{message.question}</span>
          <span className="block truncate text-xs text-slate-500">
            Result {number} of {total} · {new Date(message.askedAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
            {firstLine ? ` · ${firstLine}` : ''}
          </span>
        </span>
        <ChevronDown className={clsx('mt-1 size-4 shrink-0 text-slate-400 transition', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="border-t border-slate-100 p-4 dark:border-slate-800">
          {run.data ? (
            <Brief meta={run.data.meta} artifact={run.data.artifact} managerId={managerId} onOpenPulse={onOpenPulse} onTrack={onTrack} tracked={tracked} />
          ) : run.loading ? (
            <Skeleton className="h-24" />
          ) : (
            <p className="text-sm text-slate-500">This result is no longer available.</p>
          )}
        </div>
      )}
    </div>
  )
}

/** A short welcome between sign-in and the workspace; the workspace loads underneath. Click to skip. */
function Welcome({ manager, onDone }: { manager: Manager; onDone: () => void }) {
  const first = manager.Manager_Name.trim().split(/\s+/)[0] || manager.Manager_Name
  const [leaving, setLeaving] = useState(false)
  useEffect(() => {
    const out = window.setTimeout(() => setLeaving(true), 2200)
    const gone = window.setTimeout(onDone, 3400) // in case the fade-out event never fires
    return () => {
      window.clearTimeout(out)
      window.clearTimeout(gone)
    }
  }, [onDone])
  return (
    <div
      role="status"
      aria-live="polite"
      onClick={() => setLeaving(true)}
      onTransitionEnd={(event) => event.target === event.currentTarget && leaving && onDone()}
      className={clsx(
        'echo-entry-panel fixed inset-0 z-[100] grid cursor-pointer place-items-center overflow-hidden px-6 text-center text-white transition-all duration-700 ease-in-out',
        leaving ? 'pointer-events-none scale-[1.02] opacity-0' : 'opacity-100',
      )}
    >
      <Ripples className="pointer-events-none absolute left-1/2 top-1/2 size-[760px] -translate-x-1/2 -translate-y-1/2 overflow-visible text-[#c8d3a8]" />
      <div className="relative">
        <h1 className="echo-welcome-rise font-display text-5xl font-semibold tracking-tight sm:text-7xl">Hi {first},</h1>
        <p className="echo-welcome-rise mt-4 font-display text-2xl text-white/90 sm:text-3xl" style={{ animationDelay: '250ms' }}>
          Good to see you back!
        </p>
        <p className="echo-welcome-rise mt-8 text-sm tracking-wide text-[#c8d3a8]" style={{ animationDelay: '550ms' }}>
          Opening Echo · {manager.Primary_Team}
        </p>
      </div>
    </div>
  )
}

export default function ManagerApp() {
  const [manager, setManager] = useState<Manager | null>(null)
  const [checking, setChecking] = useState(true)
  const [welcome, setWelcome] = useState(false)
  const endWelcome = useCallback(() => setWelcome(false), [])

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
          setWelcome(true)
        }}
      />
    )
  return (
    <>
      <Workspace
        key={manager.Manager_ID}
        manager={manager}
        onLeave={() => {
          saveManagerCode(null)
          setManager(null)
        }}
      />
      {welcome && <Welcome manager={manager} onDone={endWelcome} />}
    </>
  )
}
