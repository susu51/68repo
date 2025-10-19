#!/usr/bin/env python3
"""
URGENT ADDRESS CREATION ERROR DEBUG TEST
Focus: User still reports "Adres ekleme hatası" despite API endpoint fixes
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testcustomer@example.com"
TEST_USER_PASSWORD = "test123"

class AddressDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, error=None):
        """Log test result with detailed information"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if error:
            print(f"   🚨 ERROR: {error}")
        print()

    def authenticate_user(self):
        """Step 1: Login as testcustomer@example.com/test123"""
        print("🔐 STEP 1: USER AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_data = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_result(
                    "User Authentication",
                    True,
                    f"Login successful - JWT token: {len(self.auth_token)} chars, User ID: {self.user_data.get('id')}, Role: {self.user_data.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "User Authentication", 
                    False,
                    f"Login failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("User Authentication", False, "Login request failed", e)
            return False

    def verify_token_validity(self):
        """Step 2: Verify JWT token validity via /me endpoint"""
        print("🔍 STEP 2: JWT TOKEN VALIDATION")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/me")
            
            if response.status_code == 200:
                user_info = response.json()
                self.log_result(
                    "JWT Token Validation",
                    True,
                    f"Token valid - User: {user_info.get('email')}, ID: {user_info.get('id')}, Role: {user_info.get('role')}"
                )
                return True
            else:
                self.log_result(
                    "JWT Token Validation",
                    False,
                    f"Token validation failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("JWT Token Validation", False, "Token validation request failed", e)
            return False

    def test_address_retrieval(self):
        """Step 3: Test existing address retrieval"""
        print("📍 STEP 3: ADDRESS RETRIEVAL TEST")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_result(
                    "Address Retrieval",
                    True,
                    f"Retrieved {len(addresses)} existing addresses successfully"
                )
                return True
            elif response.status_code == 403:
                self.log_result(
                    "Address Retrieval",
                    False,
                    "403 Forbidden - Authentication/authorization issue",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Address Retrieval",
                    False,
                    f"Address retrieval failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Address Retrieval", False, "Address retrieval request failed", e)
            return False

    def test_address_creation_complete_data(self):
        """Step 4: Test address creation with complete test data"""
        print("🏠 STEP 4: ADDRESS CREATION - COMPLETE DATA")
        print("=" * 50)
        
        test_address = {
            "label": "Debug Test Adres",
            "city": "İstanbul", 
            "district": "Kadıköy",
            "description": "Debug test address for error investigation",
            "lat": 40.9903,
            "lng": 29.0209
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=test_address)
            
            print(f"📤 Request URL: {BACKEND_URL}/user/addresses")
            print(f"📤 Request Headers: {dict(self.session.headers)}")
            print(f"📤 Request Data: {json.dumps(test_address, indent=2, ensure_ascii=False)}")
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"📥 Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"📥 Response Text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                self.log_result(
                    "Address Creation - Complete Data",
                    True,
                    f"Address created successfully - Status: {response.status_code}"
                )
                return True
            elif response.status_code == 422:
                self.log_result(
                    "Address Creation - Complete Data",
                    False,
                    f"422 Validation Error - Field validation failed",
                    response.text
                )
                return False
            elif response.status_code == 403:
                self.log_result(
                    "Address Creation - Complete Data",
                    False,
                    "403 Forbidden - Authentication/authorization issue",
                    response.text
                )
                return False
            else:
                self.log_result(
                    "Address Creation - Complete Data",
                    False,
                    f"Address creation failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Address Creation - Complete Data", False, "Address creation request failed", e)
            return False

    def test_field_validation_missing_fields(self):
        """Step 5: Test field validation with missing fields"""
        print("🔍 STEP 5: FIELD VALIDATION - MISSING FIELDS")
        print("=" * 50)
        
        test_cases = [
            {"name": "Missing Label", "data": {"city": "İstanbul", "district": "Kadıköy", "description": "Test", "lat": 40.9903, "lng": 29.0209}},
            {"name": "Missing City", "data": {"label": "Test", "district": "Kadıköy", "description": "Test", "lat": 40.9903, "lng": 29.0209}},
            {"name": "Missing District", "data": {"label": "Test", "city": "İstanbul", "description": "Test", "lat": 40.9903, "lng": 29.0209}},
            {"name": "Missing Description", "data": {"label": "Test", "city": "İstanbul", "district": "Kadıköy", "lat": 40.9903, "lng": 29.0209}},
            {"name": "Missing Coordinates", "data": {"label": "Test", "city": "İstanbul", "district": "Kadıköy", "description": "Test"}},
            {"name": "Missing Lat Only", "data": {"label": "Test", "city": "İstanbul", "district": "Kadıköy", "description": "Test", "lng": 29.0209}},
            {"name": "Missing Lng Only", "data": {"label": "Test", "city": "İstanbul", "district": "Kadıköy", "description": "Test", "lat": 40.9903}},
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=test_case["data"])
                
                if response.status_code == 422:
                    try:
                        error_data = response.json()
                        self.log_result(
                            f"Field Validation - {test_case['name']}",
                            True,
                            f"Validation correctly failed with 422 - {error_data}"
                        )
                    except:
                        self.log_result(
                            f"Field Validation - {test_case['name']}",
                            True,
                            f"Validation correctly failed with 422 - {response.text}"
                        )
                elif response.status_code in [200, 201]:
                    self.log_result(
                        f"Field Validation - {test_case['name']}",
                        True,
                        f"Field is optional - Address created successfully"
                    )
                else:
                    self.log_result(
                        f"Field Validation - {test_case['name']}",
                        False,
                        f"Unexpected response - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(f"Field Validation - {test_case['name']}", False, "Request failed", e)

    def test_coordinate_validation(self):
        """Step 6: Test coordinate validation"""
        print("🌍 STEP 6: COORDINATE VALIDATION")
        print("=" * 50)
        
        coordinate_tests = [
            {"name": "Valid Istanbul Coordinates", "lat": 41.0082, "lng": 28.9784, "should_pass": True},
            {"name": "Valid Kadıköy Coordinates", "lat": 40.9903, "lng": 29.0209, "should_pass": True},
            {"name": "Invalid Lat (Out of Range)", "lat": 91.0, "lng": 29.0209, "should_pass": False},
            {"name": "Invalid Lng (Out of Range)", "lat": 40.9903, "lng": 181.0, "should_pass": False},
            {"name": "Zero Coordinates", "lat": 0.0, "lng": 0.0, "should_pass": True},
            {"name": "Negative Coordinates", "lat": -40.9903, "lng": -29.0209, "should_pass": True},
        ]
        
        for test in coordinate_tests:
            test_address = {
                "label": f"Coordinate Test - {test['name']}",
                "city": "İstanbul",
                "district": "Test",
                "description": "Coordinate validation test",
                "lat": test["lat"],
                "lng": test["lng"]
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=test_address)
                
                if test["should_pass"]:
                    if response.status_code in [200, 201]:
                        self.log_result(
                            f"Coordinate Validation - {test['name']}",
                            True,
                            "Valid coordinates accepted"
                        )
                    else:
                        self.log_result(
                            f"Coordinate Validation - {test['name']}",
                            False,
                            f"Valid coordinates rejected - Status: {response.status_code}",
                            response.text
                        )
                else:
                    if response.status_code == 422:
                        self.log_result(
                            f"Coordinate Validation - {test['name']}",
                            True,
                            "Invalid coordinates correctly rejected"
                        )
                    else:
                        self.log_result(
                            f"Coordinate Validation - {test['name']}",
                            False,
                            f"Invalid coordinates not rejected - Status: {response.status_code}",
                            response.text
                        )
                        
            except Exception as e:
                self.log_result(f"Coordinate Validation - {test['name']}", False, "Request failed", e)

    def test_turkish_city_validation(self):
        """Step 7: Test Turkish city/district validation"""
        print("🇹🇷 STEP 7: TURKISH CITY/DISTRICT VALIDATION")
        print("=" * 50)
        
        city_tests = [
            {"city": "İstanbul", "district": "Kadıköy", "should_pass": True},
            {"city": "Ankara", "district": "Çankaya", "should_pass": True},
            {"city": "İzmir", "district": "Konak", "should_pass": True},
            {"city": "InvalidCity", "district": "InvalidDistrict", "should_pass": True},  # Assuming no strict validation
            {"city": "", "district": "Kadıköy", "should_pass": False},
            {"city": "İstanbul", "district": "", "should_pass": False},
        ]
        
        for test in city_tests:
            test_address = {
                "label": f"City Test - {test['city']}/{test['district']}",
                "city": test["city"],
                "district": test["district"],
                "description": "City validation test",
                "lat": 40.9903,
                "lng": 29.0209
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=test_address)
                
                if test["should_pass"]:
                    if response.status_code in [200, 201]:
                        self.log_result(
                            f"City Validation - {test['city']}/{test['district']}",
                            True,
                            "City/district accepted"
                        )
                    else:
                        self.log_result(
                            f"City Validation - {test['city']}/{test['district']}",
                            False,
                            f"Valid city/district rejected - Status: {response.status_code}",
                            response.text
                        )
                else:
                    if response.status_code == 422:
                        self.log_result(
                            f"City Validation - {test['city']}/{test['district']}",
                            True,
                            "Invalid city/district correctly rejected"
                        )
                    else:
                        self.log_result(
                            f"City Validation - {test['city']}/{test['district']}",
                            False,
                            f"Invalid city/district not rejected - Status: {response.status_code}",
                            response.text
                        )
                        
            except Exception as e:
                self.log_result(f"City Validation - {test['city']}/{test['district']}", False, "Request failed", e)

    def run_comprehensive_debug(self):
        """Run all debug tests"""
        print("🚨 URGENT ADDRESS CREATION ERROR DEBUG")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Step 1: Authentication
        if not self.authenticate_user():
            print("❌ CRITICAL: Authentication failed - cannot proceed with address tests")
            return
        
        # Step 2: Token validation
        if not self.verify_token_validity():
            print("❌ CRITICAL: Token validation failed - authentication issue")
            return
        
        # Step 3: Address retrieval test
        self.test_address_retrieval()
        
        # Step 4: Address creation with complete data
        self.test_address_creation_complete_data()
        
        # Step 5: Field validation tests
        self.test_field_validation_missing_fields()
        
        # Step 6: Coordinate validation
        self.test_coordinate_validation()
        
        # Step 7: Turkish city validation
        self.test_turkish_city_validation()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🔍 ADDRESS CREATION DEBUG SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical failures
        critical_failures = [r for r in self.test_results if not r["success"] and "Authentication" in r["test"]]
        if critical_failures:
            print("🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   ❌ {failure['test']}: {failure['error']}")
            print()
        
        # Address creation failures
        address_failures = [r for r in self.test_results if not r["success"] and "Address Creation" in r["test"]]
        if address_failures:
            print("🏠 ADDRESS CREATION FAILURES:")
            for failure in address_failures:
                print(f"   ❌ {failure['test']}: {failure['error']}")
            print()
        
        # Validation issues
        validation_failures = [r for r in self.test_results if not r["success"] and "Validation" in r["test"]]
        if validation_failures:
            print("🔍 VALIDATION ISSUES:")
            for failure in validation_failures:
                print(f"   ❌ {failure['test']}: {failure['error']}")
            print()
        
        print("=" * 60)
        
        # Save detailed results to file
        with open("/app/address_debug_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed results saved to: /app/address_debug_results.json")

if __name__ == "__main__":
    tester = AddressDebugTester()
    tester.run_comprehensive_debug()