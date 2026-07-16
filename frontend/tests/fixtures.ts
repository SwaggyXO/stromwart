import { test as base, expect } from '@playwright/test';
import { mockPayloads } from './mocks/handlers';

type AuthMode = 'authenticated' | 'unauthenticated';

export const test = base.extend<{ authMode: AuthMode }>({
  authMode: ['authenticated', { option: true }],

  page: async ({ page, authMode }, use) => {
    await page.addInitScript(
      ({ mode, eventId }) => {
        (window as unknown as { __AUTH0_MOCK__: unknown }).__AUTH0_MOCK__ = {
          isAuthenticated: mode === 'authenticated',
          isLoading: false,
          user: { name: 'Test User', email: 'test@stromwart.dev', sub: 'auth0|test' },
        };
        if (mode === 'authenticated') {
          localStorage.setItem('stromwart-tour-completed', 'true');
        }
        if (eventId) {
          localStorage.setItem('stromwart-active-event-id', eventId);
        }
      },
      { mode: authMode, eventId: mockPayloads.event.id },
    );

    await page.route('**/api/v1/**', async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname.replace(/^\/api\/v1/, '') || '/';
      const method = route.request().method().toUpperCase();

      const json = (body: unknown, status = 200) =>
        route.fulfill({
          status,
          contentType: 'application/json',
          body: JSON.stringify(body),
        });

      if (method === 'GET' && path === '/events/active') return json(mockPayloads.event);
      if (method === 'GET' && /\/events\/[^/]+\/kpis$/.test(path)) return json(mockPayloads.kpis);
      if (method === 'GET' && /\/events\/[^/]+\/alerts/.test(path)) return json(mockPayloads.alerts);
      if (method === 'GET' && /\/events\/[^/]+\/incidents/.test(path))
        return json(mockPayloads.incidents);
      if (method === 'GET' && /\/events\/[^/]+\/sessions/.test(path))
        return json(mockPayloads.sessions);
      if (method === 'GET' && path.startsWith('/modeling/forecast'))
        return json(mockPayloads.forecast);
      if (method === 'GET' && /\/incidents\/[^/]+\/proposals/.test(path))
        return json(mockPayloads.proposals);
      if (method === 'GET' && /\/incidents\/[^/]+$/.test(path))
        return json(mockPayloads.incidents[0]);
      if (method === 'GET' && path.startsWith('/audit')) return json(mockPayloads.audit);
      if (method === 'GET' && path === '/settings') return json(mockPayloads.settings);
      if (method === 'PUT' && path === '/settings') return json(mockPayloads.settings);
      if (method === 'GET' && path === '/settings/providers') return json(mockPayloads.providers);
      if (method === 'POST' && path === '/settings/providers/test') {
        return json({
          success: true,
          message: 'Connected',
          latency_ms: 50,
        });
      }
      if (method === 'GET' && path === '/simulation/status') {
        return json({
          status: 'idle',
          scenario_id: null,
          progress: 0,
          current_phase: '',
          event_id: null,
        });
      }
      if (method === 'GET' && path === '/evals/summary') return json({ agents: [] });
      if (method === 'POST' && /\/proposals\/[^/]+\/simulate$/.test(path)) {
        return json({
          proposal_id: 'prop_001',
          successful: true,
          projected_risk_reduction: 0.4,
          projected_affected_sessions: 1000,
          explanation: 'MOS expected to improve from 2.8 to 4.1',
        });
      }
      if (method === 'POST' && /\/proposals\/[^/]+\/approve$/.test(path)) {
        return json({ ...mockPayloads.proposals[0], state: 'approval_required' });
      }
      if (method === 'POST' && /\/proposals\/[^/]+\/reject$/.test(path)) {
        return json(mockPayloads.proposals[0]);
      }
      if (method === 'POST' && /\/alerts\/[^/]+\/acknowledge$/.test(path)) {
        return json({ ok: true });
      }

      // SSE stream — hang open as event-stream
      if (method === 'GET' && /\/events\/[^/]+\/stream$/.test(path)) {
        return route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: 'data: {"event_id":"evt_test_001","active_sessions":100}\n\n',
        });
      }

      return route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: `Unmocked ${method} ${path}` }),
      });
    });

    await use(page);
  },
});

export { expect };
