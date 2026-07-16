import { useState } from 'react';
import * as stylex from '@stylexjs/stylex';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { FailureCluster, TraceSummary } from '@/types';
import {
  formatClusterLabel,
  formatDimensionName,
  formatWorstDimensionHint,
  isTracePassing,
} from '@/lib/evalDisplay';

const styles = stylex.create({
  wrap: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 13,
  },
  th: {
    textAlign: 'left',
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--sw-text-faint)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
  },
  td: {
    paddingTop: 10,
    paddingBottom: 10,
    paddingLeft: 14,
    paddingRight: 14,
    color: 'var(--sw-text-muted)',
    borderBottomWidth: 1,
    borderBottomStyle: 'solid',
    borderBottomColor: 'var(--sw-border)',
    verticalAlign: 'top',
  },
  expandBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'transparent',
    borderWidth: 0,
    color: 'var(--sw-text)',
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    cursor: 'pointer',
    padding: 0,
  },
  statusCell: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  statusHint: {
    fontSize: 10,
    color: 'var(--sw-text-faint)',
    textTransform: 'none',
    letterSpacing: 0,
    fontWeight: 400,
  },
  detailRow: {
    backgroundColor: 'var(--sw-surface-2)',
  },
  detailCell: {
    paddingTop: 8,
    paddingBottom: 12,
    paddingLeft: 36,
    paddingRight: 14,
  },
  scoreGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: 8,
  },
  scoreItem: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.4,
  },
  scoreDim: {
    fontWeight: 600,
    color: 'var(--sw-text)',
    textTransform: 'capitalize',
  },
});

function TraceRow({
  trace,
  clusters,
}: {
  trace: TraceSummary;
  clusters?: FailureCluster[];
}) {
  const [open, setOpen] = useState(false);
  const worstHint = formatWorstDimensionHint(trace.scores);
  const passing = isTracePassing(trace.overall_score);

  return (
    <>
      <tr>
        <td {...stylex.props(styles.td)}>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            {...stylex.props(styles.expandBtn)}
            title={trace.trace_id}
          >
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {trace.trace_id.slice(0, 12)}…
          </button>
        </td>
        <td {...stylex.props(styles.td)}>{(trace.overall_score * 100).toFixed(0)}%</td>
        <td {...stylex.props(styles.td)}>
          {formatClusterLabel(trace.cluster_id, clusters)}
        </td>
        <td {...stylex.props(styles.td)}>
          <div {...stylex.props(styles.statusCell)}>
            <span className={passing ? 'badge-pass' : 'badge-fail'}>
              {passing ? 'PASS' : 'FAIL'}
            </span>
            {worstHint && <span {...stylex.props(styles.statusHint)}>{worstHint}</span>}
          </div>
        </td>
      </tr>
      {open && (
        <tr {...stylex.props(styles.detailRow)}>
          <td colSpan={4} {...stylex.props(styles.detailCell)}>
            <div {...stylex.props(styles.scoreGrid)}>
              {(trace.scores ?? []).map((score) => (
                <div key={score.dimension} {...stylex.props(styles.scoreItem)}>
                  <div {...stylex.props(styles.scoreDim)}>
                    {formatDimensionName(score.dimension)}: {(score.score * 100).toFixed(0)}%
                  </div>
                  <div>{score.explanation}</div>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function EvalTraceTable({
  traces,
  clusters,
}: {
  traces: TraceSummary[];
  clusters?: FailureCluster[];
}) {
  return (
    <div {...stylex.props(styles.wrap)}>
      <table {...stylex.props(styles.table)}>
        <thead>
          <tr>
            {['Trace', 'Score', 'Cluster', 'Status'].map((header) => (
              <th key={header} {...stylex.props(styles.th)}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {traces.map((trace) => (
            <TraceRow key={trace.trace_id} trace={trace} clusters={clusters} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
