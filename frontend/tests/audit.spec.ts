import { test, expect } from './fixtures';

test.describe('Audit Log', () => {
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
    await page.route('**/api/v1/audit**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            audit_id: 'aud_001',
            correlation_id: 'corr_abc',
            actor_type: 'llm_analyst',
            artifact_type: 'incident',
            artifact_id: 'inc_001',
            payload: {
              description: 'LLM Analyst created incident from alert correlation.',
            },
            created_at: '2026-07-15T20:16:05Z',
          },
          {
            audit_id: 'aud_002',
            correlation_id: 'corr_abc',
            actor_type: 'policy_verifier',
            artifact_type: 'proposal',
            artifact_id: 'prop_001',
            payload: {
              description: 'Policy verifier advanced proposal to RECOMMEND.',
            },
            created_at: '2026-07-15T20:16:10Z',
          },
        ]),
      }),
    );
  });

  test('renders audit entries', async ({ page }) => {
    await page.goto('/audit');
    await expect(page.getByText('LLM Analyst created incident')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Policy verifier advanced proposal')).toBeVisible();
  });

  test('shows correlation IDs', async ({ page }) => {
    await page.goto('/audit');
    // Correlation IDs may only appear in payload; artifact IDs are always shown
    await expect(page.getByText('inc_001').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('prop_001').first()).toBeVisible();
  });

  test('shows actor type badges', async ({ page }) => {
    await page.goto('/audit');
    await expect(page.getByText('llm analyst', { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('policy verifier', { exact: true })).toBeVisible();
  });

  test('shows empty state when no live demo', async ({ page }) => {
    await page.route('**/api/v1/simulation/status**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'idle',
          scenario_id: null,
          progress: 0,
          current_phase: '',
          event_id: null,
        }),
      }),
    );
    await page.goto('/audit');
    await expect(page.getByText(/start a demo to see audit events/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});
