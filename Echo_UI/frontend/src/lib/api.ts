// Typed client for the local Echo UI backend (Echo_UI/backend/app.py).

export type Profile = {
  name: string
  provider: string
  model: string
  description: string
  key_configured: boolean
}

export type Meta = {
  profiles: Profile[]
  default_profile: string
  local_split: Record<string, string> | null
  scope_min: string
  scope_max: string
  database?: 'legacy' | 'discovery_v1'
  fixed_range?: { start: string; end: string } | null
  suggested_questions: string[]
  /** The first five questions: the short label shown on the chip, and the full question sent to Echo. */
  suggested_prompts?: { label: string; prompt: string }[]
}

export type Manager = {
  Manager_ID: string
  Manager_Name: string
  Primary_Department: string
  Primary_Team: string
  Pilot_Assigned_Employees: number
}

export type SurveyRow = {
  Survey_Date: string
  Team: string
  Dimension: string
  Responses: number
  Eligible_Employees: number
  Mean_Score: number | null
  Favorable_Percent: number | null
  eNPS_Score: number | null
}

export type Overview = {
  manager: { Manager_ID: string; Manager_Name: string }
  teams: string[]
  scope: Scope
  headcount: number
  contributions: number
  comments: number
  survey: SurveyRow[]
}

export type Scope = { manager_id: string; start_date: string; end_date: string }

export type RunMeta = {
  id: string
  question: string
  typed_question: string
  manager_id: string
  start_date: string
  end_date: string
  mode: 'demo' | 'live' | 'replay' | 'offline'
  profile: string
  replay_of?: string
  recorded_at?: string
  created_at: string
  finished_at?: string
  state: string
  exit_code?: number
  result_status?: string
  verification?: string
  api_calls?: number
  charts?: number
}

export type SqlEvidence = {
  citation_id: string
  producer: string
  sql: string
  rows: Record<string, unknown>[]
  truncated: boolean
}

export type TextEvidence = {
  citation_id: string
  source: string
  record_id: string
  team?: string
  date?: string
  dimension?: string
  anonymous?: boolean
  text: string
}

export type Evidence = SqlEvidence | TextEvidence | (Record<string, unknown> & { citation_id: string })

export type Finding = {
  finding_id: string
  text: string
  citation_ids: string[]
  status: string
  reason: string
  deterministic_issues: unknown[]
  evidence_status?: 'supported' | 'withheld'
  release_blockers?: string[]
  assertions?: {
    assertion_id?: string
    claim: string
    kind: 'factual' | 'proposal'
    citation_ids: string[]
    assessment: 'supported' | 'contradicted' | 'insufficient_evidence'
    reason: string
  }[]
}

export type Review = {
  version?: string
  explanation_quality?: {
    status: 'complete' | 'incomplete'
    invalid_dimensions: string[]
    semantic_quality_verified: boolean
    repair_calls: number
  } | null
  release_gate?: {
    policy: string
    active: boolean
    issue_indices: number[]
    issues: string[]
    unexplained_low_score: boolean
    invalid_link_count: number
  } | null
  correction_judgments?: Record<string, { mandatory: boolean; addressed: boolean; reason: string }>
  decision: string
  ratings: Record<string, { score: number; rationale: string }>
  issues: unknown[]
  uncertainty: string
  deterministic_issues: unknown[]
  mode: string
  findings: Finding[]
  repair_targets: unknown[]
  clarification_question: string | null
}

export type ChartSpec = {
  source_id: string
  kind: string
  x: string
  y: string
  series?: string
  title: string
  x_label: string
  y_label: string
  unit?: string
  denominator?: string
}

export type Artifact = {
  agent: string
  question: string
  answer: string
  scope: Scope
  evidence: Evidence[]
  mode: string
  status: string
  verification: {
    decision?: string; status?: string; reviews?: Review[]; drafts_checked?: number; completed_reviews?: number
    latest_candidate_id?: string; released_candidate_id?: string | null; reviewed_candidate_id?: string
    release_counts?: { reviewed: number; supported: number; released: number; withheld_by_assertion_or_evidence?: number; withheld_by_release_gate?: number }
    release_gate?: Review['release_gate']
  }
  delegations: { agent: string; question: string; answer: string; evidence: Evidence[] }[]
  visualization: { charts?: ChartSpec[]; reason?: string; files?: { source_id: string; svg: string; csv: string; metadata: string }[] }
  rag: Record<string, unknown>
  execution: { generation_api_calls?: number; successful_generation_api_calls?: number; profiles_used?: Record<string, { model: string; api_calls: number }> }
  capture?: { run_id?: string; exchanges?: string; resume_checkpoint?: string | null; parent_run_id?: string; source_checkpoint?: string; phase_only?: boolean }
  sentiment: Record<string, unknown>
  findings: Finding[]
  limitations: string[]
  next_steps: string[]
  clarification_questions: string[]
  failure: Record<string, unknown>
  made?: Made
  triangle?: Triangle
  examples?: Example[]
  watch?: WatchItem[]
  voice?: { topic: string; responses: number; positive: number; negative: number }
  /** Business meaning of the result (offline demo answers): impact and risk, team-level, no causal claims. */
  impact?: string[]
  /** Plain sentences for "What this means" (Live: built by the backend presenter from Echo's numbers). */
  meaning?: string[]
  guardrail?: { rule: string; checked_by: string; detail: string }
  /** The Discovery section, checked by code (manager view only). */
  discovery_section?: DiscoverySection
  /** Structured Discovery findings (manager view): one card per person. */
  discovery?: DiscoveryView
  /** 'echo' when the story fields were built from Echo's own results (Live), not the offline demo. */
  story_source?: 'echo'
  metrics?: Metric[]
  state_of_team?: StateOfTeam
  journey?: { quarter: string; steps: { label: string; value: number }[] }
  /** What the Worth recognizing list is, when it isn't praised work (for example, self-review items). */
  examples_note?: string
  /** The answer card (offline demo answers): one sentence, a few number tiles, and actions the Action Center opens filled in. */
  headline?: string
  tiles?: Tile[]
  actions?: AnswerAction[]
  clarification_candidates?: ClarificationCandidate[]
  clarification_basis?: { missing_field: string; missing_detail: string; request_excerpt?: string } | null
}

export type ClarificationCandidate = { employee_id: string; name: string; team?: string; manager_id?: string }
export type Clarification = { name_as_written: string; employee_id: string }

/** Colours shared by tiles, actions and the Gaps bar: the four visibility groups, plus money and neutral. */
export type VisTone = 'no_praise' | 'not_passed' | 'unrecognized' | 'recognized' | 'money' | 'neutral'
export type Tile = { value: string; label: string; icon: string; tone: VisTone }
export type AnswerAction = {
  kind: 'recognize' | 'one_to_one' | 'partner' | 'plan' | 'goal' | 'handoff' | 'team_event' | 'room' | 'email'
  title: string
  why: string
  tone: VisTone
  person?: { id: string; name: string }
  partner?: { team: string | null; name: string | null; email: string | null } | null
  partner_team?: string
  example_id?: string
  /** The Discovery A1 action this recognize action mirrors; its decision lives in the backend action record. */
  discovery_action_id?: string
  event?: { title: string; invitation: string }
  room?: { title: string; agenda: string }
  email?: { subject: string; body: string; to?: string }
}

export type SottTopic = { topic: string; favorable: number; change: number | null; level: string; rank: number; meaning: string }
export type StateOfTeam = {
  survey: string
  note: string
  steps: { title: string; summary: string; items?: string[]; strengths?: SottTopic[]; opportunities?: SottTopic[]; focus?: string | null; questions?: string[]; actions?: string[] }[]
}

export type TrustCheck = { id: string; function: string; title: string; detail: string; passed: boolean; evidence: string; seconds: number }
export type TrustResults = { ran_at: string | null; checks: TrustCheck[]; passed: number; total: number }

export type Metric = { label: string; value: string; change: string | null; tone: 'good' | 'fair' | 'poor' | 'neutral' }

export type TriangleSide = { value: string; label: string; tone: 'good' | 'fair' | 'poor' | 'neutral'; agent: string }
export type Triangle = { work: TriangleSide; feedback: TriangleSide; voice: TriangleSide; agreement: 'conflict' | 'aligned'; note: string }
export type Example = { contribution_id: string; employee_id: string; name: string; team_helped: string; date: string; outcome: string; praise_reached_you: boolean; self_review?: boolean }
export type WatchItem = { metric: string; baseline: string; goal: string }

export type Made = {
  specialists: string[]
  queries: number
  survey_sources: number
  sentiment_runs: number
  charts: number
  findings_checked: number
  drafts_checked: number
  completed_reviews?: number
  review_status?: string
}

export type PulseTheme = { text: string; share: 'most' | 'many' | 'some' | 'a few'; tone: 'positive' | 'concern' | 'mixed' }

export type Pulse = {
  scope: Scope
  mood: { topic: string; responses: number; positive: number; neutral: number; negative: number }[]
  themes: { topic: string; headline: string; themes: PulseTheme[]; comments_used: number }[] | null
  generated_at: string | null
  model: string | null
  error: string | null
}

export type TeamUpdate = { id: string; tone: 'up' | 'down' | 'flat' | 'warn' | 'todo'; title: string; detail: string; question?: string; action?: 'gaps' }
export type GapItem = Example & { age_days: number }
export type Visibility = { Cross_Team: number; Cross_Team_Hours: number; Praised?: number; Praise_Reached?: number; No_Praise: number; Praise_Not_Passed_On: number; Unrecognized: number; Recognized: number; Unnoticed_Hours: number }
export type Partner = { Team: string; Contributions: number; Praise_Not_Passed_On: number; Contact_Name: string | null; Contact_Email: string | null }
export type ExecutiveSummary = { quarter: string; problem: string; size: string; doing: string; need: string; report: string; note: string }
export type OrgDepartment = Visibility & { Department: string; All_Hours: number }
export type OrgOverview = {
  start: string
  end: string
  totals: Visibility & { All_Hours: number }
  departments: OrgDepartment[]
  dependencies: { Helper: string; Helped: string; Contributions: number; Hours: number }[]
  late: { inside?: number; crossing?: number }
  hours_per_fte: number
  assumed_hourly_cost: number
}
export type TeamUpdates = {
  quarter: string | null
  previous_quarter: string | null
  as_of: string | null
  updates: TeamUpdate[]
  gaps: GapItem[]
  gaps_total: number
  measures: Record<string, string>
  visibility: Visibility | null
}

export type DiscoverySection = { present: boolean; status: string; finding_ids: string[]; reviewed_by_zerosugar: boolean; checked_by_code: boolean; rendered: string }
export type DiscoveryFinding = {
  finding_id: string
  kind: string
  employee_ids: string[]
  employee_names: string[]
  beneficiary_team: string
  work_summary: string
  why_it_matters: string
  visibility_state: 'praise_not_shared' | 'no_feedback' | 'shared'
  recognition_state: 'recognized' | 'not_recognized' | 'unknown'
  contribution_id: string | null
  contribution_date: string | null
  evidence_ids: string[]
  actions: { action_id: string; action_type: ActionType; subject_id?: string; beneficiary_team?: string; recipient?: unknown; draft_text: string }[]
}
export type DiscoveryView = {
  status: string
  period?: { start?: string; end?: string; as_of?: string; hint_not_applied?: boolean }
  coverage?: { team_size?: number; people_reviewed?: number }
  findings: DiscoveryFinding[]
}
export type WorkRef = { type: string; id: string }
export type ActionType = 'A1' | 'A2' | 'A3' | 'A4' | 'A5' | 'A6'
export type ActionState = 'proposed' | 'accepted' | 'edited' | 'dismissed'
export type DiscoveryAction = {
  action_id: string
  /** The Discovery action's own id (the backend record id is run_id:source_action_id). */
  source_action_id?: string
  run_id: string
  finding_id: string
  subject_kind: string
  subject_id: string
  beneficiary_team: string
  recipient?: string
  allowed_work_refs: WorkRef[]
  state: ActionState
  current: { version: number; state: ActionState; action_type: ActionType; draft_text: string; work_refs: WorkRef[]; reason?: string | null }
}
export type FollowUp = { status: 'observed' | 'not_yet' | 'unknown' | 'pending_decision' | 'dismissed'; action_type: string; reason?: string }
export type ActionDecision = { state: 'accepted' | 'edited' | 'dismissed'; reason?: string; draft_text?: string; action_type?: ActionType; work_refs?: WorkRef[] }

export type RunDetail = { meta: RunMeta; artifact: Artifact | null; console: string }

export type LogEvent = {
  time_utc: string
  run_id: string
  elapsed_seconds: number
  event: string
  agent?: string
  profile?: string
  tool?: string
  tools?: string[]
  error_category?: string
  http_status?: number
  status?: string
  [key: string]: unknown
}

export type Quota = {
  limit_per_model: number
  resets_at: string
  models: { model: string; calls: number; quota_errors: number }[]
  note: string
}

export type TableInfo = {
  name: string
  rows: number
  columns: { Column: string; Meaning: string; Primary_Key: string; References: string; Nullable: string }[]
}

/** Fired when the backend says the manager's sign-in has ended, so the app can return to the login page. */
export const SIGNED_OUT_EVENT = 'echo-signed-out'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // The Technical console stays open without a login; it says so on each request.
  const consolePage = typeof window !== 'undefined' && window.location.pathname.startsWith('/console')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (consolePage) headers['X-Echo-Console'] = '1'
  const response = await fetch(path, { headers, credentials: 'same-origin', ...init })
  if (response.status === 401 && !consolePage && !path.startsWith('/api/auth/')) {
    window.dispatchEvent(new Event(SIGNED_OUT_EVENT))
  }
  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = (await response.json()).detail ?? detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json()
}

export const api = {
  meta: () => request<Meta>('/api/meta'),
  managers: () => request<Manager[]>('/api/managers'),
  overview: (id: string, start: string, end: string) =>
    request<Overview>(`/api/managers/${encodeURIComponent(id)}/overview?start=${start}&end=${end}`),
  tables: () => request<TableInfo[]>('/api/data/tables'),
  quota: () => request<Quota>('/api/quota'),
  runs: () => request<RunMeta[]>('/api/runs'),
  run: (id: string) => request<RunDetail>(`/api/runs/${id}`),
  registerActions: (manager: string, runId: string) =>
    request<{ actions: DiscoveryAction[] }>(`/api/managers/${encodeURIComponent(manager)}/actions`, { method: 'POST', body: JSON.stringify({ run_id: runId }) }),
  listActions: (manager: string) => request<{ actions: DiscoveryAction[] }>(`/api/managers/${encodeURIComponent(manager)}/actions`),
  decideAction: (manager: string, actionId: string, decision: ActionDecision) =>
    request<DiscoveryAction>(`/api/managers/${encodeURIComponent(manager)}/actions/${encodeURIComponent(actionId)}`, { method: 'PATCH', body: JSON.stringify(decision) }),
  actionFollowUp: (manager: string) => request<{ results: Record<string, FollowUp> }>(`/api/managers/${encodeURIComponent(manager)}/actions/follow-up`),
  managerRun: (id: string) => request<RunDetail>(`/api/runs/${id}?view=manager`),
  pulse: (id: string, start: string, end: string, generate = false) =>
    request<Pulse>(`/api/managers/${encodeURIComponent(id)}/pulse?start=${start}&end=${end}${generate ? '&generate=true' : ''}`),
  teamUpdates: (id: string, start: string, end: string) =>
    request<TeamUpdates>(`/api/managers/${encodeURIComponent(id)}/updates?start=${start}&end=${end}`),
  savedAnswers: (id: string, start: string, end: string) =>
    request<{ question: string; recorded_at: string | null }[]>(`/api/recordings?manager_id=${encodeURIComponent(id)}&start=${start}&end=${end}`),
  executiveSummary: (id: string, start: string, end: string) =>
    request<ExecutiveSummary | null>(`/api/managers/${encodeURIComponent(id)}/executive-summary?start=${start}&end=${end}`),
  orgOverview: () => request<OrgOverview>('/api/org/overview'),
  /** Company-wide survey averages for one survey date (% favorable, or the eNPS score). */
  surveyBenchmark: (date: string) =>
    request<{ date: string; teams: number; areas: Record<string, number | null> }>(`/api/org/survey-benchmark?date=${encodeURIComponent(date)}`),
  partners: (id: string, start: string, end: string) =>
    request<Partner[]>(`/api/managers/${encodeURIComponent(id)}/partners?start=${start}&end=${end}`),
  recognitionQueue: (id: string, start: string, end: string) =>
    request<Example[]>(`/api/managers/${encodeURIComponent(id)}/recognition-queue?start=${start}&end=${end}`),
  trust: () => request<TrustResults>('/api/trust'),
  runTrust: () => request<TrustResults>('/api/trust/run', { method: 'POST' }),
  lookupManager: (code: string) => request<Manager>(`/api/manager/${encodeURIComponent(code)}`),
  login: (managerId: string, password: string) =>
    request<{ manager_id: string }>('/api/auth/login', { method: 'POST', body: JSON.stringify({ manager_id: managerId, password }) }),
  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
  me: () => request<{ manager_id: string }>('/api/auth/me'),
  startRun: (body: Record<string, unknown>) => request<RunMeta>('/api/runs', { method: 'POST', body: JSON.stringify(body) }),
  cancelRun: (id: string) => request<unknown>(`/api/runs/${id}/cancel`, { method: 'POST' }),
  deleteRun: (id: string) => request<unknown>(`/api/runs/${id}`, { method: 'DELETE' }),
  fileUrl: (id: string, path: string) => `/api/runs/${id}/files/${path.split('/').pop()}`,
  chartCsvUrl: (id: string, source: string) => `/api/runs/${id}/charts/${encodeURIComponent(source)}/data.csv`,
  chartPowerBiUrl: (id: string, source: string) => `/api/runs/${id}/charts/${encodeURIComponent(source)}/powerbi.zip`,
  chartTableauUrl: (id: string, source: string) => `/api/runs/${id}/charts/${encodeURIComponent(source)}/tableau.twbx`,
  chartExcelUrl: (id: string, source: string) => `/api/runs/${id}/charts/${encodeURIComponent(source)}/excel.xlsx`,
  presentationUrl: '/api/presentation.pptx',
}

export function isSql(evidence: Evidence): evidence is SqlEvidence {
  return typeof (evidence as SqlEvidence).sql === 'string'
}

export function isText(evidence: Evidence): evidence is TextEvidence {
  return typeof (evidence as TextEvidence).text === 'string'
}
