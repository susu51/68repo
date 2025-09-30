#!/usr/bin/env python3
"""
Authentication Verification Test - Critical JWT Authentication Fixes
Tests the specific authentication issues mentioned in the review request:
- Business JWT authentication for protected endpoints
- Courier JWT authentication for protected endpoints  
- Admin authentication with password 6851
- Customer authentication verification
"""

import requests
import sys
import json
from datetime import datetime
import time

class AuthVerificationTester:
    def __init__(self, base_url="https://foodlogistic.preview.emergentagent.com"):
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

    def test_business_endpoints(self):
        """Test Priority 1 - Business JWT Authentication Fix"""
        print("🏢 TESTING BUSINESS ENDPOINTS")
        print("=" * 50)
        
        if "business" not in self.tokens:
            self.log_test("Business Endpoints", False, "No business token available")
            return
        
        token = self.tokens["business"]
        
        # Test GET /api/business/stats
        response = self.make_request("GET", "/business/stats", token=token)
        if response and response.status_code == 200:
            data = response.json()
            if "today" in data and "orders" in data["today"]:
                self.log_test("GET /api/business/stats", True, 
                            f"Retrieved analytics data: {data['today']['orders']} orders today")
            else:
                self.log_test("GET /api/business/stats", False, 
                            "Invalid response structure", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("GET /api/business/stats", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")
        
        # Test PUT /api/business/status
        status_data = {"isOpen": True}
        response = self.make_request("PUT", "/business/status", status_data, token=token)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("PUT /api/business/status", True, 
                            f"Status updated successfully: {data.get('message', '')}")
            else:
                self.log_test("PUT /api/business/status", False, 
                            "Success flag not set", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("PUT /api/business/status", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")
        
        # Test GET /api/business/orders/incoming
        response = self.make_request("GET", "/business/orders/incoming", token=token)
        if response and response.status_code == 200:
            data = response.json()
            if "orders" in data:
                orders_count = len(data["orders"])
                self.log_test("GET /api/business/orders/incoming", True, 
                            f"Retrieved {orders_count} incoming orders")
            else:
                self.log_test("GET /api/business/orders/incoming", False, 
                            "Invalid response structure", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("GET /api/business/orders/incoming", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")

    def test_courier_endpoints(self):
        """Test Priority 2 - Courier Authentication"""
        print("🚴 TESTING COURIER ENDPOINTS")
        print("=" * 50)
        
        if "courier" not in self.tokens:
            self.log_test("Courier Endpoints", False, "No courier token available")
            return
        
        token = self.tokens["courier"]
        
        # Test GET /api/courier/earnings
        response = self.make_request("GET", "/courier/earnings", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/earnings", True, 
                            f"Retrieved earnings data successfully")
            elif response.status_code == 403:
                # Check if it's a KYC message
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("GET /api/courier/earnings", True, 
                                f"Appropriate KYC message returned: {error_msg}")
                else:
                    self.log_test("GET /api/courier/earnings", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/courier/earnings", False, 
                            f"Failed with status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/courier/earnings", False, "No response received")
        
        # Test GET /api/courier/stats
        response = self.make_request("GET", "/courier/stats", token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/stats", True, 
                            f"Retrieved stats data successfully")
            elif response.status_code == 403:
                # Check if it's a KYC message
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("GET /api/courier/stats", True, 
                                f"Appropriate KYC message returned: {error_msg}")
                else:
                    self.log_test("GET /api/courier/stats", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("GET /api/courier/stats", False, 
                            f"Failed with status {response.status_code}: {error_msg}")
        else:
            self.log_test("GET /api/courier/stats", False, "No response received")
        
        # Test PUT /api/courier/status
        status_data = {"isOnline": True}
        response = self.make_request("PUT", "/courier/status", status_data, token=token)
        if response:
            if response.status_code == 200:
                data = response.json()
                self.log_test("PUT /api/courier/status", True, 
                            f"Status updated successfully")
            elif response.status_code == 403:
                # Check if it's a KYC message
                error_msg = response.json().get("detail", "")
                if "KYC" in error_msg or "approval" in error_msg.lower():
                    self.log_test("PUT /api/courier/status", True, 
                                f"Appropriate KYC message returned: {error_msg}")
                else:
                    self.log_test("PUT /api/courier/status", False, 
                                f"Unexpected 403 error: {error_msg}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                self.log_test("PUT /api/courier/status", False, 
                            f"Failed with status {response.status_code}: {error_msg}")
        else:
            self.log_test("PUT /api/courier/status", False, "No response received")

    def test_admin_endpoints(self):
        """Test Priority 3 - Admin Authentication"""
        print("👑 TESTING ADMIN ENDPOINTS")
        print("=" * 50)
        
        if "admin" not in self.tokens:
            self.log_test("Admin Endpoints", False, "No admin token available")
            return
        
        token = self.tokens["admin"]
        
        # Test GET /api/admin/users
        response = self.make_request("GET", "/admin/users", token=token)
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                users_count = len(data)
                self.log_test("GET /api/admin/users", True, 
                            f"Retrieved {users_count} users successfully")
            else:
                self.log_test("GET /api/admin/users", False, 
                            "Invalid response structure - expected list", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("GET /api/admin/users", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")
        
        # Test GET /api/admin/couriers/kyc
        response = self.make_request("GET", "/admin/couriers/kyc", token=token)
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                couriers_count = len(data)
                self.log_test("GET /api/admin/couriers/kyc", True, 
                            f"Retrieved {couriers_count} couriers for KYC review")
            else:
                self.log_test("GET /api/admin/couriers/kyc", False, 
                            "Invalid response structure - expected list", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("GET /api/admin/couriers/kyc", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")

    def test_customer_endpoints(self):
        """Test Priority 3 - Customer Authentication"""
        print("👤 TESTING CUSTOMER ENDPOINTS")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_test("Customer Endpoints", False, "No customer token available")
            return
        
        token = self.tokens["customer"]
        
        # Test GET /api/businesses (public endpoint that should work with customer auth)
        response = self.make_request("GET", "/businesses", token=token)
        if response and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                businesses_count = len(data)
                self.log_test("GET /api/businesses (Customer)", True, 
                            f"Retrieved {businesses_count} businesses successfully")
            else:
                self.log_test("GET /api/businesses (Customer)", False, 
                            "Invalid response structure - expected list", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("GET /api/businesses (Customer)", False, 
                        f"Failed with status {response.status_code if response else 'None'}: {error_msg}")

    def test_token_validation(self):
        """Test that tokens are properly validated and not just ignored"""
        print("🔐 TESTING TOKEN VALIDATION")
        print("=" * 50)
        
        # Test with invalid token
        invalid_token = "invalid.jwt.token"
        response = self.make_request("GET", "/business/stats", token=invalid_token)
        
        if response and response.status_code == 401:
            error_msg = response.json().get("detail", "")
            if "credentials" in error_msg.lower() or "token" in error_msg.lower():
                self.log_test("Invalid Token Rejection", True, 
                            f"Invalid token properly rejected: {error_msg}")
            else:
                self.log_test("Invalid Token Rejection", False, 
                            f"Unexpected error message: {error_msg}")
        else:
            self.log_test("Invalid Token Rejection", False, 
                        f"Expected 401, got {response.status_code if response else 'None'}")
        
        # Test without token
        response = self.make_request("GET", "/business/stats")
        
        if response and response.status_code in [401, 403]:
            self.log_test("No Token Rejection", True, 
                        f"Request without token properly rejected (status: {response.status_code})")
        else:
            self.log_test("No Token Rejection", False, 
                        f"Expected 401/403, got {response.status_code if response else 'None'}")

    def run_all_tests(self):
        """Run all authentication verification tests"""
        print("🚀 STARTING AUTHENTICATION VERIFICATION TESTS")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test logins for all user types
        print("🔑 TESTING USER LOGINS")
        print("=" * 50)
        
        for user_type in ["business", "courier", "admin", "customer"]:
            self.test_login(user_type)
        
        print()
        
        # Test specific endpoints
        self.test_business_endpoints()
        print()
        
        self.test_courier_endpoints()
        print()
        
        self.test_admin_endpoints()
        print()
        
        self.test_customer_endpoints()
        print()
        
        self.test_token_validation()
        print()
        
        # Print summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
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
        
        print("\n🎯 AUTHENTICATION VERIFICATION COMPLETE")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AuthVerificationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)