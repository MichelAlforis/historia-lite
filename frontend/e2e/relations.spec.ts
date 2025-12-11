/**
 * E2E Tests for Phase 16: Relations Diplomatiques
 *
 * Prerequisites:
 * 1. Install Playwright: npm install -D @playwright/test
 * 2. Install browsers: npx playwright install
 * 3. Add to package.json scripts: "test:e2e": "playwright test"
 *
 * Run: npm run test:e2e
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3001';

test.describe('Relations Diplomatiques - Phase 16', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the game page
    await page.goto(`${BASE_URL}/pax`);

    // Wait for country selector to load, then select USA
    await page.waitForSelector('text=Selectionnez votre nation', { timeout: 10000 });

    // Click on USA to select it
    const usaButton = page.locator('button:has-text("Etats-Unis")');
    if (await usaButton.isVisible()) {
      await usaButton.click();
    }

    // Wait for game to load
    await page.waitForSelector('text=DEFCON', { timeout: 10000 });
  });

  test('should open RelationsPanel when clicking Relations button', async ({ page }) => {
    // Click the Relations button (Users icon)
    await page.click('button[title="Relations diplomatiques"]');

    // Verify panel opened
    await expect(page.locator('text=Relations Diplomatiques')).toBeVisible();

    // Verify stats summary is visible
    await expect(page.locator('text=Guerres')).toBeVisible();
    await expect(page.locator('text=Allies')).toBeVisible();
    await expect(page.locator('text=Rivaux')).toBeVisible();

    // Close the panel
    await page.click('button:has-text("Fermer")');

    // Verify panel closed
    await expect(page.locator('text=Relations Diplomatiques')).not.toBeVisible();
  });

  test('should open RelationMatrix when clicking Matrix button', async ({ page }) => {
    // Click the Matrix button (Grid icon)
    await page.click('button[title="Matrice des relations"]');

    // Verify matrix opened
    await expect(page.locator('text=Matrice des Relations')).toBeVisible();

    // Verify filter buttons are visible
    await expect(page.locator('button:has-text("Tous")')).toBeVisible();
    await expect(page.locator('button:has-text("Tier 1")')).toBeVisible();
    await expect(page.locator('button:has-text("Tier 2")')).toBeVisible();
    await expect(page.locator('button:has-text("Tier 3")')).toBeVisible();

    // Verify legend is visible
    await expect(page.locator('text=Guerre')).toBeVisible();

    // Close the matrix
    await page.click('button:has-text("Fermer")');

    // Verify matrix closed
    await expect(page.locator('text=Matrice des Relations')).not.toBeVisible();
  });

  test('should filter matrix by tier', async ({ page }) => {
    // Open matrix
    await page.click('button[title="Matrice des relations"]');
    await expect(page.locator('text=Matrice des Relations')).toBeVisible();

    // Click Tier 1 filter
    await page.click('button:has-text("Tier 1")');

    // Should show only 3 countries (USA, CHN, RUS)
    await expect(page.locator('text=3 pays')).toBeVisible();

    // Click Tier 2 filter
    await page.click('button:has-text("Tier 2")');

    // Should show more countries
    const countText = await page.locator('text=/\\d+ pays/').textContent();
    expect(countText).not.toBe('3 pays');

    // Click Tous to reset
    await page.click('button:has-text("Tous")');
  });

  test('should toggle map view mode between power and relations', async ({ page }) => {
    // Find the map view toggle button
    const mapToggle = page.locator('button[title="Vue relations"]');

    // Initially should show "Vue relations" (meaning current mode is power)
    await expect(mapToggle).toBeVisible();

    // Click to switch to relations mode
    await mapToggle.click();

    // Button should now show "Vue puissance" and be highlighted
    await expect(page.locator('button[title="Vue puissance"]')).toBeVisible();
    await expect(page.locator('button[title="Vue puissance"]')).toHaveClass(/bg-violet-500/);

    // Click again to switch back to power mode
    await page.locator('button[title="Vue puissance"]').click();

    // Should be back to relations view option
    await expect(page.locator('button[title="Vue relations"]')).toBeVisible();
  });

  test('should show country relations in RelationsPanel', async ({ page }) => {
    // Open Relations panel
    await page.click('button[title="Relations diplomatiques"]');

    // Should show categorized relations
    // Look for at least one of the category headers
    const hasWars = await page.locator('text=En guerre').isVisible();
    const hasAllies = await page.locator('text=Allies').isVisible();
    const hasRivals = await page.locator('text=Rivaux').isVisible();
    const hasOthers = await page.locator('text=Autres nations').isVisible();

    // At least one category should be visible
    expect(hasWars || hasAllies || hasRivals || hasOthers).toBe(true);

    // Should show relation bars
    await expect(page.locator('.bg-emerald-400, .bg-red-400').first()).toBeVisible();
  });

  test('should select country from matrix and show on map', async ({ page }) => {
    // Open matrix
    await page.click('button[title="Matrice des relations"]');
    await expect(page.locator('text=Matrice des Relations')).toBeVisible();

    // Click on a country row header (e.g., China)
    const chinaRow = page.locator('text=Chine').first();
    if (await chinaRow.isVisible()) {
      await chinaRow.click();
    }

    // Matrix should close
    await expect(page.locator('text=Matrice des Relations')).not.toBeVisible();

    // Country info panel should appear on the map
    // (This depends on the country being in the data)
  });
});

test.describe('Relations on Map', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/pax`);
    await page.waitForSelector('text=Selectionnez votre nation', { timeout: 10000 });

    const usaButton = page.locator('button:has-text("Etats-Unis")');
    if (await usaButton.isVisible()) {
      await usaButton.click();
    }

    await page.waitForSelector('text=DEFCON', { timeout: 10000 });
  });

  test('should color map differently in relations mode', async ({ page }) => {
    // Wait for map to load
    await page.waitForSelector('.maplibregl-canvas', { timeout: 10000 });

    // Switch to relations mode
    await page.click('button[title="Vue relations"]');

    // Map should now show relations-based colors
    // The player country (USA) should be gold colored
    // This is a visual test - in a real scenario we'd check canvas pixels or data attributes
    await expect(page.locator('button[title="Vue puissance"]')).toHaveClass(/bg-violet-500/);
  });
});
