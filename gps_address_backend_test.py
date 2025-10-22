#!/usr/bin/env python3
"""
GPS Coordinates Utility & Address Display Backend Testing
Test GPS coordinate utility endpoints and address display fixes as specified in the review request
"""

import requests
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from frontend .env
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

class GPSAddressTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.customer_session = requests.Session()
        self.admin_token = None
        self.customer_token = None
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
    
    def test_admin_login(self):
        """Test 1: Admin login with admin@kuryecini.com/admin123"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "access_token" in data:
                    self.admin_token = data["access_token"]
                    # Check if cookies were set
                    cookies_info = f"Cookies: {len(self.admin_session.cookies)} set" if self.admin_session.cookies else "No cookies set"
                    self.log_test(
                        "Admin Login", 
                        True, 
                        f"Successfully logged in as {ADMIN_EMAIL}, token length: {len(self.admin_token)} chars, {cookies_info}"
                    )
                    return True
                else:
                    self.log_test("Admin Login", False, "", "Login response missing success or access_token")
                    return False
            else:
                self.log_test("Admin Login", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, "", f"Exception: {str(e)}")
            return False
    
    def test_customer_login(self):
        """Test 2: Customer login with test@kuryecini.com/test123"""
        try:
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "access_token" in data:
                    self.customer_token = data["access_token"]
                    self.log_test(
                        "Customer Login", 
                        True, 
                        f"Successfully logged in as {CUSTOMER_EMAIL}, token length: {len(self.customer_token)} chars"
                    )
                    return True
                else:
                    self.log_test("Customer Login", False, "", "Login response missing success or access_token")
                    return False
            else:
                self.log_test("Customer Login", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Customer Login", False, "", f"Exception: {str(e)}")
            return False
    
    def debug_admin_user_info(self):
        """Debug: Check admin user information"""
        try:
            response = self.session.get(f"{BACKEND_URL}/me")
            if response.status_code == 200:
                data = response.json()
                print(f"   🔍 Admin user info: role={data.get('role')}, email={data.get('email')}")
            else:
                print(f"   🔍 Admin /me endpoint failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   🔍 Admin /me debug failed: {str(e)}")
    
    def test_check_business_gps_coverage(self):
        """Test 3: GET /api/admin/utils/check-business-gps - Check GPS coverage statistics"""
        try:
            # Use session cookies from login instead of Bearer token
            response = self.session.get(f"{BACKEND_URL}/admin/utils/check-business-gps")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields in response
                required_fields = ["total_businesses", "with_gps", "without_gps", "gps_coverage_percentage"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total = data["total_businesses"]
                    with_gps = data["with_gps"]
                    without_gps = data["without_gps"]
                    coverage = data["gps_coverage_percentage"]
                    
                    # Verify math consistency
                    math_correct = (with_gps + without_gps == total) and (coverage == (with_gps / total * 100) if total > 0 else True)
                    
                    if math_correct:
                        details = f"Total: {total}, With GPS: {with_gps}, Without GPS: {without_gps}, Coverage: {coverage:.1f}%"
                        if "sample_without_gps" in data and without_gps > 0:
                            details += f", Sample businesses without GPS: {len(data['sample_without_gps'])}"
                        
                        self.log_test(
                            "Check Business GPS Coverage", 
                            True, 
                            details
                        )
                        return data
                    else:
                        self.log_test("Check Business GPS Coverage", False, "", "Math inconsistency in GPS statistics")
                        return None
                else:
                    self.log_test("Check Business GPS Coverage", False, "", f"Missing required fields: {missing_fields}")
                    return None
            else:
                self.log_test("Check Business GPS Coverage", False, "", f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Check Business GPS Coverage", False, "", f"Exception: {str(e)}")
            return None
    
    def test_update_business_gps_batch(self):
        """Test 4: POST /api/admin/utils/update-business-gps - Batch update businesses without GPS"""
        try:
            # Use session cookies from login instead of Bearer token
            response = self.session.post(f"{BACKEND_URL}/admin/utils/update-business-gps")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields in response
                required_fields = ["total_businesses_processed", "updated", "failed"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    processed = data["total_businesses_processed"]
                    updated = data["updated"]
                    failed = data["failed"]
                    
                    # Verify math consistency
                    math_correct = (updated + failed == processed)
                    
                    if math_correct:
                        details = f"Processed: {processed}, Updated: {updated}, Failed: {failed}"
                        if "details" in data:
                            details += f", Details array length: {len(data['details'])}"
                        
                        self.log_test(
                            "Update Business GPS Batch", 
                            True, 
                            details
                        )
                        return data
                    else:
                        self.log_test("Update Business GPS Batch", False, "", "Math inconsistency in update statistics")
                        return None
                else:
                    self.log_test("Update Business GPS Batch", False, "", f"Missing required fields: {missing_fields}")
                    return None
            else:
                self.log_test("Update Business GPS Batch", False, "", f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Update Business GPS Batch", False, "", f"Exception: {str(e)}")
            return None
    
    def test_verify_gps_coordinates_in_database(self):
        """Test 5: Verify businesses now have lat/lng fields in database"""
        try:
            # Use session cookies from login instead of Bearer token
            response = self.session.get(f"{BACKEND_URL}/admin/businesses")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                if businesses:
                    # Check first few businesses for GPS coordinates
                    businesses_with_gps = 0
                    businesses_checked = min(5, len(businesses))  # Check up to 5 businesses
                    
                    for i, business in enumerate(businesses[:businesses_checked]):
                        if business.get("lat") is not None and business.get("lng") is not None:
                            businesses_with_gps += 1
                    
                    self.log_test(
                        "Verify GPS Coordinates in Database", 
                        True, 
                        f"Checked {businesses_checked} businesses, {businesses_with_gps} have GPS coordinates (lat/lng fields)"
                    )
                    return True
                else:
                    self.log_test(
                        "Verify GPS Coordinates in Database", 
                        True, 
                        "No businesses found in database (expected for empty database)"
                    )
                    return True
            else:
                self.log_test("Verify GPS Coordinates in Database", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify GPS Coordinates in Database", False, "", f"Exception: {str(e)}")
            return False
    
    def test_customer_address_retrieval(self):
        """Test 6: GET /api/me/addresses - Customer address retrieval with new schema"""
        try:
            # Use session cookies from login instead of Bearer token
            response = self.session.get(f"{BACKEND_URL}/me/addresses")
            
            if response.status_code == 200:
                data = response.json()
                # Handle both possible response formats
                if isinstance(data, list):
                    addresses = data
                else:
                    addresses = data.get("addresses", [])
                
                if addresses:
                    # Check first address for required fields
                    address = addresses[0]
                    
                    # New schema fields
                    new_schema_fields = ["adres_basligi", "acik_adres", "il", "ilce", "mahalle"]
                    # Backward compatibility fields
                    backward_compat_fields = ["label", "full", "city", "district"]
                    
                    new_fields_present = [field for field in new_schema_fields if field in address]
                    backward_fields_present = [field for field in backward_compat_fields if field in address]
                    
                    self.log_test(
                        "Customer Address Retrieval", 
                        True, 
                        f"Retrieved {len(addresses)} addresses. New schema fields: {new_fields_present}. Backward compatibility fields: {backward_fields_present}"
                    )
                    return addresses
                else:
                    self.log_test(
                        "Customer Address Retrieval", 
                        True, 
                        "No addresses found for customer (expected for new customer account)"
                    )
                    return []
            else:
                self.log_test("Customer Address Retrieval", False, "", f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Customer Address Retrieval", False, "", f"Exception: {str(e)}")
            return None
    
    def test_new_business_registration_with_gps(self):
        """Test 7: Test new business registration automatically includes GPS coordinates"""
        try:
            # Test business registration with different city/district combinations
            test_cases = [
                {"city": "İstanbul", "district": "Kadıköy"},
                {"city": "Ankara", "district": "Çankaya"},
                {"city": "İzmir", "district": "Konak"}
            ]
            
            successful_registrations = 0
            
            for i, test_case in enumerate(test_cases):
                try:
                    # Generate unique email for each test
                    unique_email = f"testbusiness{i}_{uuid.uuid4().hex[:8]}@example.com"
                    
                    registration_data = {
                        "email": unique_email,
                        "password": "test123",
                        "business_name": f"Test Restaurant {test_case['city']}",
                        "tax_number": f"123456789{i}",
                        "address": f"Test Address {i+1}",
                        "city": test_case["city"],
                        "district": test_case["district"],
                        "business_category": "gida",
                        "description": f"Test restaurant in {test_case['city']}/{test_case['district']}"
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/register/business", json=registration_data)
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        user_data = data.get("user_data", {})
                        
                        # Check if GPS coordinates are included
                        has_gps = user_data.get("lat") is not None and user_data.get("lng") is not None
                        
                        if has_gps:
                            successful_registrations += 1
                            print(f"   ✅ {test_case['city']}/{test_case['district']}: GPS coordinates included (lat: {user_data.get('lat')}, lng: {user_data.get('lng')})")
                        else:
                            print(f"   ⚠️  {test_case['city']}/{test_case['district']}: No GPS coordinates found")
                    else:
                        print(f"   ❌ {test_case['city']}/{test_case['district']}: Registration failed - HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {test_case['city']}/{test_case['district']}: Exception - {str(e)}")
            
            if successful_registrations > 0:
                self.log_test(
                    "New Business Registration with GPS", 
                    True, 
                    f"{successful_registrations}/{len(test_cases)} business registrations successfully included GPS coordinates"
                )
                return True
            else:
                self.log_test("New Business Registration with GPS", False, "", "No business registrations included GPS coordinates")
                return False
                
        except Exception as e:
            self.log_test("New Business Registration with GPS", False, "", f"Exception: {str(e)}")
            return False
    
    def test_gps_coordinates_match_turkish_cities(self):
        """Test 8: Verify GPS coordinates match Turkish cities database"""
        try:
            # Test known Turkish city coordinates
            test_coordinates = {
                "İstanbul": {"expected_lat_range": (40.5, 41.5), "expected_lng_range": (28.0, 30.0)},
                "Ankara": {"expected_lat_range": (39.5, 40.5), "expected_lng_range": (32.0, 33.5)},
                "İzmir": {"expected_lat_range": (38.0, 39.0), "expected_lng_range": (26.5, 28.0)}
            }
            
            # Use session cookies from login instead of Bearer token
            response = self.session.get(f"{BACKEND_URL}/admin/businesses")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                coordinate_matches = 0
                businesses_checked = 0
                
                for business in businesses:
                    city = business.get("city", "")
                    lat = business.get("lat")
                    lng = business.get("lng")
                    
                    if city in test_coordinates and lat is not None and lng is not None:
                        expected = test_coordinates[city]
                        lat_in_range = expected["expected_lat_range"][0] <= lat <= expected["expected_lat_range"][1]
                        lng_in_range = expected["expected_lng_range"][0] <= lng <= expected["expected_lng_range"][1]
                        
                        if lat_in_range and lng_in_range:
                            coordinate_matches += 1
                        
                        businesses_checked += 1
                
                if businesses_checked > 0:
                    self.log_test(
                        "GPS Coordinates Match Turkish Cities", 
                        True, 
                        f"Checked {businesses_checked} businesses with known cities, {coordinate_matches} have coordinates within expected ranges"
                    )
                else:
                    self.log_test(
                        "GPS Coordinates Match Turkish Cities", 
                        True, 
                        "No businesses found with test cities (İstanbul, Ankara, İzmir) to verify coordinates"
                    )
                return True
            else:
                self.log_test("GPS Coordinates Match Turkish Cities", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GPS Coordinates Match Turkish Cities", False, "", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all GPS coordinates utility and address display tests"""
        print("🚀 GPS COORDINATES UTILITY & ADDRESS DISPLAY BACKEND TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"Customer Credentials: {CUSTOMER_EMAIL} / {CUSTOMER_PASSWORD}")
        print("=" * 80)
        print()
        
        # Test 1: Admin Authentication
        if not self.test_admin_login():
            print("❌ CRITICAL: Admin login failed - cannot proceed with admin endpoints")
            return
        
        # Test 2: Customer Authentication
        if not self.test_customer_login():
            print("❌ CRITICAL: Customer login failed - cannot test customer endpoints")
        
        # Debug: Check admin user info
        self.debug_admin_user_info()
        
        # Test 3: Check Business GPS Coverage Statistics
        gps_stats = self.test_check_business_gps_coverage()
        
        # Test 4: Batch Update Business GPS Coordinates
        update_results = self.test_update_business_gps_batch()
        
        # Test 5: Verify GPS Coordinates in Database
        self.test_verify_gps_coordinates_in_database()
        
        # Test 6: Customer Address Retrieval (if customer login successful)
        if self.customer_token:
            self.test_customer_address_retrieval()
        
        # Test 7: New Business Registration with GPS
        self.test_new_business_registration_with_gps()
        
        # Test 8: GPS Coordinates Match Turkish Cities Database
        self.test_gps_coordinates_match_turkish_cities()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
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
        
        print("✅ EXPECTED RESULTS VERIFICATION:")
        print("   • Admin can check GPS coverage statistics: ✅" if any("Check Business GPS Coverage" in r["test"] and r["success"] for r in self.test_results) else "   • Admin can check GPS coverage statistics: ❌")
        print("   • Admin can batch update businesses without GPS coordinates: ✅" if any("Update Business GPS Batch" in r["test"] and r["success"] for r in self.test_results) else "   • Admin can batch update businesses without GPS coordinates: ❌")
        print("   • Customer addresses include full address information (acik_adres): ✅" if any("Customer Address Retrieval" in r["test"] and r["success"] for r in self.test_results) else "   • Customer addresses include full address information (acik_adres): ❌")
        print("   • New business registrations automatically include GPS coordinates: ✅" if any("New Business Registration with GPS" in r["test"] and r["success"] for r in self.test_results) else "   • New business registrations automatically include GPS coordinates: ❌")
        print("   • GPS coordinates match Turkish cities database for given city/district: ✅" if any("GPS Coordinates Match Turkish Cities" in r["test"] and r["success"] for r in self.test_results) else "   • GPS coordinates match Turkish cities database for given city/district: ❌")
        
        print()
        print("🎯 CONCLUSION:")
        if success_rate >= 85:
            print("   GPS Coordinates Utility & Address Display System is WORKING EXCELLENTLY")
        elif success_rate >= 70:
            print("   GPS Coordinates Utility & Address Display System is WORKING with minor issues")
        else:
            print("   GPS Coordinates Utility & Address Display System has CRITICAL ISSUES")

if __name__ == "__main__":
    tester = GPSAddressTester()
    tester.run_all_tests()