import { Fragment, useState } from 'react';
import * as stylex from '@stylexjs/stylex';
import { glassProps, pageLayout } from '@/lib/stylex';
import { format } from 'date-fns';
import { ClipboardList } from 'lucide-react';
import { useAuditLog } from '@/api/queries';
import { useResolvedEventId } from '@/hooks/useResolvedEventId';
import { useAppStore } from '@/store/useAppStore';
import LoadingScreen from '@/components/ui/LoadingScreen';

const ACTOR_STYLES: Record<string, { color: string; bg: string }> = {
  system: { color: 'var(--sw-text-faint)', bg: 'rgba(68,68,102,0.18)' },
  agent: { color: 'var(--sw-blue)', bg: 'rgba(59,130,246,0.12)' },
  llm_analyst: { color: 'var(--sw-blue)', bg: 'rgba(59,130,246,0.12)' },
  policy_verifier: { color: 'var(--sw-accent)', bg: 'rgba(249,115,22,0.12)' },
  human: { color: 'var(--sw-green)', bg: 'rgba(34,197,94,0.12)' },
  simulation: { color: 'var(--sw-yellow)', bg: 'rgba(234,179,8,0.12)' },
};

const COL_WIDTHS = {
  time: 120,
  actor: 100,
  artifact: 90,
  id: 240,
};

const styles = stylex.create({
  headerRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: 'var(--sw-text)',
    letterSpacing: '-0.02em',
    margin: 0,
  },
  subtitle: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    margin: 0,
  },
  card: {
    overflow: 'hidden',
    padding: 0,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    tableLayout: 'fixed',
  },
  th: {
    paddingTop: 11,
    paddingBottom: 11,
    paddingLeft: 16,
    paddingRight: 16,
    textAlign: 'left',
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--sw-text-faint)',
    letterSpacing: '0.09em',
    textTransform: 'uppercase',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  td: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 16,
    paddingRight: 16,
  },
  mono: {
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-muted)',
    whiteSpace: 'nowrap',
  },
  faint: {
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-faint)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  payload: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  actor: {
    paddingTop: 2,
    paddingBottom: 2,
    paddingLeft: 8,
    paddingRight: 8,
    borderRadius: 99,
    fontSize: 10,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    whiteSpace: 'nowrap',
  },
  rowAlt: {
    backgroundColor: 'rgba(255,255,255,0.012)',
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  rowClickable: {
    cursor: 'pointer',
  },
  rowExpanded: {
    backgroundColor: 'rgba(249,115,22,0.04)',
  },
  expandRow: {
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  expandCell: {
    paddingTop: 12,
    paddingBottom: 14,
    paddingLeft: 16,
    paddingRight: 16,
  },
  kvGrid: {
    display: 'grid',
    gridTemplateColumns: 'minmax(120px, auto) 1fr',
    gap: '6px 16px',
    fontSize: 12,
  },
  kvKey: {
    color: 'var(--sw-text-faint)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
  },
  kvValue: {
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    wordBreak: 'break-word',
  },
  empty: {
    padding: 32,
    textAlign: 'center',
    fontSize: 13,
    color: 'var(--sw-text-faint)',
  },
});

function payloadPreview(payload: Record<string, unknown>): string {
  if (payload.transition === 'acknowledged') return 'Operator acknowledged alert';
  if (typeof payload.description === 'string') return payload.description;
  const entries = Object.entries(payload);
  if (entries.length === 0) return '—';
  return entries.map(([k, v]) => `${k}: ${String(v)}`).join(' · ');
}

function formatPayloadEntries(payload: Record<string, unknown>) {
  return Object.entries(payload).map(([key, value]) => ({
    key,
    value:
      typeof value === 'object' && value !== null
        ? JSON.stringify(value)
        : String(value ?? '—'),
  }));
}

export default function AuditLogPage() {
  const eventId = useResolvedEventId();
  const { data: remote = [], isLoading } = useAuditLog(100, eventId);
  const optimistic = useAppStore((s) => s._optimisticAuditEvents);
  const events = eventId ? [...optimistic, ...remote] : [];
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (eventId && isLoading && events.length === 0) {
    return <LoadingScreen message="Loading audit log…" />;
  }

  return (
    <div {...stylex.props(pageLayout.container)}>
      <div>
        <div {...stylex.props(styles.headerRow)}>
          <ClipboardList size={18} color="var(--sw-accent)" />
          <h1 {...stylex.props(styles.title)}>Audit Log</h1>
        </div>
        <p {...stylex.props(styles.subtitle)}>
          Append-only record of system, agent, and operator actions for this event.
        </p>
      </div>

      <div {...glassProps(styles.card)}>
        {!eventId ? (
          <div {...stylex.props(styles.empty)}>
            Start a demo to see audit events for the live event.
          </div>
        ) : events.length === 0 ? (
          <div {...stylex.props(styles.empty)}>No audit events yet</div>
        ) : (
          <table {...stylex.props(styles.table)}>
            <colgroup>
              <col style={{ width: COL_WIDTHS.time }} />
              <col style={{ width: COL_WIDTHS.actor }} />
              <col style={{ width: COL_WIDTHS.artifact }} />
              <col style={{ width: COL_WIDTHS.id }} />
              <col />
            </colgroup>
            <thead>
              <tr>
                {['Time', 'Actor', 'Artifact', 'ID', 'Payload'].map((h) => (
                  <th key={h} {...stylex.props(styles.th)}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {events.map((ev, i) => {
                const actor = ACTOR_STYLES[ev.actor_type] ?? ACTOR_STYLES.system;
                const isExpanded = expandedId === ev.audit_id;
                const preview = payloadPreview(ev.payload);

                return (
                  <Fragment key={ev.audit_id}>
                    <tr
                      onClick={() =>
                        setExpandedId(isExpanded ? null : ev.audit_id)
                      }
                      title={preview}
                      {...stylex.props(
                        styles.rowBorder,
                        styles.rowClickable,
                        i % 2 === 1 && styles.rowAlt,
                        isExpanded && styles.rowExpanded,
                      )}
                    >
                      <td {...stylex.props(styles.td, styles.mono)}>
                        {format(new Date(ev.created_at), 'HH:mm:ss')}
                      </td>
                      <td {...stylex.props(styles.td)}>
                        <span
                          {...stylex.props(styles.actor)}
                          style={{ color: actor.color, background: actor.bg }}
                        >
                          {ev.actor_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td {...stylex.props(styles.td, styles.faint)}>{ev.artifact_type}</td>
                      <td {...stylex.props(styles.td, styles.faint)} title={ev.artifact_id}>
                        {ev.artifact_id}
                      </td>
                      <td {...stylex.props(styles.td, styles.payload)}>{preview}</td>
                    </tr>
                    {isExpanded && (
                      <tr {...stylex.props(styles.expandRow)}>
                        <td colSpan={5} {...stylex.props(styles.expandCell)}>
                          <div {...stylex.props(styles.kvGrid)}>
                            {formatPayloadEntries(ev.payload).map(({ key, value }) => (
                              <Fragment key={`${ev.audit_id}-${key}`}>
                                <span {...stylex.props(styles.kvKey)}>{key}</span>
                                <span {...stylex.props(styles.kvValue)}>{value}</span>
                              </Fragment>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
