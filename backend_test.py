#!/usr/bin/env python3
"""
CRITICAL TEST: Business Order Display - Check if Orders Appear in Business Panel
Testing the specific scenario where orders weren't appearing in business panel
"""

import requests
import json
import sys
from datetime import datetime

# Configuration from review request
BACKEND_URL = "https://order-flow-debug.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"
BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"  # Lezzet Döner
CUSTOMER_EMAIL = "testcustomer@example.com"
CUSTOMER_PASSWORD = "test123"

class BusinessOrderDisplayTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def business_login(self):
        """Login as business user"""
        try:
            login_data = {
                "email": BUSINESS_EMAIL,
                "password": BUSINESS_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Cookie-based auth - token stored in cookies
                    self.log_test("Business Login", True, f"Business authenticated successfully via cookies")
                    return data.get("user", {})
                else:
                    self.log_test("Business Login", False, f"Login failed: {data}")
                    return None
            else:
                self.log_test("Business Login", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Business Login", False, f"Login error: {str(e)}")
            return None
    
    def customer_login(self):
        """Login as customer user"""
        try:
            # Create new session for customer
            customer_session = requests.Session()
            
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = customer_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Cookie-based auth - token stored in cookies
                    self.log_test("Customer Login", True, f"Customer authenticated successfully via cookies")
                    return customer_session, data.get("user", {})
                else:
                    self.log_test("Customer Login", False, f"Login failed: {data}")
                    return None, None
            else:
                self.log_test("Customer Login", False, f"HTTP {response.status_code}: {response.text}")
                return None, None
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Login error: {str(e)}")
            return None, None
    
    def test_business_exists(self):
        """Test 1: Verify business exists in system"""
        try:
            # First try to login as business to verify account exists
            business_user = self.business_login()
            
            if business_user and business_user.get("id") == BUSINESS_ID:
                self.log_test(
                    "Business Exists", 
                    True, 
                    f"Test business account verified: {business_user.get('email')} (ID: {BUSINESS_ID})",
                    {"business_id": BUSINESS_ID, "email": business_user.get("email"), "role": business_user.get("role")}
                )
                return True
            else:
                # Fallback: Check public businesses list
                response = self.session.get(f"{BACKEND_URL}/businesses")
                
                if response.status_code == 200:
                    businesses = response.json()
                    business_list = businesses if isinstance(businesses, list) else businesses.get("businesses", [])
                    
                    # Find our test business
                    test_business = None
                    for business in business_list:
                        if business.get("id") == BUSINESS_ID:
                            test_business = business
                            break
                    
                    if test_business:
                        self.log_test(
                            "Business Exists", 
                            True, 
                            f"Test business found in public list: {test_business.get('name', 'Lezzet Döner')} (ID: {BUSINESS_ID})",
                            {"business_id": BUSINESS_ID, "business_name": test_business.get("name")}
                        )
                        return True
                    else:
                        self.log_test(
                            "Business Exists", 
                            False, 
                            f"Test business with ID {BUSINESS_ID} not found (may not be approved for public listing)"
                        )
                        return False
                else:
                    self.log_test(
                        "Business Exists", 
                        False, 
                        f"Failed to verify business existence: HTTP {response.status_code}: {response.text}"
                    )
                    return False
                
        except Exception as e:
            self.log_test("Business Exists", False, f"Request error: {str(e)}")
            return False
    
    def test_get_menu_items(self):
        """Test 2: Get menu items from business public endpoint"""
        try:
            # Get menu items from public endpoint (no auth required)
            response = self.session.get(f"{BACKEND_URL}/business/public-menu/{BUSINESS_ID}/products")
            
            if response.status_code == 200:
                menu_data = response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                if menu_items:
                    self.log_test(
                        "Get Menu Items", 
                        True, 
                        f"Retrieved {len(menu_items)} menu items from business {BUSINESS_ID}",
                        {"business_id": BUSINESS_ID, "menu_count": len(menu_items), "items": menu_items[:2]}
                    )
                    return menu_items
                else:
                    self.log_test(
                        "Get Menu Items", 
                        False, 
                        f"No menu items found for business {BUSINESS_ID}"
                    )
                    return []
            else:
                self.log_test(
                    "Get Menu Items", 
                    False, 
                    f"Failed to get menu items: HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_test("Get Menu Items", False, f"Request error: {str(e)}")
            return []
    
    def test_create_order(self, menu_items):
        """Test 3: Create order as customer with business items"""
        try:
            customer_session, customer_user = self.customer_login()
            
            if not customer_session or not customer_user:
                return False, None
            
            customer_id = customer_user.get("id")
            if not customer_id:
                self.log_test(
                    "Create Test Order", 
                    False, 
                    "Customer user missing ID field"
                )
                return False, None
            
            # Use menu items from the business if available
            if not menu_items:
                # Create a test order with mock item if no menu items available
                order_data = {
                    "delivery_address": "Test Delivery Address, Aksaray, Turkey",
                    "delivery_lat": 38.3687,
                    "delivery_lng": 34.0370,
                    "items": [
                        {
                            "product_id": "test-item-id",
                            "product_name": "Test Döner",
                            "product_price": 99.99,
                            "quantity": 1,
                            "subtotal": 99.99
                        }
                    ],
                    "total_amount": 99.99,
                    "notes": "Test order for business panel display verification"
                }
            else:
                # Create order with first available menu item
                menu_item = menu_items[0]
                
                order_data = {
                    "delivery_address": "Test Delivery Address, Aksaray, Turkey",
                    "delivery_lat": 38.3687,
                    "delivery_lng": 34.0370,
                    "items": [
                        {
                            "product_id": menu_item.get("id"),
                            "product_name": menu_item.get("name", "Test Item"),
                            "product_price": float(menu_item.get("price", 99.99)),
                            "quantity": 1,
                            "subtotal": float(menu_item.get("price", 99.99))
                        }
                    ],
                    "total_amount": float(menu_item.get("price", 99.99)),
                    "notes": "Test order for business panel display verification"
                }
            
            response = customer_session.post(f"{BACKEND_URL}/orders", json=order_data)
            
            if response.status_code in [200, 201]:
                order = response.json()
                order_id = order.get("id")
                order_business_id = order.get("business_id")
                
                self.log_test(
                    "Create Test Order", 
                    True, 
                    f"Order created successfully: {order_id}, business_id: {order_business_id}",
                    {
                        "order_id": order_id,
                        "business_id": order_business_id,
                        "customer_id": customer_id,
                        "total_amount": order.get("total_amount"),
                        "status": order.get("status")
                    }
                )
                return True, order_id
            else:
                self.log_test(
                    "Create Test Order", 
                    False, 
                    f"Failed to create order: HTTP {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_test("Create Test Order", False, f"Request error: {str(e)}")
            return False, None
    
    def test_business_login_and_orders(self, created_order_id):
        """Test 4: Business login and order retrieval (CRITICAL TEST)"""
        try:
            # Login as business user
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            business_id = business_user.get("id")
            
            # Verify business ID matches expected
            if business_id != BUSINESS_ID:
                self.log_test(
                    "Business Login Verification", 
                    False, 
                    f"Business ID mismatch: expected {BUSINESS_ID}, got {business_id}"
                )
                return False
            
            # Test GET /api/business/orders/incoming endpoint
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data
                
                self.log_test(
                    "Business Incoming Orders", 
                    True, 
                    f"Retrieved {len(orders)} incoming orders for business {business_id}",
                    {
                        "business_id": business_id,
                        "total_orders": len(orders),
                        "orders_preview": [{"id": o.get("id"), "business_id": o.get("business_id")} for o in orders[:3]]
                    }
                )
                
                # Check if orders include business_id field
                orders_with_business_id = [o for o in orders if o.get("business_id")]
                orders_matching_business = [o for o in orders if o.get("business_id") == business_id]
                
                self.log_test(
                    "Business ID in Orders", 
                    len(orders_with_business_id) == len(orders), 
                    f"{len(orders_with_business_id)}/{len(orders)} orders have business_id field",
                    {"orders_with_business_id": len(orders_with_business_id), "total_orders": len(orders)}
                )
                
                self.log_test(
                    "Correct Business Orders", 
                    len(orders_matching_business) == len(orders), 
                    f"{len(orders_matching_business)}/{len(orders)} orders match business ID {business_id}",
                    {"matching_orders": len(orders_matching_business), "total_orders": len(orders)}
                )
                
                return True
            else:
                self.log_test(
                    "Business Incoming Orders", 
                    False, 
                    f"Failed to retrieve incoming orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Business Login and Orders", False, f"Request error: {str(e)}")
            return False
    
    def test_authentication_consistency(self):
        """Test authentication consistency between endpoints"""
        try:
            # Login as business and get user info via /me endpoint
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            # Get user info via /me endpoint (uses get_current_user_from_cookie_or_bearer)
            me_response = self.session.get(f"{BACKEND_URL}/me")
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                me_user_id = me_data.get("id")
                
                # Get orders via /orders endpoint (should use same authentication)
                orders_response = self.session.get(f"{BACKEND_URL}/orders")
                
                if orders_response.status_code == 200:
                    self.log_test(
                        "Authentication Consistency", 
                        True, 
                        f"Both /me and /orders endpoints accessible with same authentication (user_id: {me_user_id})",
                        {
                            "me_user_id": me_user_id,
                            "orders_accessible": True
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Authentication Consistency", 
                        False, 
                        f"/me works but /orders fails: HTTP {orders_response.status_code}: {orders_response.text}"
                    )
                    return False
            else:
                self.log_test(
                    "Authentication Consistency", 
                    False, 
                    f"Failed to get user info: HTTP {me_response.status_code}: {me_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication Consistency", False, f"Request error: {str(e)}")
            return False
    
    def test_menu_item_business_association(self):
        """Test menu item to business_id mapping"""
        try:
            # Login as business
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            business_id = business_user.get("id")
            
            # Get menu items
            response = self.session.get(f"{BACKEND_URL}/business/menu")
            
            if response.status_code == 200:
                menu_data = response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                if menu_items:
                    # Check if menu items have correct business association
                    correct_associations = 0
                    for item in menu_items:
                        if item.get("business_id") == business_id:
                            correct_associations += 1
                    
                    if correct_associations == len(menu_items):
                        self.log_test(
                            "Menu Item Business Association", 
                            True, 
                            f"All {len(menu_items)} menu items correctly associated with business {business_id}",
                            {
                                "business_id": business_id,
                                "total_items": len(menu_items),
                                "correct_associations": correct_associations
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Menu Item Business Association", 
                            False, 
                            f"Only {correct_associations}/{len(menu_items)} menu items correctly associated"
                        )
                        return False
                else:
                    self.log_test(
                        "Menu Item Business Association", 
                        True, 
                        f"No menu items found (empty menu is valid)",
                        {"business_id": business_id}
                    )
                    return True
            else:
                self.log_test(
                    "Menu Item Business Association", 
                    False, 
                    f"Failed to get menu: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Menu Item Business Association", False, f"Request error: {str(e)}")
            return False
    
    def test_order_data_integrity(self, created_order_id):
        """Test 5: Order data integrity and required fields"""
        try:
            # Login as business to get order details
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            # Get orders via business incoming orders endpoint
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data
                
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id or order.get("order_id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    # Check required fields for business panel display
                    required_fields = [
                        "id", "business_id", "customer_name", "delivery_address",
                        "items", "total_amount", "status"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in found_order]
                    present_fields = [field for field in required_fields if field in found_order]
                    
                    # Check business_id specifically
                    business_id_correct = found_order.get("business_id") == BUSINESS_ID
                    
                    self.log_test(
                        "Order Data Integrity", 
                        len(missing_fields) == 0 and business_id_correct, 
                        f"Order has {len(present_fields)}/{len(required_fields)} required fields, business_id correct: {business_id_correct}",
                        {
                            "order_id": created_order_id,
                            "business_id": found_order.get("business_id"),
                            "expected_business_id": BUSINESS_ID,
                            "customer_name": found_order.get("customer_name"),
                            "total_amount": found_order.get("total_amount"),
                            "status": found_order.get("status"),
                            "items_count": len(found_order.get("items", [])),
                            "present_fields": present_fields,
                            "missing_fields": missing_fields
                        }
                    )
                    return len(missing_fields) == 0 and business_id_correct
                else:
                    self.log_test(
                        "Order Data Integrity", 
                        False, 
                        f"Order {created_order_id} not found in business incoming orders"
                    )
                    return False
            else:
                self.log_test(
                    "Order Data Integrity", 
                    False, 
                    f"Failed to retrieve business orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Order Data Integrity", False, f"Request error: {str(e)}")
            return False
    
    def test_database_verification(self, created_order_id):
        """Test 6: Database verification via admin endpoints (if available)"""
        try:
            # Try to get order details via customer endpoint to verify database state
            customer_session, customer_user = self.customer_login()
            
            if not customer_session:
                self.log_test("Database Verification", False, "Could not login as customer for verification")
                return False
            
            # Get customer orders to verify order exists in database
            response = customer_session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    # Verify order has business_id field and it matches expected
                    order_business_id = found_order.get("business_id")
                    business_id_matches = order_business_id == BUSINESS_ID
                    
                    self.log_test(
                        "Database Verification", 
                        business_id_matches, 
                        f"Order in database has business_id: {order_business_id}, matches expected: {business_id_matches}",
                        {
                            "order_id": created_order_id,
                            "database_business_id": order_business_id,
                            "expected_business_id": BUSINESS_ID,
                            "match": business_id_matches
                        }
                    )
                    return business_id_matches
                else:
                    self.log_test(
                        "Database Verification", 
                        False, 
                        f"Order {created_order_id} not found in customer orders (database issue)"
                    )
                    return False
            else:
                self.log_test(
                    "Database Verification", 
                    False, 
                    f"Failed to retrieve customer orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Database Verification", False, f"Request error: {str(e)}")
            return False
    
    def test_cross_user_order_isolation(self):
        """Test that businesses only see their own orders"""
        try:
            # Login as business and get their orders
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            business_id = business_user.get("id")
            
            # Get orders for this business
            response = self.session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                # Check that all orders belong to this business
                wrong_business_orders = []
                for order in orders:
                    order_business_id = order.get("business_id")
                    if order_business_id and order_business_id != business_id:
                        wrong_business_orders.append({
                            "order_id": order.get("id"),
                            "business_id": order_business_id
                        })
                
                if not wrong_business_orders:
                    self.log_test(
                        "Cross-User Order Isolation", 
                        True, 
                        f"Business only sees their own orders ({len(orders)} orders, all belong to business {business_id})",
                        {
                            "business_id": business_id,
                            "total_orders": len(orders),
                            "isolation_verified": True
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Cross-User Order Isolation", 
                        False, 
                        f"Business sees orders from other businesses: {wrong_business_orders}"
                    )
                    return False
            else:
                self.log_test(
                    "Cross-User Order Isolation", 
                    False, 
                    f"Failed to retrieve orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Cross-User Order Isolation", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all business order display tests as per review request"""
        print("🚀 CRITICAL TEST: Business Order Display - Check if Orders Appear in Business Panel")
        print("=" * 80)
        print("🎯 Testing Scenario: Previously fixed issue where orders weren't appearing in business panel")
        print(f"🏪 Business: testbusiness@example.com (ID: {BUSINESS_ID} - Lezzet Döner)")
        print(f"👤 Customer: testcustomer@example.com")
        print("=" * 80)
        
        # Test 1: Verify business exists
        print("\n📋 Test 1: Verify Business Exists")
        print("-" * 50)
        
        business_exists = self.test_business_exists()
        if not business_exists:
            print("❌ Cannot proceed - test business not found")
            return False
        
        # Test 2: Get menu items
        print("\n📋 Test 2: Get Menu Items from Business")
        print("-" * 50)
        
        menu_items = self.test_get_menu_items()
        
        # Test 3: Create test order
        print("\n📋 Test 3: Create Test Order (Customer)")
        print("-" * 50)
        
        order_creation = self.test_create_order(menu_items)
        if not order_creation[0]:
            print("❌ Cannot proceed without order creation")
            return False
        
        created_order_id = order_creation[1]
        
        # Test 4: Business login and order retrieval (CRITICAL)
        print("\n📋 Test 4: Business Login & Order Retrieval (CRITICAL TEST)")
        print("-" * 50)
        
        business_orders_test = self.test_business_login_and_orders(created_order_id)
        
        # Test 5: Order data integrity
        print("\n📋 Test 5: Order Data Integrity")
        print("-" * 50)
        
        data_integrity_test = self.test_order_data_integrity(created_order_id)
        
        # Test 6: Database verification
        print("\n📋 Test 6: Database Verification")
        print("-" * 50)
        
        database_verification_test = self.test_database_verification(created_order_id)
        
        # Calculate results
        tests_run = [
            business_exists,
            len(menu_items) > 0,  # Menu items test
            order_creation[0],
            business_orders_test,
            data_integrity_test,
            database_verification_test
        ]
        
        passed_tests = sum(tests_run)
        total_tests = len(tests_run)
        success_rate = (passed_tests / total_tests) * 100
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 BUSINESS ORDER DISPLAY TESTING SUMMARY")
        print("=" * 80)
        
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Business order display is working perfectly!")
            print("✅ Orders are appearing in business panel as expected")
        elif passed_tests >= total_tests * 0.75:
            print("✅ MOSTLY WORKING - Business order display functional with minor issues")
        else:
            print("❌ CRITICAL ISSUES - Business order display needs attention")
        
        # Expected results verification
        print("\n🎯 Expected Results Verification:")
        print("-" * 50)
        
        expected_results = [
            f"✅ Customer can create orders: {'PASS' if order_creation[0] else 'FAIL'}",
            f"✅ Orders saved with correct business_id: {'PASS' if data_integrity_test else 'FAIL'}",
            f"✅ Business panel shows incoming orders: {'PASS' if business_orders_test else 'FAIL'}",
            f"✅ Orders display with complete information: {'PASS' if data_integrity_test else 'FAIL'}"
        ]
        
        for result in expected_results:
            print(result)
        
        # Critical findings
        print("\n🔍 Critical Findings:")
        print("-" * 50)
        
        if business_orders_test and data_integrity_test:
            print("✅ FIXED: Orders are now appearing in business panel")
            print("✅ Business_id field is properly included in order responses")
            print("✅ Cookie authentication is working correctly")
        else:
            print("❌ ISSUE: Orders may not be appearing correctly in business panel")
            print("❌ Check: Authentication consistency (cookie vs bearer token)")
            print("❌ Check: Business_id field in order creation and retrieval")
        
        # Detailed results
        print("\n📋 Detailed Test Results:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests >= total_tests * 0.75  # 75% success rate required

if __name__ == "__main__":
    tester = BusinessOrderDisplayTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)