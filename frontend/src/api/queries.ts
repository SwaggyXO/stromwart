import { useQuery } from '@tanstack/react-query';
import { ApiError, apiFetch } from './client';
import type {
  AlertRead,
  AuditEventRead,
  EvalSummaryResponse,
  EventRead,
  EventSessionStats,
  ForecastSeriesPoint,
  IncidentRead,
  KPISnapshot,
  ProposalRead,
  AgentRunRead,
  SessionSummary,
} from '@/types';

function skipRetryOnMissingEvent(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status === 404) return false;
  return failureCount < 1;
}

/** GET /v1/events/active */
export function useActiveEvent() {
  return useQuery<EventRead>({
    queryKey: ['event', 'active'],
    queryFn: () => apiFetch('/events/active'),
    refetchInterval: 30_000,
    retry: 1,
  });
}

/** Sessions — GET /v1/events/{event_id}/sessions */
export function useSessions(eventId: string | undefined) {
  return useQuery<SessionSummary[]>({
    queryKey: ['sessions', eventId],
    queryFn: () => apiFetch(`/events/${eventId}/sessions?limit=50`),
    enabled: !!eventId,
    refetchInterval: 10_000,
    retry: skipRetryOnMissingEvent,
  });
}

/** Authoritative session counts — GET /v1/events/{event_id}/session-stats */
export function useEventSessionStats(eventId: string | undefined) {
  return useQuery<EventSessionStats>({
    queryKey: ['session-stats', eventId],
    queryFn: () => apiFetch(`/events/${eventId}/session-stats`),
    enabled: !!eventId,
    refetchInterval: 5_000,
    retry: skipRetryOnMissingEvent,
  });
}

/** KPIs — GET /v1/events/{event_id}/kpis */
export function useKPIs(eventId: string | undefined) {
  return useQuery<KPISnapshot[]>({
    queryKey: ['kpis', eventId],
    queryFn: () => apiFetch(`/events/${eventId}/kpis`),
    enabled: !!eventId,
    refetchInterval: 5_000,
    retry: skipRetryOnMissingEvent,
  });
}

/** Alerts — GET /v1/events/{event_id}/alerts */
export function useAlerts(eventId: string | undefined) {
  return useQuery<AlertRead[]>({
    queryKey: ['alerts', eventId],
    queryFn: () => apiFetch(`/events/${eventId}/alerts?limit=50`),
    enabled: !!eventId,
    refetchInterval: 5_000,
    retry: skipRetryOnMissingEvent,
  });
}

/** Incidents — GET /v1/events/{event_id}/incidents */
export function useIncidents(eventId: string | undefined, activeOnly = true) {
  return useQuery<IncidentRead[]>({
    queryKey: ['incidents', eventId, activeOnly],
    queryFn: () =>
      apiFetch(
        `/events/${eventId}/incidents?active_only=${activeOnly}&limit=50`,
      ),
    enabled: !!eventId,
    refetchInterval: 10_000,
    retry: skipRetryOnMissingEvent,
  });
}

export function useIncidentDetail(incidentId: string | undefined) {
  return useQuery<IncidentRead>({
    queryKey: ['incident', incidentId],
    queryFn: () => apiFetch(`/incidents/${incidentId}`),
    enabled: !!incidentId,
    refetchInterval: 5_000,
  });
}

/** Proposals — GET /v1/incidents/{incident_id}/proposals */
export function useIncidentProposals(incidentId: string | undefined) {
  return useQuery<ProposalRead[]>({
    queryKey: ['proposals', incidentId],
    queryFn: () => apiFetch(`/incidents/${incidentId}/proposals?limit=10`),
    enabled: !!incidentId,
    refetchInterval: 5_000,
  });
}

/** Agent runs — GET /v1/incidents/{incident_id}/agent-runs */
export function useAgentRuns(incidentId: string | undefined) {
  return useQuery<AgentRunRead[]>({
    queryKey: ['agent-runs', incidentId],
    queryFn: () => apiFetch(`/incidents/${incidentId}/agent-runs?limit=20`),
    enabled: !!incidentId,
    refetchInterval: 10_000,
  });
}

/** Audit trail for one incident — GET /v1/audit/{correlation_id} */
export function useIncidentAuditTimeline(incidentId: string | undefined) {
  return useQuery<AuditEventRead[]>({
    queryKey: ['audit', 'incident', incidentId],
    queryFn: () => apiFetch(`/audit/${incidentId}`),
    enabled: !!incidentId,
    refetchInterval: 5_000,
  });
}

/** Audit — GET /v1/audit (scoped to event when eventId is set) */
export function useAuditLog(limit = 50, eventId?: string) {
  return useQuery<AuditEventRead[]>({
    queryKey: ['audit', limit, eventId],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (eventId) params.set('event_id', eventId);
      return apiFetch(`/audit?${params.toString()}`);
    },
    enabled: !!eventId,
    refetchInterval: 5_000,
  });
}

/** Forecast — GET /v1/modeling/forecast (event-scoped time series) */
export function useForecast(eventId: string | undefined) {
  return useQuery<ForecastSeriesPoint[]>({
    queryKey: ['forecast', eventId],
    queryFn: () =>
      apiFetch<ForecastSeriesPoint[]>(
        `/modeling/forecast?event_id=${eventId}&metric_name=stall_risk&horizon_minutes=10&step_seconds=60`,
      ),
    enabled: !!eventId,
    refetchInterval: 30_000,
    retry: skipRetryOnMissingEvent,
  });
}

export function useEvalSummary() {
  return useQuery<EvalSummaryResponse>({
    queryKey: ['evals', 'summary'],
    queryFn: () => apiFetch('/evals/summary'),
    refetchInterval: 15_000,
  });
}
