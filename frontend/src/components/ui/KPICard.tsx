import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import type { KPISnapshot } from '@/types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const styles = stylex.create({
  card: {
    paddingTop: 20,
    paddingBottom: 20,
    paddingLeft: 22,
    paddingRight: 22,
    position: 'relative',
    overflow: 'hidden',
  },
  gloss: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '50%',
    backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, transparent 100%)',
    borderTopLeftRadius: 'var(--sw-radius-lg)',
    borderTopRightRadius: 'var(--sw-radius-lg)',
    pointerEvents: 'none',
  },
  body: {
    position: 'relative',
    zIndex: 1,
  },
  label: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    fontWeight: 600,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  valueRow: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: 8,
    marginBottom: 8,
  },
  value: {
    fontSize: 32,
    fontWeight: 700,
    lineHeight: 1,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text)',
    letterSpacing: '-0.03em',
  },
  unit: {
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    marginBottom: 3,
  },
  trendRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
  },
  trendHint: {
    fontSize: 12,
    color: 'var(--sw-text-faint)',
  },
  statusGood: { color: 'var(--sw-green)' },
  statusWarning: { color: 'var(--sw-yellow)' },
  statusCritical: { color: 'var(--sw-red)' },
  strip: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: 3,
    height: '100%',
    borderTopLeftRadius: 3,
    borderBottomLeftRadius: 3,
  },
  stripGood: { backgroundColor: 'var(--sw-green)', boxShadow: '0 0 12px var(--sw-green)' },
  stripWarning: { backgroundColor: 'var(--sw-yellow)', boxShadow: '0 0 12px var(--sw-yellow)' },
  stripCritical: { backgroundColor: 'var(--sw-red)', boxShadow: '0 0 12px var(--sw-red)' },
});

export default function KPICard({ kpi }: { kpi: KPISnapshot }) {
  const TrendIcon = kpi.trend === 'up' ? TrendingUp : kpi.trend === 'down' ? TrendingDown : Minus;
  const statusStyle =
    kpi.status === 'good'
      ? styles.statusGood
      : kpi.status === 'warning'
        ? styles.statusWarning
        : styles.statusCritical;
  const stripStyle =
    kpi.status === 'good'
      ? styles.stripGood
      : kpi.status === 'warning'
        ? styles.stripWarning
        : styles.stripCritical;

  return (
    <div {...glassProps(styles.card)}>
      <div {...stylex.props(styles.gloss)} />
      <div {...stylex.props(styles.body)}>
        <div {...stylex.props(styles.label)}>{kpi.label}</div>
        <div {...stylex.props(styles.valueRow)}>
          <span {...stylex.props(styles.value)}>{kpi.value}</span>
          {kpi.unit != null && kpi.unit !== '' && (
            <span {...stylex.props(styles.unit)}>{kpi.unit}</span>
          )}
        </div>
        <div {...stylex.props(styles.trendRow)}>
          <TrendIcon size={13} {...stylex.props(statusStyle)} />
          {kpi.delta != null && (
            <span {...stylex.props(styles.trendHint, statusStyle)}>
              {kpi.delta > 0 ? '+' : ''}
              {kpi.delta.toFixed(1)}
            </span>
          )}
          {kpi.delta != null && (
            <span {...stylex.props(styles.trendHint)}>vs prev. 5m</span>
          )}
        </div>
      </div>
      <div {...stylex.props(styles.strip, stripStyle)} />
    </div>
  );
}
