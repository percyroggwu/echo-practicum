import clsx from 'clsx'
import { ArrowDown, ArrowRight, ArrowUp, CalendarClock, CalendarPlus, ChevronUp, Gauge, Minus, PenLine, ShieldCheck, Target, TriangleAlert, WandSparkles } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { api, type GapItem, type Manager, type SurveyRow, type TeamUpdates, type Visibility } from '../lib/api'
import { loadActions } from './actionStore'
import { statusLabel } from './ActionHistory'
import { DraftNoteDialog } from './Brief'
import { Skeleton } from './motion'
import type { Watched } from './store'
import { GapsTab, GoalsTab } from './TeamPulse'
import { ASSUMED_HOURLY_COST, FTE_QUARTER_HOURS, TAGLINE, dollars, type AnswerPlan } from './visual'

/** The survey areas shown on Home, in reading order. eNPS is a score from -100 to 100, the rest are % favorable. */
const AREAS = ['Engagement', 'Recognition', 'Workload', 'Manager support', 'Team climate', 'Development', 'Role clarity', 'eNPS'] as const

type Score = { area: string; value: number; change: number | null }

/** Team averages per area for the latest survey and the one before, weighted by responses (survey summaries only). */
function scores(rows: SurveyRow[]): { date: string | null; previous: string | null; items: Score[] } {
  const dates = [...new Set(rows.map((r) => r.Survey_Date))].sort()
  const date = dates.at(-1) ?? null
  const previous = dates.at(-2) ?? null
  const average = (d: string | null, area: string) => {
    const hits = rows.filter((r) => r.Survey_Date === d && r.Dimension === area)
    const value = (r: SurveyRow) => (area === 'eNPS' ? r.eNPS_Score : r.Favorable_Percent)
    const used = hits.filter((r) => value(r) !== null && r.Responses > 0)
    const total = used.reduce((sum, r) => sum + r.Responses, 0)
    return total ? used.reduce((sum, r) => sum + (value(r) as number) * r.Responses, 0) / total : null
  }
  const items: Score[] = []
  for (const area of AREAS) {
    const now = average(date, area)
    if (now === null) continue
    const before = average(previous, area)
    items.push({ area, value: now, change: before === null ? null : now - before })
  }
  return { date, previous, items }
}

const month = (iso: string | null) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : '')

/** Where the team stands against the company average for the same survey (3 points either way counts as level). */
function VsCompany({ value, company, enps }: { value: number; company: number | null | undefined; enps: boolean }) {
  if (company === null || company === undefined) return null
  const gap = Math.round(value - company)
  const tone = Math.abs(gap) < 3 ? 'level' : gap > 0 ? 'above' : 'below'
  return (
    <div
      title={`Company average: ${Math.round(company)}${enps ? '' : '%'}`}
      className={clsx(
        'mt-0.5 text-[10.5px] leading-tight tabular-nums',
        tone === 'above' && 'text-emerald-700 dark:text-emerald-400',
        tone === 'below' && 'font-semibold text-rose-700 dark:text-rose-400',
        tone === 'level' && 'text-slate-400',
      )}
    >
      {tone === 'level' ? '= company' : `${gap > 0 ? '+' : '−'}${Math.abs(gap)} vs company`}
    </div>
  )
}

/** One survey area as a ring: % favorable (eNPS mapped from −100..100), coloured by how much it moved. */
function Dial({ score, company }: { score: Score; company?: number | null }) {
  const enps = score.area === 'eNPS'
  const step = Math.round(score.change ?? 0)
  const tone = score.change === null || Math.abs(step) < 3 ? 'flat' : step > 0 ? 'up' : 'down'
  const Arrow = tone === 'up' ? ArrowUp : tone === 'down' ? ArrowDown : Minus
  const share = enps ? (score.value + 100) / 2 : score.value
  const colour = tone === 'down' ? (step <= -15 ? '#c25b78' : '#d98a99') : '#7b934b'
  const r = 25
  const circ = 2 * Math.PI * r
  return (
    <div className="flex min-w-0 flex-col items-center text-center">
      <svg viewBox="0 0 62 62" className="size-14 sm:size-16" aria-hidden>
        <circle cx="31" cy="31" r={r} fill="none" className="stroke-slate-100 dark:stroke-slate-800" strokeWidth="7" />
        <circle cx="31" cy="31" r={r} fill="none" stroke={colour} strokeWidth="7" strokeLinecap="round" strokeDasharray={`${(circ * Math.max(2, Math.min(100, share))) / 100} ${circ}`} transform="rotate(-90 31 31)" />
        <text x="31" y="35.5" textAnchor="middle" className="fill-slate-900 text-[13px] font-semibold dark:fill-white">
          {enps && score.value > 0 ? '+' : ''}
          {Math.round(score.value)}
          {enps ? '' : '%'}
        </text>
      </svg>
      <div className="mt-1 w-full text-[11px] font-semibold leading-tight text-slate-800 sm:text-xs dark:text-slate-200">{score.area}</div>
      {score.change !== null ? (
        <div className={clsx('inline-flex items-center gap-0.5 text-[11px] font-semibold tabular-nums', tone === 'up' && 'text-emerald-600 dark:text-emerald-400', tone === 'down' && 'text-rose-600 dark:text-rose-400', tone === 'flat' && 'text-slate-400')}>
          <Arrow className="size-3" />
          {Math.abs(step)}
        </div>
      ) : (
        <div className="text-[11px] text-slate-400">new</div>
      )}
      <VsCompany value={score.value} company={company} enps={enps} />
    </div>
  )
}

/** The iceberg: help that reached the manager sits above the water, help that didn't sits below. */
function Iceberg({ v, quarter, onAsk, onGaps }: { v: Visibility; quarter: string | null; onAsk: () => void; onGaps: () => void }) {
  const unnoticed = v.No_Praise + v.Praise_Not_Passed_On
  const seen = v.Cross_Team - unnoticed
  return (
    <section className="ice-band relative overflow-hidden rounded-3xl border border-[#d7e0e8] sm:min-h-[330px] dark:border-slate-700" aria-label={`Help your team gave other teams${quarter ? ` in ${quarter}` : ''}`}>
      <svg className="ice-berg pointer-events-none absolute top-0 hidden h-[330px] w-[570px] xl:block" viewBox="0 0 760 440" preserveAspectRatio="xMidYMin meet" aria-hidden>
        <path d="M330 150 L360 80 L392 108 L414 62 L446 128 L470 150 Z" fill="#ffffff" />
        <path d="M330 150 L470 150 L560 215 L620 300 L590 380 L480 425 L330 432 L210 395 L150 310 L190 225 Z" fill="#e9f1f5" opacity=".88" />
        <path d="M330 150 L470 150 L560 215 L520 236 L430 196 L330 206 L240 246 L190 225 Z" fill="#ffffff" opacity=".5" />
      </svg>
      <div className="absolute inset-x-0 top-[119px] border-t-2 border-white/40" aria-hidden />

      <div className="relative flex h-[119px] flex-col justify-center px-6 sm:px-8">
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[#556477] dark:text-slate-400">Above the surface · seen</span>
          <button onClick={onGaps} className="text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">
            See who
          </button>
        </div>
        <div className="font-display text-[40px] font-semibold leading-none text-[#3f5a2a] dark:text-[#c8d3a8]">{seen}</div>
        <div className="mt-1 text-[13px] text-[#556477] dark:text-slate-400">
          {v.Recognized} recognized by you · {v.Unrecognized} praise reached you
        </div>
      </div>

      {/* The iceberg sits on the right (about 540px wide), so the text keeps to the left of it. */}
      <div className="relative px-6 pb-6 pt-4 text-white sm:px-8 xl:pr-[min(520px,50%)]">
        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-white/85">Below the surface · unnoticed</span>
        <div className="mt-0.5 font-display text-5xl font-semibold leading-none sm:text-[56px]">
          {unnoticed} <span className="text-2xl opacity-75 sm:text-[26px]">of {v.Cross_Team}</span>
        </div>
        <div className="mt-1.5 max-w-[40rem] text-sm text-white/90">pieces of help your team gave other teams{quarter ? ` in ${quarter}` : ''} never reached you</div>
        <div className="mt-4 flex flex-wrap items-end gap-x-9 gap-y-3">
          <div>
            <div className="font-display text-[26px] font-semibold leading-none">{Math.round(v.Unnoticed_Hours).toLocaleString()} h</div>
            <div className="mt-1 text-xs text-white/85">about {(v.Unnoticed_Hours / FTE_QUARTER_HOURS).toFixed(1)} people's quarter</div>
          </div>
          <div>
            <div className="font-display text-[26px] font-semibold leading-none">{dollars(v.Unnoticed_Hours)}</div>
            <div className="mt-1 text-xs text-white/85">off the books, ${ASSUMED_HOURLY_COST}/h assumed</div>
          </div>
        </div>
        <button
          onClick={onAsk}
          className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm transition hover:bg-indigo-50 lg:absolute lg:bottom-5 lg:right-6 lg:mt-0 dark:bg-slate-900 dark:text-indigo-200 dark:hover:bg-slate-800"
        >
          Bring it to the surface: ask Echo <ArrowRight className="size-4" />
        </button>
      </div>
    </section>
  )
}

const TONES = ['bg-rose-100 text-rose-800', 'bg-lime-100 text-lime-900', 'bg-sky-100 text-sky-900', 'bg-amber-100 text-amber-900', 'bg-violet-100 text-violet-900']
const initials = (name: string) => name.split(/\s+/).map((w) => w[0]).join('').slice(0, 2)

const QUICK = [
  "How much of my team's cross-team work goes unnoticed or unrecognized?",
  "How is my team's morale?",
  'What happens to work that crosses team lines?',
]

/** Home: the team at a glance. Numbers only, from team-level data; every deeper look goes through Ask Echo. */
export default function HomeDashboard({
  manager,
  updates,
  updatesLoading,
  survey,
  surveyLoading,
  latestPlan,
  thanked = {},
  watch,
  onThank,
  onAsk,
  onActions,
  onRecognize,
}: {
  manager: Manager
  updates: TeamUpdates | null
  updatesLoading: boolean
  survey: SurveyRow[] | null
  surveyLoading: boolean
  latestPlan: AnswerPlan | null
  /** Contributions already marked as recognized in this browser, so they leave the waiting list. */
  thanked?: Record<string, string>
  /** Measures the manager chose to track from an answer ("Track next quarter"). */
  watch: Watched[]
  onThank: (id: string, done: boolean) => void
  onAsk: (question: string) => void
  onActions: (plan: AnswerPlan | null) => void
  /** Plan a recognition conversation in the Action Center. */
  onRecognize: (gap: GapItem) => void
}) {
  const first = manager.Manager_Name.trim().split(/\s+/)[0]
  const pulse = useMemo(() => scores(survey ?? []), [survey])
  // The company average for the same survey, so a green score that's still behind everyone else shows it.
  const [company, setCompany] = useState<Record<string, number | null> | null>(null)
  useEffect(() => {
    if (!pulse.date) return
    let live = true
    api.surveyBenchmark(pulse.date).then((b) => live && setCompany(b.areas)).catch(() => live && setCompany(null))
    return () => {
      live = false
    }
  }, [pulse.date])
  // "See who" and "See all" open the full recognition list here on Home, instead of in a side panel.
  const [gapsOpen, setGapsOpen] = useState(false)
  const gapsRef = useRef<HTMLElement>(null)
  const onGaps = () => {
    setGapsOpen(true)
    window.setTimeout(() => gapsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }
  const v = updates?.visibility ?? null
  const upcoming = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10)
    return loadActions(manager.Manager_ID)
      .filter((a) => a.status !== 'Cancelled' && a.status !== 'Completed' && a.slot.date >= today)
      .sort((a, b) => `${a.slot.date} ${a.slot.start}`.localeCompare(`${b.slot.date} ${b.slot.start}`))
  }, [manager.Manager_ID])
  const falling = pulse.items.filter((s) => s.change !== null && s.change <= -5).sort((a, b) => (a.change ?? 0) - (b.change ?? 0))
  const [draft, setDraft] = useState<GapItem | null>(null)
  // People whose praise reached the manager but who have no recognition on record yet, oldest first.
  const waiting = (updates?.gaps ?? []).filter((g) => g.praise_reached_you && !thanked[g.contribution_id]).sort((a, b) => b.age_days - a.age_days)
  const next = waiting[0] ?? null
  const capacity = updates?.updates.find((u) => u.id === 'capacity') ?? null
  const overWeeks = capacity ? /^(\d+)/.exec(capacity.title)?.[1] : undefined
  const ofWeeks = capacity ? /Out of (\d+)/.exec(capacity.detail)?.[1] : undefined
  const unnoticed = v ? v.No_Praise + v.Praise_Not_Passed_On : 0
  const mostlyHidden = !!v && unnoticed > v.Cross_Team - unnoticed

  return (
    <div className="space-y-6">
      <header>
        <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-700 dark:text-indigo-300">Echo · {TAGLINE}</div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">
          {mostlyHidden ? `Hi ${first}, most of your team's help sits below the surface` : `Hi ${first}, here's ${manager.Primary_Team} at a glance`}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {manager.Primary_Team} · {manager.Pilot_Assigned_Employees} people{updates?.quarter ? ` · ${updates.quarter}` : ''}
        </p>
      </header>

      {/* 1. The iceberg: what reached the manager, and what didn't */}
      {updatesLoading && !v ? (
        <Skeleton className="h-80 rounded-3xl" />
      ) : v && v.Cross_Team > 0 ? (
        <Iceberg v={v} quarter={updates?.quarter ?? null} onAsk={() => onAsk(QUICK[0])} onGaps={onGaps} />
      ) : (
        <p className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900">No cross-team work recorded in this period.</p>
      )}

      {/* 2. Who is waiting, the one thing to do this week, and capacity */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.25fr_1fr_0.75fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 md:col-span-2 xl:col-span-1 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <h2 className="flex-1 text-[11px] font-semibold uppercase tracking-[0.13em] text-slate-500">Waiting for your recognition · {waiting.length}</h2>
            <button onClick={onGaps} className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">
              See all <ArrowRight className="size-3.5" />
            </button>
          </div>
          {updatesLoading && !updates ? (
            <Skeleton className="mt-3 h-40" />
          ) : waiting.length ? (
            <ul className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
              {waiting.slice(0, 4).map((g, i) => (
                <li key={g.contribution_id} className="flex items-center gap-3 py-2.5">
                  <span className={clsx('grid size-8 shrink-0 place-items-center rounded-full text-[11px] font-semibold', TONES[i % TONES.length])}>{initials(g.name)}</span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{g.name}</span>
                    <span className="block truncate text-xs text-slate-500">
                      {g.team_helped} · {g.age_days} days
                    </span>
                  </span>
                  <button
                    onClick={() => setDraft(g)}
                    className="shrink-0 rounded-full border border-indigo-200 px-2.5 py-1 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-50 dark:border-indigo-500/40 dark:text-indigo-200 dark:hover:bg-indigo-500/10"
                  >
                    Recognize
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">No praised work is waiting for your recognition. Nicely done.</p>
          )}
        </section>

        <section className="flex flex-col rounded-3xl border border-amber-200/70 bg-gradient-to-br from-amber-50 to-orange-50/60 p-5 dark:border-amber-500/20 dark:from-amber-500/10 dark:to-transparent">
          <h2 className="text-[11px] font-semibold uppercase tracking-[0.13em] text-amber-700 dark:text-amber-300">Your one action this week</h2>
          {next ? (
            <>
              <p className="mt-3 font-display text-xl font-semibold leading-snug">
                Recognize {next.name} for helping {next.team_helped}
              </p>
              <p className="mt-2 text-xs text-amber-800/80 dark:text-amber-200/70">Waiting {next.age_days} days · praise reached you</p>
              <div className="mt-auto flex flex-wrap gap-2 pt-4">
                <button onClick={() => setDraft(next)} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700">
                  <PenLine className="size-4" /> Draft the note
                </button>
                <button onClick={() => onRecognize(next)} className="inline-flex items-center gap-1.5 rounded-xl border border-amber-300/70 bg-white/70 px-3.5 py-2 text-sm font-medium text-slate-700 transition hover:bg-white dark:border-amber-500/30 dark:bg-slate-900/40 dark:text-slate-200">
                  <CalendarPlus className="size-4" /> Plan a 1:1
                </button>
              </div>
            </>
          ) : falling[0] ? (
            <>
              <p className="mt-3 font-display text-xl font-semibold leading-snug">Find out why {falling[0].area.toLowerCase()} fell {Math.abs(Math.round(falling[0].change ?? 0))} points</p>
              <button onClick={() => onAsk(QUICK[1])} className="mt-auto inline-flex items-center gap-1.5 self-start rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white">
                Ask Echo <ArrowRight className="size-4" />
              </button>
            </>
          ) : (
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">Nothing urgent. Ask Echo a question to find the next thing worth doing.</p>
          )}
        </section>

        <section className="flex flex-col rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.13em] text-slate-500">
            <Gauge className="size-3.5" /> Over capacity
          </h2>
          {overWeeks ? (
            <>
              <div className="mt-3 text-[44px] font-semibold leading-none tracking-tight tabular-nums">
                {overWeeks}
                {ofWeeks && <span className="text-lg font-medium text-slate-400"> / {ofWeeks} wks</span>}
              </div>
              <p className="mt-2 text-xs text-slate-500">weeks when someone was asked for more than their project hours</p>
              {capacity?.question && (
                <button onClick={() => onAsk(capacity.question!)} className="mt-auto inline-flex items-center gap-1 self-start pt-3 text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">
                  Which weeks? <ArrowRight className="size-3.5" />
                </button>
              )}
            </>
          ) : updatesLoading ? (
            <Skeleton className="mt-3 h-16" />
          ) : (
            <p className="mt-3 text-sm text-slate-500">No week over project hours in this period.</p>
          )}
        </section>
      </div>

      {/* The full recognition list, opened from "See who" or "See all" */}
      {gapsOpen && updates && (
        <section ref={gapsRef} className="scroll-mt-4 rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <h2 className="flex-1 text-lg font-semibold tracking-tight">Who helped other teams{updates.quarter ? ` in ${updates.quarter}` : ''}</h2>
            <button onClick={() => setGapsOpen(false)} className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
              Close <ChevronUp className="size-3.5" />
            </button>
          </div>
          <div className="mt-3">
            <GapsTab updates={updates} thanked={thanked} onThank={onThank} onSchedule={onRecognize} />
          </div>
        </section>
      )}

      {/* 3. Team pulse as dials: survey averages only */}
      <section className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h2 className="flex-1 text-[11px] font-semibold uppercase tracking-[0.13em] text-slate-500">
            Team pulse{pulse.date ? ` · ${month(pulse.date)}${pulse.previous ? ` vs ${month(pulse.previous)}` : ''}` : ''}
          </h2>
          <button onClick={() => onAsk(QUICK[1])} className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">
            Ask Echo about morale <ArrowRight className="size-3.5" />
          </button>
        </div>
        {falling.length > 0 && (
          <p className="mt-3 flex items-start gap-2 rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-800 dark:bg-rose-500/10 dark:text-rose-200">
            <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
            {falling.map((s) => `${s.area} fell ${Math.abs(Math.round(s.change ?? 0))} points`).join(', ')} since the last survey.
          </p>
        )}
        {surveyLoading && !survey ? (
          <Skeleton className="mt-4 h-24" />
        ) : pulse.items.length ? (
          <div className="mt-4 grid grid-cols-4 gap-x-2 gap-y-4 sm:grid-cols-8">
            {pulse.items.map((s) => (
              <Dial key={s.area} score={s} company={company?.[s.area]} />
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No survey with enough responses in this period.</p>
        )}
        <p className="mt-4 flex items-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="size-3.5" /> Team averages only, compared with the whole company. No individual answers or comments.
        </p>
      </section>

      {/* 4. What changed and what's planned */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-lg font-semibold tracking-tight">What changed{updates?.previous_quarter ? ` since ${updates.previous_quarter}` : ''}</h2>
          <ul className="mt-3 space-y-2">
            {(updates?.updates ?? []).slice(0, 4).map((u) => (
              <li key={u.id}>
                <button
                  disabled={!u.question && u.action !== 'gaps'}
                  onClick={() => (u.question ? onAsk(u.question) : onGaps())}
                  className="flex w-full items-start gap-2.5 rounded-xl px-2 py-1.5 text-left transition enabled:hover:bg-slate-50 dark:enabled:hover:bg-slate-800"
                >
                  <span
                    className={clsx(
                      'mt-0.5 grid size-6 shrink-0 place-items-center rounded-full',
                      u.tone === 'up' && 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10',
                      u.tone === 'down' && 'bg-rose-50 text-rose-600 dark:bg-rose-500/10',
                      (u.tone === 'warn' || u.tone === 'todo') && 'bg-amber-50 text-amber-600 dark:bg-amber-500/10',
                      u.tone === 'flat' && 'bg-slate-100 text-slate-500 dark:bg-slate-800',
                    )}
                  >
                    {u.tone === 'up' ? <ArrowUp className="size-3.5" /> : u.tone === 'down' ? <ArrowDown className="size-3.5" /> : u.tone === 'flat' ? <Minus className="size-3.5" /> : <TriangleAlert className="size-3.5" />}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium">{u.title}</span>
                    <span className="block text-xs text-slate-500">{u.detail}</span>
                  </span>
                  {(u.question || u.action === 'gaps') && <ArrowRight className="mt-1 size-3.5 shrink-0 text-slate-400" />}
                </button>
              </li>
            ))}
            {updates && !updates.updates.length && <li className="text-sm text-slate-500">Nothing notable changed.</li>}
            {updatesLoading && !updates && <Skeleton className="h-24" />}
          </ul>
        </section>

        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <WandSparkles className="size-5 text-indigo-500" /> Your next steps
          </h2>
          {upcoming.length ? (
            <ul className="mt-3 space-y-2">
              {upcoming.slice(0, 3).map((a) => (
                <li key={a.id} className="flex items-start gap-2.5 text-sm">
                  <CalendarClock className="mt-0.5 size-4 shrink-0 text-slate-400" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{a.title}</span>
                    <span className="block text-xs text-slate-500">
                      {new Date(`${a.slot.date}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} · {a.slot.start} · {statusLabel(a)}
                    </span>
                  </span>
                </li>
              ))}
              {upcoming.length > 3 && <li className="text-xs text-slate-500">and {upcoming.length - 3} more</li>}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">Nothing planned yet. Ask Echo a question, then act on the answer.</p>
          )}
          {latestPlan && (
            <div className="mt-4 rounded-xl bg-indigo-50 p-3 dark:bg-indigo-500/10">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-700 dark:text-indigo-300">From your latest answer</div>
              <p className="mt-1 line-clamp-2 text-sm">{latestPlan.headline}</p>
              <p className="mt-1 text-xs text-slate-500">{latestPlan.actions.length} suggested actions</p>
            </div>
          )}
          <button onClick={() => onActions(latestPlan)} className="mt-auto inline-flex items-center gap-1 self-start pt-4 text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
            Open the Action Center <ArrowRight className="size-4" />
          </button>
        </section>
      </div>

      {/* 5. Measures the manager chose to track from an answer (only once there are some) */}
      {watch.length > 0 && updates && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <Target className="size-5 text-indigo-500" /> What you're tracking
          </h2>
          <div className="mt-2">
            <GoalsTab watch={watch} updates={updates} />
          </div>
        </section>
      )}
      {draft && <DraftNoteDialog example={draft} onClose={() => setDraft(null)} />}
    </div>
  )
}
