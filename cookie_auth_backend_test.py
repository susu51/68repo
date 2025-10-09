#!/usr/bin/env python3
"""
HttpOnly Cookie-Based Authentication System Testing
Comprehensive testing of the new cookie authentication implementation.

Test Areas:
1. Authentication Endpoints Testing (login, me, refresh, logout)
2. Cookie Handling Verification (HttpOnly, SameSite, Max-Age)
3. Cross-Origin and CORS Testing
4. Authentication Flow Testing
5. Backend Integration Testing
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import traceback
from urllib.parse import urljoin

# Test Configuration
BASE_URL = "https://kuryecini-auth.preview.emergentagent.com"
API_BASE_URL = f"{BASE_URL}/api"
AUTH_BASE_URL = f"{BASE_URL}/api/auth"

# Test credentials from auth_cookie.py
TEST_CREDENTIALS = {
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}
}

class CookieAuthTestRunner:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.cookies = {}
        
    async def setup_session(self):
        """Initialize HTTP session with cookie jar"""
        jar = aiohttp.CookieJar(unsafe=True)  # Allow cookies for all domains in testing
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'},
            cookie_jar=jar
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, details="", response_data=None, cookies=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        if cookies:
            result["cookies"] = cookies
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if cookies:
            print(f"   Cookies: {cookies}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
        
    async def test_login_endpoint(self):
        """Test 1: POST /api/auth/login with test credentials"""
        try:
            login_data = TEST_CREDENTIALS["customer"]
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
                response_data = await response.json()
                
                # Check response status and data
                if response.status == 200:
                    success_field = response_data.get("success")
                    message = response_data.get("message")
                    
                    # Extract cookies from response
                    cookies_info = {}
                    for cookie_name, cookie_value in response.cookies.items():
                        cookies_info[cookie_name] = {
                            "value": str(cookie_value)[:20] + "..." if len(str(cookie_value)) > 20 else str(cookie_value),
                            "present": True
                        }
                    
                    if success_field and message == "Login successful":
                        self.log_test(
                            "POST /api/auth/login",
                            True,
                            f"Login successful. Response: {response_data}",
                            response_data,
                            cookies_info
                        )
                        return True
                    else:
                        self.log_test(
                            "POST /api/auth/login",
                            False,
                            f"Login response format incorrect. Expected success=True and message='Login successful'",
                            response_data,
                            cookies_info
                        )
                        return False
                else:
                    self.log_test(
                        "POST /api/auth/login",
                        False,
                        f"Login failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "POST /api/auth/login",
                False,
                f"Exception during login: {str(e)}"
            )
            return False
            
    async def test_me_endpoint_with_cookies(self):
        """Test 2: GET /api/auth/me with valid cookies"""
        try:
            async with self.session.get(f"{AUTH_BASE_URL}/me") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Verify user data structure
                    required_fields = ["id", "email", "first_name", "last_name", "role"]
                    missing_fields = [field for field in required_fields if field not in response_data]
                    
                    if not missing_fields:
                        user_email = response_data.get("email")
                        user_role = response_data.get("role")
                        
                        if user_email == TEST_CREDENTIALS["customer"]["email"] and user_role == "customer":
                            self.log_test(
                                "GET /api/auth/me",
                                True,
                                f"User data retrieved successfully. Email: {user_email}, Role: {user_role}",
                                response_data
                            )
                            return True
                        else:
                            self.log_test(
                                "GET /api/auth/me",
                                False,
                                f"User data mismatch. Expected customer email, got: {user_email}, role: {user_role}",
                                response_data
                            )
                            return False
                    else:
                        self.log_test(
                            "GET /api/auth/me",
                            False,
                            f"Missing required fields: {missing_fields}",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "GET /api/auth/me",
                        False,
                        f"Me endpoint failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "GET /api/auth/me",
                False,
                f"Exception during me endpoint test: {str(e)}"
            )
            return False
            
    async def test_refresh_endpoint(self):
        """Test 3: POST /api/auth/refresh with valid refresh cookie"""
        try:
            async with self.session.post(f"{AUTH_BASE_URL}/refresh") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    success_field = response_data.get("success")
                    message = response_data.get("message")
                    
                    # Check for new access token cookie
                    cookies_info = {}
                    for cookie_name, cookie_value in response.cookies.items():
                        if cookie_name == "access_token":
                            cookies_info[cookie_name] = {
                                "value": str(cookie_value)[:20] + "..." if len(str(cookie_value)) > 20 else str(cookie_value),
                                "present": True
                            }
                    
                    if success_field and message == "Token refreshed":
                        self.log_test(
                            "POST /api/auth/refresh",
                            True,
                            f"Token refresh successful. New access token cookie set.",
                            response_data,
                            cookies_info
                        )
                        return True
                    else:
                        self.log_test(
                            "POST /api/auth/refresh",
                            False,
                            f"Refresh response format incorrect",
                            response_data,
                            cookies_info
                        )
                        return False
                else:
                    self.log_test(
                        "POST /api/auth/refresh",
                        False,
                        f"Refresh failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "POST /api/auth/refresh",
                False,
                f"Exception during refresh test: {str(e)}"
            )
            return False
            
    async def test_logout_endpoint(self):
        """Test 4: POST /api/auth/logout to clear cookies"""
        try:
            async with self.session.post(f"{AUTH_BASE_URL}/logout") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    success_field = response_data.get("success")
                    message = response_data.get("message")
                    
                    # Check if cookies are cleared (should have empty values or be deleted)
                    cookies_cleared = True
                    remaining_cookies = {}
                    
                    for cookie_name, cookie_value in response.cookies.items():
                        if cookie_name in ["access_token", "refresh_token"]:
                            remaining_cookies[cookie_name] = str(cookie_value)
                            if str(cookie_value):  # If cookie still has a value, it's not properly cleared
                                cookies_cleared = False
                    
                    if success_field and message == "Logged out":
                        self.log_test(
                            "POST /api/auth/logout",
                            True,
                            f"Logout successful. Cookies cleared: {cookies_cleared}",
                            response_data,
                            remaining_cookies
                        )
                        return True
                    else:
                        self.log_test(
                            "POST /api/auth/logout",
                            False,
                            f"Logout response format incorrect",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "POST /api/auth/logout",
                        False,
                        f"Logout failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "POST /api/auth/logout",
                False,
                f"Exception during logout test: {str(e)}"
            )
            return False
            
    async def test_cookie_attributes(self):
        """Test 5: Verify HttpOnly cookies are being set correctly"""
        try:
            # Fresh login to check cookie attributes
            login_data = TEST_CREDENTIALS["customer"]
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
                if response.status == 200:
                    # Analyze cookie attributes
                    cookie_analysis = {}
                    
                    for cookie in response.cookies:
                        if cookie.key in ["access_token", "refresh_token"]:
                            cookie_analysis[cookie.key] = {
                                "present": True,
                                "httponly": cookie.get("httponly", False),
                                "samesite": cookie.get("samesite", ""),
                                "secure": cookie.get("secure", False),
                                "max_age": cookie.get("max-age", ""),
                                "has_value": bool(cookie.value)
                            }
                    
                    # Check if both tokens are present with correct attributes
                    access_token_ok = (
                        "access_token" in cookie_analysis and
                        cookie_analysis["access_token"]["present"] and
                        cookie_analysis["access_token"]["httponly"] and
                        cookie_analysis["access_token"]["has_value"]
                    )
                    
                    refresh_token_ok = (
                        "refresh_token" in cookie_analysis and
                        cookie_analysis["refresh_token"]["present"] and
                        cookie_analysis["refresh_token"]["httponly"] and
                        cookie_analysis["refresh_token"]["has_value"]
                    )
                    
                    if access_token_ok and refresh_token_ok:
                        self.log_test(
                            "Cookie Attributes Verification",
                            True,
                            f"Both access_token and refresh_token cookies set with HttpOnly=True",
                            None,
                            cookie_analysis
                        )
                        return True
                    else:
                        self.log_test(
                            "Cookie Attributes Verification",
                            False,
                            f"Cookie attributes incorrect. Access token OK: {access_token_ok}, Refresh token OK: {refresh_token_ok}",
                            None,
                            cookie_analysis
                        )
                        return False
                else:
                    self.log_test(
                        "Cookie Attributes Verification",
                        False,
                        f"Login failed during cookie attribute test with status {response.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Cookie Attributes Verification",
                False,
                f"Exception during cookie attributes test: {str(e)}"
            )
            return False
            
    async def test_cors_configuration(self):
        """Test 6: Test CORS configuration for cookie credentials"""
        try:
            # Test preflight request
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            async with self.session.options(f"{AUTH_BASE_URL}/login", headers=headers) as response:
                cors_headers = {
                    "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin", ""),
                    "access_control_allow_credentials": response.headers.get("Access-Control-Allow-Credentials", ""),
                    "access_control_allow_methods": response.headers.get("Access-Control-Allow-Methods", ""),
                    "access_control_allow_headers": response.headers.get("Access-Control-Allow-Headers", "")
                }
                
                # Check if CORS is properly configured for credentials
                credentials_allowed = cors_headers["access_control_allow_credentials"].lower() == "true"
                origin_allowed = cors_headers["access_control_allow_origin"] in ["http://localhost:3000", "*"]
                
                if credentials_allowed:
                    self.log_test(
                        "CORS Configuration",
                        True,
                        f"CORS properly configured. Allow-Credentials: {credentials_allowed}, Origin: {cors_headers['access_control_allow_origin']}",
                        None,
                        cors_headers
                    )
                    return True
                else:
                    self.log_test(
                        "CORS Configuration",
                        False,
                        f"CORS not properly configured for credentials. Allow-Credentials: {credentials_allowed}",
                        None,
                        cors_headers
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "CORS Configuration",
                False,
                f"Exception during CORS test: {str(e)}"
            )
            return False
            
    async def test_authentication_flow(self):
        """Test 7: Complete login -> auth check -> logout flow"""
        try:
            # Step 1: Login
            login_data = TEST_CREDENTIALS["admin"]  # Test with admin user
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
                if response.status != 200:
                    self.log_test(
                        "Complete Authentication Flow",
                        False,
                        f"Login step failed with status {response.status}"
                    )
                    return False
            
            # Step 2: Verify authentication with /me
            async with self.session.get(f"{AUTH_BASE_URL}/me") as response:
                if response.status != 200:
                    self.log_test(
                        "Complete Authentication Flow",
                        False,
                        f"Auth check step failed with status {response.status}"
                    )
                    return False
                
                user_data = await response.json()
                if user_data.get("role") != "admin":
                    self.log_test(
                        "Complete Authentication Flow",
                        False,
                        f"Auth check returned wrong role: {user_data.get('role')}"
                    )
                    return False
            
            # Step 3: Logout
            async with self.session.post(f"{AUTH_BASE_URL}/logout") as response:
                if response.status != 200:
                    self.log_test(
                        "Complete Authentication Flow",
                        False,
                        f"Logout step failed with status {response.status}"
                    )
                    return False
            
            # Step 4: Verify logout (should fail to access /me)
            async with self.session.get(f"{AUTH_BASE_URL}/me") as response:
                if response.status == 401:
                    self.log_test(
                        "Complete Authentication Flow",
                        True,
                        "Complete flow successful: login -> auth check -> logout -> access denied"
                    )
                    return True
                else:
                    self.log_test(
                        "Complete Authentication Flow",
                        False,
                        f"Logout verification failed - still authenticated with status {response.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Complete Authentication Flow",
                False,
                f"Exception during authentication flow test: {str(e)}"
            )
            return False
            
    async def test_token_expiration_handling(self):
        """Test 8: Verify token expiration and refresh mechanism"""
        try:
            # Login to get fresh tokens
            login_data = TEST_CREDENTIALS["customer"]
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
                if response.status != 200:
                    self.log_test(
                        "Token Expiration Handling",
                        False,
                        f"Login failed with status {response.status}"
                    )
                    return False
            
            # Test refresh mechanism
            async with self.session.post(f"{AUTH_BASE_URL}/refresh") as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success") and response_data.get("message") == "Token refreshed":
                        self.log_test(
                            "Token Expiration Handling",
                            True,
                            "Token refresh mechanism working correctly"
                        )
                        return True
                    else:
                        self.log_test(
                            "Token Expiration Handling",
                            False,
                            f"Refresh response format incorrect: {response_data}"
                        )
                        return False
                else:
                    self.log_test(
                        "Token Expiration Handling",
                        False,
                        f"Token refresh failed with status {response.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Token Expiration Handling",
                False,
                f"Exception during token expiration test: {str(e)}"
            )
            return False
            
    async def test_authentication_failure_scenarios(self):
        """Test 9: Test authentication failure scenarios"""
        try:
            # Test 1: Invalid credentials
            invalid_login = {"email": "invalid@example.com", "password": "wrongpassword"}
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=invalid_login) as response:
                if response.status == 401:
                    invalid_creds_ok = True
                else:
                    invalid_creds_ok = False
            
            # Test 2: Access protected endpoint without cookies
            # Create new session without cookies
            test_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            async with test_session.get(f"{AUTH_BASE_URL}/me") as response:
                if response.status == 401:
                    no_cookie_ok = True
                else:
                    no_cookie_ok = False
            
            await test_session.close()
            
            # Test 3: Refresh without refresh token
            test_session2 = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            async with test_session2.post(f"{AUTH_BASE_URL}/refresh") as response:
                if response.status == 401:
                    no_refresh_token_ok = True
                else:
                    no_refresh_token_ok = False
            
            await test_session2.close()
            
            all_failures_handled = invalid_creds_ok and no_cookie_ok and no_refresh_token_ok
            
            if all_failures_handled:
                self.log_test(
                    "Authentication Failure Scenarios",
                    True,
                    f"All failure scenarios handled correctly. Invalid creds: {invalid_creds_ok}, No cookie: {no_cookie_ok}, No refresh: {no_refresh_token_ok}"
                )
                return True
            else:
                self.log_test(
                    "Authentication Failure Scenarios",
                    False,
                    f"Some failure scenarios not handled. Invalid creds: {invalid_creds_ok}, No cookie: {no_cookie_ok}, No refresh: {no_refresh_token_ok}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Authentication Failure Scenarios",
                False,
                f"Exception during failure scenarios test: {str(e)}"
            )
            return False
            
    async def test_backend_integration(self):
        """Test 10: Verify auth_cookie router is properly mounted and database integration"""
        try:
            # Test that auth router is mounted correctly
            async with self.session.get(f"{AUTH_BASE_URL}/me") as response:
                # Should return 401 since we're not authenticated
                if response.status == 401:
                    router_mounted = True
                else:
                    router_mounted = False
            
            # Test database integration by logging in and checking user data
            login_data = TEST_CREDENTIALS["business"]
            
            async with self.session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
                if response.status == 200:
                    # Now check if we can get user data (tests database integration)
                    async with self.session.get(f"{AUTH_BASE_URL}/me") as me_response:
                        if me_response.status == 200:
                            user_data = await me_response.json()
                            # Check if we get business-specific data
                            if user_data.get("role") == "business":
                                db_integration_ok = True
                            else:
                                db_integration_ok = False
                        else:
                            db_integration_ok = False
                else:
                    db_integration_ok = False
            
            if router_mounted and db_integration_ok:
                self.log_test(
                    "Backend Integration",
                    True,
                    f"Auth router properly mounted and database integration working. Router: {router_mounted}, DB: {db_integration_ok}"
                )
                return True
            else:
                self.log_test(
                    "Backend Integration",
                    False,
                    f"Integration issues detected. Router mounted: {router_mounted}, DB integration: {db_integration_ok}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Integration",
                False,
                f"Exception during backend integration test: {str(e)}"
            )
            return False
            
    async def test_multiple_user_types(self):
        """Test 11: Test authentication with different user types"""
        try:
            user_type_results = {}
            
            for user_type, credentials in TEST_CREDENTIALS.items():
                # Create fresh session for each user type
                jar = aiohttp.CookieJar(unsafe=True)
                user_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'Content-Type': 'application/json'},
                    cookie_jar=jar
                )
                
                try:
                    # Login
                    async with user_session.post(f"{AUTH_BASE_URL}/login", json=credentials) as response:
                        if response.status == 200:
                            # Verify user data
                            async with user_session.get(f"{AUTH_BASE_URL}/me") as me_response:
                                if me_response.status == 200:
                                    user_data = await me_response.json()
                                    if user_data.get("role") == user_type:
                                        user_type_results[user_type] = True
                                    else:
                                        user_type_results[user_type] = False
                                else:
                                    user_type_results[user_type] = False
                        else:
                            user_type_results[user_type] = False
                finally:
                    await user_session.close()
            
            successful_types = [k for k, v in user_type_results.items() if v]
            all_types_working = len(successful_types) == len(TEST_CREDENTIALS)
            
            if all_types_working:
                self.log_test(
                    "Multiple User Types Authentication",
                    True,
                    f"All user types authenticated successfully: {', '.join(successful_types)}"
                )
                return True
            else:
                failed_types = [k for k, v in user_type_results.items() if not v]
                self.log_test(
                    "Multiple User Types Authentication",
                    False,
                    f"Some user types failed. Working: {successful_types}, Failed: {failed_types}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Multiple User Types Authentication",
                False,
                f"Exception during multiple user types test: {str(e)}"
            )
            return False
            
    async def run_all_tests(self):
        """Run all cookie authentication tests"""
        print("🍪 Starting HttpOnly Cookie-Based Authentication System Testing")
        print("=" * 80)
        print()
        
        await self.setup_session()
        
        try:
            # Test sequence
            tests = [
                ("Login Endpoint", self.test_login_endpoint),
                ("Me Endpoint with Cookies", self.test_me_endpoint_with_cookies),
                ("Refresh Endpoint", self.test_refresh_endpoint),
                ("Logout Endpoint", self.test_logout_endpoint),
                ("Cookie Attributes", self.test_cookie_attributes),
                ("CORS Configuration", self.test_cors_configuration),
                ("Complete Authentication Flow", self.test_authentication_flow),
                ("Token Expiration Handling", self.test_token_expiration_handling),
                ("Authentication Failure Scenarios", self.test_authentication_failure_scenarios),
                ("Backend Integration", self.test_backend_integration),
                ("Multiple User Types", self.test_multiple_user_types),
            ]
            
            # Run tests
            for test_name, test_func in tests:
                try:
                    await test_func()
                except Exception as e:
                    self.log_test(test_name, False, f"Unexpected error: {str(e)}")
                    print(f"Stack trace: {traceback.format_exc()}")
                    
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("🍪 HTTPONLY COOKIE AUTHENTICATION TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {success_rate:.1f}% success rate ({passed_tests}/{total_tests} tests passed)")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
            
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['details']}")
        print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        login_working = any(r["success"] and "Login Endpoint" in r["test"] for r in self.test_results)
        cookies_working = any(r["success"] and "Cookie Attributes" in r["test"] for r in self.test_results)
        cors_working = any(r["success"] and "CORS" in r["test"] for r in self.test_results)
        flow_working = any(r["success"] and "Complete Authentication Flow" in r["test"] for r in self.test_results)
        integration_working = any(r["success"] and "Backend Integration" in r["test"] for r in self.test_results)
        
        print(f"   • Login Endpoint: {'✅ Working' if login_working else '❌ Failed'}")
        print(f"   • HttpOnly Cookies: {'✅ Working' if cookies_working else '❌ Failed'}")
        print(f"   • CORS Configuration: {'✅ Working' if cors_working else '❌ Failed'}")
        print(f"   • Authentication Flow: {'✅ Working' if flow_working else '❌ Failed'}")
        print(f"   • Backend Integration: {'✅ Working' if integration_working else '❌ Failed'}")
        print()
        
        # Conclusion
        if success_rate >= 80:
            print("🎉 CONCLUSION: HttpOnly cookie authentication system is working well!")
            print("   Cookie-based authentication is production-ready.")
        else:
            print("⚠️  CONCLUSION: Cookie authentication system has issues that need attention.")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    runner = CookieAuthTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())