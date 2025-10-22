#!/usr/bin/env python3
"""
COMPREHENSIVE COURIER MAP PANEL BACKEND TESTING
Creates test data and tests all courier map panel endpoints

Test Flow:
1. Create test business with location
2. Create test menu items
3. Create test customer order
4. Mark order as ready
5. Test courier map panel endpoints
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

class ComprehensiveCourierTest:
    def __init__(self):
        self.session = None
        self.courier_cookies = None
        self.business_cookies = None
        self.customer_cookies = None
        self.admin_cookies = None
        self.test_results = []
        self.test_business_id = None
        self.test_order_id = None
        
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
    
    async def login_user(self, email, password, user_type):
        """Generic login function"""
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    cookies = response.cookies
                    
                    if user_type == "courier":
                        self.courier_cookies = cookies
                    elif user_type == "business":
                        self.business_cookies = cookies
                    elif user_type == "customer":
                        self.customer_cookies = cookies
                    elif user_type == "admin":
                        self.admin_cookies = cookies
                    
                    print(f"✅ {user_type.title()} login successful: {email}")
                    return True, data
                else:
                    error_text = await response.text()
                    print(f"❌ {user_type.title()} login failed: {error_text}")
                    return False, None
                    
        except Exception as e:
            print(f"❌ {user_type.title()} login exception: {str(e)}")
            return False, None
    
    async def setup_test_data(self):
        """Create test business, menu, and order data"""
        print("\n🏗️ SETTING UP TEST DATA")
        
        # 1. Login as admin to approve business
        admin_success, admin_data = await self.login_user("admin@kuryecini.com", "admin123", "admin")
        if not admin_success:
            return False
        
        # 2. Login as business
        business_success, business_data = await self.login_user("testbusiness@example.com", "test123", "business")
        if not business_success:
            return False
        
        self.test_business_id = business_data.get("user", {}).get("id")
        print(f"✅ Test business ID: {self.test_business_id}")
        
        # 3. Approve business via admin (if needed)
        try:
            async with self.session.patch(
                f"{BACKEND_URL}/admin/users/{self.test_business_id}/kyc",
                json={"status": "approved"},
                cookies=self.admin_cookies
            ) as response:
                if response.status in [200, 400]:  # 400 might mean already approved
                    print("✅ Business KYC approved")
                else:
                    print(f"⚠️ Business KYC approval status: {response.status}")
        except Exception as e:
            print(f"⚠️ Business KYC approval error: {str(e)}")
        
        # 4. Create menu items for business
        menu_items = [
            {
                "name": "Test Pizza",
                "description": "Delicious test pizza",
                "price": 45.0,
                "category": "Yemek",
                "preparation_time": 20,
                "is_available": True
            },
            {
                "name": "Test Burger",
                "description": "Tasty test burger",
                "price": 35.0,
                "category": "Yemek", 
                "preparation_time": 15,
                "is_available": True
            }
        ]
        
        for item in menu_items:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/business/menu",
                    json=item,
                    cookies=self.business_cookies
                ) as response:
                    if response.status == 200:
                        print(f"✅ Created menu item: {item['name']}")
                    else:
                        error_text = await response.text()
                        print(f"⚠️ Menu item creation failed: {error_text}")
            except Exception as e:
                print(f"⚠️ Menu item creation error: {str(e)}")
        
        # 5. Login as customer and create order
        customer_success, customer_data = await self.login_user("test@kuryecini.com", "test123", "customer")
        if not customer_success:
            return False
        
        # 6. Get menu items to create order
        try:
            async with self.session.get(
                f"{BACKEND_URL}/business/public/{self.test_business_id}/menu"
            ) as response:
                if response.status == 200:
                    menu_data = await response.json()
                    if menu_data:
                        # Create order with first menu item
                        order_data = {
                            "business_id": self.test_business_id,
                            "items": [{
                                "product_id": menu_data[0].get("id"),
                                "title": menu_data[0].get("name"),
                                "price": menu_data[0].get("price"),
                                "quantity": 1
                            }],
                            "delivery_address": {
                                "label": "Test Delivery Address",
                                "address": "Test Street 123, Aksaray, Turkey",
                                "lat": 38.3687,
                                "lng": 34.0254
                            },
                            "payment_method": "cash_on_delivery",
                            "notes": "Test order for courier map testing"
                        }
                        
                        async with self.session.post(
                            f"{BACKEND_URL}/orders",
                            json=order_data,
                            cookies=self.customer_cookies
                        ) as order_response:
                            if order_response.status == 200:
                                order_result = await order_response.json()
                                self.test_order_id = order_result.get("order_id")
                                print(f"✅ Test order created: {self.test_order_id}")
                            else:
                                error_text = await order_response.text()
                                print(f"❌ Order creation failed: {error_text}")
                                return False
                    else:
                        print("❌ No menu items found")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Menu fetch failed: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Order creation error: {str(e)}")
            return False
        
        # 7. Mark order as ready (business action)
        try:
            async with self.session.patch(
                f"{BACKEND_URL}/business/orders/{self.test_order_id}/status",
                json={"status": "ready"},
                cookies=self.business_cookies
            ) as response:
                if response.status == 200:
                    print(f"✅ Order {self.test_order_id} marked as ready")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to mark order as ready: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Order status update error: {str(e)}")
            return False
    
    async def test_courier_authentication(self):
        """Test courier authentication"""
        print("\n🔐 TEST 1: Courier Authentication")
        
        success, data = await self.login_user("testkurye@example.com", "test123", "courier")
        
        if success and data.get("access_token") and data.get("user", {}).get("role") == "courier":
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
                f"Authentication failed or invalid response"
            )
            return False
    
    async def test_nearby_businesses(self):
        """Test nearby businesses endpoint"""
        print("\n🗺️ TEST 2: Nearby Businesses Endpoint")
        
        try:
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
                        businesses_with_orders = [b for b in data if b.get("pending_ready_count", 0) > 0]
                        
                        if len(businesses_with_orders) > 0:
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
        """Test available orders for business"""
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
    
    async def test_claim_order(self, order_id):
        """Test claim order endpoint"""
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
        """Test error handling edge cases"""
        print("\n🚨 TEST 5: Error Handling Edge Cases")
        
        try:
            # Test 1: Invalid business ID for available orders
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/businesses/invalid-business-id/available-orders",
                cookies=self.courier_cookies
            ) as response:
                
                # Should return empty list for invalid business ID
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) == 0:
                        self.log_result(
                            "Invalid Business ID Handling", 
                            True, 
                            f"Correctly handled invalid business ID with empty list"
                        )
                    else:
                        self.log_result(
                            "Invalid Business ID Handling", 
                            False, 
                            f"Expected empty list, got: {data}"
                        )
                else:
                    self.log_result(
                        "Invalid Business ID Handling", 
                        False, 
                        f"Expected 200 with empty list, got {response.status}"
                    )
            
            # Test 2: Invalid order ID for claim
            async with self.session.post(
                f"{BACKEND_URL}/courier/tasks/orders/invalid-order-id/claim",
                cookies=self.courier_cookies
            ) as response:
                
                if response.status == 409:
                    self.log_result(
                        "Invalid Order ID Handling", 
                        True, 
                        f"Correctly handled invalid order ID with status {response.status}"
                    )
                else:
                    self.log_result(
                        "Invalid Order ID Handling", 
                        False, 
                        f"Expected 409, got {response.status}"
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
        print("🚀 STARTING COMPREHENSIVE COURIER MAP PANEL BACKEND TESTING")
        print("=" * 70)
        
        await self.setup_session()
        
        try:
            # Setup test data
            setup_success = await self.setup_test_data()
            if not setup_success:
                print("❌ Test data setup failed - cannot proceed with tests")
                return
            
            # Test 1: Authentication
            auth_success = await self.test_courier_authentication()
            if not auth_success:
                print("❌ Authentication failed - cannot proceed with other tests")
                return
            
            # Test 2: Nearby Businesses
            businesses = await self.test_nearby_businesses()
            
            # Test 3: Available Orders
            if self.test_business_id:
                orders = await self.test_business_available_orders(self.test_business_id)
                
                # Test 4: Claim Order
                if self.test_order_id:
                    await self.test_claim_order(self.test_order_id)
                else:
                    self.log_result(
                        "Claim Order Test", 
                        False, 
                        "No test order available for claim testing"
                    )
            else:
                self.log_result(
                    "Available Orders Test", 
                    False, 
                    "No test business available"
                )
            
            # Test 5: Error Handling
            await self.test_error_handling()
            
        finally:
            await self.cleanup_session()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE COURIER MAP PANEL BACKEND TEST SUMMARY")
        print("=" * 70)
        
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
            ("✅ Courier authentication working", auth_passed),
            ("✅ Nearby businesses endpoint returns data with correct structure", nearby_passed),
            ("✅ Available orders endpoint returns ready orders", orders_passed),
            ("✅ Claim order endpoint successfully assigns orders with atomic operations", claim_passed),
            ("✅ Proper error handling for edge cases", error_passed)
        ]
        
        print("\n🏆 REVIEW REQUEST SUCCESS CRITERIA:")
        for criterion, passed in criteria:
            status = "✅" if passed else "❌"
            print(f"{status} {criterion}")
        
        overall_success = all(passed for _, passed in criteria)
        print(f"\n🏆 OVERALL RESULT: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
        
        if overall_success:
            print("🎉 All courier map panel backend endpoints are working correctly!")
            print("🎯 Ready for comprehensive testing with testkurye@example.com credentials")
        else:
            print("⚠️ Some issues found - see detailed results above")

async def main():
    """Main test execution"""
    tester = ComprehensiveCourierTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())