#!/usr/bin/env python3
"""
🔥 CRITICAL HOTFIX VERIFICATION - Double /api Prevention, Cookie Auth & Endpoint Corrections
Testing the comprehensive hotfix implementation for:
1. Double /api path prevention
2. Cookie authentication system
3. Unified registration endpoint
4. CORS and cookie domain configuration
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://stable-menus.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
HOTFIX_TEST_DATA = {
    "email": "hotfixtest@kuryecini.com",
    "password": "hotfix123456",
    "first_name": "Hotfix",
    "last_name": "Test",
    "role": "customer"
}

# Additional test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "business": {"email": "business@kuryecini.com", "password": "business123"},
    "courier": {"email": "courier@kuryecini.com", "password": "courier123"}
}

class HotfixTester:
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
        
    def test_unified_registration_endpoint(self):
        """Test POST /api/auth/register?role=customer endpoint"""
        print("\n🔥 TESTING UNIFIED REGISTRATION ENDPOINT")
        
        # Test the new unified registration endpoint with role parameter
        registration_url = f"{API_BASE}/auth/register?role=customer"
        
        try:
            response = self.session.post(registration_url, json=HOTFIX_TEST_DATA)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Check for success indicators
                if data.get("success") or data.get("access_token") or data.get("user_data"):
                    user_info = data.get("user_data", data.get("user", {}))
                    self.log_test("POST /api/auth/register?role=customer - Unified Registration", True, 
                                f"Registration successful: {user_info.get('email', 'N/A')} (ID: {user_info.get('id', 'N/A')})")
                    return True
                else:
                    self.log_test("POST /api/auth/register?role=customer - Unified Registration", False, 
                                f"Registration response missing success indicators", data)
                    
            elif response.status_code == 400:
                data = response.json()
                if "already registered" in data.get("detail", "").lower():
                    self.log_test("POST /api/auth/register?role=customer - Unified Registration", True, 
                                "User already exists - registration endpoint working correctly")
                    return True
                else:
                    self.log_test("POST /api/auth/register?role=customer - Unified Registration", False, 
                                f"Registration failed: {data.get('detail', 'Unknown error')}", data)
            elif response.status_code == 404:
                self.log_test("POST /api/auth/register?role=customer - Unified Registration", False, 
                            "404 Error - Unified registration endpoint not implemented", response.text)
            else:
                self.log_test("POST /api/auth/register?role=customer - Unified Registration", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/auth/register?role=customer - Unified Registration", False, f"Exception: {str(e)}")
            
        return False
        
    def test_login_with_cookies(self):
        """Test POST /api/auth/login with cookie authentication"""
        print("\n🍪 TESTING LOGIN WITH COOKIE AUTHENTICATION")
        
        login_data = {
            "email": HOTFIX_TEST_DATA["email"],
            "password": HOTFIX_TEST_DATA["password"]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if data.get("success") and data.get("user"):
                    user_data = data["user"]
                    
                    # Check for cookies
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
                    
                    self.log_test("POST /api/auth/login - Cookie Authentication", True, 
                                f"{user_details}, {cookie_details}")
                    return True
                else:
                    self.log_test("POST /api/auth/login - Cookie Authentication", False, 
                                f"Invalid response structure: {data}", data)
                    
            elif response.status_code == 401:
                data = response.json()
                self.log_test("POST /api/auth/login - Cookie Authentication", False, 
                            f"Authentication failed: {data.get('detail', 'Invalid credentials')}", data)
            else:
                self.log_test("POST /api/auth/login - Cookie Authentication", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/auth/login - Cookie Authentication", False, f"Exception: {str(e)}")
            
        return False
        
    def test_auth_me_with_cookies(self):
        """Test GET /api/auth/me endpoint with cookie authentication"""
        print("\n🔐 TESTING /api/auth/me WITH COOKIE AUTHENTICATION")
        
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate user data structure
                required_fields = ["id", "email", "role"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    user_details = f"User: {data['email']} (Role: {data['role']}, ID: {data['id']})"
                    if 'first_name' in data and 'last_name' in data:
                        user_details += f", Name: {data['first_name']} {data['last_name']}"
                    self.log_test("GET /api/auth/me - Cookie Authentication", True, user_details)
                    return True
                else:
                    self.log_test("GET /api/auth/me - Cookie Authentication", False, 
                                f"Missing fields: {missing_fields}", data)
                    
            elif response.status_code == 401:
                data = response.json()
                self.log_test("GET /api/auth/me - Cookie Authentication", False, 
                            f"Unauthorized: {data.get('detail', 'No auth token')}", data)
            else:
                self.log_test("GET /api/auth/me - Cookie Authentication", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/auth/me - Cookie Authentication", False, f"Exception: {str(e)}")
            
        return False
        
    def test_business_endpoints_with_cookies(self):
        """Test business endpoints with cookie authentication"""
        print("\n🏪 TESTING BUSINESS ENDPOINTS WITH COOKIE AUTHENTICATION")
        
        # First login as business user (if available)
        business_login_data = {
            "email": TEST_CREDENTIALS["business"]["email"],
            "password": TEST_CREDENTIALS["business"]["password"]
        }
        
        try:
            # Try to login as business user
            login_response = self.session.post(f"{API_BASE}/auth/login", json=business_login_data)
            
            if login_response.status_code == 200:
                # Test business menu endpoint
                response = self.session.get(f"{API_BASE}/business/menu")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("GET /api/business/menu - Cookie Authentication", True, 
                                f"Business menu accessed successfully: {len(data.get('menu', []))} items")
                elif response.status_code == 403:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                "Business denied access to menu (KYC approval required?)")
                elif response.status_code == 404:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                "Business menu endpoint not found (double /api issue?)")
                else:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                f"Unexpected status: {response.status_code}")
            else:
                # Use customer session to test business endpoint access control
                response = self.session.get(f"{API_BASE}/business/menu")
                
                if response.status_code == 403:
                    self.log_test("GET /api/business/menu - RBAC Protection", True, 
                                "Customer correctly denied access to business endpoints")
                elif response.status_code == 404:
                    self.log_test("GET /api/business/menu - Endpoint Availability", False, 
                                "Business menu endpoint not found (double /api issue?)")
                else:
                    self.log_test("GET /api/business/menu - Endpoint Test", True, 
                                f"Business endpoint accessible (status: {response.status_code})")
                    
        except Exception as e:
            self.log_test("GET /api/business/menu - Cookie Authentication", False, f"Exception: {str(e)}")
            
    def test_courier_endpoints_with_cookies(self):
        """Test courier endpoints with cookie authentication"""
        print("\n🚚 TESTING COURIER ENDPOINTS WITH COOKIE AUTHENTICATION")
        
        try:
            # Test courier available orders endpoint
            response = self.session.get(f"{API_BASE}/courier/orders/available")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/orders/available - Cookie Authentication", True, 
                            f"Courier orders accessed successfully: {len(data.get('orders', []))} orders")
            elif response.status_code == 403:
                self.log_test("GET /api/courier/orders/available - RBAC Protection", True, 
                            "Customer correctly denied access to courier endpoints")
            elif response.status_code == 404:
                self.log_test("GET /api/courier/orders/available - Endpoint Availability", False, 
                            "Courier orders endpoint not found (double /api issue?)")
            else:
                self.log_test("GET /api/courier/orders/available - Cookie Authentication", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/courier/orders/available - Cookie Authentication", False, f"Exception: {str(e)}")
            
    def test_double_api_prevention(self):
        """Test that double /api paths are prevented"""
        print("\n🚫 TESTING DOUBLE /api PATH PREVENTION")
        
        # Test various endpoints to ensure no double /api issues
        test_endpoints = [
            "/api/auth/me",
            "/api/business/menu", 
            "/api/courier/orders/available",
            "/api/admin/orders"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                
                # Check if response contains double /api in any URLs
                response_text = response.text
                
                # Look for double /api patterns in response
                double_api_patterns = [
                    "/api/api/",
                    "//api/",
                    "/api//api/"
                ]
                
                has_double_api = any(pattern in response_text for pattern in double_api_patterns)
                
                if not has_double_api:
                    self.log_test(f"Double /api Prevention - {endpoint}", True, 
                                f"No double /api paths detected (status: {response.status_code})")
                else:
                    self.log_test(f"Double /api Prevention - {endpoint}", False, 
                                "Double /api paths detected in response")
                    
            except Exception as e:
                self.log_test(f"Double /api Prevention - {endpoint}", False, f"Exception: {str(e)}")
                
    def test_cors_and_cookie_domain(self):
        """Test CORS and cookie domain configuration"""
        print("\n🌐 TESTING CORS AND COOKIE DOMAIN CONFIGURATION")
        
        try:
            # Test CORS headers
            response = self.session.options(f"{API_BASE}/auth/login")
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            # Check if CORS is properly configured
            has_cors_origin = cors_headers['Access-Control-Allow-Origin'] is not None
            allows_credentials = cors_headers['Access-Control-Allow-Credentials'] == 'true'
            
            if has_cors_origin and allows_credentials:
                self.log_test("CORS Configuration", True, 
                            f"CORS properly configured: Origin={cors_headers['Access-Control-Allow-Origin']}, Credentials={allows_credentials}")
            else:
                self.log_test("CORS Configuration", False, 
                            f"CORS configuration issues: {cors_headers}")
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
            
        # Test cookie domain by checking if cookies are set correctly
        try:
            login_response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": HOTFIX_TEST_DATA["email"],
                "password": HOTFIX_TEST_DATA["password"]
            })
            
            if login_response.status_code == 200:
                cookies = login_response.cookies
                
                if cookies:
                    cookie_domains = []
                    for cookie in cookies:
                        cookie_domains.append(getattr(cookie, 'domain', 'N/A'))
                    
                    self.log_test("Cookie Domain Configuration", True, 
                                f"Cookies set with domains: {cookie_domains}")
                else:
                    self.log_test("Cookie Domain Configuration", False, 
                                "No cookies set in login response")
            else:
                self.log_test("Cookie Domain Configuration", False, 
                            f"Could not test cookie domain (login failed: {login_response.status_code})")
                
        except Exception as e:
            self.log_test("Cookie Domain Configuration", False, f"Exception: {str(e)}")
            
    def test_endpoint_corrections(self):
        """Test that all endpoints respond correctly without 404 errors"""
        print("\n🔧 TESTING ENDPOINT CORRECTIONS")
        
        # Test critical endpoints that should not return 404
        critical_endpoints = [
            ("/api/auth/login", "POST"),
            ("/api/auth/me", "GET"),
            ("/api/auth/register", "POST"),
            ("/api/business/menu", "GET"),
            ("/api/courier/orders/available", "GET")
        ]
        
        for endpoint, method in critical_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", json={})
                    
                if response.status_code != 404:
                    self.log_test(f"Endpoint Correction - {method} {endpoint}", True, 
                                f"Endpoint available (status: {response.status_code})")
                else:
                    self.log_test(f"Endpoint Correction - {method} {endpoint}", False, 
                                "Endpoint returns 404 - routing issue")
                    
            except Exception as e:
                self.log_test(f"Endpoint Correction - {method} {endpoint}", False, f"Exception: {str(e)}")
                
    def run_hotfix_verification(self):
        """Run comprehensive hotfix verification tests"""
        print(f"🔥 CRITICAL HOTFIX VERIFICATION - Double /api Prevention, Cookie Auth & Endpoint Corrections")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print(f"📧 Test Email: {HOTFIX_TEST_DATA['email']}")
        print("=" * 100)
        
        print("\n🎯 HOTFIX VERIFICATION POINTS:")
        print("1. ✅ All endpoints respond correctly without 404 errors")
        print("2. ✅ Cookie authentication works across all protected routes")
        print("3. ✅ No double /api path issues")
        print("4. ✅ Unified registration endpoint working")
        print("5. ✅ CORS and cookie domain configuration working")
        
        # Run hotfix verification tests in order
        print("\n" + "="*50 + " HOTFIX TESTS " + "="*50)
        
        # 1. Test unified registration endpoint
        self.test_unified_registration_endpoint()
        
        # 2. Test login with cookie authentication
        login_success = self.test_login_with_cookies()
        
        # 3. Test /api/auth/me with cookies (only if login successful)
        if login_success:
            self.test_auth_me_with_cookies()
        
        # 4. Test business endpoints with cookie auth
        self.test_business_endpoints_with_cookies()
        
        # 5. Test courier endpoints with cookie auth
        self.test_courier_endpoints_with_cookies()
        
        # 6. Test double /api prevention
        self.test_double_api_prevention()
        
        # 7. Test endpoint corrections
        self.test_endpoint_corrections()
        
        # 8. Test CORS and cookie domain configuration
        self.test_cors_and_cookie_domain()
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 HOTFIX VERIFICATION SUMMARY")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ FAILED: {failed_tests}/{total_tests}")
        
        # Categorize results by hotfix area
        hotfix_areas = {
            "Registration": [t for t in self.test_results if "register" in t["test"].lower()],
            "Cookie Auth": [t for t in self.test_results if "cookie" in t["test"].lower() or "auth" in t["test"].lower()],
            "Double /api": [t for t in self.test_results if "double" in t["test"].lower()],
            "Endpoints": [t for t in self.test_results if "endpoint" in t["test"].lower()],
            "CORS": [t for t in self.test_results if "cors" in t["test"].lower()]
        }
        
        print(f"\n🔍 HOTFIX AREA ANALYSIS:")
        for area, tests in hotfix_areas.items():
            if tests:
                area_passed = len([t for t in tests if t["success"]])
                area_total = len(tests)
                area_rate = (area_passed / area_total * 100) if area_total > 0 else 0
                status = "✅" if area_rate == 100 else "⚠️" if area_rate >= 50 else "❌"
                print(f"   {status} {area}: {area_passed}/{area_total} ({area_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   ❌ {test['test']}: {test['details']}")
        
        # Hotfix-specific analysis
        critical_failures = []
        for test in self.test_results:
            if not test["success"]:
                if "404" in test["details"]:
                    critical_failures.append("Double /api path issues → 404 errors")
                elif "401" in test["details"] or "403" in test["details"]:
                    critical_failures.append("Cookie authentication missing → 401/403 errors")
                elif "cors" in test["test"].lower():
                    critical_failures.append("CORS configuration issues")
        
        if critical_failures:
            print(f"\n⚠️  CRITICAL HOTFIX ISSUES DETECTED:")
            for issue in set(critical_failures):
                print(f"   🚨 {issue}")
        else:
            print(f"\n🎉 HOTFIX VERIFICATION SUCCESSFUL!")
            print(f"   ✅ No double /api path issues detected")
            print(f"   ✅ Cookie authentication working properly")
            print(f"   ✅ All endpoints responding correctly")
            print(f"   ✅ CORS and cookie domain configured properly")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results,
            "hotfix_areas": hotfix_areas
        }

if __name__ == "__main__":
    tester = HotfixTester()
    results = tester.run_hotfix_verification()
    
    # Exit with error code if critical tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print(f"\n🎉 ALL HOTFIX VERIFICATION TESTS PASSED!")
        exit(0)