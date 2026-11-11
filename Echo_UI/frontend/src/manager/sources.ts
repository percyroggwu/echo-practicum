import type { AgentName } from '../lib/agents'
import { isSql, type Artifact, type RunMeta, type SqlEvidence } from '../lib/api'

// Which kinds of records a cited query read, in words a manager uses.
const KINDS: [RegExp, string][] = [
  [/\bOP_(contributions|work_requests|projects|priority_decisions)\b/, 'work'],
  [/\bOP_capacity\b/, 'capacity'],
  [/\bHR_recognition_feedback\b/, 'feedback'],
  [/\bHR_survey_(summary|comments)\b/, 'survey'],
]

export function sourceLabel(sql: string) {
  const kinds = KINDS.filter(([pattern]) => pattern.test(sql)).map(([, kind]) => kind)
  if (!kinds.length) return 'Records'
  if (kinds.length === 1) return kinds[0] === 'survey' ? 'Survey results' : `${kinds[0][0].toUpperCase()}${kinds[0].slice(1)} records`
  return `${kinds.slice(0, 2).map((k, i) => (i ? k : k[0].toUpperCase() + k.slice(1))).join(' + ')}${kinds.length > 2 ? ' + more' : ''} records`
}

export function citedQueries(artifact: Artifact): SqlEvidence[] {
  const all = [...(artifact.evidence ?? []), ...(artifact.delegations ?? []).flatMap((d) => d.evidence ?? [])]
  const seen = new Map<string, SqlEvidence>()
  for (const item of all) if (isSql(item) && !item.sql.startsWith('--') && !seen.has(item.citation_id)) seen.set(item.citation_id, item)
  return [...seen.values()]
}

/** What each agent contributed to a finished answer, stated as plainly and as honestly as the run allows. */
export function runOutcomes(meta: RunMeta, artifact: Artifact): { agents: Partial<Record<AgentName, string>>; headline: string } {
  const queries = citedQueries(artifact)
  const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`
  const usedSurvey = queries.some((q) => /HR_survey_/.test(q.sql)) || !!artifact.voice
  const charts = artifact.visualization?.charts?.length ?? 0
  const claims = artifact.findings?.length ?? 0
  const demo = meta.mode === 'offline'
  const accepted = artifact.verification?.decision === 'accept' && artifact.status === 'complete'
  // Demo answers come from fixed queries; their numbers are recomputed, but no AI fact-checker ran.
  const checker = demo
    ? 'Demo: numbers recomputed from your data'
    : accepted
      ? `Checked ${plural(claims, 'claim')} and accepted the answer`
      : 'Did not fully verify this answer'
  return {
    agents: {
      Original: 'Wrote the brief',
      Cherry: `${plural(queries.length, 'query', 'queries')} on your team's records`,
      Vanilla: usedSurvey ? "Added your team's survey results" : 'Not needed for this question',
      Lime: charts ? plural(charts, 'chart') : 'No chart needed',
      ZeroSugar: checker,
    },
    headline: `Done · ${plural(queries.length, 'query', 'queries')} on your records · ${demo ? 'numbers recomputed (demo)' : accepted ? `${plural(claims, 'claim')} fact-checked` : 'not fully verified'}`,
  }
}
