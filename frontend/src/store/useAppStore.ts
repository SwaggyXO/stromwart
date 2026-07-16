import { create } from 'zustand';
import type { AuditEventRead, LiveEventUpdate, LiveIncidentSummary } from '@/types';

interface AppState {
  selectedIncidentId: string | null;
  isSimulating: boolean;
  sseConnected: boolean;
  liveUpdate: LiveEventUpdate | null;
  _optimisticAuditEvents: AuditEventRead[];
  seenAlertIds: string[];
  alertHydratedEventId: string | null;

  setSelectedIncident: (id: string | null) => void;
  startSimulation: () => void;
  stopSimulation: () => void;
  setSseConnected: (connected: boolean) => void;
  setLiveUpdate: (update: LiveEventUpdate) => void;
  markAlertsSeen: (ids: string[]) => void;
  setAlertHydratedEventId: (eventId: string | null) => void;
  resetAlertTracking: () => void;
  clearOptimisticAudit: () => void;
  addAuditEvent: (
    event: Omit<AuditEventRead, 'audit_id' | 'created_at' | 'payload'> & {
      payload?: Record<string, unknown>;
      description?: string;
    },
  ) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedIncidentId: null,
  isSimulating: false,
  sseConnected: false,
  liveUpdate: null,
  _optimisticAuditEvents: [],
  seenAlertIds: [],
  alertHydratedEventId: null,

  setSelectedIncident: (id) => set({ selectedIncidentId: id }),
  startSimulation: () => set({ isSimulating: true }),
  stopSimulation: () => set({ isSimulating: false }),
  setSseConnected: (connected) => set({ sseConnected: connected }),
  setLiveUpdate: (update) => set({ liveUpdate: update }),

  markAlertsSeen: (ids) =>
    set((state) => {
      const merged = new Set([...state.seenAlertIds, ...ids]);
      return { seenAlertIds: [...merged] };
    }),

  setAlertHydratedEventId: (eventId) => set({ alertHydratedEventId: eventId }),

  resetAlertTracking: () =>
    set({ seenAlertIds: [], alertHydratedEventId: null }),

  clearOptimisticAudit: () => set({ _optimisticAuditEvents: [] }),

  addAuditEvent: (event) =>
    set((state) => ({
      _optimisticAuditEvents: [
        {
          audit_id: `aud_${Date.now()}`,
          created_at: new Date().toISOString(),
          correlation_id: event.correlation_id,
          actor_type: event.actor_type,
          artifact_type: event.artifact_type,
          artifact_id: event.artifact_id,
          payload: event.payload ?? { description: event.description },
        },
        ...state._optimisticAuditEvents,
      ],
    })),
}));

export function selectLiveIncidents(state: AppState): LiveIncidentSummary[] {
  return state.liveUpdate?.incidents ?? [];
}

export function selectActiveSessions(state: AppState): number {
  return state.liveUpdate?.active_sessions ?? 0;
}
