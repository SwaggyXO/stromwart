import { test, expect } from './fixtures';

test.describe('Color Mode', () => {
  test('defaults to dark mode', async ({ page }) => {
    await page.goto('/');
    const html = page.locator('html');
    await expect(html).not.toHaveClass(/light/);
  });

  test('toggle switches to light mode', async ({ page }) => {
    await page.goto('/');
    const toggle = page.getByRole('button', { name: /switch to light mode/i });
    await toggle.click();
    const html = page.locator('html');
    await expect(html).toHaveClass(/light/);
  });

  test('persists across reload', async ({ page }) => {
    await page.goto('/');
    const toggle = page.getByRole('button', { name: /switch to light mode/i });
    await toggle.click();
    await page.reload();
    const html = page.locator('html');
    await expect(html).toHaveClass(/light/);
  });

  test('toggle back to dark mode', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /switch to light mode/i }).click();
    await page.getByRole('button', { name: /switch to dark mode/i }).click();
    const html = page.locator('html');
    await expect(html).not.toHaveClass(/light/);
  });
});
