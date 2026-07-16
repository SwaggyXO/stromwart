import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { AlertRead, ApprovalCreate, ProposalRead, RejectCreate, SimulationRead } from '@/types';

/** POST /v1/alerts/{id}/acknowledge */
export function useAcknowledgeAlert(eventId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) =>
      apiFetch<AlertRead>(`/alerts/${alertId}/acknowledge`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts', eventId] });
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });
}

/** POST /v1/proposals/{id}/approve */
export function useApproveProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      proposalId,
      body,
    }: {
      proposalId: string;
      body: ApprovalCreate;
    }) =>
      apiFetch<ProposalRead>(`/proposals/${proposalId}/approve`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['incident', data.incident_id] });
      qc.invalidateQueries({ queryKey: ['proposals', data.incident_id] });
      qc.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
}

/** POST /v1/proposals/{id}/reject */
export function useRejectProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      proposalId,
      body,
    }: {
      proposalId: string;
      body: RejectCreate;
    }) =>
      apiFetch<ProposalRead>(`/proposals/${proposalId}/reject`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['incident', data.incident_id] });
      qc.invalidateQueries({ queryKey: ['proposals', data.incident_id] });
      qc.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
}

/** POST /v1/proposals/{id}/simulate */
export function useSimulateAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (proposalId: string) =>
      apiFetch<SimulationRead>(`/proposals/${proposalId}/simulate`, {
        method: 'POST',
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incident'] });
      qc.invalidateQueries({ queryKey: ['proposals'] });
      qc.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
}

/** POST /v1/incidents/{id}/resolve */
export function useResolveIncident() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (incidentId: string) =>
      apiFetch(`/incidents/${incidentId}/resolve`, { method: 'POST' }),
    onSuccess: (_data, incidentId) => {
      qc.invalidateQueries({ queryKey: ['incident', incidentId] });
      qc.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
}
