import clsx from 'clsx'
import { useEffect, useState } from 'react'
import type { Visibility } from '../lib/api'

const STEP_MS = 800

export function journeySteps(v: Visibility) {
  return [
    { label: 'Helped another team', value: v.Cross_Team },
    { label: 'Praised by that team', value: v.Praised ?? 0 },
    { label: 'Praise reached you', value: v.Praise_Reached ?? 0 },
    { label: 'Recognized by a manager', value: v.Recognized },
  ]
}

/** How far the team's cross-team work travelled. It fills in step by step while an answer loads, then stays with the answer. */
export default function WorkJourney({ steps, quarter, animate = false }: { steps: { label: string; value: number }[]; quarter: string | null; animate?: boolean }) {
  const total = steps[0]?.value ?? 0
  const [shown, setShown] = useState(() => (animate && !window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 1 : steps.length))
  useEffect(() => {
    if (shown >= steps.length) return
    const timer = window.setTimeout(() => setShown((n) => n + 1), STEP_MS)
    return () => window.clearTimeout(timer)
  }, [shown, steps.length])

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" aria-label="How far your team's cross-team work travelled">
      <h3 className="text-sm font-semibold">{animate ? "Following your team's cross-team work" : "How far your team's cross-team work travelled"}</h3>
      <p className="mt-0.5 text-xs text-slate-500">{quarter}, from your team's records</p>
      <ol className="mt-4 space-y-3">
        {steps.map((step, i) => (
          <li key={step.label} className={clsx('transition-opacity duration-500', i < shown ? 'opacity-100' : 'opacity-0')}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="text-slate-600 dark:text-slate-300">{step.label}</span>
              <span className="font-semibold tabular-nums">{step.value}</span>
            </div>
            <div className="mt-1 h-2 rounded-r bg-slate-100 dark:bg-slate-800">
              <div
                className="h-full rounded-r bg-indigo-500 transition-[width] duration-700 ease-out dark:bg-indigo-400"
                style={{ width: i < shown && total ? `${(100 * step.value) / total}%` : 0 }}
              />
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-[11px] text-slate-500">Each count comes from its own records, so a later step can include work that skipped an earlier one.</p>
    </section>
  )
}
