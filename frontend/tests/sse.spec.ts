import { test, expect } from './fixtures';

test.describe('SSE Real-Time Updates', () => {
  test('page attempts SSE connection', async ({ page }) => {
    const sseRequests: string[] = [];
    page.on('request', (req) => {
      // Frontend uses GET /api/v1/events/{event_id}/stream (OpenAPI LiveEventUpdate)
      if (req.url().includes('/stream') || req.url().includes('/live/stream')) {
        sseRequests.push(req.url());
      }
    });

    await page.addInitScript(() => {
      localStorage.setItem('stromwart-active-event-id', 'evt_001');
    });

    await page.goto('/');
    await expect(page.locator('[data-tour="kpi-panel"]')).toBeVisible({ timeout: 10_000 });
    await page.waitForTimeout(2000);

    expect(sseRequests.length).toBeGreaterThan(0);
    expect(sseRequests[0]).toMatch(/events\/[^/]+\/stream/);
    // Active event id may come from VITE_ACTIVE_EVENT_ID, query, or localStorage
    expect(sseRequests.some((u) => /\/events\/[^/]+\/stream/.test(u))).toBe(true);
  });
});
