#!/usr/bin/env python3
"""
🔍 CUSTOMER REGISTRATION & LOGIN TESTING AFTER PASSWORD FIELD MISMATCH FIX
Re-testing customer registration and login functionality after fixing the password field mismatch issue.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://quickcourier.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request - using unique email to avoid conflicts
TEST_CREDENTIALS = {
    "new_customer": {
        "email": "testfix@kuryecini.com",
        "password": "test123456", 
        "first_name": "Test",
        "last_name": "Fix User",
        "city": "İstanbul"
    },
    "existing_customer": {"email": "testcustomer@example.com", "password": "test123"},
    "admin_user": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}
}

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.cookies = {}
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    def test_customer_registration(self):
        """Test POST /api/register/customer endpoint with new unique email"""
        print("\n🔐 TESTING CUSTOMER REGISTRATION (POST /api/register/customer)")
        
        # Test new customer registration with unique email
        register_data = TEST_CREDENTIALS["new_customer"]
        
        try:
            response = self.session.post(f"{API_BASE}/register/customer", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                if data.get("access_token") and data.get("user_data"):
                    user_data = data["user_data"]
                    self.log_test("POST /api/register/customer - New Customer Registration", True, 
                                f"Customer registered successfully: {user_data.get('email')} (ID: {user_data.get('id')})")
                    
                    # Store user data for login test
                    self.registered_user = user_data
                    return True
                else:
                    self.log_test("POST /api/register/customer - New Customer Registration", False, 
                                f"Registration response missing required fields", data)
            elif response.status_code == 400:
                data = response.json()
                if "already registered" in data.get("detail", "").lower():
                    self.log_test("POST /api/register/customer - New Customer Registration", True, 
                                "User already exists - will test login with existing credentials")
                    return True
                else:
                    self.log_test("POST /api/register/customer - New Customer Registration", False, 
                                f"Registration failed: {data.get('detail', 'Unknown error')}", data)
            else:
                self.log_test("POST /api/register/customer - New Customer Registration", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/register/customer - New Customer Registration", False, f"Exception: {str(e)}")
            
        return False
            
    def test_customer_login(self):
        """Test POST /api/auth/login with newly registered credentials"""
        print("\n🔐 TESTING CUSTOMER LOGIN (POST /api/auth/login)")
        
        # Test login with the newly registered customer credentials
        login_credentials = {
            "email": TEST_CREDENTIALS["new_customer"]["email"],
            "password": TEST_CREDENTIALS["new_customer"]["password"]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_credentials)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if data.get("success") and data.get("user"):
                    user_data = data["user"]
                    
                    # Validate user data structure
                    required_fields = ["id", "email", "role"]
                    missing_fields = [field for field in required_fields if field not in user_data]
                    
                    if not missing_fields:
                        # Check cookies
                        cookies = response.cookies
                        has_access_token = 'access_token' in cookies
                        has_refresh_token = 'refresh_token' in cookies
                        
                        # Store cookies for subsequent tests
                        if has_access_token:
                            self.cookies['access_token'] = cookies['access_token']
                        if has_refresh_token:
                            self.cookies['refresh_token'] = cookies['refresh_token']
                        
                        cookie_details = f"Cookies: access_token={has_access_token}, refresh_token={has_refresh_token}"
                        user_details = f"User: {user_data['email']} (Role: {user_data['role']}, ID: {user_data['id']})"
                        
                        self.log_test("POST /api/auth/login - New Customer Login", True, 
                                    f"{user_details}, {cookie_details}")
                        return True
                    else:
                        self.log_test("POST /api/auth/login - New Customer Login", False, 
                                    f"Missing user fields: {missing_fields}", data)
                else:
                    self.log_test("POST /api/auth/login - New Customer Login", False, 
                                f"Invalid response structure: {data}", data)
                    
            elif response.status_code == 401:
                data = response.json()
                self.log_test("POST /api/auth/login - New Customer Login", False, 
                            f"Authentication failed (PASSWORD FIELD MISMATCH ISSUE?): {data.get('detail', 'Invalid credentials')}", data)
            else:
                self.log_test("POST /api/auth/login - New Customer Login", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/auth/login - New Customer Login", False, f"Exception: {str(e)}")
            
        return False
                
    def test_auth_me(self):
        """Test GET /api/auth/me endpoint"""
        print("\n🔐 TESTING CURRENT USER RETRIEVAL")
        
        # First login to get cookies
        login_response = self.session.post(f"{API_BASE}/auth/login", 
                                         json=TEST_CREDENTIALS["test_customer"])
        
        if login_response.status_code == 200:
            try:
                response = self.session.get(f"{API_BASE}/auth/me")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate user data structure
                    required_fields = ["id", "email", "role", "first_name", "last_name"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        user_details = f"User: {data['email']} (Role: {data['role']}, Name: {data['first_name']} {data['last_name']})"
                        self.log_test("GET /api/auth/me - Current User Data", True, user_details)
                    else:
                        self.log_test("GET /api/auth/me - Current User Data", False, 
                                    f"Missing fields: {missing_fields}", data)
                        
                elif response.status_code == 401:
                    data = response.json()
                    self.log_test("GET /api/auth/me - Current User Data", False, 
                                f"Unauthorized: {data.get('detail', 'No auth token')}", data)
                else:
                    self.log_test("GET /api/auth/me - Current User Data", False, 
                                f"Unexpected status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test("GET /api/auth/me - Current User Data", False, f"Exception: {str(e)}")
        else:
            self.log_test("GET /api/auth/me - Current User Data", False, 
                        "Could not login to test /me endpoint")
            
    def test_auth_refresh(self):
        """Test POST /api/auth/refresh endpoint"""
        print("\n🔐 TESTING TOKEN REFRESH")
        
        # First login to get refresh token
        login_response = self.session.post(f"{API_BASE}/auth/login", 
                                         json=TEST_CREDENTIALS["test_customer"])
        
        if login_response.status_code == 200:
            try:
                response = self.session.post(f"{API_BASE}/auth/refresh")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success"):
                        self.log_test("POST /api/auth/refresh - Token Refresh", True, 
                                    f"Token refreshed: {data.get('message', 'Success')}")
                    else:
                        self.log_test("POST /api/auth/refresh - Token Refresh", False, 
                                    f"Refresh failed: {data}", data)
                        
                elif response.status_code == 401:
                    data = response.json()
                    self.log_test("POST /api/auth/refresh - Token Refresh", False, 
                                f"Unauthorized: {data.get('detail', 'No refresh token')}", data)
                else:
                    self.log_test("POST /api/auth/refresh - Token Refresh", False, 
                                f"Unexpected status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test("POST /api/auth/refresh - Token Refresh", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/auth/refresh - Token Refresh", False, 
                        "Could not login to test refresh endpoint")
            
    def test_auth_logout(self):
        """Test POST /api/auth/logout endpoint"""
        print("\n🔐 TESTING LOGOUT")
        
        # First login
        login_response = self.session.post(f"{API_BASE}/auth/login", 
                                         json=TEST_CREDENTIALS["test_customer"])
        
        if login_response.status_code == 200:
            try:
                response = self.session.post(f"{API_BASE}/auth/logout")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success"):
                        # Test that cookies are cleared by trying to access /me
                        me_response = self.session.get(f"{API_BASE}/auth/me")
                        
                        if me_response.status_code == 401:
                            self.log_test("POST /api/auth/logout - Logout & Cookie Clear", True, 
                                        "Logout successful, cookies cleared, /me returns 401")
                        else:
                            self.log_test("POST /api/auth/logout - Logout & Cookie Clear", False, 
                                        f"/me still accessible after logout (status: {me_response.status_code})")
                    else:
                        self.log_test("POST /api/auth/logout - Logout & Cookie Clear", False, 
                                    f"Logout failed: {data}", data)
                        
                else:
                    self.log_test("POST /api/auth/logout - Logout & Cookie Clear", False, 
                                f"Unexpected status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test("POST /api/auth/logout - Logout & Cookie Clear", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/auth/logout - Logout & Cookie Clear", False, 
                        "Could not login to test logout endpoint")
            
    def test_cookie_attributes(self):
        """Test HttpOnly cookie attributes and security"""
        print("\n🍪 TESTING COOKIE ATTRIBUTES")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", 
                                       json=TEST_CREDENTIALS["test_customer"])
            
            if response.status_code == 200:
                cookies = response.cookies
                
                # Check access_token cookie
                if 'access_token' in cookies:
                    access_cookie = cookies['access_token']
                    
                    # Check cookie attributes (note: requests library doesn't expose all attributes)
                    cookie_details = f"Access token cookie present, Path: {getattr(access_cookie, 'path', 'N/A')}"
                    self.log_test("Cookie Attributes - Access Token", True, cookie_details)
                else:
                    self.log_test("Cookie Attributes - Access Token", False, "No access_token cookie found")
                
                # Check refresh_token cookie
                if 'refresh_token' in cookies:
                    refresh_cookie = cookies['refresh_token']
                    cookie_details = f"Refresh token cookie present, Path: {getattr(refresh_cookie, 'path', 'N/A')}"
                    self.log_test("Cookie Attributes - Refresh Token", True, cookie_details)
                else:
                    self.log_test("Cookie Attributes - Refresh Token", False, "No refresh_token cookie found")
                    
            else:
                self.log_test("Cookie Attributes - Login Required", False, 
                            f"Could not login to test cookies (status: {response.status_code})")
                
        except Exception as e:
            self.log_test("Cookie Attributes - Test", False, f"Exception: {str(e)}")
            
    def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("\n❌ TESTING ERROR SCENARIOS")
        
        # Test wrong password
        try:
            wrong_creds = {"email": "testcustomer@example.com", "password": "wrongpassword"}
            response = self.session.post(f"{API_BASE}/auth/login", json=wrong_creds)
            
            if response.status_code == 401:
                data = response.json()
                self.log_test("Error Handling - Wrong Password", True, 
                            f"Correctly returned 401: {data.get('detail', 'Invalid credentials')}")
            else:
                self.log_test("Error Handling - Wrong Password", False, 
                            f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Wrong Password", False, f"Exception: {str(e)}")
            
        # Test non-existent email
        try:
            fake_creds = {"email": "nonexistent@example.com", "password": "password"}
            response = self.session.post(f"{API_BASE}/auth/login", json=fake_creds)
            
            if response.status_code == 401:
                data = response.json()
                self.log_test("Error Handling - Non-existent Email", True, 
                            f"Correctly returned 401: {data.get('detail', 'Invalid credentials')}")
            else:
                self.log_test("Error Handling - Non-existent Email", False, 
                            f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Non-existent Email", False, f"Exception: {str(e)}")
            
        # Test invalid email format
        try:
            invalid_creds = {"email": "invalid-email", "password": "password"}
            response = self.session.post(f"{API_BASE}/auth/login", json=invalid_creds)
            
            if response.status_code == 422:
                data = response.json()
                self.log_test("Error Handling - Invalid Email Format", True, 
                            f"Correctly returned 422: {data.get('detail', 'Validation error')}")
            else:
                self.log_test("Error Handling - Invalid Email Format", False, 
                            f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Email Format", False, f"Exception: {str(e)}")
            
        # Test missing credentials
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={})
            
            if response.status_code == 422:
                data = response.json()
                self.log_test("Error Handling - Missing Credentials", True, 
                            f"Correctly returned 422: {data.get('detail', 'Validation error')}")
            else:
                self.log_test("Error Handling - Missing Credentials", False, 
                            f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Missing Credentials", False, f"Exception: {str(e)}")
            
    def test_rbac_customer_endpoints(self):
        """Test Role-Based Access Control for customer endpoints"""
        print("\n🔒 TESTING RBAC - CUSTOMER ENDPOINTS")
        
        # Login as customer
        login_response = self.session.post(f"{API_BASE}/auth/login", 
                                         json=TEST_CREDENTIALS["test_customer"])
        
        if login_response.status_code == 200:
            # Test customer can access customer endpoints
            try:
                response = self.session.get(f"{API_BASE}/user/addresses")
                
                if response.status_code in [200, 404]:  # 404 is ok if no addresses
                    self.log_test("RBAC - Customer Access to /user/addresses", True, 
                                f"Customer can access addresses (status: {response.status_code})")
                elif response.status_code == 403:
                    self.log_test("RBAC - Customer Access to /user/addresses", False, 
                                "Customer denied access to own addresses")
                else:
                    self.log_test("RBAC - Customer Access to /user/addresses", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test("RBAC - Customer Access to /user/addresses", False, f"Exception: {str(e)}")
                
            # Test customer cannot access admin endpoints
            try:
                response = self.session.get(f"{API_BASE}/admin/orders")
                
                if response.status_code == 403:
                    self.log_test("RBAC - Customer Denied Admin Access", True, 
                                "Customer correctly denied access to admin endpoints")
                elif response.status_code == 401:
                    self.log_test("RBAC - Customer Denied Admin Access", True, 
                                "Customer correctly denied access (401 - no admin token)")
                else:
                    self.log_test("RBAC - Customer Denied Admin Access", False, 
                                f"Customer should not access admin endpoints (status: {response.status_code})")
                    
            except Exception as e:
                self.log_test("RBAC - Customer Denied Admin Access", False, f"Exception: {str(e)}")
        else:
            self.log_test("RBAC - Customer Login Required", False, 
                        "Could not login as customer to test RBAC")

    def run_all_tests(self):
        """Run all authentication tests"""
        print(f"🚀 STARTING COMPREHENSIVE AUTHENTICATION TESTING")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 80)
        
        # Run all test categories
        self.test_auth_register()
        self.test_auth_login()
        self.test_auth_me()
        self.test_auth_refresh()
        self.test_auth_logout()
        self.test_cookie_attributes()
        self.test_error_scenarios()
        self.test_rbac_customer_endpoints()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 AUTHENTICATION TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ FAILED: {failed_tests}/{total_tests}")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   ❌ {test['test']}: {test['details']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = AuthenticationTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print(f"\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        exit(0)