/** Types aligned with docs/openapi.json schemas */

export type ContentType = string;
export type ClientType = string;
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type IncidentState = 'detected' | 'investigating' | 'assessed' | 'resolved';
export type ProposalState =
  | 'observe'
  | 'investigate'
  | 'simulate'
  | 'approval_required'
  | 'approved'
  | 'blocked';
export type AgentRunState =
  | 'gathering_evidence'
  | 'reflection_required'
  | 'waiting_for_human'
  | 'completed'
  | 'rejected'
  | 'failed';
export type AutonomyLevel = 'observe_only' | 'recommend' | 'auto_simulate' | 'auto_execute';
export type LlmProvider =
  | 'disabled'
  | 'groq'
  | 'gemini'
  | 'ollama'
  | 'openai'
  | 'anthropic';

/** OpenAPI: EventRead */
export interface EventRead {
  id: string;
  name: string;
  content_type: string;
  starts_at: string;
  ends_at?: string | null;
  metadata?: Record<string, unknown>;
}

/** OpenAPI: SessionSummary */
export interface SessionSummary {
  session_id: string;
  event_id: string;
  external_id: string;
  client_type: string;
  region?: string | null;
  started_at?: string | null;
}

/** OpenAPI: IncidentRead */
export interface IncidentRead {
  id: string;
  event_id: string;
  slice_key: string;
  state: IncidentState;
  severity: AlertSeverity;
  affected_slice: Record<string, string | null>;
  evidence_ids: string[];
  hypothesis?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/** OpenAPI: LiveIncidentSummary */
export interface LiveIncidentSummary {
  incident_id: string;
  severity: string;
  state: string;
  slice_key: string;
}

/** OpenAPI: LiveEventUpdate */
export interface LiveEventUpdate {
  event_id: string;
  active_sessions: number;
  total_sessions?: number;
  incidents?: LiveIncidentSummary[];
}

/** OpenAPI: EventSessionStats */
export interface EventSessionStats {
  total_sessions: number;
  active_sessions: number;
}

/** OpenAPI: ProposalRead */
export interface ProposalRead {
  id: string;
  incident_id: string;
  action_type: string;
  target_scope: Record<string, string | number | boolean | null>;
  rationale: string;
  expected_effect: string;
  confidence: number;
  risk_score: number;
  evidence_ids: string[];
  prediction_interval_width?: number | null;
  drift_active?: boolean;
  state: ProposalState;
  policy_reasons: string[];
  created_at: string;
}

/** OpenAPI: AlertRead */
export type AlertState = 'open' | 'acknowledged' | 'resolved';

export interface AlertRead {
  id: string;
  event_id: string;
  slice_key: string;
  rule_id: string;
  severity: AlertSeverity;
  state: AlertState;
  observed_value: number;
  threshold: number;
  description: string;
  created_at: string;
}

/** OpenAPI: ApprovalCreate */
export interface ApprovalCreate {
  approved: boolean;
  actor_id: string;
  reason: string;
}

/** OpenAPI: RejectCreate */
export interface RejectCreate {
  actor_id: string;
  reason: string;
}

/** OpenAPI: SimulationRead */
export interface SimulationRead {
  proposal_id: string;
  successful: boolean;
  projected_risk_reduction: number;
  projected_affected_sessions: number;
  explanation: string;
}

/** OpenAPI: AuditEventRead */
export interface AuditEventRead {
  audit_id: string;
  correlation_id: string;
  actor_type: string;
  artifact_type: string;
  artifact_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}

/** OpenAPI: ForecastResult */
export interface ForecastResult {
  p10: number;
  p50: number;
  p90: number;
}

/** OpenAPI: ForecastRequest */
export interface ForecastRequest {
  session_id: string;
  metric_name: string;
  horizon_seconds: number;
  model: ModelIdentity;
}

/** OpenAPI: ModelIdentity */
export interface ModelIdentity {
  name: string;
  version: string;
  feature_schema_version: string;
}

/** OpenAPI: ScoreResult */
export interface ScoreResult {
  prediction_type: string;
  value: number;
  lower_bound?: number | null;
  upper_bound?: number | null;
  confidence?: number | null;
}

/** OpenAPI: AgentRunRead */
export interface AgentRunRead {
  id: string;
  incident_id: string;
  state: AgentRunState;
  workflow_data: Record<string, unknown>;
  created_at: string;
}

/** OpenAPI: SystemSettings */
export interface SystemSettings {
  llm_provider?: LlmProvider;
  llm_model?: string;
  llm_endpoint?: string | null;
  llm_api_key?: string | null;
  llm_discovered_models?: string[];
  llm_connection_verified?: boolean;
  qoe_model_path?: string;
  forecaster_model_path?: string;
  alert_mos_threshold?: number;
  alert_buffer_ratio_threshold?: number;
  alert_stall_count_threshold?: number;
  policy_min_confidence?: number;
  policy_max_blast_radius?: number;
  policy_max_prediction_interval?: number;
  policy_high_risk_threshold?: number;
  detector_enabled?: boolean;
  diagnostician_enabled?: boolean;
  mitigator_enabled?: boolean;
  verifier_enabled?: boolean;
  autonomy_level?: AutonomyLevel;
  max_retries?: number;
  agent_step_budget?: number;
  agent_time_budget_seconds?: number;
  eval_enabled?: boolean;
  eval_llm_judge_enabled?: boolean;
  eval_trace_sample_rate?: number;
  mcp_server_enabled?: boolean;
  mcp_external_servers?: Array<Record<string, string>>;
  data_sources?: DataSourceConfig[];
}

export interface DataSourceConfig {
  type: 'simulation' | 'prometheus' | 'websocket' | 'file';
  endpoint?: string | null;
  scenario_id?: string | null;
  active?: boolean;
  label?: string;
}

export interface TraceSummary {
  trace_id: string;
  overall_score: number;
  cluster_id: string | null;
  scores: Array<{ dimension: string; score: number; explanation: string }>;
}

export interface FailureCluster {
  cluster_id: string;
  label: string;
  count: number;
  representative_trace_id: string | null;
  common_attributes: Record<string, unknown>;
}

/** OpenAPI: ProviderInfo */
export interface ProviderInfo {
  id: string;
  name: string;
  description: string;
  requires_api_key: boolean;
  requires_endpoint: boolean;
  free_tier: boolean;
  models: string[];
}

/** OpenAPI: KPISnapshot */
export interface KPISnapshot {
  label: string;
  value: number | string;
  unit?: string | null;
  delta?: number | null;
  trend: 'up' | 'down' | 'stable' | string;
  status: 'good' | 'warning' | 'critical' | string;
}

/** OpenAPI: ForecastSeriesPoint */
export interface ForecastSeriesPoint {
  timestamp: string;
  p10: number;
  p50: number;
  p90: number;
}

/** Alias for chart components */
export type ForecastPoint = ForecastSeriesPoint & { actual?: number };

/** OpenAPI: EvalAgentMetric */
export interface EvalAgentMetric {
  name: string;
  total_runs: number;
  avg_latency_ms: number;
  avg_score: number;
  failure_rate: number;
}

/** OpenAPI: EvalSummaryResponse */
export interface EvalSummaryResponse {
  agents: EvalAgentMetric[];
}

/** Display helpers for PolicyBadge — maps OpenAPI ProposalState */
export type PolicyStateDisplay =
  | 'OBSERVE'
  | 'INVESTIGATE'
  | 'RECOMMEND'
  | 'SIMULATE'
  | 'APPROVE_REQUIRED'
  | 'APPROVED'
  | 'BLOCKED';

export function toPolicyDisplay(state: ProposalState | string): PolicyStateDisplay {
  const map: Record<string, PolicyStateDisplay> = {
    observe: 'OBSERVE',
    investigate: 'INVESTIGATE',
    simulate: 'SIMULATE',
    approval_required: 'APPROVE_REQUIRED',
    approved: 'APPROVED',
    blocked: 'BLOCKED',
    // legacy uppercase from older UI
    OBSERVE: 'OBSERVE',
    INVESTIGATE: 'INVESTIGATE',
    RECOMMEND: 'RECOMMEND',
    SIMULATE: 'SIMULATE',
    APPROVE_REQUIRED: 'APPROVE_REQUIRED',
    BLOCKED: 'BLOCKED',
  };
  return map[state] ?? 'OBSERVE';
}

export function hypothesisText(hypothesis: Record<string, unknown> | null | undefined): string {
  if (!hypothesis) return 'No hypothesis yet — awaiting analyst run.';
  if (typeof hypothesis.summary === 'string') return hypothesis.summary;
  if (typeof hypothesis.text === 'string') return hypothesis.text;
  if (typeof hypothesis.hypothesis === 'string') return hypothesis.hypothesis;
  return JSON.stringify(hypothesis);
}

export function sliceLabel(slice: Record<string, string | null> | string): string {
  if (typeof slice === 'string') return slice;
  return Object.entries(slice)
    .filter(([, v]) => v != null && v !== '')
    .map(([k, v]) => `${k}=${v}`)
    .join(' · ') || '—';
}
