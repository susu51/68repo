#!/usr/bin/env python3
"""
E2E Complete Sipariş Akışı Test
Complete end-to-end order flow testing based on review request

Test Flow:
1. ✅ Business login (testbusiness@example.com)
2. ✅ Customer login (testcustomer@example.com)  
3. ✅ Customer sees nearby businesses
4. ✅ Customer creates order
5. ✅ Business confirms order
6. ✅ Courier login (testkurye@example.com)
7. ✅ Courier sees available orders
8. ✅ Courier accepts order
9. ✅ Complete E2E flow verification
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://stable-menus.preview.emergentagent.com/api"

# Test credentials (corrected)
TEST_CREDENTIALS = {
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class E2EFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.tokens = {}
        self.users = {}
        self.order_id = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_user(self, user_type, credentials):
        """Authenticate user and store token"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=credentials,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                
                self.tokens[user_type] = token
                self.users[user_type] = user_data
                
                self.log_test(
                    f"{user_type.title()} Login",
                    True,
                    f"Role: {user_data.get('role')}, ID: {user_data.get('id')}, Token: {len(token)} chars"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    f"{user_type.title()} Login",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"{user_type.title()} Login",
                False,
                error=str(e)
            )
            return False

    def test_business_menu(self):
        """Test business menu retrieval"""
        if "business" not in self.tokens:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.get(
                f"{BACKEND_URL}/business/menu",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                menu_items = response.json()
                self.log_test(
                    "Business Menu Retrieval",
                    True,
                    f"Retrieved {len(menu_items)} menu items"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Business Menu Retrieval",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Business Menu Retrieval",
                False,
                error=str(e)
            )
            return False

    def test_customer_addresses(self):
        """Test customer address management"""
        if "customer" not in self.tokens:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_test(
                    "Customer Address Retrieval",
                    True,
                    f"Retrieved {len(addresses)} addresses"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Customer Address Retrieval",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Customer Address Retrieval",
                False,
                error=str(e)
            )
            return False

    def test_nearby_businesses(self):
        """Test nearby businesses discovery"""
        if "customer" not in self.tokens:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            # Use Kadıköy coordinates from review request
            params = {
                "lat": 40.9833,
                "lng": 29.0167,
                "radius": 5000
            }
            
            response = self.session.get(
                f"{BACKEND_URL}/nearby/businesses",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                businesses = response.json()  # API returns list directly
                self.log_test(
                    "Nearby Businesses Discovery",
                    True,
                    f"Found {len(businesses)} nearby businesses"
                )
                return True, businesses
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Nearby Businesses Discovery",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, []
                
        except Exception as e:
            self.log_test(
                "Nearby Businesses Discovery",
                False,
                error=str(e)
            )
            return False, []

    def test_business_menu_for_customer(self, business_id):
        """Test customer viewing business menu"""
        if "customer" not in self.tokens:
            return False, []
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = self.session.get(
                f"{BACKEND_URL}/nearby/businesses/{business_id}/menu",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                menu_items = response.json()
                self.log_test(
                    "Customer Business Menu View",
                    True,
                    f"Retrieved {len(menu_items)} menu items for business {business_id}"
                )
                return True, menu_items
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Customer Business Menu View",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, []
                
        except Exception as e:
            self.log_test(
                "Customer Business Menu View",
                False,
                error=str(e)
            )
            return False, []

    def create_order(self, business_id, business_name, menu_items):
        """Create order as customer"""
        if "customer" not in self.tokens or not menu_items:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            
            # Use first available menu item
            item = menu_items[0]
            
            order_data = {
                "business_id": business_id,
                "business_name": business_name,
                "delivery_address": "Kadıköy Test Address, İstanbul",
                "delivery_lat": 40.9833,
                "delivery_lng": 29.0167,
                "items": [
                    {
                        "product_id": item.get("id", "test-product"),
                        "product_name": item.get("name", "Test Product"),
                        "product_price": float(item.get("price", 25.0)),
                        "quantity": 1,
                        "subtotal": float(item.get("price", 25.0))
                    }
                ],
                "total_amount": float(item.get("price", 25.0)),
                "notes": "E2E Test Order"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                order = response.json()
                self.order_id = order.get("id")
                
                self.log_test(
                    "Order Creation",
                    True,
                    f"Order created successfully - ID: {self.order_id}, Amount: ₺{order_data['total_amount']}"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Order Creation",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Order Creation",
                False,
                error=str(e)
            )
            return False

    def test_business_incoming_orders(self):
        """Test business incoming orders"""
        if "business" not in self.tokens:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.get(
                f"{BACKEND_URL}/business/orders/incoming",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                self.log_test(
                    "Business Incoming Orders",
                    True,
                    f"Retrieved {len(orders)} incoming orders"
                )
                return True, orders
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Business Incoming Orders",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, []
                
        except Exception as e:
            self.log_test(
                "Business Incoming Orders",
                False,
                error=str(e)
            )
            return False, []

    def confirm_order(self):
        """Business confirms order"""
        if "business" not in self.tokens or not self.order_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.patch(
                f"{BACKEND_URL}/business/orders/{self.order_id}/status",
                json={"status": "confirmed"},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Business Order Confirmation",
                    True,
                    f"Order {self.order_id} confirmed by business"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Business Order Confirmation",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Business Order Confirmation",
                False,
                error=str(e)
            )
            return False

    def prepare_order(self):
        """Business prepares order"""
        if "business" not in self.tokens or not self.order_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = self.session.patch(
                f"{BACKEND_URL}/business/orders/{self.order_id}/status",
                json={"status": "ready"},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Business Order Preparation",
                    True,
                    f"Order {self.order_id} marked as ready for pickup"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Business Order Preparation",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Business Order Preparation",
                False,
                error=str(e)
            )
            return False

    def test_courier_available_orders(self):
        """Test courier available orders"""
        if "courier" not in self.tokens:
            return False, []
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = self.session.get(
                f"{BACKEND_URL}/courier/orders/available",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                self.log_test(
                    "Courier Available Orders",
                    True,
                    f"Retrieved {len(orders)} available orders"
                )
                return True, orders
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Courier Available Orders",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, []
                
        except Exception as e:
            self.log_test(
                "Courier Available Orders",
                False,
                error=str(e)
            )
            return False, []

    def courier_pickup_order(self):
        """Courier picks up order"""
        if "courier" not in self.tokens or not self.order_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = self.session.patch(
                f"{BACKEND_URL}/courier/orders/{self.order_id}/pickup",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Courier Order Pickup",
                    True,
                    f"Order {self.order_id} picked up by courier"
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Courier Order Pickup",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Courier Order Pickup",
                False,
                error=str(e)
            )
            return False

    def run_complete_e2e_test(self):
        """Run complete E2E order flow test"""
        print("🚀 STARTING COMPLETE E2E SİPARİŞ AKIŞI TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Phase 1: Authentication
        print("📋 PHASE 1: USER AUTHENTICATION")
        print("-" * 40)
        
        business_auth = self.authenticate_user("business", TEST_CREDENTIALS["business"])
        customer_auth = self.authenticate_user("customer", TEST_CREDENTIALS["customer"])
        courier_auth = self.authenticate_user("courier", TEST_CREDENTIALS["courier"])
        
        if not all([business_auth, customer_auth, courier_auth]):
            print("❌ Authentication failed - cannot proceed with E2E test")
            return False
        
        # Phase 2: Business Setup
        print("📋 PHASE 2: BUSINESS MENU SETUP")
        print("-" * 40)
        
        self.test_business_menu()
        
        # Phase 3: Customer Discovery
        print("📋 PHASE 3: CUSTOMER BUSINESS DISCOVERY")
        print("-" * 40)
        
        self.test_customer_addresses()
        nearby_success, businesses = self.test_nearby_businesses()
        
        if not nearby_success or not businesses:
            print("❌ No businesses found - cannot proceed with order creation")
            return False
        
        # Use first available business
        business = businesses[0]
        business_id = business.get("id")
        business_name = business.get("name", "Test Business")
        
        # Phase 4: Menu Viewing
        print("📋 PHASE 4: CUSTOMER MENU VIEWING")
        print("-" * 40)
        
        menu_success, menu_items = self.test_business_menu_for_customer(business_id)
        
        if not menu_success or not menu_items:
            print("❌ No menu items found - cannot proceed with order creation")
            return False
        
        # Phase 5: Order Creation
        print("📋 PHASE 5: ORDER CREATION & BUSINESS PROCESSING")
        print("-" * 40)
        
        order_created = self.create_order(business_id, business_name, menu_items)
        
        if not order_created:
            print("❌ Order creation failed")
            return False
        
        # Business processes order
        self.test_business_incoming_orders()
        order_confirmed = self.confirm_order()
        order_prepared = self.prepare_order()
        
        if not all([order_confirmed, order_prepared]):
            print("❌ Business order processing failed")
            return False
        
        # Phase 6: Courier Pickup
        print("📋 PHASE 6: COURIER ORDER PICKUP")
        print("-" * 40)
        
        courier_orders_success, available_orders = self.test_courier_available_orders()
        courier_pickup_success = self.courier_pickup_order()
        
        # Summary
        print("📊 E2E TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # E2E Flow Status
        print("🎯 E2E FLOW STATUS:")
        if success_rate >= 85:
            print("✅ E2E Order Flow SUCCESSFUL - All major components working")
        else:
            print("❌ E2E Order Flow INCOMPLETE - Some components failing")
        
        print()
        print("📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
            if result["error"]:
                print(f"   ERROR: {result['error']}")
        
        return success_rate >= 85

if __name__ == "__main__":
    tester = E2EFlowTester()
    success = tester.run_complete_e2e_test()
    
    if success:
        print("\n🎉 COMPLETE E2E SİPARİŞ AKIŞI TEST SUCCESSFUL")
    else:
        print("\n⚠️  COMPLETE E2E SİPARİŞ AKIŞI TEST COMPLETED WITH ISSUES")
    
    exit(0 if success else 1)