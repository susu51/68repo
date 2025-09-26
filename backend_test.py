#!/usr/bin/env python3
"""
DeliverTR Backend API Testing Suite - Phone/SMS OTP Authentication
Tests all API endpoints for the Turkish delivery platform MVP with new OTP system
"""

import requests
import sys
import json
from datetime import datetime
import time

class DeliverTRAPITester:
    def __init__(self, base_url="https://quick-courier-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.refresh_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_phone = "+905551234567"
        self.test_phone_business = "+905551234568"
        self.test_phone_customer = "+905551234569"
        self.test_results = []
        self.mock_otp = None

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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.access_token:
            test_headers['Authorization'] = f'Bearer {self.access_token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
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
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_send_verification_code(self):
        """Test SMS verification code sending"""
        success, response = self.run_test(
            "Send Verification Code",
            "POST",
            "auth/send-code",
            200,
            data={"phone": self.test_phone}
        )
        
        if success and 'verification_id' in response:
            self.verification_id = response['verification_id']
            print(f"   Verification ID stored: {self.verification_id}")
        
        return success

    def test_verify_code_new_user(self):
        """Test code verification for new user"""
        if not self.verification_id:
            self.log_test("Verify Code (New User)", False, "No verification ID available")
            return False
        
        # Use mock code "123456" - this should work with the mock system
        success, response = self.run_test(
            "Verify Code (New User)",
            "POST",
            "auth/verify-code",
            200,
            data={
                "phone": self.test_phone,
                "code": "123456",
                "verification_id": self.verification_id
            }
        )
        
        return success

    def test_courier_registration(self):
        """Test courier registration"""
        courier_data = {
            "phone": self.test_phone,
            "first_name": "Test",
            "last_name": "Kurye",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "license_class": "A2"
        }
        
        success, response = self.run_test(
            "Courier Registration",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token stored for courier: {self.token[:20]}...")
        
        return success

    def test_business_registration(self):
        """Test business registration"""
        # Use different phone for business
        business_phone = "+905551234568"
        
        # First send verification code for business
        self.run_test(
            "Send Code for Business",
            "POST",
            "auth/send-code",
            200,
            data={"phone": business_phone}
        )
        
        business_data = {
            "phone": business_phone,
            "business_name": "Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Mahallesi, Test Sokak No:1, İstanbul",
            "business_type": "restaurant"
        }
        
        success, response = self.run_test(
            "Business Registration",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        return success

    def test_customer_registration(self):
        """Test customer registration"""
        # Use different phone for customer
        customer_phone = "+905551234569"
        
        # First send verification code for customer
        self.run_test(
            "Send Code for Customer",
            "POST",
            "auth/send-code",
            200,
            data={"phone": customer_phone}
        )
        
        customer_data = {
            "phone": customer_phone,
            "first_name": "Test",
            "last_name": "Müşteri",
            "email": "test@example.com"
        }
        
        success, response = self.run_test(
            "Customer Registration",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        return success

    def test_get_profile(self):
        """Test getting user profile"""
        if not self.token:
            self.log_test("Get Profile", False, "No authentication token available")
            return False
        
        return self.run_test("Get Profile", "GET", "profile", 200)

    def test_admin_endpoints(self):
        """Test admin endpoints"""
        # Test getting pending couriers
        success1, response = self.run_test(
            "Get Pending Couriers",
            "GET",
            "admin/couriers/pending",
            200
        )
        
        # If there are pending couriers, test approval/rejection
        if success1 and isinstance(response, list) and len(response) > 0:
            courier_id = response[0].get('id')
            if courier_id:
                # Test courier approval
                success2 = self.run_test(
                    "Approve Courier",
                    "POST",
                    f"admin/courier/{courier_id}/approve",
                    200,
                    data={"notes": "Test approval"}
                )
                
                return success1 and success2
        
        return success1

    def test_invalid_endpoints(self):
        """Test invalid endpoints and error handling"""
        # Test invalid phone format
        success1, _ = self.run_test(
            "Invalid Phone Format",
            "POST",
            "auth/send-code",
            400,
            data={"phone": "invalid-phone"}
        )
        
        # Test invalid verification code
        success2, _ = self.run_test(
            "Invalid Verification Code",
            "POST",
            "auth/verify-code",
            400,
            data={
                "phone": self.test_phone,
                "code": "000000",
                "verification_id": "invalid-id"
            }
        )
        
        # Test unauthorized access
        old_token = self.token
        self.token = "invalid-token"
        success3, _ = self.run_test(
            "Unauthorized Access",
            "GET",
            "profile",
            401
        )
        self.token = old_token
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting DeliverTR Backend API Tests")
        print("=" * 50)
        
        # Test basic connectivity
        self.test_root_endpoint()
        
        # Test authentication flow
        self.test_send_verification_code()
        time.sleep(1)  # Brief pause between requests
        self.test_verify_code_new_user()
        
        # Test registration endpoints
        self.test_courier_registration()
        time.sleep(1)
        self.test_business_registration()
        time.sleep(1)
        self.test_customer_registration()
        
        # Test authenticated endpoints
        self.test_get_profile()
        
        # Test admin endpoints
        self.test_admin_endpoints()
        
        # Test error handling
        self.test_invalid_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = DeliverTRAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())