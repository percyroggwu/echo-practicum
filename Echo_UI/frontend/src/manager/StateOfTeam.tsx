import clsx from 'clsx'
import { TrendingDown, TrendingUp } from 'lucide-react'
import type { SottTopic, StateOfTeam as Sott } from '../lib/api'

const LEVEL_STYLE: Record<string, string> = {
  'Basic needs': 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300',
  Individual: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
  Teamwork: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  Growth: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  Overall: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
}

export function LevelTag({ level }: { level: string }) {
  return <span className={clsx('rounded-full px-2 py-0.5 text-[11px] font-medium', LEVEL_STYLE[level] ?? LEVEL_STYLE.Overall)}>{level}</span>
}

function TopicRow({ topic }: { topic: SottTopic }) {
  return (
    <li className="flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm dark:bg-slate-800/50">
      <span className="font-medium">{topic.topic}</span>
      <LevelTag level={topic.level} />
      <span className="ml-auto tabular-nums">{topic.favorable.toFixed(0)}% favorable</span>
      {topic.change !== null && (
        <span className={clsx('inline-flex items-center gap-0.5 text-xs font-medium tabular-nums', topic.change >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400')}>
          {topic.change >= 0 ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />}
          {topic.change >= 0 ? '+' : ''}
          {topic.change.toFixed(0)}
        </span>
      )}
    </li>
  )
}

/** Gallup's State of the Team flow, filled in from the team's data: goal → results → focus → review. */
export default function StateOfTeam({ data }: { data: Sott }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="text-base font-semibold">State of the Team conversation guide</div>
        <div className="text-xs text-slate-500">Based on the {data.survey} survey</div>
      </div>
      <p className="mt-1 text-xs text-slate-500">Follows Gallup's State of the Team flow. Echo prepares the evidence; the team decides.</p>
      <ol className="mt-4 space-y-4">
        {data.steps.map((step, i) => (
          <li key={step.title} className="flex gap-4">
            <span className="grid size-8 shrink-0 place-items-center rounded-full border-2 border-indigo-500 text-sm font-semibold text-indigo-600 dark:text-indigo-300">{i + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="font-semibold">{step.title}</div>
              <p className="text-sm text-slate-500">{step.summary}</p>
              {step.items && step.items.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm">
                  {step.items.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="text-indigo-500">•</span> {item}
                    </li>
                  ))}
                </ul>
              )}
              {step.strengths && (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Strengths to keep</div>
                    <ul className="space-y-1.5">{step.strengths.map((t) => <TopicRow key={t.topic} topic={t} />)}</ul>
                  </div>
                  <div>
                    <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-400">Opportunities</div>
                    <ul className="space-y-1.5">{(step.opportunities ?? []).map((t) => <TopicRow key={t.topic} topic={t} />)}</ul>
                  </div>
                </div>
              )}
              {step.questions && step.questions.length > 0 && (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl bg-indigo-50/60 p-3 dark:bg-indigo-500/5">
                    <div className="mb-1 text-xs font-semibold text-indigo-700 dark:text-indigo-300">Ask the team</div>
                    <ul className="space-y-1 text-sm">
                      {step.questions.map((q) => (
                        <li key={q}>“{q}”</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
                    <div className="mb-1 text-xs font-semibold text-slate-600 dark:text-slate-300">Possible actions · owner agreed in the room</div>
                    <ul className="space-y-1 text-sm">
                      {(step.actions ?? []).map((a) => (
                        <li key={a} className="flex gap-2">
                          <span className="text-slate-400">☐</span> {a} <span className="ml-auto shrink-0 text-xs text-slate-400">Owner: ____</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-500 dark:border-slate-800">{data.note}</p>
    </section>
  )
}
