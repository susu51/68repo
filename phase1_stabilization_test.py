#!/usr/bin/env python3
"""
Phase 1 Stabilization - Backend System Testing
Tests critical backend endpoints after emergency debug fixes:
1. Duplicate /admin/users endpoint removal
2. datetime serialization issues  
3. JWT authentication flows

PRIMARY TEST TARGETS:
- Admin endpoints: GET /api/admin/users, GET /api/admin/couriers/kyc, simple admin login
- Customer endpoints: login, restaurant fetching, profile management
- Business endpoints: registration, login, product management
- Core functionality: order system, payments, authentication flows

AUTHENTICATION TESTS:
- Admin login (any email + password '6851')
- Customer login (testcustomer@example.com/test123)
- Business login (testrestoran@example.com/test123)
- JWT token validation across all roles

CRITICAL ENDPOINTS TO VERIFY:
- GET /api/admin/users (previously had 500 error)
- GET /api/businesses (customer restaurant discovery)
- POST /api/auth/login (all user types)
- GET /api/products/my (business dashboard)
- Order management endpoints

FOCUS ON:
- No 500 internal server errors
- Proper datetime handling
- ObjectId to string conversion
- Authentication middleware working
- CORS and API routing
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class Phase1StabilizationTester:
    def __init__(self, base_url="https://quickcourier.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Authentication tokens
        self.admin_token = None
        self.customer_token = None
        self.business_token = None
        
        # Test data
        self.test_customer_email = "testcustomer@example.com"
        self.test_customer_password = "test123"
        self.test_business_email = "testrestoran@example.com"
        self.test_business_password = "test123"

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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {'Content-Type': 'application/json'}
        
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        
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

    # ===== ADMIN AUTHENTICATION TESTS =====
    
    def test_admin_login_simple(self):
        """Test admin login with any email + password '6851'"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
        
        test_cases = [
            {
                "name": "Admin Login - Any Email + Password 6851",
                "email": "admin@test.com",
                "password": "6851"
            },
            {
                "name": "Admin Login - Different Email + Password 6851", 
                "email": "test@admin.com",
                "password": "6851"
            }
        ]
        
        all_success = True
        
        for test_case in test_cases:
            login_data = {
                "email": test_case["email"],
                "password": test_case["password"]
            }
            
            success, response = self.run_test(
                test_case["name"],
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if success:
                # Verify admin user data structure
                if self.verify_admin_response(response):
                    # Store admin token for later tests
                    if response.get('access_token'):
                        self.admin_token = response['access_token']
                        print(f"   Admin token stored: {self.admin_token[:20]}...")
                else:
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def verify_admin_response(self, response):
        """Verify admin login returns proper structure"""
        if not response:
            print(f"   ❌ No response data")
            return False
        
        # Check response structure
        required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
        for field in required_fields:
            if field not in response:
                print(f"   ❌ Missing field in response: {field}")
                return False
        
        # Check user type
        if response.get('user_type') != 'admin':
            print(f"   ❌ Wrong user_type: {response.get('user_type')}, expected 'admin'")
            return False
        
        # Check user_data structure
        user_data = response.get('user_data', {})
        if user_data.get('role') != 'admin':
            print(f"   ❌ Wrong role in user_data: {user_data.get('role')}, expected 'admin'")
            return False
        
        print(f"   ✅ Admin response structure correct")
        return True

    # ===== CRITICAL ADMIN ENDPOINTS =====
    
    def test_admin_users_endpoint(self):
        """Test GET /api/admin/users (previously had 500 error)"""
        print("\n👥 TESTING ADMIN USERS ENDPOINT")
        
        if not self.admin_token:
            self.log_test("Admin Users Endpoint", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "GET /api/admin/users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Retrieved {len(response)} users")
                
                # Check for datetime serialization issues
                datetime_issues = []
                for i, user in enumerate(response[:5]):  # Check first 5 users
                    if 'created_at' in user:
                        created_at = user['created_at']
                        if not isinstance(created_at, str):
                            datetime_issues.append(f"User {i}: created_at is {type(created_at)}, not string")
                
                if datetime_issues:
                    print(f"   ⚠️  Datetime serialization issues found:")
                    for issue in datetime_issues:
                        print(f"      - {issue}")
                else:
                    print(f"   ✅ No datetime serialization issues detected")
                
                return True
            else:
                print(f"   ❌ Response is not a list: {type(response)}")
                return False
        
        return success

    def test_admin_couriers_kyc_endpoint(self):
        """Test GET /api/admin/couriers/kyc"""
        print("\n🚚 TESTING ADMIN COURIERS KYC ENDPOINT")
        
        if not self.admin_token:
            self.log_test("Admin Couriers KYC Endpoint", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "GET /api/admin/couriers/kyc",
            "GET",
            "admin/couriers/kyc",
            200,
            token=self.admin_token
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Retrieved {len(response)} couriers for KYC review")
                return True
            else:
                print(f"   ❌ Response is not a list: {type(response)}")
                return False
        
        return success

    # ===== CUSTOMER AUTHENTICATION & ENDPOINTS =====
    
    def test_customer_login(self):
        """Test customer login (testcustomer@example.com/test123)"""
        print("\n👤 TESTING CUSTOMER AUTHENTICATION")
        
        login_data = {
            "email": self.test_customer_email,
            "password": self.test_customer_password
        }
        
        success, response = self.run_test(
            "Customer Login - testcustomer@example.com",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            # Store customer token
            if response.get('access_token'):
                self.customer_token = response['access_token']
                print(f"   Customer token stored: {self.customer_token[:20]}...")
            
            # Verify it's customer role
            user_data = response.get('user_data', {})
            if user_data.get('role') == 'customer':
                print(f"   ✅ Customer role verified")
                return True
            else:
                print(f"   ❌ Wrong role: {user_data.get('role')}, expected 'customer'")
                return False
        
        return success

    def test_customer_restaurant_discovery(self):
        """Test GET /api/businesses (customer restaurant discovery)"""
        print("\n🍽️ TESTING CUSTOMER RESTAURANT DISCOVERY")
        
        success, response = self.run_test(
            "GET /api/businesses - Restaurant Discovery",
            "GET",
            "businesses",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Retrieved {len(response)} businesses")
                
                # Check business data structure
                if response:
                    business = response[0]
                    required_fields = ['id', 'name', 'category']
                    missing_fields = [field for field in required_fields if field not in business]
                    
                    if missing_fields:
                        print(f"   ⚠️  Missing business fields: {missing_fields}")
                    else:
                        print(f"   ✅ Business data structure correct")
                
                return True
            else:
                print(f"   ❌ Response is not a list: {type(response)}")
                return False
        
        return success

    # ===== BUSINESS AUTHENTICATION & ENDPOINTS =====
    
    def test_business_login(self):
        """Test business login (testrestoran@example.com/test123)"""
        print("\n🏢 TESTING BUSINESS AUTHENTICATION")
        
        login_data = {
            "email": self.test_business_email,
            "password": self.test_business_password
        }
        
        success, response = self.run_test(
            "Business Login - testrestoran@example.com",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            # Store business token
            if response.get('access_token'):
                self.business_token = response['access_token']
                print(f"   Business token stored: {self.business_token[:20]}...")
            
            # Verify it's business role
            user_data = response.get('user_data', {})
            if user_data.get('role') == 'business':
                print(f"   ✅ Business role verified")
                return True
            else:
                print(f"   ❌ Wrong role: {user_data.get('role')}, expected 'business'")
                return False
        
        return success

    def test_business_products_endpoint(self):
        """Test GET /api/products/my (business dashboard)"""
        print("\n📦 TESTING BUSINESS PRODUCTS ENDPOINT")
        
        if not self.business_token:
            self.log_test("Business Products Endpoint", False, "No business token available")
            return False
        
        success, response = self.run_test(
            "GET /api/products/my - Business Dashboard",
            "GET",
            "products/my",
            200,
            token=self.business_token
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Retrieved {len(response)} business products")
                
                # Check for datetime serialization issues
                if response:
                    product = response[0]
                    if 'created_at' in product:
                        created_at = product['created_at']
                        if isinstance(created_at, str):
                            print(f"   ✅ Product datetime properly serialized")
                        else:
                            print(f"   ⚠️  Product datetime not serialized: {type(created_at)}")
                
                return True
            else:
                print(f"   ❌ Response is not a list: {type(response)}")
                return False
        
        return success

    # ===== JWT TOKEN VALIDATION TESTS =====
    
    def test_jwt_token_validation(self):
        """Test JWT token validation across all roles"""
        print("\n🔑 TESTING JWT TOKEN VALIDATION")
        
        all_success = True
        
        # Test admin token validation
        if self.admin_token:
            success, response = self.run_test(
                "Admin Token Validation",
                "GET",
                "admin/users",
                200,
                token=self.admin_token
            )
            if not success:
                all_success = False
        
        # Test customer token validation
        if self.customer_token:
            success, response = self.run_test(
                "Customer Token Validation",
                "GET",
                "businesses",  # Public endpoint that should work
                200,
                token=self.customer_token
            )
            if not success:
                all_success = False
        
        # Test business token validation
        if self.business_token:
            success, response = self.run_test(
                "Business Token Validation",
                "GET",
                "products/my",
                200,
                token=self.business_token
            )
            if not success:
                all_success = False
        
        # Test invalid token
        success, response = self.run_test(
            "Invalid Token Test",
            "GET",
            "admin/users",
            401,  # Should fail with unauthorized
            token="invalid_token_12345"
        )
        if not success:
            all_success = False
        
        return all_success

    # ===== CORE FUNCTIONALITY TESTS =====
    
    def test_order_management_endpoints(self):
        """Test core order management endpoints"""
        print("\n📋 TESTING ORDER MANAGEMENT ENDPOINTS")
        
        all_success = True
        
        # Test getting orders as customer
        if self.customer_token:
            success, response = self.run_test(
                "GET /api/orders - Customer Orders",
                "GET",
                "orders",
                200,
                token=self.customer_token
            )
            if not success:
                all_success = False
        
        # Test getting orders as business
        if self.business_token:
            success, response = self.run_test(
                "GET /api/orders - Business Orders",
                "GET",
                "orders",
                200,
                token=self.business_token
            )
            if not success:
                all_success = False
        
        # Test getting orders as admin
        if self.admin_token:
            success, response = self.run_test(
                "GET /api/admin/orders - Admin Orders",
                "GET",
                "admin/orders",
                200,
                token=self.admin_token
            )
            if not success:
                all_success = False
        
        return all_success

    # ===== ERROR HANDLING TESTS =====
    
    def test_no_500_errors(self):
        """Test that critical endpoints don't return 500 errors"""
        print("\n🚨 TESTING FOR 500 INTERNAL SERVER ERRORS")
        
        critical_endpoints = [
            ("GET /api/admin/users", "GET", "admin/users", self.admin_token),
            ("GET /api/businesses", "GET", "businesses", None),
            ("GET /api/products", "GET", "products", None),
            ("GET /api/admin/orders", "GET", "admin/orders", self.admin_token),
        ]
        
        all_success = True
        
        for name, method, endpoint, token in critical_endpoints:
            if endpoint.startswith("admin/") and not token:
                continue  # Skip admin endpoints without token
            
            success, response = self.run_test(
                f"No 500 Error - {name}",
                method,
                endpoint,
                200,  # Expect success, not 500
                token=token
            )
            
            if not success:
                # Check if it's a 500 error specifically
                try:
                    url = f"{self.api_url}/{endpoint}"
                    headers = {'Content-Type': 'application/json'}
                    if token:
                        headers['Authorization'] = f'Bearer {token}'
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 500:
                        print(f"   🚨 CRITICAL: 500 Internal Server Error on {name}")
                        all_success = False
                    else:
                        print(f"   ✅ No 500 error (got {response.status_code})")
                except Exception as e:
                    print(f"   ⚠️  Error testing {name}: {e}")
        
        return all_success

    # ===== MAIN TEST RUNNER =====
    
    def run_all_tests(self):
        """Run all Phase 1 stabilization tests"""
        print("🚀 STARTING PHASE 1 STABILIZATION TESTING")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test sequence based on review request priorities
        test_methods = [
            self.test_admin_login_simple,
            self.test_admin_users_endpoint,
            self.test_admin_couriers_kyc_endpoint,
            self.test_customer_login,
            self.test_customer_restaurant_discovery,
            self.test_business_login,
            self.test_business_products_endpoint,
            self.test_jwt_token_validation,
            self.test_order_management_endpoints,
            self.test_no_500_errors,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
                self.log_test(test_method.__name__, False, f"Exception: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 PHASE 1 STABILIZATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Print critical issues
        critical_issues = []
        for test in failed_tests:
            if "500" in test['details'] or "Internal Server Error" in test['details']:
                critical_issues.append(test)
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
            for test in critical_issues:
                print(f"   - {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = Phase1StabilizationTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 ALL PHASE 1 STABILIZATION TESTS PASSED!")
        sys.exit(0)
    else:
        print("⚠️  SOME PHASE 1 STABILIZATION TESTS FAILED")
        sys.exit(1)