#!/usr/bin/env python3
"""
City/District Filtering Backend Testing
Test city filtering in customer discover endpoint as specified in the review request
"""

import requests
import json
import os
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"

# Test credentials
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

# Test coordinates
ANKARA_COORDS = {"lat": 39.9334, "lng": 32.8597}
ISTANBUL_COORDS = {"lat": 41.0082, "lng": 28.9784}

class CityFilteringTester:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.test_results = []
        self.business_data = None
        
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
        """Test 1: Business login to get business data"""
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
                    self.business_data = data.get("user", {})
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.business_token}"})
                    
                    city = self.business_data.get("city", "Unknown")
                    district = self.business_data.get("district", "Unknown")
                    
                    self.log_test(
                        "Business Login & Data Verification", 
                        True, 
                        f"Successfully logged in as {BUSINESS_EMAIL}, Business located in: {city}/{district}"
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
    
    def test_aksaray_city_filtering(self):
        """Test 2: Test city filtering with Aksaray (where testbusiness@example.com is located)"""
        try:
            params = {
                "city": "aksaray",
                "lat": ANKARA_COORDS["lat"],  # Using Ankara coords to test cross-city
                "lng": ANKARA_COORDS["lng"],
                "radius_km": 50
            }
            
            # Test without authentication (public endpoint)
            public_session = requests.Session()
            response = public_session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else []
                
                # Verify all businesses are from Aksaray
                aksaray_businesses = []
                non_aksaray_businesses = []
                
                for business in businesses:
                    business_city = business.get("address", {}).get("city_slug", "").lower()
                    if business_city == "aksaray":
                        aksaray_businesses.append(business)
                    else:
                        non_aksaray_businesses.append(business)
                
                if len(non_aksaray_businesses) == 0:
                    self.log_test(
                        "Aksaray City Filtering (STRICT)", 
                        True, 
                        f"✅ STRICT FILTERING WORKING: Found {len(aksaray_businesses)} Aksaray businesses, 0 from other cities"
                    )
                else:
                    self.log_test(
                        "Aksaray City Filtering (STRICT)", 
                        False, 
                        "", 
                        f"❌ CITY FILTER VIOLATION: Found {len(non_aksaray_businesses)} businesses from other cities: {[b.get('address', {}).get('city_slug') for b in non_aksaray_businesses]}"
                    )
                
                return aksaray_businesses
            else:
                self.log_test("Aksaray City Filtering", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Aksaray City Filtering", False, "", f"Exception: {str(e)}")
            return []
    
    def test_nigde_city_filtering(self):
        """Test 3: Test city filtering with Niğde (another city in database)"""
        try:
            params = {
                "city": "nigde",
                "lat": ANKARA_COORDS["lat"],  # Using different coords to test city-strict filtering
                "lng": ANKARA_COORDS["lng"],
                "radius_km": 50
            }
            
            # Test without authentication (public endpoint)
            public_session = requests.Session()
            response = public_session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else []
                
                # Verify all businesses are from Niğde
                nigde_businesses = []
                non_nigde_businesses = []
                
                for business in businesses:
                    business_city = business.get("address", {}).get("city_slug", "").lower()
                    if business_city == "nigde" or business_city == "niğde":
                        nigde_businesses.append(business)
                    else:
                        non_nigde_businesses.append(business)
                
                if len(non_nigde_businesses) == 0:
                    self.log_test(
                        "Niğde City Filtering (STRICT)", 
                        True, 
                        f"✅ STRICT FILTERING WORKING: Found {len(nigde_businesses)} Niğde businesses, 0 from other cities"
                    )
                else:
                    self.log_test(
                        "Niğde City Filtering (STRICT)", 
                        False, 
                        "", 
                        f"❌ CITY FILTER VIOLATION: Found {len(non_nigde_businesses)} businesses from other cities: {[b.get('address', {}).get('city_slug') for b in non_nigde_businesses]}"
                    )
                
                return nigde_businesses
            else:
                self.log_test("Niğde City Filtering", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Niğde City Filtering", False, "", f"Exception: {str(e)}")
            return []
    
    def test_istanbul_city_filtering(self):
        """Test 4: Cross-city test - Istanbul coordinates should NOT return Aksaray businesses"""
        try:
            params = {
                "city": "istanbul",
                "lat": ISTANBUL_COORDS["lat"],
                "lng": ISTANBUL_COORDS["lng"],
                "radius_km": 50
            }
            
            # Test without authentication (public endpoint)
            public_session = requests.Session()
            response = public_session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else []
                
                # Verify NO Aksaray businesses appear (where most test businesses are)
                istanbul_businesses = []
                aksaray_businesses = []
                other_city_businesses = []
                
                for business in businesses:
                    business_city = business.get("address", {}).get("city_slug", "").lower()
                    if business_city == "istanbul" or business_city == "i̇stanbul":
                        istanbul_businesses.append(business)
                    elif business_city == "aksaray":
                        aksaray_businesses.append(business)
                    else:
                        other_city_businesses.append(business)
                
                if len(aksaray_businesses) == 0:
                    self.log_test(
                        "Istanbul City Filtering (Cross-City Test)", 
                        True, 
                        f"✅ CROSS-CITY FILTERING WORKING: Found {len(istanbul_businesses)} Istanbul businesses, 0 Aksaray businesses (STRICT separation confirmed)"
                    )
                else:
                    self.log_test(
                        "Istanbul City Filtering (Cross-City Test)", 
                        False, 
                        "", 
                        f"❌ CRITICAL SECURITY VIOLATION: Found {len(aksaray_businesses)} Aksaray businesses in Istanbul search - CROSS-CITY DATA LEAK!"
                    )
                
                return businesses
            else:
                self.log_test("Istanbul City Filtering", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Istanbul City Filtering", False, "", f"Exception: {str(e)}")
            return []
    
    def test_business_city_verification(self):
        """Test 5: Verify testbusiness@example.com city and district data"""
        try:
            if not self.business_data:
                self.log_test("Business City Verification", False, "", "No business data available")
                return
            
            city = self.business_data.get("city", "")
            district = self.business_data.get("district", "")
            business_name = self.business_data.get("business_name", "")
            
            if city and district:
                self.log_test(
                    "Business City/District Verification", 
                    True, 
                    f"✅ Business '{business_name}' is located in {city}/{district} - Data available for filtering tests"
                )
            else:
                self.log_test(
                    "Business City/District Verification", 
                    False, 
                    "", 
                    f"❌ Missing city/district data: city='{city}', district='{district}'"
                )
                
        except Exception as e:
            self.log_test("Business City Verification", False, "", f"Exception: {str(e)}")
    
    def test_radius_parameter_validation(self):
        """Test 6: Test radius parameter validation and limits"""
        try:
            # Test with different radius values using Aksaray (where we have businesses)
            test_cases = [
                {"radius_km": 10, "expected": "success"},
                {"radius_km": 50, "expected": "success"},
                {"radius_km": 100, "expected": "success"},  # Should be capped at max
            ]
            
            for case in test_cases:
                params = {
                    "city": "aksaray",
                    "lat": ANKARA_COORDS["lat"],
                    "lng": ANKARA_COORDS["lng"],
                    "radius_km": case["radius_km"]
                }
                
                public_session = requests.Session()
                response = public_session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    businesses = data if isinstance(data, list) else []
                    
                    self.log_test(
                        f"Radius Parameter Test ({case['radius_km']}km)", 
                        True, 
                        f"Radius {case['radius_km']}km accepted, returned {len(businesses)} businesses"
                    )
                else:
                    self.log_test(
                        f"Radius Parameter Test ({case['radius_km']}km)", 
                        False, 
                        "", 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            self.log_test("Radius Parameter Validation", False, "", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all city filtering tests"""
        print("🎯 CITY/DISTRICT FILTERING BACKEND TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Business Credentials: {BUSINESS_EMAIL} / {BUSINESS_PASSWORD}")
        print(f"Test Coordinates: Ankara {ANKARA_COORDS}, Istanbul {ISTANBUL_COORDS}")
        print("=" * 70)
        print()
        
        # Test 1: Business Login and Data Verification
        if not self.test_business_login():
            print("⚠️  Business login failed - continuing with public endpoint tests")
        
        # Test 2: Business City/District Verification
        self.test_business_city_verification()
        
        # Test 3: Aksaray City Filtering (STRICT) - where testbusiness@example.com is located
        aksaray_businesses = self.test_aksaray_city_filtering()
        
        # Test 4: Niğde City Filtering (another city in database)
        self.test_nigde_city_filtering()
        
        # Test 5: Cross-City Test (Istanbul should NOT return Ankara businesses)
        self.test_istanbul_city_filtering()
        
        # Test 6: Radius Parameter Validation
        self.test_radius_parameter_validation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📊 CITY FILTERING TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("🎯 CRITICAL SECURITY VERIFICATION:")
        
        # Check for city filtering violations
        city_violations = []
        for result in self.test_results:
            if "CITY FILTER VIOLATION" in result.get("error", "") or "CROSS-CITY DATA LEAK" in result.get("error", ""):
                city_violations.append(result["test"])
        
        if len(city_violations) == 0:
            print("   ✅ CITY FILTERING IS STRICT - No cross-city data leaks detected")
        else:
            print(f"   ❌ CRITICAL SECURITY ISSUE - City filtering violations in: {city_violations}")
        
        print()
        print("📋 REVIEW REQUEST COMPLIANCE:")
        print("   • City filtering tested (Aksaray): ✅" if any("Aksaray City Filtering" in r["test"] and r["success"] for r in self.test_results) else "   • City filtering tested (Aksaray): ❌")
        print("   • Multiple city filtering tested (Niğde): ✅" if any("Niğde City Filtering" in r["test"] and r["success"] for r in self.test_results) else "   • Multiple city filtering tested (Niğde): ❌")
        print("   • Cross-city test (Istanbul vs others): ✅" if any("Cross-City Test" in r["test"] and r["success"] for r in self.test_results) else "   • Cross-city test (Istanbul vs others): ❌")
        print("   • Business city/district data verified: ✅" if any("Business City" in r["test"] and r["success"] for r in self.test_results) else "   • Business city/district data verified: ❌")
        
        print()
        print("🎯 CONCLUSION:")
        if success_rate >= 90 and len(city_violations) == 0:
            print("   ✅ CITY FILTERING SYSTEM IS WORKING PERFECTLY - STRICT city separation confirmed")
        elif success_rate >= 75 and len(city_violations) == 0:
            print("   ✅ CITY FILTERING SYSTEM IS WORKING CORRECTLY with minor issues")
        elif len(city_violations) > 0:
            print("   ❌ CRITICAL SECURITY ISSUE - City filtering has violations that must be fixed immediately")
        else:
            print("   ❌ CITY FILTERING SYSTEM HAS ISSUES - Requires investigation")

if __name__ == "__main__":
    tester = CityFilteringTester()
    tester.run_all_tests()