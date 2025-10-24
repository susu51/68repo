#!/usr/bin/env python3
"""
CRITICAL BUSINESS ORDER FLOW TESTING - Turkish Scenario
Müşteri siparişinden işletme onayına ve kurye havuzuna kadar tüm akışı test et

Test Senaryosu:
1. Müşteri olarak login yap (test@kuryecini.com / test123)
2. Yeni bir sipariş oluştur
3. İşletme olarak login yap (test_business@example.com / test123)
4. GET /api/business/orders/incoming - Yeni sipariş geldi mi kontrol et
5. PATCH /api/orders/{order_id}/status - Siparişi onayla {"to": "confirmed"}
6. PATCH /api/orders/{order_id}/status - Hazır duruma getir {"to": "ready"}
7. Kurye olarak login yap (testkurye@example.com / test123)
8. GET /api/courier/tasks/nearby-businesses - İşletme listesinde var mı?
9. GET /api/courier/tasks/businesses/{business_id}/available-orders - Hazır sipariş görünüyor mu?
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from frontend environment
BASE_URL = "https://kuryecini-hub.preview.emergentagent.com/api"

class KuryeciniOrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'KuryeciniTester/1.0'
        })
        self.customer_token = None
        self.business_token = None
        self.courier_token = None
        self.order_id = None
        self.business_id = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"  # Test business ID
        
        # Test results tracking
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        
        self.results.append(result)
        if success:
            self.passed += 1
        else:
            self.failed += 1
        
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and response_data:
            print(f"   🔍 Response: {response_data}")
        print()

    def test_customer_login(self):
        """Test 1: Müşteri olarak login yap (test@kuryecini.com / test123)"""
        try:
            login_data = {
                "email": "test@kuryecini.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    # Set cookie-based authentication
                    self.customer_token = "cookie_auth"
                    user_info = data["user"]
                    self.log_result(
                        "Customer Login", 
                        True, 
                        f"Login successful for {user_info.get('email', 'N/A')}, Role: {user_info.get('role', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result("Customer Login", False, "Login response missing success or user data", data)
                    return False
            else:
                self.log_result("Customer Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Customer Login", False, f"Exception: {str(e)}")
            return False

    def test_create_order(self):
                        False, 

    def test_create_order(self):
        """Test 2: Yeni bir sipariş oluştur"""
        try:
            # First get menu items for the business
            menu_response = self.session.get(f"{BASE_URL}/business/public/{self.business_id}/menu")
            
            if menu_response.status_code != 200:
                self.log_result("Get Menu Items", False, f"Menu API failed: HTTP {menu_response.status_code}")
                return False
            
            # Menu API returns a list directly, not an object with "items"
            menu_items = menu_response.json()
            
            if not menu_items or not isinstance(menu_items, list):
                self.log_result("Get Menu Items", False, "No menu items found for business")
                return False
            
            # Use first menu item for order
            test_item = menu_items[0]
            
            order_data = {
                "restaurant_id": self.business_id,
                "items": [{
                    "product_id": test_item.get("id", "test"),
                    "title": test_item.get("name", "Test Ürün"),
                    "price": float(test_item.get("price", 25.0)),
                    "quantity": 2
                }],
                "delivery_address": "Test Adres, Ankara",
                "delivery_lat": 39.9334,
                "delivery_lng": 32.8597,
                "payment_method": "cash_on_delivery",
                "notes": "Test order for flow verification"
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                if "order" in data and "id" in data["order"]:
                    self.order_id = data["order"]["id"]
                    total_amount = data["order"].get("totals", {}).get("grand", 0)
                    order_code = data["order"].get("order_code", "N/A")
                    self.log_result(
                        "Create Order", 
                        True, 
                        f"Order created successfully. ID: {self.order_id}, Code: {order_code}, Total: ₺{total_amount}"
                    )
                    return True
                else:
                    self.log_result("Create Order", False, "Order response missing order.id", data)
                    return False
            else:
                self.log_result("Create Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Order", False, f"Exception: {str(e)}")
            return False

    def test_business_login(self):
        """Test 3: İşletme olarak login yap (testbusiness@example.com / test123)"""
        try:
            # Clear previous session
            self.session.cookies.clear()
            
            login_data = {
                "email": "testbusiness@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    self.business_token = "cookie_auth"
                    user_info = data["user"]
                    self.log_result(
                        "Business Login", 
                        True, 
                        f"Login successful for {user_info.get('email', 'N/A')}, Role: {user_info.get('role', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result("Business Login", False, "Login response missing success or user data", data)
                    return False
            else:
                self.log_result("Business Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Business Login", False, f"Exception: {str(e)}")
            return False

    def test_business_incoming_orders(self):
        """Test 4: GET /api/business/orders/incoming - Yeni sipariş geldi mi kontrol et"""
        try:
            response = self.session.get(f"{BASE_URL}/business/orders/incoming")
            
            if response.status_code == 200:
                # API returns a list directly
                orders = response.json()
                
                # Look for our test order
                test_order_found = False
                order_details = None
                
                for order in orders:
                    if order.get("id") == self.order_id or order.get("order_id") == self.order_id:
                        test_order_found = True
                        order_details = order
                        break
                
                if test_order_found:
                    customer_name = order_details.get("customer_name", "N/A")
                    customer_phone = order_details.get("customer_phone", "N/A")
                    total_orders = len(orders)
                    
                    self.log_result(
                        "Business Incoming Orders", 
                        True, 
                        f"Test order found! Total incoming orders: {total_orders}, Customer: {customer_name}, Phone: {customer_phone}"
                    )
                    return True
                else:
                    self.log_result(
                        "Business Incoming Orders", 
                        False, 
                        f"Test order {self.order_id} not found in {len(orders)} incoming orders"
                    )
                    return False
            else:
                self.log_result("Business Incoming Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Business Incoming Orders", False, f"Exception: {str(e)}")
            return False

    def test_confirm_order(self):
        """Test 5: PATCH /api/orders/{order_id}/status - Siparişi onayla {"to": "confirmed"}"""
        try:
            if not self.order_id:
                self.log_result("Confirm Order", False, "No order ID available")
                return False
            
            status_data = {"to": "confirmed"}
            response = self.session.patch(f"{BASE_URL}/business/orders/{self.order_id}/status", json=status_data)
            
            if response.status_code == 200:
                data = response.json()
                new_status = data.get("status", "unknown")
                self.log_result(
                    "Confirm Order", 
                    True, 
                    f"Order confirmed successfully. New status: {new_status}"
                )
                return True
            else:
                self.log_result("Confirm Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Confirm Order", False, f"Exception: {str(e)}")
            return False

    def test_ready_order(self):
        """Test 6: PATCH /api/orders/{order_id}/status - Hazır duruma getir {"to": "ready"}"""
        try:
            if not self.order_id:
                self.log_result("Ready Order", False, "No order ID available")
                return False
            
            status_data = {"to": "ready"}
            response = self.session.patch(f"{BASE_URL}/business/orders/{self.order_id}/status", json=status_data)
            
            if response.status_code == 200:
                data = response.json()
                new_status = data.get("status", "unknown")
                self.log_result(
                    "Ready Order", 
                    True, 
                    f"Order marked as ready. New status: {new_status}"
                )
                return True
            else:
                self.log_result("Ready Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Ready Order", False, f"Exception: {str(e)}")
            return False

    def test_courier_login(self):
        """Test 7: Kurye olarak login yap (testkurye@example.com / test123)"""
        try:
            # Clear previous session
            self.session.cookies.clear()
            
            login_data = {
                "email": "testkurye@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    self.courier_token = "cookie_auth"
                    user_info = data["user"]
                    self.log_result(
                        "Courier Login", 
                        True, 
                        f"Login successful for {user_info.get('email', 'N/A')}, Role: {user_info.get('role', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result("Courier Login", False, "Login response missing success or user data", data)
                    return False
            else:
                self.log_result("Courier Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Courier Login", False, f"Exception: {str(e)}")
            return False

    def test_courier_nearby_businesses(self):
        """Test 8: GET /api/courier/tasks/nearby-businesses - İşletme listesinde var mı?"""
        try:
            # Add required coordinates
            params = {
                "lat": 39.9334,
                "lng": 32.8597
            }
            response = self.session.get(f"{BASE_URL}/courier/tasks/nearby-businesses", params=params)
            
            if response.status_code == 200:
                # API returns a list directly
                businesses = response.json()
                
                # Look for our test business
                test_business_found = False
                business_details = None
                
                for business in businesses:
                    if business.get("id") == self.business_id or business.get("business_id") == self.business_id:
                        test_business_found = True
                        business_details = business
                        break
                
                if test_business_found:
                    business_name = business_details.get("name", "N/A")
                    ready_orders = business_details.get("ready_orders_count", 0)
                    
                    self.log_result(
                        "Courier Nearby Businesses", 
                        True, 
                        f"Test business found! Name: {business_name}, Ready orders: {ready_orders}, Total businesses: {len(businesses)}"
                    )
                    return True
                else:
                    self.log_result(
                        "Courier Nearby Businesses", 
                        False, 
                        f"Test business {self.business_id} not found in {len(businesses)} nearby businesses"
                    )
                    return False
            else:
                self.log_result("Courier Nearby Businesses", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Courier Nearby Businesses", False, f"Exception: {str(e)}")
            return False

    def test_courier_available_orders(self):
        """Test 9: GET /api/courier/tasks/businesses/{business_id}/available-orders - Hazır sipariş görünüyor mu?"""
        try:
            response = self.session.get(f"{BASE_URL}/courier/tasks/businesses/{self.business_id}/available-orders")
            
            if response.status_code == 200:
                # API might return a list directly or an object with orders
                response_data = response.json()
                if isinstance(response_data, list):
                    orders = response_data
                else:
                    orders = response_data.get("orders", [])
                
                # Look for our test order
                test_order_found = False
                order_details = None
                
                for order in orders:
                    if order.get("id") == self.order_id or order.get("order_id") == self.order_id:
                        test_order_found = True
                        order_details = order
                        break
                
                if test_order_found:
                    customer_name = order_details.get("customer_name", "N/A")
                    delivery_address = order_details.get("delivery_address", "N/A")
                    total_amount = order_details.get("total_amount", 0)
                    
                    self.log_result(
                        "Courier Available Orders", 
                        True, 
                        f"Test order found! Customer: {customer_name}, Amount: ₺{total_amount}, Address: {delivery_address}, Total available: {len(orders)}"
                    )
                    return True
                else:
                    self.log_result(
                        "Courier Available Orders", 
                        False, 
                        f"Test order {self.order_id} not found in {len(orders)} available orders"
                    )
                    return False
            else:
                self.log_result("Courier Available Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Courier Available Orders", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 CRITICAL BUSINESS ORDER FLOW TESTING - Turkish Scenario")
        print("=" * 70)
        print()
        
        # Test sequence
        tests = [
            self.test_customer_login,
            self.test_create_order,
            self.test_business_login,
            self.test_business_incoming_orders,
            self.test_confirm_order,
            self.test_ready_order,
            self.test_courier_login,
            self.test_courier_nearby_businesses,
            self.test_courier_available_orders
        ]
        
        for test in tests:
            test()
        
        # Summary
        print("=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(tests)
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! Complete order flow is working perfectly.")
            print("✅ Sipariş oluşturulmalı")
            print("✅ İşletme incoming orders'da görmeli (detaylarla)")
            print("✅ İşletme onaylayabilmeli (created → confirmed)")
            print("✅ İşletme hazır duruma getirebilmeli (confirmed → ready)")
            print("✅ Kurye haritada işletmeyi görmeli")
            print("✅ Kurye siparişi görebilmeli")
        else:
            print("❌ SOME TESTS FAILED! Check the details above.")
            print("\nFailed Tests:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print()
        return self.failed == 0

if __name__ == "__main__":
    tester = KuryeciniOrderFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
