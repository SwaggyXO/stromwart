import * as stylex from '@stylexjs/stylex';
import { glassProps, primaryButtonProps } from '@/lib/stylex';
import {
  useScenarios,
  useSimulationStatus,
  useStartSimulation,
  useStopSimulation,
} from '@/api/simulation';
import { useState, useEffect } from 'react';
import { Play, Square, Zap } from 'lucide-react';

const styles = stylex.create({
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--sw-text)',
  },
  scenarioGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: 12,
  },
  scenarioCard: {
    padding: 16,
    cursor: 'pointer',
    transitionProperty: 'transform',
    transitionDuration: '150ms',
  },
  scenarioName: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--sw-text)',
    marginBottom: 4,
  },
  scenarioDesc: {
    fontSize: 11,
    color: 'var(--sw-text-muted)',
    lineHeight: 1.4,
  },
  scenarioMeta: {
    display: 'flex',
    gap: 12,
    marginTop: 8,
    fontSize: 10,
    color: 'var(--sw-text-faint)',
    fontFamily: 'var(--font-mono)',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
  },
  progressBar: {
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255,255,255,0.06)',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
    backgroundColor: 'var(--sw-accent)',
    transitionProperty: 'width',
    transitionDuration: '500ms',
  },
  statusText: {
    fontSize: 12,
    color: 'var(--sw-text-muted)',
    fontStyle: 'italic',
  },
  completedBanner: {
    padding: 12,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'var(--sw-accent-dim)',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'rgba(249,115,22,0.25)',
    fontSize: 13,
    color: 'var(--sw-text-muted)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    flexWrap: 'wrap',
  },
  secondaryBtn: {
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 12,
    paddingRight: 12,
    borderRadius: 'var(--sw-radius-md)',
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderStyle: 'solid',
    borderColor: 'var(--sw-border)',
    color: 'var(--sw-text-muted)',
    fontSize: 12,
    cursor: 'pointer',
  },
});

type SimulationControlProps = {
  compact?: boolean;
};

export default function SimulationControl({ compact = false }: SimulationControlProps) {
  const { data: scenarios } = useScenarios();
  const { data: simStatus } = useSimulationStatus();
  const startSim = useStartSimulation();
  const stopSim = useStopSimulation();
  const [selected, setSelected] = useState<string | null>(null);
  const [showPicker, setShowPicker] = useState(false);

  const status = simStatus?.status ?? 'idle';
  const isRunning = status === 'running';
  const isCompleted = status === 'completed';
  const isIdle = status === 'idle';

  const showFullPicker =
    !isRunning && (isIdle || !compact || (isCompleted && showPicker));

  useEffect(() => {
    if (simStatus?.scenario_id && !isRunning) {
      setSelected(simStatus.scenario_id);
    }
  }, [simStatus?.scenario_id, isRunning]);

  useEffect(() => {
    if (isRunning) setShowPicker(false);
  }, [isRunning]);

  const scenarioName =
    scenarios?.find((s) => s.id === simStatus?.scenario_id)?.name ??
    simStatus?.scenario_id ??
    'scenario';

  const canStart = Boolean(selected) && !startSim.isPending;

  return (
    <div {...stylex.props(styles.wrapper)}>
      {!compact && (
        <div {...stylex.props(styles.header)}>
          <Zap size={16} />
          Demo Scenarios
        </div>
      )}

      {compact && isCompleted && !showPicker && (
        <div {...stylex.props(styles.completedBanner)}>
          <span>
            Simulation complete · <strong>{scenarioName}</strong>
          </span>
          <div {...stylex.props(styles.actions)}>
            <button
              type="button"
              {...stylex.props(styles.secondaryBtn)}
              onClick={() => setShowPicker(true)}
            >
              Change scenario
            </button>
            <button
              {...primaryButtonProps()}
              disabled={startSim.isPending}
              onClick={() =>
                simStatus?.scenario_id &&
                startSim.mutate({ scenario_id: simStatus.scenario_id })
              }
            >
              <Play size={14} /> Re-run same
            </button>
          </div>
        </div>
      )}

      {showFullPicker && (
        <div {...stylex.props(styles.scenarioGrid)}>
          {(scenarios ?? []).map((s) => {
            const glass = glassProps(styles.scenarioCard);
            const peakLabel = `${(s.sessions_peak / 1000).toFixed(0)}k peak audience`;
            return (
              <div
                key={s.id}
                onClick={() => setSelected(s.id)}
                {...glass}
                className={[
                  glass.className,
                  selected === s.id ? 'scenario-card-selected' : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                <div {...stylex.props(styles.scenarioName)}>{s.name}</div>
                <div {...stylex.props(styles.scenarioDesc)}>{s.description}</div>
                <div {...stylex.props(styles.scenarioMeta)}>
                  <span>{s.duration_minutes}min</span>
                  <span>{peakLabel}</span>
                  <span>{s.phase_count} phases</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isRunning && (
        <>
          <div {...stylex.props(styles.progressBar)}>
            <div
              {...stylex.props(styles.progressFill)}
              style={{ width: `${(simStatus?.progress ?? 0) * 100}%` }}
            />
          </div>
          <div {...stylex.props(styles.statusText)}>{simStatus?.current_phase}</div>
        </>
      )}

      <div {...stylex.props(styles.actions)}>
        {!isRunning ? (
          (!compact || !isCompleted || showPicker) && (
            <button
              {...primaryButtonProps()}
              disabled={!canStart}
              onClick={() => selected && startSim.mutate({ scenario_id: selected })}
            >
              <Play size={14} /> Start Simulation
            </button>
          )
        ) : (
          <button
            {...primaryButtonProps()}
            onClick={() => stopSim.mutate()}
            disabled={stopSim.isPending}
          >
            <Square size={14} /> Stop
          </button>
        )}
      </div>
    </div>
  );
}
