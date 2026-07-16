import * as stylex from '@stylexjs/stylex';
import type { PolicyStateDisplay, ProposalState } from '@/types';
import { toPolicyDisplay } from '@/types';

const styles = stylex.create({
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    paddingTop: 3,
    paddingBottom: 3,
    paddingLeft: 10,
    paddingRight: 10,
    borderRadius: 99,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.07em',
    fontFamily: 'var(--font-mono)',
    borderWidth: 1,
    borderStyle: 'solid',
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: '50%',
    display: 'inline-block',
  },
  OBSERVE: {
    color: '#94a3b8',
    backgroundColor: 'rgba(148,163,184,0.1)',
    borderColor: 'rgba(148,163,184,0.2)',
  },
  INVESTIGATE: {
    color: '#3b82f6',
    backgroundColor: 'rgba(59,130,246,0.12)',
    borderColor: 'rgba(59,130,246,0.3)',
  },
  RECOMMEND: {
    color: '#f97316',
    backgroundColor: 'rgba(249,115,22,0.12)',
    borderColor: 'rgba(249,115,22,0.35)',
  },
  SIMULATE: {
    color: '#a855f7',
    backgroundColor: 'rgba(168,85,247,0.12)',
    borderColor: 'rgba(168,85,247,0.3)',
  },
  APPROVE_REQUIRED: {
    color: '#eab308',
    backgroundColor: 'rgba(234,179,8,0.12)',
    borderColor: 'rgba(234,179,8,0.35)',
  },
  BLOCKED: {
    color: '#ef4444',
    backgroundColor: 'rgba(239,68,68,0.12)',
    borderColor: 'rgba(239,68,68,0.3)',
  },
  APPROVED: {
    color: '#22c55e',
    backgroundColor: 'rgba(34,197,94,0.12)',
    borderColor: 'rgba(34,197,94,0.3)',
  },
  dotOBSERVE: { backgroundColor: '#94a3b8', boxShadow: '0 0 6px #94a3b8' },
  dotINVESTIGATE: { backgroundColor: '#3b82f6', boxShadow: '0 0 6px #3b82f6' },
  dotRECOMMEND: { backgroundColor: '#f97316', boxShadow: '0 0 6px #f97316' },
  dotSIMULATE: { backgroundColor: '#a855f7', boxShadow: '0 0 6px #a855f7' },
  dotAPPROVE_REQUIRED: { backgroundColor: '#eab308', boxShadow: '0 0 6px #eab308' },
  dotBLOCKED: { backgroundColor: '#ef4444', boxShadow: '0 0 6px #ef4444' },
  dotAPPROVED: { backgroundColor: '#22c55e', boxShadow: '0 0 6px #22c55e' },
});

export default function PolicyBadge({
  state,
}: {
  state: PolicyStateDisplay | ProposalState | string;
}) {
  const display = toPolicyDisplay(state);

  const variant =
    display === 'INVESTIGATE'
      ? styles.INVESTIGATE
      : display === 'RECOMMEND'
        ? styles.RECOMMEND
        : display === 'SIMULATE'
          ? styles.SIMULATE
          : display === 'APPROVE_REQUIRED'
            ? styles.APPROVE_REQUIRED
            : display === 'APPROVED'
              ? styles.APPROVED
              : display === 'BLOCKED'
                ? styles.BLOCKED
                : styles.OBSERVE;

  const dot =
    display === 'INVESTIGATE'
      ? styles.dotINVESTIGATE
      : display === 'RECOMMEND'
        ? styles.dotRECOMMEND
        : display === 'SIMULATE'
          ? styles.dotSIMULATE
          : display === 'APPROVE_REQUIRED'
            ? styles.dotAPPROVE_REQUIRED
            : display === 'APPROVED'
              ? styles.dotAPPROVED
              : display === 'BLOCKED'
                ? styles.dotBLOCKED
                : styles.dotOBSERVE;

  return (
    <span {...stylex.props(styles.badge, variant)}>
      <span {...stylex.props(styles.dot, dot)} />
      {display.replace('_', ' ')}
    </span>
  );
}
