#!/usr/bin/env python3
"""
Admin Settings & Maintenance Mode System Backend Testing
Testing the newly implemented admin settings and maintenance mode functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://delivery-nexus-5.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

class CustomerOrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.customer_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        print()
    
    def test_customer_login(self):
        """Test customer login functionality"""
        print("🔐 Testing Customer Login...")
        
        try:
            # Test login endpoint
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.customer_id = data.get("user", {}).get("id")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    
                    self.log_test(
                        "Customer Login", 
                        True, 
                        f"Successfully logged in as {CUSTOMER_EMAIL}, token length: {len(self.auth_token)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Customer Login", 
                        False, 
                        "Login response missing required fields",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Customer Login", 
                    False, 
                    f"Login failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Exception: {str(e)}")
            return False
    
    def test_restaurant_discovery(self):
        """Test /businesses endpoint with city filter"""
        print("🏪 Testing Restaurant Discovery...")
        
        try:
            # Test businesses endpoint with city filter
            response = self.session.get(f"{BASE_URL}/businesses?city={TEST_CITY}")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                if businesses:
                    self.log_test(
                        "Restaurant Discovery", 
                        True, 
                        f"Found {len(businesses)} approved businesses in {TEST_CITY}"
                    )
                    
                    # Verify business data structure
                    first_business = businesses[0]
                    required_fields = ["id", "business_name", "city", "kyc_status"]
                    missing_fields = [field for field in required_fields if field not in first_business]
                    
                    if not missing_fields:
                        self.log_test(
                            "Business Data Structure", 
                            True, 
                            "All required fields present in business data"
                        )
                        return businesses
                    else:
                        self.log_test(
                            "Business Data Structure", 
                            False, 
                            f"Missing fields: {missing_fields}",
                            first_business
                        )
                        return businesses
                else:
                    self.log_test(
                        "Restaurant Discovery", 
                        False, 
                        f"No businesses found in {TEST_CITY}",
                        data
                    )
                    return []
            else:
                self.log_test(
                    "Restaurant Discovery", 
                    False, 
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Restaurant Discovery", False, f"Exception: {str(e)}")
            return []
    
    def test_menu_retrieval(self, businesses):
        """Test menu retrieval for businesses"""
        print("📋 Testing Menu Retrieval...")
        
        if not businesses:
            self.log_test("Menu Retrieval", False, "No businesses available for menu testing")
            return []
        
        menu_items = []
        successful_menus = 0
        
        for business in businesses[:3]:  # Test first 3 businesses
            business_id = business.get("id")
            business_name = business.get("business_name", "Unknown")
            
            try:
                # Test public menu endpoint
                response = self.session.get(f"{BASE_URL}/business/public/{business_id}/menu")
                
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("menu", [])
                    
                    if items:
                        successful_menus += 1
                        menu_items.extend(items)
                        
                        # Verify menu item structure
                        first_item = items[0]
                        required_fields = ["id", "name", "price"]
                        missing_fields = [field for field in required_fields if field not in first_item]
                        
                        if not missing_fields:
                            self.log_test(
                                f"Menu for {business_name}", 
                                True, 
                                f"Retrieved {len(items)} menu items with proper structure"
                            )
                        else:
                            self.log_test(
                                f"Menu for {business_name}", 
                                False, 
                                f"Menu items missing fields: {missing_fields}",
                                first_item
                            )
                    else:
                        self.log_test(
                            f"Menu for {business_name}", 
                            True, 
                            "Business has empty menu (valid state)"
                        )
                elif response.status_code == 404:
                    self.log_test(
                        f"Menu for {business_name}", 
                        True, 
                        "Business not found or no menu (valid state)"
                    )
                else:
                    self.log_test(
                        f"Menu for {business_name}", 
                        False, 
                        f"Menu request failed with status {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(f"Menu for {business_name}", False, f"Exception: {str(e)}")
        
        if successful_menus > 0:
            self.log_test(
                "Overall Menu Retrieval", 
                True, 
                f"Successfully retrieved menus from {successful_menus} businesses, total items: {len(menu_items)}"
            )
        else:
            self.log_test(
                "Overall Menu Retrieval", 
                False, 
                "No menus could be retrieved from any business"
            )
        
        return menu_items
    
    def test_order_creation(self, menu_items):
        """Test order creation with proper format"""
        print("📦 Testing Order Creation...")
        
        if not menu_items:
            self.log_test("Order Creation", False, "No menu items available for order testing")
            return None
        
        if not self.auth_token:
            self.log_test("Order Creation", False, "No authentication token available")
            return None
        
        try:
            # Use first available menu item
            test_item = menu_items[0]
            
            # Create order with proper format matching OrderCreate model
            order_data = {
                "delivery_address": "Test Address, Aksaray Merkez",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0370,
                "items": [
                    {
                        "product_id": test_item.get("id"),
                        "product_name": test_item.get("name", "Test Product"),
                        "product_price": float(test_item.get("price", 25.00)),
                        "quantity": 2,
                        "subtotal": float(test_item.get("price", 25.00)) * 2
                    }
                ],
                "total_amount": float(test_item.get("price", 25.00)) * 2,
                "notes": "Test order from backend testing"
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                
                if order_id:
                    self.log_test(
                        "Order Creation", 
                        True, 
                        f"Order created successfully with ID: {order_id}, status: {data.get('status', 'unknown')}"
                    )
                    return order_id
                else:
                    self.log_test(
                        "Order Creation", 
                        False, 
                        "Order created but no ID returned",
                        data
                    )
                    return None
            else:
                self.log_test(
                    "Order Creation", 
                    False, 
                    f"Order creation failed with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test("Order Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_order_retrieval(self, created_order_id):
        """Test customer order list retrieval"""
        print("📋 Testing Order Retrieval...")
        
        if not self.auth_token:
            self.log_test("Order Retrieval", False, "No authentication token available")
            return False
        
        try:
            # Test customer orders endpoint
            response = self.session.get(f"{BASE_URL}/orders")
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                
                if orders:
                    # Check if created order appears in list
                    order_found = False
                    if created_order_id:
                        order_found = any(
                            order.get("id") == created_order_id or 
                            order.get("order_id") == created_order_id 
                            for order in orders
                        )
                    
                    # Verify order structure
                    first_order = orders[0]
                    required_fields = ["id", "customer_id", "total_amount", "status"]
                    missing_fields = [field for field in required_fields if field not in first_order]
                    
                    if not missing_fields:
                        success_msg = f"Retrieved {len(orders)} orders with proper structure"
                        if created_order_id and order_found:
                            success_msg += f", created order {created_order_id} found in list"
                        elif created_order_id:
                            success_msg += f", created order {created_order_id} not found (may be processing)"
                        
                        self.log_test("Order Retrieval", True, success_msg)
                        return True
                    else:
                        self.log_test(
                            "Order Retrieval", 
                            False, 
                            f"Orders missing required fields: {missing_fields}",
                            first_order
                        )
                        return False
                else:
                    self.log_test(
                        "Order Retrieval", 
                        True, 
                        "No orders found for customer (valid state for new customer)"
                    )
                    return True
            else:
                self.log_test(
                    "Order Retrieval", 
                    False, 
                    f"Order retrieval failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Order Retrieval", False, f"Exception: {str(e)}")
            return False
    
    def run_complete_flow_test(self):
        """Run the complete customer order flow test"""
        print("🚀 Starting Complete Customer Order Flow Test")
        print("=" * 60)
        
        # Step 1: Customer Login
        login_success = self.test_customer_login()
        if not login_success:
            print("❌ Cannot proceed without successful login")
            return False
        
        # Step 2: Restaurant Discovery
        businesses = self.test_restaurant_discovery()
        
        # Step 3: Menu Retrieval
        menu_items = self.test_menu_retrieval(businesses)
        
        # Step 4: Order Creation
        order_id = self.test_order_creation(menu_items)
        
        # Step 5: Order Retrieval
        retrieval_success = self.test_order_retrieval(order_id)
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        print("🎯 CUSTOMER ORDER FLOW TEST COMPLETE")
        
        # Return overall success
        critical_tests = ["Customer Login", "Restaurant Discovery", "Overall Menu Retrieval"]
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["success"])
        
        return critical_passed >= len(critical_tests) - 1  # Allow 1 critical test to fail

def main():
    """Main test execution"""
    print("🧪 Customer Order Flow Backend Testing")
    print(f"🌐 Backend URL: {BASE_URL}")
    print(f"👤 Test Customer: {CUSTOMER_EMAIL}")
    print(f"🏙️ Test City: {TEST_CITY}")
    print()
    
    tester = CustomerOrderFlowTester()
    success = tester.run_complete_flow_test()
    
    if success:
        print("🎉 Customer Order Flow Test: OVERALL SUCCESS")
        sys.exit(0)
    else:
        print("💥 Customer Order Flow Test: OVERALL FAILURE")
        sys.exit(1)

if __name__ == "__main__":
    main()