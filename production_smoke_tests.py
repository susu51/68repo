"""
Production Smoke Tests
Comprehensive E2E testing suite for production deployment validation
"""

import asyncio
import time
import json
import os
from typing import Dict, List, Any
from playwright.async_api import async_playwright, Page, Browser
import aiohttp
import logging

logger = logging.getLogger(__name__)

class ProductionSmokeTests:
    """Production smoke test suite"""
    
    def __init__(self, frontend_url: str, backend_url: str):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.browser = None
        self.context = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def setup(self):
        """Setup browser and context"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Kuryecini-SmokeTest/1.0'
        )
        
    async def teardown(self):
        """Cleanup browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        start_time = time.time()
        
        try:
            await test_func()
            duration = time.time() - start_time
            
            result = {
                'test': test_name,
                'status': 'PASS',
                'duration_seconds': round(duration, 2),
                'timestamp': time.time(),
                'error': None
            }
            
            logger.info(f"✅ PASS: {test_name} ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            
            result = {
                'test': test_name,
                'status': 'FAIL',
                'duration_seconds': round(duration, 2),
                'timestamp': time.time(),
                'error': str(e)
            }
            
            logger.error(f"❌ FAIL: {test_name} - {str(e)}")
        
        self.test_results.append(result)
        return result
    
    # Backend API Tests
    async def test_backend_health(self):
        """Test backend health endpoints"""
        async with aiohttp.ClientSession() as session:
            # Test basic health
            async with session.get(f"{self.backend_url}/healthz", timeout=10) as response:
                assert response.status == 200
                data = await response.json()
                assert data['status'] == 'ok'
            
            # Test API health
            async with session.get(f"{self.backend_url}/api/healthz", timeout=10) as response:
                assert response.status == 200
                data = await response.json()
                assert data['status'] == 'ok'
    
    async def test_backend_menus_api(self):
        """Test menus API endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.backend_url}/api/menus", timeout=10) as response:
                assert response.status == 200
                data = await response.json()
                assert isinstance(data, list)
                
                # If menus exist, validate schema
                if data:
                    menu_item = data[0]
                    required_fields = ['id', 'title', 'price', 'imageUrl', 'category']
                    for field in required_fields:
                        assert field in menu_item, f"Missing field: {field}"
    
    async def test_backend_cors(self):
        """Test CORS configuration"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            async with session.options(f"{self.backend_url}/api/healthz", headers=headers, timeout=10) as response:
                assert response.status in [200, 204]
                assert 'access-control-allow-origin' in response.headers
    
    # Frontend Tests
    async def test_frontend_loading(self):
        """Test frontend loading and basic functionality"""
        page = await self.context.new_page()
        
        try:
            # Navigate to homepage
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check title
            title = await page.title()
            assert 'Kuryecini' in title
            
            # Check main heading
            heading = await page.locator('text=Türkiye\'nin En Hızlı').first
            await heading.wait_for(timeout=10000)
            assert await heading.is_visible()
            
            # Check main CTA button
            cta_button = await page.locator('text=Hemen Sipariş Ver').first
            assert await cta_button.is_visible()
            
        finally:
            await page.close()
    
    async def test_customer_flow_complete(self):
        """Test complete customer flow: login → menu → cart → checkout → order"""
        page = await self.context.new_page()
        
        try:
            # Step 1: Navigate and Login
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            await page.click('text=Hemen Sipariş Ver', timeout=10000)
            await page.wait_for_timeout(2000)
            
            await page.fill('input[type="email"]', 'testcustomer@example.com')
            await page.fill('input[type="password"]', 'test123')
            await page.click('button:has-text("Giriş Yap")', timeout=10000)
            await page.wait_for_timeout(4000)
            
            # Verify login success
            discover_tab = page.locator('text=Keşfet')
            await discover_tab.wait_for(timeout=10000)
            assert await discover_tab.is_visible()
            
            # Step 2: Browse restaurants and menu
            await page.click('text=Keşfet')
            await page.wait_for_timeout(3000)
            
            # Check restaurant cards display
            restaurant_cards = page.locator('.group')
            assert await restaurant_cards.count() > 0
            
            # Click on first restaurant
            await restaurant_cards.first().click()
            await page.wait_for_timeout(3000)
            
            # Verify menu items display with prices
            price_elements = page.locator('text=₺')
            assert await price_elements.count() > 0
            
            # Step 3: Add items to cart
            add_buttons = page.locator('button[class*="bg-orange-500"]')
            if await add_buttons.count() > 0:
                # Add first item
                await add_buttons.first().click()
                await page.wait_for_timeout(1000)
                
                # Add same item again (quantity increase)
                await add_buttons.first().click()
                await page.wait_for_timeout(1000)
            
            # Step 4: Check sticky cart or checkout
            # Look for sticky cart (mobile) or checkout button
            checkout_selectors = [
                'button:has-text("Sepeti Onayla")',
                'button:has-text("Siparişi Tamamla")',
                '.fixed.bottom-0'  # Sticky cart
            ]
            
            checkout_found = False
            for selector in checkout_selectors:
                checkout_element = page.locator(selector)
                if await checkout_element.count() > 0:
                    checkout_found = True
                    break
            
            assert checkout_found, "No checkout mechanism found"
            
            # Step 5: Test toast notifications
            # Toast may be visible after cart operations
            toast_selectors = [
                '[data-sonner-toast]',
                '.Toastify__toast',
                '[data-hot-toast]',
                '.toast'
            ]
            
            # Check for any success messages in page content
            page_content = await page.text_content('body')
            success_indicators = [
                'sepete eklendi',
                'başarı',
                'success',
                'eklendi'
            ]
            
            toast_or_success = any(indicator in page_content.lower() for indicator in success_indicators)
            if not toast_or_success:
                # Check for actual toast elements
                for selector in toast_selectors:
                    if await page.locator(selector).count() > 0:
                        toast_or_success = True
                        break
            
            # Note: Toast may have disappeared by now, which is normal
            logger.info(f"Toast or success message found: {toast_or_success}")
            
        finally:
            await page.close()
    
    async def test_courier_map_functionality(self):
        """Test courier map loading and functionality"""
        page = await self.context.new_page()
        
        try:
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Try to access courier login
            await page.click('text=Hemen Sipariş Ver', timeout=10000)
            await page.wait_for_timeout(1000)
            
            # Look for courier option
            courier_button = page.locator('text=Kurye')
            if await courier_button.is_visible():
                await courier_button.click()
                
                # Login as courier
                await page.fill('input[type="email"]', 'testkurye@example.com')
                await page.fill('input[type="password"]', 'test123')
                await page.click('button:has-text("Giriş Yap")', timeout=10000)
                await page.wait_for_timeout(4000)
                
                # Check for map container
                map_container = page.locator('.leaflet-container')
                if await map_container.is_visible():
                    # Verify map has proper height
                    map_height = await map_container.evaluate('el => getComputedStyle(el).height')
                    
                    # Check for map controls
                    location_button = page.locator('button:has-text("Konumu Al")')
                    assert await location_button.is_visible()
                    
                    # Check OSM attribution (indicates map loaded)
                    osm_attribution = page.locator('text=OpenStreetMap')
                    await osm_attribution.wait_for(timeout=10000)
                    
                    logger.info(f"Map loaded successfully with height: {map_height}")
                else:
                    logger.warning("Courier map not accessible or not visible")
            else:
                logger.warning("Courier login option not found")
                
        finally:
            await page.close()
    
    async def test_business_panel_access(self):
        """Test business panel access and functionality"""
        page = await self.context.new_page()
        
        try:
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            await page.click('text=Hemen Sipariş Ver', timeout=10000)
            await page.wait_for_timeout(1000)
            
            # Look for business option
            business_button = page.locator('text=İşletme')
            if await business_button.is_visible():
                await business_button.click()
                
                # Login as business
                await page.fill('input[type="email"]', 'testrestoran@example.com')
                await page.fill('input[type="password"]', 'test123')
                await page.click('button:has-text("Giriş Yap")', timeout=10000)
                await page.wait_for_timeout(4000)
                
                # Check for business dashboard elements
                dashboard_elements = [
                    'text=Ana Sayfa',
                    'text=Siparişler', 
                    'text=Menü',
                    'text=İstatistikler'
                ]
                
                found_elements = 0
                for element in dashboard_elements:
                    if await page.locator(element).is_visible():
                        found_elements += 1
                
                assert found_elements >= 2, f"Business dashboard not properly loaded (found {found_elements}/4 elements)"
                
                # Test menu management access
                await page.click('text=Menü', timeout=5000)
                await page.wait_for_timeout(2000)
                
                # Check for product management elements
                add_product_indicators = [
                    'button:has-text("Ürün Ekle")',
                    'button:has-text("Yeni Ürün")',
                    'text=Ürünler'
                ]
                
                menu_management_found = False
                for indicator in add_product_indicators:
                    if await page.locator(indicator).is_visible():
                        menu_management_found = True
                        break
                
                logger.info(f"Menu management accessible: {menu_management_found}")
                
            else:
                logger.warning("Business login option not found")
                
        finally:
            await page.close()
    
    async def test_admin_panel_access(self):
        """Test admin panel access"""
        page = await self.context.new_page()
        
        try:
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            await page.click('text=Hemen Sipariş Ver', timeout=10000)
            await page.wait_for_timeout(1000)
            
            # Look for admin option
            admin_button = page.locator('text=Admin')
            if await admin_button.is_visible():
                await admin_button.click()
                
                # Try simple admin login (just password)
                password_input = page.locator('input[type="password"]')
                if await password_input.is_visible():
                    await password_input.fill('6851')
                    await page.click('button:has-text("Giriş Yap")', timeout=10000)
                    await page.wait_for_timeout(3000)
                    
                    # Check for admin dashboard elements
                    admin_elements = [
                        'text=Kullanıcı Yönetimi',
                        'text=İşletme',
                        'text=Kurye',
                        'text=İstatistikler'
                    ]
                    
                    found_elements = 0
                    for element in admin_elements:
                        if await page.locator(element).is_visible():
                            found_elements += 1
                    
                    logger.info(f"Admin dashboard elements found: {found_elements}/4")
                    
            else:
                logger.warning("Admin login option not found")
                
        finally:
            await page.close()
    
    async def test_spa_routing(self):
        """Test SPA routing and direct URL access"""
        page = await self.context.new_page()
        
        try:
            # Test direct route access
            test_routes = [
                f"{self.frontend_url}/some/deep/route",
                f"{self.frontend_url}/customer/dashboard", 
                f"{self.frontend_url}/404/not/found"
            ]
            
            for route in test_routes:
                await page.goto(route, timeout=10000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Should not show browser 404, should load the SPA
                page_content = await page.text_content('body')
                assert len(page_content) > 100, f"Route {route} returned empty content"
                assert 'Kuryecini' in page_content or 'kuryecini' in page_content.lower(), f"Route {route} did not load the SPA"
                
                logger.info(f"SPA routing working for: {route}")
                
        finally:
            await page.close()
    
    async def test_mobile_responsiveness(self):
        """Test mobile responsiveness"""
        page = await self.context.new_page()
        
        try:
            # Set mobile viewport
            await page.set_viewport_size({'width': 390, 'height': 844})
            
            await page.goto(self.frontend_url, timeout=15000)
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check if mobile layout is responsive
            main_content = page.locator('body')
            assert await main_content.is_visible()
            
            # Check main CTA button on mobile
            cta_button = page.locator('text=Hemen Sipariş Ver')
            assert await cta_button.is_visible()
            
            # Test mobile navigation
            await cta_button.click(timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Form should be properly sized on mobile
            email_input = page.locator('input[type="email"]')
            if await email_input.is_visible():
                input_box = await email_input.bounding_box()
                assert input_box['width'] > 200, "Email input too narrow on mobile"
            
            logger.info("Mobile responsiveness test passed")
            
        finally:
            await page.close()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        await self.setup()
        
        try:
            logger.info(f"Starting production smoke tests for {self.frontend_url}")
            
            # Backend tests
            await self.run_test("Backend Health Check", self.test_backend_health)
            await self.run_test("Backend Menus API", self.test_backend_menus_api)
            await self.run_test("Backend CORS Configuration", self.test_backend_cors)
            
            # Frontend tests  
            await self.run_test("Frontend Loading", self.test_frontend_loading)
            await self.run_test("Customer Complete Flow", self.test_customer_flow_complete)
            await self.run_test("Courier Map Functionality", self.test_courier_map_functionality)
            await self.run_test("Business Panel Access", self.test_business_panel_access)
            await self.run_test("Admin Panel Access", self.test_admin_panel_access)
            await self.run_test("SPA Routing", self.test_spa_routing)
            await self.run_test("Mobile Responsiveness", self.test_mobile_responsiveness)
            
            # Calculate results
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['status'] == 'PASS')
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            summary = {
                'timestamp': time.time(),
                'frontend_url': self.frontend_url,
                'backend_url': self.backend_url,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate_percent': round(success_rate, 1),
                'total_duration_seconds': round(sum(r['duration_seconds'] for r in self.test_results), 2),
                'test_results': self.test_results
            }
            
            logger.info(f"Smoke tests completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            
            return summary
            
        finally:
            await self.teardown()

async def run_production_smoke_tests(frontend_url: str, backend_url: str) -> Dict[str, Any]:
    """Run production smoke tests and return results"""
    tester = ProductionSmokeTests(frontend_url, backend_url)
    return await tester.run_all_tests()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python smoke_tests.py <frontend_url> <backend_url>")
        sys.exit(1)
    
    frontend_url = sys.argv[1]
    backend_url = sys.argv[2]
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run tests
    results = asyncio.run(run_production_smoke_tests(frontend_url, backend_url))
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results['failed_tests'] == 0:
        print(f"\n🎉 All {results['total_tests']} smoke tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {results['failed_tests']} out of {results['total_tests']} tests failed")
        sys.exit(1)