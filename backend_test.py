#!/usr/bin/env python3
"""
DeliverTR Backend API Testing Suite - Core Business Flow
Tests all API endpoints for the Turkish delivery platform MVP core business flow:
- Product Management (Business creates products with photos)
- Order Creation (Customer creates orders with multiple items)
- Order Status Management (CREATED→ASSIGNED→ON_ROUTE→DELIVERED)
- Admin Authentication (password "6851")
- Admin Management (users, products, orders)
- Commission Calculation (3%)
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class DeliverTRAPITester:
    def __init__(self, base_url="https://quick-courier-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.admin_token = None
        self.business_token = None
        self.customer_token = None
        self.courier_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.business_email = f"business_{uuid.uuid4().hex[:8]}@test.com"
        self.customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"
        self.courier_email = f"courier_{uuid.uuid4().hex[:8]}@test.com"
        self.test_password = "TestPass123!"
        
        # Store created entities for testing
        self.created_products = []
        self.created_orders = []
        self.business_id = None
        self.customer_id = None
        self.courier_id = None

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

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_otp_request_valid_phone(self):
        """Test OTP request with valid Turkish phone number"""
        success, response = self.run_test(
            "OTP Request - Valid Phone",
            "POST",
            "auth/otp/request",
            200,
            data={
                "phone": self.test_phone,
                "device_id": "test_device_123"
            }
        )
        
        if success and response.get('success'):
            self.mock_otp = response.get('mock_otp')
            print(f"   Mock OTP received: {self.mock_otp}")
        
        return success

    def test_otp_request_invalid_phone(self):
        """Test OTP request with invalid phone format"""
        return self.run_test(
            "OTP Request - Invalid Phone",
            "POST",
            "auth/otp/request",
            400,
            data={
                "phone": "invalid-phone-123",
                "device_id": "test_device_123"
            }
        )

    def test_otp_verify_correct_code(self):
        """Test OTP verification with correct code"""
        if not self.mock_otp:
            # Try to get mock OTP from debug endpoint
            success, response = self.run_test(
                "Get Mock OTP",
                "GET",
                f"debug/mock-otp/{self.test_phone.replace('+', '')}",
                200
            )
            if success and response.get('mock_otp'):
                self.mock_otp = response.get('mock_otp')
        
        if not self.mock_otp:
            self.log_test("OTP Verify - Correct Code", False, "No mock OTP available")
            return False
        
        success, response = self.run_test(
            "OTP Verify - Correct Code",
            "POST",
            "auth/otp/verify",
            200,
            data={
                "phone": self.test_phone,
                "otp": self.mock_otp
            }
        )
        
        if success and response.get('access_token'):
            self.access_token = response['access_token']
            self.refresh_token = response['refresh_token']
            print(f"   Access token stored: {self.access_token[:20]}...")
            print(f"   Refresh token stored: {self.refresh_token[:20]}...")
        
        return success

    def test_otp_verify_incorrect_code(self):
        """Test OTP verification with incorrect code"""
        return self.run_test(
            "OTP Verify - Incorrect Code",
            "POST",
            "auth/otp/verify",
            400,
            data={
                "phone": self.test_phone,
                "otp": "000000"
            }
        )

    def test_token_refresh(self):
        """Test JWT token refresh"""
        if not self.refresh_token:
            self.log_test("Token Refresh", False, "No refresh token available")
            return False
        
        success, response = self.run_test(
            "Token Refresh",
            "POST",
            "auth/refresh",
            200,
            data={
                "refresh_token": self.refresh_token
            }
        )
        
        if success and response.get('access_token'):
            old_token = self.access_token
            self.access_token = response['access_token']
            print(f"   Token refreshed: {old_token[:20]}... -> {self.access_token[:20]}...")
        
        return success

    def test_get_profile(self):
        """Test getting user profile"""
        if not self.access_token:
            self.log_test("Get Profile", False, "No authentication token available")
            return False
        
        return self.run_test("Get Profile", "GET", "me", 200)

    def test_update_profile(self):
        """Test updating user profile"""
        if not self.access_token:
            self.log_test("Update Profile", False, "No authentication token available")
            return False
        
        return self.run_test(
            "Update Profile",
            "PATCH",
            "me",
            200,
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            }
        )

    def test_courier_registration(self):
        """Test courier registration after phone verification"""
        if not self.access_token:
            self.log_test("Courier Registration", False, "No authentication token available")
            return False
        
        courier_data = {
            "phone": self.test_phone,
            "first_name": "Test",
            "last_name": "Kurye",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "vehicle_model": "Honda PCX 150",
            "license_class": "A2",
            "city": "İstanbul"
        }
        
        return self.run_test(
            "Courier Registration",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )

    def test_business_registration_flow(self):
        """Test complete business registration flow"""
        # First request OTP for business phone
        success1, response1 = self.run_test(
            "Business OTP Request",
            "POST",
            "auth/otp/request",
            200,
            data={
                "phone": self.test_phone_business,
                "device_id": "business_device_123"
            }
        )
        
        if not success1:
            return False
        
        # Get mock OTP for business
        business_mock_otp = response1.get('mock_otp')
        if not business_mock_otp:
            success_debug, response_debug = self.run_test(
                "Get Business Mock OTP",
                "GET",
                f"debug/mock-otp/{self.test_phone_business.replace('+', '')}",
                200
            )
            if success_debug:
                business_mock_otp = response_debug.get('mock_otp')
        
        if not business_mock_otp:
            self.log_test("Business Registration Flow", False, "No business mock OTP available")
            return False
        
        # Verify OTP for business
        success2, response2 = self.run_test(
            "Business OTP Verify",
            "POST",
            "auth/otp/verify",
            200,
            data={
                "phone": self.test_phone_business,
                "otp": business_mock_otp
            }
        )
        
        if not success2 or not response2.get('access_token'):
            return False
        
        # Store business token temporarily
        business_token = response2['access_token']
        old_token = self.access_token
        self.access_token = business_token
        
        # Register as business
        business_data = {
            "phone": self.test_phone_business,
            "business_name": "Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Mahallesi, Test Sokak No:1, İstanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant for API testing"
        }
        
        success3 = self.run_test(
            "Business Registration",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        # Restore original token
        self.access_token = old_token
        
        return success1 and success2 and success3

    def test_customer_registration_flow(self):
        """Test complete customer registration flow"""
        # First request OTP for customer phone
        success1, response1 = self.run_test(
            "Customer OTP Request",
            "POST",
            "auth/otp/request",
            200,
            data={
                "phone": self.test_phone_customer,
                "device_id": "customer_device_123"
            }
        )
        
        if not success1:
            return False
        
        # Get mock OTP for customer
        customer_mock_otp = response1.get('mock_otp')
        if not customer_mock_otp:
            success_debug, response_debug = self.run_test(
                "Get Customer Mock OTP",
                "GET",
                f"debug/mock-otp/{self.test_phone_customer.replace('+', '')}",
                200
            )
            if success_debug:
                customer_mock_otp = response_debug.get('mock_otp')
        
        if not customer_mock_otp:
            self.log_test("Customer Registration Flow", False, "No customer mock OTP available")
            return False
        
        # Verify OTP for customer
        success2, response2 = self.run_test(
            "Customer OTP Verify",
            "POST",
            "auth/otp/verify",
            200,
            data={
                "phone": self.test_phone_customer,
                "otp": customer_mock_otp
            }
        )
        
        if not success2 or not response2.get('access_token'):
            return False
        
        # Store customer token temporarily
        customer_token = response2['access_token']
        old_token = self.access_token
        self.access_token = customer_token
        
        # Register as customer
        customer_data = {
            "phone": self.test_phone_customer,
            "first_name": "Test",
            "last_name": "Müşteri",
            "city": "İstanbul",
            "email": "customer@example.com"
        }
        
        success3 = self.run_test(
            "Customer Registration",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        # Restore original token
        self.access_token = old_token
        
        return success1 and success2 and success3

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test multiple rapid OTP requests to trigger rate limiting
        test_phone_rate = "+905551234570"
        
        # Send first request (should succeed)
        success1, _ = self.run_test(
            "Rate Limit Test - Request 1",
            "POST",
            "auth/otp/request",
            200,
            data={"phone": test_phone_rate}
        )
        
        # Send second request immediately (should succeed)
        success2, _ = self.run_test(
            "Rate Limit Test - Request 2",
            "POST",
            "auth/otp/request",
            200,
            data={"phone": test_phone_rate}
        )
        
        # Send third request immediately (should be rate limited)
        success3, response3 = self.run_test(
            "Rate Limit Test - Request 3 (Should Fail)",
            "POST",
            "auth/otp/request",
            400,
            data={"phone": test_phone_rate}
        )
        
        # Check if rate limiting message is present
        rate_limited = False
        if not success3 and isinstance(response3, dict):
            error_detail = response3.get('detail', '')
            if 'rate limit' in error_detail.lower() or 'retry' in error_detail.lower():
                rate_limited = True
        
        return success1 and success2 and rate_limited

    def test_phone_format_validation(self):
        """Test various Turkish phone number formats"""
        phone_formats = [
            ("+905551234567", True),   # International format
            ("905551234567", True),    # Without +
            ("05551234567", True),     # With leading 0
            ("5551234567", True),      # Without country code
            ("123456789", False),      # Too short
            ("+1234567890", False),    # Non-Turkish
            ("invalid", False),        # Invalid format
        ]
        
        all_passed = True
        for phone, should_succeed in phone_formats:
            expected_status = 200 if should_succeed else 400
            test_name = f"Phone Format - {phone} ({'Valid' if should_succeed else 'Invalid'})"
            
            success, _ = self.run_test(
                test_name,
                "POST",
                "auth/otp/request",
                expected_status,
                data={"phone": phone}
            )
            
            if not success:
                all_passed = False
        
        return all_passed

    def test_logout(self):
        """Test user logout"""
        if not self.refresh_token:
            self.log_test("Logout", False, "No refresh token available")
            return False
        
        return self.run_test(
            "Logout",
            "POST",
            "auth/logout",
            200,
            data={
                "refresh_token": self.refresh_token
            }
        )

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        old_token = self.access_token
        self.access_token = "invalid-token"
        
        success, _ = self.run_test(
            "Unauthorized Access",
            "GET",
            "me",
            401
        )
        
        self.access_token = old_token
        return success

    def run_all_tests(self):
        """Run all backend tests for Phone/SMS OTP Authentication"""
        print("🚀 Starting DeliverTR Backend API Tests - Phone/SMS OTP Authentication")
        print("=" * 70)
        
        # Test basic connectivity
        self.test_root_endpoint()
        self.test_health_check()
        
        # Test phone format validation
        self.test_phone_format_validation()
        
        # Test OTP request flow
        self.test_otp_request_valid_phone()
        time.sleep(1)  # Brief pause between requests
        self.test_otp_request_invalid_phone()
        
        # Test OTP verification flow
        self.test_otp_verify_correct_code()
        time.sleep(1)
        self.test_otp_verify_incorrect_code()
        
        # Test JWT token management
        self.test_token_refresh()
        
        # Test authenticated endpoints
        self.test_get_profile()
        self.test_update_profile()
        
        # Test role registration endpoints
        self.test_courier_registration()
        time.sleep(1)
        self.test_business_registration_flow()
        time.sleep(1)
        self.test_customer_registration_flow()
        
        # Test rate limiting
        self.test_rate_limiting()
        
        # Test logout
        self.test_logout()
        
        # Test unauthorized access
        self.test_unauthorized_access()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY - Phone/SMS OTP Authentication")
        print("=" * 70)
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
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100,
                    "timestamp": datetime.now().isoformat(),
                    "test_type": "phone_sms_otp_authentication"
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