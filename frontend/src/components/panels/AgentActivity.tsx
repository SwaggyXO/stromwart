import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import { useEvalSummary } from '@/api/settings';
import { formatAgentDurationMs } from '@/lib/agentDisplay';
import { Activity, CheckCircle, Clock } from 'lucide-react';

const styles = stylex.create({
  container: {
    marginTop: 16,
  },
  title: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--sw-text)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 12,
  },
  agentCard: {
    paddingTop: 14,
    paddingBottom: 14,
    paddingLeft: 16,
    paddingRight: 16,
  },
  agentName: {
    fontSize: 13,
    fontWeight: 700,
    color: 'var(--sw-accent)',
    textTransform: 'capitalize',
    marginBottom: 8,
  },
  metrics: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  metric: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  runs: {
    fontSize: 11,
    color: 'var(--sw-text-faint)',
    marginTop: 8,
    fontFamily: 'var(--font-mono)',
  },
  empty: {
    fontSize: 13,
    color: 'var(--sw-text-faint)',
    textAlign: 'center',
    padding: 24,
  },
});

export default function AgentActivity() {
  const { data } = useEvalSummary();
  const agents = data?.agents ?? [];

  return (
    <div {...stylex.props(styles.container)}>
      <h3 {...stylex.props(styles.title)}>
        <Activity size={16} /> Agent Orchestration
      </h3>
      <div {...stylex.props(styles.grid)}>
        {agents.map((agent) => (
          <div key={agent.name} {...glassProps(styles.agentCard)}>
            <div {...stylex.props(styles.agentName)}>{agent.name}</div>
            <div {...stylex.props(styles.metrics)}>
              <span {...stylex.props(styles.metric)}>
                <CheckCircle size={12} /> {((1 - agent.failure_rate) * 100).toFixed(0)}%
              </span>
              <span {...stylex.props(styles.metric)}>
                <Clock size={12} /> {formatAgentDurationMs(agent.avg_latency_ms)}
              </span>
              <span {...stylex.props(styles.metric)}>Score: {agent.avg_score.toFixed(2)}</span>
            </div>
            <div {...stylex.props(styles.runs)}>{agent.total_runs} runs</div>
          </div>
        ))}
      </div>
      {agents.length === 0 && (
        <div {...stylex.props(styles.empty)}>No agent activity yet</div>
      )}
    </div>
  );
}
