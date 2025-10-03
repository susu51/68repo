#!/usr/bin/env python3
"""
Customer Address and Restaurant System Testing
Testing the specific areas mentioned in the review request:
1. Authentication System
2. Restaurant Endpoints  
3. Address Endpoints
4. City Normalization
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration - Use local backend for testing
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from the review request
TEST_CREDENTIALS = {
    "admin": {"email": "admin@test.com", "password": "6851"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class CustomerAddressRestaurantTest:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def test_authentication_system(self):
        """Test Area 1: Authentication System"""
        print("\n🔐 AUTHENTICATION SYSTEM TESTING")
        print("=" * 60)
        
        # Test login endpoint for existing users
        for role, creds in TEST_CREDENTIALS.items():
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data and "user" in data:
                        self.tokens[role] = data["access_token"]
                        user_info = data["user"]
                        self.log_result(
                            f"Login {role.title()} User",
                            True,
                            f"Successfully authenticated {user_info.get('email', 'unknown')} with role {user_info.get('role', 'unknown')}",
                            response_time
                        )
                        
                        # Verify JWT token generation
                        if len(data["access_token"]) > 50:  # JWT tokens are typically long
                            self.log_result(
                                f"JWT Token Generation - {role.title()}",
                                True,
                                f"Valid JWT token generated (length: {len(data['access_token'])})",
                                0
                            )
                        else:
                            self.log_result(
                                f"JWT Token Generation - {role.title()}",
                                False,
                                f"JWT token seems invalid (length: {len(data['access_token'])})",
                                0
                            )
                    else:
                        self.log_result(
                            f"Login {role.title()} User",
                            False,
                            f"Missing access_token or user data in response",
                            response_time
                        )
                else:
                    self.log_result(
                        f"Login {role.title()} User",
                        False,
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(
                    f"Login {role.title()} User",
                    False,
                    f"Request failed: {str(e)}",
                    time.time() - start_time
                )
    
    def test_restaurant_endpoints(self):
        """Test Area 2: Restaurant Endpoints"""
        print("\n🏪 RESTAURANT ENDPOINTS TESTING")
        print("=" * 60)
        
        # Test GET /api/restaurants (without parameters)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/restaurants", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/restaurants (basic)",
                    True,
                    f"Retrieved {len(data) if isinstance(data, list) else 'unknown count'} restaurants",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/restaurants (basic)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/restaurants (basic)",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test GET /api/restaurants?city=aksaray (city filter)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/restaurants?city=aksaray", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/restaurants?city=aksaray",
                    True,
                    f"City filter working - retrieved {len(data) if isinstance(data, list) else 'unknown count'} restaurants for Aksaray",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/restaurants?city=aksaray",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/restaurants?city=aksaray",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test GET /api/restaurants/near (geolocation filter)
        # Using Aksaray coordinates as mentioned in review
        aksaray_coords = {"lat": 38.3687, "lng": 34.0370}
        start_time = time.time()
        try:
            response = self.session.get(
                f"{API_BASE}/restaurants/near?lat={aksaray_coords['lat']}&lng={aksaray_coords['lng']}&radius=10",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/restaurants/near (geolocation)",
                    True,
                    f"Geolocation filter working - found {len(data) if isinstance(data, list) else 'unknown count'} restaurants near Aksaray",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/restaurants/near (geolocation)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/restaurants/near (geolocation)",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test alternative endpoint - GET /api/businesses (as seen in server.py)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/businesses", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/businesses (alternative)",
                    True,
                    f"Alternative businesses endpoint working - retrieved {len(data) if isinstance(data, list) else 'unknown count'} businesses",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/businesses (alternative)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/businesses (alternative)",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
    
    def test_address_endpoints(self):
        """Test Area 3: Address Endpoints"""
        print("\n📍 ADDRESS ENDPOINTS TESTING")
        print("=" * 60)
        
        # Need customer token for address endpoints
        if "customer" not in self.tokens:
            self.log_result(
                "Address Endpoints Setup",
                False,
                "Customer authentication required but not available",
                0
            )
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test GET /api/user/addresses (with valid token)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/user/addresses", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/user/addresses",
                    True,
                    f"Retrieved user addresses - count: {len(data) if isinstance(data, list) else 'unknown'}",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/user/addresses",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/user/addresses",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test alternative endpoint - GET /api/addresses
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/addresses", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "GET /api/addresses (alternative)",
                    True,
                    f"Alternative addresses endpoint working - count: {len(data) if isinstance(data, list) else 'unknown'}",
                    response_time
                )
            else:
                self.log_result(
                    "GET /api/addresses (alternative)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "GET /api/addresses (alternative)",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test POST /api/user/addresses (address creation with city normalization)
        test_address = {
            "title": "Test Address",
            "address": "Test Street No:123",
            "city": "Aksary",  # Misspelled city to test normalization
            "district": "Merkez",
            "postal_code": "68100",
            "is_default": True
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/user/addresses",
                json=test_address,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_result(
                    "POST /api/user/addresses",
                    True,
                    f"Address created successfully with city normalization",
                    response_time
                )
                
                # Check if city normalization worked
                if isinstance(data, dict) and "city_normalized" in data:
                    if data["city_normalized"] == "aksaray":
                        self.log_result(
                            "City Normalization in Address Creation",
                            True,
                            f"'Aksary' correctly normalized to 'aksaray'",
                            0
                        )
                    else:
                        self.log_result(
                            "City Normalization in Address Creation",
                            False,
                            f"Expected 'aksaray', got '{data.get('city_normalized', 'none')}'",
                            0
                        )
            else:
                self.log_result(
                    "POST /api/user/addresses",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "POST /api/user/addresses",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test alternative endpoint - POST /api/addresses
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/addresses",
                json=test_address,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                self.log_result(
                    "POST /api/addresses (alternative)",
                    True,
                    f"Alternative address creation endpoint working",
                    response_time
                )
            else:
                self.log_result(
                    "POST /api/addresses (alternative)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "POST /api/addresses (alternative)",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
    
    def test_city_normalization(self):
        """Test Area 4: City Normalization Function"""
        print("\n🏙️ CITY NORMALIZATION TESTING")
        print("=" * 60)
        
        # Test city normalization through business registration
        test_business = {
            "email": f"test_city_norm_{int(time.time())}@example.com",
            "password": "test123",
            "business_name": "Test City Normalization Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address",
            "city": "Aksary",  # Misspelled city as mentioned in review
            "business_category": "gida",
            "description": "Testing city normalization"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/register/business",
                json=test_business,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_result(
                    "Business Registration with City Normalization",
                    True,
                    f"Business registered successfully",
                    response_time
                )
                
                # Check city normalization in response
                if "user_data" in data:
                    user_data = data["user_data"]
                    original_city = user_data.get("city", "")
                    normalized_city = user_data.get("city_normalized", "")
                    
                    if original_city == "Aksary" and normalized_city == "aksaray":
                        self.log_result(
                            "City Normalization Function",
                            True,
                            f"'Aksary' correctly normalized to 'aksaray' (original: '{original_city}', normalized: '{normalized_city}')",
                            0
                        )
                    else:
                        self.log_result(
                            "City Normalization Function",
                            False,
                            f"Normalization failed - original: '{original_city}', normalized: '{normalized_city}'",
                            0
                        )
                else:
                    self.log_result(
                        "City Normalization Function",
                        False,
                        "No user_data in registration response to verify normalization",
                        0
                    )
            else:
                self.log_result(
                    "Business Registration with City Normalization",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "Business Registration with City Normalization",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test other common misspellings mentioned in the system
        test_cases = [
            ("Istanbul", "ıstanbul"),
            ("Gaziantap", "gaziantep"),
            ("ANKARA", "ankara"),
            ("izmir", "izmir")
        ]
        
        for original, expected in test_cases:
            test_business_case = {
                "email": f"test_city_{original.lower()}_{int(time.time())}@example.com",
                "password": "test123",
                "business_name": f"Test {original} Restaurant",
                "tax_number": f"123456789{len(original)}",
                "address": "Test Address",
                "city": original,
                "business_category": "gida",
                "description": f"Testing {original} normalization"
            }
            
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{API_BASE}/register/business",
                    json=test_business_case,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    if "user_data" in data:
                        user_data = data["user_data"]
                        normalized_city = user_data.get("city_normalized", "")
                        
                        if normalized_city == expected:
                            self.log_result(
                                f"City Normalization: {original} → {expected}",
                                True,
                                f"Correctly normalized '{original}' to '{normalized_city}'",
                                response_time
                            )
                        else:
                            self.log_result(
                                f"City Normalization: {original} → {expected}",
                                False,
                                f"Expected '{expected}', got '{normalized_city}'",
                                response_time
                            )
                else:
                    self.log_result(
                        f"City Normalization: {original} → {expected}",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(
                    f"City Normalization: {original} → {expected}",
                    False,
                    f"Request failed: {str(e)}",
                    time.time() - start_time
                )
    
    def run_all_tests(self):
        """Run all test areas"""
        print("🚀 CUSTOMER ADDRESS & RESTAURANT SYSTEM TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all test areas
        self.test_authentication_system()
        self.test_restaurant_endpoints()
        self.test_address_endpoints()
        self.test_city_normalization()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 CUSTOMER ADDRESS & RESTAURANT SYSTEM TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print("=" * 80)
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n🎯 TEST FOCUS AREAS COVERAGE:")
        print(f"  ✅ Authentication System - Login endpoints and JWT tokens")
        print(f"  ✅ Restaurant Endpoints - Basic listing, city filter, geolocation")
        print(f"  ✅ Address Endpoints - User address management with authentication")
        print(f"  ✅ City Normalization - Function testing with common misspellings")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "test_results": self.test_results
        }

if __name__ == "__main__":
    tester = CustomerAddressRestaurantTest()
    tester.run_all_tests()