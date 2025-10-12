#!/usr/bin/env python3
"""
🔍 CUSTOMER REGISTRATION FUNCTIONALITY TESTING
Testing customer registration endpoint and authentication flow as requested
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://stable-menus.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test data from review request
TEST_CUSTOMER_DATA = {
    "email": "testcustomer@kuryecini.com",
    "password": "test123456", 
    "first_name": "Test",
    "last_name": "Customer",
    "city": "İstanbul"
}

# Alternative test data with unique email for testing
import uuid
UNIQUE_EMAIL = f"testcustomer{str(uuid.uuid4())[:8]}@kuryecini.com"
TEST_CUSTOMER_DATA_UNIQUE = {
    "email": UNIQUE_EMAIL,
    "password": "test123456", 
    "first_name": "Test",
    "last_name": "Customer",
    "city": "İstanbul"
}

class CustomerRegistrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.cookies = {}
        self.registered_user_id = None
        
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
        """Test POST /api/register/customer endpoint"""
        print("\n🔐 TESTING CUSTOMER REGISTRATION")
        
        # Use unique email to avoid conflicts
        test_data = TEST_CUSTOMER_DATA_UNIQUE.copy()
        print(f"   Using unique email: {test_data['email']}")
        
        try:
            # Test customer registration
            response = self.session.post(
                f"{API_BASE}/register/customer",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Registration Response Status: {response.status_code}")
            print(f"Registration Response Headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"Registration Response Data: {json.dumps(data, indent=2)}")
                
                # Check response structure
                if "access_token" in data and "user_data" in data:
                    user_data = data["user_data"]
                    self.registered_user_id = user_data.get("id")
                    
                    # Verify user data fields
                    expected_fields = ["id", "email", "first_name", "last_name", "city", "role"]
                    missing_fields = [field for field in expected_fields if field not in user_data]
                    
                    if not missing_fields:
                        self.log_test(
                            "Customer Registration", 
                            True, 
                            f"User registered successfully with ID: {self.registered_user_id}, Email: {user_data.get('email')}, Role: {user_data.get('role')}"
                        )
                        
                        # Verify specific field values
                        if (user_data.get("email") == TEST_CUSTOMER_DATA["email"] and
                            user_data.get("first_name") == TEST_CUSTOMER_DATA["first_name"] and
                            user_data.get("last_name") == TEST_CUSTOMER_DATA["last_name"] and
                            user_data.get("city") == TEST_CUSTOMER_DATA["city"] and
                            user_data.get("role") == "customer"):
                            
                            self.log_test(
                                "Registration Data Validation", 
                                True, 
                                "All registration fields saved correctly"
                            )
                        else:
                            self.log_test(
                                "Registration Data Validation", 
                                False, 
                                f"Field mismatch - Expected: {TEST_CUSTOMER_DATA}, Got: {user_data}"
                            )
                    else:
                        self.log_test(
                            "Customer Registration", 
                            False, 
                            f"Missing required fields in response: {missing_fields}",
                            data
                        )
                else:
                    self.log_test(
                        "Customer Registration", 
                        False, 
                        "Missing access_token or user_data in response",
                        data
                    )
            elif response.status_code == 400:
                # Check if user already exists
                try:
                    error_data = response.json()
                    if "already registered" in error_data.get("detail", "").lower():
                        print("   User already exists, proceeding with login test...")
                        self.log_test(
                            "Customer Registration", 
                            True, 
                            "User already exists (expected for repeat tests)"
                        )
                    else:
                        self.log_test(
                            "Customer Registration", 
                            False, 
                            f"Registration failed with error: {error_data.get('detail')}",
                            error_data
                        )
                except:
                    self.log_test(
                        "Customer Registration", 
                        False, 
                        f"Registration failed with status {response.status_code}",
                        response.text
                    )
            else:
                self.log_test(
                    "Customer Registration", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Customer Registration", 
                False, 
                f"Request failed: {str(e)}"
            )
    
    def test_customer_login(self):
        """Test POST /api/auth/login with registered customer credentials"""
        print("\n🔑 TESTING CUSTOMER LOGIN")
        
        try:
            login_data = {
                "email": TEST_CUSTOMER_DATA["email"],
                "password": TEST_CUSTOMER_DATA["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Login Response Status: {response.status_code}")
            print(f"Login Response Headers: {dict(response.headers)}")
            print(f"Login Response Cookies: {dict(response.cookies)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Login Response Data: {json.dumps(data, indent=2)}")
                    
                    # Check for success message
                    if data.get("success") == True:
                        # Store cookies for subsequent requests
                        self.cookies.update(dict(response.cookies))
                        
                        self.log_test(
                            "Customer Login", 
                            True, 
                            f"Login successful with message: {data.get('message', 'No message')}"
                        )
                        
                        # Verify cookies are set
                        if response.cookies:
                            cookie_names = list(response.cookies.keys())
                            self.log_test(
                                "Cookie Authentication", 
                                True, 
                                f"Cookies set successfully: {cookie_names}"
                            )
                        else:
                            self.log_test(
                                "Cookie Authentication", 
                                False, 
                                "No cookies set in login response"
                            )
                    else:
                        self.log_test(
                            "Customer Login", 
                            False, 
                            f"Login response missing success flag or false",
                            data
                        )
                except json.JSONDecodeError:
                    self.log_test(
                        "Customer Login", 
                        False, 
                        "Invalid JSON response",
                        response.text
                    )
            else:
                try:
                    error_data = response.json()
                    self.log_test(
                        "Customer Login", 
                        False, 
                        f"Login failed: {error_data.get('detail', 'Unknown error')}",
                        error_data
                    )
                except:
                    self.log_test(
                        "Customer Login", 
                        False, 
                        f"Login failed with status {response.status_code}",
                        response.text
                    )
                    
        except Exception as e:
            self.log_test(
                "Customer Login", 
                False, 
                f"Login request failed: {str(e)}"
            )
    
    def test_authenticated_user_info(self):
        """Test GET /api/auth/me with authentication cookies"""
        print("\n👤 TESTING AUTHENTICATED USER INFO")
        
        try:
            # Use cookies from login
            response = self.session.get(
                f"{API_BASE}/auth/me",
                cookies=self.cookies
            )
            
            print(f"User Info Response Status: {response.status_code}")
            print(f"User Info Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"User Info Response Data: {json.dumps(data, indent=2)}")
                    
                    # Verify user data matches registration
                    if (data.get("email") == TEST_CUSTOMER_DATA["email"] and
                        data.get("role") == "customer" and
                        data.get("first_name") == TEST_CUSTOMER_DATA["first_name"] and
                        data.get("last_name") == TEST_CUSTOMER_DATA["last_name"]):
                        
                        self.log_test(
                            "Authenticated User Info", 
                            True, 
                            f"User info retrieved successfully - ID: {data.get('id')}, Email: {data.get('email')}, Role: {data.get('role')}"
                        )
                    else:
                        self.log_test(
                            "Authenticated User Info", 
                            False, 
                            f"User data mismatch - Expected customer data, got: {data}"
                        )
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Authenticated User Info", 
                        False, 
                        "Invalid JSON response",
                        response.text
                    )
            elif response.status_code == 401:
                self.log_test(
                    "Authenticated User Info", 
                    False, 
                    "Authentication failed - cookies not working",
                    response.text
                )
            else:
                self.log_test(
                    "Authenticated User Info", 
                    False, 
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Authenticated User Info", 
                False, 
                f"Request failed: {str(e)}"
            )
    
    def test_registration_flow_complete(self):
        """Test complete registration and authentication flow"""
        print("\n🔄 TESTING COMPLETE REGISTRATION FLOW")
        
        # Run all tests in sequence
        self.test_customer_registration()
        time.sleep(1)  # Brief pause between tests
        
        self.test_customer_login()
        time.sleep(1)
        
        self.test_authenticated_user_info()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 CUSTOMER REGISTRATION TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 100:
            print("   ✅ Customer registration functionality is working perfectly!")
        elif success_rate >= 75:
            print("   ⚠️  Customer registration mostly working with minor issues")
        else:
            print("   ❌ Customer registration has significant issues requiring fixes")
        
        return success_rate, passed_tests, total_tests

def main():
    """Main test execution"""
    print("🚀 STARTING CUSTOMER REGISTRATION TESTING")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📧 Test Email: {TEST_CUSTOMER_DATA['email']}")
    print(f"🏙️  Test City: {TEST_CUSTOMER_DATA['city']}")
    
    tester = CustomerRegistrationTester()
    tester.test_registration_flow_complete()
    success_rate, passed, total = tester.print_summary()
    
    # Return exit code based on results
    return 0 if success_rate >= 75 else 1

if __name__ == "__main__":
    exit(main())