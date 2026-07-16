const API_BASE = '/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { timeoutMs?: number } = {},
): Promise<T> {
  const { timeoutMs, ...fetchOptions } = options;
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string> | undefined),
  };

  if (fetchOptions.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const controller = timeoutMs ? new AbortController() : null;
  const timeoutId =
    controller && timeoutMs
      ? window.setTimeout(() => controller.abort(), timeoutMs)
      : null;

  try {
    const res = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller?.signal ?? fetchOptions.signal,
    });

    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new ApiError(res.status, body || res.statusText);
    }

    if (res.status === 204) {
      return undefined as T;
    }

    const text = await res.text();
    if (!text) return undefined as T;
    return JSON.parse(text) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(408, 'Request timed out');
    }
    throw error;
  } finally {
    if (timeoutId) window.clearTimeout(timeoutId);
  }
}

/** Active event id — env/query/localStorage override, else resolved from GET /events/active in useActiveEvent. */
export function resolveActiveEventId(): string | undefined {
  const fromEnv = import.meta.env.VITE_ACTIVE_EVENT_ID as string | undefined;
  if (fromEnv?.trim()) return fromEnv.trim();

  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get('event_id');
  if (fromQuery?.trim()) {
    localStorage.setItem('stromwart-active-event-id', fromQuery.trim());
    return fromQuery.trim();
  }

  return localStorage.getItem('stromwart-active-event-id') ?? undefined;
}

export function setActiveEventId(eventId: string) {
  localStorage.setItem('stromwart-active-event-id', eventId);
}

export function clearActiveEventId() {
  localStorage.removeItem('stromwart-active-event-id');
}
