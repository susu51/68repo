#!/usr/bin/env python3
"""
COURIER MAP PANEL BACKEND TESTING
Test the courier map panel backend endpoints as requested in review:

1. Courier Authentication Test - Login with testkurye@example.com/test123
2. Nearby Businesses Endpoint Test - GET /api/courier/tasks/nearby-businesses
3. Available Orders for Business Test - GET /api/courier/tasks/businesses/{business_id}/available-orders
4. Claim Order Test - POST /api/courier/tasks/orders/{order_id}/claim

SUCCESS CRITERIA:
✅ Courier authentication working
✅ Nearby businesses endpoint returns data with correct structure
✅ Available orders endpoint returns ready orders
✅ Claim order endpoint successfully assigns orders with atomic operations
✅ Proper error handling for edge cases
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com/api"

class CourierMapPanelTest:
    def __init__(self):
        self.session = None
        self.courier_cookies = None
        self.business_cookies = None
        self.customer_cookies = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        print("🔗 HTTP session initialized")
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            print("🔗 HTTP session closed")
    
    def log_result(self, test_name, success, details):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_courier_authentication(self):
        """Test 1: Courier Authentication with testkurye@example.com/test123"""
        print("\n🔐 TEST 1: Courier Authentication")
        
        try:
            login_data = {
                "email": "testkurye@example.com",
                "password": "test123"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.courier_cookies = response.cookies
                    
                    # Verify JWT token and role
                    if data.get("access_token") and data.get("user", {}).get("role") == "courier":
                        self.log_result(
                            "Courier Authentication", 
                            True, 
                            f"Login successful, JWT token received, role=courier, user_id={data.get('user', {}).get('id')}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Courier Authentication", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Courier Authentication", 
                        False, 
                        f"Login failed with status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Courier Authentication", False, f"Exception: {str(e)}")
            return False
    
    async def test_nearby_businesses(self):
        """Test 2: Nearby Businesses Endpoint"""
        print("\n🗺️ TEST 2: Nearby Businesses Endpoint")
        
        try:
            # Test coordinates (Aksaray, Turkey)
            params = {
                "lng": 34.0254,
                "lat": 38.3687,
                "radius_m": 10000
            }
            
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/nearby-businesses",
                params=params,
                cookies=self.courier_cookies
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        # Check if we have businesses with ready orders
                        businesses_with_orders = [b for b in data if b.get("pending_ready_count", 0) > 0]
                        
                        if len(businesses_with_orders) > 0:
                            # Verify expected fields
                            sample_business = businesses_with_orders[0]
                            required_fields = ["business_id", "name", "location", "pending_ready_count", "address_short", "distance"]
                            missing_fields = [field for field in required_fields if field not in sample_business]
                            
                            if not missing_fields:
                                self.log_result(
                                    "Nearby Businesses Structure", 
                                    True, 
                                    f"Found {len(businesses_with_orders)} businesses with ready orders, all required fields present"
                                )
                                return businesses_with_orders
                            else:
                                self.log_result(
                                    "Nearby Businesses Structure", 
                                    False, 
                                    f"Missing required fields: {missing_fields}"
                                )
                                return []
                        else:
                            self.log_result(
                                "Nearby Businesses Data", 
                                True, 
                                f"Endpoint working but no businesses with ready orders found (total businesses: {len(data)})"
                            )
                            return []
                    else:
                        self.log_result(
                            "Nearby Businesses Response", 
                            False, 
                            f"Expected list, got: {type(data)}"
                        )
                        return []
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Nearby Businesses Endpoint", 
                        False, 
                        f"Request failed with status {response.status}: {error_text}"
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Nearby Businesses Endpoint", False, f"Exception: {str(e)}")
            return []
    
    async def test_business_available_orders(self, business_id):
        """Test 3: Available Orders for Business"""
        print(f"\n📋 TEST 3: Available Orders for Business {business_id}")
        
        try:
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/businesses/{business_id}/available-orders",
                cookies=self.courier_cookies
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        ready_orders = [order for order in data if order.get("order_id")]
                        
                        if len(ready_orders) > 0:
                            # Verify expected fields
                            sample_order = ready_orders[0]
                            required_fields = [
                                "order_id", "order_code", "customer_name", 
                                "delivery_address", "delivery_location", 
                                "total_amount", "delivery_fee", "grand_total", 
                                "items_count", "notes"
                            ]
                            missing_fields = [field for field in required_fields if field not in sample_order]
                            
                            if not missing_fields:
                                self.log_result(
                                    "Available Orders Structure", 
                                    True, 
                                    f"Found {len(ready_orders)} ready orders with all required fields"
                                )
                                return ready_orders
                            else:
                                self.log_result(
                                    "Available Orders Structure", 
                                    False, 
                                    f"Missing required fields: {missing_fields}"
                                )
                                return []
                        else:
                            self.log_result(
                                "Available Orders Data", 
                                True, 
                                f"Endpoint working but no ready orders found for business {business_id}"
                            )
                            return []
                    else:
                        self.log_result(
                            "Available Orders Response", 
                            False, 
                            f"Expected list, got: {type(data)}"
                        )
                        return []
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Available Orders Endpoint", 
                        False, 
                        f"Request failed with status {response.status}: {error_text}"
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Available Orders Endpoint", False, f"Exception: {str(e)}")
            return []
    
    async def create_test_order(self):
        """Helper: Create a test order to claim"""
        print("\n🛒 HELPER: Creating test order for claim testing")
        
        try:
            # First login as customer
            customer_login = {
                "email": "test@kuryecini.com",
                "password": "test123"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=customer_login
            ) as response:
                if response.status == 200:
                    self.customer_cookies = response.cookies
                    print("✅ Customer login successful")
                else:
                    print("❌ Customer login failed")
                    return None
            
            # Get a business with menu items
            async with self.session.get(
                f"{BACKEND_URL}/businesses?city=Aksaray",
                cookies=self.customer_cookies
            ) as response:
                if response.status == 200:
                    businesses = await response.json()
                    if businesses:
                        business_id = businesses[0].get("id")
                        print(f"✅ Found business: {business_id}")
                        
                        # Get menu items
                        async with self.session.get(
                            f"{BACKEND_URL}/business/public/{business_id}/menu",
                        ) as menu_response:
                            if menu_response.status == 200:
                                menu_items = await menu_response.json()
                                if menu_items:
                                    # Create order
                                    order_data = {
                                        "business_id": business_id,
                                        "items": [{
                                            "product_id": menu_items[0].get("id"),
                                            "title": menu_items[0].get("name"),
                                            "price": menu_items[0].get("price"),
                                            "quantity": 1
                                        }],
                                        "delivery_address": {
                                            "label": "Test Address",
                                            "address": "Test Street 123, Aksaray",
                                            "lat": 38.3687,
                                            "lng": 34.0254
                                        },
                                        "payment_method": "cash_on_delivery",
                                        "notes": "Test order for courier claim testing"
                                    }
                                    
                                    async with self.session.post(
                                        f"{BACKEND_URL}/orders",
                                        json=order_data,
                                        cookies=self.customer_cookies
                                    ) as order_response:
                                        if order_response.status == 200:
                                            order_result = await order_response.json()
                                            order_id = order_result.get("order_id")
                                            print(f"✅ Test order created: {order_id}")
                                            
                                            # Now login as business and mark order as ready
                                            business_login = {
                                                "email": "testbusiness@example.com",
                                                "password": "test123"
                                            }
                                            
                                            async with self.session.post(
                                                f"{BACKEND_URL}/auth/login",
                                                json=business_login
                                            ) as business_response:
                                                if business_response.status == 200:
                                                    self.business_cookies = business_response.cookies
                                                    
                                                    # Mark order as ready
                                                    async with self.session.patch(
                                                        f"{BACKEND_URL}/business/orders/{order_id}/status",
                                                        json={"status": "ready"},
                                                        cookies=self.business_cookies
                                                    ) as status_response:
                                                        if status_response.status == 200:
                                                            print(f"✅ Order {order_id} marked as ready")
                                                            return order_id
                                                        else:
                                                            print(f"❌ Failed to mark order as ready: {status_response.status}")
                                                            return None
                                                else:
                                                    print("❌ Business login failed")
                                                    return None
                                        else:
                                            print(f"❌ Order creation failed: {order_response.status}")
                                            return None
                                else:
                                    print("❌ No menu items found")
                                    return None
                            else:
                                print(f"❌ Menu fetch failed: {menu_response.status}")
                                return None
                    else:
                        print("❌ No businesses found")
                        return None
                else:
                    print(f"❌ Business discovery failed: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ Exception creating test order: {str(e)}")
            return None
    
    async def test_claim_order(self, order_id):
        """Test 4: Claim Order"""
        print(f"\n🎯 TEST 4: Claim Order {order_id}")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/courier/tasks/orders/{order_id}/claim",
                cookies=self.courier_cookies
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success") and data.get("status") == "assigned":
                        self.log_result(
                            "Claim Order Success", 
                            True, 
                            f"Order {order_id} successfully claimed and assigned to courier"
                        )
                        
                        # Test claiming the same order again (should return 409)
                        async with self.session.post(
                            f"{BACKEND_URL}/courier/tasks/orders/{order_id}/claim",
                            cookies=self.courier_cookies
                        ) as retry_response:
                            
                            if retry_response.status == 409:
                                self.log_result(
                                    "Claim Order Conflict Handling", 
                                    True, 
                                    "Correctly returned 409 conflict when trying to claim already assigned order"
                                )
                            else:
                                self.log_result(
                                    "Claim Order Conflict Handling", 
                                    False, 
                                    f"Expected 409 conflict, got {retry_response.status}"
                                )
                        
                        return True
                    else:
                        self.log_result(
                            "Claim Order Response", 
                            False, 
                            f"Invalid response structure: {data}"
                        )
                        return False
                        
                elif response.status == 409:
                    error_data = await response.json()
                    self.log_result(
                        "Claim Order Already Taken", 
                        True, 
                        f"Order already claimed by another courier: {error_data.get('detail')}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Claim Order Endpoint", 
                        False, 
                        f"Request failed with status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Claim Order Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_handling(self):
        """Test 5: Error Handling Edge Cases"""
        print("\n🚨 TEST 5: Error Handling Edge Cases")
        
        try:
            # Test 1: Invalid business ID for available orders
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/businesses/invalid-business-id/available-orders",
                cookies=self.courier_cookies
            ) as response:
                
                if response.status in [404, 400]:
                    self.log_result(
                        "Invalid Business ID Handling", 
                        True, 
                        f"Correctly handled invalid business ID with status {response.status}"
                    )
                else:
                    self.log_result(
                        "Invalid Business ID Handling", 
                        False, 
                        f"Expected 404/400, got {response.status}"
                    )
            
            # Test 2: Invalid order ID for claim
            async with self.session.post(
                f"{BACKEND_URL}/courier/tasks/orders/invalid-order-id/claim",
                cookies=self.courier_cookies
            ) as response:
                
                if response.status in [404, 400]:
                    self.log_result(
                        "Invalid Order ID Handling", 
                        True, 
                        f"Correctly handled invalid order ID with status {response.status}"
                    )
                else:
                    self.log_result(
                        "Invalid Order ID Handling", 
                        False, 
                        f"Expected 404/400, got {response.status}"
                    )
            
            # Test 3: Unauthenticated access
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/nearby-businesses?lng=34.0254&lat=38.3687"
            ) as response:
                
                if response.status in [401, 403]:
                    self.log_result(
                        "Unauthenticated Access Handling", 
                        True, 
                        f"Correctly blocked unauthenticated access with status {response.status}"
                    )
                else:
                    self.log_result(
                        "Unauthenticated Access Handling", 
                        False, 
                        f"Expected 401/403, got {response.status}"
                    )
                    
        except Exception as e:
            self.log_result("Error Handling Tests", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all courier map panel tests"""
        print("🚀 STARTING COURIER MAP PANEL BACKEND TESTING")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Test 1: Authentication
            auth_success = await self.test_courier_authentication()
            if not auth_success:
                print("❌ Authentication failed - cannot proceed with other tests")
                return
            
            # Test 2: Nearby Businesses
            businesses = await self.test_nearby_businesses()
            
            # Test 3: Available Orders (use first business if available)
            if businesses:
                business_id = businesses[0].get("business_id")
                orders = await self.test_business_available_orders(business_id)
                
                # Test 4: Claim Order (create test order if no existing orders)
                if orders:
                    order_id = orders[0].get("order_id")
                    await self.test_claim_order(order_id)
                else:
                    # Create a test order
                    test_order_id = await self.create_test_order()
                    if test_order_id:
                        await self.test_claim_order(test_order_id)
                    else:
                        self.log_result(
                            "Claim Order Test", 
                            False, 
                            "Could not create test order for claim testing"
                        )
            else:
                self.log_result(
                    "Available Orders Test", 
                    False, 
                    "No businesses with ready orders found - cannot test available orders and claim"
                )
            
            # Test 5: Error Handling
            await self.test_error_handling()
            
        finally:
            await self.cleanup_session()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COURIER MAP PANEL BACKEND TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print("\n🎯 SUCCESS CRITERIA CHECK:")
        auth_passed = any(r["success"] for r in self.test_results if "Authentication" in r["test"])
        nearby_passed = any(r["success"] for r in self.test_results if "Nearby Businesses" in r["test"])
        orders_passed = any(r["success"] for r in self.test_results if "Available Orders" in r["test"])
        claim_passed = any(r["success"] for r in self.test_results if "Claim Order" in r["test"])
        error_passed = any(r["success"] for r in self.test_results if "Error" in r["test"] or "Invalid" in r["test"])
        
        criteria = [
            ("Courier authentication working", auth_passed),
            ("Nearby businesses endpoint returns data", nearby_passed),
            ("Available orders endpoint returns ready orders", orders_passed),
            ("Claim order endpoint successfully assigns orders", claim_passed),
            ("Proper error handling for edge cases", error_passed)
        ]
        
        for criterion, passed in criteria:
            status = "✅" if passed else "❌"
            print(f"{status} {criterion}")
        
        overall_success = all(passed for _, passed in criteria)
        print(f"\n🏆 OVERALL RESULT: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
        
        if overall_success:
            print("🎉 All courier map panel backend endpoints are working correctly!")
        else:
            print("⚠️ Some issues found - see detailed results above")

async def main():
    """Main test execution"""
    tester = CourierMapPanelTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())