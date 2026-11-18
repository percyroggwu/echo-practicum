import type { Artifact, Clarification } from '../lib/api'

/** Roster candidates for an ambiguous name, or (when the metric or task is missing) the focus to look at. Choosing one resends the original question with the choice; there is no free subject selector. */
export const FOCUS_CHOICES = ['Cross-team contributions', 'Recognition survey', 'Engagement survey', 'Workload']

export default function ClarificationCard({ artifact, onChoose, onFocus }: { artifact: Artifact; onChoose: (clarification: Clarification) => void; onFocus: (focus: string) => void }) {
  const candidates = (artifact.clarification_candidates ?? []).filter((c) => c.employee_id)
  const askFocus = ['metric', 'task'].includes(artifact.clarification_basis?.missing_field ?? '')
  if (!candidates.length && !askFocus) return null
  const written = artifact.clarification_basis?.request_excerpt || artifact.question
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
      <p className="text-sm font-medium text-amber-900 dark:text-amber-200">{artifact.clarification_basis?.missing_detail || 'Who do you mean?'}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {askFocus && FOCUS_CHOICES.map((focus) => (
          <button
            key={focus}
            onClick={() => onFocus(focus)}
            className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-sm text-slate-800 hover:bg-amber-100 dark:border-amber-500/40 dark:bg-slate-900 dark:text-slate-100"
          >
            {focus}
          </button>
        ))}
        {candidates.map((c) => (
          <button
            key={c.employee_id}
            onClick={() => onChoose({ name_as_written: written, employee_id: c.employee_id })}
            className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-sm text-slate-800 hover:bg-amber-100 dark:border-amber-500/40 dark:bg-slate-900 dark:text-slate-100"
          >
            {c.name}
            {c.team ? <span className="ml-1 text-xs text-slate-500">{c.team}</span> : null}
          </button>
        ))}
      </div>
    </div>
  )
}
