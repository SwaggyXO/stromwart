/**
 * Regenerates PNGs for the GitHub Pages one-pager under ../landing/assets/.
 *
 * Run (from frontend/):
 *   $env:CAPTURE_DEMO='1'; npx playwright test tests/capture-demo.spec.ts --project=chromium
 *
 * Skipped unless CAPTURE_DEMO=1 so normal CI / local suites stay clean.
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, expect } from './fixtures';
import { mockPayloads } from './mocks/handlers';

const CAPTURE = process.env.CAPTURE_DEMO === '1';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ASSETS = path.resolve(__dirname, '../../landing/assets');

const agentSummary = {
  agents: [
    {
      name: 'detector',
      total_runs: 14,
      avg_latency_ms: 42,
      avg_score: 0.91,
      failure_rate: 0.07,
    },
    {
      name: 'diagnostician',
      total_runs: 11,
      avg_latency_ms: 180,
      avg_score: 0.86,
      failure_rate: 0.09,
    },
    {
      name: 'mitigator',
      total_runs: 9,
      avg_latency_ms: 95,
      avg_score: 0.88,
      failure_rate: 0.11,
    },
    {
      name: 'verifier',
      total_runs: 8,
      avg_latency_ms: 70,
      avg_score: 0.93,
      failure_rate: 0.05,
    },
  ],
};

test.describe('Demo screenshot capture', () => {
  test.skip(!CAPTURE, 'Set CAPTURE_DEMO=1 to regenerate landing/assets screenshots');

  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.route('**/api/v1/evals/summary', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(agentSummary),
      }),
    );
    await page.route('**/api/v1/evals/traces**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      }),
    );
    await page.route('**/api/v1/evals/clusters**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      }),
    );
    await page.route('**/api/v1/events/*/session-stats**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          active_sessions: 142500,
          total_sessions: 318000,
        }),
      }),
    );
    await page.route('**/api/v1/agent-runs**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      }),
    );
    await page.route('**/api/v1/simulation/scenarios**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'fifa_wc_ger_jpn',
            name: 'FIFA WC 2026 — Germany vs Japan',
            description: 'CDN regional outage during peak',
            duration_minutes: 12,
            category: 'sports',
            sessions_peak: 500000,
            phase_count: 4,
          },
        ]),
      }),
    );
  });

  test('capture walkthrough screenshots', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/FIFA WC/i).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('[data-tour="kpi-panel"]')).toBeVisible();
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(ASSETS, '01-live-event.png'),
      fullPage: false,
    });

    await page.locator('[data-tour="forecast-chart"]').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await page.screenshot({
      path: path.join(ASSETS, '02-forecast-alerts.png'),
      fullPage: false,
    });

    await page.locator('text=Agent System').scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    await page.screenshot({
      path: path.join(ASSETS, '03-agent-system.png'),
      fullPage: false,
    });

    await page.goto('/incidents/inc_001');
    await expect(page.getByText(/CDN edge node saturation/i)).toBeVisible({ timeout: 15_000 });
    await page.waitForTimeout(600);
    await page.screenshot({
      path: path.join(ASSETS, '04-incident-detail.png'),
      fullPage: false,
    });

    await page.goto('/agents');
    await expect(page.getByText(/Detector/i).first()).toBeVisible({ timeout: 15_000 });
    await page.waitForTimeout(600);
    await page.screenshot({
      path: path.join(ASSETS, '05-agents.png'),
      fullPage: false,
    });

    await page.goto('/settings');
    await expect(page.getByText(/settings/i).first()).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: /^Data Sources$/i }).click();
    await expect(page.getByText(/Phase 1/i)).toBeVisible();
    await page.waitForTimeout(400);
    await page.screenshot({
      path: path.join(ASSETS, '06-settings.png'),
      fullPage: false,
    });
  });
});
