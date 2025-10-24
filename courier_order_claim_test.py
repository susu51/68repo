#!/usr/bin/env python3
"""
COURIER ORDER CLAIMING FLOW TEST - Turkish Scenario
Kuryenin sipariş alma akışını test et

Test Senaryosu:
1. Kurye login (testkurye@example.com / test123)
2. GET /api/courier/tasks/nearby-businesses veya GET /api/map/businesses - Hazır siparişli işletmeleri listele
3. Bir business_id seç (örn: e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed)
4. GET /api/courier/tasks/businesses/{business_id}/available-orders - Hazır siparişleri getir
5. İlk sipariş ID'sini kaydet
6. POST /api/courier/tasks/orders/{order_id}/claim - Siparişi kabul et
7. GET /api/courier/tasks/my-orders - Alınan sipariş "Siparişlerim"de görünüyor mu?

Beklenen Sonuçlar:
✅ Kurye login başarılı
✅ İşletmeler listeleniyor
✅ Hazır siparişler görünüyor
✅ Claim başarılı (200 OK)
✅ Status: ready → assigned değişti mi?
✅ assigned_courier_id set edildi mi?
✅ "Siparişlerim"de görünüyor mu?
✅ Paket detayları tam mı? (müşteri, adres, ödeme, items)
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from frontend environment
BASE_URL = "https://kuryecini-hub.preview.emergentagent.com/api"

class CourierOrderClaimTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CourierClaimTester/1.0'
        })
        self.courier_token = None
        self.business_id = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"  # Test business ID
        self.order_id = None
        self.claimed_order_id = None
        
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

    def test_courier_login(self):
        """Test 1: Kurye login (testkurye@example.com / test123)"""
        try:
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

    def test_nearby_businesses(self):
        """Test 2: GET /api/courier/tasks/nearby-businesses - Hazır siparişli işletmeleri listele"""
        try:
            # Try both endpoints as mentioned in the request
            endpoints_to_try = [
                "/courier/tasks/nearby-businesses",
                "/map/businesses"
            ]
            
            for endpoint in endpoints_to_try:
                # Add required coordinates for nearby businesses
                params = {
                    "lat": 39.9334,
                    "lng": 32.8597
                }
                
                response = self.session.get(f"{BASE_URL}{endpoint}", params=params)
                
                if response.status_code == 200:
                    businesses = response.json()
                    
                    # Handle different response formats
                    if isinstance(businesses, dict) and "businesses" in businesses:
                        businesses = businesses["businesses"]
                    elif not isinstance(businesses, list):
                        businesses = []
                    
                    # Look for businesses with ready orders
                    businesses_with_orders = []
                    target_business_found = False
                    
                    for business in businesses:
                        ready_orders = business.get("ready_orders_count", 0)
                        if ready_orders > 0:
                            businesses_with_orders.append(business)
                        
                        # Check if our target business is in the list
                        if (business.get("id") == self.business_id or 
                            business.get("business_id") == self.business_id):
                            target_business_found = True
                    
                    if businesses_with_orders:
                        self.log_result(
                            f"Nearby Businesses ({endpoint})", 
                            True, 
                            f"Found {len(businesses_with_orders)} businesses with ready orders out of {len(businesses)} total. Target business found: {target_business_found}"
                        )
                        return True
                    else:
                        self.log_result(
                            f"Nearby Businesses ({endpoint})", 
                            False, 
                            f"No businesses with ready orders found. Total businesses: {len(businesses)}"
                        )
                        # Continue to try next endpoint
                        continue
                else:
                    self.log_result(f"Nearby Businesses ({endpoint})", False, f"HTTP {response.status_code}", response.text)
                    # Continue to try next endpoint
                    continue
            
            # If we reach here, all endpoints failed
            return False
                
        except Exception as e:
            self.log_result("Nearby Businesses", False, f"Exception: {str(e)}")
            return False

    def test_available_orders(self):
        """Test 3: GET /api/courier/tasks/businesses/{business_id}/available-orders - Hazır siparişleri getir"""
        try:
            response = self.session.get(f"{BASE_URL}/courier/tasks/businesses/{self.business_id}/available-orders")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle different response formats
                if isinstance(response_data, list):
                    orders = response_data
                elif isinstance(response_data, dict) and "orders" in response_data:
                    orders = response_data["orders"]
                else:
                    orders = []
                
                if orders:
                    # Save the first order ID for claiming
                    self.order_id = orders[0].get("id") or orders[0].get("order_id")
                    
                    # Get order details
                    first_order = orders[0]
                    customer_name = first_order.get("customer_name", "N/A")
                    delivery_address = first_order.get("delivery_address", "N/A")
                    total_amount = first_order.get("total_amount", 0)
                    status = first_order.get("status", "N/A")
                    
                    self.log_result(
                        "Available Orders", 
                        True, 
                        f"Found {len(orders)} available orders. First order ID: {self.order_id}, Customer: {customer_name}, Amount: ₺{total_amount}, Status: {status}"
                    )
                    return True
                else:
                    self.log_result(
                        "Available Orders", 
                        False, 
                        f"No available orders found for business {self.business_id}"
                    )
                    return False
            else:
                self.log_result("Available Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Available Orders", False, f"Exception: {str(e)}")
            return False

    def test_claim_order(self):
        """Test 4: POST /api/courier/tasks/orders/{order_id}/claim - Siparişi kabul et"""
        try:
            if not self.order_id:
                self.log_result("Claim Order", False, "No order ID available to claim")
                return False
            
            response = self.session.post(f"{BASE_URL}/courier/tasks/orders/{self.order_id}/claim")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if claim was successful
                success = data.get("success", False)
                message = data.get("message", "")
                
                if success:
                    self.claimed_order_id = self.order_id
                    self.log_result(
                        "Claim Order", 
                        True, 
                        f"Order claimed successfully! Order ID: {self.order_id}, Message: {message}"
                    )
                    return True
                else:
                    self.log_result("Claim Order", False, f"Claim failed: {message}", data)
                    return False
            else:
                self.log_result("Claim Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Claim Order", False, f"Exception: {str(e)}")
            return False

    def test_order_status_change(self):
        """Test 5: Verify Status: ready → assigned değişti mi?"""
        try:
            if not self.claimed_order_id:
                self.log_result("Order Status Change", False, "No claimed order ID available")
                return False
            
            # Try different endpoints to get order details
            endpoints_to_try = [
                f"/orders/{self.claimed_order_id}",
                f"/orders/{self.claimed_order_id}/track",
                f"/courier/tasks/orders/{self.claimed_order_id}",
                f"/courier/tasks/my-orders"
            ]
            
            for endpoint in endpoints_to_try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    order_data = response.json()
                    
                    # Handle different response formats
                    if endpoint.endswith("/my-orders"):
                        # This returns a list, find our order
                        if isinstance(order_data, list):
                            orders = order_data
                        elif isinstance(order_data, dict) and "orders" in order_data:
                            orders = order_data["orders"]
                        else:
                            continue
                        
                        order = None
                        for o in orders:
                            if (o.get("id") == self.claimed_order_id or 
                                o.get("order_id") == self.claimed_order_id):
                                order = o
                                break
                        
                        if not order:
                            continue
                    else:
                        # Single order response
                        if "order" in order_data:
                            order = order_data["order"]
                        else:
                            order = order_data
                    
                    current_status = order.get("status", "unknown")
                    assigned_courier_id = order.get("assigned_courier_id") or order.get("courier_id")
                    
                    if current_status == "assigned":
                        self.log_result(
                            "Order Status Change", 
                            True, 
                            f"Status successfully changed to 'assigned' (via {endpoint}). Assigned courier ID: {assigned_courier_id}"
                        )
                        return True
                    else:
                        # Continue trying other endpoints
                        continue
            
            # If we reach here, no endpoint returned the expected status
            self.log_result(
                "Order Status Change", 
                False, 
                f"Could not verify status change to 'assigned' via any endpoint"
            )
            return False
                
        except Exception as e:
            self.log_result("Order Status Change", False, f"Exception: {str(e)}")
            return False

    def test_my_orders(self):
        """Test 6: GET /api/courier/tasks/my-orders - Alınan sipariş "Siparişlerim"de görünüyor mu?"""
        try:
            response = self.session.get(f"{BASE_URL}/courier/tasks/my-orders")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle different response formats
                if isinstance(response_data, list):
                    my_orders = response_data
                elif isinstance(response_data, dict) and "orders" in response_data:
                    my_orders = response_data["orders"]
                else:
                    my_orders = []
                
                # Look for our claimed order
                claimed_order_found = False
                order_details = None
                
                for order in my_orders:
                    if (order.get("id") == self.claimed_order_id or 
                        order.get("order_id") == self.claimed_order_id):
                        claimed_order_found = True
                        order_details = order
                        break
                
                if claimed_order_found:
                    # Check if order has complete details
                    customer_name = order_details.get("customer_name", "N/A")
                    delivery_address = order_details.get("delivery_address", "N/A")
                    payment_method = order_details.get("payment_method", "N/A")
                    items = order_details.get("items", [])
                    business_name = order_details.get("business_name", "N/A")
                    
                    self.log_result(
                        "My Orders", 
                        True, 
                        f"Claimed order found in 'My Orders'! Customer: {customer_name}, Business: {business_name}, Items: {len(items)}, Payment: {payment_method}"
                    )
                    return True
                else:
                    self.log_result(
                        "My Orders", 
                        False, 
                        f"Claimed order {self.claimed_order_id} not found in {len(my_orders)} orders in 'My Orders'"
                    )
                    return False
            else:
                self.log_result("My Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("My Orders", False, f"Exception: {str(e)}")
            return False

    def test_package_details(self):
        """Test 7: Paket detayları tam mı? (müşteri, adres, ödeme, items)"""
        try:
            if not self.claimed_order_id:
                self.log_result("Package Details", False, "No claimed order ID available")
                return False
            
            # Get detailed order information
            response = self.session.get(f"{BASE_URL}/orders/{self.claimed_order_id}")
            
            if response.status_code == 200:
                order_data = response.json()
                
                # Handle different response formats
                if "order" in order_data:
                    order = order_data["order"]
                else:
                    order = order_data
                
                # Check required details
                required_fields = {
                    "customer_name": order.get("customer_name"),
                    "delivery_address": order.get("delivery_address"),
                    "payment_method": order.get("payment_method"),
                    "items": order.get("items", []),
                    "business_name": order.get("business_name"),
                    "total_amount": order.get("total_amount")
                }
                
                missing_fields = []
                for field, value in required_fields.items():
                    if not value or (isinstance(value, list) and len(value) == 0):
                        missing_fields.append(field)
                
                if not missing_fields:
                    items_count = len(required_fields["items"])
                    self.log_result(
                        "Package Details", 
                        True, 
                        f"All package details complete! Customer: {required_fields['customer_name']}, Business: {required_fields['business_name']}, Items: {items_count}, Payment: {required_fields['payment_method']}, Amount: ₺{required_fields['total_amount']}"
                    )
                    return True
                else:
                    self.log_result(
                        "Package Details", 
                        False, 
                        f"Missing package details: {', '.join(missing_fields)}"
                    )
                    return False
            else:
                self.log_result("Package Details", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Package Details", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 COURIER ORDER CLAIMING FLOW TEST - Turkish Scenario")
        print("=" * 70)
        print()
        
        # Test sequence
        tests = [
            self.test_courier_login,
            self.test_nearby_businesses,
            self.test_available_orders,
            self.test_claim_order,
            self.test_order_status_change,
            self.test_my_orders,
            self.test_package_details
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
            print("🎉 ALL TESTS PASSED! Courier order claiming flow is working perfectly.")
            print("✅ Kurye login başarılı")
            print("✅ İşletmeler listeleniyor")
            print("✅ Hazır siparişler görünüyor")
            print("✅ Claim başarılı (200 OK)")
            print("✅ Status: ready → assigned değişti")
            print("✅ assigned_courier_id set edildi")
            print("✅ 'Siparişlerim'de görünüyor")
            print("✅ Paket detayları tam (müşteri, adres, ödeme, items)")
        else:
            print("❌ SOME TESTS FAILED! Check the details above.")
            print("\nFailed Tests:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print()
        return self.failed == 0

if __name__ == "__main__":
    tester = CourierOrderClaimTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)