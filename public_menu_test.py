#!/usr/bin/env python3
"""
Public Menu Endpoint Testing
Test the new public menu endpoint as specified in the review request
"""

import requests
import json
import os
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

# Test credentials
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

class PublicMenuTester:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.business_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_business_login(self):
        """Test 1: Login as business user testbusiness@example.com / test123"""
        try:
            login_data = {
                "email": BUSINESS_EMAIL,
                "password": BUSINESS_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "access_token" in data:
                    self.business_token = data["access_token"]
                    user_data = data.get("user", {})
                    self.business_id = user_data.get("id")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.business_token}"})
                    
                    self.log_test(
                        "Business Login", 
                        True, 
                        f"Successfully logged in as {BUSINESS_EMAIL}, business_id: {self.business_id}, token length: {len(self.business_token)} chars"
                    )
                    return True
                else:
                    self.log_test("Business Login", False, "", "Login response missing success or access_token")
                    return False
            else:
                self.log_test("Business Login", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Business Login", False, "", f"Exception: {str(e)}")
            return False
    
    def test_business_has_menu_items(self):
        """Test 2: Verify business has menu items (from previous tests)"""
        try:
            response = self.session.get(f"{BACKEND_URL}/business/menu")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and object responses
                if isinstance(data, list):
                    menu_items = data
                else:
                    menu_items = data.get("menu_items", [])
                
                if len(menu_items) > 0:
                    available_items = [item for item in menu_items if item.get("is_available", False)]
                    self.log_test(
                        "Business Has Menu Items", 
                        True, 
                        f"Business has {len(menu_items)} total menu items, {len(available_items)} available items"
                    )
                    return menu_items
                else:
                    self.log_test("Business Has Menu Items", False, "", "Business has no menu items")
                    return []
            else:
                self.log_test("Business Has Menu Items", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Business Has Menu Items", False, "", f"Exception: {str(e)}")
            return []
    
    def test_public_menu_endpoint_no_auth(self):
        """Test 3: Test public menu endpoint (NO AUTH): GET /api/business/public/{business_id}/menu"""
        try:
            if not self.business_id:
                self.log_test("Public Menu Endpoint (No Auth)", False, "", "No business_id available")
                return []
            
            # Create a new session without authentication
            public_session = requests.Session()
            
            response = public_session.get(f"{BACKEND_URL}/business/public/{self.business_id}/menu")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's a list or has menu_items key
                if isinstance(data, list):
                    menu_items = data
                else:
                    menu_items = data.get("menu_items", [])
                
                self.log_test(
                    "Public Menu Endpoint (No Auth)", 
                    True, 
                    f"Successfully accessed public menu without authentication, returned {len(menu_items)} items"
                )
                return menu_items
            else:
                self.log_test("Public Menu Endpoint (No Auth)", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Public Menu Endpoint (No Auth)", False, "", f"Exception: {str(e)}")
            return []
    
    def test_public_menu_returns_available_only(self, public_menu_items):
        """Test 4: Should only return available items (is_available=true)"""
        try:
            if not public_menu_items:
                self.log_test(
                    "Public Menu Returns Available Only", 
                    True, 
                    "No menu items returned (expected if business has no available items)"
                )
                return True
            
            # Check if all returned items have is_available=true
            available_items = [item for item in public_menu_items if item.get("is_available", False)]
            unavailable_items = [item for item in public_menu_items if not item.get("is_available", True)]
            
            if len(unavailable_items) == 0:
                self.log_test(
                    "Public Menu Returns Available Only", 
                    True, 
                    f"All {len(public_menu_items)} returned items are available (is_available=true)"
                )
                return True
            else:
                self.log_test(
                    "Public Menu Returns Available Only", 
                    False, 
                    "", 
                    f"Found {len(unavailable_items)} unavailable items in public menu response"
                )
                return False
                
        except Exception as e:
            self.log_test("Public Menu Returns Available Only", False, "", f"Exception: {str(e)}")
            return False
    
    def test_public_menu_response_format(self, public_menu_items):
        """Test 5: Returns proper response format with all fields (id, name, description, price, category, image_url, etc.)"""
        try:
            if not public_menu_items:
                self.log_test(
                    "Public Menu Response Format", 
                    True, 
                    "No menu items to validate format (expected if business has no available items)"
                )
                return True
            
            # Check first item for required fields
            sample_item = public_menu_items[0]
            required_fields = ["id", "name", "price", "category"]
            optional_fields = ["description", "image_url", "preparation_time", "is_available"]
            
            missing_required = []
            present_optional = []
            
            for field in required_fields:
                if field not in sample_item:
                    missing_required.append(field)
            
            for field in optional_fields:
                if field in sample_item:
                    present_optional.append(field)
            
            if len(missing_required) == 0:
                self.log_test(
                    "Public Menu Response Format", 
                    True, 
                    f"Response format correct. Required fields present: {required_fields}. Optional fields present: {present_optional}. Sample item: {json.dumps(sample_item, indent=2)}"
                )
                return True
            else:
                self.log_test(
                    "Public Menu Response Format", 
                    False, 
                    "", 
                    f"Missing required fields: {missing_required}. Sample item: {json.dumps(sample_item, indent=2)}"
                )
                return False
                
        except Exception as e:
            self.log_test("Public Menu Response Format", False, "", f"Exception: {str(e)}")
            return False
    
    def test_public_menu_endpoint_different_business(self):
        """Test 6: Test public menu endpoint with different business ID (should return empty or 404)"""
        try:
            # Test with a non-existent business ID
            fake_business_id = "non-existent-business-id"
            
            # Create a new session without authentication
            public_session = requests.Session()
            
            response = public_session.get(f"{BACKEND_URL}/business/public/{fake_business_id}/menu")
            
            if response.status_code in [200, 404]:
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        menu_items = data
                    else:
                        menu_items = data.get("menu_items", [])
                    
                    if len(menu_items) == 0:
                        self.log_test(
                            "Public Menu Endpoint (Non-existent Business)", 
                            True, 
                            "Non-existent business ID returns empty menu (correct behavior)"
                        )
                    else:
                        self.log_test(
                            "Public Menu Endpoint (Non-existent Business)", 
                            False, 
                            "", 
                            f"Non-existent business ID returned {len(menu_items)} items (should be empty)"
                        )
                else:  # 404
                    self.log_test(
                        "Public Menu Endpoint (Non-existent Business)", 
                        True, 
                        "Non-existent business ID returns 404 (acceptable behavior)"
                    )
            else:
                self.log_test("Public Menu Endpoint (Non-existent Business)", False, "", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Menu Endpoint (Non-existent Business)", False, "", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all public menu endpoint tests"""
        print("🚀 PUBLIC MENU ENDPOINT TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Business Credentials: {BUSINESS_EMAIL} / {BUSINESS_PASSWORD}")
        print("=" * 60)
        print()
        
        # Test 1: Business Login
        if not self.test_business_login():
            print("❌ CRITICAL: Business login failed - cannot proceed with tests")
            return
        
        # Test 2: Verify Business Has Menu Items
        business_menu_items = self.test_business_has_menu_items()
        
        # Test 3: Test Public Menu Endpoint (No Auth)
        public_menu_items = self.test_public_menu_endpoint_no_auth()
        
        # Test 4: Verify Only Available Items Returned
        self.test_public_menu_returns_available_only(public_menu_items)
        
        # Test 5: Verify Response Format
        self.test_public_menu_response_format(public_menu_items)
        
        # Test 6: Test with Non-existent Business
        self.test_public_menu_endpoint_different_business()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
            print()
        
        print("✅ REVIEW REQUEST VERIFICATION:")
        print("   • Business login working: ✅" if any("Business Login" in r["test"] and r["success"] for r in self.test_results) else "   • Business login working: ❌")
        print("   • Business has menu items: ✅" if any("Business Has Menu Items" in r["test"] and r["success"] for r in self.test_results) else "   • Business has menu items: ❌")
        print("   • Public endpoint accessible without auth: ✅" if any("Public Menu Endpoint (No Auth)" in r["test"] and r["success"] for r in self.test_results) else "   • Public endpoint accessible without auth: ❌")
        print("   • Returns only available items: ✅" if any("Public Menu Returns Available Only" in r["test"] and r["success"] for r in self.test_results) else "   • Returns only available items: ❌")
        print("   • Proper response format: ✅" if any("Public Menu Response Format" in r["test"] and r["success"] for r in self.test_results) else "   • Proper response format: ❌")
        
        print()
        print("🎯 CONCLUSION:")
        if success_rate >= 85:
            print("   Public Menu Endpoint is WORKING EXCELLENTLY")
        elif success_rate >= 70:
            print("   Public Menu Endpoint is WORKING with minor issues")
        else:
            print("   Public Menu Endpoint has CRITICAL ISSUES")

if __name__ == "__main__":
    tester = PublicMenuTester()
    tester.run_all_tests()