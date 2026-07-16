import { test, expect } from './fixtures';

test.describe('Agent Activity Panel', () => {
  test('renders compact agent summary when metrics available', async ({ page }) => {
    await page.route('**/api/v1/evals/summary', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          agents: [
            {
              name: 'detector',
              total_runs: 12,
              avg_latency_ms: 45.2,
              avg_score: 0.92,
              failure_rate: 0.08,
            },
            {
              name: 'diagnostician',
              total_runs: 8,
              avg_latency_ms: 120.5,
              avg_score: 0.85,
              failure_rate: 0.12,
            },
          ],
        }),
      }),
    );
    await page.goto('/');
    await expect(page.getByText('Agent System')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('detector')).toBeVisible();
    await expect(page.getByText('diagnostician')).toBeVisible();
    await expect(page.getByRole('link', { name: /view details/i })).toBeVisible();
  });

  test('shows empty state when no activity', async ({ page }) => {
    await page.route('**/api/v1/evals/summary', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ agents: [] }),
      }),
    );
    await page.goto('/');
    await expect(page.getByText(/no agent activity/i)).toBeVisible({ timeout: 10_000 });
  });

  test('displays success rate percentage', async ({ page }) => {
    await page.route('**/api/v1/evals/summary', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          agents: [
            {
              name: 'detector',
              total_runs: 10,
              avg_latency_ms: 50,
              avg_score: 0.9,
              failure_rate: 0.1,
            },
          ],
        }),
      }),
    );
    await page.goto('/');
    await expect(page.getByText('90%')).toBeVisible({ timeout: 10_000 });
  });
});
