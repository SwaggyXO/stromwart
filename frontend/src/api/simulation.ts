import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, clearActiveEventId, setActiveEventId } from './client';
import { useAppStore } from '@/store/useAppStore';

export interface Scenario {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  category: string;
  sessions_peak: number;
  phase_count: number;
}

export interface SimulationStatus {
  status: 'idle' | 'running' | 'completed' | 'failed';
  scenario_id: string | null;
  progress: number;
  current_phase: string;
  event_id: string | null;
  sessions_provisioned?: number | null;
  sessions_peak_narrative?: number | null;
  execution_mode?: 'deterministic' | 'llm_enriched' | null;
}

function clearDemoClientState(qc: ReturnType<typeof useQueryClient>) {
  useAppStore.getState().clearOptimisticAudit();
  useAppStore.getState().resetAlertTracking();
  qc.removeQueries({ queryKey: ['evals'] });
  qc.invalidateQueries({ queryKey: ['evals'] });
}

export function useScenarios() {
  return useQuery<Scenario[]>({
    queryKey: ['simulation', 'scenarios'],
    queryFn: () => apiFetch('/simulation/scenarios'),
  });
}

export function useSimulationStatus(enabled = true) {
  return useQuery<SimulationStatus>({
    queryKey: ['simulation', 'status'],
    queryFn: () => apiFetch('/simulation/status'),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'running' || status === 'completed' ? 2000 : 10_000;
    },
    enabled,
  });
}

export function useStartSimulation() {
  const qc = useQueryClient();
  return useMutation<SimulationStatus, Error, { scenario_id: string; speed_multiplier?: number }>({
    mutationFn: (params) =>
      apiFetch<SimulationStatus>('/simulation/start', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
    onSuccess: (data) => {
      clearDemoClientState(qc);
      qc.setQueryData(['simulation', 'status'], data);
      if (data.event_id) {
        setActiveEventId(data.event_id);
      }
      qc.invalidateQueries({ queryKey: ['simulation'] });
      qc.invalidateQueries({ queryKey: ['event', 'active'] });
      qc.invalidateQueries({ queryKey: ['session-stats'] });
      qc.invalidateQueries({ queryKey: ['kpis'] });
      qc.invalidateQueries({ queryKey: ['sessions'] });
      qc.invalidateQueries({ queryKey: ['incidents'] });
      qc.invalidateQueries({ queryKey: ['alerts'] });
      qc.invalidateQueries({ queryKey: ['forecast'] });
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });
}

export function useStopSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch('/simulation/stop', { method: 'POST' }),
    onSuccess: () => {
      clearDemoClientState(qc);
      qc.setQueryData(['simulation', 'status'], {
        status: 'idle',
        scenario_id: null,
        progress: 0,
        current_phase: '',
        event_id: null,
      });
      clearActiveEventId();
      qc.invalidateQueries({ queryKey: ['simulation'] });
      qc.invalidateQueries({ queryKey: ['event', 'active'] });
      qc.removeQueries({ queryKey: ['session-stats'] });
      qc.removeQueries({ queryKey: ['kpis'] });
      qc.removeQueries({ queryKey: ['sessions'] });
      qc.removeQueries({ queryKey: ['incidents'] });
      qc.removeQueries({ queryKey: ['alerts'] });
      qc.removeQueries({ queryKey: ['forecast'] });
      qc.removeQueries({ queryKey: ['audit'] });
    },
  });
}
