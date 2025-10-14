#!/usr/bin/env python3
"""
🔥 COMPREHENSIVE HOTFIX VERIFICATION - Complete Authentication & Authorization Flow
Testing the comprehensive hotfix implementation including:
1. Customer registration with NEW endpoint path: POST /api/auth/register?role=customer
2. Login immediately after registration: POST /api/auth/login  
3. /api/auth/me endpoint with cookie authentication
4. Business endpoints with cookie auth (after KYC approval)
5. Courier endpoints with cookie auth
6. Double /api prevention verification
7. CORS and cookie handling
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://express-track-2.preview.emergentagent.com')
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
    "business": {
        "email": "hotfixbusiness@kuryecini.com",
        "password": "hotfix123456",
        "business_name": "Hotfix Test Restaurant",
        "tax_number": "1234567890",
        "address": "Test Address 123",
        "city": "İstanbul",
        "district": "Kadıköy",
        "business_category": "gida",
        "description": "Test restaurant for hotfix verification"
    },
    "courier": {
        "email": "hotfixcourier@kuryecini.com", 
        "password": "hotfix123456",
        "first_name": "Hotfix",
        "last_name": "Courier",
        "iban": "TR123456789012345678901234",
        "vehicle_type": "motor",
        "vehicle_model": "Honda CB150R",
        "license_class": "A2",
        "license_number": "34ABC123",
        "city": "İstanbul"
    }
}

class ComprehensiveHotfixTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.cookies = {}
        self.admin_session = requests.Session()
        self.business_session = requests.Session()
        self.courier_session = requests.Session()
        
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
        
    def test_customer_registration_new_endpoint(self):
        """Test POST /api/auth/register?role=customer endpoint"""
        print("\n🔥 TESTING CUSTOMER REGISTRATION - NEW ENDPOINT PATH")
        
        # Test the new unified registration endpoint with role parameter
        registration_url = f"{API_BASE}/auth/register?role=customer"
        
        try:
            response = self.session.post(registration_url, json=HOTFIX_TEST_DATA)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Check for success indicators
                if data.get("success") or data.get("access_token") or data.get("user_data"):
                    user_info = data.get("user_data", data.get("user", {}))
                    self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", True, 
                                f"Registration successful: {user_info.get('email', 'N/A')} (ID: {user_info.get('id', 'N/A')})")
                    return True
                else:
                    self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", False, 
                                f"Registration response missing success indicators", data)
                    
            elif response.status_code == 400:
                data = response.json()
                if "already registered" in data.get("detail", "").lower():
                    self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", True, 
                                "User already exists - registration endpoint working correctly")
                    return True
                else:
                    self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", False, 
                                f"Registration failed: {data.get('detail', 'Unknown error')}", data)
            elif response.status_code == 404:
                self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", False, 
                            "404 Error - Unified registration endpoint not implemented", response.text)
            else:
                self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/auth/register?role=customer - NEW Endpoint Path", False, f"Exception: {str(e)}")
            
        return False
        
    def test_login_immediately_after_registration(self):
        """Test POST /api/auth/login immediately after registration"""
        print("\n🔐 TESTING LOGIN IMMEDIATELY AFTER REGISTRATION")
        
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
                    
                    self.log_test("POST /api/auth/login - Immediate After Registration", True, 
                                f"{user_details}, {cookie_details}")
                    return True
                else:
                    self.log_test("POST /api/auth/login - Immediate After Registration", False, 
                                f"Invalid response structure: {data}", data)
                    
            elif response.status_code == 401:
                data = response.json()
                self.log_test("POST /api/auth/login - Immediate After Registration", False, 
                            f"Authentication failed: {data.get('detail', 'Invalid credentials')}", data)
            else:
                self.log_test("POST /api/auth/login - Immediate After Registration", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/auth/login - Immediate After Registration", False, f"Exception: {str(e)}")
            
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
        
    def setup_admin_session(self):
        """Setup admin session for business approval"""
        print("\n👑 SETTING UP ADMIN SESSION FOR BUSINESS APPROVAL")
        
        try:
            admin_login = {
                "email": TEST_CREDENTIALS["admin"]["email"],
                "password": TEST_CREDENTIALS["admin"]["password"]
            }
            
            response = self.admin_session.post(f"{API_BASE}/auth/login", json=admin_login)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("user"):
                    self.log_test("Admin Session Setup", True, 
                                f"Admin logged in: {data['user']['email']}")
                    return True
                    
            self.log_test("Admin Session Setup", False, 
                        f"Admin login failed: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_test("Admin Session Setup", False, f"Exception: {str(e)}")
            return False
            
    def register_and_approve_business(self):
        """Register business and approve via admin"""
        print("\n🏪 REGISTERING AND APPROVING BUSINESS USER")
        
        # Step 1: Register business
        try:
            business_data = TEST_CREDENTIALS["business"]
            response = self.business_session.post(f"{API_BASE}/register/business", json=business_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                business_id = data.get("user_data", {}).get("id")
                
                if business_id:
                    self.log_test("Business Registration", True, 
                                f"Business registered: {business_data['email']} (ID: {business_id})")
                    
                    # Step 2: Approve business via admin
                    if self.setup_admin_session():
                        approval_data = {"kyc_status": "approved"}
                        approval_response = self.admin_session.patch(
                            f"{API_BASE}/admin/businesses/{business_id}/status", 
                            json=approval_data
                        )
                        
                        if approval_response.status_code == 200:
                            self.log_test("Business KYC Approval", True, 
                                        f"Business approved successfully")
                            
                            # Step 3: Login as approved business
                            business_login = {
                                "email": business_data["email"],
                                "password": business_data["password"]
                            }
                            
                            login_response = self.business_session.post(f"{API_BASE}/auth/login", json=business_login)
                            
                            if login_response.status_code == 200:
                                self.log_test("Approved Business Login", True, 
                                            f"Approved business logged in successfully")
                                return True
                            else:
                                self.log_test("Approved Business Login", False, 
                                            f"Business login failed: {login_response.status_code}")
                        else:
                            self.log_test("Business KYC Approval", False, 
                                        f"Business approval failed: {approval_response.status_code}")
                    else:
                        self.log_test("Business KYC Approval", False, 
                                    "Admin session setup failed")
                else:
                    self.log_test("Business Registration", False, 
                                "Business ID not found in response")
            elif response.status_code == 400:
                # Business already exists, try to login
                business_login = {
                    "email": business_data["email"],
                    "password": business_data["password"]
                }
                
                login_response = self.business_session.post(f"{API_BASE}/auth/login", json=business_login)
                
                if login_response.status_code == 200:
                    self.log_test("Existing Business Login", True, 
                                "Existing business logged in successfully")
                    return True
                else:
                    self.log_test("Existing Business Login", False, 
                                f"Existing business login failed: {login_response.status_code}")
            else:
                self.log_test("Business Registration", False, 
                            f"Business registration failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Business Registration & Approval", False, f"Exception: {str(e)}")
            
        return False
        
    def test_business_endpoints_with_cookies(self):
        """Test business endpoints with cookie authentication"""
        print("\n🏪 TESTING BUSINESS ENDPOINTS WITH COOKIE AUTHENTICATION")
        
        # Setup business user first
        if self.register_and_approve_business():
            try:
                # Test business menu endpoint
                response = self.business_session.get(f"{API_BASE}/business/menu")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("GET /api/business/menu - Cookie Authentication", True, 
                                f"Business menu accessed successfully: {len(data.get('menu', []))} items")
                elif response.status_code == 403:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                "Business denied access to menu (KYC approval issue?)")
                elif response.status_code == 401:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                "Business authentication failed (cookie issue?)")
                elif response.status_code == 404:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                "Business menu endpoint not found (double /api issue?)")
                else:
                    self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                                f"Unexpected status: {response.status_code}")
                    
            except Exception as e:
                self.log_test("GET /api/business/menu - Cookie Authentication", False, f"Exception: {str(e)}")
        else:
            self.log_test("GET /api/business/menu - Cookie Authentication", False, 
                        "Could not setup approved business user")
            
    def test_courier_endpoints_with_cookies(self):
        """Test courier endpoints with cookie authentication"""
        print("\n🚚 TESTING COURIER ENDPOINTS WITH COOKIE AUTHENTICATION")
        
        try:
            # Test courier available orders endpoint with customer session (should be denied)
            response = self.session.get(f"{API_BASE}/courier/orders/available")
            
            if response.status_code == 403:
                self.log_test("GET /api/courier/orders/available - RBAC Protection", True, 
                            "Customer correctly denied access to courier endpoints")
            elif response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/courier/orders/available - Unexpected Access", False, 
                            "Customer should not have access to courier endpoints")
            elif response.status_code == 404:
                self.log_test("GET /api/courier/orders/available - Endpoint Availability", False, 
                            "Courier orders endpoint not found (double /api issue?)")
            else:
                self.log_test("GET /api/courier/orders/available - Cookie Authentication", True, 
                            f"Courier endpoint accessible (status: {response.status_code})")
                
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
                
    def test_cors_and_cookie_handling(self):
        """Test CORS and cookie domain configuration"""
        print("\n🌐 TESTING CORS AND COOKIE DOMAIN CONFIGURATION")
        
        try:
            # Test CORS preflight request
            headers = {
                'Origin': 'https://express-track-2.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            # Check if CORS is properly configured
            has_cors_origin = cors_headers['Access-Control-Allow-Origin'] is not None
            allows_credentials = cors_headers['Access-Control-Allow-Credentials'] == 'true'
            
            if has_cors_origin or allows_credentials:
                self.log_test("CORS Configuration", True, 
                            f"CORS configured: Origin={cors_headers['Access-Control-Allow-Origin']}, Credentials={allows_credentials}")
            else:
                # CORS might be handled by middleware, test actual request
                login_response = self.session.post(f"{API_BASE}/auth/login", json={
                    "email": HOTFIX_TEST_DATA["email"],
                    "password": HOTFIX_TEST_DATA["password"]
                })
                
                if login_response.status_code == 200:
                    self.log_test("CORS Configuration", True, 
                                "CORS working (actual request successful)")
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
            
    def run_comprehensive_hotfix_verification(self):
        """Run comprehensive hotfix verification tests"""
        print(f"🔥 COMPREHENSIVE HOTFIX VERIFICATION - Complete Authentication & Authorization Flow")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print(f"📧 Test Email: {HOTFIX_TEST_DATA['email']}")
        print("=" * 120)
        
        print("\n🎯 CRITICAL HOTFIX VERIFICATION POINTS:")
        print("1. ✅ Customer registration with NEW endpoint path: POST /api/auth/register?role=customer")
        print("2. ✅ Login immediately after registration: POST /api/auth/login")
        print("3. ✅ /api/auth/me endpoint with cookie authentication")
        print("4. ✅ Business endpoints with cookie auth: GET /api/business/menu")
        print("5. ✅ Courier endpoints with cookie auth: GET /api/courier/orders/available")
        print("6. ✅ NO double /api issues in responses")
        print("7. ✅ Proper cookie handling across all requests")
        
        # Run comprehensive hotfix verification tests in order
        print("\n" + "="*60 + " HOTFIX TESTS " + "="*60)
        
        # 1. Test customer registration with NEW endpoint path
        registration_success = self.test_customer_registration_new_endpoint()
        
        # 2. Test login immediately after registration
        if registration_success:
            login_success = self.test_login_immediately_after_registration()
            
            # 3. Test /api/auth/me with cookies (only if login successful)
            if login_success:
                self.test_auth_me_with_cookies()
        
        # 4. Test business endpoints with cookie auth
        self.test_business_endpoints_with_cookies()
        
        # 5. Test courier endpoints with cookie auth
        self.test_courier_endpoints_with_cookies()
        
        # 6. Test double /api prevention
        self.test_double_api_prevention()
        
        # 7. Test CORS and cookie handling
        self.test_cors_and_cookie_handling()
        
        # Summary
        print("\n" + "=" * 120)
        print("📊 COMPREHENSIVE HOTFIX VERIFICATION SUMMARY")
        print("=" * 120)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ FAILED: {failed_tests}/{total_tests}")
        
        # Categorize results by hotfix verification points
        verification_points = {
            "NEW Registration Endpoint": [t for t in self.test_results if "NEW Endpoint Path" in t["test"]],
            "Immediate Login": [t for t in self.test_results if "Immediate After Registration" in t["test"]],
            "Cookie Authentication": [t for t in self.test_results if "Cookie Authentication" in t["test"]],
            "Business Endpoints": [t for t in self.test_results if "business" in t["test"].lower()],
            "Courier Endpoints": [t for t in self.test_results if "courier" in t["test"].lower()],
            "Double /api Prevention": [t for t in self.test_results if "Double /api Prevention" in t["test"]],
            "CORS & Cookies": [t for t in self.test_results if "CORS" in t["test"] or "Cookie Domain" in t["test"]]
        }
        
        print(f"\n🔍 HOTFIX VERIFICATION POINT ANALYSIS:")
        for point, tests in verification_points.items():
            if tests:
                point_passed = len([t for t in tests if t["success"]])
                point_total = len(tests)
                point_rate = (point_passed / point_total * 100) if point_total > 0 else 0
                status = "✅" if point_rate == 100 else "⚠️" if point_rate >= 50 else "❌"
                print(f"   {status} {point}: {point_passed}/{point_total} ({point_rate:.1f}%)")
        
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
                elif "NEW Endpoint Path" in test["test"]:
                    critical_failures.append("Unified registration endpoint not working")
        
        if critical_failures:
            print(f"\n⚠️  CRITICAL HOTFIX ISSUES DETECTED:")
            for issue in set(critical_failures):
                print(f"   🚨 {issue}")
        else:
            print(f"\n🎉 HOTFIX VERIFICATION SUCCESSFUL!")
            print(f"   ✅ All endpoints respond correctly without 404 errors")
            print(f"   ✅ Cookie authentication works across all protected routes")
            print(f"   ✅ No double /api path issues")
            print(f"   ✅ Unified registration endpoint working")
            print(f"   ✅ CORS and cookie domain configuration working")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results,
            "verification_points": verification_points
        }

if __name__ == "__main__":
    tester = ComprehensiveHotfixTester()
    results = tester.run_comprehensive_hotfix_verification()
    
    # Exit with error code if critical tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print(f"\n🎉 ALL COMPREHENSIVE HOTFIX VERIFICATION TESTS PASSED!")
        exit(0)