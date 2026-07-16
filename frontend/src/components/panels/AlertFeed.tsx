import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import { Bell, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useAcknowledgeAlert } from '@/api/mutations';
import SeverityBadge from '@/components/ui/SeverityBadge';
import type { AlertRead } from '@/types';

const styles = stylex.create({
  card: {
    padding: 0,
    overflow: 'hidden',
  },
  header: {
    paddingTop: 14,
    paddingBottom: 14,
    paddingLeft: 18,
    paddingRight: 18,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  count: {
    paddingTop: 2,
    paddingBottom: 2,
    paddingLeft: 8,
    paddingRight: 8,
    borderRadius: 99,
    fontSize: 11,
    fontWeight: 700,
    backgroundColor: 'var(--sw-red-dim)',
    color: 'var(--sw-red)',
  },
  list: {
    maxHeight: 320,
    overflowY: 'auto',
  },
  row: {
    paddingTop: 12,
    paddingBottom: 12,
    paddingLeft: 18,
    paddingRight: 18,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  rowResolved: {
    opacity: 0.45,
  },
  rowInner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  meta: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  mono: {
    fontSize: 11,
    color: 'var(--sw-text-faint)',
    fontFamily: 'var(--font-mono)',
  },
  desc: {
    fontSize: 13,
    color: 'var(--sw-text)',
    lineHeight: 1.4,
  },
  slice: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    marginTop: 3,
    fontFamily: 'var(--font-mono)',
  },
  ackBtn: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    borderRadius: 'var(--sw-radius-sm)',
    paddingTop: 5,
    paddingBottom: 5,
    paddingLeft: 8,
    paddingRight: 8,
    cursor: 'pointer',
    color: 'var(--sw-text-muted)',
    flexShrink: 0,
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    fontSize: 11,
  },
  empty: {
    padding: 24,
    textAlign: 'center',
    fontSize: 13,
    color: 'var(--sw-text-faint)',
  },
});

export default function AlertFeed({
  alerts = [],
  eventId,
  showHeader = true,
}: {
  alerts?: AlertRead[];
  eventId?: string;
  showHeader?: boolean;
}) {
  const acknowledge = useAcknowledgeAlert(eventId);
  const openCount = alerts.filter((a) => a.state === 'open').length;

  return (
    <div {...glassProps(styles.card)}>
      {showHeader && (
        <div {...stylex.props(styles.header)}>
          <div {...stylex.props(styles.headerLeft)}>
            <Bell size={15} color="var(--sw-accent)" />
            <span {...stylex.props(styles.title)}>Alert Feed</span>
          </div>
          <span {...stylex.props(styles.count)}>{openCount} open</span>
        </div>
      )}

      <div {...stylex.props(styles.list)}>
        {alerts.length === 0 ? (
          <div {...stylex.props(styles.empty)}>No alerts for this event yet</div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              {...stylex.props(styles.row, alert.state === 'resolved' && styles.rowResolved)}
            >
              <div {...stylex.props(styles.rowInner)}>
                <div {...stylex.props(styles.content)}>
                  <div {...stylex.props(styles.meta)}>
                    <SeverityBadge severity={alert.severity} />
                    <span {...stylex.props(styles.mono)}>
                      {format(new Date(alert.created_at), 'HH:mm:ss')}
                    </span>
                  </div>
                  <div {...stylex.props(styles.desc)}>{alert.description}</div>
                  <div {...stylex.props(styles.slice)}>{alert.slice_key}</div>
                </div>
                {alert.state === 'open' && (
                  <button
                    type="button"
                    title="Acknowledge"
                    disabled={acknowledge.isPending}
                    onClick={() => acknowledge.mutate(alert.id)}
                    {...stylex.props(styles.ackBtn)}
                  >
                    <CheckCircle size={12} />
                    Ack
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
