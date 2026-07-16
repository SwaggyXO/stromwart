import { Link } from 'react-router-dom';
import * as stylex from '@stylexjs/stylex';
import { glassProps, pageLayout } from '@/lib/stylex';
import {
  useEvalSummary,
  useEvalTraces,
  useFailureClusters,
  useSettings,
  useUpdateSettings,
} from '@/api/settings';
import {
  useAgentRuns,
  useIncidentAuditTimeline,
  useIncidentProposals,
  useIncidents,
} from '@/api/queries';
import { useResolvedEventId } from '@/hooks/useResolvedEventId';
import { useSimulationStatus } from '@/api/simulation';
import { formatAgentDurationMs, AGENT_STACK, agentStackKindLabel } from '@/lib/agentDisplay';
import SeverityBadge from '@/components/ui/SeverityBadge';
import PolicyBadge from '@/components/ui/PolicyBadge';
import EvalTraceTable from '@/components/evals/EvalTraceTable';
import type { IncidentRead, SystemSettings } from '@/types';
import {
  Activity,
  CheckCircle,
  Clock,
  Search,
  Wrench,
  Zap,
  ExternalLink,
} from 'lucide-react';

const AGENT_DEFINITIONS = [
  {
    id: 'detector',
    name: 'Detector',
    icon: Search,
    blurb: 'Flags QoE anomalies on the live event',
    settingKey: 'detector_enabled' as const,
    color: 'var(--sw-blue)',
  },
  {
    id: 'diagnostician',
    name: 'Diagnostician',
    icon: Activity,
    blurb: 'Explains root cause with evidence',
    settingKey: 'diagnostician_enabled' as const,
    color: 'var(--sw-accent)',
  },
  {
    id: 'mitigator',
    name: 'Mitigator',
    icon: Wrench,
    blurb: 'Proposes remediation actions',
    settingKey: 'mitigator_enabled' as const,
    color: 'var(--sw-yellow)',
  },
  {
    id: 'verifier',
    name: 'Verifier',
    icon: CheckCircle,
    blurb: 'Confirms KPIs recovered after action',
    settingKey: 'verifier_enabled' as const,
    color: 'var(--sw-green)',
  },
] as const;

const PIPELINE_CAP = 8;

const styles = stylex.create({
  header: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--sw-text)',
    margin: 0,
  },
  subtitle: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    margin: '4px 0 0',
  },
  demoChip: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-accent)',
    backgroundColor: 'var(--sw-accent-dim)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(249,115,22,0.25)',
    borderRadius: 'var(--sw-radius-md)',
    paddingTop: 6,
    paddingBottom: 6,
    paddingLeft: 12,
    paddingRight: 12,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    whiteSpace: 'nowrap',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--sw-text)',
    margin: 0,
    letterSpacing: '0.02em',
  },
  sectionDesc: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    marginTop: 4,
    marginBottom: 0,
  },
  stackGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: 10,
    marginTop: 12,
  },
  stackCard: {
    padding: 12,
    borderRadius: 'var(--sw-radius-md)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    backgroundColor: 'var(--sw-surface-2)',
  },
  stackName: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
    marginBottom: 4,
  },
  stackKind: {
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
    color: 'var(--sw-accent)',
    marginBottom: 6,
  },
  stackDetail: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.45,
    margin: 0,
  },
  agentGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: 16,
  },
  agentCard: {
    padding: 18,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  agentHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 10,
  },
  agentTitleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  agentName: {
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--sw-text)',
  },
  agentBlurb: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.5,
    marginTop: 2,
  },
  toggleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },
  toggleLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-text-faint)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
  metrics: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 14,
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-muted)',
    borderTopWidth: 1,
    borderTopStyle: 'solid',
    borderTopColor: 'rgba(255,255,255,0.06)',
    paddingTop: 10,
  },
  metricValue: {
    fontWeight: 700,
    color: 'var(--sw-text)',
  },
  noRuns: {
    fontSize: 12,
    color: 'var(--sw-text-faint)',
    fontStyle: 'italic',
    paddingTop: 16,
    paddingBottom: 16,
    paddingLeft: 18,
    paddingRight: 18,
  },
  metricStrip: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: 10,
    marginBottom: 12,
  },
  metricCard: {
    padding: 12,
  },
  metricName: {
    fontSize: 11,
    fontWeight: 700,
    color: 'var(--sw-accent)',
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  metricBody: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  traceTable: {
    overflowX: 'auto',
    fontSize: 12,
  },
  traceTableInner: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  traceTh: {
    textAlign: 'left',
    padding: '8px 10px',
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--sw-text-faint)',
    letterSpacing: '0.07em',
    textTransform: 'uppercase',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  traceTd: {
    padding: '8px 10px',
    color: 'var(--sw-text-muted)',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'rgba(255,255,255,0.04)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
  },
  pipelineTable: {
    overflowX: 'auto',
  },
  pipelineInner: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 12,
  },
  pipelineTd: {
    padding: '10px 12px',
    color: 'var(--sw-text-muted)',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'rgba(255,255,255,0.04)',
    verticalAlign: 'middle',
  },
  incidentLink: {
    color: 'var(--sw-text)',
    textDecoration: 'none',
    fontWeight: 600,
    fontSize: 12,
  },
  incidentMeta: {
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-faint)',
    marginTop: 2,
  },
  proposalCell: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  actionLink: {
    fontSize: 12,
    fontWeight: 500,
    color: 'var(--sw-accent)',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
  },
  emptyState: {
    fontSize: 13,
    color: 'var(--sw-text-faint)',
    padding: 20,
    textAlign: 'center',
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
});

function getAgentMetric(name: string, agents: { name: string; failure_rate: number; avg_latency_ms: number; total_runs: number }[]) {
  return agents.find((a) => a.name.toLowerCase() === name.toLowerCase());
}

function OodaTimeline({ incidentId }: { incidentId: string }) {
  const { data: audit = [] } = useIncidentAuditTimeline(incidentId);
  const steps = audit
    .filter(
      (e) =>
        e.artifact_type === 'supervisor_step' ||
        (e.artifact_type === 'agent_run' && e.actor_type === 'agent'),
    )
    .slice(-12)
    .reverse();

  if (steps.length === 0) {
    return (
      <div {...stylex.props(styles.noRuns)}>No OODA steps recorded yet for this incident.</div>
    );
  }

  return (
    <div {...stylex.props(styles.traceTable)}>
      <table {...stylex.props(styles.traceTableInner)}>
        <thead>
          <tr>
            {['Agent', 'Action', 'Duration', 'Reflection', 'Status'].map((h) => (
              <th key={h} {...stylex.props(styles.traceTh)}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {steps.map((entry) => {
            const payload = entry.payload;
            const agent = String(payload.agent ?? '—');
            const action = String(payload.action ?? '—');
            const durationMs = payload.duration_ms;
            const stopReason = payload.stop_reason;
            const success = payload.success !== false;
            const reflection = payload.step_reflection as
              | { passed?: boolean }
              | undefined;
            const reflectionOk = reflection?.passed !== false;
            return (
              <tr key={entry.audit_id}>
                <td {...stylex.props(styles.traceTd)} style={{ textTransform: 'capitalize' }}>
                  {agent}
                </td>
                <td {...stylex.props(styles.traceTd)}>{action.replace(/_/g, ' ')}</td>
                <td {...stylex.props(styles.traceTd)}>
                  {formatAgentDurationMs(durationMs)}
                  {stopReason ? ` · ${String(stopReason)}` : ''}
                </td>
                <td {...stylex.props(styles.traceTd)}>
                  <span className={reflectionOk ? 'badge-pass' : 'badge-fail'}>
                    {reflection ? (reflectionOk ? 'PASS' : 'FAIL') : '—'}
                  </span>
                </td>
                <td {...stylex.props(styles.traceTd)}>
                  <span className={success ? 'badge-pass' : 'badge-fail'}>
                    {success ? 'OK' : 'FAIL'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function IncidentPipelineRow({ incident }: { incident: IncidentRead }) {
  const { data: proposals = [] } = useIncidentProposals(incident.id);
  const { data: agentRuns = [] } = useAgentRuns(incident.id);

  const latestRun = [...agentRuns].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];
  const latestProposal = [...proposals].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )[0];

  const agentTouch = latestRun
    ? latestRun.state.replace(/_/g, ' ')
    : '—';

  return (
    <tr>
      <td {...stylex.props(styles.pipelineTd)}>
        <Link to={`/incidents/${incident.id}`} {...stylex.props(styles.incidentLink)}>
          <SeverityBadge severity={incident.severity} />
        </Link>
        <div {...stylex.props(styles.incidentMeta)}>{incident.slice_key}</div>
      </td>
      <td {...stylex.props(styles.pipelineTd)}>{incident.state}</td>
      <td {...stylex.props(styles.pipelineTd)} style={{ textTransform: 'capitalize' }}>
        {agentTouch}
      </td>
      <td {...stylex.props(styles.pipelineTd)}>
        {latestProposal ? (
          <div {...stylex.props(styles.proposalCell)}>
            <span>{latestProposal.action_type}</span>
            <PolicyBadge state={latestProposal.state} />
          </div>
        ) : (
          'None yet'
        )}
      </td>
      <td {...stylex.props(styles.pipelineTd)}>
        <Link to={`/incidents/${incident.id}`} {...stylex.props(styles.actionLink)}>
          Open <ExternalLink size={12} />
        </Link>
      </td>
    </tr>
  );
}

export default function AgentsPage() {
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();
  const { data: evalSummary } = useEvalSummary();
  const { data: traces } = useEvalTraces(20);
  const { data: clustersData } = useFailureClusters();
  const { data: simStatus } = useSimulationStatus(true);

  const eventId = useResolvedEventId();
  const { data: incidents = [] } = useIncidents(eventId, true);

  const agentMetrics = evalSummary?.agents ?? [];
  const traceList = traces?.traces ?? [];
  const clusters = clustersData?.clusters ?? [];
  const isRunning = simStatus?.status === 'running';
  const openIncidents = incidents.slice(0, PIPELINE_CAP);

  const toggleAgent = (key: keyof SystemSettings, enabled: boolean) => {
    updateSettings.mutate({ [key]: enabled });
  };

  return (
    <div {...stylex.props(pageLayout.container)}>
      <div {...stylex.props(styles.header)}>
        <div>
          <h1 {...stylex.props(styles.title)}>Agents</h1>
          <p {...stylex.props(styles.subtitle)}>
            Live agent health, activity, and work on open incidents
          </p>
        </div>
        {isRunning && (
          <div {...stylex.props(styles.demoChip)}>
            <Zap size={12} />
            Demo running: {simStatus?.current_phase}
            {simStatus?.execution_mode && (
              <span style={{ opacity: 0.85 }}> · {simStatus.execution_mode}</span>
            )}
          </div>
        )}
      </div>

      <div {...stylex.props(styles.section)}>
        <div>
          <h2 {...stylex.props(styles.sectionTitle)}>Agent stack</h2>
          <p {...stylex.props(styles.sectionDesc)}>
            Which specialists use trained ML models, deterministic rules, or an LLM when
            configured in Settings.
          </p>
        </div>
        <div {...stylex.props(styles.stackGrid)}>
          {AGENT_STACK.map((entry) => (
            <div key={entry.id} {...stylex.props(styles.stackCard)}>
              <div {...stylex.props(styles.stackName)}>{entry.name}</div>
              <div {...stylex.props(styles.stackKind)}>{agentStackKindLabel(entry.kind)}</div>
              <p {...stylex.props(styles.stackDetail)}>{entry.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div {...stylex.props(styles.section)}>
        <div>
          <h2 {...stylex.props(styles.sectionTitle)}>Agent health</h2>
          <p {...stylex.props(styles.sectionDesc)}>
            Enable specialists and monitor success rate, latency, and run volume.
          </p>
        </div>
        <div {...stylex.props(styles.agentGrid)}>
          {AGENT_DEFINITIONS.map((agent) => {
            const Icon = agent.icon;
            const metrics = getAgentMetric(agent.id, agentMetrics);
            const enabled = Boolean(settings?.[agent.settingKey]);

            return (
              <div key={agent.id} {...glassProps(styles.agentCard)}>
                <div {...stylex.props(styles.agentHeader)}>
                  <div>
                    <div {...stylex.props(styles.agentTitleRow)}>
                      <Icon size={18} color={agent.color} />
                      <span {...stylex.props(styles.agentName)}>{agent.name}</span>
                    </div>
                    <div {...stylex.props(styles.agentBlurb)}>{agent.blurb}</div>
                  </div>
                  <div {...stylex.props(styles.toggleRow)}>
                    <span {...stylex.props(styles.toggleLabel)}>Enabled</span>
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={(e) => toggleAgent(agent.settingKey, e.target.checked)}
                    />
                  </div>
                </div>
                {metrics && metrics.total_runs > 0 ? (
                  <div {...stylex.props(styles.metrics)}>
                    <span>
                      Success rate:{' '}
                      <span {...stylex.props(styles.metricValue)}>
                        {((1 - metrics.failure_rate) * 100).toFixed(0)}%
                      </span>
                    </span>
                    <span>
                      Avg latency:{' '}
                      <span {...stylex.props(styles.metricValue)}>
                        {formatAgentDurationMs(metrics.avg_latency_ms)}
                      </span>
                    </span>
                    <span>
                      Total runs:{' '}
                      <span {...stylex.props(styles.metricValue)}>{metrics.total_runs}</span>
                    </span>
                  </div>
                ) : (
                  <div {...stylex.props(styles.noRuns)}>No runs yet</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div {...stylex.props(styles.section)}>
        <div>
          <h2 {...stylex.props(styles.sectionTitle)}>Recent agent activity</h2>
        </div>
        {agentMetrics.length > 0 && (
          <div {...stylex.props(styles.metricStrip)}>
            {agentMetrics.slice(0, 4).map((agent) => (
              <div key={agent.name} {...glassProps(styles.metricCard)}>
                <div {...stylex.props(styles.metricName)}>{agent.name}</div>
                <div {...stylex.props(styles.metricBody)}>
                  <CheckCircle size={11} />
                  {((1 - agent.failure_rate) * 100).toFixed(0)}% ·{' '}
                  <Clock size={11} />
                  {formatAgentDurationMs(agent.avg_latency_ms)}
                </div>
              </div>
            ))}
          </div>
        )}
        {traceList.length > 0 ? (
          <div {...glassProps()}>
            <EvalTraceTable traces={traceList} clusters={clusters} />
          </div>
        ) : (
          <div {...glassProps(styles.emptyState)}>
            No agent activity yet. Open incidents or run a demo scenario.
          </div>
        )}
      </div>

      <div {...stylex.props(styles.section)}>
        <div>
          <h2 {...stylex.props(styles.sectionTitle)}>Work on open incidents</h2>
        </div>
        {openIncidents.length > 0 ? (
          <>
            <div {...glassProps()}>
              <div {...stylex.props(styles.pipelineTable)}>
                <table {...stylex.props(styles.pipelineInner)}>
                  <thead>
                    <tr>
                      {['Incident', 'State', 'Latest agent touch', 'Proposal', 'Action'].map(
                        (h) => (
                          <th key={h} {...stylex.props(styles.traceTh)}>
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {openIncidents.map((inc) => (
                      <IncidentPipelineRow key={inc.id} incident={inc} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            {openIncidents[0] && (
              <div {...stylex.props(styles.section)}>
                <div>
                  <h3 {...stylex.props(styles.sectionTitle)}>OODA timeline</h3>
                  <p {...stylex.props(styles.sectionDesc)}>
                    Supervisor steps for the most recent open incident (matches audit trail).
                  </p>
                </div>
                <div {...glassProps()}>
                  <OodaTimeline incidentId={openIncidents[0].id} />
                </div>
              </div>
            )}
          </>
        ) : (
          <div {...glassProps(styles.emptyState)}>
            No open incidents. Agents appear here when the live event degrades.
          </div>
        )}
      </div>
    </div>
  );
}
