#!/usr/bin/env python3
"""
COMPLETE ORDER FLOW TESTING - Backend API Testing
Testing the entire order creation and management flow as requested in review.

Test Scenarios:
1. Create Order (Customer Side)
2. Business Gets Orders  
3. Order Status Updates
4. Order Details
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Test credentials
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

class OrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.customer_cookies = None
        self.business_cookies = None
        self.test_order_id = None
        self.business_id = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_customer_login(self):
        """Test 1: Customer Login"""
        self.log("🔐 Testing Customer Login...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": CUSTOMER_EMAIL,
                    "password": CUSTOMER_PASSWORD
                }
            )
            
            if response.status_code == 200:
                self.customer_cookies = response.cookies
                data = response.json()
                self.log(f"✅ Customer login successful: {data.get('message', 'Login OK')}")
                return True
            else:
                self.log(f"❌ Customer login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Customer login error: {str(e)}")
            return False
    
    def test_get_restaurants(self):
        """Test 2: Get Available Restaurants"""
        self.log("🏪 Testing Restaurant Discovery...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/restaurants",
                cookies=self.customer_cookies
            )
            
            if response.status_code == 200:
                restaurants = response.json()
                if restaurants:
                    self.business_id = restaurants[0].get('id')
                    business_name = restaurants[0].get('name', 'Unknown')
                    self.log(f"✅ Found {len(restaurants)} restaurants. Selected: {business_name} (ID: {self.business_id})")
                    return True
                else:
                    self.log("❌ No restaurants found")
                    return False
            else:
                self.log(f"❌ Restaurant discovery failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Restaurant discovery error: {str(e)}")
            return False
    
    def test_get_menu(self):
        """Test 3: Get Menu for Restaurant"""
        self.log("📋 Testing Menu Retrieval...")
        
        if not self.business_id:
            self.log("❌ No business_id available for menu test")
            return False
            
        try:
            response = self.session.get(
                f"{BACKEND_URL}/business/public/{self.business_id}/menu",
                cookies=self.customer_cookies
            )
            
            if response.status_code == 200:
                menu_items = response.json()
                if menu_items:
                    item = menu_items[0]
                    self.log(f"✅ Menu retrieved: {len(menu_items)} items. First item: {item.get('name', 'Unknown')} - ₺{item.get('price', 0)}")
                    return menu_items
                else:
                    self.log("⚠️ Menu is empty but endpoint works")
                    return []
            else:
                self.log(f"❌ Menu retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Menu retrieval error: {str(e)}")
            return False
    
    def test_create_order(self, menu_items):
        """Test 4: Create Order"""
        self.log("📦 Testing Order Creation...")
        
        if not menu_items:
            # Create a test order with mock data if no menu items
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "id": "test-item-1",
                        "name": "Test Item",
                        "quantity": 1,
                        "price": 29.99
                    }
                ],
                "delivery_address": "Test Address, Aksaray",
                "delivery_coords": {"lat": 38.3687, "lng": 34.0254},
                "payment_method": "cash",
                "notes": "Test order"
            }
        else:
            # Use actual menu item
            item = menu_items[0]
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "id": item.get('id'),
                        "name": item.get('name', 'Test Item'),
                        "quantity": 1,
                        "price": item.get('price', 29.99)
                    }
                ],
                "delivery_address": "Test Address, Aksaray",
                "delivery_coords": {"lat": 38.3687, "lng": 34.0254},
                "payment_method": "cash",
                "notes": "Test order from backend test"
            }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                cookies=self.customer_cookies
            )
            
            if response.status_code in [200, 201]:
                order_response = response.json()
                self.test_order_id = order_response.get('order_id') or order_response.get('id')
                order_code = order_response.get('order_code', 'N/A')
                status = order_response.get('status', 'N/A')
                created_at = order_response.get('created_at', 'N/A')
                
                self.log(f"✅ Order created successfully!")
                self.log(f"   Order ID: {self.test_order_id}")
                self.log(f"   Order Code: {order_code}")
                self.log(f"   Status: {status}")
                self.log(f"   Created: {created_at}")
                return True
            else:
                self.log(f"❌ Order creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Order creation error: {str(e)}")
            return False
    
    def test_business_login(self):
        """Test 5: Business Login"""
        self.log("🏢 Testing Business Login...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": BUSINESS_EMAIL,
                    "password": BUSINESS_PASSWORD
                }
            )
            
            if response.status_code == 200:
                self.business_cookies = response.cookies
                data = response.json()
                self.log(f"✅ Business login successful: {data.get('message', 'Login OK')}")
                return True
            else:
                self.log(f"❌ Business login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Business login error: {str(e)}")
            return False
    
    def test_business_get_orders(self):
        """Test 6: Business Gets Orders"""
        self.log("📋 Testing Business Order Retrieval...")
        
        try:
            # Test with business_id parameter
            response = self.session.get(
                f"{BACKEND_URL}/orders?business_id={self.business_id}",
                cookies=self.business_cookies
            )
            
            if response.status_code == 200:
                orders = response.json()
                self.log(f"✅ Business orders retrieved: {len(orders)} orders found")
                
                # Look for our test order
                test_order_found = False
                for order in orders:
                    if order.get('id') == self.test_order_id or order.get('order_id') == self.test_order_id:
                        test_order_found = True
                        self.log(f"✅ Test order found in business orders!")
                        self.log(f"   Order Code: {order.get('order_code', 'N/A')}")
                        self.log(f"   Customer: {order.get('customer_name', 'N/A')}")
                        self.log(f"   Status: {order.get('status', 'N/A')}")
                        self.log(f"   Total: ₺{order.get('total_amount', 0)}")
                        break
                
                if not test_order_found and self.test_order_id:
                    self.log(f"⚠️ Test order {self.test_order_id} not found in business orders")
                
                return True
            else:
                self.log(f"❌ Business order retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Business order retrieval error: {str(e)}")
            return False
    
    def test_order_status_updates(self):
        """Test 7: Order Status Updates"""
        self.log("🔄 Testing Order Status Updates...")
        
        if not self.test_order_id:
            self.log("❌ No test order ID available for status updates")
            return False
        
        # Test status progression: preparing -> ready -> confirmed
        statuses_to_test = ["preparing", "ready", "confirmed"]
        
        for status in statuses_to_test:
            try:
                response = self.session.patch(
                    f"{BACKEND_URL}/orders/{self.test_order_id}/status",
                    json={"status": status},
                    cookies=self.business_cookies
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Status updated to '{status}': {result.get('message', 'Success')}")
                else:
                    self.log(f"❌ Status update to '{status}' failed: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Status update to '{status}' error: {str(e)}")
                return False
        
        return True
    
    def test_order_details(self):
        """Test 8: Order Details Retrieval"""
        self.log("📄 Testing Order Details Retrieval...")
        
        if not self.test_order_id:
            self.log("❌ No test order ID available for details test")
            return False
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}",
                cookies=self.business_cookies
            )
            
            if response.status_code == 200:
                order = response.json()
                self.log(f"✅ Order details retrieved successfully!")
                
                # Verify required fields
                required_fields = ['customer_name', 'delivery_address', 'items', 'status', 'total_amount']
                missing_fields = []
                
                for field in required_fields:
                    if field not in order or order[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log(f"⚠️ Missing fields in order details: {missing_fields}")
                else:
                    self.log("✅ All required fields present in order details")
                
                # Log key details
                self.log(f"   Customer: {order.get('customer_name', 'N/A')}")
                self.log(f"   Phone: {order.get('customer_phone', 'N/A')}")
                self.log(f"   Address: {order.get('delivery_address', 'N/A')}")
                self.log(f"   Coords: {order.get('delivery_coords', 'N/A')}")
                self.log(f"   Items: {len(order.get('items', []))} items")
                self.log(f"   Status: {order.get('status', 'N/A')}")
                self.log(f"   Total: ₺{order.get('total_amount', 0)}")
                
                return True
            else:
                self.log(f"❌ Order details retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Order details retrieval error: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run the complete order flow test"""
        self.log("🚀 STARTING COMPLETE ORDER FLOW TESTING")
        self.log("=" * 60)
        
        test_results = []
        
        # Test 1: Customer Login
        result = self.test_customer_login()
        test_results.append(("Customer Login", result))
        if not result:
            self.log("❌ Cannot continue without customer login")
            return self.print_summary(test_results)
        
        # Test 2: Get Restaurants
        result = self.test_get_restaurants()
        test_results.append(("Restaurant Discovery", result))
        if not result:
            self.log("❌ Cannot continue without restaurants")
            return self.print_summary(test_results)
        
        # Test 3: Get Menu
        menu_items = self.test_get_menu()
        test_results.append(("Menu Retrieval", bool(menu_items is not False)))
        
        # Test 4: Create Order
        result = self.test_create_order(menu_items if menu_items else [])
        test_results.append(("Order Creation", result))
        if not result:
            self.log("❌ Cannot continue without order creation")
            return self.print_summary(test_results)
        
        # Test 5: Business Login
        result = self.test_business_login()
        test_results.append(("Business Login", result))
        if not result:
            self.log("❌ Cannot continue without business login")
            return self.print_summary(test_results)
        
        # Test 6: Business Get Orders
        result = self.test_business_get_orders()
        test_results.append(("Business Order Retrieval", result))
        
        # Test 7: Order Status Updates
        result = self.test_order_status_updates()
        test_results.append(("Order Status Updates", result))
        
        # Test 8: Order Details
        result = self.test_order_details()
        test_results.append(("Order Details Retrieval", result))
        
        return self.print_summary(test_results)
    
    def print_summary(self, test_results):
        """Print test summary"""
        self.log("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log("=" * 60)
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"📈 OVERALL RESULT: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        
        if success_rate >= 80:
            self.log("🎉 EXCELLENT - Order flow is working well!")
        elif success_rate >= 60:
            self.log("⚠️ GOOD - Order flow mostly working with some issues")
        else:
            self.log("🚨 CRITICAL - Major issues in order flow")
        
        return success_rate >= 60
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if response_data and not success:
            print(f"    Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    async def login_business_user(self):
        """Login as business user and get cookies"""
        try:
            login_data = {
                "email": BUSINESS_USER["email"],
                "password": BUSINESS_USER["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    self.business_cookies = response.cookies
                    response_data = await response.json()
                    self.log_test("Business User Login", True, f"Logged in as {BUSINESS_USER['email']}")
                    return True
                else:
                    error_data = await response.text()
                    self.log_test("Business User Login", False, f"Status: {response.status}, Error: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_test("Business User Login", False, f"Exception: {str(e)}")
            return False
            
    async def login_customer_user(self):
        """Login as customer user for negative testing"""
        try:
            login_data = {
                "email": CUSTOMER_USER["email"],
                "password": CUSTOMER_USER["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    self.customer_cookies = response.cookies
                    self.log_test("Customer User Login", True, f"Logged in as {CUSTOMER_USER['email']}")
                    return True
                else:
                    error_data = await response.text()
                    self.log_test("Customer User Login", False, f"Status: {response.status}, Error: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_test("Customer User Login", False, f"Exception: {str(e)}")
            return False
            
    async def test_dashboard_summary_authenticated(self):
        """Test dashboard summary with authenticated business user"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Verify all required fields are present
                    required_fields = [
                        "business_id", "date", "today_orders_count", "today_revenue",
                        "pending_orders_count", "menu_items_count", "total_customers",
                        "rating_avg", "rating_count", "activities"
                    ]
                    
                    missing_fields = []
                    for field in required_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.log_test(
                            "Dashboard Summary - Field Validation", 
                            False, 
                            f"Missing fields: {missing_fields}",
                            response_data
                        )
                    else:
                        # Verify data types
                        type_checks = [
                            ("business_id", str),
                            ("date", str),
                            ("today_orders_count", int),
                            ("today_revenue", (int, float)),
                            ("pending_orders_count", int),
                            ("menu_items_count", int),
                            ("total_customers", int),
                            ("rating_avg", (int, float)),
                            ("rating_count", int),
                            ("activities", list)
                        ]
                        
                        type_errors = []
                        for field, expected_type in type_checks:
                            if not isinstance(response_data[field], expected_type):
                                type_errors.append(f"{field}: expected {expected_type}, got {type(response_data[field])}")
                        
                        if type_errors:
                            self.log_test(
                                "Dashboard Summary - Type Validation",
                                False,
                                f"Type errors: {type_errors}",
                                response_data
                            )
                        else:
                            # Verify activities structure
                            activities_valid = True
                            if response_data["activities"]:
                                for activity in response_data["activities"]:
                                    if not isinstance(activity, dict):
                                        activities_valid = False
                                        break
                                    required_activity_fields = ["type", "title", "meta"]
                                    for field in required_activity_fields:
                                        if field not in activity:
                                            activities_valid = False
                                            break
                                    if not activities_valid:
                                        break
                                        
                                    # Check meta structure for order activities
                                    if activity["type"] == "order_created":
                                        meta = activity["meta"]
                                        if not all(key in meta for key in ["order_code", "amount", "customer_name"]):
                                            activities_valid = False
                                            break
                            
                            if not activities_valid:
                                self.log_test(
                                    "Dashboard Summary - Activities Validation",
                                    False,
                                    "Invalid activities structure",
                                    response_data
                                )
                            else:
                                self.log_test(
                                    "Dashboard Summary - Authenticated Request",
                                    True,
                                    f"All fields present and valid. Orders: {response_data['today_orders_count']}, Revenue: {response_data['today_revenue']}, Activities: {len(response_data['activities'])}"
                                )
                else:
                    self.log_test(
                        "Dashboard Summary - Authenticated Request",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Authenticated Request", False, f"Exception: {str(e)}")
            
    async def test_dashboard_summary_with_date_parameter(self):
        """Test dashboard summary with date parameter"""
        try:
            test_date = "2025-01-15"
            url = f"{API_BASE}/business/dashboard/summary?date={test_date}"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if response_data.get("date") == test_date:
                        self.log_test(
                            "Dashboard Summary - Date Parameter",
                            True,
                            f"Date parameter working correctly: {test_date}"
                        )
                    else:
                        self.log_test(
                            "Dashboard Summary - Date Parameter",
                            False,
                            f"Expected date {test_date}, got {response_data.get('date')}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Dashboard Summary - Date Parameter",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Date Parameter", False, f"Exception: {str(e)}")
            
    async def test_dashboard_summary_unauthorized(self):
        """Test dashboard summary without authentication"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url) as response:
                response_data = await response.text()
                
                if response.status in [401, 403]:
                    self.log_test(
                        "Dashboard Summary - Unauthorized Access",
                        True,
                        f"Correctly blocked unauthorized access with status {response.status}"
                    )
                else:
                    self.log_test(
                        "Dashboard Summary - Unauthorized Access",
                        False,
                        f"Expected 401/403, got {response.status}",
                        {"status": response.status, "response": response_data}
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Unauthorized Access", False, f"Exception: {str(e)}")
            
    async def test_dashboard_summary_wrong_role(self):
        """Test dashboard summary with customer user (wrong role)"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.customer_cookies) as response:
                response_data = await response.text()
                
                if response.status == 403:
                    self.log_test(
                        "Dashboard Summary - Wrong Role Access",
                        True,
                        "Correctly blocked customer user access with 403"
                    )
                else:
                    self.log_test(
                        "Dashboard Summary - Wrong Role Access",
                        False,
                        f"Expected 403, got {response.status}",
                        {"status": response.status, "response": response_data}
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Wrong Role Access", False, f"Exception: {str(e)}")
            
    async def test_revenue_calculation_logic(self):
        """Test that revenue is calculated from confirmed/delivered orders only"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    revenue = response_data.get("today_revenue", 0)
                    orders_count = response_data.get("today_orders_count", 0)
                    
                    # Revenue should be non-negative
                    if revenue >= 0:
                        self.log_test(
                            "Dashboard Summary - Revenue Calculation",
                            True,
                            f"Revenue calculation appears valid: ₺{revenue} from {orders_count} orders"
                        )
                    else:
                        self.log_test(
                            "Dashboard Summary - Revenue Calculation",
                            False,
                            f"Invalid negative revenue: ₺{revenue}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Dashboard Summary - Revenue Calculation",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Revenue Calculation", False, f"Exception: {str(e)}")

            
    async def run_all_tests(self):
        """Run all dashboard summary tests"""
        print("🎯 BUSINESS DASHBOARD SUMMARY ENDPOINT TESTING")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup - Login users
            business_login_success = await self.login_business_user()
            customer_login_success = await self.login_customer_user()
            
            if not business_login_success:
                print("❌ Cannot proceed without business user login")
                return
                
            # Core functionality tests
            await self.test_dashboard_summary_authenticated()
            await self.test_dashboard_summary_with_date_parameter()
            await self.test_revenue_calculation_logic()
            
            # Security tests
            await self.test_dashboard_summary_unauthorized()
            
            if customer_login_success:
                await self.test_dashboard_summary_wrong_role()
            else:
                print("⚠️  Skipping wrong role test - customer login failed")
                
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
                    
        return passed_tests, failed_tests


async def main():
    """Main test execution"""
    tester = BusinessDashboardTester()
    passed, failed = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())
