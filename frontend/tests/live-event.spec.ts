import { test, expect } from './fixtures';
import { mockPayloads } from './mocks/handlers';

test.describe('Live Event Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/simulation/status**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'running',
          scenario_id: 'cdn_regional_outage',
          progress: 0.4,
          current_phase: 'Degradation',
          event_id: 'evt_001',
        }),
      }),
    );
    await page.route('**/api/v1/simulation/scenarios**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'cdn_regional_outage',
            name: 'FIFA WC — GER vs JPN',
            description: 'CDN outage demo',
            duration_minutes: 10,
            category: 'sports',
            sessions_peak: 50000,
            phase_count: 4,
          },
        ]),
      }),
    );
    await page.route('**/api/v1/events/active', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockPayloads.event,
          id: 'evt_001',
          name: 'FIFA WC — GER vs JPN',
        }),
      }),
    );
  });

  test('renders event name', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('FIFA WC — GER vs JPN')).toBeVisible({ timeout: 10_000 });
  });

  test('renders KPI cards', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('MOS Score')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('4.21')).toBeVisible();
    await expect(page.getByText('Buffer Ratio')).toBeVisible();
  });

  test('KPI panel has tour attribute', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('[data-tour="kpi-panel"]')).toBeVisible({ timeout: 10_000 });
  });

  test('forecast chart section exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('[data-tour="forecast-chart"]')).toBeVisible({ timeout: 10_000 });
  });

  test('alert feed section exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('[data-tour="alert-feed"]')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/alert feed/i).first()).toBeVisible();
  });
});
