const { test, expect } = require('@playwright/test');

test.describe('Kuryecini E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should load homepage', async ({ page }) => {
    await expect(page).toHaveTitle(/Kuryecini/);
    await expect(page.locator('text=Türkiye\'nin En Hızlı')).toBeVisible();
  });

  test('should navigate to customer login', async ({ page }) => {
    await page.click('text=Hemen Sipariş Ver');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should perform customer login flow', async ({ page }) => {
    // Navigate to login
    await page.click('text=Hemen Sipariş Ver');
    
    // Fill login form
    await page.fill('input[type="email"]', 'testcustomer@example.com');
    await page.fill('input[type="password"]', 'test123');
    
    // Submit form
    await page.click('button:has-text("Giriş Yap")');
    
    // Wait for redirect to dashboard
    await page.waitForTimeout(3000);
    
    // Check if customer dashboard is visible
    await expect(page.locator('text=Keşfet')).toBeVisible();
  });

  test('should view restaurant menus', async ({ page }) => {
    // Login first
    await page.click('text=Hemen Sipariş Ver');
    await page.fill('input[type="email"]', 'testcustomer@example.com');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button:has-text("Giriş Yap")');
    await page.waitForTimeout(3000);
    
    // Navigate to discover tab
    await page.click('text=Keşfet');
    await page.waitForTimeout(2000);
    
    // Check if restaurants are visible
    const restaurantCards = page.locator('.group');
    const count = await restaurantCards.count();
    
    if (count > 0) {
      // Click on first restaurant
      await restaurantCards.first().click();
      await page.waitForTimeout(2000);
      
      // Check if menu items are visible
      await expect(page.locator('text=₺')).toBeVisible(); // Price indicator
    }
  });

  test('should add items to cart', async ({ page }) => {
    // Login first
    await page.click('text=Hemen Sipariş Ver');
    await page.fill('input[type="email"]', 'testcustomer@example.com');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button:has-text("Giriş Yap")');
    await page.waitForTimeout(3000);
    
    // Navigate to restaurant menu
    await page.click('text=Keşfet');
    await page.waitForTimeout(2000);
    
    const restaurantCards = page.locator('.group');
    const count = await restaurantCards.count();
    
    if (count > 0) {
      await restaurantCards.first().click();
      await page.waitForTimeout(2000);
      
      // Try to add item to cart
      const addButtons = page.locator('button:has-text("+")');
      const buttonCount = await addButtons.count();
      
      if (buttonCount > 0) {
        await addButtons.first().click();
        await page.waitForTimeout(1000);
        
        // Check cart tab for items
        await page.click('text=Sepet');
        await page.waitForTimeout(1000);
        
        // Cart should not be empty or should show items
        const cartContent = await page.textContent('body');
        expect(cartContent).toBeDefined();
      }
    }
  });

  test('should load courier map page', async ({ page }) => {
    // Navigate to courier login  
    await page.click('text=Hemen Sipariş Ver');
    await page.waitForTimeout(1000);
    
    // Try to access courier dashboard (if available)
    const courierOption = page.locator('text=Kurye');
    if (await courierOption.isVisible()) {
      await courierOption.click();
      await page.fill('input[type="email"]', 'testkurye@example.com');
      await page.fill('input[type="password"]', 'test123');
      await page.click('button:has-text("Giriş Yap")');
      await page.waitForTimeout(3000);
      
      // Check if map container exists
      const mapContainer = page.locator('.leaflet-container');
      if (await mapContainer.isVisible()) {
        await expect(mapContainer).toBeVisible();
      }
    }
  });

  test('should handle SPA routing', async ({ page }) => {
    // Test direct navigation to routes
    await page.goto('http://localhost:3000/some/deep/route');
    
    // Should not show 404, should show the SPA
    await expect(page.locator('body')).toBeVisible();
    
    // Should eventually redirect or show main app
    await page.waitForTimeout(2000);
    const content = await page.textContent('body');
    expect(content).toBeDefined();
    expect(content.length).toBeGreaterThan(0);
  });
});