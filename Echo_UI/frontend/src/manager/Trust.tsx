import clsx from 'clsx'
import { CheckCircle2, Loader2, Play, ShieldCheck, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type TrustResults } from '../lib/api'
import Fold from './Fold'

// NIST AI RMF functions; Govern and Manage also list the standing design controls behind the automated checks.
const FUNCTIONS: { id: string; title: string; purpose: string; controls: string[] }[] = [
  {
    id: 'Govern',
    title: 'Govern',
    purpose: 'Policies and accountability',
    controls: [
      'Supports human review only; Echo never makes or recommends personnel decisions',
      'Synthetic data in this prototype; the manager code is a demo scope, not a secure login',
      'Every answer states whether it came from live AI, a saved answer or the offline demo',
    ],
  },
  {
    id: 'Map',
    title: 'Map',
    purpose: 'Context and risks identified',
    controls: [
      'Risks addressed: re-identification, surveillance of individuals, made-up numbers, over-reliance',
      'Agents only ever see one manager’s pilot team and chosen dates (Echo’s ScopedData layer)',
    ],
  },
  {
    id: 'Measure',
    title: 'Measure',
    purpose: 'Tested, repeatable evidence',
    controls: ['ZeroSugar reviews every live answer against its evidence before release'],
  },
  {
    id: 'Manage',
    title: 'Manage',
    purpose: 'What happens when something goes wrong',
    controls: [
      'Answers that fail review are sent back for revision; unverified answers are labelled',
      'Failed or quota-limited runs show a plain message, never partial numbers',
      'Any run can be stopped; limitations are listed with every brief',
    ],
  },
]

export default function Trust() {
  const [results, setResults] = useState<TrustResults | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.trust().then(setResults).catch((e) => setError(String(e)))
  }, [])

  async function run() {
    setRunning(true)
    setError('')
    try {
      setResults(await api.runTrust())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setRunning(false)
    }
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <ShieldCheck className="size-5 text-indigo-500" /> Trust & evaluation
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">Automated checks on the real data and code, grouped by the NIST AI Risk Management Framework.</p>
        </div>
        <button onClick={run} disabled={running} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60">
          {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />} {running ? 'Running checks…' : 'Run checks'}
        </button>
      </div>

      {results?.ran_at && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className={clsx('text-3xl font-semibold tabular-nums', results.passed === results.total ? 'text-indigo-600' : 'text-amber-600')}>
            {results.passed}/{results.total}
          </div>
          <div className="text-sm text-slate-500">
            checks passed · last run {new Date(results.ran_at).toLocaleString()}
          </div>
        </div>
      )}
      {!results?.ran_at && !running && <p className="text-sm text-slate-500">Not run yet (about 15 seconds).</p>}
      {error && <p className="text-sm text-rose-600">{error}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        {FUNCTIONS.map((fn) => {
          const checks = (results?.checks ?? []).filter((c) => c.function === fn.id)
          return (
            <Fold
              key={fn.id}
              title={fn.title}
              meta={checks.length ? `${checks.filter((c) => c.passed).length}/${checks.length} passed` : fn.purpose}
              className="h-fit rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              {checks.length > 0 && (
                <ul className="space-y-2">
                  {checks.map((check) => (
                    <li key={check.id} className={clsx('rounded-xl p-3', check.passed ? 'bg-indigo-50/70 dark:bg-indigo-500/5' : 'bg-rose-50 dark:bg-rose-500/10')}>
                      <div className="flex items-center gap-2 text-sm font-medium">
                        {check.passed ? <CheckCircle2 className="size-4 text-indigo-600" /> : <XCircle className="size-4 text-rose-600" />}
                        {check.title}
                        <span className="ml-auto text-[11px] font-normal text-slate-400">{check.seconds}s</span>
                      </div>
                      <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{check.evidence}</div>
                      <div className="mt-0.5 text-[11px] text-slate-500">{check.detail}</div>
                    </li>
                  ))}
                </ul>
              )}
              <ul className="mt-3 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
                {fn.controls.map((control) => (
                  <li key={control} className="flex gap-2">
                    <span className="text-slate-400">—</span> {control}
                  </li>
                ))}
              </ul>
            </Fold>
          )
        })}
      </div>
    </section>
  )
}
