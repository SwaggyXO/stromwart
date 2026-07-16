import { test, expect } from './fixtures';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('dashboard has no critical accessibility violations', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .disableRules(['color-contrast'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('audit page has no critical accessibility violations', async ({ page }) => {
    await page.goto('/audit');
    await page.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .disableRules(['color-contrast'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('login page has no critical accessibility violations', async ({ page }) => {
    test.info().annotations.push({ type: 'auth', description: 'unauthenticated' });
    await page.addInitScript(() => {
      (window as unknown as { __AUTH0_MOCK__: unknown }).__AUTH0_MOCK__ = {
        isAuthenticated: false,
        isLoading: false,
      };
    });
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });
});
