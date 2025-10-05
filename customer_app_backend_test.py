#!/usr/bin/env python3
"""
Customer App Backend Endpoints Testing
=====================================

This script tests the new Customer App backend endpoints as requested:

1. Restaurant discovery endpoints:
   - GET /api/restaurants/discover
   - GET /api/restaurants/near?lat=41.0058&lng=29.0281&radius=50000
   - GET /api/businesses/{business_id}/products

2. Profile endpoints:
   - GET /api/profile/coupons
   - GET /api/profile/discounts  
   - GET /api/campaigns
   - GET /api/payment-methods

3. Customer login flow:
   - POST /api/auth/login with testcustomer@example.com/test123

Usage: python customer_app_backend_test.py
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://kurye-platform.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_details": []
}

def log_test(test_name, success, details="", response_data=None):
    """Log test result"""
    test_results["total_tests"] += 1
    if success:
        test_results["passed_tests"] += 1
        status = "✅ PASS"
    else:
        test_results["failed_tests"] += 1
        status = "❌ FAIL"
    
    test_info = {
        "name": test_name,
        "status": status,
        "details": details,
        "response_data": response_data
    }
    test_results["test_details"].append(test_info)
    
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    if not success and response_data:
        print(f"   Response: {response_data}")
    print()

def test_customer_login():
    """Test customer login flow"""
    print("🔐 TESTING CUSTOMER LOGIN FLOW")
    print("=" * 50)
    
    try:
        login_data = {
            "email": TEST_CUSTOMER_EMAIL,
            "password": TEST_CUSTOMER_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                user = data["user"]
                token_length = len(data["access_token"])
                log_test(
                    "Customer Login",
                    True,
                    f"Login successful. User: {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')}), Token length: {token_length} chars"
                )
                return data["access_token"]
            else:
                log_test("Customer Login", False, "Missing access_token or user in response", data)
                return None
        else:
            log_test("Customer Login", False, f"HTTP {response.status_code}", response.text)
            return None
            
    except Exception as e:
        log_test("Customer Login", False, f"Exception: {str(e)}")
        return None

def test_restaurant_discovery_endpoints(auth_token=None):
    """Test restaurant discovery endpoints"""
    print("🍽️ TESTING RESTAURANT DISCOVERY ENDPOINTS")
    print("=" * 50)
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Test 1: GET /api/restaurants/discover
    try:
        response = requests.get(f"{API_BASE}/restaurants/discover", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/restaurants/discover",
                    True,
                    f"Retrieved {len(data)} restaurants for discovery page"
                )
            else:
                log_test("GET /api/restaurants/discover", False, "Response is not a list", data)
        else:
            log_test("GET /api/restaurants/discover", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/restaurants/discover", False, f"Exception: {str(e)}")
    
    # Test 2: GET /api/restaurants/near with Kadıköy coordinates
    try:
        params = {
            "lat": 41.0058,
            "lng": 29.0281,
            "radius": 50000
        }
        response = requests.get(f"{API_BASE}/restaurants/near", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/restaurants/near (Kadıköy)",
                    True,
                    f"Retrieved {len(data)} restaurants within 50km of Kadıköy coordinates (41.0058, 29.0281)"
                )
                # Store first business ID for products test
                if data:
                    return data[0].get("id")
            else:
                log_test("GET /api/restaurants/near (Kadıköy)", False, "Response is not a list", data)
        else:
            log_test("GET /api/restaurants/near (Kadıköy)", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/restaurants/near (Kadıköy)", False, f"Exception: {str(e)}")
    
    return None

def test_business_products_endpoint(business_id, auth_token=None):
    """Test business products endpoint"""
    print("🛍️ TESTING BUSINESS PRODUCTS ENDPOINT")
    print("=" * 50)
    
    if not business_id:
        log_test("GET /api/businesses/{business_id}/products", False, "No business ID available from previous tests")
        return
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        response = requests.get(f"{API_BASE}/businesses/{business_id}/products", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    f"GET /api/businesses/{business_id}/products",
                    True,
                    f"Retrieved {len(data)} products for business {business_id}"
                )
            else:
                log_test(f"GET /api/businesses/{business_id}/products", False, "Response is not a list", data)
        else:
            log_test(f"GET /api/businesses/{business_id}/products", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test(f"GET /api/businesses/{business_id}/products", False, f"Exception: {str(e)}")

def test_profile_endpoints(auth_token):
    """Test profile endpoints (require authentication)"""
    print("👤 TESTING PROFILE ENDPOINTS")
    print("=" * 50)
    
    if not auth_token:
        log_test("Profile Endpoints", False, "No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test 1: GET /api/profile/coupons
    try:
        response = requests.get(f"{API_BASE}/profile/coupons", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/profile/coupons",
                    True,
                    f"Retrieved {len(data)} user coupons (mock data expected)"
                )
            else:
                log_test("GET /api/profile/coupons", False, "Response is not a list", data)
        else:
            log_test("GET /api/profile/coupons", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/profile/coupons", False, f"Exception: {str(e)}")
    
    # Test 2: GET /api/profile/discounts
    try:
        response = requests.get(f"{API_BASE}/profile/discounts", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/profile/discounts",
                    True,
                    f"Retrieved {len(data)} user discounts (mock data expected)"
                )
            else:
                log_test("GET /api/profile/discounts", False, "Response is not a list", data)
        else:
            log_test("GET /api/profile/discounts", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/profile/discounts", False, f"Exception: {str(e)}")
    
    # Test 3: GET /api/campaigns (public endpoint)
    try:
        response = requests.get(f"{API_BASE}/campaigns", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/campaigns",
                    True,
                    f"Retrieved {len(data)} active campaigns (mock data expected)"
                )
            else:
                log_test("GET /api/campaigns", False, "Response is not a list", data)
        else:
            log_test("GET /api/campaigns", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/campaigns", False, f"Exception: {str(e)}")
    
    # Test 4: GET /api/payment-methods
    try:
        response = requests.get(f"{API_BASE}/payment-methods", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_test(
                    "GET /api/payment-methods",
                    True,
                    f"Retrieved {len(data)} payment methods (empty list expected for new user)"
                )
            else:
                log_test("GET /api/payment-methods", False, "Response is not a list", data)
        else:
            log_test("GET /api/payment-methods", False, f"HTTP {response.status_code}", response.text)
            
    except Exception as e:
        log_test("GET /api/payment-methods", False, f"Exception: {str(e)}")

def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("🎯 CUSTOMER APP BACKEND TESTING SUMMARY")
    print("=" * 60)
    
    total = test_results["total_tests"]
    passed = test_results["passed_tests"]
    failed = test_results["failed_tests"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS ({failed}):")
        for test in test_results["test_details"]:
            if "❌" in test["status"]:
                print(f"  • {test['name']}: {test['details']}")
    
    if passed > 0:
        print(f"\n✅ PASSED TESTS ({passed}):")
        for test in test_results["test_details"]:
            if "✅" in test["status"]:
                print(f"  • {test['name']}: {test['details']}")
    
    print(f"\n🌐 Backend URL: {BACKEND_URL}")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 80  # Consider 80%+ success rate as overall success

def main():
    """Main test execution"""
    print("🚀 CUSTOMER APP BACKEND ENDPOINTS TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Test customer login
    auth_token = test_customer_login()
    
    # Step 2: Test restaurant discovery endpoints
    business_id = test_restaurant_discovery_endpoints(auth_token)
    
    # Step 3: Test business products endpoint
    test_business_products_endpoint(business_id, auth_token)
    
    # Step 4: Test profile endpoints
    test_profile_endpoints(auth_token)
    
    # Step 5: Print summary
    success = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()