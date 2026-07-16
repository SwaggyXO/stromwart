import { test, expect } from '@playwright/test';

test.describe('Onboarding Tour', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      (window as unknown as { __AUTH0_MOCK__: unknown }).__AUTH0_MOCK__ = {
        isAuthenticated: true,
        isLoading: false,
        user: { name: 'Test User', email: 'test@stromwart.dev' },
      };
      localStorage.removeItem('stromwart-tour-completed');
      localStorage.setItem('stromwart-active-event-id', 'evt_001');
    });

    await page.route('**/api/v1/**', async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;

      if (path.includes('/events/active')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'evt_001',
            name: 'Test Event',
            starts_at: '2026-07-15T20:00:00Z',
            content_type: 'sports',
            ends_at: null,
          }),
        });
      }
      if (path.includes('/stream')) {
        return route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: 'data: {"event_id":"evt_001","active_sessions":10}\n\n',
        });
      }
      if (path.includes('/evals/summary')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ agents: [] }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '[]',
      });
    });
  });

  test('tour auto-starts for new user', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Real-Time KPIs')).toBeVisible({ timeout: 5000 });
  });

  test('tour progresses through steps', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Real-Time KPIs')).toBeVisible({ timeout: 5000 });

    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByText('QoE Forecast')).toBeVisible();

    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByText('3/6')).toBeVisible();
    await expect(page.getByText('Alert Feed').last()).toBeVisible();
  });

  test('skip button closes tour and persists', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Real-Time KPIs')).toBeVisible({ timeout: 5000 });

    await page.getByRole('button', { name: /skip/i }).click();
    await expect(page.getByText('Real-Time KPIs')).not.toBeVisible();

    await page.reload();
    await expect(page.getByText('Real-Time KPIs')).not.toBeVisible({ timeout: 3000 });
  });

  test('tour does not show if already completed', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('stromwart-tour-completed', 'true');
    });
    await page.goto('/');
    await expect(page.getByText('Real-Time KPIs')).not.toBeVisible({ timeout: 3000 });
  });
});
