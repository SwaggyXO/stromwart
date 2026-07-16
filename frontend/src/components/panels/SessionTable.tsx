import * as stylex from '@stylexjs/stylex';
import { glassProps } from '@/lib/stylex';
import type { SessionSummary } from '@/types';

const styles = stylex.create({
  card: {
    overflow: 'hidden',
    padding: 0,
  },
  header: {
    paddingTop: 14,
    paddingBottom: 10,
    paddingLeft: 18,
    paddingRight: 18,
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
  },
  count: {
    marginLeft: 8,
    fontSize: 11,
    color: 'var(--sw-text-faint)',
    fontWeight: 400,
  },
  scroll: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    paddingTop: 9,
    paddingBottom: 9,
    paddingLeft: 14,
    paddingRight: 14,
    textAlign: 'left',
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--sw-text-faint)',
    letterSpacing: '0.09em',
    textTransform: 'uppercase',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
    whiteSpace: 'nowrap',
  },
  td: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    fontSize: 12,
    color: 'var(--sw-text)',
  },
  mono: {
    fontSize: 11,
    fontFamily: 'var(--font-mono)',
    color: 'var(--sw-text-muted)',
  },
  muted: {
    color: 'var(--sw-text-muted)',
  },
  empty: {
    padding: 24,
    textAlign: 'center',
    fontSize: 13,
    color: 'var(--sw-text-faint)',
  },
  rowAlt: {
    backgroundColor: 'rgba(255,255,255,0.015)',
  },
});

export default function SessionTable({
  sessions,
  totalActive,
}: {
  sessions: SessionSummary[];
  totalActive?: number;
}) {
  return (
    <div {...glassProps(styles.card)}>
      <div {...stylex.props(styles.header)}>
        Session Sample
        <span {...stylex.props(styles.count)}>
          ({sessions.length}
          {totalActive != null ? ` of ${totalActive.toLocaleString()}` : ''})
        </span>
      </div>
      <div {...stylex.props(styles.scroll)}>
        {sessions.length === 0 ? (
          <div {...stylex.props(styles.empty)}>No sessions for this event yet</div>
        ) : (
          <table {...stylex.props(styles.table)}>
            <thead>
              <tr>
                {['Session', 'External ID', 'Client', 'Region', 'Started'].map((h) => (
                  <th key={h} {...stylex.props(styles.th)}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sessions.map((s, i) => (
                <tr key={s.session_id} {...stylex.props(i % 2 === 1 && styles.rowAlt)}>
                  <td {...stylex.props(styles.td, styles.mono)}>{s.session_id.slice(0, 8)}…</td>
                  <td {...stylex.props(styles.td, styles.mono)}>{s.external_id}</td>
                  <td {...stylex.props(styles.td)}>{s.client_type}</td>
                  <td {...stylex.props(styles.td, styles.muted)}>{s.region ?? '—'}</td>
                  <td {...stylex.props(styles.td, styles.mono)}>
                    {s.started_at ? new Date(s.started_at).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
