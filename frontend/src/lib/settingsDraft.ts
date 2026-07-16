import type { SystemSettings } from '@/types';

export const LLM_SETTING_KEYS = [
  'llm_provider',
  'llm_model',
  'llm_endpoint',
  'llm_api_key',
  'llm_discovered_models',
  'llm_connection_verified',
] as const;

function stableStringify(value: unknown): string {
  return JSON.stringify(value ?? null);
}

export function settingsEqual(
  a: Partial<SystemSettings> | null | undefined,
  b: Partial<SystemSettings> | null | undefined,
): boolean {
  if (!a && !b) return true;
  if (!a || !b) return false;
  return stableStringify(a) === stableStringify(b);
}

export function isLlmDirty(
  draft: Partial<SystemSettings>,
  saved: Partial<SystemSettings>,
): boolean {
  for (const key of LLM_SETTING_KEYS) {
    if (stableStringify(draft[key]) !== stableStringify(saved[key])) {
      return true;
    }
  }
  return false;
}

/** Demo scenario is the only viable data source in Phase 1 — always keep it active. */
export function withLockedDataSources(
  sources: SystemSettings['data_sources'] | undefined,
): SystemSettings['data_sources'] {
  return (sources ?? []).map((source) =>
    source.type === 'simulation' ? { ...source, active: true } : source,
  );
}

export function buildSavePayload(
  draft: Partial<SystemSettings>,
  saved: Partial<SystemSettings>,
  connectionVerified: boolean,
): Partial<SystemSettings> {
  const normalizedDraft: Partial<SystemSettings> = {
    ...draft,
    data_sources: withLockedDataSources(draft.data_sources),
  };
  const payload: Partial<SystemSettings> = {};
  for (const key of Object.keys(normalizedDraft) as (keyof SystemSettings)[]) {
    if (stableStringify(normalizedDraft[key]) !== stableStringify(saved[key])) {
      (payload as Record<string, unknown>)[key] = normalizedDraft[key];
    }
  }
  if (isLlmDirty(normalizedDraft, saved) && normalizedDraft.llm_provider !== 'disabled') {
    payload.llm_connection_verified = connectionVerified;
  }
  return payload;
}

export function touchesLlmSettings(changes: Partial<SystemSettings>): boolean {
  return LLM_SETTING_KEYS.some((key) => key in changes);
}
