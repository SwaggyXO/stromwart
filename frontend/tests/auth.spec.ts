import { test, expect } from './fixtures';

test.describe('Authentication', () => {
  test.use({ authMode: 'unauthenticated' });

  test('redirects unauthenticated users to /login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading')).toContainText(/SRE Command Center|sign in|log in|welcome/i);
    await expect(page.getByRole('button', { name: /sign in with auth0/i })).toBeVisible();
  });

  test('signup page renders correctly', async ({ page }) => {
    await page.goto('/signup');
    await expect(page.getByRole('heading')).toContainText(/sign up|create|register/i);
  });
});

test.describe('Authentication (authenticated)', () => {
  test('authenticated user sees dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByText(/FIFA WC|Live Event/i).first()).toBeVisible({ timeout: 10_000 });
  });
});
