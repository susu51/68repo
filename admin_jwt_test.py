#!/usr/bin/env python3
"""
Admin JWT Token Validation Test Suite
Tests the FIXED admin JWT token validation system focusing on:
1. Admin Token Access with new login integration (admin@kuryecini.com)
2. Admin Login Integration (any email + password "6851")
3. Legacy Admin Token Compatibility (admin@delivertr.com)
4. Admin Endpoint Access with valid tokens
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class AdminJWTTester:
    def __init__(self, base_url="https://meal-dash-163.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Store tokens for testing
        self.new_admin_token = None
        self.legacy_admin_token = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {'Content-Type': 'application/json'}
        
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if token:
            print(f"   Token: {token[:20]}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    response_text = response.text
                    print(f"   Response: {response_text}")
                    self.log_test(name, True)
                    return True, response_text
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_admin_login_new_integration(self):
        """Test admin login via new integration (any email + password '6851')"""
        print("\n🔐 TESTING NEW ADMIN LOGIN INTEGRATION")
        
        test_cases = [
            {
                "name": "Admin Login - Any Email + Password 6851",
                "email": "any@email.com",
                "password": "6851"
            },
            {
                "name": "Admin Login - Test Email + Password 6851", 
                "email": "test@admin.com",
                "password": "6851"
            },
            {
                "name": "Admin Login - Admin Email + Password 6851",
                "email": "admin@kuryecini.com", 
                "password": "6851"
            }
        ]
        
        all_success = True
        
        for test_case in test_cases:
            login_data = {
                "email": test_case["email"],
                "password": test_case["password"]
            }
            
            success, response = self.run_test(
                test_case["name"],
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success:
                # Verify admin user data structure
                if self.verify_admin_user_data(response):
                    # Store admin token for later tests
                    if response.get('access_token'):
                        self.new_admin_token = response['access_token']
                        print(f"   ✅ New admin token stored: {self.new_admin_token[:20]}...")
                else:
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_legacy_admin_login(self):
        """Test legacy admin login endpoint still works"""
        print("\n🔐 TESTING LEGACY ADMIN LOGIN")
        
        success, response = self.run_test(
            "Legacy Admin Login - Password 6851",
            "POST",
            "auth/admin",
            200,
            data={"password": "6851"}
        )
        
        if success:
            # Verify admin user data structure
            if self.verify_admin_user_data(response):
                # Store legacy admin token for comparison
                if response.get('access_token'):
                    self.legacy_admin_token = response['access_token']
                    print(f"   ✅ Legacy admin token stored: {self.legacy_admin_token[:20]}...")
                    return True
            return False
        
        return success

    def verify_admin_user_data(self, response):
        """Verify admin login returns proper user_data structure"""
        if not response:
            print(f"   ❌ No response data")
            return False
        
        # Check response structure
        required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
        for field in required_fields:
            if field not in response:
                print(f"   ❌ Missing field in response: {field}")
                return False
        
        # Check token type
        if response.get('token_type') != 'bearer':
            print(f"   ❌ Wrong token_type: {response.get('token_type')}, expected 'bearer'")
            return False
        
        # Check user type
        if response.get('user_type') != 'admin':
            print(f"   ❌ Wrong user_type: {response.get('user_type')}, expected 'admin'")
            return False
        
        # Check user_data structure
        user_data = response.get('user_data', {})
        
        # Check role
        if user_data.get('role') != 'admin':
            print(f"   ❌ Wrong role in user_data: {user_data.get('role')}, expected 'admin'")
            return False
        
        # Check email (should be admin@kuryecini.com for new integration or admin@delivertr.com for legacy)
        email = user_data.get('email')
        if email not in ['admin@kuryecini.com', 'admin@delivertr.com']:
            print(f"   ❌ Wrong email in user_data: {email}, expected admin@kuryecini.com or admin@delivertr.com")
            return False
        
        # Check other admin fields
        expected_admin_fields = {
            'id': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_active': True
        }
        
        for field, expected_value in expected_admin_fields.items():
            actual_value = user_data.get(field)
            if actual_value != expected_value:
                print(f"   ❌ Wrong {field} in user_data: {actual_value}, expected {expected_value}")
                return False
        
        # Check created_at exists
        if 'created_at' not in user_data:
            print(f"   ❌ Missing created_at in user_data")
            return False
        
        print(f"   ✅ Admin user data structure correct:")
        print(f"       - Role: {user_data.get('role')}")
        print(f"       - Email: {user_data.get('email')}")
        print(f"       - ID: {user_data.get('id')}")
        print(f"       - Name: {user_data.get('first_name')} {user_data.get('last_name')}")
        print(f"       - Active: {user_data.get('is_active')}")
        
        return True

    def test_admin_endpoint_access_new_token(self):
        """Test admin endpoints with new integration token"""
        print("\n🔑 TESTING ADMIN ENDPOINT ACCESS WITH NEW TOKEN")
        
        if not self.new_admin_token:
            print("   ❌ No new admin token available")
            return False
        
        admin_endpoints = [
            {
                "name": "GET /api/admin/users",
                "method": "GET",
                "endpoint": "admin/users",
                "expected_status": 200
            },
            {
                "name": "GET /api/admin/couriers/kyc",
                "method": "GET", 
                "endpoint": "admin/couriers/kyc",
                "expected_status": 200
            },
            {
                "name": "GET /api/admin/orders",
                "method": "GET",
                "endpoint": "admin/orders", 
                "expected_status": 200
            }
        ]
        
        all_success = True
        
        for endpoint_test in admin_endpoints:
            success, response = self.run_test(
                f"New Token - {endpoint_test['name']}",
                endpoint_test["method"],
                endpoint_test["endpoint"],
                endpoint_test["expected_status"],
                token=self.new_admin_token
            )
            
            if success:
                print(f"   ✅ {endpoint_test['name']} accessible with new admin token")
            else:
                print(f"   ❌ {endpoint_test['name']} NOT accessible with new admin token")
                all_success = False
        
        return all_success

    def test_admin_endpoint_access_legacy_token(self):
        """Test admin endpoints with legacy token"""
        print("\n🔑 TESTING ADMIN ENDPOINT ACCESS WITH LEGACY TOKEN")
        
        if not self.legacy_admin_token:
            print("   ❌ No legacy admin token available")
            return False
        
        admin_endpoints = [
            {
                "name": "GET /api/admin/users",
                "method": "GET",
                "endpoint": "admin/users",
                "expected_status": 200
            },
            {
                "name": "GET /api/admin/couriers/kyc",
                "method": "GET", 
                "endpoint": "admin/couriers/kyc",
                "expected_status": 200
            },
            {
                "name": "GET /api/admin/orders",
                "method": "GET",
                "endpoint": "admin/orders", 
                "expected_status": 200
            }
        ]
        
        all_success = True
        
        for endpoint_test in admin_endpoints:
            success, response = self.run_test(
                f"Legacy Token - {endpoint_test['name']}",
                endpoint_test["method"],
                endpoint_test["endpoint"],
                endpoint_test["expected_status"],
                token=self.legacy_admin_token
            )
            
            if success:
                print(f"   ✅ {endpoint_test['name']} accessible with legacy admin token")
            else:
                print(f"   ❌ {endpoint_test['name']} NOT accessible with legacy admin token")
                all_success = False
        
        return all_success

    def test_complete_admin_flow(self):
        """Test complete admin flow: login → get token → access endpoints"""
        print("\n🔄 TESTING COMPLETE ADMIN FLOW")
        
        # Step 1: Login with any email + password "6851"
        login_data = {
            "email": "flowtest@admin.com",
            "password": "6851"
        }
        
        login_success, login_response = self.run_test(
            "Complete Flow - Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if not login_success:
            print("   ❌ Admin login failed - cannot continue flow test")
            return False
        
        # Step 2: Extract token
        access_token = login_response.get('access_token')
        if not access_token:
            print("   ❌ No access token in login response")
            return False
        
        print(f"   ✅ Admin token obtained: {access_token[:20]}...")
        
        # Step 3: Test accessing admin endpoints
        admin_endpoints = [
            "admin/users",
            "admin/couriers/kyc", 
            "admin/orders"
        ]
        
        all_endpoints_success = True
        
        for endpoint in admin_endpoints:
            success, response = self.run_test(
                f"Complete Flow - Access {endpoint}",
                "GET",
                endpoint,
                200,
                token=access_token
            )
            
            if success:
                print(f"   ✅ Successfully accessed {endpoint}")
            else:
                print(f"   ❌ Failed to access {endpoint}")
                all_endpoints_success = False
        
        if all_endpoints_success:
            print("   ✅ Complete admin flow successful - JWT token validation FIXED")
            return True
        else:
            print("   ❌ Complete admin flow failed - JWT token validation still has issues")
            return False

    def test_invalid_password_scenarios(self):
        """Test that wrong passwords return 401 unauthorized"""
        print("\n🚫 TESTING INVALID PASSWORD SCENARIOS")
        
        test_cases = [
            {
                "name": "Invalid Password - Wrong Password",
                "email": "any@email.com",
                "password": "wrongpass",
                "expected_status": 401
            },
            {
                "name": "Invalid Password - Empty Password",
                "email": "test@example.com", 
                "password": "",
                "expected_status": 401
            },
            {
                "name": "Invalid Password - Almost Correct",
                "email": "admin@test.com",
                "password": "6850",  # Close but wrong
                "expected_status": 401
            },
            {
                "name": "Invalid Password - Case Sensitive",
                "email": "admin@test.com",
                "password": "6851 ",  # Extra space
                "expected_status": 401
            }
        ]
        
        all_success = True
        
        for test_case in test_cases:
            login_data = {
                "email": test_case["email"],
                "password": test_case["password"]
            }
            
            success, response = self.run_test(
                test_case["name"],
                "POST",
                "auth/login",
                test_case["expected_status"],
                data=login_data
            )
            
            if success:
                print(f"   ✅ Invalid password correctly rejected")
            else:
                all_success = False
        
        return all_success

    def test_normal_user_login_still_works(self):
        """Test that normal user login still works correctly"""
        print("\n👤 TESTING NORMAL USER LOGIN COMPATIBILITY")
        
        # First register a test customer
        customer_data = {
            "email": "normaluser@test.com",
            "password": "test123",
            "first_name": "Normal",
            "last_name": "User",
            "city": "İstanbul"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Normal User",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        if not reg_success:
            print("   ❌ Failed to register normal user")
            return False
        
        # Test normal user login
        login_data = {
            "email": "normaluser@test.com",
            "password": "test123"
        }
        
        success, response = self.run_test(
            "Normal User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            # Verify it's NOT admin user
            user_data = response.get('user_data', {})
            if user_data.get('role') == 'admin':
                print("   ❌ Normal user login returned admin role")
                return False
            
            if user_data.get('role') != 'customer':
                print(f"   ❌ Expected customer role, got {user_data.get('role')}")
                return False
            
            print(f"   ✅ Normal user login successful with role: {user_data.get('role')}")
            print(f"   ✅ User email: {user_data.get('email')}")
            
            # Test that normal user cannot access admin endpoints
            normal_token = response.get('access_token')
            if normal_token:
                admin_access_success, admin_response = self.run_test(
                    "Normal User - Admin Access (Should Fail)",
                    "GET",
                    "admin/users",
                    403,  # Should be forbidden
                    token=normal_token
                )
                
                if admin_access_success:
                    print("   ✅ Normal user correctly denied admin access")
                    return True
                else:
                    print("   ❌ Normal user was able to access admin endpoints")
                    return False
        
        return success

    def run_all_tests(self):
        """Run all admin JWT token validation tests"""
        print("🚀 STARTING ADMIN JWT TOKEN VALIDATION TESTS")
        print("=" * 60)
        
        test_methods = [
            self.test_admin_login_new_integration,
            self.test_legacy_admin_login,
            self.test_admin_endpoint_access_new_token,
            self.test_admin_endpoint_access_legacy_token,
            self.test_complete_admin_flow,
            self.test_invalid_password_scenarios,
            self.test_normal_user_login_still_works
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 ADMIN JWT TOKEN VALIDATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED - ADMIN JWT TOKEN VALIDATION SYSTEM IS WORKING!")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED - ADMIN JWT TOKEN VALIDATION NEEDS ATTENTION")
            
            # Print failed tests
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['details']}")
            
            return False

if __name__ == "__main__":
    tester = AdminJWTTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)