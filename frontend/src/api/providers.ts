import { useMutation, useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';

export interface DiscoveryResult {
  models: string[];
  status: 'connected' | 'unreachable' | 'auth_required' | 'unsupported';
  message: string | null;
}

export interface ProviderGuide {
  title: string;
  description: string;
  setup_steps: string;
  docs_url: string;
  free: string;
  requires_api_key: string;
  requires_endpoint: string;
}

export function useDiscoverModels() {
  return useMutation({
    mutationFn: (params: {
      provider_id: string;
      api_key?: string;
      endpoint?: string;
    }) =>
      apiFetch<DiscoveryResult>(
        `/settings/providers/${params.provider_id}/discover-models`,
        {
          method: 'POST',
          body: JSON.stringify({
            api_key: params.api_key,
            endpoint: params.endpoint,
          }),
        },
      ),
  });
}

export function useProviderGuide(providerId: string | null) {
  return useQuery<ProviderGuide>({
    queryKey: ['provider-guide', providerId],
    queryFn: () => apiFetch(`/settings/providers/${providerId}/guide`),
    enabled: !!providerId && providerId !== 'disabled',
  });
}
