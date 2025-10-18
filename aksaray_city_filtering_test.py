#!/usr/bin/env python3
"""
Aksaray City Filtering Backend Test
Tests the fixed Aksaray city filtering in business endpoints
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://order-flow-debug.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AksarayCityFilteringTest:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
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

    def test_basic_business_listing(self):
        """Test 1: Basic Business Listing - GET /api/businesses"""
        try:
            response = requests.get(f"{API_BASE}/businesses", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                if isinstance(businesses, list):
                    self.log_test(
                        "Basic Business Listing",
                        True,
                        f"Successfully retrieved {len(businesses)} businesses from businesses collection"
                    )
                    return businesses
                else:
                    self.log_test(
                        "Basic Business Listing",
                        False,
                        "Response is not a list",
                        f"Expected list, got {type(businesses)}"
                    )
            else:
                self.log_test(
                    "Basic Business Listing",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Basic Business Listing",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_aksaray_case_sensitive(self):
        """Test 2: Aksaray City Filtering - Case Sensitive"""
        try:
            response = requests.get(f"{API_BASE}/businesses?city=Aksaray", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "Aksaray Case Sensitive Filtering",
                    True,
                    f"Successfully retrieved {len(businesses)} businesses for 'Aksaray'"
                )
                return businesses
            else:
                self.log_test(
                    "Aksaray Case Sensitive Filtering",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Aksaray Case Sensitive Filtering",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_aksaray_lowercase(self):
        """Test 3: Aksaray City Filtering - Lowercase"""
        try:
            response = requests.get(f"{API_BASE}/businesses?city=aksaray", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "Aksaray Lowercase Filtering",
                    True,
                    f"Successfully retrieved {len(businesses)} businesses for 'aksaray'"
                )
                return businesses
            else:
                self.log_test(
                    "Aksaray Lowercase Filtering",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Aksaray Lowercase Filtering",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_aksaray_uppercase(self):
        """Test 4: Aksaray City Filtering - Uppercase"""
        try:
            response = requests.get(f"{API_BASE}/businesses?city=AKSARAY", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "Aksaray Uppercase Filtering",
                    True,
                    f"Successfully retrieved {len(businesses)} businesses for 'AKSARAY'"
                )
                return businesses
            else:
                self.log_test(
                    "Aksaray Uppercase Filtering",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Aksaray Uppercase Filtering",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_aksaray_mixed_case(self):
        """Test 5: Aksaray City Filtering - Mixed Case"""
        try:
            response = requests.get(f"{API_BASE}/businesses?city=AkSaRaY", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "Aksaray Mixed Case Filtering",
                    True,
                    f"Successfully retrieved {len(businesses)} businesses for 'AkSaRaY'"
                )
                return businesses
            else:
                self.log_test(
                    "Aksaray Mixed Case Filtering",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Aksaray Mixed Case Filtering",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_restaurants_aksaray_case_sensitive(self):
        """Test 6: Restaurant Endpoint - Aksaray Case Sensitive"""
        try:
            response = requests.get(f"{API_BASE}/restaurants?city=Aksaray", timeout=10)
            
            if response.status_code == 200:
                restaurants = response.json()
                self.log_test(
                    "Restaurants Aksaray Case Sensitive",
                    True,
                    f"Successfully retrieved {len(restaurants)} restaurants for 'Aksaray'"
                )
                return restaurants
            else:
                self.log_test(
                    "Restaurants Aksaray Case Sensitive",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Restaurants Aksaray Case Sensitive",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_restaurants_aksaray_lowercase(self):
        """Test 7: Restaurant Endpoint - Aksaray Lowercase"""
        try:
            response = requests.get(f"{API_BASE}/restaurants?city=aksaray", timeout=10)
            
            if response.status_code == 200:
                restaurants = response.json()
                self.log_test(
                    "Restaurants Aksaray Lowercase",
                    True,
                    f"Successfully retrieved {len(restaurants)} restaurants for 'aksaray'"
                )
                return restaurants
            else:
                self.log_test(
                    "Restaurants Aksaray Lowercase",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Restaurants Aksaray Lowercase",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_address_search_aksaray(self):
        """Test 8: Address Search with Aksaray"""
        try:
            # Test if businesses with Aksaray in address are found
            response = requests.get(f"{API_BASE}/businesses?city=Aksaray", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                aksaray_in_address = []
                for business in businesses:
                    if business.get('address') and 'aksaray' in business['address'].lower():
                        aksaray_in_address.append(business)
                
                self.log_test(
                    "Address Search with Aksaray",
                    True,
                    f"Found {len(aksaray_in_address)} businesses with Aksaray in address out of {len(businesses)} total"
                )
                return aksaray_in_address
            else:
                self.log_test(
                    "Address Search with Aksaray",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Address Search with Aksaray",
                False,
                "Request failed",
                str(e)
            )
        return []

    def test_collection_verification(self):
        """Test 9: Verify businesses collection is being queried (not users)"""
        try:
            # Test that we get business-specific fields
            response = requests.get(f"{API_BASE}/businesses", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                if businesses:
                    # Check if we have business-specific fields
                    first_business = businesses[0]
                    business_fields = ['name', 'category', 'description', 'rating']
                    has_business_fields = any(field in first_business for field in business_fields)
                    
                    # Check if we don't have user-specific fields that shouldn't be there
                    user_fields = ['password_hash', 'role']
                    has_user_fields = any(field in first_business for field in user_fields)
                    
                    if has_business_fields and not has_user_fields:
                        self.log_test(
                            "Collection Verification",
                            True,
                            f"Correctly querying businesses collection - found business fields: {list(first_business.keys())}"
                        )
                    else:
                        self.log_test(
                            "Collection Verification",
                            False,
                            "Response structure suggests wrong collection",
                            f"Fields found: {list(first_business.keys())}"
                        )
                else:
                    self.log_test(
                        "Collection Verification",
                        True,
                        "Empty businesses collection - no data to verify structure"
                    )
            else:
                self.log_test(
                    "Collection Verification",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:200]
                )
        except Exception as e:
            self.log_test(
                "Collection Verification",
                False,
                "Request failed",
                str(e)
            )

    def test_case_insensitive_consistency(self):
        """Test 10: Verify case-insensitive filtering returns consistent results"""
        try:
            # Get results for different cases
            cases = ['Aksaray', 'aksaray', 'AKSARAY', 'AkSaRaY']
            results = {}
            
            for case in cases:
                response = requests.get(f"{API_BASE}/businesses?city={case}", timeout=10)
                if response.status_code == 200:
                    results[case] = len(response.json())
                else:
                    results[case] = -1  # Error indicator
            
            # Check if all cases return the same number of results
            result_counts = list(results.values())
            if len(set(result_counts)) == 1 and result_counts[0] >= 0:
                self.log_test(
                    "Case-Insensitive Consistency",
                    True,
                    f"All case variations return same count: {results}"
                )
            else:
                self.log_test(
                    "Case-Insensitive Consistency",
                    False,
                    "Different case variations return different results",
                    f"Results: {results}"
                )
        except Exception as e:
            self.log_test(
                "Case-Insensitive Consistency",
                False,
                "Request failed",
                str(e)
            )

    def test_no_500_errors(self):
        """Test 11: Verify no 500 errors on all endpoints"""
        endpoints = [
            "/businesses",
            "/businesses?city=Aksaray",
            "/businesses?city=aksaray",
            "/restaurants",
            "/restaurants?city=Aksaray",
            "/restaurants?city=aksaray"
        ]
        
        errors_found = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
                if response.status_code == 500:
                    errors_found.append(f"{endpoint}: {response.text[:100]}")
            except Exception as e:
                errors_found.append(f"{endpoint}: {str(e)}")
        
        if not errors_found:
            self.log_test(
                "No 500 Errors Check",
                True,
                f"All {len(endpoints)} endpoints returned non-500 status codes"
            )
        else:
            self.log_test(
                "No 500 Errors Check",
                False,
                f"Found {len(errors_found)} 500 errors",
                "; ".join(errors_found)
            )

    def run_all_tests(self):
        """Run all Aksaray city filtering tests"""
        print("🧪 AKSARAY CITY FILTERING BACKEND TEST")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Run all tests
        self.test_basic_business_listing()
        self.test_aksaray_case_sensitive()
        self.test_aksaray_lowercase()
        self.test_aksaray_uppercase()
        self.test_aksaray_mixed_case()
        self.test_restaurants_aksaray_case_sensitive()
        self.test_restaurants_aksaray_lowercase()
        self.test_address_search_aksaray()
        self.test_collection_verification()
        self.test_case_insensitive_consistency()
        self.test_no_500_errors()
        
        # Print summary
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print()
        
        if self.failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
            print()
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['test'].lower() for keyword in ['basic', 'collection', '500']):
                critical_issues.append(result['test'])
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  - {issue}")
            print()
        
        print("✅ AKSARAY CITY FILTERING TEST COMPLETE")
        return self.passed_tests, self.failed_tests, self.test_results

if __name__ == "__main__":
    tester = AksarayCityFilteringTest()
    passed, failed, results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if failed == 0 else 1)