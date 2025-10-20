#!/usr/bin/env python3
"""
E2E Sipariş Akışı - Courier Authentication Fix Test
Focus: Resolve courier login bcrypt hash issue preventing E2E flow completion

Based on review request:
- Business login ✅ (testfix@example.com)
- Customer login ✅ (testcustomer@example.com)  
- Order creation and business confirmation ✅
- Courier login ❌ (bcrypt hash sorunu)
- Need to test courier available orders API

Test Coverage:
1. Courier Authentication Issue Diagnosis
2. Test User Password Hash Verification
3. Courier Available Orders API Test
4. Complete E2E Flow Test
"""

import requests
import json
import time
import bcrypt
from datetime import datetime, timezone

# Configuration from frontend/.env
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"

# Test credentials from review request (corrected business email)
TEST_CREDENTIALS = {
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class CourierAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.tokens = {}
        
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

    def test_authentication(self, user_type, credentials):
        """Test user authentication"""
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
                
                self.log_test(
                    f"{user_type.title()} Authentication",
                    True,
                    f"Login successful - Token: {token[:20]}...({len(token)} chars), Role: {user_data.get('role')}, ID: {user_data.get('id')}"
                )
                return True, token, user_data
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    f"{user_type.title()} Authentication",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, None, None
                
        except Exception as e:
            self.log_test(
                f"{user_type.title()} Authentication",
                False,
                error=str(e)
            )
            return False, None, None

    def test_courier_available_orders(self):
        """Test courier available orders API"""
        if "courier" not in self.tokens:
            self.log_test(
                "Courier Available Orders",
                False,
                error="No courier token available"
            )
            return False
            
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
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Courier Available Orders",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Courier Available Orders",
                False,
                error=str(e)
            )
            return False

    def test_order_creation_flow(self):
        """Test order creation and business confirmation flow"""
        if "customer" not in self.tokens or "business" not in self.tokens:
            self.log_test(
                "Order Creation Flow",
                False,
                error="Missing customer or business tokens"
            )
            return False, None
            
        try:
            # Create order as customer
            customer_headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            
            order_data = {
                "delivery_address": "Test Address, Kadıköy, İstanbul",
                "delivery_lat": 40.9833,
                "delivery_lng": 29.0167,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Pizza",
                        "product_price": 45.0,
                        "quantity": 1,
                        "subtotal": 45.0
                    }
                ],
                "total_amount": 45.0,
                "notes": "Test order for E2E flow"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=customer_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                order = response.json()
                order_id = order.get("id")
                
                self.log_test(
                    "Order Creation",
                    True,
                    f"Order created successfully - ID: {order_id}"
                )
                
                # Test business order confirmation
                business_headers = {"Authorization": f"Bearer {self.tokens['business']}"}
                
                # Update order status to confirmed
                status_response = self.session.patch(
                    f"{BACKEND_URL}/business/orders/{order_id}/status",
                    json={"status": "confirmed"},
                    headers=business_headers,
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    self.log_test(
                        "Business Order Confirmation",
                        True,
                        f"Order {order_id} confirmed by business"
                    )
                    return True, order_id
                else:
                    error_detail = status_response.json().get("detail", "Unknown error") if status_response.content else f"HTTP {status_response.status_code}"
                    self.log_test(
                        "Business Order Confirmation",
                        False,
                        f"Status: {status_response.status_code}",
                        error_detail
                    )
                    return False, order_id
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"HTTP {response.status_code}"
                self.log_test(
                    "Order Creation",
                    False,
                    f"Status: {response.status_code}",
                    error_detail
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Order Creation Flow",
                False,
                error=str(e)
            )
            return False, None

    def diagnose_courier_auth_issue(self):
        """Diagnose courier authentication bcrypt hash issue"""
        print("🔍 DIAGNOSING COURIER AUTHENTICATION ISSUE...")
        print("=" * 60)
        
        # Test if courier user exists in test users
        test_password = "test123"
        
        # Check what the server expects vs what we're sending
        print(f"Testing courier login with:")
        print(f"  Email: {TEST_CREDENTIALS['courier']['email']}")
        print(f"  Password: {TEST_CREDENTIALS['courier']['password']}")
        print()
        
        # Try authentication
        success, token, user_data = self.test_authentication("courier", TEST_CREDENTIALS["courier"])
        
        if not success:
            print("🔧 ATTEMPTING BCRYPT HASH DIAGNOSIS...")
            
            # Generate bcrypt hash for test password
            test_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            print(f"Generated bcrypt hash for '{test_password}': {test_hash}")
            
            # Test if the issue is with hash verification
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), test_hash.encode('utf-8'))
            print(f"Bcrypt verification test: {is_valid}")
            
            if is_valid:
                print("✅ Bcrypt hashing/verification working correctly")
                print("❌ Issue likely in server-side test user configuration")
            else:
                print("❌ Bcrypt hashing/verification issue detected")
        
        return success

    def run_comprehensive_test(self):
        """Run comprehensive E2E flow test"""
        print("🚀 STARTING E2E SİPARİŞ AKIŞI - COURIER AUTH FIX TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        # Test all authentications
        print("📋 PHASE 1: AUTHENTICATION TESTING")
        print("-" * 40)
        
        business_success, _, _ = self.test_authentication("business", TEST_CREDENTIALS["business"])
        customer_success, _, _ = self.test_authentication("customer", TEST_CREDENTIALS["customer"])
        
        # Focus on courier authentication issue
        print("🎯 COURIER AUTHENTICATION DIAGNOSIS:")
        courier_success = self.diagnose_courier_auth_issue()
        
        # Test order flow if business and customer auth work
        if business_success and customer_success:
            print("📋 PHASE 2: ORDER CREATION & BUSINESS CONFIRMATION")
            print("-" * 40)
            order_success, order_id = self.test_order_creation_flow()
        else:
            print("⚠️  Skipping order flow - authentication issues")
            order_success = False
            order_id = None
        
        # Test courier available orders if courier auth works
        if courier_success:
            print("📋 PHASE 3: COURIER AVAILABLE ORDERS")
            print("-" * 40)
            courier_orders_success = self.test_courier_available_orders()
        else:
            print("⚠️  Skipping courier orders - authentication failed")
            courier_orders_success = False
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
            if result["error"]:
                print(f"   ERROR: {result['error']}")
        
        print()
        print("🎯 COURIER AUTHENTICATION ISSUE ANALYSIS:")
        if courier_success:
            print("✅ Courier authentication working - E2E flow can proceed")
        else:
            print("❌ Courier authentication failing - blocking E2E flow")
            print("🔧 RECOMMENDED FIXES:")
            print("   1. Check test user password hash in server.py")
            print("   2. Verify bcrypt.checkpw() implementation")
            print("   3. Ensure test courier user exists with correct credentials")
            print("   4. Check if courier role is properly set")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = CourierAuthTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 E2E COURIER AUTH TEST COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️  E2E COURIER AUTH TEST COMPLETED WITH ISSUES")
    
    exit(0 if success else 1)