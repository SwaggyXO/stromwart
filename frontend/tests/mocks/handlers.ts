import { http, HttpResponse } from 'msw';

const BASE = '/api/v1';

/** Shapes aligned with frontend/src/types/index.ts (OpenAPI) */
const mockEvent = {
  id: 'evt_test_001',
  name: 'FIFA WC 2026 — Germany vs Japan',
  content_type: 'sports',
  starts_at: '2026-07-15T20:00:00Z',
  ends_at: null,
  metadata: {},
};

const mockKPIs = [
  { label: 'MOS Score', value: 4.21, unit: '', delta: 0.05, trend: 'up', status: 'good' },
  { label: 'Buffer Ratio', value: '1.2%', delta: -0.3, trend: 'down', status: 'good' },
  { label: 'Active Sessions', value: '142.5K', delta: 2100, trend: 'up', status: 'good' },
  { label: 'Risk Score', value: 0.42, delta: 0.08, trend: 'up', status: 'warning' },
];

const mockAlerts = [
  {
    id: 'alrt_001',
    event_id: 'evt_test_001',
    slice_key: 'region:eu-west/client:android',
    severity: 'high',
    state: 'open',
    observed_value: 2.8,
    threshold: 3.5,
    rule_id: 'mos_below_threshold',
    created_at: '2026-07-15T20:15:00Z',
    description: 'MOS dropped below 3.5 for Android users in EU-West',
  },
  {
    id: 'alrt_002',
    event_id: 'evt_test_001',
    slice_key: 'region:apac/client:web',
    severity: 'medium',
    state: 'open',
    observed_value: 5.2,
    threshold: 3.0,
    rule_id: 'stall_ratio_high',
    created_at: '2026-07-15T20:18:00Z',
    description: 'Stall ratio exceeded 3% for web users in APAC',
  },
];

const mockIncidents = [
  {
    id: 'inc_001',
    event_id: 'evt_test_001',
    slice_key: 'region:eu-west/client:android',
    state: 'investigating',
    severity: 'high',
    affected_slice: { region: 'eu-west', client: 'android' },
    evidence_ids: ['alrt_001'],
    hypothesis: {
      summary: 'CDN edge node saturation causing bitrate drops for Android clients in EU-West region.',
    },
    created_at: '2026-07-15T20:16:00Z',
    updated_at: '2026-07-15T20:16:00Z',
  },
];

const mockProposals = [
  {
    id: 'prop_001',
    incident_id: 'inc_001',
    action_type: 'scale_cdn_edge',
    target_scope: { cluster: 'eu-west-cdn-cluster-3' },
    rationale: 'Edge node CPU at 92%. Adding 2 nodes would distribute load.',
    expected_effect: 'Reduce p95 latency by ~40%, restore MOS above 3.8',
    confidence: 0.82,
    risk_score: 0.15,
    evidence_ids: ['alrt_001'],
    state: 'approval_required',
    policy_reasons: [],
    created_at: '2026-07-15T20:16:30Z',
  },
];

const mockForecast = Array.from({ length: 12 }, (_, i) => ({
  timestamp: new Date(Date.UTC(2026, 6, 15, 20, i * 5)).toISOString(),
  p10: 3.5 + (i % 3) * 0.1,
  p50: 4.0 + (i % 3) * 0.1,
  p90: 4.5 + (i % 2) * 0.1,
  actual: i < 6 ? 4.1 + (i % 2) * 0.1 : undefined,
}));

const mockSessions = Array.from({ length: 20 }, (_, i) => ({
  session_id: `sess_${String(i).padStart(3, '0')}`,
  event_id: 'evt_test_001',
  external_id: `usr_${i}`,
  client_type: ['web', 'ios', 'android', 'tv'][i % 4],
  region: ['eu-west', 'us-east', 'apac', 'eu-central'][i % 4],
  started_at: '2026-07-15T20:00:00Z',
}));

const mockAudit = [
  {
    audit_id: 'aud_001',
    correlation_id: 'corr_abc123',
    actor_type: 'llm_analyst',
    artifact_type: 'incident',
    artifact_id: 'inc_001',
    payload: { description: 'LLM Analyst created incident inc_001 from alert correlation.' },
    created_at: '2026-07-15T20:16:05Z',
  },
  {
    audit_id: 'aud_002',
    correlation_id: 'corr_abc123',
    actor_type: 'policy_verifier',
    artifact_type: 'proposal',
    artifact_id: 'prop_001',
    payload: { description: 'Policy verifier advanced proposal prop_001 to RECOMMEND state.' },
    created_at: '2026-07-15T20:16:10Z',
  },
];

const mockSettings = {
  llm_provider: 'disabled',
  llm_model: '',
  llm_endpoint: null,
  llm_api_key: null,
  llm_discovered_models: [],
  llm_connection_verified: false,
  alert_mos_threshold: 3.5,
  alert_buffer_ratio_threshold: 3.0,
  policy_min_confidence: 0.6,
  policy_max_blast_radius: 50000,
  detector_enabled: true,
  diagnostician_enabled: true,
  mitigator_enabled: true,
  verifier_enabled: true,
  autonomy_level: 'recommend',
  eval_enabled: true,
  eval_llm_judge_enabled: false,
  eval_trace_sample_rate: 1.0,
  data_sources: [
    { type: 'simulation', label: 'Demo Scenario', active: true },
    { type: 'prometheus', label: 'Prometheus', active: false },
    { type: 'websocket', label: 'Custom WebSocket', active: false },
  ],
};

const mockProviders = [
  {
    id: 'disabled',
    name: 'Disabled',
    description: 'No LLM',
    requires_api_key: false,
    requires_endpoint: false,
    free_tier: true,
    models: [],
  },
  {
    id: 'groq',
    name: 'Groq',
    description: 'Fast inference',
    requires_api_key: true,
    requires_endpoint: false,
    free_tier: true,
    models: ['llama-3.3-70b-versatile'],
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local models',
    requires_api_key: false,
    requires_endpoint: true,
    free_tier: true,
    models: ['llama3.3'],
  },
];

export const mockPayloads = {
  event: mockEvent,
  kpis: mockKPIs,
  alerts: mockAlerts,
  incidents: mockIncidents,
  proposals: mockProposals,
  forecast: mockForecast,
  sessions: mockSessions,
  audit: mockAudit,
  settings: mockSettings,
  providers: mockProviders,
};

export const handlers = [
  http.get(`${BASE}/events/active`, () => HttpResponse.json(mockEvent)),
  http.get(`${BASE}/events/:id/sessions`, () => HttpResponse.json(mockSessions)),
  http.get(`${BASE}/events/:id/alerts`, () => HttpResponse.json(mockAlerts)),
  http.get(`${BASE}/events/:id/incidents`, () => HttpResponse.json(mockIncidents)),
  http.get(`${BASE}/events/:id/kpis`, () => HttpResponse.json(mockKPIs)),
  http.get(`${BASE}/modeling/forecast`, () => HttpResponse.json(mockForecast)),
  http.get(`${BASE}/incidents/:id`, () => HttpResponse.json(mockIncidents[0])),
  http.get(`${BASE}/incidents/:id/proposals`, () => HttpResponse.json(mockProposals)),
  http.get(`${BASE}/audit`, () => HttpResponse.json(mockAudit)),
  http.get(`${BASE}/settings`, () => HttpResponse.json(mockSettings)),
  http.put(`${BASE}/settings`, () => HttpResponse.json(mockSettings)),
  http.get(`${BASE}/settings/providers`, () => HttpResponse.json(mockProviders)),
  http.get(`${BASE}/settings/providers/:id/guide`, ({ params }) =>
    HttpResponse.json({
      title: `Guide for ${params.id}`,
      description: 'Setup instructions',
      setup_steps: '1. Configure provider\n2. Test connection',
      docs_url: 'https://example.com',
      free: 'true',
      requires_api_key: 'true',
      requires_endpoint: 'false',
    }),
  ),
  http.post(`${BASE}/settings/providers/:id/discover-models`, () =>
    HttpResponse.json({
      models: ['gpt-4o', 'gpt-4o-mini'],
      status: 'connected',
      message: null,
    }),
  ),
  http.post(`${BASE}/settings/providers/test`, () =>
    HttpResponse.json({
      success: true,
      message: 'Connected to Groq — model is available',
      latency_ms: 120,
    }),
  ),
  http.get(`${BASE}/simulation/status`, () =>
    HttpResponse.json({
      status: 'running',
      scenario_id: 'fifa_wc_ger_jpn',
      progress: 0.4,
      current_phase: 'Degradation',
      event_id: mockEvent.id,
    }),
  ),
  http.get(`${BASE}/evals/summary`, () => HttpResponse.json({ agents: [] })),
  http.post(`${BASE}/alerts/:id/acknowledge`, () => HttpResponse.json({ ok: true })),
  http.post(`${BASE}/proposals/:id/approve`, () =>
    HttpResponse.json({ ...mockProposals[0], state: 'approval_required' }),
  ),
  http.post(`${BASE}/proposals/:id/reject`, () => HttpResponse.json(mockProposals[0])),
  http.post(`${BASE}/proposals/:id/simulate`, () =>
    HttpResponse.json({
      proposal_id: 'prop_001',
      successful: true,
      projected_risk_reduction: 0.4,
      projected_affected_sessions: 1000,
      explanation: 'MOS expected to improve from 2.8 to 4.1',
    }),
  ),
];
