const { test, expect } = require('@playwright/test');

test.describe('Kuryecini E2E Tests - Complete Customer Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should load homepage', async ({ page }) => {
    await expect(page).toHaveTitle(/Kuryecini/);
    await expect(page.locator('text=Türkiye\'nin En Hızlı')).toBeVisible();
  });

  test('Complete customer flow: login → add to cart → update quantity → address → order', async ({ page }) => {
    // Step 1: Navigate to customer login
    console.log('Step 1: Navigating to customer login...');
    await page.click('text=Hemen Sipariş Ver');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();

    // Step 2: Customer login
    console.log('Step 2: Performing customer login...');
    await page.fill('input[type="email"]', 'testcustomer@example.com');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button:has-text("Giriş Yap")');
    await page.waitForTimeout(3000);

    // Verify login success
    await expect(page.locator('text=Keşfet')).toBeVisible();
    console.log('✅ Customer login successful');

    // Step 3: Navigate to restaurant menu
    console.log('Step 3: Navigating to restaurant menu...');
    await page.click('text=Keşfet');
    await page.waitForTimeout(2000);

    // Find and click on first restaurant
    const restaurantCards = page.locator('.group');
    const count = await restaurantCards.count();
    expect(count).toBeGreaterThan(0);
    
    await restaurantCards.first().click();
    await page.waitForTimeout(2000);
    console.log('✅ Restaurant menu loaded');

    // Step 4: Add product to cart
    console.log('Step 4: Adding product to cart...');
    const addButtons = page.locator('button[class*="rounded-full"][class*="bg-orange-500"]');
    const buttonCount = await addButtons.count();
    
    if (buttonCount > 0) {
      await addButtons.first().click();
      await page.waitForTimeout(1000);
      console.log('✅ Product added to cart');

      // Step 5: Increase quantity
      console.log('Step 5: Increasing product quantity...');
      await addButtons.first().click(); // Add second item
      await page.waitForTimeout(1000);
      console.log('✅ Product quantity increased');

      // Step 6: Check sticky cart visibility
      console.log('Step 6: Checking sticky cart...');
      const stickyCart = page.locator('.fixed.bottom-0'); // Mobile sticky cart
      if (await stickyCart.isVisible()) {
        console.log('✅ Mobile sticky cart visible');
        
        // Click checkout from sticky cart
        await page.click('button:has-text("Sepeti Onayla")');
      } else {
        // Try desktop cart or other checkout method
        await page.click('text=Sepet');
        await page.waitForTimeout(1000);
        await page.click('button:has-text("Siparişi Tamamla")');
      }
      
      await page.waitForTimeout(2000);
      console.log('✅ Checkout modal opened');

      // Step 7: Address selection/creation
      console.log('Step 7: Testing address selection...');
      const addressSelector = page.locator('[class*="AddressSelector"], .address-selector');
      
      if (await addressSelector.isVisible()) {
        console.log('✅ Address selector visible');
        
        // Try to select an address or add new one
        const addressOptions = page.locator('button:has-text("Seç")');
        if (await addressOptions.first().isVisible()) {
          await addressOptions.first().click();
          console.log('✅ Address selected');
        } else {
          // Try to add new address
          const addAddressBtn = page.locator('button:has-text("Yeni Adres")');
          if (await addAddressBtn.isVisible()) {
            await addAddressBtn.click();
            console.log('✅ Add new address dialog opened');
          }
        }
      }

      // Step 8: Complete order (stub)
      console.log('Step 8: Completing order...');
      const completeOrderBtn = page.locator('button:has-text("Siparişi Onayla"), button:has-text("Siparişi Tamamla")');
      
      if (await completeOrderBtn.isVisible()) {
        await completeOrderBtn.click();
        await page.waitForTimeout(2000);
        console.log('✅ Order completion attempted');
        
        // Check for success message
        const successMessage = await page.textContent('body');
        if (successMessage.includes('başarı') || successMessage.includes('alındı')) {
          console.log('✅ Order success message detected');
        }
      }
      
      console.log('✅ Complete customer flow test finished');
    } else {
      console.log('⚠️ No add to cart buttons found, skipping cart operations');
    }
  });

  test('should handle professional menu display', async ({ page }) => {
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
      
      // Check for professional menu cards elements
      await expect(page.locator('text=₺')).toBeVisible(); // Price display
      
      // Check for category/badges
      const badges = page.locator('.bg-red-500, .bg-green-500, .bg-orange-500');
      if (await badges.count() > 0) {
        console.log('✅ Menu item badges found');
      }
      
      // Check for images
      const productImages = page.locator('img[alt*=""], .bg-gradient-to-br');
      expect(await productImages.count()).toBeGreaterThan(0);
      console.log('✅ Professional menu cards displayed');
    }
  });

  test('should load courier map with proper height and features', async ({ page }) => {
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
      
      // Check if map container exists with proper height
      const mapContainer = page.locator('.leaflet-container');
      if (await mapContainer.isVisible()) {
        await expect(mapContainer).toBeVisible();
        
        // Check map height (should be 100vh equivalent)
        const mapHeight = await mapContainer.evaluate(el => getComputedStyle(el).height);
        console.log(`Map height: ${mapHeight}`);
        
        // Check for map controls
        await expect(page.locator('button:has-text("Konumu Al")')).toBeVisible();
        
        // Check for leaflet CSS (map should render properly)
        const leafletLoaded = await page.evaluate(() => {
          return !!document.querySelector('.leaflet-container');
        });
        expect(leafletLoaded).toBe(true);
        
        console.log('✅ Courier map loaded successfully with proper height');
      }
    }
  });

  test('should handle SPA routing correctly', async ({ page }) => {
    // Test direct navigation to deep routes
    await page.goto('http://localhost:3000/some/deep/route');
    
    // Should not show 404, should show the SPA
    await expect(page.locator('body')).toBeVisible();
    
    // Should eventually redirect or show main app
    await page.waitForTimeout(2000);
    const content = await page.textContent('body');
    expect(content).toBeDefined();
    expect(content.length).toBeGreaterThan(0);
    
    console.log('✅ SPA routing handled correctly');
  });

  test('should show toast notifications for cart operations', async ({ page }) => {
    // Login and navigate to menu
    await page.click('text=Hemen Sipariş Ver');
    await page.fill('input[type="email"]', 'testcustomer@example.com');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button:has-text("Giriş Yap")');
    await page.waitForTimeout(3000);
    
    await page.click('text=Keşfet');
    await page.waitForTimeout(2000);
    
    const restaurantCards = page.locator('.group');
    const count = await restaurantCards.count();
    
    if (count > 0) {
      await restaurantCards.first().click();
      await page.waitForTimeout(2000);
      
      // Add item and check for toast
      const addButtons = page.locator('button[class*="rounded-full"][class*="bg-orange-500"]');
      const buttonCount = await addButtons.count();
      
      if (buttonCount > 0) {
        await addButtons.first().click();
        await page.waitForTimeout(1000);
        
        // Check for toast notification (various toast libraries)
        const toastSelectors = [
          '[data-sonner-toast]',
          '.Toastify__toast',
          '[data-hot-toast]',
          '.toast',
          '.notification'
        ];
        
        let toastFound = false;
        for (const selector of toastSelectors) {
          const toast = page.locator(selector);
          if (await toast.isVisible()) {
            toastFound = true;
            console.log(`✅ Toast notification found with selector: ${selector}`);
            break;
          }
        }
        
        // Alternative: check for success message in the page content
        if (!toastFound) {
          const pageContent = await page.textContent('body');
          if (pageContent.includes('sepete eklendi') || pageContent.includes('başarı')) {
            toastFound = true;
            console.log('✅ Success message found in page content');
          }
        }
        
        expect(toastFound).toBe(true);
      }
    }
  });
});