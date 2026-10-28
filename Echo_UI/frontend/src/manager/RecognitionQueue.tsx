import clsx from 'clsx'
import { Award, Check, PenLine, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import type { Example } from '../lib/api'
import { DraftNoteDialog } from './Brief'

/** Praised cross-team work with no recognition record: draft a note, mark it done, watch the list shrink. */
export default function RecognitionQueue({ items, done, loading, onToggle, periodLabel }: { items: Example[]; done: string[]; loading: boolean; onToggle: (id: string) => void; periodLabel: string }) {
  const [tab, setTab] = useState<'open' | 'done'>('open')
  const [draft, setDraft] = useState<Example | null>(null)
  const open = items.filter((i) => !done.includes(i.contribution_id))
  const closed = items.filter((i) => done.includes(i.contribution_id))
  const shown = tab === 'open' ? open : closed

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <Award className="size-5 text-indigo-500" /> Recognition queue
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Praised by the team they helped, not yet recognized · {periodLabel}
          </p>
        </div>
        <div className="flex rounded-xl bg-slate-100 p-1 text-sm dark:bg-slate-800/60">
          {(
            [
              ['open', `Waiting (${open.length})`],
              ['done', `Recognized (${closed.length})`],
            ] as const
          ).map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} className={clsx('rounded-lg px-3 py-1', tab === id ? 'bg-white shadow-sm dark:bg-slate-900' : 'text-slate-500')}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {items.length > 0 && (
        <div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${(100 * closed.length) / items.length}%` }} />
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {closed.length} of {items.length} recognized from this list
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : shown.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500 dark:border-slate-800">
          {tab === 'open' ? 'Nothing waiting — every praised piece of cross-team work in this period has been recognized.' : 'Nothing marked as recognized yet.'}
        </p>
      ) : (
        <ul className="space-y-2">
          {shown.map((item) => (
            <li key={item.contribution_id} className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">
                  {item.name} <span className="font-normal text-slate-500">helped {item.team_helped}</span>
                </div>
                <div className="text-xs text-slate-500">
                  {item.outcome} · {item.date}
                </div>
              </div>
              {tab === 'open' && (
                <button onClick={() => setDraft(item)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:hover:border-indigo-500">
                  <PenLine className="size-3.5" /> Draft note
                </button>
              )}
              <button
                onClick={() => onToggle(item.contribution_id)}
                className={clsx(
                  'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium',
                  tab === 'open' ? 'bg-emerald-600 text-white hover:bg-emerald-500' : 'border border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800',
                )}
              >
                {tab === 'open' ? <Check className="size-3.5" /> : <RotateCcw className="size-3.5" />} {tab === 'open' ? 'Mark recognized' : 'Undo'}
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="text-xs text-slate-500">Saved in this browser only. Echo never changes HR records.</p>
      {draft && <DraftNoteDialog example={draft} onClose={() => setDraft(null)} />}
    </section>
  )
}
