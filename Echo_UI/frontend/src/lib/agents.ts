import { BarChart3, Compass, Database, MessageSquareText, ShieldCheck, Workflow, type LucideIcon } from 'lucide-react'

export type AgentName = 'Original' | 'Cherry' | 'Vanilla' | 'Lime' | 'ZeroSugar' | 'Discovery'

export const AGENTS: { name: AgentName; label: string; role: string; detail: string; color: string; icon: LucideIcon }[] = [
  { name: 'Original', label: 'Coordinator', role: 'Coordinator', detail: 'Plans the work, delegates and writes the cited answer.', color: 'var(--color-original)', icon: Workflow },
  { name: 'Cherry', label: 'Text-to-SQL', role: 'Text-to-SQL', detail: 'Turns questions into scoped SQL over the HR and operations tables.', color: 'var(--color-cherry)', icon: Database },
  { name: 'Vanilla', label: 'Text analyst', role: 'Text RAG & sentiment', detail: 'Retrieves anonymous comments and labels survey sentiment.', color: 'var(--color-vanilla)', icon: MessageSquareText },
  { name: 'Lime', label: 'Chart builder', role: 'Charts', detail: 'Chooses evidence-bound charts, or explains why none fits.', color: 'var(--color-lime)', icon: BarChart3 },
  { name: 'ZeroSugar', label: 'Reviewer', role: 'Reviewer', detail: 'Checks citations, scope, SQL replay and rates the answer.', color: 'var(--color-zerosugar)', icon: ShieldCheck },
]

/** The sixth agent. It is not in AGENTS: the stage adds it only when the run's events name it (see events.ts). */
export const DISCOVERY = { name: 'Discovery' as AgentName, label: 'Discovery', role: 'Cross-team patterns', detail: 'Finds work that crosses teams; every finding is checked by code.', color: 'var(--color-discovery)', icon: Compass }
export const ALL_AGENTS = [...AGENTS, DISCOVERY]

export const agentByName = (name?: string) =>
  ALL_AGENTS.find((agent) => agent.name.toLowerCase() === (name ?? '').toLowerCase())

/** The plain name managers see (the internal names stay in code, logs and the run pages). */
export const agentLabel = (name?: string | null) => agentByName(name ?? '')?.label ?? name ?? ''

// Pastel chart colours (deep enough for projectors), starting with the sage and mist-blue palette colours. Power BI exports use the same list. Each series (or each bar of a one-series bar chart) takes the next one.
export const SERIES_COLORS = ['#8fa066', '#7f97b5', '#d98a99', '#e0a267', '#9c8fcb', '#6fb39a', '#d2b356', '#78a9cf']
