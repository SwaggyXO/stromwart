import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ShieldCheck, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';
import type { IncidentRead } from '@/types';
import { hypothesisText, sliceLabel } from '@/types';
import SeverityBadge from '@/components/ui/SeverityBadge';

const styles = stylex.create({
  card: {
    padding: 20,
    cursor: 'pointer',
    position: 'relative',
    overflow: 'hidden',
  },
  cardResolved: {
    opacity: 0.65,
    borderColor: 'rgba(34, 197, 94, 0.2)',
  },
  gloss: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '40%',
    backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, transparent 100%)',
    pointerEvents: 'none',
    borderTopLeftRadius: 'var(--sw-radius-lg)',
    borderTopRightRadius: 'var(--sw-radius-lg)',
  },
  body: {
    position: 'relative',
    zIndex: 1,
  },
  top: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 10,
  },
  idRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  id: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
  },
  hypothesis: {
    fontSize: 13,
    color: 'var(--sw-text)',
    lineHeight: 1.5,
    marginBottom: 10,
  },
  slice: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    fontFamily: 'var(--font-mono)',
    marginBottom: 10,
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  time: {
    fontSize: 11,
    color: 'var(--sw-text-faint)',
  },
  state: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-blue)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
  stateResolved: {
    color: 'var(--sw-green)',
  },
});

export default function IncidentCard({ incident }: { incident: IncidentRead }) {
  const navigate = useNavigate();
  const text = hypothesisText(incident.hypothesis);
  const preview = text.length > 120 ? `${text.slice(0, 120)}…` : text;
  const isResolved = incident.state === 'resolved';

  return (
    <div
      onClick={() => navigate(`/incidents/${incident.id}`)}
      {...glassProps(styles.card, isResolved && styles.cardResolved)}
    >
      <div {...stylex.props(styles.gloss)} />
      <div {...stylex.props(styles.body)}>
        <div {...stylex.props(styles.top)}>
          <div {...stylex.props(styles.idRow)}>
            {isResolved ? (
              <ShieldCheck size={15} color="var(--sw-green)" />
            ) : (
              <ShieldAlert
                size={15}
                color={incident.severity === 'critical' ? 'var(--sw-red)' : 'var(--sw-accent)'}
              />
            )}
            <span {...stylex.props(styles.id)}>{incident.id.slice(0, 8)}…</span>
          </div>
          {!isResolved && <SeverityBadge severity={incident.severity} />}
        </div>

        <div {...stylex.props(styles.hypothesis)}>{preview}</div>
        <div {...stylex.props(styles.slice)}>
          {incident.slice_key || sliceLabel(incident.affected_slice)}
        </div>

        <div {...stylex.props(styles.footer)}>
          <div {...stylex.props(styles.idRow)}>
            <span {...stylex.props(styles.state, isResolved && styles.stateResolved)}>
              {isResolved ? 'resolved' : incident.state}
            </span>
            <span {...stylex.props(styles.time)}>
              {format(new Date(incident.created_at), 'HH:mm')}
            </span>
          </div>
          <ArrowRight size={14} color="var(--sw-text-faint)" />
        </div>
      </div>
    </div>
  );
}
