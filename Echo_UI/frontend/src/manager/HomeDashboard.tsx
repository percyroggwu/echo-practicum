import clsx from 'clsx'
import { ArrowDown, ArrowRight, ArrowUp, CalendarClock, HeartPulse, Minus, Newspaper, ShieldCheck, Sparkles, TriangleAlert, WandSparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Manager, SurveyRow, TeamUpdates } from '../lib/api'
import { loadActions } from './actionStore'
import { Skeleton } from './motion'
import { ASSUMED_HOURLY_COST, FTE_QUARTER_HOURS, Tiles, dollars, type AnswerPlan } from './visual'

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

function ScoreCard({ score }: { score: Score }) {
  const enps = score.area === 'eNPS'
  const step = Math.round(score.change ?? 0)
  const tone = score.change === null || Math.abs(step) < 3 ? 'flat' : step > 0 ? 'up' : 'down'
  const Arrow = tone === 'up' ? ArrowUp : tone === 'down' ? ArrowDown : Minus
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="truncate text-xs font-medium text-slate-500">{score.area}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums tracking-tight">
          {enps && score.value > 0 ? '+' : ''}
          {Math.round(score.value)}
          {enps ? '' : '%'}
        </span>
        {score.change !== null && (
          <span
            className={clsx(
              'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[11px] font-semibold tabular-nums',
              tone === 'up' && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300',
              tone === 'down' && 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300',
              tone === 'flat' && 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
            )}
          >
            <Arrow className="size-3" />
            {step > 0 ? '+' : ''}
            {step}
          </span>
        )}
      </div>
      {!enps && (
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div className={clsx('h-full rounded-full', tone === 'down' ? 'bg-rose-400' : 'bg-indigo-500')} style={{ width: `${Math.max(2, Math.min(100, score.value))}%` }} />
        </div>
      )}
      <div className="mt-1.5 text-[11px] text-slate-400">{enps ? 'eNPS, −100 to 100' : 'favorable'}</div>
    </div>
  )
}

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
  onAsk,
  onGaps,
  onActions,
}: {
  manager: Manager
  updates: TeamUpdates | null
  updatesLoading: boolean
  survey: SurveyRow[] | null
  surveyLoading: boolean
  latestPlan: AnswerPlan | null
  onAsk: (question: string) => void
  onGaps: () => void
  onActions: (plan: AnswerPlan | null) => void
}) {
  const [question, setQuestion] = useState('')
  const first = manager.Manager_Name.trim().split(/\s+/)[0]
  const pulse = useMemo(() => scores(survey ?? []), [survey])
  const v = updates?.visibility ?? null
  const upcoming = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10)
    return loadActions(manager.Manager_ID)
      .filter((a) => a.status !== 'Cancelled' && a.status !== 'Completed' && a.slot.date >= today)
      .sort((a, b) => `${a.slot.date} ${a.slot.start}`.localeCompare(`${b.slot.date} ${b.slot.start}`))
  }, [manager.Manager_ID])
  const falling = pulse.items.filter((s) => s.change !== null && s.change <= -5).sort((a, b) => (a.change ?? 0) - (b.change ?? 0))

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Hi {first}, here's {manager.Primary_Team} at a glance</h1>
        <p className="mt-1 text-sm text-slate-500">
          {manager.Pilot_Assigned_Employees} people{updates?.quarter ? ` · latest quarter ${updates.quarter}` : ''}
        </p>
      </header>

      {/* 1. The headline problem: help to other teams that nobody saw */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="flex-1 text-lg font-semibold tracking-tight">Help your team gave other teams{updates?.quarter ? ` in ${updates.quarter}` : ''}</h2>
          <button onClick={onGaps} className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
            See who <ArrowRight className="size-4" />
          </button>
        </div>
        <div className="mt-4">
          {updatesLoading && !v ? (
            <Skeleton className="h-28 rounded-2xl" />
          ) : v ? (
            <Tiles
              tiles={[
                { value: `${v.No_Praise + v.Praise_Not_Passed_On} of ${v.Cross_Team}`, label: 'pieces of help went unnoticed', icon: 'eye', tone: 'no_praise' },
                { value: `${Math.round(v.Unnoticed_Hours).toLocaleString()} h`, label: `of unnoticed work, about ${(v.Unnoticed_Hours / FTE_QUARTER_HOURS).toFixed(1)} people's quarter`, icon: 'hours', tone: 'not_passed' },
                { value: dollars(v.Unnoticed_Hours), label: `of work off the books (at $${ASSUMED_HOURLY_COST}/h, assumed)`, icon: 'cost', tone: 'money' },
                { value: `${v.Unrecognized}`, label: 'praised by another team, not yet recognized by you', icon: 'award', tone: 'unrecognized' },
              ]}
            />
          ) : (
            <p className="text-sm text-slate-500">No cross-team work recorded in this period.</p>
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={() => onAsk(QUICK[0])} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700">
            <Sparkles className="size-4" /> Ask Echo what's behind this
          </button>
        </div>
      </section>

      {/* 2. Team pulse: survey averages only */}
      <section className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1">
            <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
              <HeartPulse className="size-5 text-rose-500" /> Team pulse
            </h2>
            <p className="text-xs text-slate-500">
              Survey of {month(pulse.date)}
              {pulse.previous ? `, change since ${month(pulse.previous)}` : ''}
            </p>
          </div>
          <button onClick={() => onAsk(QUICK[1])} className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400">
            Ask Echo about morale <ArrowRight className="size-4" />
          </button>
        </div>
        {falling.length > 0 && (
          <p className="flex items-start gap-2 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:bg-rose-500/10 dark:text-rose-200">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            {falling.map((s) => `${s.area} fell ${Math.abs(Math.round(s.change ?? 0))} points`).join(', ')} since the last survey.
          </p>
        )}
        {surveyLoading && !survey ? (
          <Skeleton className="h-48 rounded-2xl" />
        ) : pulse.items.length ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {pulse.items.map((s) => (
              <ScoreCard key={s.area} score={s} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No survey with enough responses in this period.</p>
        )}
        <p className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="size-3.5" /> Team averages only. No individual answers or comments are shown.
        </p>
      </section>

      {/* 3. What changed and what's planned */}
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
                      {new Date(`${a.slot.date}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })} · {a.slot.start} · {a.status}
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

      {/* 4. A way in to Ask Echo */}
      <section className="rounded-2xl border border-slate-200 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-900/70">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (question.trim()) onAsk(question)
          }}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-1.5 pl-3 focus-within:border-indigo-400 dark:border-slate-700 dark:bg-slate-900"
        >
          <Newspaper className="size-4 shrink-0 text-indigo-400" />
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask Echo about your team's work" className="min-w-0 flex-1 bg-transparent py-1.5 text-sm outline-none placeholder:text-slate-400" />
          <button disabled={!question.trim()} className="grid size-8 place-items-center rounded-lg bg-indigo-600 text-white disabled:bg-indigo-200 dark:disabled:bg-indigo-500/20" aria-label="Ask">
            <ArrowRight className="size-4" />
          </button>
        </form>
        <div className="mt-2.5 flex flex-wrap gap-2">
          {QUICK.map((q) => (
            <button key={q} onClick={() => onAsk(q)} className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 transition hover:border-indigo-300 hover:text-indigo-800 dark:border-slate-700 dark:text-slate-300">
              {q}
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
