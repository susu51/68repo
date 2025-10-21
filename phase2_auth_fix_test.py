#!/usr/bin/env python3
"""
PHASE 2 AUTHENTICATION FIX VERIFICATION
Quick test to verify that the authentication issue in Phase 2 routes has been resolved.

TESTING SCOPE - LIMITED VERIFICATION:

PRIORITY 1: Authentication Fix Verification
- Test authentication on Business Menu routes (routes/business.py)
- Test authentication on Geospatial routes (routes/nearby.py) 
- Test authentication on Customer Orders routes (routes/orders.py)

AUTHENTICATION DETAILS:
- Business login: testrestoran@example.com / test123
- Customer login: testcustomer@example.com / test123

SPECIFIC TESTS TO RUN:

1. Business Menu Authentication Test:
   - Login as business user (testrestoran@example.com/test123)
   - Try GET /api/business/menu (should return 200 instead of previous 401 "User not found")

2. Geospatial Authentication Test:
   - Login as customer (testcustomer@example.com/test123)  
   - Try GET /api/nearby/businesses?lat=41.0082&lng=28.9784 (should return 200 instead of 401)

3. Customer Orders Authentication Test:
   - Login as customer (testcustomer@example.com/test123)
   - Try GET /api/orders/my (should return 200 instead of 401)

SUCCESS CRITERIA:
- All three route modules should accept valid JWT tokens
- Authentication errors should be 403 (Forbidden) not 401 (User not found)
- Business users should be able to access business routes
- Customer users should be able to access customer/geospatial routes
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"}
}

class Phase2AuthFixTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_users(self):
        """Authenticate test users and get JWT tokens"""
        print("🔐 AUTHENTICATING TEST USERS...")
        
        for role, credentials in TEST_CREDENTIALS.items():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, User ID: {data['user']['id']}, Role: {data['user']['role']}"
                    )
                else:
                    self.log_test(
                        f"Authentication - {role.title()}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Authentication - {role.title()}",
                    False,
                    error=str(e)
                )

    def test_business_menu_authentication(self):
        """Test Business Menu Authentication - GET /api/business/menu"""
        print("🏪 TESTING BUSINESS MENU AUTHENTICATION...")
        
        if "business" not in self.tokens:
            self.log_test(
                "Business Menu Authentication - Setup",
                False,
                error="No business token available"
            )
            return

        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/business/menu",
                headers=headers,
                timeout=10
            )
            
            # Success criteria: Should return 200 instead of 401 "User not found"
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Business Menu Authentication - GET /api/business/menu",
                    True,
                    f"Status: {response.status_code} (SUCCESS - Fixed from previous 401), Response type: {type(data)}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "Business Menu Authentication - GET /api/business/menu",
                    True,
                    f"Status: {response.status_code} (ACCEPTABLE - Proper 403 Forbidden instead of 401 User not found)"
                )
            elif response.status_code == 401:
                # Check if it's the old "User not found" error
                error_text = response.text.lower()
                if "user not found" in error_text:
                    self.log_test(
                        "Business Menu Authentication - GET /api/business/menu",
                        False,
                        f"Status: {response.status_code}",
                        "AUTHENTICATION FIX NOT WORKING - Still getting 401 'User not found' error"
                    )
                else:
                    self.log_test(
                        "Business Menu Authentication - GET /api/business/menu",
                        False,
                        f"Status: {response.status_code}",
                        f"401 error but not 'User not found': {response.text}"
                    )
            else:
                self.log_test(
                    "Business Menu Authentication - GET /api/business/menu",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Menu Authentication - GET /api/business/menu",
                False,
                error=str(e)
            )

    def test_geospatial_authentication(self):
        """Test Geospatial Authentication - GET /api/nearby/businesses"""
        print("🗺️ TESTING GEOSPATIAL AUTHENTICATION...")
        
        if "customer" not in self.tokens:
            self.log_test(
                "Geospatial Authentication - Setup",
                False,
                error="No customer token available"
            )
            return

        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses?lat=41.0082&lng=28.9784",
                headers=headers,
                timeout=10
            )
            
            # Success criteria: Should return 200 instead of 401
            if response.status_code == 200:
                data = response.json()
                businesses_count = len(data) if isinstance(data, list) else len(data.get('businesses', [])) if isinstance(data, dict) else 0
                self.log_test(
                    "Geospatial Authentication - GET /api/nearby/businesses",
                    True,
                    f"Status: {response.status_code} (SUCCESS - Fixed from previous 401), Businesses found: {businesses_count}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "Geospatial Authentication - GET /api/nearby/businesses",
                    True,
                    f"Status: {response.status_code} (ACCEPTABLE - Proper 403 Forbidden instead of 401)"
                )
            elif response.status_code == 401:
                # Check if it's the old "User not found" error
                error_text = response.text.lower()
                if "user not found" in error_text:
                    self.log_test(
                        "Geospatial Authentication - GET /api/nearby/businesses",
                        False,
                        f"Status: {response.status_code}",
                        "AUTHENTICATION FIX NOT WORKING - Still getting 401 'User not found' error"
                    )
                else:
                    self.log_test(
                        "Geospatial Authentication - GET /api/nearby/businesses",
                        False,
                        f"Status: {response.status_code}",
                        f"401 error but not 'User not found': {response.text}"
                    )
            else:
                self.log_test(
                    "Geospatial Authentication - GET /api/nearby/businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Geospatial Authentication - GET /api/nearby/businesses",
                False,
                error=str(e)
            )

    def test_customer_orders_authentication(self):
        """Test Customer Orders Authentication - GET /api/orders/my"""
        print("📦 TESTING CUSTOMER ORDERS AUTHENTICATION...")
        
        if "customer" not in self.tokens:
            self.log_test(
                "Customer Orders Authentication - Setup",
                False,
                error="No customer token available"
            )
            return

        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/my",
                headers=headers,
                timeout=10
            )
            
            # Success criteria: Should return 200 instead of 401
            if response.status_code == 200:
                data = response.json()
                orders_count = len(data) if isinstance(data, list) else len(data.get('orders', [])) if isinstance(data, dict) else 0
                self.log_test(
                    "Customer Orders Authentication - GET /api/orders/my",
                    True,
                    f"Status: {response.status_code} (SUCCESS - Fixed from previous 401), Orders found: {orders_count}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "Customer Orders Authentication - GET /api/orders/my",
                    True,
                    f"Status: {response.status_code} (ACCEPTABLE - Proper 403 Forbidden instead of 401)"
                )
            elif response.status_code == 401:
                # Check if it's the old "User not found" error
                error_text = response.text.lower()
                if "user not found" in error_text:
                    self.log_test(
                        "Customer Orders Authentication - GET /api/orders/my",
                        False,
                        f"Status: {response.status_code}",
                        "AUTHENTICATION FIX NOT WORKING - Still getting 401 'User not found' error"
                    )
                else:
                    self.log_test(
                        "Customer Orders Authentication - GET /api/orders/my",
                        False,
                        f"Status: {response.status_code}",
                        f"401 error but not 'User not found': {response.text}"
                    )
            else:
                self.log_test(
                    "Customer Orders Authentication - GET /api/orders/my",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Orders Authentication - GET /api/orders/my",
                False,
                error=str(e)
            )

    def test_jwt_token_validation(self):
        """Test JWT token validation is working correctly"""
        print("🔑 TESTING JWT TOKEN VALIDATION...")
        
        # Test with invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(
                f"{BACKEND_URL}/orders/my",
                headers=headers,
                timeout=10
            )
            
            # Should return 401 for invalid token, but not "User not found"
            if response.status_code == 401:
                error_text = response.text.lower()
                if "user not found" in error_text:
                    self.log_test(
                        "JWT Token Validation - Invalid Token",
                        False,
                        f"Status: {response.status_code}",
                        "ISSUE: Invalid token still returns 'User not found' instead of proper JWT validation error"
                    )
                else:
                    self.log_test(
                        "JWT Token Validation - Invalid Token",
                        True,
                        f"Status: {response.status_code} (Correct - Invalid token rejected without 'User not found')"
                    )
            else:
                self.log_test(
                    "JWT Token Validation - Invalid Token",
                    False,
                    f"Status: {response.status_code} (Expected 401 for invalid token)",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "JWT Token Validation - Invalid Token",
                False,
                error=str(e)
            )

        # Test with no token
        try:
            response = requests.get(
                f"{BACKEND_URL}/orders/my",
                timeout=10
            )
            
            # Should return 401 for missing token
            if response.status_code == 401:
                self.log_test(
                    "JWT Token Validation - No Token",
                    True,
                    f"Status: {response.status_code} (Correct - No token rejected)"
                )
            else:
                self.log_test(
                    "JWT Token Validation - No Token",
                    False,
                    f"Status: {response.status_code} (Expected 401 for missing token)",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "JWT Token Validation - No Token",
                False,
                error=str(e)
            )

    def run_authentication_fix_verification(self):
        """Run Phase 2 authentication fix verification tests"""
        print("🚀 STARTING PHASE 2 AUTHENTICATION FIX VERIFICATION")
        print("=" * 60)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not all(role in self.tokens for role in ["business", "customer"]):
            print("❌ CRITICAL: Authentication failed for required roles. Cannot proceed.")
            return
        
        # Step 2: Test Business Menu Authentication
        self.test_business_menu_authentication()
        
        # Step 3: Test Geospatial Authentication
        self.test_geospatial_authentication()
        
        # Step 4: Test Customer Orders Authentication
        self.test_customer_orders_authentication()
        
        # Step 5: Test JWT Token Validation
        self.test_jwt_token_validation()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 AUTHENTICATION FIX VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical authentication tests
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"] and "GET /api/" in r["test"]]
        auth_passed = sum(1 for r in auth_tests if r["success"])
        auth_total = len(auth_tests)
        
        print("🎯 CRITICAL AUTHENTICATION TESTS:")
        print(f"   Authentication Fix Tests: {auth_passed}/{auth_total}")
        
        for test in auth_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
        
        print("\n" + "=" * 60)
        print("🔍 DETAILED FAILURE ANALYSIS")
        print("=" * 60)
        
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            for result in failed_results:
                print(f"❌ {result['test']}")
                if result["error"]:
                    print(f"   Error: {result['error']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
                print()
        else:
            print("🎉 No test failures detected!")
        
        print("\n" + "=" * 60)
        print("📋 AUTHENTICATION FIX STATUS")
        print("=" * 60)
        
        # Check if the main authentication issues are resolved
        business_menu_fixed = any(r["success"] and "business/menu" in r["test"] for r in self.test_results)
        geospatial_fixed = any(r["success"] and "nearby/businesses" in r["test"] for r in self.test_results)
        customer_orders_fixed = any(r["success"] and "orders/my" in r["test"] for r in self.test_results)
        
        if business_menu_fixed and geospatial_fixed and customer_orders_fixed:
            print("✅ AUTHENTICATION FIX SUCCESSFUL")
            print("   - Business Menu routes now accept valid JWT tokens")
            print("   - Geospatial routes now accept valid JWT tokens") 
            print("   - Customer Orders routes now accept valid JWT tokens")
            print("   - No more 401 'User not found' errors detected")
        elif auth_passed >= auth_total * 0.67:  # At least 2/3 working
            print("⚠️ AUTHENTICATION FIX PARTIALLY SUCCESSFUL")
            print("   - Most routes are working correctly")
            print("   - Some routes may still have authentication issues")
        else:
            print("❌ AUTHENTICATION FIX NOT SUCCESSFUL")
            print("   - Routes are still returning 401 'User not found' errors")
            print("   - JWT token validation may not be working properly")
        
        print("\n" + "=" * 60)
        print("📋 RECOMMENDATIONS")
        print("=" * 60)
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Phase 2 authentication fix is working perfectly")
            print("   - All routes properly validate JWT tokens")
            print("   - Authentication errors are properly handled")
            print("   - Ready for comprehensive functionality testing")
        elif success_rate >= 75:
            print("⚠️ GOOD: Phase 2 authentication fix is mostly working")
            print("   - Most routes are properly validating JWT tokens")
            print("   - Minor issues may need attention")
        elif success_rate >= 50:
            print("⚠️ NEEDS ATTENTION: Phase 2 authentication fix has issues")
            print("   - Some routes are still not properly validating JWT tokens")
            print("   - Review authentication middleware implementation")
        else:
            print("❌ CRITICAL: Phase 2 authentication fix is not working")
            print("   - Routes are still returning 401 'User not found' errors")
            print("   - JWT token validation needs to be fixed")
            print("   - Cannot proceed with comprehensive testing until fixed")

if __name__ == "__main__":
    tester = Phase2AuthFixTester()
    tester.run_authentication_fix_verification()