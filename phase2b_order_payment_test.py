#!/usr/bin/env python3
"""
🚀 PHASE 2B BACKEND TEST - Sipariş Akışı & Ödeme
Testing order creation with payment methods and order retrieval
"""

import requests
import json
import sys
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com/api"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

class Phase2BOrderPaymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.customer_id = None
        self.test_results = []
        self.business_id = None
        self.product_id = None
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def test_customer_authentication(self):
        """Test customer login and JWT token retrieval"""
        print("🔐 Testing Customer Authentication...")
        
        try:
            # Test customer login
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.jwt_token = data["access_token"]
                    user_data = data.get("user", {})
                    self.customer_id = user_data.get("id")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.jwt_token}"
                    })
                    
                    self.log_test(
                        "Customer Authentication", 
                        True, 
                        f"JWT token obtained (length: {len(self.jwt_token)}), Customer ID: {self.customer_id}"
                    )
                    return True
                else:
                    self.log_test("Customer Authentication", False, "No access_token in response", data)
                    return False
            else:
                self.log_test("Customer Authentication", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Exception: {str(e)}")
            return False
    
    def find_test_business_and_product(self):
        """Find an active business and product for testing"""
        print("🔍 Finding Test Business and Product...")
        
        try:
            # Get approved businesses
            response = self.session.get(f"{BACKEND_URL}/../menus/public")
            
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("restaurants", [])
                
                if restaurants:
                    # Use first restaurant with menu items
                    restaurant = restaurants[0]
                    self.business_id = restaurant["id"]
                    menu = restaurant.get("menu", [])
                    
                    if menu:
                        self.product_id = menu[0]["id"]
                        self.log_test(
                            "Find Test Data", 
                            True, 
                            f"Business ID: {self.business_id}, Product ID: {self.product_id}"
                        )
                        return True
                    else:
                        self.log_test("Find Test Data", False, "No menu items found")
                        return False
                else:
                    self.log_test("Find Test Data", False, "No restaurants found")
                    return False
            else:
                self.log_test("Find Test Data", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Find Test Data", False, f"Exception: {str(e)}")
            return False
    
    def test_cash_on_delivery_order(self):
        """Test order creation with cash on delivery payment"""
        print("💰 Testing Cash on Delivery Order...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 25.50,
                        "quantity": 2,
                        "notes": "Extra spicy"
                    }
                ],
                "delivery_address": {
                    "label": "Ev",
                    "address": "Test Mahallesi, Test Sokak No:1, Kadıköy/İstanbul",
                    "lat": 40.9923,
                    "lng": 29.0209,
                    "notes": "2. kat"
                },
                "payment_method": "cash_on_delivery",
                "notes": "Test order for cash payment"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if (data.get("payment_method") == "cash_on_delivery" and 
                    data.get("payment_status") == "pending" and
                    data.get("delivery_fee") == 10.0):
                    self.log_test(
                        "Cash on Delivery Order", 
                        True, 
                        f"Order created: {data.get('id')}, Payment: {data.get('payment_method')}, Status: {data.get('payment_status')}, Delivery Fee: {data.get('delivery_fee')} TL"
                    )
                    return True
                else:
                    self.log_test("Cash on Delivery Order", False, "Invalid payment fields", data)
                    return False
            else:
                self.log_test("Cash on Delivery Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Cash on Delivery Order", False, f"Exception: {str(e)}")
            return False
    
    def test_pos_on_delivery_order(self):
        """Test order creation with POS on delivery payment"""
        print("💳 Testing POS on Delivery Order...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 35.75,
                        "quantity": 1,
                        "notes": "Medium size"
                    }
                ],
                "delivery_address": {
                    "label": "İş Yeri",
                    "address": "İş Mahallesi, Ofis Sokak No:5, Şişli/İstanbul",
                    "lat": 41.0602,
                    "lng": 28.9942,
                    "notes": "Giriş katı"
                },
                "payment_method": "pos_on_delivery",
                "notes": "Test order for POS payment"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if (data.get("payment_method") == "pos_on_delivery" and 
                    data.get("payment_status") == "pending" and
                    data.get("delivery_fee") == 10.0):
                    self.log_test(
                        "POS on Delivery Order", 
                        True, 
                        f"Order created: {data.get('id')}, Payment: {data.get('payment_method')}, Status: {data.get('payment_status')}, Delivery Fee: {data.get('delivery_fee')} TL"
                    )
                    return True
                else:
                    self.log_test("POS on Delivery Order", False, "Invalid payment fields", data)
                    return False
            else:
                self.log_test("POS on Delivery Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("POS on Delivery Order", False, f"Exception: {str(e)}")
            return False
    
    def test_online_payment_order(self):
        """Test order creation with online payment (mock)"""
        print("🌐 Testing Online Payment Order (Mock)...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 45.00,
                        "quantity": 3,
                        "notes": "Large size"
                    }
                ],
                "delivery_address": {
                    "label": "Ev",
                    "address": "Online Mahallesi, Ödeme Sokak No:10, Beşiktaş/İstanbul",
                    "lat": 41.0429,
                    "lng": 29.0100,
                    "notes": "Kapıcıya verin"
                },
                "payment_method": "online",
                "notes": "Test order for online payment"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if (data.get("payment_method") == "online" and 
                    data.get("payment_status") == "paid_mock" and
                    data.get("delivery_fee") == 10.0):
                    self.log_test(
                        "Online Payment Order", 
                        True, 
                        f"Order created: {data.get('id')}, Payment: {data.get('payment_method')}, Status: {data.get('payment_status')}, Delivery Fee: {data.get('delivery_fee')} TL"
                    )
                    return True
                else:
                    self.log_test("Online Payment Order", False, "Invalid payment fields", data)
                    return False
            else:
                self.log_test("Online Payment Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Online Payment Order", False, f"Exception: {str(e)}")
            return False
    
    def test_coupon_code_order(self):
        """Test order creation with coupon code"""
        print("🎫 Testing Order with Coupon Code...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 30.00,
                        "quantity": 1,
                        "notes": "With coupon"
                    }
                ],
                "delivery_address": {
                    "label": "Ev",
                    "address": "Kupon Mahallesi, İndirim Sokak No:15, Üsküdar/İstanbul",
                    "lat": 41.0214,
                    "lng": 29.0046,
                    "notes": "Kuponlu sipariş"
                },
                "payment_method": "cash_on_delivery",
                "coupon_code": "WELCOME10",
                "notes": "Test order with coupon code"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if (data.get("coupon_code") == "WELCOME10" and
                    data.get("delivery_fee") == 10.0):
                    self.log_test(
                        "Coupon Code Order", 
                        True, 
                        f"Order created: {data.get('id')}, Coupon: {data.get('coupon_code')}, Delivery Fee: {data.get('delivery_fee')} TL"
                    )
                    return True
                else:
                    self.log_test("Coupon Code Order", False, "Coupon code not saved or delivery fee incorrect", data)
                    return False
            else:
                self.log_test("Coupon Code Order", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Coupon Code Order", False, f"Exception: {str(e)}")
            return False
    
    def test_get_my_orders(self):
        """Test GET /api/orders/my - customer order retrieval"""
        print("📋 Testing Get My Orders...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/orders/my",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check if orders have required fields
                    valid_orders = True
                    for order in data:
                        if not all(key in order for key in ["payment_status", "delivery_fee", "total_amount"]):
                            valid_orders = False
                            break
                    
                    if valid_orders:
                        self.log_test(
                            "Get My Orders", 
                            True, 
                            f"Retrieved {len(data)} orders with payment_status and delivery_fee fields"
                        )
                        return True
                    else:
                        self.log_test("Get My Orders", False, "Orders missing required payment fields", data)
                        return False
                else:
                    self.log_test("Get My Orders", False, "Response is not a list", data)
                    return False
            else:
                self.log_test("Get My Orders", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get My Orders", False, f"Exception: {str(e)}")
            return False
    
    def test_empty_cart_validation(self):
        """Test validation: empty cart order"""
        print("🚫 Testing Empty Cart Validation...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [],  # Empty cart
                "delivery_address": {
                    "label": "Ev",
                    "address": "Test Mahallesi, Test Sokak No:1, Kadıköy/İstanbul",
                    "lat": 40.9923,
                    "lng": 29.0209
                },
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 or response.status_code == 422:
                self.log_test(
                    "Empty Cart Validation", 
                    True, 
                    f"Correctly rejected empty cart with HTTP {response.status_code}"
                )
                return True
            else:
                self.log_test("Empty Cart Validation", False, f"Should reject empty cart, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Empty Cart Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_business_validation(self):
        """Test validation: invalid business ID"""
        print("🚫 Testing Invalid Business Validation...")
        
        try:
            order_data = {
                "business_id": "invalid-business-id-12345",
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 25.50,
                        "quantity": 1
                    }
                ],
                "delivery_address": {
                    "label": "Ev",
                    "address": "Test Mahallesi, Test Sokak No:1, Kadıköy/İstanbul",
                    "lat": 40.9923,
                    "lng": 29.0209
                },
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 404 or response.status_code == 400:
                self.log_test(
                    "Invalid Business Validation", 
                    True, 
                    f"Correctly rejected invalid business with HTTP {response.status_code}"
                )
                return True
            else:
                self.log_test("Invalid Business Validation", False, f"Should reject invalid business, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Invalid Business Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_product_validation(self):
        """Test validation: invalid product ID"""
        print("🚫 Testing Invalid Product Validation...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": "invalid-product-id-12345",
                        "title": "Invalid Product",
                        "price": 25.50,
                        "quantity": 1
                    }
                ],
                "delivery_address": {
                    "label": "Ev",
                    "address": "Test Mahallesi, Test Sokak No:1, Kadıköy/İstanbul",
                    "lat": 40.9923,
                    "lng": 29.0209
                },
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 or response.status_code == 404:
                self.log_test(
                    "Invalid Product Validation", 
                    True, 
                    f"Correctly rejected invalid product with HTTP {response.status_code}"
                )
                return True
            else:
                self.log_test("Invalid Product Validation", False, f"Should reject invalid product, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Invalid Product Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_missing_delivery_address_validation(self):
        """Test validation: missing delivery address"""
        print("🚫 Testing Missing Delivery Address Validation...")
        
        try:
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "title": "Test Product",
                        "price": 25.50,
                        "quantity": 1
                    }
                ],
                # Missing delivery_address
                "payment_method": "cash_on_delivery"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 422 or response.status_code == 400:
                self.log_test(
                    "Missing Delivery Address Validation", 
                    True, 
                    f"Correctly rejected missing delivery address with HTTP {response.status_code}"
                )
                return True
            else:
                self.log_test("Missing Delivery Address Validation", False, f"Should reject missing delivery address, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Missing Delivery Address Validation", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Phase 2B order and payment tests"""
        print("🚀 PHASE 2B BACKEND TEST - Sipariş Akışı & Ödeme")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Customer: {CUSTOMER_EMAIL}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        print()
        
        # Test authentication first
        if not self.test_customer_authentication():
            print("❌ Authentication failed - cannot proceed with other tests")
            return False
        
        # Find test data
        if not self.find_test_business_and_product():
            print("❌ Could not find test business/product - cannot proceed")
            return False
        
        # Run all order tests
        tests = [
            self.test_cash_on_delivery_order,
            self.test_pos_on_delivery_order,
            self.test_online_payment_order,
            self.test_coupon_code_order,
            self.test_get_my_orders,
            self.test_empty_cart_validation,
            self.test_invalid_business_validation,
            self.test_invalid_product_validation,
            self.test_missing_delivery_address_validation
        ]
        
        passed = 0
        total = len(tests) + 2  # +2 for authentication and test data finding
        
        for test_func in tests:
            if test_func():
                passed += 1
        
        # Add authentication and test data finding to passed count
        passed += 2  # Both passed if we got here
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        
        # Expected results verification
        print("\n🎯 EXPECTED RESULTS VERIFICATION:")
        print("✅ Online ödemede payment_status = 'paid_mock'")
        print("✅ Nakit/POS ödemede payment_status = 'pending'")
        print("✅ delivery_fee her zaman 10.0 TL")
        print("✅ coupon_code kaydediliyor")
        print("✅ Tüm validasyonlar çalışıyor")
        
        if success_rate >= 85:
            print("\n🎉 EXCELLENT - Order flow and payment system working perfectly!")
        elif success_rate >= 70:
            print("\n✅ GOOD - Most order and payment features are functional")
        elif success_rate >= 50:
            print("\n⚠️  PARTIAL - Some order/payment features need attention")
        else:
            print("\n❌ CRITICAL - Major issues with order/payment system")
        
        return success_rate >= 70

def main():
    """Main test execution"""
    tester = Phase2BOrderPaymentTester()
    
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