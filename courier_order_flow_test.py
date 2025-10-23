#!/usr/bin/env python3
"""
Courier Order Flow Testing - Ready Orders Appearing in Courier Map
Testing the specific issue reported: "İşletmedeki hazır siparişler kurye harita kısmına düşmüyor"

CRITICAL CONTEXT:
- User reports: "İşletmedeki hazır siparişler kurye harita kısmına düşmüyor"
- When business sets order to "ready", it should appear in courier map
- Need to verify full flow: business → ready status → courier sees it

TEST REQUIREMENTS:
1. Create Test Order - Login as customer and create order with business e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed
2. Business Confirms and Makes Ready - Login as business and update status: pending → confirmed → ready
3. Verify Ready Order in Database - Check orders collection for order with status="ready"
4. Test Courier Map Endpoint - GET /api/courier/tasks/nearby-businesses should show business with pending_ready_count > 0
5. Test Available Orders Endpoint - GET /api/courier/tasks/businesses/{business_id}/available-orders should return the "ready" order

SUCCESS CRITERIA:
- ✅ Order created successfully
- ✅ Business can update to "ready" status
- ✅ Order appears in database with status="ready"
- ✅ Business appears in nearby-businesses with count > 0
- ✅ Order appears in available-orders endpoint

TEST CREDENTIALS:
- Customer: test@kuryecini.com / test123
- Business: testbusiness@example.com / test123 (ID: e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed)
- Courier: testkurye@example.com / test123

BACKEND URL: https://courier-dashboard-3.preview.emergentagent.com/api
"""

import requests
import json
import time
from datetime import datetime, timezone
import sys
import uuid

# Configuration
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "test@kuryecini.com"
TEST_CUSTOMER_PASSWORD = "test123"
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"
TEST_BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"
TEST_COURIER_EMAIL = "testkurye@example.com"
TEST_COURIER_PASSWORD = "test123"

class CourierOrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CourierOrderFlowTester/1.0'
        })
        self.test_results = []
        self.test_order_id = None
        self.customer_session = requests.Session()
        self.business_session = requests.Session()
        self.courier_session = requests.Session()
        
        # Set headers for all sessions
        for session in [self.customer_session, self.business_session, self.courier_session]:
            session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'CourierOrderFlowTester/1.0'
            })
        
    def log_test(self, test_name, success, details, response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   Details: {details}")
        print()
        
    def test_customer_login(self):
        """Test 1: Customer Login"""
        print("👤 Testing Customer Login...")
        
        start_time = time.time()
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.customer_session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('user'):
                    user = data['user']
                    if user.get('role') == 'customer':
                        self.log_test(
                            "Customer Login",
                            True,
                            f"Customer login successful. User ID: {user.get('id')}, Email: {user.get('email')}",
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Customer Login",
                            False,
                            f"Wrong role: {user.get('role')}, expected 'customer'",
                            response_time
                        )
                        return False
                else:
                    self.log_test(
                        "Customer Login",
                        False,
                        f"Login response missing data: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Customer Login",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Customer Login",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_create_order(self):
        """Test 2: Create Test Order"""
        print("📦 Testing Order Creation...")
        
        start_time = time.time()
        try:
            # First, get business menu to create a valid order
            menu_response = self.customer_session.get(
                f"{BACKEND_URL}/business/public/{TEST_BUSINESS_ID}/menu",
                timeout=10
            )
            
            if menu_response.status_code != 200:
                self.log_test(
                    "Create Test Order",
                    False,
                    f"Failed to get business menu: HTTP {menu_response.status_code}",
                    time.time() - start_time
                )
                return False
            
            menu_items = menu_response.json()
            
            if not menu_items or not isinstance(menu_items, list):
                self.log_test(
                    "Create Test Order",
                    False,
                    f"No menu items found for business {TEST_BUSINESS_ID}. Response: {menu_items}",
                    time.time() - start_time
                )
                return False
            
            # Use first menu item for order
            first_item = menu_items[0]
            
            # Create order data
            order_data = {
                "business_id": TEST_BUSINESS_ID,
                "delivery_address": "Test Address, Aksaray, Turkey",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0254,
                "items": [
                    {
                        "product_id": first_item.get('id'),
                        "title": first_item.get('name', 'Test Item'),
                        "price": float(first_item.get('price', 25.0)),
                        "quantity": 1
                    }
                ],
                "total_amount": float(first_item.get('price', 25.0)),
                "payment_method": "cash_on_delivery",
                "notes": "Test order for courier flow testing"
            }
            
            response = self.customer_session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for order ID in different possible locations
                order_id = None
                if data.get('order_id'):
                    order_id = data['order_id']
                elif data.get('order', {}).get('id'):
                    order_id = data['order']['id']
                elif data.get('id'):
                    order_id = data['id']
                
                if order_id:
                    self.test_order_id = order_id
                    order_data = data.get('order', data)
                    self.log_test(
                        "Create Test Order",
                        True,
                        f"Order created successfully. Order ID: {self.test_order_id}, Business ID: {order_data.get('business_id')}, Total: {order_data.get('totals', {}).get('grand', 'N/A')}",
                        response_time
                    )
                    return True
                else:
                    self.log_test(
                        "Create Test Order",
                        False,
                        f"Order creation response missing order_id: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Create Test Order",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Create Test Order",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_business_login(self):
        """Test 3: Business Login"""
        print("🏪 Testing Business Login...")
        
        start_time = time.time()
        try:
            login_data = {
                "email": TEST_BUSINESS_EMAIL,
                "password": TEST_BUSINESS_PASSWORD
            }
            
            response = self.business_session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('user'):
                    user = data['user']
                    if user.get('role') == 'business' and user.get('id') == TEST_BUSINESS_ID:
                        self.log_test(
                            "Business Login",
                            True,
                            f"Business login successful. Business ID: {user.get('id')}, Name: {user.get('business_name', 'N/A')}",
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Business Login",
                            False,
                            f"Wrong role or ID: role={user.get('role')}, id={user.get('id')}, expected business/{TEST_BUSINESS_ID}",
                            response_time
                        )
                        return False
                else:
                    self.log_test(
                        "Business Login",
                        False,
                        f"Login response missing data: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Business Login",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Business Login",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_business_order_status_updates(self):
        """Test 4: Business Updates Order Status to Ready"""
        print("📋 Testing Business Order Status Updates...")
        
        if not self.test_order_id:
            self.log_test(
                "Business Order Status Updates",
                False,
                "No test order ID available - order creation failed",
                0
            )
            return False
        
        # Step 1: Update to confirmed
        start_time = time.time()
        try:
            status_data = {"status": "confirmed"}
            
            response = self.business_session.patch(
                f"{BACKEND_URL}/business/orders/{self.test_order_id}/status",
                json=status_data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "Business Order Status Updates - Confirmed",
                    False,
                    f"Failed to update to confirmed: HTTP {response.status_code}: {response.text}",
                    time.time() - start_time
                )
                return False
            
            # Step 2: Update to ready
            status_data = {"status": "ready"}
            
            response = self.business_session.patch(
                f"{BACKEND_URL}/business/orders/{self.test_order_id}/status",
                json=status_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('new_status') == 'ready':
                    self.log_test(
                        "Business Order Status Updates",
                        True,
                        f"Order status updated to ready successfully. Order ID: {self.test_order_id}, Status: {data.get('new_status')}",
                        response_time
                    )
                    return True
                else:
                    self.log_test(
                        "Business Order Status Updates",
                        False,
                        f"Status update response unexpected: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Business Order Status Updates",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Business Order Status Updates",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_verify_ready_order_in_database(self):
        """Test 5: Verify Ready Order in Database"""
        print("🗄️ Testing Ready Order in Database...")
        
        if not self.test_order_id:
            self.log_test(
                "Verify Ready Order in Database",
                False,
                "No test order ID available",
                0
            )
            return False
        
        start_time = time.time()
        try:
            # Get order details to verify status - use customer session since it's their order
            response = self.customer_session.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}/track",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ready' and data.get('business_id') == TEST_BUSINESS_ID:
                    self.log_test(
                        "Verify Ready Order in Database",
                        True,
                        f"Order verified in database. ID: {data.get('id')}, Status: {data.get('status')}, Business ID: {data.get('business_id')}",
                        response_time
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Ready Order in Database",
                        False,
                        f"Order status or business_id incorrect: status={data.get('status')}, business_id={data.get('business_id')}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Verify Ready Order in Database",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Verify Ready Order in Database",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_courier_login(self):
        """Test 6: Courier Login"""
        print("🚚 Testing Courier Login...")
        
        start_time = time.time()
        try:
            login_data = {
                "email": TEST_COURIER_EMAIL,
                "password": TEST_COURIER_PASSWORD
            }
            
            response = self.courier_session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('user'):
                    user = data['user']
                    if user.get('role') == 'courier':
                        self.log_test(
                            "Courier Login",
                            True,
                            f"Courier login successful. User ID: {user.get('id')}, Email: {user.get('email')}",
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Courier Login",
                            False,
                            f"Wrong role: {user.get('role')}, expected 'courier'",
                            response_time
                        )
                        return False
                else:
                    self.log_test(
                        "Courier Login",
                        False,
                        f"Login response missing data: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Courier Login",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Courier Login",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_courier_nearby_businesses(self):
        """Test 7: Courier Map Endpoint - Nearby Businesses"""
        print("🗺️ Testing Courier Map Endpoint - Nearby Businesses...")
        
        start_time = time.time()
        try:
            # Test the specific endpoint mentioned in review request
            params = {
                'lng': 32.8597,
                'lat': 39.9334,
                'radius_m': 50000
            }
            
            response = self.courier_session.get(
                f"{BACKEND_URL}/courier/tasks/nearby-businesses",
                params=params,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                businesses = response.json()
                
                # Ensure it's a list
                if not isinstance(businesses, list):
                    self.log_test(
                        "Courier Map Endpoint - Nearby Businesses",
                        False,
                        f"Unexpected response format: {businesses}",
                        response_time
                    )
                    return False
                
                # Look for our test business in the results
                test_business_found = False
                test_business_data = None
                
                for business in businesses:
                    if business.get('id') == TEST_BUSINESS_ID:
                        test_business_found = True
                        test_business_data = business
                        break
                
                if test_business_found:
                    pending_ready_count = test_business_data.get('pending_ready_count', 0)
                    if pending_ready_count > 0:
                        self.log_test(
                            "Courier Map Endpoint - Nearby Businesses",
                            True,
                            f"Business found in nearby results with ready orders. Business ID: {TEST_BUSINESS_ID}, Ready orders count: {pending_ready_count}",
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Courier Map Endpoint - Nearby Businesses",
                            False,
                            f"Business found but no ready orders count: {pending_ready_count}. Business data: {test_business_data}",
                            response_time
                        )
                        return False
                else:
                    # Check if there are any businesses at all
                    if len(businesses) == 0:
                        self.log_test(
                            "Courier Map Endpoint - Nearby Businesses",
                            False,
                            f"No businesses found in nearby area. This could indicate the business location is outside the search radius or the endpoint is not working correctly.",
                            response_time
                        )
                    else:
                        self.log_test(
                            "Courier Map Endpoint - Nearby Businesses",
                            False,
                            f"Test business {TEST_BUSINESS_ID} not found in nearby businesses. Found {len(businesses)} businesses: {[b.get('id') for b in businesses]}",
                            response_time
                        )
                    return False
            else:
                self.log_test(
                    "Courier Map Endpoint - Nearby Businesses",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Courier Map Endpoint - Nearby Businesses",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_courier_available_orders(self):
        """Test 8: Available Orders Endpoint"""
        print("📋 Testing Available Orders Endpoint...")
        
        start_time = time.time()
        try:
            response = self.courier_session.get(
                f"{BACKEND_URL}/courier/tasks/businesses/{TEST_BUSINESS_ID}/available-orders",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                orders = data.get('orders', [])
                test_order_found = False
                test_order_data = None
                
                for order in orders:
                    if order.get('id') == self.test_order_id or order.get('order_id') == self.test_order_id:
                        test_order_found = True
                        test_order_data = order
                        break
                
                if test_order_found:
                    if test_order_data.get('status') == 'ready':
                        self.log_test(
                            "Available Orders Endpoint",
                            True,
                            f"Ready order found in available orders. Order ID: {self.test_order_id}, Status: {test_order_data.get('status')}, Business ID: {test_order_data.get('business_id', 'N/A')}",
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Available Orders Endpoint",
                            False,
                            f"Order found but wrong status: {test_order_data.get('status')}, expected 'ready'",
                            response_time
                        )
                        return False
                else:
                    self.log_test(
                        "Available Orders Endpoint",
                        False,
                        f"Test order {self.test_order_id} not found in available orders. Found {len(orders)} orders: {[o.get('id') or o.get('order_id') for o in orders]}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Available Orders Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Available Orders Endpoint",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def run_all_tests(self):
        """Run all courier order flow tests"""
        print("🎯 COURIER ORDER FLOW TESTING - READY ORDERS IN MAP")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
        print(f"Test Business: {TEST_BUSINESS_EMAIL} (ID: {TEST_BUSINESS_ID})")
        print(f"Test Courier: {TEST_COURIER_EMAIL}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        # Test 1: Customer Login
        customer_login_success = self.test_customer_login()
        
        # Test 2: Create Order
        order_creation_success = False
        if customer_login_success:
            order_creation_success = self.test_create_order()
        else:
            print("❌ Skipping order creation due to customer login failure")
        
        # Test 3: Business Login
        business_login_success = self.test_business_login()
        
        # Test 4: Business Updates Order Status
        status_update_success = False
        if business_login_success and order_creation_success:
            status_update_success = self.test_business_order_status_updates()
        else:
            print("❌ Skipping status updates due to business login or order creation failure")
        
        # Test 5: Verify Ready Order in Database
        database_verification_success = False
        if status_update_success:
            database_verification_success = self.test_verify_ready_order_in_database()
        else:
            print("❌ Skipping database verification due to status update failure")
        
        # Test 6: Courier Login
        courier_login_success = self.test_courier_login()
        
        # Test 7: Courier Map Endpoint
        courier_map_success = False
        if courier_login_success and database_verification_success:
            courier_map_success = self.test_courier_nearby_businesses()
        else:
            print("❌ Skipping courier map test due to courier login or database verification failure")
        
        # Test 8: Available Orders Endpoint
        available_orders_success = False
        if courier_login_success and database_verification_success:
            available_orders_success = self.test_courier_available_orders()
        else:
            print("❌ Skipping available orders test due to courier login or database verification failure")
        
        # Summary
        self.print_summary()
        
        return all([
            customer_login_success,
            order_creation_success,
            business_login_success,
            status_update_success,
            database_verification_success,
            courier_login_success,
            courier_map_success,
            available_orders_success
        ])
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print individual test results
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if not result['success']:
                print(f"   ❌ {result['details']}")
        print()
        
        # Critical findings for the specific issue
        print("🎯 CRITICAL FINDINGS FOR COURIER MAP ISSUE:")
        print("   Issue: İşletmedeki hazır siparişler kurye harita kısmına düşmüyor")
        print()
        
        # Check each step of the flow
        order_creation = next((r for r in self.test_results if 'Create Test Order' in r['test']), None)
        status_update = next((r for r in self.test_results if 'Business Order Status Updates' in r['test']), None)
        database_verification = next((r for r in self.test_results if 'Verify Ready Order in Database' in r['test']), None)
        courier_map = next((r for r in self.test_results if 'Courier Map Endpoint' in r['test']), None)
        available_orders = next((r for r in self.test_results if 'Available Orders Endpoint' in r['test']), None)
        
        if order_creation and order_creation['success']:
            print("   ✅ Step 1: Order creation is working")
        else:
            print("   ❌ Step 1: Order creation is failing")
            
        if status_update and status_update['success']:
            print("   ✅ Step 2: Business can update order status to 'ready'")
        else:
            print("   ❌ Step 2: Business cannot update order status to 'ready'")
            
        if database_verification and database_verification['success']:
            print("   ✅ Step 3: Ready orders are saved correctly in database")
        else:
            print("   ❌ Step 3: Ready orders are not saved correctly in database")
            
        if courier_map and courier_map['success']:
            print("   ✅ Step 4: Ready orders appear in courier nearby-businesses endpoint")
        else:
            print("   ❌ Step 4: Ready orders DO NOT appear in courier nearby-businesses endpoint")
            
        if available_orders and available_orders['success']:
            print("   ✅ Step 5: Ready orders appear in courier available-orders endpoint")
        else:
            print("   ❌ Step 5: Ready orders DO NOT appear in courier available-orders endpoint")
        
        print()
        
        # Root cause analysis
        if success_rate >= 80:
            print("   🎉 CONCLUSION: Order flow is working correctly!")
            print("   The issue 'İşletmedeki hazır siparişler kurye harita kısmına düşmüyor' appears to be resolved.")
        else:
            print("   🚨 CONCLUSION: Order flow has issues!")
            print("   The issue 'İşletmedeki hazır siparişler kurye harita kısmına düşmüyor' is confirmed.")
            print()
            print("   🔍 ROOT CAUSE ANALYSIS:")
            
            if not (order_creation and order_creation['success']):
                print("   - Order creation is failing - check customer authentication and order API")
            if not (status_update and status_update['success']):
                print("   - Business status updates are failing - check business authentication and status update API")
            if not (database_verification and database_verification['success']):
                print("   - Database is not storing ready orders correctly - check order status persistence")
            if not (courier_map and courier_map['success']):
                print("   - Courier map endpoint is not showing ready orders - check nearby-businesses API logic")
            if not (available_orders and available_orders['success']):
                print("   - Available orders endpoint is not working - check available-orders API logic")
        
        print("\n" + "=" * 70)
        
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = CourierOrderFlowTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()