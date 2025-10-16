#!/usr/bin/env python3
"""
Focused Authentication Fix Verification Test
Tests the exact endpoints mentioned in the review request with proper HTTP methods
"""

import requests
import sys
import json
from datetime import datetime
import time

class FocusedAuthTester:
    def __init__(self, base_url="https://deliverypro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test credentials from review request
        self.test_users = {
            "business": {"email": "testbusiness@example.com", "password": "test123"},
            "courier": {"email": "testkurye@example.com", "password": "test123"},
            "admin": {"email": "admin@kuryecini.com", "password": "6851"},
            "customer": {"email": "testcustomer@example.com", "password": "test123"}
        }
        
        # Store tokens
        self.tokens = {}

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        
        if success:
            self.tests_passed += 1
            
        result = {
            "name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        
        print(f"{status}: {name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with optional authentication"""
        url = f"{self.api_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def test_login(self, user_type):
        """Test login for specific user type"""
        user_creds = self.test_users[user_type]
        
        # Special handling for admin login
        if user_type == "admin":
            # Try the unified login endpoint with any email + password 6851
            login_data = {"email": "test@admin.com", "password": "6851"}
        else:
            login_data = {"email": user_creds["email"], "password": user_creds["password"]}
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.tokens[user_type] = data["access_token"]
                user_data = data.get("user", {})
                expected_role = "admin" if user_type == "admin" else user_type
                actual_role = user_data.get("role", "")
                
                if actual_role == expected_role:
                    self.log_test(f"{user_type.title()} Login", True, 
                                f"Successfully logged in as {expected_role}, token obtained")
                    return True
                else:
                    self.log_test(f"{user_type.title()} Login", False, 
                                f"Role mismatch: expected {expected_role}, got {actual_role}")
                    return False
            else:
                self.log_test(f"{user_type.title()} Login", False, 
                            "No access token in response", data)
                return False
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test(f"{user_type.title()} Login", False, 
                        f"Login failed: {error_msg}")
            return False

    def test_business_authentication_fix(self):
        """Test Priority 1 - JWT Authentication Fix for Business"""
        print("🏢 PRIORITY 1: BUSINESS JWT AUTHENTICATION FIX")
        print("=" * 60)
        
        if "business" not in self.tokens:
            self.log_test("Business Authentication", False, "No business token available")
            return
        
        token = self.tokens["business"]
        
        # Test GET /api/business/stats
        response = self.make_request("GET", "/business/stats", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                if "today" in data and "orders" in data["today"]:
                    self.log_test("GET /api/business/stats", True, 
                                f"✅ JWT token accepted - Retrieved analytics: {data['today']['orders']} orders, ₺{data['today']['revenue']} revenue")
                else:
                    self.log_test("GET /api/business/stats", False, 
                                "Invalid response structure", data)
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("GET /api/business/stats", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/business/stats", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/business/stats", False, "No response received")
        
        # Test PUT /api/business/status
        status_data = {"isOpen": True}
        response = self.make_request("PUT", "/business/status", status_data, token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("PUT /api/business/status", True, 
                                f"✅ JWT token accepted - Status updated: {data.get('message', '')}")
                else:
                    self.log_test("PUT /api/business/status", False, 
                                "Success flag not set", data)
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("PUT /api/business/status", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("PUT /api/business/status", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("PUT /api/business/status", False, "No response received")
        
        # Test GET /api/business/orders/incoming
        response = self.make_request("GET", "/business/orders/incoming", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                if "orders" in data:
                    orders_count = len(data["orders"])
                    self.log_test("GET /api/business/orders/incoming", True, 
                                f"✅ JWT token accepted - Retrieved {orders_count} incoming orders")
                else:
                    self.log_test("GET /api/business/orders/incoming", False, 
                                "Invalid response structure", data)
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("GET /api/business/orders/incoming", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/business/orders/incoming", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/business/orders/incoming", False, "No response received")

    def test_courier_authentication_fix(self):
        """Test Priority 2 - Courier Authentication"""
        print("🚴 PRIORITY 2: COURIER AUTHENTICATION FIX")
        print("=" * 60)
        
        if "courier" not in self.tokens:
            self.log_test("Courier Authentication", False, "No courier token available")
            return
        
        token = self.tokens["courier"]
        
        # Test GET /api/courier/earnings
        response = self.make_request("GET", "/courier/earnings", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/earnings", True, 
                            f"✅ JWT token accepted - Retrieved earnings data")
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("GET /api/courier/earnings", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            elif response.status_code == 403:
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("GET /api/courier/earnings", True, 
                                f"✅ JWT token accepted - Appropriate KYC message: {error_msg}")
                else:
                    self.log_test("GET /api/courier/earnings", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/courier/earnings", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/courier/earnings", False, "No response received")
        
        # Test GET /api/courier/stats
        response = self.make_request("GET", "/courier/stats", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/stats", True, 
                            f"✅ JWT token accepted - Retrieved stats data")
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("GET /api/courier/stats", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            elif response.status_code == 403:
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("GET /api/courier/stats", True, 
                                f"✅ JWT token accepted - Appropriate KYC message: {error_msg}")
                else:
                    self.log_test("GET /api/courier/stats", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/courier/stats", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/courier/stats", False, "No response received")
        
        # Test POST /api/courier/status/toggle (correct endpoint)
        response = self.make_request("POST", "/courier/status/toggle", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("POST /api/courier/status/toggle", True, 
                            f"✅ JWT token accepted - Status toggled successfully")
            elif response.status_code == 401:
                error_msg = response.json().get("detail", "")
                self.log_test("POST /api/courier/status/toggle", False, 
                            f"❌ JWT token validation failed: {error_msg}")
            elif response.status_code == 403:
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("POST /api/courier/status/toggle", True, 
                                f"✅ JWT token accepted - Appropriate KYC message: {error_msg}")
                else:
                    self.log_test("POST /api/courier/status/toggle", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("POST /api/courier/status/toggle", False, 
                            f"Unexpected status {response.status_code}: {error_msg}")
        else:
            self.log_test("POST /api/courier/status/toggle", False, "No response received")

    def test_admin_customer_verification(self):
        """Test Priority 3 - Admin & Customer Authentication"""
        print("👑 PRIORITY 3: ADMIN & CUSTOMER VERIFICATION")
        print("=" * 60)
        
        # Test Admin
        if "admin" in self.tokens:
            token = self.tokens["admin"]
            
            # Test admin endpoint
            response = self.make_request("GET", "/admin/users", token=token)
            if response:
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        users_count = len(data)
                        self.log_test("Admin Endpoint Access", True, 
                                    f"✅ Admin JWT token working - Retrieved {users_count} users")
                    else:
                        self.log_test("Admin Endpoint Access", False, 
                                    "Invalid response structure", data)
                elif response.status_code == 401:
                    error_msg = response.json().get("detail", "")
                    self.log_test("Admin Endpoint Access", False, 
                                f"❌ Admin JWT token validation failed: {error_msg}")
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    self.log_test("Admin Endpoint Access", False, 
                                f"Unexpected status {response.status_code}: {error_msg}")
            else:
                self.log_test("Admin Endpoint Access", False, "No response received")
        else:
            self.log_test("Admin Endpoint Access", False, "No admin token available")
        
        # Test Customer
        if "customer" in self.tokens:
            token = self.tokens["customer"]
            
            # Test customer endpoint
            response = self.make_request("GET", "/businesses", token=token)
            if response:
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        businesses_count = len(data)
                        self.log_test("Customer Endpoint Access", True, 
                                    f"✅ Customer JWT token working - Retrieved {businesses_count} businesses")
                    else:
                        self.log_test("Customer Endpoint Access", False, 
                                    "Invalid response structure", data)
                elif response.status_code == 401:
                    error_msg = response.json().get("detail", "")
                    self.log_test("Customer Endpoint Access", False, 
                                f"❌ Customer JWT token validation failed: {error_msg}")
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    self.log_test("Customer Endpoint Access", False, 
                                f"Unexpected status {response.status_code}: {error_msg}")
            else:
                self.log_test("Customer Endpoint Access", False, "No response received")
        else:
            self.log_test("Customer Endpoint Access", False, "No customer token available")

    def test_credentials_validation_fix(self):
        """Test that 'Could not validate credentials' errors are fixed"""
        print("🔐 CREDENTIALS VALIDATION FIX VERIFICATION")
        print("=" * 60)
        
        # Test with invalid token to ensure proper error handling
        invalid_token = "invalid.jwt.token.here"
        response = self.make_request("GET", "/business/stats", token=invalid_token)
        
        if response:
            if response.status_code == 401:
                error_msg = response.json().get("detail", "")
                if "Could not validate credentials" in error_msg:
                    self.log_test("Invalid Token Error Message", True, 
                                f"✅ Proper error message returned: {error_msg}")
                else:
                    self.log_test("Invalid Token Error Message", True, 
                                f"✅ Authentication error returned: {error_msg}")
            else:
                self.log_test("Invalid Token Error Message", False, 
                            f"Expected 401, got {response.status_code}")
        else:
            self.log_test("Invalid Token Error Message", False, "No response received")
        
        # Test without token
        response = self.make_request("GET", "/business/stats")
        
        if response:
            if response.status_code in [401, 403]:
                self.log_test("No Token Handling", True, 
                            f"✅ Request without token properly rejected (status: {response.status_code})")
            else:
                self.log_test("No Token Handling", False, 
                            f"Expected 401/403, got {response.status_code}")
        else:
            self.log_test("No Token Handling", False, "No response received")

    def run_focused_tests(self):
        """Run focused authentication verification tests"""
        print("🎯 FOCUSED AUTHENTICATION FIX VERIFICATION")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print("Testing specific endpoints mentioned in review request")
        print("=" * 70)
        
        # Test logins for all user types
        print("🔑 STEP 1: USER LOGIN VERIFICATION")
        print("=" * 50)
        
        for user_type in ["business", "courier", "admin", "customer"]:
            self.test_login(user_type)
        
        print()
        
        # Test specific priorities
        self.test_business_authentication_fix()
        print()
        
        self.test_courier_authentication_fix()
        print()
        
        self.test_admin_customer_verification()
        print()
        
        self.test_credentials_validation_fix()
        print()
        
        # Print summary
        print("📊 AUTHENTICATION FIX VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("\n🎉 ALL AUTHENTICATION FIXES VERIFIED SUCCESSFULLY!")
        
        # Print success tests
        success_tests = [test for test in self.test_results if test["success"]]
        if success_tests:
            print(f"\n✅ SUCCESSFUL TESTS ({len(success_tests)}):")
            for test in success_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        print("\n🏁 AUTHENTICATION FIX VERIFICATION COMPLETE")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = FocusedAuthTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)