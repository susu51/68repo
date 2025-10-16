#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE CUSTOMER REGISTRATION & LOGIN VERIFICATION
Testing the complete authentication flow after password field mismatch fix
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://order-system-44.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveAuthTester:
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

    def test_fresh_registration_and_login(self):
        """Test with completely fresh email to verify registration → login flow"""
        print("\n🆕 TESTING FRESH REGISTRATION → LOGIN FLOW")
        
        # Use timestamp to ensure unique email
        timestamp = int(time.time())
        fresh_email = f"testfresh{timestamp}@kuryecini.com"
        
        # Step 1: Register new customer
        register_data = {
            "email": fresh_email,
            "password": "test123456",
            "first_name": "Fresh",
            "last_name": "Test User",
            "city": "İstanbul"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/register/customer", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                if data.get("access_token") and data.get("user_data"):
                    user_data = data["user_data"]
                    self.log_test("Fresh Registration", True, 
                                f"New customer registered: {user_data.get('email')} (ID: {user_data.get('id')})")
                    
                    # Step 2: Immediately test login with same credentials
                    login_data = {
                        "email": fresh_email,
                        "password": "test123456"
                    }
                    
                    # Clear session to simulate fresh login
                    self.session.cookies.clear()
                    
                    login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
                    
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        if login_result.get("success") and login_result.get("user"):
                            user_info = login_result["user"]
                            cookies = login_response.cookies
                            has_access_token = 'access_token' in cookies
                            has_refresh_token = 'refresh_token' in cookies
                            
                            self.log_test("Fresh Login After Registration", True, 
                                        f"Login successful: {user_info['email']} (Cookies: access={has_access_token}, refresh={has_refresh_token})")
                            
                            # Step 3: Test /me endpoint
                            me_response = self.session.get(f"{API_BASE}/auth/me")
                            if me_response.status_code == 200:
                                me_data = me_response.json()
                                self.log_test("Dashboard Access After Login", True, 
                                            f"User data retrieved: {me_data.get('email')} (Role: {me_data.get('role')})")
                            else:
                                self.log_test("Dashboard Access After Login", False, 
                                            f"/me endpoint failed: {me_response.status_code}")
                        else:
                            self.log_test("Fresh Login After Registration", False, 
                                        f"Login response invalid: {login_result}")
                    else:
                        login_error = login_response.json() if login_response.content else {}
                        self.log_test("Fresh Login After Registration", False, 
                                    f"Login failed with status {login_response.status_code}: {login_error}")
                else:
                    self.log_test("Fresh Registration", False, 
                                f"Registration response missing fields: {data}")
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Fresh Registration", False, 
                            f"Registration failed with status {response.status_code}: {error_data}")
                
        except Exception as e:
            self.log_test("Fresh Registration → Login Flow", False, f"Exception: {str(e)}")

    def test_existing_user_login(self):
        """Test login with existing user from review request"""
        print("\n👤 TESTING EXISTING USER LOGIN")
        
        login_data = {
            "email": "testfix@kuryecini.com",
            "password": "test123456"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("user"):
                    user_data = data["user"]
                    cookies = response.cookies
                    has_access_token = 'access_token' in cookies
                    has_refresh_token = 'refresh_token' in cookies
                    
                    self.log_test("Existing User Login", True, 
                                f"Login successful: {user_data['email']} (ID: {user_data['id']}, Cookies: access={has_access_token}, refresh={has_refresh_token})")
                else:
                    self.log_test("Existing User Login", False, 
                                f"Invalid login response: {data}")
            else:
                error_data = response.json() if response.content else {}
                self.log_test("Existing User Login", False, 
                            f"Login failed with status {response.status_code}: {error_data}")
                
        except Exception as e:
            self.log_test("Existing User Login", False, f"Exception: {str(e)}")

    def test_password_field_consistency(self):
        """Test that password field is consistently handled between registration and login"""
        print("\n🔐 TESTING PASSWORD FIELD CONSISTENCY")
        
        # Use another unique email for this test
        timestamp = int(time.time())
        test_email = f"passwordtest{timestamp}@kuryecini.com"
        test_password = "consistencytest123"
        
        # Step 1: Register with specific password
        register_data = {
            "email": test_email,
            "password": test_password,
            "first_name": "Password",
            "last_name": "Test",
            "city": "Ankara"
        }
        
        try:
            reg_response = self.session.post(f"{API_BASE}/register/customer", json=register_data)
            
            if reg_response.status_code == 201:
                # Step 2: Clear session and try login with exact same password
                self.session.cookies.clear()
                
                login_data = {
                    "email": test_email,
                    "password": test_password
                }
                
                login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    if login_result.get("success"):
                        self.log_test("Password Field Consistency", True, 
                                    "Password correctly stored and verified - no field mismatch")
                    else:
                        self.log_test("Password Field Consistency", False, 
                                    f"Login succeeded but response invalid: {login_result}")
                else:
                    login_error = login_response.json() if login_response.content else {}
                    self.log_test("Password Field Consistency", False, 
                                f"Password field mismatch detected - login failed: {login_error}")
            else:
                reg_error = reg_response.json() if reg_response.content else {}
                self.log_test("Password Field Consistency", False, 
                            f"Registration failed: {reg_error}")
                
        except Exception as e:
            self.log_test("Password Field Consistency", False, f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive authentication tests"""
        print(f"🚀 COMPREHENSIVE CUSTOMER AUTHENTICATION VERIFICATION")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print(f"📅 Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run comprehensive tests
        self.test_fresh_registration_and_login()
        self.test_existing_user_login()
        self.test_password_field_consistency()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE AUTHENTICATION VERIFICATION SUMMARY")
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
        
        # Final verdict
        if success_rate >= 100:
            print(f"\n🎉 PASSWORD FIELD MISMATCH ISSUE RESOLVED!")
            print(f"   ✅ Customer registration working correctly")
            print(f"   ✅ Customer login working correctly") 
            print(f"   ✅ Authentication chain working correctly")
            print(f"   ✅ Complete registration → login → dashboard flow working")
        elif success_rate >= 75:
            print(f"\n⚠️  MOSTLY WORKING - Minor issues detected")
        else:
            print(f"\n❌ CRITICAL ISSUES DETECTED - Password field mismatch may still exist")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = ComprehensiveAuthTester()
    results = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 100:
        exit(0)
    else:
        exit(1)