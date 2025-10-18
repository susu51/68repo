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
            
            if response.status_code == 201:
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
    
    def test_maintenance_status_public(self):
        """Test GET /api/maintenance-status (public endpoint)"""
        try:
            # Test without authentication (public endpoint)
            public_session = requests.Session()
            response = public_session.get(f"{BACKEND_URL}/maintenance-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                if "maintenance_mode" in data:
                    self.log_test(
                        "Public Maintenance Status", 
                        True, 
                        f"Public maintenance status accessible: maintenance_mode={data['maintenance_mode']}",
                        {"response": data}
                    )
                    return True
                else:
                    self.log_test(
                        "Public Maintenance Status", 
                        False, 
                        f"Missing maintenance_mode field: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Public Maintenance Status", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Public Maintenance Status", False, f"Request error: {str(e)}")
            return False
    
    def test_backend_logs_retrieval(self):
        """Test GET /api/admin/logs/backend"""
        try:
            # Test with default parameters
            response = self.session.get(f"{BACKEND_URL}/admin/logs/backend")
            
            if response.status_code == 200:
                data = response.json()
                
                if "logs" in data and "total_lines" in data:
                    self.log_test(
                        "Backend Logs (Default)", 
                        True, 
                        f"Retrieved {data['total_lines']} log lines",
                        {"log_file": data.get("log_file"), "sample_logs": data["logs"][:3] if data["logs"] else []}
                    )
                    
                    # Test with custom parameters
                    response2 = self.session.get(f"{BACKEND_URL}/admin/logs/backend?lines=50&level=error")
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        
                        self.log_test(
                            "Backend Logs (Filtered)", 
                            True, 
                            f"Retrieved {data2['total_lines']} filtered log lines (level=error)",
                            {"filtered_logs": len(data2["logs"])}
                        )
                        return True
                    else:
                        self.log_test(
                            "Backend Logs (Filtered)", 
                            False, 
                            f"HTTP {response2.status_code}: {response2.text}"
                        )
                        return False
                else:
                    self.log_test(
                        "Backend Logs (Default)", 
                        False, 
                        f"Missing required fields in response: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Backend Logs (Default)", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Retrieval", False, f"Request error: {str(e)}")
            return False
    
    def test_system_button_tests(self):
        """Test POST /api/admin/test-buttons"""
        try:
            # Test all button types
            test_data = {"button_type": "all"}
            
            response = self.session.post(f"{BACKEND_URL}/admin/test-buttons", json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "test_results" in data and "overall_status" in data:
                    test_results = data["test_results"]
                    overall_status = data["overall_status"]
                    
                    self.log_test(
                        "System Tests (All)", 
                        True, 
                        f"System tests completed with status: {overall_status} ({len(test_results)} tests)",
                        {"test_results": test_results}
                    )
                    
                    # Test specific button types
                    for button_type in ["api", "auth", "orders"]:
                        specific_data = {"button_type": button_type}
                        response2 = self.session.post(f"{BACKEND_URL}/admin/test-buttons", json=specific_data)
                        
                        if response2.status_code == 200:
                            data2 = response2.json()
                            self.log_test(
                                f"System Tests ({button_type})", 
                                True, 
                                f"Specific test '{button_type}' completed: {data2['overall_status']}",
                                {"results": data2["test_results"]}
                            )
                        else:
                            self.log_test(
                                f"System Tests ({button_type})", 
                                False, 
                                f"HTTP {response2.status_code}: {response2.text}"
                            )
                    
                    return True
                else:
                    self.log_test(
                        "System Tests (All)", 
                        False, 
                        f"Missing required fields in response: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "System Tests (All)", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("System Button Tests", False, f"Request error: {str(e)}")
            return False
    
    def test_admin_authentication_required(self):
        """Test that admin endpoints require admin authentication"""
        try:
            # Test without authentication
            public_session = requests.Session()
            
            admin_endpoints = [
                "/admin/settings/system",
                "/admin/logs/backend"
            ]
            
            auth_test_results = []
            
            for endpoint in admin_endpoints:
                response = public_session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code in [401, 403]:
                    auth_test_results.append(f"✅ {endpoint}: Properly secured ({response.status_code})")
                else:
                    auth_test_results.append(f"❌ {endpoint}: Not secured ({response.status_code})")
            
            # Test POST endpoints
            post_endpoints = [
                ("/admin/settings/system", {"test": "data"}),
                ("/admin/settings/maintenance-mode", {"enabled": True}),
                ("/admin/test-buttons", {"button_type": "all"})
            ]
            
            for endpoint, data in post_endpoints:
                response = public_session.post(f"{BACKEND_URL}{endpoint}", json=data)
                
                if response.status_code in [401, 403]:
                    auth_test_results.append(f"✅ {endpoint}: Properly secured ({response.status_code})")
                else:
                    auth_test_results.append(f"❌ {endpoint}: Not secured ({response.status_code})")
            
            all_secured = all("✅" in result for result in auth_test_results)
            
            self.log_test(
                "Admin Authentication Required", 
                all_secured, 
                f"Admin endpoints security check: {'All secured' if all_secured else 'Some endpoints not secured'}",
                {"security_results": auth_test_results}
            )
            
            return all_secured
                
        except Exception as e:
            self.log_test("Admin Authentication Required", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin settings and maintenance mode tests"""
        print("🚀 Starting Admin Settings & Maintenance Mode System Testing")
        print("=" * 70)
        
        # Step 1: Admin Login
        if not self.admin_login():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        print("\n📋 Testing Admin Settings & Maintenance Mode Endpoints:")
        print("-" * 50)
        
        # Step 2: Test all endpoints
        tests = [
            self.test_get_system_settings,
            self.test_update_system_settings,
            self.test_maintenance_mode_toggle,
            self.test_maintenance_status_public,
            self.test_backend_logs_retrieval,
            self.test_system_button_tests,
            self.test_admin_authentication_required
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
        print("📊 ADMIN SETTINGS & MAINTENANCE MODE TESTING SUMMARY")
        print("=" * 70)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Admin Settings & Maintenance Mode system is working perfectly!")
        elif passed_tests >= total_tests * 0.8:
            print("✅ MOSTLY WORKING - Admin Settings & Maintenance Mode system is functional with minor issues")
        else:
            print("❌ CRITICAL ISSUES - Admin Settings & Maintenance Mode system needs attention")
        
        # Detailed results
        print("\n📋 Detailed Test Results:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = AdminSettingsMaintenanceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)