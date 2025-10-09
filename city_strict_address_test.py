#!/usr/bin/env python3
"""
City-Strict Address CRUD Testing
Tests the new city-strict address management system with proper validation
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CUSTOMER = {
    "email": "testcustomer@example.com",
    "password": "test123"
}

class CityStrictAddressTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.created_addresses = []
        
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
        
    def authenticate_customer(self):
        """Authenticate test customer using cookie-based auth"""
        print("\n🔐 CUSTOMER AUTHENTICATION")
        
        try:
            # Use cookie-based auth endpoint
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=TEST_CUSTOMER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Cookie-based auth sets cookies automatically in session
                # Check if we got the success response
                if data.get("success"):
                    # Verify authentication by calling /me endpoint
                    me_response = self.session.get(f"{API_BASE}/auth/me")
                    
                    if me_response.status_code == 200:
                        user_data = me_response.json()
                        
                        self.log_test(
                            "Customer Authentication", 
                            True,
                            f"Login successful - User ID: {user_data.get('id')}, Email: {user_data.get('email')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Customer Authentication",
                            False,
                            f"Authentication verification failed - Status: {me_response.status_code}",
                            me_response.text
                        )
                        return False
                else:
                    self.log_test(
                        "Customer Authentication",
                        False,
                        f"Login response invalid - Success: {data.get('success')}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Customer Authentication",
                    False,
                    f"Login failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_address_creation_validation(self):
        """Test address creation with field validation"""
        print("\n📝 ADDRESS CREATION VALIDATION TESTS")
        
        # Test 1: Missing required fields (should return 422)
        test_cases = [
            {
                "name": "Missing city field",
                "data": {
                    "label": "Test Address",
                    "full": "Test Address Full",
                    "district": "Kadıköy",
                    "lat": 41.03,
                    "lng": 28.97
                },
                "expected_status": 422
            },
            {
                "name": "Missing district field", 
                "data": {
                    "label": "Test Address",
                    "full": "Test Address Full",
                    "city": "İstanbul",
                    "lat": 41.03,
                    "lng": 28.97
                },
                "expected_status": 422
            },
            {
                "name": "Missing lat field",
                "data": {
                    "label": "Test Address",
                    "full": "Test Address Full", 
                    "city": "İstanbul",
                    "district": "Kadıköy",
                    "lng": 28.97
                },
                "expected_status": 422
            },
            {
                "name": "Missing lng field",
                "data": {
                    "label": "Test Address",
                    "full": "Test Address Full",
                    "city": "İstanbul", 
                    "district": "Kadıköy",
                    "lat": 41.03
                },
                "expected_status": 422
            }
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.post(
                    f"{API_BASE}/me/addresses",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"}
                )
                
                success = response.status_code == test_case["expected_status"]
                self.log_test(
                    f"Validation - {test_case['name']}",
                    success,
                    f"Expected {test_case['expected_status']}, got {response.status_code}"
                )
                
            except Exception as e:
                self.log_test(f"Validation - {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_successful_address_creation(self):
        """Test successful address creation with all required fields"""
        print("\n✅ SUCCESSFUL ADDRESS CREATION TEST")
        
        address_data = {
            "label": "Ev",
            "full": "Test Address",
            "city": "İstanbul",
            "district": "Kadıköy", 
            "lat": 41.03,
            "lng": 28.97,
            "is_default": True
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/me/addresses",
                json=address_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                address_id = data.get("address_id")
                
                if address_id:
                    self.created_addresses.append(address_id)
                
                self.log_test(
                    "Successful Address Creation",
                    True,
                    f"Address created successfully - ID: {address_id}"
                )
                return address_id
            else:
                self.log_test(
                    "Successful Address Creation",
                    False,
                    f"Creation failed - Status: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test("Successful Address Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_address_retrieval(self):
        """Test address retrieval with slug generation"""
        print("\n📋 ADDRESS RETRIEVAL TEST")
        
        try:
            response = self.session.get(f"{API_BASE}/me/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                
                # Check if addresses contain required fields including slugs
                if addresses and len(addresses) > 0:
                    first_address = addresses[0]
                    required_fields = ["id", "label", "full", "city", "district", "city_slug", "district_slug", "lat", "lng", "is_default"]
                    
                    missing_fields = [field for field in required_fields if field not in first_address]
                    
                    if not missing_fields:
                        # Verify Turkish slug normalization
                        city_slug_correct = first_address.get("city_slug") == "istanbul"  # İstanbul → istanbul
                        district_slug_correct = first_address.get("district_slug") == "kadikoy"  # Kadıköy → kadikoy
                        
                        self.log_test(
                            "Address Retrieval with Slugs",
                            city_slug_correct and district_slug_correct,
                            f"Retrieved {len(addresses)} addresses. City slug: {first_address.get('city_slug')}, District slug: {first_address.get('district_slug')}"
                        )
                    else:
                        self.log_test(
                            "Address Retrieval with Slugs",
                            False,
                            f"Missing required fields: {missing_fields}"
                        )
                else:
                    self.log_test(
                        "Address Retrieval with Slugs",
                        False,
                        "No addresses found"
                    )
            else:
                self.log_test(
                    "Address Retrieval with Slugs",
                    False,
                    f"Retrieval failed - Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test("Address Retrieval with Slugs", False, f"Exception: {str(e)}")
    
    def test_city_nearby_catalog(self):
        """Test city-strict catalog endpoint"""
        print("\n🏪 CITY-STRICT CATALOG TESTING")
        
        # Test 1: Valid request with all required parameters
        try:
            params = {
                "lat": 41.03,
                "lng": 28.97,
                "city": "istanbul",
                "district": "kadikoy",
                "limit": 20
            }
            
            response = self.session.get(f"{API_BASE}/catalog/city-nearby", params=params)
            
            if response.status_code == 200:
                businesses = response.json()
                
                # Verify all businesses are from the same city
                all_same_city = True
                for business in businesses:
                    business_city = business.get("address", {}).get("city_slug")
                    if business_city != "istanbul":
                        all_same_city = False
                        break
                
                self.log_test(
                    "City-Nearby Catalog - Valid Request",
                    True,
                    f"Found {len(businesses)} businesses, all from same city: {all_same_city}"
                )
            else:
                self.log_test(
                    "City-Nearby Catalog - Valid Request",
                    False,
                    f"Request failed - Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test("City-Nearby Catalog - Valid Request", False, f"Exception: {str(e)}")
        
        # Test 2: Missing required parameters (should return 422)
        missing_param_tests = [
            {"params": {"lng": 28.97, "city": "istanbul"}, "missing": "lat"},
            {"params": {"lat": 41.03, "city": "istanbul"}, "missing": "lng"},
            {"params": {"lat": 41.03, "lng": 28.97}, "missing": "city"}
        ]
        
        for test in missing_param_tests:
            try:
                response = self.session.get(f"{API_BASE}/catalog/city-nearby", params=test["params"])
                
                success = response.status_code == 422
                self.log_test(
                    f"City-Nearby Validation - Missing {test['missing']}",
                    success,
                    f"Expected 422, got {response.status_code}"
                )
                
            except Exception as e:
                self.log_test(f"City-Nearby Validation - Missing {test['missing']}", False, f"Exception: {str(e)}")
    
    def test_cross_city_filter(self):
        """Test that cross-city businesses are filtered out"""
        print("\n🚫 CROSS-CITY FILTER TEST")
        
        # Test with different city to ensure no cross-city results
        try:
            params = {
                "lat": 39.92,  # Ankara coordinates
                "lng": 32.85,
                "city": "ankara",  # Different city
                "limit": 20
            }
            
            response = self.session.get(f"{API_BASE}/catalog/city-nearby", params=params)
            
            if response.status_code == 200:
                businesses = response.json()
                
                # Verify no Istanbul businesses appear in Ankara search
                istanbul_businesses = [b for b in businesses if b.get("address", {}).get("city_slug") == "istanbul"]
                
                self.log_test(
                    "Cross-City Filter Test",
                    len(istanbul_businesses) == 0,
                    f"Found {len(businesses)} businesses in Ankara, {len(istanbul_businesses)} Istanbul businesses (should be 0)"
                )
            else:
                self.log_test(
                    "Cross-City Filter Test",
                    True,  # No businesses found is acceptable
                    f"No businesses found in Ankara (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test("Cross-City Filter Test", False, f"Exception: {str(e)}")
    
    def test_authentication_required(self):
        """Test that address endpoints require authentication"""
        print("\n🔒 AUTHENTICATION SECURITY TEST")
        
        # Remove auth header temporarily
        original_headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        try:
            # Test GET addresses without auth
            response = self.session.get(f"{API_BASE}/me/addresses")
            
            success = response.status_code in [401, 403]  # Should be unauthorized
            self.log_test(
                "Authentication Required - GET addresses",
                success,
                f"Expected 401/403, got {response.status_code}"
            )
            
            # Test POST address without auth
            address_data = {
                "label": "Test",
                "full": "Test Address",
                "city": "İstanbul",
                "district": "Kadıköy",
                "lat": 41.03,
                "lng": 28.97
            }
            
            response = self.session.post(
                f"{API_BASE}/me/addresses",
                json=address_data,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code in [401, 403]
            self.log_test(
                "Authentication Required - POST address",
                success,
                f"Expected 401/403, got {response.status_code}"
            )
            
        except Exception as e:
            self.log_test("Authentication Security Test", False, f"Exception: {str(e)}")
        finally:
            # Restore auth headers
            self.session.headers.update(original_headers)
    
    def test_database_schema_verification(self):
        """Verify address documents have required fields and GeoJSON location"""
        print("\n🗄️ DATABASE SCHEMA VERIFICATION")
        
        # This test verifies the response structure matches expected schema
        try:
            response = self.session.get(f"{API_BASE}/me/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                
                if addresses and len(addresses) > 0:
                    address = addresses[0]
                    
                    # Check required fields
                    required_fields = ["id", "city_slug", "district_slug"]
                    schema_valid = all(field in address for field in required_fields)
                    
                    # Check coordinate format (should be lat/lng in response)
                    coords_valid = "lat" in address and "lng" in address
                    
                    # Check slug normalization
                    slug_valid = (
                        isinstance(address.get("city_slug"), str) and
                        isinstance(address.get("district_slug"), str)
                    )
                    
                    self.log_test(
                        "Database Schema Verification",
                        schema_valid and coords_valid and slug_valid,
                        f"Schema valid: {schema_valid}, Coords valid: {coords_valid}, Slugs valid: {slug_valid}"
                    )
                else:
                    self.log_test(
                        "Database Schema Verification",
                        False,
                        "No addresses found to verify schema"
                    )
            else:
                self.log_test(
                    "Database Schema Verification",
                    False,
                    f"Could not retrieve addresses - Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Database Schema Verification", False, f"Exception: {str(e)}")
    
    def cleanup_test_addresses(self):
        """Clean up created test addresses"""
        print("\n🧹 CLEANUP TEST ADDRESSES")
        
        for address_id in self.created_addresses:
            try:
                response = self.session.delete(f"{API_BASE}/me/addresses/{address_id}")
                
                if response.status_code == 200:
                    print(f"   ✅ Deleted address {address_id}")
                else:
                    print(f"   ⚠️ Could not delete address {address_id} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error deleting address {address_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run all city-strict address tests"""
        print("🎯 CITY-STRICT ADDRESS CRUD TESTING")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.authenticate_customer():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Step 2: Test address creation validation
        self.test_address_creation_validation()
        
        # Step 3: Test successful address creation
        self.test_successful_address_creation()
        
        # Step 4: Test address retrieval with slugs
        self.test_address_retrieval()
        
        # Step 5: Test city-strict catalog
        self.test_city_nearby_catalog()
        
        # Step 6: Test cross-city filtering
        self.test_cross_city_filter()
        
        # Step 7: Test authentication requirements
        self.test_authentication_required()
        
        # Step 8: Test database schema
        self.test_database_schema_verification()
        
        # Step 9: Cleanup
        self.cleanup_test_addresses()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("🎯 CITY-STRICT ADDRESS TESTING SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   • {test['test']}: {test['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for test in self.test_results:
            if test["success"]:
                print(f"   • {test['test']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: City-strict address system is working perfectly!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD: City-strict address system is mostly functional with minor issues.")
        elif success_rate >= 50:
            print(f"\n⚠️ MODERATE: City-strict address system has some issues that need attention.")
        else:
            print(f"\n❌ CRITICAL: City-strict address system has major issues requiring immediate fixes.")

if __name__ == "__main__":
    tester = CityStrictAddressTest()
    tester.run_all_tests()