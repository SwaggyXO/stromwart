import { test, expect } from './fixtures';

async function selectProvider(page: import('@playwright/test').Page, label: string) {
  await page.getByRole('button', { name: 'Provider' }).click();
  await page.getByRole('option', { name: label }).click();
}

test.describe('Settings Page', () => {
  test('loads settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByText(/settings/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test('shows provider list', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Provider' }).click();
    await expect(page.getByRole('option', { name: /Disabled/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Groq/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Ollama/i })).toBeVisible();
  });

  test('switches between tabs', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: /^Thresholds$/i }).click();
    await expect(page.getByText(/MOS threshold/i)).toBeVisible();
    await page.getByRole('button', { name: /^Evals$/i }).click();
    await expect(page.getByText(/detector/i).first()).toBeVisible();
  });

  test('test connection button exists', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('button', { name: /test connection/i })).toBeVisible({
      timeout: 10_000,
    });
  });

  test('threshold values display', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: /^Thresholds$/i }).click();
    await expect(page.getByText('3.5')).toBeVisible();
  });

  test('shows save bar after editing evals', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: /^Evals$/i }).click();
    await page
      .locator('div')
      .filter({ hasText: /^LLM judge$/ })
      .locator('input[type="checkbox"]')
      .click();
    await expect(page.getByText('Unsaved changes')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible();
  });

  test('demo scenario is locked active on data sources tab', async ({ page }) => {
    await page.goto('/settings');
    await page.getByRole('button', { name: /^Data Sources$/i }).click();
    await expect(page.getByText(/only available data source during phase 1/i)).toBeVisible();
    await expect(page.getByText('Active', { exact: true })).toBeVisible();
    await expect(page.getByText('Coming soon')).toBeVisible();
  });

  test('test connection failure shows toast not raw JSON', async ({ page }) => {
    await page.route('**/api/v1/settings/providers/test**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          message: 'Connection timed out (10s)',
          latency_ms: 10000,
        }),
      }),
    );
    await page.goto('/settings');
    await selectProvider(page, 'Groq (free)');
    await page.getByRole('button', { name: /test connection/i }).click();
    await expect(page.getByText(/connection timed out/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/^OK:/)).toHaveCount(0);
  });
});
