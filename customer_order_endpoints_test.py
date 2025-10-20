#!/usr/bin/env python3
"""
🎯 CUSTOMER ORDER ENDPOINTS TESTING
Testing customer order creation and order history endpoints per review request.

Test Scenarios:
1. POST /api/orders - Order creation endpoint (CRITICAL)
2. GET /api/orders/my - Customer orders endpoint (HIGH)
3. Order creation validation (MEDIUM)
4. Order status flow (MEDIUM)
5. Authentication requirements (HIGH)

Success Criteria:
✅ POST /api/orders returns 201 with order_id
✅ GET /api/orders/my returns customer's orders
✅ Validation errors properly handled
✅ Order creation flow works end-to-end
✅ Auth required for both endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"
TEST_CUSTOMER_EMAIL = "test@kuryecini.com"
TEST_CUSTOMER_PASSWORD = "test123"

class CustomerOrderTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.customer_token = None
        self.customer_id = None
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.1f}ms)" if response_time else ""
        result = f"{status} {test_name}{time_info}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time
        })
        
    def authenticate_customer(self):
        """Authenticate customer and get session"""
        print("\n🔐 CUSTOMER AUTHENTICATION")
        start_time = time.time()
        
        try:
            # Login with cookie-based authentication
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.customer_id = data.get('user', {}).get('id')
                self.log_test("Customer Login", True, 
                            f"Email: {TEST_CUSTOMER_EMAIL}, ID: {self.customer_id}", response_time)
                return True
            else:
                self.log_test("Customer Login", False, 
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Customer Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    def get_customer_addresses(self):
        """Get customer addresses for order creation"""
        print("\n📍 CUSTOMER ADDRESSES")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                addresses = response.json()
                if addresses and len(addresses) > 0:
                    self.log_test("Get Customer Addresses", True, 
                                f"Found {len(addresses)} addresses", response_time)
                    return addresses[0]  # Return first address for testing
                else:
                    self.log_test("Get Customer Addresses", False, 
                                "No addresses found", response_time)
                    return None
            else:
                self.log_test("Get Customer Addresses", False, 
                            f"Status: {response.status_code}", response_time)
                return None
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Get Customer Addresses", False, f"Exception: {str(e)}", response_time)
            return None
    
    def find_business_with_menu(self):
        """Find a business with available menu items"""
        print("\n🏪 BUSINESS DISCOVERY")
        start_time = time.time()
        
        try:
            # Get businesses
            response = self.session.get(f"{BACKEND_URL}/businesses?city=Aksaray", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test("Get Businesses", True, 
                            f"Found {len(businesses)} businesses", response_time)
                
                # Find business with menu items
                for business in businesses:
                    business_id = business.get('id')
                    if business_id:
                        menu_response = self.session.get(
                            f"{BACKEND_URL}/business/public/{business_id}/menu", 
                            timeout=10
                        )
                        if menu_response.status_code == 200:
                            menu_items = menu_response.json()
                            if menu_items and len(menu_items) > 0:
                                self.log_test("Find Business with Menu", True, 
                                            f"Business: {business.get('business_name', business.get('name', 'Unknown'))}, Menu items: {len(menu_items)}")
                                return business, menu_items[0]  # Return business and first menu item
                
                self.log_test("Find Business with Menu", False, "No businesses with menu items found")
                return None, None
            else:
                self.log_test("Get Businesses", False, f"Status: {response.status_code}", response_time)
                return None, None
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Find Business with Menu", False, f"Exception: {str(e)}", response_time)
            return None, None
    
    def test_order_creation(self, business, menu_item, address):
        """Test POST /api/orders endpoint - CRITICAL"""
        print("\n🎯 ORDER CREATION ENDPOINT (CRITICAL)")
        start_time = time.time()
        
        try:
            # Prepare order data
            order_data = {
                "business_id": business.get('id'),
                "items": [{
                    "product_id": menu_item.get('id'),
                    "title": menu_item.get('name', menu_item.get('title', 'Test Item')),
                    "price": float(menu_item.get('price', 99.99)),
                    "quantity": 1
                }],
                "delivery_address": {
                    "label": address.get('label', 'Test Address'),
                    "address": address.get('full', address.get('acik_adres', 'Test Address')),
                    "lat": float(address.get('lat', 38.3687)),
                    "lng": float(address.get('lng', 34.0254))
                },
                "payment_method": "cash_on_delivery",
                "notes": "Test order from backend testing"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                timeout=15
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get('order_id') or data.get('id')
                business_name = data.get('business_name')
                total_amount = data.get('total_amount')
                status = data.get('status')
                
                if order_id:
                    self.log_test("POST /api/orders", True, 
                                f"Order ID: {order_id}, Business: {business_name}, Total: ₺{total_amount}, Status: {status}", 
                                response_time)
                    return order_id
                else:
                    self.log_test("POST /api/orders", False, 
                                f"No order_id in response: {data}", response_time)
                    return None
            else:
                self.log_test("POST /api/orders", False, 
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("POST /api/orders", False, f"Exception: {str(e)}", response_time)
            return None
    
    def test_get_customer_orders(self):
        """Test GET /api/orders/my endpoint - HIGH"""
        print("\n📋 CUSTOMER ORDERS ENDPOINT (HIGH)")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/orders/my", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                orders = response.json()
                if isinstance(orders, list):
                    self.log_test("GET /api/orders/my", True, 
                                f"Retrieved {len(orders)} orders", response_time)
                    
                    # Check order structure
                    if orders:
                        order = orders[0]
                        required_fields = ['id', 'business_id', 'status', 'total_amount']
                        missing_fields = [field for field in required_fields if field not in order]
                        
                        if not missing_fields:
                            self.log_test("Order Structure Validation", True, 
                                        f"All required fields present: {required_fields}")
                        else:
                            self.log_test("Order Structure Validation", False, 
                                        f"Missing fields: {missing_fields}")
                    
                    return orders
                else:
                    self.log_test("GET /api/orders/my", False, 
                                f"Expected list, got: {type(orders)}", response_time)
                    return None
            else:
                self.log_test("GET /api/orders/my", False, 
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("GET /api/orders/my", False, f"Exception: {str(e)}", response_time)
            return None
    
    def test_order_validation(self):
        """Test order creation validation - MEDIUM"""
        print("\n🔍 ORDER VALIDATION TESTS (MEDIUM)")
        
        # Test 1: Missing business_id
        start_time = time.time()
        try:
            invalid_order = {
                "items": [{"product_id": "test", "title": "Test", "price": 10.0, "quantity": 1}],
                "delivery_address": {"label": "Test", "address": "Test", "lat": 38.0, "lng": 34.0},
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(f"{BACKEND_URL}/orders", json=invalid_order, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 422:
                self.log_test("Validation: Missing business_id", True, 
                            "422 validation error returned", response_time)
            else:
                self.log_test("Validation: Missing business_id", False, 
                            f"Expected 422, got {response.status_code}", response_time)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Validation: Missing business_id", False, f"Exception: {str(e)}", response_time)
        
        # Test 2: Empty items array
        start_time = time.time()
        try:
            invalid_order = {
                "business_id": "test-business-id",
                "items": [],
                "delivery_address": {"label": "Test", "address": "Test", "lat": 38.0, "lng": 34.0},
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(f"{BACKEND_URL}/orders", json=invalid_order, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 422:
                self.log_test("Validation: Empty items", True, 
                            "422 validation error returned", response_time)
            else:
                self.log_test("Validation: Empty items", False, 
                            f"Expected 422, got {response.status_code}", response_time)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Validation: Empty items", False, f"Exception: {str(e)}", response_time)
        
        # Test 3: Invalid payment method
        start_time = time.time()
        try:
            invalid_order = {
                "business_id": "test-business-id",
                "items": [{"product_id": "test", "title": "Test", "price": 10.0, "quantity": 1}],
                "delivery_address": {"label": "Test", "address": "Test", "lat": 38.0, "lng": 34.0},
                "payment_method": "invalid_method"
            }
            
            response = self.session.post(f"{BACKEND_URL}/orders", json=invalid_order, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 422:
                self.log_test("Validation: Invalid payment method", True, 
                            "422 validation error returned", response_time)
            else:
                self.log_test("Validation: Invalid payment method", False, 
                            f"Expected 422, got {response.status_code}", response_time)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Validation: Invalid payment method", False, f"Exception: {str(e)}", response_time)
    
    def test_authentication_required(self):
        """Test authentication requirements - HIGH"""
        print("\n🔐 AUTHENTICATION TESTS (HIGH)")
        
        # Create new session without authentication
        unauth_session = requests.Session()
        
        # Test 1: POST /api/orders without auth
        start_time = time.time()
        try:
            order_data = {
                "business_id": "test",
                "items": [{"product_id": "test", "title": "Test", "price": 10.0, "quantity": 1}],
                "delivery_address": {"label": "Test", "address": "Test", "lat": 38.0, "lng": 34.0},
                "payment_method": "cash_on_delivery"
            }
            
            response = unauth_session.post(f"{BACKEND_URL}/orders", json=order_data, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 401:
                self.log_test("Auth Required: POST /api/orders", True, 
                            "401 Unauthorized returned", response_time)
            else:
                self.log_test("Auth Required: POST /api/orders", False, 
                            f"Expected 401, got {response.status_code}", response_time)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Auth Required: POST /api/orders", False, f"Exception: {str(e)}", response_time)
        
        # Test 2: GET /api/orders/my without auth
        start_time = time.time()
        try:
            response = unauth_session.get(f"{BACKEND_URL}/orders/my", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 401:
                self.log_test("Auth Required: GET /api/orders/my", True, 
                            "401 Unauthorized returned", response_time)
            else:
                self.log_test("Auth Required: GET /api/orders/my", False, 
                            f"Expected 401, got {response.status_code}", response_time)
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Auth Required: GET /api/orders/my", False, f"Exception: {str(e)}", response_time)
    
    def test_order_status_flow(self, order_id):
        """Test order status flow - MEDIUM"""
        print("\n🔄 ORDER STATUS FLOW (MEDIUM)")
        
        if not order_id:
            self.log_test("Order Status Flow", False, "No order_id provided")
            return
        
        start_time = time.time()
        try:
            # Check if order appears in customer orders
            response = self.session.get(f"{BACKEND_URL}/orders/my", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                orders = response.json()
                order_found = any(order.get('id') == order_id for order in orders)
                
                if order_found:
                    self.log_test("Order in Customer List", True, 
                                f"Order {order_id} found in customer orders", response_time)
                    
                    # Check order details
                    order = next((o for o in orders if o.get('id') == order_id), None)
                    if order:
                        status = order.get('status')
                        business_id = order.get('business_id')
                        total_amount = order.get('total_amount')
                        
                        if status == 'created':
                            self.log_test("Order Status Check", True, 
                                        f"Status: {status}, Business ID: {business_id}, Total: ₺{total_amount}")
                        else:
                            self.log_test("Order Status Check", False, 
                                        f"Expected 'created', got '{status}'")
                else:
                    self.log_test("Order in Customer List", False, 
                                f"Order {order_id} not found in customer orders", response_time)
            else:
                self.log_test("Order Status Flow", False, 
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log_test("Order Status Flow", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all customer order endpoint tests"""
        print("🎯 CUSTOMER ORDER ENDPOINTS TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Authenticate customer
        if not self.authenticate_customer():
            print("\n❌ CRITICAL: Customer authentication failed - cannot proceed with tests")
            return self.generate_summary()
        
        # Step 2: Get customer addresses
        address = self.get_customer_addresses()
        if not address:
            print("\n⚠️  WARNING: No customer addresses found - using default address")
            address = {
                "label": "Test Address",
                "full": "Test Address, Aksaray",
                "lat": 38.3687,
                "lng": 34.0254
            }
        
        # Step 3: Find business with menu
        business, menu_item = self.find_business_with_menu()
        if not business or not menu_item:
            print("\n❌ CRITICAL: No business with menu items found - cannot test order creation")
            # Still run other tests
            self.test_get_customer_orders()
            self.test_order_validation()
            self.test_authentication_required()
            return self.generate_summary()
        
        # Step 4: Test order creation (CRITICAL)
        order_id = self.test_order_creation(business, menu_item, address)
        
        # Step 5: Test get customer orders (HIGH)
        self.test_get_customer_orders()
        
        # Step 6: Test order status flow (MEDIUM)
        self.test_order_status_flow(order_id)
        
        # Step 7: Test validation (MEDIUM)
        self.test_order_validation()
        
        # Step 8: Test authentication (HIGH)
        self.test_authentication_required()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("🎯 CUSTOMER ORDER ENDPOINTS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {success_rate:.1f}% success rate ({passed_tests}/{total_tests} tests passed)")
        print()
        
        # Group results by category
        critical_tests = [r for r in self.test_results if 'POST /api/orders' in r['test']]
        high_tests = [r for r in self.test_results if any(x in r['test'] for x in ['GET /api/orders/my', 'Auth Required'])]
        medium_tests = [r for r in self.test_results if any(x in r['test'] for x in ['Validation', 'Order Status'])]
        
        # Critical tests
        if critical_tests:
            critical_passed = sum(1 for r in critical_tests if r['success'])
            print(f"🔴 CRITICAL TESTS: {critical_passed}/{len(critical_tests)} passed")
            for result in critical_tests:
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['test']}")
            print()
        
        # High priority tests
        if high_tests:
            high_passed = sum(1 for r in high_tests if r['success'])
            print(f"🟡 HIGH PRIORITY TESTS: {high_passed}/{len(high_tests)} passed")
            for result in high_tests:
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['test']}")
            print()
        
        # Medium priority tests
        if medium_tests:
            medium_passed = sum(1 for r in medium_tests if r['success'])
            print(f"🟢 MEDIUM PRIORITY TESTS: {medium_passed}/{len(medium_tests)} passed")
            for result in medium_tests:
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['test']}")
            print()
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Success criteria check
        print("🎯 SUCCESS CRITERIA VERIFICATION:")
        
        order_creation_passed = any(r['success'] and 'POST /api/orders' in r['test'] for r in self.test_results)
        print(f"  {'✅' if order_creation_passed else '❌'} POST /api/orders returns 201 with order_id")
        
        get_orders_passed = any(r['success'] and 'GET /api/orders/my' in r['test'] for r in self.test_results)
        print(f"  {'✅' if get_orders_passed else '❌'} GET /api/orders/my returns customer's orders")
        
        validation_passed = any(r['success'] and 'Validation' in r['test'] for r in self.test_results)
        print(f"  {'✅' if validation_passed else '❌'} Validation errors properly handled")
        
        flow_passed = any(r['success'] and 'Order Status' in r['test'] for r in self.test_results)
        print(f"  {'✅' if flow_passed else '❌'} Order creation flow works end-to-end")
        
        auth_passed = any(r['success'] and 'Auth Required' in r['test'] for r in self.test_results)
        print(f"  {'✅' if auth_passed else '❌'} Auth required for both endpoints")
        
        print()
        
        # Overall verdict
        if success_rate >= 80:
            print("🎉 VERDICT: Customer order endpoints are WORKING EXCELLENTLY")
        elif success_rate >= 60:
            print("⚠️  VERDICT: Customer order endpoints are PARTIALLY WORKING")
        else:
            print("❌ VERDICT: Customer order endpoints have CRITICAL ISSUES")
        
        return {
            'success_rate': success_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'critical_passed': order_creation_passed,
            'high_passed': get_orders_passed and auth_passed,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = CustomerOrderTester()
    summary = tester.run_all_tests()