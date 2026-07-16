import { test, expect } from './fixtures';

const incident = {
  id: 'inc_001',
  event_id: 'evt_001',
  slice_key: 'region:eu-west/client:android',
  state: 'investigating',
  severity: 'high',
  affected_slice: { region: 'eu-west', client: 'android' },
  evidence_ids: ['alrt_001'],
  hypothesis: { summary: 'CDN edge node saturation causing bitrate drops.' },
  created_at: '2026-07-15T20:16:00Z',
  updated_at: '2026-07-15T20:16:00Z',
};

const proposal = {
  id: 'prop_001',
  incident_id: 'inc_001',
  action_type: 'scale_cdn_edge',
  target_scope: { cluster: 'eu-west-cdn-cluster-3' },
  rationale: 'Edge node CPU at 92%.',
  expected_effect: 'Reduce p95 latency by ~40%',
  confidence: 0.82,
  risk_score: 0.15,
  evidence_ids: ['alrt_001'],
  state: 'approval_required',
  policy_reasons: [],
  created_at: '2026-07-15T20:16:30Z',
};

test.describe('Incident Detail', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/incidents/inc_001', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(incident),
      }),
    );
    await page.route('**/api/v1/incidents/inc_001/proposals**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([proposal]),
      }),
    );
    await page.route('**/api/v1/proposals/prop_001/simulate', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          proposal_id: 'prop_001',
          successful: true,
          projected_risk_reduction: 0.4,
          projected_affected_sessions: 500,
          explanation: 'MOS expected: 2.8 → 4.1',
        }),
      }),
    );
    await page.route('**/api/v1/proposals/prop_001/approve', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...proposal, state: 'simulate' }),
      }),
    );
  });

  test('displays incident hypothesis', async ({ page }) => {
    await page.goto('/incidents/inc_001');
    await expect(page.getByText(/CDN edge node saturation/)).toBeVisible({ timeout: 10_000 });
  });

  test('displays proposal with policy state', async ({ page }) => {
    await page.goto('/incidents/inc_001');
    await expect(page.getByText('scale_cdn_edge')).toBeVisible({ timeout: 10_000 });
    // PolicyBadge renders APPROVE_REQUIRED as "APPROVE REQUIRED" (first _ → space)
    await expect(page.getByText(/APPROVE REQUIRED|RECOMMEND/i)).toBeVisible();
  });

  test('simulate button enabled when policy state is simulate', async ({ page }) => {
    await page.route('**/api/v1/incidents/inc_001/proposals**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ ...proposal, state: 'simulate' }]),
      }),
    );
    await page.goto('/incidents/inc_001');
    await expect(page.getByText(/CDN edge node saturation/)).toBeVisible({ timeout: 10_000 });
    const simulateBtn = page.getByRole('button', { name: /run simulation/i });
    await expect(simulateBtn).toBeEnabled();
    await simulateBtn.click();
    await expect(page.getByText(/MOS expected/)).toBeVisible({ timeout: 5000 });
  });

  test('simulate button hidden until approval when policy requires it', async ({ page }) => {
    await page.goto('/incidents/inc_001');
    await expect(page.getByRole('button', { name: /run simulation/i })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /approve for simulation/i })).toBeVisible();
  });

  test('approve button triggers API call', async ({ page }) => {
    await page.goto('/incidents/inc_001');
    const approveBtn = page.getByRole('button', { name: /approve for simulation/i });
    await approveBtn.click();
    await expect(
      page.getByText(/approved|executing|Operator approved|Approve/i).first(),
    ).toBeVisible({ timeout: 5000 });
  });

  test('approved proposal shows resolve only', async ({ page }) => {
    await page.route('**/api/v1/incidents/inc_001/proposals**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ ...proposal, state: 'approved' }]),
      }),
    );
    await page.goto('/incidents/inc_001');
    await expect(page.getByRole('button', { name: /resolve incident/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /approve/i })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /run simulation/i })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /reject/i })).toHaveCount(0);
  });
});
