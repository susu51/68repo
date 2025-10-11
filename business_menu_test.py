#!/usr/bin/env python3
"""
🍕 BUSINESS MENU PRODUCT CREATION ENDPOINT TESTING
Testing POST /business/menu endpoint with business authentication
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://address-manager-5.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
BUSINESS_CREDENTIALS = {
    "email": "business@kuryecini.com",
    "password": "business123"
}

# Test payload from review request - Updated to match API schema
TEST_MENU_ITEM = {
    "title": "Test Pizza",  # API uses 'title' not 'name'
    "description": "Delicious test pizza",
    "price": 50.00,
    "category": "food",
    "is_available": True
}

class BusinessMenuTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.business_token = None
        self.business_user = None
        
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
        
    def test_business_login(self):
        """Test business user login and get authentication cookie"""
        print("\n🔐 TESTING BUSINESS LOGIN")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=BUSINESS_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and data.get("user"):
                    user_data = data["user"]
                    
                    # Validate business user
                    if user_data.get("role") == "business":
                        self.business_user = user_data
                        
                        # Check cookies
                        cookies = response.cookies
                        has_access_token = 'access_token' in cookies
                        
                        if has_access_token:
                            cookie_details = f"Business: {user_data['email']} (ID: {user_data['id']}) - Cookie auth successful"
                            self.log_test("Business Login Authentication", True, cookie_details)
                            return True
                        else:
                            self.log_test("Business Login Authentication", False, "No access_token cookie received", data)
                    else:
                        self.log_test("Business Login Authentication", False, 
                                    f"User role is '{user_data.get('role')}', expected 'business'", data)
                else:
                    self.log_test("Business Login Authentication", False, 
                                f"Invalid response structure: {data}", data)
                    
            elif response.status_code == 401:
                data = response.json()
                self.log_test("Business Login Authentication", False, 
                            f"Authentication failed: {data.get('detail', 'Invalid credentials')}", data)
            else:
                self.log_test("Business Login Authentication", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Login Authentication", False, f"Exception: {str(e)}")
            
        return False
        
    def test_menu_creation_endpoint(self):
        """Test POST /business/menu endpoint"""
        print("\n🍕 TESTING MENU ITEM CREATION")
        
        if not self.business_user:
            self.log_test("Menu Item Creation", False, "Business login required first")
            return
            
        try:
            # Test POST /business/menu endpoint
            response = self.session.post(f"{API_BASE}/business/menu", json=TEST_MENU_ITEM)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                
                # Check if product was created successfully
                if data.get("success") or data.get("id"):
                    product_id = data.get("id") or data.get("product_id")
                    created_name = data.get("name") or data.get("title")
                    created_price = data.get("price")
                    
                    success_details = f"Product created - ID: {product_id}, Name: {created_name}, Price: {created_price}"
                    self.log_test("POST /business/menu - Product Creation", True, success_details)
                    
                    # Validate response data matches input
                    validation_issues = []
                    if created_name != TEST_MENU_ITEM["title"]:
                        validation_issues.append(f"Title mismatch: expected '{TEST_MENU_ITEM['title']}', got '{created_name}'")
                    if created_price != TEST_MENU_ITEM["price"]:
                        validation_issues.append(f"Price mismatch: expected {TEST_MENU_ITEM['price']}, got {created_price}")
                        
                    if validation_issues:
                        self.log_test("Menu Item Data Validation", False, "; ".join(validation_issues), data)
                    else:
                        self.log_test("Menu Item Data Validation", True, "All input data correctly saved")
                        
                else:
                    self.log_test("POST /business/menu - Product Creation", False, 
                                f"Product creation failed: {data}", data)
                    
            elif response.status_code == 403:
                data = response.json()
                self.log_test("POST /business/menu - Product Creation", False, 
                            f"Access denied (403): {data.get('detail', 'Forbidden')}", data)
                            
            elif response.status_code == 401:
                data = response.json()
                self.log_test("POST /business/menu - Product Creation", False, 
                            f"Authentication required (401): {data.get('detail', 'Unauthorized')}", data)
                            
            elif response.status_code == 422:
                data = response.json()
                self.log_test("POST /business/menu - Product Creation", False, 
                            f"Validation error (422): {data.get('detail', 'Invalid data')}", data)
                            
            elif response.status_code == 404:
                self.log_test("POST /business/menu - Product Creation", False, 
                            "Endpoint not found (404) - Check if endpoint exists", response.text)
                            
            else:
                self.log_test("POST /business/menu - Product Creation", False, 
                            f"Unexpected status code: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /business/menu - Product Creation", False, f"Exception: {str(e)}")
            
    def test_alternative_endpoints(self):
        """Test alternative menu/product endpoints if main one fails"""
        print("\n🔍 TESTING ALTERNATIVE ENDPOINTS")
        
        if not self.business_user:
            self.log_test("Alternative Endpoints Test", False, "Business login required first")
            return
            
        # Test alternative endpoints that might handle menu creation
        alternative_endpoints = [
            "/business/products",
            "/business/menu-items", 
            "/products",
            "/menu-items"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                response = self.session.post(f"{API_BASE}{endpoint}", json=TEST_MENU_ITEM)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_test(f"Alternative Endpoint {endpoint}", True, 
                                f"Endpoint works - Status: {response.status_code}")
                elif response.status_code == 404:
                    self.log_test(f"Alternative Endpoint {endpoint}", False, 
                                "Endpoint not found (404)")
                elif response.status_code == 403:
                    self.log_test(f"Alternative Endpoint {endpoint}", False, 
                                "Access denied (403)")
                else:
                    self.log_test(f"Alternative Endpoint {endpoint}", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Alternative Endpoint {endpoint}", False, f"Exception: {str(e)}")
                
    def test_business_kyc_status(self):
        """Check if business KYC status affects menu creation"""
        print("\n🔍 TESTING BUSINESS KYC STATUS")
        
        if not self.business_user:
            self.log_test("Business KYC Status Check", False, "Business login required first")
            return
            
        try:
            # Get current user info to check KYC status
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                kyc_status = data.get("kyc_status", "unknown")
                business_status = data.get("business_status", "unknown")
                
                status_details = f"KYC Status: {kyc_status}, Business Status: {business_status}"
                
                if kyc_status == "approved":
                    self.log_test("Business KYC Status Check", True, 
                                f"Business is approved - {status_details}")
                elif kyc_status == "pending":
                    self.log_test("Business KYC Status Check", False, 
                                f"Business KYC pending - may block menu creation - {status_details}")
                elif kyc_status == "rejected":
                    self.log_test("Business KYC Status Check", False, 
                                f"Business KYC rejected - will block menu creation - {status_details}")
                else:
                    self.log_test("Business KYC Status Check", False, 
                                f"Unknown KYC status - {status_details}")
                    
            else:
                self.log_test("Business KYC Status Check", False, 
                            f"Could not get user info - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Business KYC Status Check", False, f"Exception: {str(e)}")
            
    def test_validation_errors(self):
        """Test validation scenarios"""
        print("\n❌ TESTING VALIDATION SCENARIOS")
        
        if not self.business_user:
            self.log_test("Validation Tests", False, "Business login required first")
            return
            
        # Test missing required fields
        test_cases = [
            {"name": "Missing Title", "data": {k: v for k, v in TEST_MENU_ITEM.items() if k != "title"}},
            {"name": "Missing Price", "data": {k: v for k, v in TEST_MENU_ITEM.items() if k != "price"}},
            {"name": "Invalid Price", "data": {**TEST_MENU_ITEM, "price": "invalid"}},
            {"name": "Negative Price", "data": {**TEST_MENU_ITEM, "price": -10}},
            {"name": "Empty Title", "data": {**TEST_MENU_ITEM, "title": ""}},
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.post(f"{API_BASE}/business/menu", json=test_case["data"])
                
                if response.status_code == 422:
                    self.log_test(f"Validation - {test_case['name']}", True, 
                                "Correctly rejected invalid data with 422")
                elif response.status_code == 400:
                    self.log_test(f"Validation - {test_case['name']}", True, 
                                "Correctly rejected invalid data with 400")
                else:
                    self.log_test(f"Validation - {test_case['name']}", False, 
                                f"Should reject invalid data, got status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Validation - {test_case['name']}", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all business menu tests"""
        print(f"🚀 STARTING BUSINESS MENU PRODUCT CREATION TESTING")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print(f"👤 Business Credentials: {BUSINESS_CREDENTIALS['email']}")
        print("=" * 80)
        
        # Run tests in sequence
        login_success = self.test_business_login()
        
        if login_success:
            self.test_business_kyc_status()
            self.test_menu_creation_endpoint()
            self.test_validation_errors()
        else:
            print("⚠️  Skipping menu tests due to login failure")
            
        self.test_alternative_endpoints()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 BUSINESS MENU TESTING SUMMARY")
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
        
        # Specific findings for the review request
        print(f"\n🎯 REVIEW REQUEST FINDINGS:")
        print(f"📧 Business Login: {BUSINESS_CREDENTIALS['email']}")
        print(f"🍕 Test Payload: {TEST_MENU_ITEM}")
        
        menu_creation_test = next((t for t in self.test_results if "Product Creation" in t["test"]), None)
        if menu_creation_test:
            if menu_creation_test["success"]:
                print(f"✅ POST /business/menu: WORKING - {menu_creation_test['details']}")
            else:
                print(f"❌ POST /business/menu: FAILED - {menu_creation_test['details']}")
        else:
            print(f"⚠️  POST /business/menu: NOT TESTED (login failed)")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = BusinessMenuTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print(f"\n🎉 ALL BUSINESS MENU TESTS PASSED!")
        exit(0)