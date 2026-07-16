import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import * as stylex from '@stylexjs/stylex';
import { Bot } from 'lucide-react';
import { glassProps, pageLayout } from '@/lib/stylex';
import {
  useAlerts,
  useEventSessionStats,
  useForecast,
  useIncidents,
  useKPIs,
  useSessions,
} from '@/api/queries';
import { useEvalSummary } from '@/api/settings';
import { useResolvedEventId } from '@/hooks/useResolvedEventId';
import { useSpotlight } from '@/components/tour/TourProvider';
import KPICard from '@/components/ui/KPICard';
import ForecastChart from '@/components/charts/ForecastChart';
import AlertFeed from '@/components/panels/AlertFeed';
import IncidentCard from '@/components/panels/IncidentCard';
import SessionTable from '@/components/panels/SessionTable';
import SimulationControl from '@/components/panels/SimulationControl';
import { useSimulationStatus, useScenarios } from '@/api/simulation';

const styles = stylex.create({
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  liveRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 4,
  },
  liveLabel: {
    fontSize: 11,
    color: 'var(--sw-accent)',
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--sw-text)',
    letterSpacing: '-0.02em',
    margin: 0,
  },
  meta: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    marginTop: 4,
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
  },
  twoCol: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16,
  },
  col: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-text-muted)',
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
  },
  emptyBox: {
    padding: 40,
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    alignItems: 'center',
  },
  emptyBody: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    maxWidth: 420,
    lineHeight: 1.6,
  },
  agentSummaryCard: {
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  agentSummaryHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  agentLink: {
    marginLeft: 'auto',
    fontSize: 12,
    fontWeight: 500,
    color: 'var(--sw-accent)',
    textDecoration: 'none',
  },
  agentSummaryRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 16,
    fontSize: 12,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-muted)',
  },
  agentEmpty: {
    fontSize: 12,
    color: 'var(--sw-text-faint)',
  },
});

export default function LiveEventPage() {
  const eventId = useResolvedEventId();
  const { data: simStatus } = useSimulationStatus();
  const { data: scenarios } = useScenarios();
  const isSimRunning = simStatus?.status === 'running';

  const { data: kpis = [], isLoading: kpisLoading } = useKPIs(eventId);
  const { data: sessionStats } = useEventSessionStats(eventId);
  const { data: alerts = [] } = useAlerts(eventId);
  const { data: incidents = [] } = useIncidents(eventId, false);
  const activeIncidents = incidents.filter((inc) => inc.state !== 'resolved');
  const resolvedIncidents = incidents.filter((inc) => inc.state === 'resolved');
  const { data: sessions = [] } = useSessions(eventId);
  const { data: forecast = [] } = useForecast(eventId);
  const { data: evalSummary } = useEvalSummary();
  const agentMetrics = evalSummary?.agents ?? [];

  const { start } = useSpotlight();
  useEffect(() => {
    if (!localStorage.getItem('stromwart-tour-completed') && eventId) {
      const t = setTimeout(() => start(), 800);
      return () => clearTimeout(t);
    }
  }, [start, eventId]);

  const activeSessions =
    sessionStats?.active_sessions ??
    kpis.find((k) => k.label === 'Active Sessions')?.value ??
    0;
  const totalSessions =
    sessionStats?.total_sessions ??
    kpis.find((k) => k.label === 'Total Sessions')?.value ??
    activeSessions;

  if (!eventId) {
    return (
      <div {...stylex.props(pageLayout.container)}>
        <SimulationControl />
        <div {...glassProps(styles.emptyBox)}>
          <div {...stylex.props(styles.emptyBody)}>
            Select a demo scenario above and click <strong>Start Simulation</strong>.
            Try <em>CDN Regional Outage</em> for the fastest incident demo.
          </div>
        </div>
      </div>
    );
  }

  const scenario = scenarios?.find((s) => s.id === simStatus?.scenario_id);
  const eventName = scenario?.name ?? `Event ${eventId.slice(0, 8)}…`;

  return (
    <div {...stylex.props(pageLayout.container)}>
      <SimulationControl compact />

      <div {...stylex.props(styles.header)}>
        <div>
          <div {...stylex.props(styles.liveRow)}>
            <span className="glow-dot" />
            <span {...stylex.props(styles.liveLabel)}>Live Event</span>
          </div>
          <h1 {...stylex.props(styles.title)}>{eventName}</h1>
          <div {...stylex.props(styles.meta)}>
            {Number(activeSessions).toLocaleString()} active sessions ·{' '}
            {Number(totalSessions).toLocaleString()} total · {scenario?.category ?? 'live'}
            {scenario?.sessions_peak != null && (
              <> · {(scenario.sessions_peak / 1000).toFixed(0)}k peak audience</>
            )}
          </div>
        </div>
      </div>

      <div data-tour="kpi-panel" {...stylex.props(styles.kpiGrid)}>
        {kpisLoading && kpis.length === 0 ? (
          <div {...stylex.props(styles.emptyBody)}>Loading KPIs…</div>
        ) : (
          kpis.map((kpi) => <KPICard key={kpi.label} kpi={kpi} />)
        )}
      </div>

      <div data-tour="forecast-chart">
        <ForecastChart data={forecast} />
      </div>

      <div {...stylex.props(styles.twoCol)}>
        <div data-tour="incident-card" {...stylex.props(styles.col)}>
          <div {...stylex.props(styles.sectionLabel)}>
            Active Incidents ({activeIncidents.length})
            {alerts.length > 0 && (
              <> · {alerts.length} alert{alerts.length !== 1 ? 's' : ''}</>
            )}
          </div>
          {activeIncidents.length === 0 ? (
            <div {...glassProps(styles.emptyBox)}>
              <div {...stylex.props(styles.emptyBody)}>
                {isSimRunning
                  ? 'Waiting for degraded telemetry…'
                  : 'No open incidents for this event.'}
              </div>
            </div>
          ) : (
            activeIncidents.map((inc) => <IncidentCard key={inc.id} incident={inc} />)
          )}
          {resolvedIncidents.length > 0 && (
            <>
              <div {...stylex.props(styles.sectionLabel)}>
                Resolved ({resolvedIncidents.length})
              </div>
              {resolvedIncidents.map((inc) => (
                <IncidentCard key={inc.id} incident={inc} />
              ))}
            </>
          )}
        </div>
        <div data-tour="alert-feed" {...stylex.props(styles.col)}>
          <div {...stylex.props(styles.sectionLabel)}>
            Alert Feed ({alerts.length})
            {alerts.filter((a) => a.state === 'open').length > 0 && (
              <>
                {' '}
                · {alerts.filter((a) => a.state === 'open').length} open
              </>
            )}
          </div>
          <AlertFeed alerts={alerts} eventId={eventId} showHeader={false} />
        </div>
      </div>

      <SessionTable
        sessions={sessions}
        totalActive={
          typeof totalSessions === 'number' ? totalSessions : undefined
        }
      />

      <div {...glassProps(styles.agentSummaryCard)}>
        <div {...stylex.props(styles.agentSummaryHeader)}>
          <Bot size={16} />
          <span>Agent System</span>
          <NavLink to="/agents" {...stylex.props(styles.agentLink)}>
            Agents →
          </NavLink>
        </div>
        {agentMetrics.length > 0 ? (
          <div {...stylex.props(styles.agentSummaryRow)}>
            {agentMetrics.slice(0, 4).map((a) => (
              <span key={a.name}>
                {a.name}: {((1 - a.failure_rate) * 100).toFixed(0)}%
              </span>
            ))}
          </div>
        ) : (
          <span {...stylex.props(styles.agentEmpty)}>No agent activity yet</span>
        )}
      </div>
    </div>
  );
}
