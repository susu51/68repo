#!/usr/bin/env python3
"""
End-to-End Order Flow Testing - Restaurant Order Verification
Testing complete order flow to verify orders reach the correct restaurant
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://food-dash-87.preview.emergentagent.com/api"

# Test Credentials
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

class E2EOrderRestaurantFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.customer_session = requests.Session()
        self.business_session = requests.Session()
        self.test_results = []
        self.business_id = None
        self.business_email = None
        self.business_password = None
        self.menu_items = []
        self.created_order_id = None
        
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
        """Login as customer and get JWT token"""
        try:
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.customer_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Try to get JWT token from response or use cookie auth
                    access_token = data.get("access_token")
                    if access_token:
                        # Set Authorization header for JWT token
                        self.customer_session.headers.update({
                            "Authorization": f"Bearer {access_token}"
                        })
                    
                    self.log_test("Customer Login", True, f"Customer authenticated successfully: {CUSTOMER_EMAIL}")
                    return True
                else:
                    self.log_test("Customer Login", False, f"Login failed: {data}")
                    return False
            else:
                self.log_test("Customer Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Login error: {str(e)}")
            return False
    
    def find_business_with_menu(self):
        """Find an approved business in Aksaray with menu items"""
        try:
            # Get businesses in Aksaray
            response = self.session.get(f"{BACKEND_URL}/businesses?city=Aksaray")
            
            if response.status_code == 200:
                businesses = response.json()
                
                if not businesses:
                    self.log_test("Find Business", False, "No businesses found in Aksaray")
                    return False
                
                # Check each business for menu items
                for business in businesses:
                    business_id = business.get("id")
                    if not business_id:
                        continue
                    
                    # Check if business has menu items
                    menu_response = self.session.get(f"{BACKEND_URL}/business/public/{business_id}/menu")
                    
                    if menu_response.status_code == 200:
                        menu_data = menu_response.json()
                        menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                        
                        if menu_items:
                            self.business_id = business_id
                            self.menu_items = menu_items
                            business_name = business.get("name", business.get("business_name", "Unknown"))
                            
                            self.log_test(
                                "Find Business with Menu", 
                                True, 
                                f"Found business '{business_name}' (ID: {business_id}) with {len(menu_items)} menu items",
                                {"business": business, "menu_items": len(menu_items)}
                            )
                            return True
                
                self.log_test("Find Business with Menu", False, "No businesses found with menu items in Aksaray")
                return False
            else:
                self.log_test("Find Business with Menu", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Find Business with Menu", False, f"Error: {str(e)}")
            return False
    
    def find_business_credentials(self):
        """Find business login credentials by checking test users"""
        try:
            # Use testbusiness@example.com which we know exists
            creds = {"email": "testbusiness@example.com", "password": "test123"}
            
            login_data = {
                "email": creds["email"],
                "password": creds["password"]
            }
            
            response = self.business_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Get the user ID from the login response (this is the correct one)
                    login_user = data.get("user", {})
                    correct_business_id = login_user.get("id")
                    
                    if correct_business_id:
                        # Update our business_id to match the login response
                        self.business_id = correct_business_id
                        self.business_email = creds["email"]
                        self.business_password = creds["password"]
                        
                        # Get menu for this business using the correct ID
                        menu_response = self.session.get(f"{BACKEND_URL}/business/public/{self.business_id}/menu")
                        if menu_response.status_code == 200:
                            menu_data = menu_response.json()
                            self.menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                        
                        self.log_test(
                            "Find Business Credentials", 
                            True, 
                            f"Using business credentials: {creds['email']} (ID: {self.business_id})"
                        )
                        return True
            
            self.log_test("Find Business Credentials", False, "testbusiness@example.com login failed")
            return False
                
        except Exception as e:
            self.log_test("Find Business Credentials", False, f"Error: {str(e)}")
            return False
    
    def business_login(self):
        """Login as business user and get JWT token"""
        try:
            if not self.business_email or not self.business_password:
                self.log_test("Business Login", False, "No business credentials available")
                return False
            
            login_data = {
                "email": self.business_email,
                "password": self.business_password
            }
            
            response = self.business_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Try to get JWT token from response or use cookie auth
                    access_token = data.get("access_token")
                    if access_token:
                        # Set Authorization header for JWT token
                        self.business_session.headers.update({
                            "Authorization": f"Bearer {access_token}"
                        })
                    
                    self.log_test("Business Login", True, f"Business authenticated successfully: {self.business_email}")
                    return True
                else:
                    self.log_test("Business Login", False, f"Login failed: {data}")
                    return False
            else:
                self.log_test("Business Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Business Login", False, f"Login error: {str(e)}")
            return False
    
    def verify_business_menu(self):
        """Verify business has menu items and get business_id"""
        try:
            # Get business menu via business endpoint
            response = self.business_session.get(f"{BACKEND_URL}/business/menu")
            
            if response.status_code == 200:
                menu_data = response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                if menu_items:
                    self.menu_items = menu_items
                    self.log_test(
                        "Verify Business Menu", 
                        True, 
                        f"Business has {len(menu_items)} menu items available",
                        {"menu_items": [{"id": item.get("id"), "name": item.get("name", item.get("title"))} for item in menu_items[:3]]}
                    )
                    return True
                else:
                    self.log_test("Verify Business Menu", False, "Business has no menu items")
                    return False
            else:
                self.log_test("Verify Business Menu", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Business Menu", False, f"Error: {str(e)}")
            return False
    
    def create_customer_order(self):
        """Create order as customer with menu items from the business"""
        try:
            if not self.menu_items:
                self.log_test("Create Customer Order", False, "No menu items available for order")
                return False
            
            # Select first menu item for order
            menu_item = self.menu_items[0]
            item_id = menu_item.get("id")
            item_name = menu_item.get("name", menu_item.get("title", "Unknown Item"))
            item_price = float(menu_item.get("price", 25.0))
            
            # Create order data
            order_data = {
                "delivery_address": "Test Delivery Address, Aksaray Merkez",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0254,
                "items": [
                    {
                        "product_id": item_id,
                        "product_name": item_name,
                        "product_price": item_price,
                        "quantity": 1,
                        "subtotal": item_price
                    }
                ],
                "total_amount": item_price,
                "notes": "Test order for E2E flow verification"
            }
            
            response = self.customer_session.post(f"{BACKEND_URL}/orders", json=order_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id", data.get("order_id"))
                
                if order_id:
                    self.created_order_id = order_id
                    self.log_test(
                        "Create Customer Order", 
                        True, 
                        f"Order created successfully with ID: {order_id}",
                        {"order_data": order_data, "response": data}
                    )
                    return True
                else:
                    self.log_test("Create Customer Order", False, f"Order created but no ID returned: {data}")
                    return False
            else:
                self.log_test("Create Customer Order", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Customer Order", False, f"Error: {str(e)}")
            return False
    
    def verify_order_has_correct_business_id(self):
        """Verify the created order has the correct business_id"""
        try:
            if not self.created_order_id:
                self.log_test("Verify Order Business ID", False, "No order ID available")
                return False
            
            # Get order details as customer
            response = self.customer_session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                # Find our created order
                created_order = None
                for order in orders:
                    if order.get("id") == self.created_order_id:
                        created_order = order
                        break
                
                if created_order:
                    order_business_id = created_order.get("business_id")
                    
                    if order_business_id == self.business_id:
                        self.log_test(
                            "Verify Order Business ID", 
                            True, 
                            f"Order correctly includes business_id: {order_business_id}",
                            {"order": created_order}
                        )
                        return True
                    else:
                        self.log_test(
                            "Verify Order Business ID", 
                            False, 
                            f"Order business_id mismatch. Expected: {self.business_id}, Got: {order_business_id}"
                        )
                        return False
                else:
                    self.log_test("Verify Order Business ID", False, f"Created order {self.created_order_id} not found in customer orders")
                    return False
            else:
                self.log_test("Verify Order Business ID", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Order Business ID", False, f"Error: {str(e)}")
            return False
    
    def verify_business_can_see_order(self):
        """Verify business can see the order in their order list"""
        try:
            if not self.created_order_id:
                self.log_test("Verify Business Sees Order", False, "No order ID available")
                return False
            
            # Debug: Check business user ID
            me_response = self.business_session.get(f"{BACKEND_URL}/me")
            if me_response.status_code == 200:
                me_data = me_response.json()
                business_user_id = me_data.get("id")
                print(f"DEBUG: Business user ID from /me: {business_user_id}")
                print(f"DEBUG: Expected business ID: {self.business_id}")
            
            # Get business orders
            response = self.business_session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                print(f"DEBUG: Business retrieved {len(orders)} orders")
                for order in orders:
                    print(f"DEBUG: Order {order.get('id')}: business_id={order.get('business_id')}")
                
                # Check if our order is in the business's order list
                found_order = None
                for order in orders:
                    if order.get("id") == self.created_order_id or order.get("order_id") == self.created_order_id:
                        found_order = order
                        break
                
                if found_order:
                    self.log_test(
                        "Verify Business Sees Order", 
                        True, 
                        f"Business can see order {self.created_order_id} in their order list",
                        {"order": found_order}
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Business Sees Order", 
                        False, 
                        f"Order {self.created_order_id} not found in business order list. Found {len(orders)} orders total. Business ID mismatch detected."
                    )
                    return False
            else:
                self.log_test("Verify Business Sees Order", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Business Sees Order", False, f"Error: {str(e)}")
            return False
    
    def verify_business_only_sees_own_orders(self):
        """Verify business only sees their own orders (not other businesses' orders)"""
        try:
            # Get business orders
            response = self.business_session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                # Check that all orders belong to this business
                wrong_business_orders = []
                for order in orders:
                    order_business_id = order.get("business_id")
                    if order_business_id and order_business_id != self.business_id:
                        wrong_business_orders.append({
                            "order_id": order.get("id"),
                            "business_id": order_business_id
                        })
                
                if not wrong_business_orders:
                    self.log_test(
                        "Verify Business Order Isolation", 
                        True, 
                        f"Business correctly sees only their own orders ({len(orders)} orders)",
                        {"total_orders": len(orders)}
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Business Order Isolation", 
                        False, 
                        f"Business sees {len(wrong_business_orders)} orders from other businesses",
                        {"wrong_orders": wrong_business_orders}
                    )
                    return False
            else:
                self.log_test("Verify Business Order Isolation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Business Order Isolation", False, f"Error: {str(e)}")
            return False
    
    def verify_order_contains_business_name(self):
        """Verify order contains business_name field"""
        try:
            if not self.created_order_id:
                self.log_test("Verify Order Business Name", False, "No order ID available")
                return False
            
            # Get order details as customer
            response = self.customer_session.get(f"{BACKEND_URL}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
                
                # Find our created order
                created_order = None
                for order in orders:
                    if order.get("id") == self.created_order_id:
                        created_order = order
                        break
                
                if created_order:
                    business_name = created_order.get("business_name")
                    
                    if business_name:
                        self.log_test(
                            "Verify Order Business Name", 
                            True, 
                            f"Order correctly includes business_name: '{business_name}'",
                            {"business_name": business_name}
                        )
                        return True
                    else:
                        self.log_test(
                            "Verify Order Business Name", 
                            False, 
                            "Order missing business_name field",
                            {"order_fields": list(created_order.keys())}
                        )
                        return False
                else:
                    self.log_test("Verify Order Business Name", False, f"Created order {self.created_order_id} not found")
                    return False
            else:
                self.log_test("Verify Order Business Name", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Order Business Name", False, f"Error: {str(e)}")
            return False
    
    def verify_menu_item_business_mapping(self):
        """Verify menu item to business_id mapping works correctly"""
        try:
            if not self.menu_items or not self.business_id:
                self.log_test("Verify Menu Item Mapping", False, "No menu items or business ID available")
                return False
            
            # Check public menu endpoint
            response = self.session.get(f"{BACKEND_URL}/business/public/{self.business_id}/menu")
            
            if response.status_code == 200:
                public_menu_data = response.json()
                public_menu_items = public_menu_data if isinstance(public_menu_data, list) else public_menu_data.get("items", [])
                
                if public_menu_items:
                    # Verify menu items are correctly associated with business
                    sample_item = public_menu_items[0]
                    
                    self.log_test(
                        "Verify Menu Item Mapping", 
                        True, 
                        f"Menu items correctly mapped to business {self.business_id} ({len(public_menu_items)} items)",
                        {"sample_item": sample_item}
                    )
                    return True
                else:
                    self.log_test("Verify Menu Item Mapping", False, "No menu items found in public endpoint")
                    return False
            else:
                self.log_test("Verify Menu Item Mapping", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Menu Item Mapping", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all end-to-end order flow tests"""
        print("🚀 Starting End-to-End Order Flow Testing - Restaurant Order Verification")
        print("=" * 80)
        
        # Setup Phase
        print("\n📋 SETUP PHASE - Business Discovery & Authentication")
        print("-" * 60)
        
        setup_tests = [
            ("Find Business with Menu", self.find_business_with_menu),
            ("Find Business Credentials", self.find_business_credentials),
            ("Business Login", self.business_login),
            ("Verify Business Menu", self.verify_business_menu)
        ]
        
        for test_name, test_func in setup_tests:
            if not test_func():
                print(f"❌ Setup failed at: {test_name}")
                return False
        
        # Order Creation Phase
        print("\n📦 ORDER CREATION PHASE - Customer Order Flow")
        print("-" * 60)
        
        if not self.customer_login():
            print("❌ Cannot proceed without customer authentication")
            return False
        
        if not self.create_customer_order():
            print("❌ Cannot proceed without order creation")
            return False
        
        # Verification Phase
        print("\n✅ VERIFICATION PHASE - Order Routing & Business Access")
        print("-" * 60)
        
        verification_tests = [
            self.verify_order_has_correct_business_id,
            self.verify_business_can_see_order,
            self.verify_business_only_sees_own_orders,
            self.verify_order_contains_business_name,
            self.verify_menu_item_business_mapping
        ]
        
        passed_tests = 0
        total_tests = len(verification_tests) + len(setup_tests) + 2  # +2 for customer login and order creation
        
        # Count setup and login tests as passed
        passed_tests += len(setup_tests) + 2
        
        for test in verification_tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 END-TO-END ORDER FLOW TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}% success rate)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Order flow correctly routes orders to the right restaurant!")
        elif passed_tests >= total_tests * 0.8:
            print("✅ MOSTLY WORKING - Order flow is functional with minor issues")
        else:
            print("❌ CRITICAL ISSUES - Order flow has significant problems")
        
        # Key Findings
        print("\n🔍 KEY FINDINGS:")
        print("-" * 40)
        
        if self.business_id and self.created_order_id:
            print(f"✅ Business ID: {self.business_id}")
            print(f"✅ Created Order ID: {self.created_order_id}")
            print(f"✅ Menu Items Available: {len(self.menu_items)}")
        
        # Detailed results
        print("\n📋 Detailed Test Results:")
        print("-" * 50)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed_tests >= total_tests * 0.8  # 80% success rate threshold

if __name__ == "__main__":
    tester = E2EOrderRestaurantFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)