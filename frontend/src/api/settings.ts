import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { EvalSummaryResponse, FailureCluster, ProviderInfo, SystemSettings, TraceSummary } from '@/types';

export interface TraceListResponse {
  traces: TraceSummary[];
}

export interface FailureClusterListResponse {
  clusters: FailureCluster[];
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  latency_ms: number;
}

export function useSettings() {
  return useQuery<SystemSettings>({
    queryKey: ['settings'],
    queryFn: () => apiFetch('/settings'),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (changes: Partial<SystemSettings>) =>
      apiFetch<SystemSettings>('/settings', {
        method: 'PUT',
        body: JSON.stringify(changes),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  });
}

export function useProviders() {
  return useQuery<ProviderInfo[]>({
    queryKey: ['settings', 'providers'],
    queryFn: () => apiFetch('/settings/providers'),
  });
}

/** POST /v1/settings/providers/test — query params per OpenAPI */
export function useTestProvider() {
  return useMutation({
    mutationFn: (params: {
      provider_id: string;
      model: string;
      api_key?: string;
      endpoint?: string;
    }) => {
      const qs = new URLSearchParams({
        provider_id: params.provider_id,
        model: params.model,
      });
      if (params.api_key) qs.set('api_key', params.api_key);
      if (params.endpoint) qs.set('endpoint', params.endpoint);
      return apiFetch<TestConnectionResponse>(
        `/settings/providers/test?${qs.toString()}`,
        { method: 'POST', timeoutMs: 15_000 },
      );
    },
  });
}

export function useEvalSummary() {
  return useQuery<EvalSummaryResponse>({
    queryKey: ['evals', 'summary'],
    queryFn: () => apiFetch('/evals/summary'),
    refetchInterval: 30_000,
  });
}

export function useEvalTraces(limit = 50) {
  return useQuery<TraceListResponse>({
    queryKey: ['evals', 'traces', limit],
    queryFn: () => apiFetch<TraceListResponse>(`/evals/traces?limit=${limit}`),
  });
}

export function useFailureClusters() {
  return useQuery<FailureClusterListResponse>({
    queryKey: ['evals', 'clusters'],
    queryFn: () => apiFetch<FailureClusterListResponse>('/evals/clusters'),
  });
}
