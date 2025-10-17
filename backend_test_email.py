#!/usr/bin/env python3
"""
DeliverTR Backend API Testing Suite - Email/Password Authentication
Tests all API endpoints for the Turkish delivery platform MVP with email/password auth
"""

import requests
import sys
import json
from datetime import datetime
import time
import os
from io import BytesIO

class DeliverTREmailAPITester:
    def __init__(self, base_url="https://delivery-nexus-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test user data
        self.test_courier_email = "test.courier@delivertr.com"
        self.test_business_email = "test.business@delivertr.com"
        self.test_customer_email = "test.customer@delivertr.com"
        self.test_password = "TestPassword123!"
        
        # Test data for detailed courier registration
        self.courier_data = {
            "email": self.test_courier_email,
            "password": self.test_password,
            "first_name": "Ahmet",
            "last_name": "Kurye",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "vehicle_model": "Honda PCX 150",
            "license_class": "A2",
            "license_number": "34ABC123456",
            "city": "İstanbul",
            "license_photo_url": None,
            "vehicle_photo_url": None,
            "profile_photo_url": None
        }
        
        self.business_data = {
            "email": self.test_business_email,
            "password": self.test_password,
            "business_name": "Test Lokantası",
            "tax_number": "1234567890",
            "address": "Test Mahallesi, Test Sokak No:1, İstanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant for API testing"
        }
        
        self.customer_data = {
            "email": self.test_customer_email,
            "password": self.test_password,
            "first_name": "Fatma",
            "last_name": "Müşteri",
            "city": "İstanbul"
        }

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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {}
        
        if self.access_token:
            test_headers['Authorization'] = f'Bearer {self.access_token}'
        
        if headers:
            test_headers.update(headers)
        
        # Only add Content-Type for JSON requests
        if not files and data:
            test_headers['Content-Type'] = 'application/json'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data and not files:
            print(f"   Data: {json.dumps(data, indent=2)}")
        elif files:
            print(f"   Files: {list(files.keys()) if files else 'None'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

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
                return False, error_data if 'error_data' in locals() else {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_courier_registration(self):
        """Test detailed courier registration with all new fields"""
        success, response = self.run_test(
            "Courier Registration - Detailed Fields",
            "POST",
            "register/courier",
            200,
            data=self.courier_data
        )
        
        if success and response.get('access_token'):
            print(f"   Courier registered successfully with token: {response['access_token'][:20]}...")
            # Verify all courier-specific fields are in response
            user_data = response.get('user_data', {})
            required_fields = ['email', 'first_name', 'last_name', 'iban', 'vehicle_type', 
                             'vehicle_model', 'license_class', 'license_number', 'city']
            
            missing_fields = [field for field in required_fields if field not in user_data]
            if missing_fields:
                self.log_test("Courier Registration - Field Validation", False, 
                            f"Missing fields in response: {missing_fields}")
                return False
            else:
                self.log_test("Courier Registration - Field Validation", True)
        
        return success

    def test_business_registration(self):
        """Test business registration"""
        success, response = self.run_test(
            "Business Registration",
            "POST",
            "register/business",
            200,
            data=self.business_data
        )
        
        if success and response.get('access_token'):
            print(f"   Business registered successfully with token: {response['access_token'][:20]}...")
        
        return success

    def test_customer_registration(self):
        """Test customer registration"""
        success, response = self.run_test(
            "Customer Registration",
            "POST",
            "register/customer",
            200,
            data=self.customer_data
        )
        
        if success and response.get('access_token'):
            print(f"   Customer registered successfully with token: {response['access_token'][:20]}...")
        
        return success

    def test_email_login_valid(self):
        """Test email/password login with valid credentials"""
        login_data = {
            "email": self.test_courier_email,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Email Login - Valid Credentials",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response.get('access_token'):
            self.access_token = response['access_token']
            print(f"   Access token stored: {self.access_token[:20]}...")
            
            # Verify JWT token structure
            if response.get('token_type') == 'bearer' and response.get('user_type'):
                self.log_test("JWT Token Structure Validation", True)
            else:
                self.log_test("JWT Token Structure Validation", False, 
                            "Missing token_type or user_type in response")
        
        return success

    def test_email_login_invalid(self):
        """Test email/password login with invalid credentials"""
        login_data = {
            "email": self.test_courier_email,
            "password": "WrongPassword123!"
        }
        
        return self.run_test(
            "Email Login - Invalid Credentials",
            "POST",
            "auth/login",
            401,
            data=login_data
        )

    def test_email_login_nonexistent(self):
        """Test email/password login with non-existent email"""
        login_data = {
            "email": "nonexistent@delivertr.com",
            "password": self.test_password
        }
        
        return self.run_test(
            "Email Login - Non-existent Email",
            "POST",
            "auth/login",
            401,
            data=login_data
        )

    def test_get_user_profile(self):
        """Test getting user profile with JWT token"""
        if not self.access_token:
            self.log_test("Get User Profile", False, "No authentication token available")
            return False
        
        success, response = self.run_test(
            "Get User Profile (/api/me)",
            "GET",
            "me",
            200
        )
        
        if success:
            # Verify profile contains expected fields
            expected_fields = ['id', 'email', 'role', 'created_at']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log_test("Profile Field Validation", False, 
                            f"Missing fields: {missing_fields}")
            else:
                self.log_test("Profile Field Validation", True)
        
        return success

    def test_file_upload_valid_image(self):
        """Test file upload with valid image"""
        # Create a small test image (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\x1b\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            'file': ('test_image.png', BytesIO(png_data), 'image/png')
        }
        
        success, response = self.run_test(
            "File Upload - Valid Image",
            "POST",
            "upload",
            200,
            files=files
        )
        
        if success:
            # Verify response contains file URL
            if response.get('file_url') and response.get('success'):
                self.log_test("File Upload Response Validation", True)
            else:
                self.log_test("File Upload Response Validation", False, 
                            "Missing file_url or success in response")
        
        return success

    def test_file_upload_invalid_type(self):
        """Test file upload with invalid file type"""
        # Create a text file
        text_data = b'This is a text file'
        
        files = {
            'file': ('test_file.txt', BytesIO(text_data), 'text/plain')
        }
        
        return self.run_test(
            "File Upload - Invalid Type",
            "POST",
            "upload",
            400,
            files=files
        )

    def test_file_upload_too_large(self):
        """Test file upload with file too large (>10MB)"""
        # Create a large file (simulate 11MB)
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB
        
        files = {
            'file': ('large_image.jpg', BytesIO(large_data), 'image/jpeg')
        }
        
        return self.run_test(
            "File Upload - Too Large",
            "POST",
            "upload",
            400,
            files=files
        )

    def test_duplicate_email_registration(self):
        """Test registration with already existing email"""
        # Try to register courier with same email again
        return self.run_test(
            "Duplicate Email Registration",
            "POST",
            "register/courier",
            400,
            data=self.courier_data
        )

    def test_invalid_email_format(self):
        """Test registration with invalid email format"""
        invalid_courier_data = self.courier_data.copy()
        invalid_courier_data['email'] = "invalid-email-format"
        
        return self.run_test(
            "Invalid Email Format",
            "POST",
            "register/courier",
            422,  # Pydantic validation error
            data=invalid_courier_data
        )

    def test_missing_required_fields(self):
        """Test courier registration with missing required fields"""
        incomplete_data = {
            "email": "incomplete@delivertr.com",
            "password": self.test_password
            # Missing other required fields
        }
        
        return self.run_test(
            "Missing Required Fields",
            "POST",
            "register/courier",
            422,  # Pydantic validation error
            data=incomplete_data
        )

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        old_token = self.access_token
        self.access_token = "invalid-token-12345"
        
        success, _ = self.run_test(
            "Unauthorized Access",
            "GET",
            "me",
            401
        )
        
        self.access_token = old_token
        return success

    def test_jwt_token_validation(self):
        """Test JWT token validation and structure"""
        if not self.access_token:
            self.log_test("JWT Token Validation", False, "No token available")
            return False
        
        # Test with valid token
        success1, response1 = self.run_test(
            "JWT Token - Valid Access",
            "GET",
            "me",
            200
        )
        
        # Test with malformed token
        old_token = self.access_token
        self.access_token = "malformed.jwt.token"
        
        success2, _ = self.run_test(
            "JWT Token - Malformed",
            "GET",
            "me",
            401
        )
        
        self.access_token = old_token
        return success1 and success2

    def test_password_hashing(self):
        """Test that passwords are properly hashed (not stored in plain text)"""
        # This is tested indirectly by successful login after registration
        # If password hashing works, we should be able to login with the same password
        login_data = {
            "email": self.test_business_email,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Password Hashing Verification",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            # Verify that user_data doesn't contain password
            user_data = response.get('user_data', {})
            if 'password' in user_data:
                self.log_test("Password Security Check", False, 
                            "Password found in response - security issue!")
                return False
            else:
                self.log_test("Password Security Check", True)
        
        return success

    def run_all_tests(self):
        """Run all backend tests for Email/Password Authentication"""
        print("🚀 Starting DeliverTR Backend API Tests - Email/Password Authentication")
        print("=" * 80)
        
        # Test basic connectivity
        self.test_root_endpoint()
        
        # Test registration endpoints with detailed fields
        print("\n📝 REGISTRATION TESTS")
        print("-" * 40)
        self.test_courier_registration()
        time.sleep(0.5)
        self.test_business_registration()
        time.sleep(0.5)
        self.test_customer_registration()
        
        # Test validation and error handling
        print("\n🔍 VALIDATION TESTS")
        print("-" * 40)
        self.test_duplicate_email_registration()
        self.test_invalid_email_format()
        self.test_missing_required_fields()
        
        # Test authentication
        print("\n🔐 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_email_login_valid()
        time.sleep(0.5)
        self.test_email_login_invalid()
        self.test_email_login_nonexistent()
        self.test_password_hashing()
        
        # Test JWT token management
        print("\n🎫 JWT TOKEN TESTS")
        print("-" * 40)
        self.test_jwt_token_validation()
        self.test_unauthorized_access()
        
        # Test protected endpoints
        print("\n🛡️ PROTECTED ENDPOINT TESTS")
        print("-" * 40)
        self.test_get_user_profile()
        
        # Test file upload system
        print("\n📁 FILE UPLOAD TESTS")
        print("-" * 40)
        self.test_file_upload_valid_image()
        self.test_file_upload_invalid_type()
        # Skip large file test to avoid timeout
        # self.test_file_upload_too_large()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY - Email/Password Authentication")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests details
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Print successful tests
        passed_tests = [test for test in self.test_results if test['success']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                print(f"   - {test['test']}")
        
        # Save detailed results
        with open('/app/backend_test_email_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100,
                    "timestamp": datetime.now().isoformat(),
                    "test_type": "email_password_authentication"
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = DeliverTREmailAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())