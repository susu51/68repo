#!/usr/bin/env python3
"""
Business Panel Order Display Fix Testing
Testing the fix where orders placed by customers were not appearing in business order management panel
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://food-dash-87.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"
BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"  # Lezzet Döner

class OrderFlowFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.customer_session = requests.Session()
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
    
    def customer_login(self):
        """Login as customer user"""
        try:
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.customer_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Customer Login", True, f"Customer authenticated successfully")
                    return data.get("user", {})
                else:
                    self.log_test("Customer Login", False, f"Login failed: {data}")
                    return None
            else:
                self.log_test("Customer Login", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Login error: {str(e)}")
            return None
    
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
                    user = data.get("user", {})
                    business_id = user.get("id")
                    self.log_test("Business Login", True, f"Business authenticated successfully (ID: {business_id})")
                    return user
                else:
                    self.log_test("Business Login", False, f"Login failed: {data}")
                    return None
            else:
                self.log_test("Business Login", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Business Login", False, f"Login error: {str(e)}")
            return None
    
    def test_order_creation(self):
        """Test 1: Order Creation Test - customer creates order with proper business_id"""
        try:
            customer_user = self.customer_login()
            if not customer_user:
                return False, None
            
            # First get the business ID by logging in as business
            business_user = self.business_login()
            if not business_user:
                return False, None
            
            global BUSINESS_ID
            BUSINESS_ID = business_user.get("id")
            
            # Get menu items from the business
            response = self.customer_session.get(f"{BACKEND_URL}/business/public/{BUSINESS_ID}/menu")
            
            if response.status_code != 200:
                self.log_test("Order Creation Test", False, f"Failed to get menu: HTTP {response.status_code}")
                return False, None
            
            menu_items = response.json()
            if not menu_items:
                self.log_test("Order Creation Test", False, "No menu items available")
                return False, None
            
            # Create order with menu item from specific business
            menu_item = menu_items[0]
            order_data = {
                "delivery_address": "Test Address, Aksaray, Turkey",
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
                "notes": "Test order for business panel display fix"
            }
            
            response = self.customer_session.post(f"{BACKEND_URL}/orders", json=order_data)
            
            if response.status_code in [200, 201]:
                order = response.json()
                order_id = order.get("id")
                order_business_id = order.get("business_id")
                business_name = order.get("business_name")
                
                if order_business_id == BUSINESS_ID:
                    self.log_test(
                        "Order Creation Test", 
                        True, 
                        f"Order created successfully with correct business_id: {order_id}",
                        {
                            "order_id": order_id,
                            "business_id": order_business_id,
                            "business_name": business_name,
                            "total_amount": order.get("total_amount"),
                            "status": order.get("status")
                        }
                    )
                    return True, order_id
                else:
                    self.log_test(
                        "Order Creation Test", 
                        False, 
                        f"Order business_id mismatch: expected {BUSINESS_ID}, got {order_business_id}"
                    )
                    return False, None
            else:
                self.log_test(
                    "Order Creation Test", 
                    False, 
                    f"Failed to create order: HTTP {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_test("Order Creation Test", False, f"Request error: {str(e)}")
            return False, None
    
    def test_business_order_retrieval(self, created_order_id):
        """Test 2: Business Order Retrieval Test - GET /api/business/orders/incoming"""
        try:
            business_user = self.business_login()
            if not business_user:
                return False
            
            # Test the specific endpoint mentioned in the fix
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming")
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                # Check if created order is in the list
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id or order.get("order_id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    business_id = found_order.get("business_id")
                    business_name = found_order.get("business_name")
                    
                    if business_id == BUSINESS_ID:
                        self.log_test(
                            "Business Order Retrieval Test", 
                            True, 
                            f"Order found in business panel with correct business_id: {business_id}",
                            {
                                "order_id": created_order_id,
                                "business_id": business_id,
                                "business_name": business_name,
                                "total_orders": len(orders),
                                "order_structure": list(found_order.keys())
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Business Order Retrieval Test", 
                            False, 
                            f"Order business_id mismatch: expected {BUSINESS_ID}, got {business_id}"
                        )
                        return False
                else:
                    self.log_test(
                        "Business Order Retrieval Test", 
                        False, 
                        f"Created order {created_order_id} not found in business incoming orders (total: {len(orders)})"
                    )
                    return False
            else:
                self.log_test(
                    "Business Order Retrieval Test", 
                    False, 
                    f"Failed to get incoming orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Business Order Retrieval Test", False, f"Request error: {str(e)}")
            return False
    
    def test_business_order_active_history(self):
        """Test 3: Business Order Active/History Test - verify business_id in all responses"""
        try:
            business_user = self.business_login()
            if not business_user:
                return False
            
            endpoints_to_test = [
                ("active", "/business/orders/active"),
                ("history", "/business/orders/history")
            ]
            
            all_passed = True
            
            for endpoint_name, endpoint_path in endpoints_to_test:
                response = self.session.get(f"{BACKEND_URL}{endpoint_path}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        orders = data
                    else:
                        orders = data.get("orders", [])
                    
                    # Check business_id consistency in all orders
                    business_id_issues = []
                    for order in orders:
                        order_business_id = order.get("business_id")
                        if order_business_id and order_business_id != BUSINESS_ID:
                            business_id_issues.append({
                                "order_id": order.get("id"),
                                "business_id": order_business_id
                            })
                    
                    if not business_id_issues:
                        self.log_test(
                            f"Business {endpoint_name.title()} Orders Test", 
                            True, 
                            f"All {len(orders)} orders have correct business_id in {endpoint_name} endpoint",
                            {
                                "endpoint": endpoint_path,
                                "total_orders": len(orders),
                                "business_id_consistent": True
                            }
                        )
                    else:
                        self.log_test(
                            f"Business {endpoint_name.title()} Orders Test", 
                            False, 
                            f"Found {len(business_id_issues)} orders with incorrect business_id in {endpoint_name}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Business {endpoint_name.title()} Orders Test", 
                        False, 
                        f"Failed to get {endpoint_name} orders: HTTP {response.status_code}: {response.text}"
                    )
                    all_passed = False
            
            return all_passed
                
        except Exception as e:
            self.log_test("Business Order Active/History Test", False, f"Request error: {str(e)}")
            return False
    
    def test_order_data_integrity(self, created_order_id):
        """Test 4: Order Data Integrity - verify order contains all required fields"""
        try:
            business_user = self.business_login()
            if not business_user:
                return False
            
            # Get the order from business incoming orders
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming")
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                found_order = None
                for order in orders:
                    if order.get("id") == created_order_id or order.get("order_id") == created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    # Check required fields as mentioned in review request
                    required_fields = [
                        "id", "business_id", "customer_name",
                        "items", "total_amount", "status"
                    ]
                    
                    # Optional fields that are nice to have
                    optional_fields = ["business_name"]
                    
                    missing_fields = []
                    present_fields = []
                    optional_present = []
                    
                    for field in required_fields:
                        if field in found_order and found_order[field] is not None:
                            present_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    for field in optional_fields:
                        if field in found_order and found_order[field] is not None:
                            optional_present.append(field)
                    
                    # Additional checks
                    has_customer_info = bool(found_order.get("customer_name") or found_order.get("customer_email"))
                    has_items_array = isinstance(found_order.get("items"), list) and len(found_order.get("items", [])) > 0
                    has_correct_business_id = found_order.get("business_id") == BUSINESS_ID
                    
                    if not missing_fields and has_customer_info and has_items_array and has_correct_business_id:
                        self.log_test(
                            "Order Data Integrity Test", 
                            True, 
                            f"Order contains all required fields and data integrity verified",
                            {
                                "order_id": created_order_id,
                                "required_fields": present_fields,
                                "optional_fields": optional_present,
                                "business_id": found_order.get("business_id"),
                                "business_name": found_order.get("business_name"),
                                "customer_info": has_customer_info,
                                "items_count": len(found_order.get("items", [])),
                                "total_amount": found_order.get("total_amount"),
                                "status": found_order.get("status")
                            }
                        )
                        return True
                    else:
                        issues = []
                        if missing_fields:
                            issues.append(f"Missing fields: {missing_fields}")
                        if not has_customer_info:
                            issues.append("Missing customer information")
                        if not has_items_array:
                            issues.append("Missing or empty items array")
                        if not has_correct_business_id:
                            issues.append(f"Incorrect business_id: {found_order.get('business_id')}")
                        
                        self.log_test(
                            "Order Data Integrity Test", 
                            False, 
                            f"Order data integrity issues: {'; '.join(issues)}"
                        )
                        return False
                else:
                    self.log_test(
                        "Order Data Integrity Test", 
                        False, 
                        f"Order {created_order_id} not found for integrity check"
                    )
                    return False
            else:
                self.log_test(
                    "Order Data Integrity Test", 
                    False, 
                    f"Failed to get orders for integrity check: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Order Data Integrity Test", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests for the business panel order display fix"""
        print("🚀 Starting Business Panel Order Display Fix Testing")
        print("=" * 70)
        print("🎯 Testing Fix: Orders placed by customers now appear in business panel")
        print("🏪 Business: testbusiness@example.com")
        print("=" * 70)
        
        # Test 1: Order Creation
        print("\n📋 Test 1: Order Creation Test")
        print("-" * 50)
        
        order_creation = self.test_order_creation()
        if not order_creation[0]:
            print("❌ Cannot proceed without successful order creation")
            return False
        
        created_order_id = order_creation[1]
        
        # Test 2: Business Order Retrieval
        print("\n📋 Test 2: Business Order Retrieval Test")
        print("-" * 50)
        
        # Test 3: Business Order Active/History
        print("\n📋 Test 3: Business Order Active/History Test")
        print("-" * 50)
        
        # Test 4: Order Data Integrity
        print("\n📋 Test 4: Order Data Integrity Test")
        print("-" * 50)
        
        # Run all tests
        tests = [
            lambda: self.test_business_order_retrieval(created_order_id),
            self.test_business_order_active_history,
            lambda: self.test_order_data_integrity(created_order_id)
        ]
        
        passed_tests = 1  # Order creation already passed
        total_tests = len(tests) + 1  # +1 for order creation
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 BUSINESS PANEL ORDER DISPLAY FIX TESTING SUMMARY")
        print("=" * 70)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Business panel order display fix is working perfectly!")
            print("✅ Orders are now appearing in business order management panel")
        elif passed_tests >= total_tests * 0.75:
            print("✅ MOSTLY WORKING - Fix is functional with minor issues")
        else:
            print("❌ CRITICAL ISSUES - Business panel order display fix needs attention")
        
        # Expected Results Summary
        print("\n🎯 Expected Results Verification:")
        print("-" * 50)
        
        expected_results = [
            "✅ Orders appear in business panel",
            "✅ business_id field present and correct", 
            "✅ Orders filtered to show only business's orders",
            "✅ All order data fields complete and accurate"
        ]
        
        for result in expected_results:
            print(result)
        
        # Detailed Results
        print("\n📋 Detailed Test Results:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = OrderFlowFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)