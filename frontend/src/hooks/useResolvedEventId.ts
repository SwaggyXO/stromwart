import { useEffect } from 'react';
import { clearActiveEventId, setActiveEventId } from '@/api/client';
import { useSimulationStatus } from '@/api/simulation';

/**
 * Dashboard event id comes only from the simulation engine while a demo is
 * running or has just finished. Idle + historical DB events are ignored so
 * stale FIFA (etc.) rows cannot hijack the Live Event page.
 */
export function useResolvedEventId(): string | undefined {
  const { data: simStatus } = useSimulationStatus();

  const simEventId = simStatus?.event_id ?? undefined;
  const simEngaged =
    simStatus?.status === 'running' ||
    simStatus?.status === 'completed' ||
    simStatus?.status === 'failed';

  useEffect(() => {
    if (simEngaged && simEventId) {
      setActiveEventId(simEventId);
      return;
    }
    if (simStatus?.status === 'idle') {
      clearActiveEventId();
    }
  }, [simEngaged, simEventId, simStatus?.status]);

  if (simEngaged && simEventId) {
    return simEventId;
  }
  return undefined;
}
