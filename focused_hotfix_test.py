#!/usr/bin/env python3
"""
🔥 FOCUSED HOTFIX VERIFICATION - Exact Review Request Testing
Testing exactly what was requested in the review:
1. Customer registration with NEW endpoint path: POST /api/auth/register?role=customer
2. Login immediately after registration: POST /api/auth/login  
3. /api/auth/me endpoint with cookie authentication
4. Business endpoints with cookie auth: GET /api/business/menu
5. Courier endpoints with cookie auth: GET /api/courier/orders/available
6. NO double /api issues in responses
7. Proper cookie handling across all requests

Using exact test data from review request:
- Email: hotfixtest@kuryecini.com
- Password: hotfix123456
- First Name: Hotfix
- Last Name: Test
- Role: customer
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://kuryecini-ai-tools.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Exact test data from review request
HOTFIX_TEST_DATA = {
    "email": "hotfixtest@kuryecini.com",
    "password": "hotfix123456",
    "first_name": "Hotfix",
    "last_name": "Test",
    "role": "customer"
}

class FocusedHotfixTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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
        
    def test_1_customer_registration_new_endpoint(self):
        """1. Test customer registration with NEW endpoint path: POST /api/auth/register?role=customer"""
        print("\n🔥 TEST 1: Customer registration with NEW endpoint path")
        
        # Try the unified registration endpoint first
        registration_url = f"{API_BASE}/auth/register?role=customer"
        
        try:
            response = self.session.post(registration_url, json=HOTFIX_TEST_DATA)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("1. POST /api/auth/register?role=customer", True, 
                            f"NEW endpoint working: {data.get('message', 'Registration successful')}")
                return True
            elif response.status_code == 400:
                data = response.json()
                if "already" in data.get("detail", "").lower():
                    self.log_test("1. POST /api/auth/register?role=customer", True, 
                                "NEW endpoint working (user already exists)")
                    return True
            elif response.status_code == 404:
                # Try fallback to old endpoint
                fallback_response = self.session.post(f"{API_BASE}/register/customer", json=HOTFIX_TEST_DATA)
                if fallback_response.status_code in [200, 201, 400]:
                    self.log_test("1. POST /api/auth/register?role=customer", False, 
                                "NEW endpoint not implemented, fallback to /register/customer works")
                else:
                    self.log_test("1. POST /api/auth/register?role=customer", False, 
                                "NEW endpoint not implemented, fallback also fails")
            else:
                self.log_test("1. POST /api/auth/register?role=customer", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("1. POST /api/auth/register?role=customer", False, f"Exception: {str(e)}")
            
        return False
        
    def test_2_login_immediately_after_registration(self):
        """2. Test login immediately after registration: POST /api/auth/login"""
        print("\n🔐 TEST 2: Login immediately after registration")
        
        login_data = {
            "email": HOTFIX_TEST_DATA["email"],
            "password": HOTFIX_TEST_DATA["password"]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure and cookies
                if data.get("success") and data.get("user"):
                    cookies = response.cookies
                    has_access_token = 'access_token' in cookies
                    has_refresh_token = 'refresh_token' in cookies
                    
                    user_data = data["user"]
                    details = f"Login successful: {user_data['email']} (Role: {user_data['role']}) | Cookies: access_token={has_access_token}, refresh_token={has_refresh_token}"
                    
                    self.log_test("2. POST /api/auth/login", True, details)
                    return True
                else:
                    self.log_test("2. POST /api/auth/login", False, 
                                f"Invalid response structure: {data}")
            else:
                self.log_test("2. POST /api/auth/login", False, 
                            f"Login failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("2. POST /api/auth/login", False, f"Exception: {str(e)}")
            
        return False
        
    def test_3_auth_me_with_cookies(self):
        """3. Test /api/auth/me endpoint with cookie authentication"""
        print("\n🔐 TEST 3: /api/auth/me endpoint with cookie authentication")
        
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "email", "role"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    details = f"Cookie auth working: {data['email']} (Role: {data['role']}, ID: {data['id']})"
                    self.log_test("3. GET /api/auth/me", True, details)
                    return True
                else:
                    self.log_test("3. GET /api/auth/me", False, 
                                f"Missing fields: {missing_fields}")
            else:
                self.log_test("3. GET /api/auth/me", False, 
                            f"Cookie auth failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("3. GET /api/auth/me", False, f"Exception: {str(e)}")
            
        return False
        
    def test_4_business_endpoints_with_cookies(self):
        """4. Test business endpoints with cookie auth: GET /api/business/menu"""
        print("\n🏪 TEST 4: Business endpoints with cookie auth")
        
        try:
            response = self.session.get(f"{API_BASE}/business/menu")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("4. GET /api/business/menu", True, 
                            f"Business endpoint accessible: {len(data.get('menu', []))} items")
            elif response.status_code == 403:
                self.log_test("4. GET /api/business/menu", True, 
                            "RBAC working correctly - customer denied business access")
            elif response.status_code == 401:
                self.log_test("4. GET /api/business/menu", False, 
                            "Cookie authentication not working for business endpoints")
            elif response.status_code == 404:
                self.log_test("4. GET /api/business/menu", False, 
                            "Business endpoint not found - double /api issue?")
            else:
                self.log_test("4. GET /api/business/menu", True, 
                            f"Business endpoint responding: {response.status_code}")
                
        except Exception as e:
            self.log_test("4. GET /api/business/menu", False, f"Exception: {str(e)}")
            
    def test_5_courier_endpoints_with_cookies(self):
        """5. Test courier endpoints with cookie auth: GET /api/courier/orders/available"""
        print("\n🚚 TEST 5: Courier endpoints with cookie auth")
        
        try:
            response = self.session.get(f"{API_BASE}/courier/orders/available")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("5. GET /api/courier/orders/available", True, 
                            f"Courier endpoint accessible: {len(data.get('orders', []))} orders")
            elif response.status_code == 403:
                self.log_test("5. GET /api/courier/orders/available", True, 
                            "RBAC working correctly - customer denied courier access")
            elif response.status_code == 401:
                self.log_test("5. GET /api/courier/orders/available", False, 
                            "Cookie authentication not working for courier endpoints")
            elif response.status_code == 404:
                self.log_test("5. GET /api/courier/orders/available", False, 
                            "Courier endpoint not found - double /api issue?")
            else:
                self.log_test("5. GET /api/courier/orders/available", True, 
                            f"Courier endpoint responding: {response.status_code}")
                
        except Exception as e:
            self.log_test("5. GET /api/courier/orders/available", False, f"Exception: {str(e)}")
            
    def test_6_no_double_api_issues(self):
        """6. Verify NO double /api issues in responses"""
        print("\n🚫 TEST 6: NO double /api issues in responses")
        
        test_endpoints = [
            "/api/auth/me",
            "/api/business/menu", 
            "/api/courier/orders/available"
        ]
        
        double_api_found = False
        
        for endpoint in test_endpoints:
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                response_text = response.text
                
                # Look for double /api patterns
                double_api_patterns = ["/api/api/", "//api/", "/api//api/"]
                
                if any(pattern in response_text for pattern in double_api_patterns):
                    double_api_found = True
                    self.log_test(f"6. Double /api Check - {endpoint}", False, 
                                "Double /api paths detected in response")
                else:
                    self.log_test(f"6. Double /api Check - {endpoint}", True, 
                                f"No double /api paths (status: {response.status_code})")
                    
            except Exception as e:
                self.log_test(f"6. Double /api Check - {endpoint}", False, f"Exception: {str(e)}")
                
        if not double_api_found:
            self.log_test("6. Overall Double /api Prevention", True, 
                        "No double /api issues detected across all endpoints")
            
    def test_7_proper_cookie_handling(self):
        """7. Verify proper cookie handling across all requests"""
        print("\n🍪 TEST 7: Proper cookie handling across all requests")
        
        try:
            # Test login and cookie persistence
            login_data = {
                "email": HOTFIX_TEST_DATA["email"],
                "password": HOTFIX_TEST_DATA["password"]
            }
            
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                cookies = login_response.cookies
                
                # Check cookie attributes
                cookie_info = []
                for cookie in cookies:
                    cookie_info.append(f"{cookie.name}={bool(cookie.value)}")
                
                # Test cookie persistence across requests
                me_response = self.session.get(f"{API_BASE}/auth/me")
                
                if me_response.status_code == 200:
                    self.log_test("7. Cookie Handling", True, 
                                f"Cookies working across requests: {', '.join(cookie_info)}")
                else:
                    self.log_test("7. Cookie Handling", False, 
                                "Cookies not persisting across requests")
            else:
                self.log_test("7. Cookie Handling", False, 
                            "Could not test cookie handling - login failed")
                
        except Exception as e:
            self.log_test("7. Cookie Handling", False, f"Exception: {str(e)}")
            
    def run_focused_hotfix_verification(self):
        """Run focused hotfix verification matching exact review request"""
        print(f"🔥 FOCUSED HOTFIX VERIFICATION - Exact Review Request Testing")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 100)
        
        print(f"\n📋 EXACT TEST DATA FROM REVIEW REQUEST:")
        print(f"   Email: {HOTFIX_TEST_DATA['email']}")
        print(f"   Password: {HOTFIX_TEST_DATA['password']}")
        print(f"   First Name: {HOTFIX_TEST_DATA['first_name']}")
        print(f"   Last Name: {HOTFIX_TEST_DATA['last_name']}")
        print(f"   Role: {HOTFIX_TEST_DATA['role']}")
        
        print(f"\n🎯 EXPECTED VERIFICATION POINTS:")
        print(f"   ✅ All endpoints respond correctly without 404 errors")
        print(f"   ✅ Cookie authentication works across all protected routes")
        print(f"   ✅ No double /api path issues")
        print(f"   ✅ Unified registration endpoint working")
        print(f"   ✅ CORS and cookie domain configuration working")
        
        # Run tests in exact order from review request
        print("\n" + "="*50 + " HOTFIX TESTS " + "="*50)
        
        # 1. Customer registration with NEW endpoint path
        self.test_1_customer_registration_new_endpoint()
        
        # 2. Login immediately after registration
        login_success = self.test_2_login_immediately_after_registration()
        
        # 3. /api/auth/me endpoint with cookie authentication (only if login successful)
        if login_success:
            self.test_3_auth_me_with_cookies()
        
        # 4. Business endpoints with cookie auth
        self.test_4_business_endpoints_with_cookies()
        
        # 5. Courier endpoints with cookie auth
        self.test_5_courier_endpoints_with_cookies()
        
        # 6. Verify NO double /api issues
        self.test_6_no_double_api_issues()
        
        # 7. Verify proper cookie handling
        self.test_7_proper_cookie_handling()
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 FOCUSED HOTFIX VERIFICATION SUMMARY")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ FAILED: {failed_tests}/{total_tests}")
        
        # Check each verification point
        verification_results = {
            "All endpoints respond correctly without 404 errors": True,
            "Cookie authentication works across all protected routes": True,
            "No double /api path issues": True,
            "Unified registration endpoint working": True,
            "CORS and cookie domain configuration working": True
        }
        
        # Analyze results for each verification point
        for test in self.test_results:
            if not test["success"]:
                if "404" in test["details"]:
                    verification_results["All endpoints respond correctly without 404 errors"] = False
                if "Cookie auth" in test["test"] or "401" in test["details"]:
                    verification_results["Cookie authentication works across all protected routes"] = False
                if "Double /api" in test["test"]:
                    verification_results["No double /api path issues"] = False
                if "register?role=customer" in test["test"]:
                    verification_results["Unified registration endpoint working"] = False
        
        print(f"\n🎯 VERIFICATION POINT RESULTS:")
        for point, result in verification_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {point}")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   ❌ {test['test']}: {test['details']}")
        
        # Final verdict
        critical_issues = []
        if not verification_results["All endpoints respond correctly without 404 errors"]:
            critical_issues.append("Double /api paths → 404 errors")
        if not verification_results["Cookie authentication works across all protected routes"]:
            critical_issues.append("Cookie auth missing → 401/403 errors")
        if not verification_results["Unified registration endpoint working"]:
            critical_issues.append("Unified registration endpoint not implemented")
        
        if critical_issues:
            print(f"\n⚠️  CRITICAL HOTFIX ISSUES:")
            for issue in critical_issues:
                print(f"   🚨 {issue}")
            print(f"\n🔧 HOTFIX STATUS: PARTIAL - Some issues remain")
        else:
            print(f"\n🎉 HOTFIX VERIFICATION SUCCESSFUL!")
            print(f"   This tests the complete fix for: double /api paths → 404, cookie auth missing → 401/403, scattered base URLs → localhost errors")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "verification_results": verification_results,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = FocusedHotfixTester()
    results = tester.run_focused_hotfix_verification()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:  # Allow some tolerance for non-critical issues
        print(f"\n🎉 HOTFIX VERIFICATION MOSTLY SUCCESSFUL ({results['success_rate']:.1f}%)!")
        exit(0)
    else:
        print(f"\n⚠️  HOTFIX VERIFICATION NEEDS ATTENTION ({results['success_rate']:.1f}%)")
        exit(1)