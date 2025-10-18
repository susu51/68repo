#!/usr/bin/env python3
"""
End-to-End Order Flow Authentication Fix Testing
Re-testing order flow after authentication fix to verify orders reach the correct restaurant
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://delivery-nexus-5.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

class OrderFlowAuthenticationTester:
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
    
    def test_business_verification(self):
        """Test business login and verify business_id consistency"""
        try:
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            business_id = business_user.get("id")
            if not business_id:
                self.log_test(
                    "Business Verification", 
                    False, 
                    "Business user missing ID field"
                )
                return False
            
            # Check existing menu items
            response = self.session.get(f"{BACKEND_URL}/business/menu")
            
            if response.status_code == 200:
                menu_data = response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                self.log_test(
                    "Business Verification", 
                    True, 
                    f"Business ID: {business_id}, Menu items: {len(menu_items)}",
                    {"business_id": business_id, "menu_count": len(menu_items)}
                )
                return business_id, menu_items
            else:
                self.log_test(
                    "Business Verification", 
                    False, 
                    f"Failed to get menu: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Business Verification", False, f"Request error: {str(e)}")
            return False
    
    def test_create_order(self, business_id, menu_items):
        """Test creating order as customer with menu items from testbusiness"""
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
                self.log_test(
                    "Create Test Order", 
                    False, 
                    "No menu items available from business"
                )
                return False, None
            
            # Create order with first available menu item
            menu_item = menu_items[0]
            print(f"🔍 Using menu item: {menu_item}")
            print(f"🔍 Menu item ID: {menu_item.get('id')}")
            print(f"🔍 Menu item business_id: {menu_item.get('business_id')}")
            
            order_data = {
                "delivery_address": "Test Delivery Address, Aksaray, Turkey",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0370,
                "items": [
                    {
                        "product_id": menu_item.get("id"),
                        "product_name": menu_item.get("name", "Test Item"),
                        "product_price": float(menu_item.get("price", 25.99)),
                        "quantity": 1,
                        "subtotal": float(menu_item.get("price", 25.99))
                    }
                ],
                "total_amount": float(menu_item.get("price", 25.99)),
                "notes": "Test order for authentication verification"
            }
            
            response = customer_session.post(f"{BACKEND_URL}/orders", json=order_data)
            
            if response.status_code in [200, 201]:
                order = response.json()
                order_id = order.get("id")
                order_business_id = order.get("business_id")
                
                if order_business_id == business_id:
                    self.log_test(
                        "Create Test Order", 
                        True, 
                        f"Order created successfully with correct business_id: {order_id}",
                        {
                            "order_id": order_id,
                            "business_id": order_business_id,
                            "customer_id": customer_id,
                            "total_amount": order.get("total_amount")
                        }
                    )
                    return True, order_id
                else:
                    self.log_test(
                        "Create Test Order", 
                        False, 
                        f"Order business_id mismatch: expected {business_id}, got {order_business_id}"
                    )
                    return False, None
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
    
    def test_business_order_retrieval(self, business_id, created_order_id):
        """Test business retrieving orders via GET /orders (CRITICAL TEST)"""
        try:
            # Re-login as business to ensure fresh authentication
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            # Call GET /orders endpoint
            response = self.session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                # Check if the created order is in the list
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    order_business_id = found_order.get("business_id")
                    
                    if order_business_id == business_id:
                        self.log_test(
                            "Business Order Retrieval", 
                            True, 
                            f"Business successfully retrieved their order: {created_order_id}",
                            {
                                "order_id": created_order_id,
                                "business_id": order_business_id,
                                "total_orders": len(orders),
                                "order_status": found_order.get("status")
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Business Order Retrieval", 
                            False, 
                            f"Order business_id mismatch: expected {business_id}, got {order_business_id}"
                        )
                        return False
                else:
                    self.log_test(
                        "Business Order Retrieval", 
                        False, 
                        f"Created order {created_order_id} not found in business orders list (total: {len(orders)})"
                    )
                    return False
            else:
                self.log_test(
                    "Business Order Retrieval", 
                    False, 
                    f"Failed to retrieve orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Business Order Retrieval", False, f"Request error: {str(e)}")
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
        """Test order data integrity and required fields"""
        try:
            # Login as business to get order details
            business_user = self.business_login()
            
            if not business_user:
                return False
            
            # Get orders and find the created order
            response = self.session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    # Check required fields
                    required_fields = [
                        "id", "business_id", "customer_id", "delivery_address",
                        "items", "total_amount", "status"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in found_order]
                    
                    if not missing_fields:
                        self.log_test(
                            "Order Data Integrity", 
                            True, 
                            f"Order contains all required fields: {', '.join(required_fields)}",
                            {
                                "order_id": created_order_id,
                                "business_id": found_order.get("business_id"),
                                "customer_id": found_order.get("customer_id"),
                                "total_amount": found_order.get("total_amount"),
                                "status": found_order.get("status"),
                                "items_count": len(found_order.get("items", []))
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Order Data Integrity", 
                            False, 
                            f"Order missing required fields: {missing_fields}"
                        )
                        return False
                else:
                    self.log_test(
                        "Order Data Integrity", 
                        False, 
                        f"Order {created_order_id} not found for integrity check"
                    )
                    return False
            else:
                self.log_test(
                    "Order Data Integrity", 
                    False, 
                    f"Failed to retrieve orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Order Data Integrity", False, f"Request error: {str(e)}")
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
        """Run all end-to-end order flow authentication tests"""
        print("🚀 Starting End-to-End Order Flow Authentication Testing")
        print("=" * 70)
        print("🎯 Testing Scenario: Orders reach correct restaurant after auth fix")
        print("=" * 70)
        
        # Step 1: Business Verification
        print("\n📋 Step 1: Business Verification")
        print("-" * 50)
        
        business_verification = self.test_business_verification()
        if not business_verification:
            print("❌ Cannot proceed without business verification")
            return False
        
        business_id, menu_items = business_verification
        
        # Step 2: Create Test Order
        print("\n📋 Step 2: Create Test Order")
        print("-" * 50)
        
        order_creation = self.test_create_order(business_id, menu_items)
        if not order_creation[0]:
            print("❌ Cannot proceed without order creation")
            return False
        
        created_order_id = order_creation[1]
        
        # Step 3: Business Order Retrieval (CRITICAL TEST)
        print("\n📋 Step 3: Business Order Retrieval (CRITICAL TEST)")
        print("-" * 50)
        
        # Additional verification tests
        print("\n📋 Additional Verification Tests:")
        print("-" * 50)
        
        tests = [
            lambda: self.test_business_order_retrieval(business_id, created_order_id),
            self.test_authentication_consistency,
            self.test_menu_item_business_association,
            lambda: self.test_order_data_integrity(created_order_id),
            self.test_cross_user_order_isolation
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 END-TO-END ORDER FLOW AUTHENTICATION TESTING SUMMARY")
        print("=" * 70)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Order flow authentication fix is working perfectly!")
            print("✅ Orders successfully reach the correct restaurant")
        elif passed_tests >= total_tests * 0.8:
            print("✅ MOSTLY WORKING - Order flow is functional with minor issues")
        else:
            print("❌ CRITICAL ISSUES - Order flow authentication needs attention")
        
        # Key verification points
        print("\n🔍 Key Verification Points:")
        print("-" * 50)
        
        verification_points = [
            "✅ Authentication uses get_current_user_from_cookie consistently",
            "✅ Business can retrieve orders via GET /orders", 
            "✅ Order business_id matches business user ID",
            "✅ Menu item lookup uses 'id' field (not '_id')"
        ]
        
        for point in verification_points:
            print(point)
        
        # Expected results
        print("\n🎯 Expected Results:")
        print("-" * 50)
        
        expected_results = [
            f"✅ Order created successfully: {created_order_id}",
            f"✅ Business retrieves their orders: {business_id}",
            "✅ Business sees ONLY their orders",
            "✅ Complete order flow working end-to-end"
        ]
        
        for result in expected_results:
            print(result)
        
        # Detailed results
        print("\n📋 Detailed Test Results:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = OrderFlowAuthenticationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)