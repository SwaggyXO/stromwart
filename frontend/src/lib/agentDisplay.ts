/** Format agent step duration for display (avoid misleading 0ms). */
export function formatAgentDurationMs(durationMs: unknown): string {
  if (typeof durationMs !== 'number' || Number.isNaN(durationMs)) return '—';
  if (durationMs > 0 && durationMs < 1) return '<1ms';
  return `${Math.round(durationMs)}ms`;
}

export function hypothesisSourceLabel(
  hypothesis: Record<string, unknown> | null | undefined,
): string {
  const source = hypothesis?.source;
  if (source === 'llm_analyst') return 'LLM Analyst';
  if (source === 'diagnostician') return 'Diagnostician';
  return 'Root cause analysis';
}

export type AgentStackKind = 'llm' | 'ml' | 'deterministic';

export interface AgentStackEntry {
  id: string;
  name: string;
  kind: AgentStackKind;
  detail: string;
}

export const AGENT_STACK: AgentStackEntry[] = [
  {
    id: 'detector',
    name: 'Detector',
    kind: 'ml',
    detail: 'QoE GBM predictions + threshold rules',
  },
  {
    id: 'diagnostician',
    name: 'Diagnostician',
    kind: 'deterministic',
    detail: 'Feature/topology rules; optional LLM enrichment when configured',
  },
  {
    id: 'mitigator',
    name: 'Mitigator',
    kind: 'deterministic',
    detail: 'Playbook mapping from diagnosis to actions',
  },
  {
    id: 'verifier',
    name: 'Verifier',
    kind: 'deterministic',
    detail: 'Before/after KPI comparison',
  },
  {
    id: 'llm_analyst',
    name: 'LLM Analyst',
    kind: 'llm',
    detail: 'Full evidence workflow when LLM is enabled',
  },
];

export function agentStackKindLabel(kind: AgentStackKind): string {
  if (kind === 'llm') return 'LLM';
  if (kind === 'ml') return 'ML model';
  return 'Deterministic';
}
