/**
 * Live backend contract E2E — exercises the exact paths the frontend client uses.
 * Set EVENT_ID env (defaults to VITE_ACTIVE_EVENT_ID / event 1).
 * Does not use page.route mocks; hits http://127.0.0.1:8000 directly.
 */
import { test, expect, type APIRequestContext } from '@playwright/test';

const BACKEND = process.env.STROMWART_API_BASE ?? 'http://127.0.0.1:8000';
const EVENT_ID =
  process.env.EVENT_ID ??
  process.env.VITE_ACTIVE_EVENT_ID ??
  'a6593b6e-65c9-43c7-ade7-97ff25cb0a03';

async function getJson(request: APIRequestContext, path: string) {
  const res = await request.get(`${BACKEND}${path}`);
  const text = await res.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  return { status: res.status(), body, headers: res.headers() };
}

test.describe(`Live API contract — event ${EVENT_ID}`, () => {
  test('GET /v1/events/active returns EventRead', async ({ request }) => {
    const { status, body } = await getJson(request, '/v1/events/active');
    expect(status).toBe(200);
    expect(body).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      content_type: expect.any(String),
      starts_at: expect.any(String),
    });
  });

  test('GET /v1/events/{id}/sessions', async ({ request }) => {
    const { status, body } = await getJson(request, `/v1/events/${EVENT_ID}/sessions?limit=50`);
    expect(status).toBe(200);
    expect(Array.isArray(body)).toBe(true);
  });

  test('GET /v1/events/{id}/kpis', async ({ request }) => {
    const { status, body } = await getJson(request, `/v1/events/${EVENT_ID}/kpis`);
    expect(status).toBe(200);
    expect(Array.isArray(body)).toBe(true);
    if (Array.isArray(body) && body.length > 0) {
      expect(body[0]).toHaveProperty('label');
      expect(body[0]).toHaveProperty('value');
      expect(body[0]).toHaveProperty('trend');
      expect(body[0]).toHaveProperty('status');
    }
  });

  test('GET /v1/events/{id}/alerts', async ({ request }) => {
    const { status, body } = await getJson(request, `/v1/events/${EVENT_ID}/alerts?limit=50`);
    expect(status).toBe(200);
    expect(Array.isArray(body)).toBe(true);
  });

  test('GET /v1/events/{id}/incidents', async ({ request }) => {
    const { status, body } = await getJson(
      request,
      `/v1/events/${EVENT_ID}/incidents?active_only=true&limit=50`,
    );
    expect(status).toBe(200);
    expect(Array.isArray(body)).toBe(true);
  });

  test('GET /v1/modeling/forecast?event_id= (frontend ForecastChart)', async ({ request }) => {
    const { status, body } = await getJson(
      request,
      `/v1/modeling/forecast?event_id=${EVENT_ID}&metric_name=stall_risk&horizon_minutes=10&step_seconds=60`,
    );
    expect(status).toBe(200);
    expect(Array.isArray(body)).toBe(true);
    if (Array.isArray(body) && body.length > 0) {
      expect(body[0]).toEqual(
        expect.objectContaining({
          timestamp: expect.any(String),
          p10: expect.any(Number),
          p50: expect.any(Number),
          p90: expect.any(Number),
        }),
      );
    }
  });

  test('GET /v1/events/{id}/stream is event-stream', async () => {
    // APIRequestContext waits for body end — SSE never ends. Probe headers only.
    const result = await new Promise<{ status: number; contentType: string }>((resolve, reject) => {
      const url = new URL(`${BACKEND}/v1/events/${EVENT_ID}/stream`);
      import('node:http').then((http) => {
        const req = http.request(
          {
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: 'GET',
            headers: { Accept: 'text/event-stream' },
            timeout: 5000,
          },
          (res) => {
            const contentType = String(res.headers['content-type'] ?? '');
            const status = res.statusCode ?? 0;
            res.destroy();
            resolve({ status, contentType });
          },
        );
        req.on('error', reject);
        req.on('timeout', () => {
          req.destroy();
          reject(new Error('SSE header probe timed out'));
        });
        req.end();
      }, reject);
    });
    expect(result.status).toBe(200);
    expect(result.contentType).toMatch(/text\/event-stream/);
  });

  test('browser Live Event page renders against live backend', async ({ page }) => {
    await page.addInitScript((eventId) => {
      (window as unknown as { __AUTH0_MOCK__: unknown }).__AUTH0_MOCK__ = {
        isAuthenticated: true,
        isLoading: false,
        user: { name: 'E2E', email: 'e2e@stromwart.dev', sub: 'auth0|e2e' },
      };
      localStorage.setItem('stromwart-tour-completed', 'true');
      localStorage.setItem('stromwart-active-event-id', eventId);
    }, EVENT_ID);

    // Do NOT mock API — proxy to real backend via Vite
    await page.goto(`/?event_id=${EVENT_ID}`);
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.locator('[data-tour="kpi-panel"]')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('[data-tour="forecast-chart"]')).toBeVisible();
    await expect(page.locator('[data-tour="alert-feed"]')).toBeVisible();
  });
});
