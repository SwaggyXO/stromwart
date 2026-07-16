import * as stylex from '@stylexjs/stylex';
import type { AlertSeverity } from '@/types';

const styles = stylex.create({
  badge: {
    paddingTop: 2,
    paddingBottom: 2,
    paddingLeft: 8,
    paddingRight: 8,
    borderRadius: 99,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
  },
  critical: { color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.15)' },
  high: { color: '#f97316', backgroundColor: 'rgba(249,115,22,0.15)' },
  medium: { color: '#eab308', backgroundColor: 'rgba(234,179,8,0.15)' },
  low: { color: '#22c55e', backgroundColor: 'rgba(34,197,94,0.15)' },
});

export default function SeverityBadge({ severity }: { severity: AlertSeverity | string }) {
  const variant =
    severity === 'critical'
      ? styles.critical
      : severity === 'high'
        ? styles.high
        : severity === 'medium'
          ? styles.medium
          : styles.low;

  return <span {...stylex.props(styles.badge, variant)}>{severity}</span>;
}
