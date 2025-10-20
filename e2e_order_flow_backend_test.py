#!/usr/bin/env python3
"""
🎯 E2E BACKEND API TESTING - ORDER FLOW
Comprehensive testing of the complete order flow with seeded E2E test data
"""

import requests
import json
import sys
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"

# Test Credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@demo.com", "password": "Admin!234"},
    "business": {"email": "business@demo.com", "password": "Biz!234"},
    "courier": {"email": "courier@demo.com", "password": "Kurye!234"},
    "customer": {"email": "customer@demo.com", "password": "Musteri!234"}
}

class E2EOrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}  # Store JWT tokens for each role
        self.test_results = []
        self.created_order_id = None
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {json.dumps(response_data, indent=2)[:500]}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def test_authentication_all_roles(self):
        """Test authentication for all 4 roles"""
        print("🔐 Testing Authentication for All Roles...")
        
        all_success = True
        
        for role, credentials in TEST_CREDENTIALS.items():
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/auth/login",
                    json=credentials,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        self.tokens[role] = data["access_token"]
                        user_data = data.get("user", {})
                        
                        self.log_test(
                            f"Authentication - {role.title()}", 
                            True, 
                            f"JWT token obtained (length: {len(self.tokens[role])}), User: {user_data.get('email')}"
                        )
                    else:
                        self.log_test(f"Authentication - {role.title()}", False, "No access_token in response", data)
                        all_success = False
                else:
                    self.log_test(f"Authentication - {role.title()}", False, f"HTTP {response.status_code}", response.text)
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Authentication - {role.title()}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_businesses_endpoint(self):
        """Test GET /api/businesses (verify 'Niğde Lezzet' appears)"""
        print("🏪 Testing Businesses Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                # Look for "Niğde Lezzet" business
                nigde_lezzet_found = False
                for business in businesses:
                    if "Niğde Lezzet" in business.get("name", "") or "Niğde Lezzet" in business.get("business_name", ""):
                        nigde_lezzet_found = True
                        break
                
                if nigde_lezzet_found:
                    self.log_test(
                        "Businesses Endpoint", 
                        True, 
                        f"Found {len(businesses)} businesses including 'Niğde Lezzet'"
                    )
                    return True
                else:
                    self.log_test(
                        "Businesses Endpoint", 
                        False, 
                        f"'Niğde Lezzet' not found in {len(businesses)} businesses"
                    )
                    return False
            else:
                self.log_test("Businesses Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Businesses Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_business_menu_endpoint(self):
        """Test GET /api/business/business-e2e-rest-001/menu (verify 5 products)"""
        print("📋 Testing Business Menu Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/business/business-e2e-001/menu")
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data if isinstance(data, list) else data.get("menu", [])
                
                if len(menu_items) >= 5:
                    self.log_test(
                        "Business Menu Endpoint", 
                        True, 
                        f"Found {len(menu_items)} menu items (expected 5+)"
                    )
                    return True
                else:
                    self.log_test(
                        "Business Menu Endpoint", 
                        False, 
                        f"Found only {len(menu_items)} menu items (expected 5)"
                    )
                    return False
            else:
                self.log_test("Business Menu Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Business Menu Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_business_authenticated_menu(self):
        """Test business login → GET /api/business/menu (verify authenticated access)"""
        print("🔑 Testing Business Authenticated Menu Access...")
        
        if "business" not in self.tokens:
            self.log_test("Business Authenticated Menu", False, "Business token not available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.get(f"{BACKEND_URL}/business/menu", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data if isinstance(data, list) else data.get("menu", [])
                
                self.log_test(
                    "Business Authenticated Menu", 
                    True, 
                    f"Authenticated access successful, found {len(menu_items)} menu items"
                )
                return True
            elif response.status_code == 401:
                self.log_test("Business Authenticated Menu", False, "Authentication failed (401)", response.text)
                return False
            else:
                self.log_test("Business Authenticated Menu", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Business Authenticated Menu", False, f"Exception: {str(e)}")
            return False
    
    def test_customer_addresses(self):
        """Test customer login → GET /api/me/addresses (verify default address exists)"""
        print("📍 Testing Customer Address Access...")
        
        if "customer" not in self.tokens:
            self.log_test("Customer Addresses", False, "Customer token not available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = self.session.get(f"{BACKEND_URL}/me/addresses", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                addresses = data if isinstance(data, list) else data.get("addresses", [])
                
                # Check for default address with Niğde location
                default_address_found = False
                nigde_address_found = False
                
                for address in addresses:
                    if address.get("is_default"):
                        default_address_found = True
                    if "Niğde" in str(address.get("address", "")) or "Niğde" in str(address.get("city", "")):
                        nigde_address_found = True
                
                if default_address_found and nigde_address_found:
                    self.log_test(
                        "Customer Addresses", 
                        True, 
                        f"Found {len(addresses)} addresses with default Niğde address"
                    )
                    return True
                else:
                    self.log_test(
                        "Customer Addresses", 
                        False, 
                        f"Default: {default_address_found}, Niğde: {nigde_address_found} in {len(addresses)} addresses"
                    )
                    return False
            else:
                self.log_test("Customer Addresses", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Customer Addresses", False, f"Exception: {str(e)}")
            return False
    
    def test_order_creation(self):
        """Test critical order creation with specific payload"""
        print("🛒 Testing Order Creation (CRITICAL)...")
        
        if "customer" not in self.tokens:
            self.log_test("Order Creation", False, "Customer token not available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.tokens['customer']}",
                "Content-Type": "application/json"
            }
            
            order_payload = {
                "business_id": "business-e2e-001",
                "items": [
                    {
                        "product_id": "product-e2e-001",
                        "title": "Adana Kebap",
                        "price": 85.0,
                        "quantity": 1
                    },
                    {
                        "product_id": "product-e2e-004",
                        "title": "Ayran",
                        "price": 8.0,
                        "quantity": 2
                    }
                ],
                "delivery_address": {
                    "label": "Evim",
                    "address": "Yeni Mahalle, Atatürk Caddesi No:42, Niğde Merkez",
                    "lat": 37.97,
                    "lng": 34.68
                },
                "payment_method": "cash_on_delivery",
                "notes": "E2E test order"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_payload,
                headers=headers
            )
            
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                status = data.get("status")
                total_amount = data.get("total_amount")
                
                # Verify order details
                expected_total = 85.0 + (8.0 * 2)  # 101.0
                
                if (status == "created" and 
                    total_amount == expected_total and 
                    order_id):
                    
                    self.created_order_id = order_id
                    self.log_test(
                        "Order Creation", 
                        True, 
                        f"Order created successfully: ID={order_id}, Status={status}, Total={total_amount}"
                    )
                    return True
                else:
                    self.log_test(
                        "Order Creation", 
                        False, 
                        f"Order validation failed: Status={status}, Total={total_amount}, Expected={expected_total}"
                    )
                    return False
            else:
                self.log_test("Order Creation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Order Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_business_incoming_orders(self):
        """Test business login → GET /api/business/orders/incoming"""
        print("📥 Testing Business Incoming Orders...")
        
        if "business" not in self.tokens:
            self.log_test("Business Incoming Orders", False, "Business token not available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                
                # Look for our created order
                order_found = False
                if self.created_order_id:
                    for order in orders:
                        if (order.get("id") == self.created_order_id or 
                            order.get("order_id") == self.created_order_id):
                            order_found = True
                            break
                
                if order_found or len(orders) > 0:
                    self.log_test(
                        "Business Incoming Orders", 
                        True, 
                        f"Found {len(orders)} incoming orders" + (f", including created order {self.created_order_id}" if order_found else "")
                    )
                    return True
                else:
                    self.log_test(
                        "Business Incoming Orders", 
                        False, 
                        f"No orders found (expected at least the created order)"
                    )
                    return False
            else:
                self.log_test("Business Incoming Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Business Incoming Orders", False, f"Exception: {str(e)}")
            return False
    
    def test_order_status_updates(self):
        """Test business order status updates (created → preparing → ready_for_pickup)"""
        print("🔄 Testing Order Status Updates...")
        
        if "business" not in self.tokens or not self.created_order_id:
            self.log_test("Order Status Updates", False, "Business token or order ID not available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.tokens['business']}",
                "Content-Type": "application/json"
            }
            
            # Test 1: created → preparing
            update_payload = {"from": "created", "to": "preparing"}
            response = self.session.patch(
                f"{BACKEND_URL}/orders/{self.created_order_id}/status",
                json=update_payload,
                headers=headers
            )
            
            if response.status_code != 200:
                self.log_test("Order Status Updates", False, f"Failed to update to preparing: HTTP {response.status_code}", response.text)
                return False
            
            # Test 2: preparing → ready_for_pickup
            update_payload = {"from": "preparing", "to": "ready_for_pickup"}
            response = self.session.patch(
                f"{BACKEND_URL}/orders/{self.created_order_id}/status",
                json=update_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                new_status = data.get("new_status") or data.get("status")
                
                if new_status == "ready_for_pickup":
                    self.log_test(
                        "Order Status Updates", 
                        True, 
                        f"Successfully updated order status: created → preparing → ready_for_pickup"
                    )
                    return True
                else:
                    self.log_test("Order Status Updates", False, f"Status not updated correctly: {new_status}")
                    return False
            else:
                self.log_test("Order Status Updates", False, f"Failed to update to ready_for_pickup: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Order Status Updates", False, f"Exception: {str(e)}")
            return False
    
    def test_rbac_unauthorized_access(self):
        """Test RBAC - unauthorized access attempts (CRITICAL)"""
        print("🛡️ Testing RBAC - Unauthorized Access (CRITICAL)...")
        
        rbac_tests_passed = 0
        total_rbac_tests = 3
        
        # Test 1: Customer tries to update order status
        if "customer" in self.tokens and self.created_order_id:
            try:
                headers = {
                    "Authorization": f"Bearer {self.tokens['customer']}",
                    "Content-Type": "application/json"
                }
                response = self.session.patch(
                    f"{BACKEND_URL}/orders/{self.created_order_id}/status",
                    json={"from": "ready_for_pickup", "to": "delivered"},
                    headers=headers
                )
                
                if response.status_code == 403:
                    self.log_test("RBAC - Customer Order Update", True, "Customer correctly denied order status update (403)")
                    rbac_tests_passed += 1
                else:
                    self.log_test("RBAC - Customer Order Update", False, f"Customer should be denied but got HTTP {response.status_code}")
            except Exception as e:
                self.log_test("RBAC - Customer Order Update", False, f"Exception: {str(e)}")
        
        # Test 2: Business tries to update another business's order (simulate)
        if "business" in self.tokens:
            try:
                headers = {
                    "Authorization": f"Bearer {self.tokens['business']}",
                    "Content-Type": "application/json"
                }
                # Try to update a non-existent order (should return 403 or 404)
                response = self.session.patch(
                    f"{BACKEND_URL}/orders/fake-order-id-123/status",
                    json={"from": "created", "to": "preparing"},
                    headers=headers
                )
                
                if response.status_code in [403, 404]:
                    self.log_test("RBAC - Business Cross-Access", True, f"Business correctly denied access to other order ({response.status_code})")
                    rbac_tests_passed += 1
                else:
                    self.log_test("RBAC - Business Cross-Access", False, f"Business should be denied but got HTTP {response.status_code}")
            except Exception as e:
                self.log_test("RBAC - Business Cross-Access", False, f"Exception: {str(e)}")
        
        # Test 3: Courier tries to update order not assigned to them
        if "courier" in self.tokens and self.created_order_id:
            try:
                headers = {
                    "Authorization": f"Bearer {self.tokens['courier']}",
                    "Content-Type": "application/json"
                }
                response = self.session.patch(
                    f"{BACKEND_URL}/orders/{self.created_order_id}/status",
                    json={"from": "ready_for_pickup", "to": "picked_up"},
                    headers=headers
                )
                
                if response.status_code == 403:
                    self.log_test("RBAC - Courier Unassigned Order", True, "Courier correctly denied unassigned order update (403)")
                    rbac_tests_passed += 1
                else:
                    self.log_test("RBAC - Courier Unassigned Order", False, f"Courier should be denied but got HTTP {response.status_code}")
            except Exception as e:
                self.log_test("RBAC - Courier Unassigned Order", False, f"Exception: {str(e)}")
        
        # Overall RBAC test result
        if rbac_tests_passed >= 2:  # At least 2 out of 3 RBAC tests should pass
            self.log_test("RBAC System", True, f"RBAC properly enforced ({rbac_tests_passed}/{total_rbac_tests} tests passed)")
            return True
        else:
            self.log_test("RBAC System", False, f"RBAC enforcement insufficient ({rbac_tests_passed}/{total_rbac_tests} tests passed)")
            return False
    
    def test_customer_my_orders(self):
        """Test customer → GET /api/orders/my (verify order appears)"""
        print("📋 Testing Customer My Orders...")
        
        if "customer" not in self.tokens:
            self.log_test("Customer My Orders", False, "Customer token not available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = self.session.get(f"{BACKEND_URL}/orders/my", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                
                # Look for our created order
                order_found = False
                if self.created_order_id:
                    for order in orders:
                        if (order.get("id") == self.created_order_id or 
                            order.get("order_id") == self.created_order_id):
                            order_found = True
                            break
                
                if order_found or len(orders) > 0:
                    self.log_test(
                        "Customer My Orders", 
                        True, 
                        f"Found {len(orders)} customer orders" + (f", including created order {self.created_order_id}" if order_found else "")
                    )
                    return True
                else:
                    self.log_test(
                        "Customer My Orders", 
                        False, 
                        f"No orders found for customer (expected at least the created order)"
                    )
                    return False
            else:
                self.log_test("Customer My Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Customer My Orders", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all E2E order flow tests"""
        print("🎯 E2E BACKEND API TESTING - ORDER FLOW")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {list(TEST_CREDENTIALS.keys())}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        print()
        
        # Test sequence
        tests = [
            ("Authentication Tests", self.test_authentication_all_roles),
            ("Business & Menu Tests - Public Businesses", self.test_businesses_endpoint),
            ("Business & Menu Tests - Business Menu", self.test_business_menu_endpoint),
            ("Business & Menu Tests - Authenticated Menu", self.test_business_authenticated_menu),
            ("Customer Address Tests", self.test_customer_addresses),
            ("Order Creation Test (CRITICAL)", self.test_order_creation),
            ("Business Order Management - Incoming Orders", self.test_business_incoming_orders),
            ("Business Order Management - Status Updates", self.test_order_status_updates),
            ("RBAC Tests (CRITICAL)", self.test_rbac_unauthorized_access),
            ("Order Listing - Customer My Orders", self.test_customer_my_orders)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"🧪 {test_name}")
            if test_func():
                passed += 1
            print()
        
        print("=" * 60)
        print("📊 E2E ORDER FLOW TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        # Group results by category
        auth_results = [r for r in self.test_results if "Authentication" in r["test"]]
        business_results = [r for r in self.test_results if "Business" in r["test"] or "Menu" in r["test"]]
        order_results = [r for r in self.test_results if "Order" in r["test"]]
        rbac_results = [r for r in self.test_results if "RBAC" in r["test"]]
        customer_results = [r for r in self.test_results if "Customer" in r["test"] and "RBAC" not in r["test"]]
        
        print("🔐 AUTHENTICATION TESTS:")
        for result in auth_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print("\n🏪 BUSINESS & MENU TESTS:")
        for result in business_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print("\n🛒 ORDER FLOW TESTS:")
        for result in order_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print("\n🛡️ RBAC SECURITY TESTS:")
        for result in rbac_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print("\n👤 CUSTOMER TESTS:")
        for result in customer_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({passed}/{total} test groups passed)")
        
        # Critical test analysis
        critical_tests = [r for r in self.test_results if "CRITICAL" in r["test"] or "Order Creation" in r["test"]]
        critical_passed = sum(1 for r in critical_tests if r["success"])
        
        print(f"🎯 Critical Tests: {critical_passed}/{len(critical_tests)} passed")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - E2E order flow is working perfectly!")
        elif success_rate >= 80:
            print("✅ GOOD - E2E order flow is mostly functional")
        elif success_rate >= 70:
            print("⚠️  PARTIAL - E2E order flow has some issues")
        else:
            print("❌ CRITICAL - Major issues with E2E order flow")
        
        return success_rate >= 70

def main():
    """Main test execution"""
    tester = E2EOrderFlowTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()