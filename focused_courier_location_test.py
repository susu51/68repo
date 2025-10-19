#!/usr/bin/env python3
"""
FOCUSED COURIER LOCATION SYSTEM TESTING
Testing the core courier location endpoints without order dependencies.
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://admin-wsocket.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"}
}

class FocusedCourierLocationTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.test_courier_id = None
        
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
        """Authenticate all test users"""
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
                    
                    if role == "courier":
                        self.test_courier_id = data["user"]["id"]
                    
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, User ID: {data['user']['id']}"
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

    def test_courier_location_endpoints(self):
        """Test all courier location endpoints comprehensively"""
        print("📍 TESTING COURIER LOCATION ENDPOINTS...")
        
        # Test 1: Courier location update with valid data
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "heading": 45.5,
                "speed": 25.0,
                "accuracy": 10.0,
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "POST /api/courier/location - Valid Update",
                    True,
                    f"Success: {data.get('success')}, Message: {data.get('message')}, Timestamp: {data.get('timestamp')}"
                )
            else:
                self.log_test(
                    "POST /api/courier/location - Valid Update",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "POST /api/courier/location - Valid Update",
                False,
                error=str(e)
            )

        # Test 2: RBAC - Customer trying to update location (should fail)
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "POST /api/courier/location - RBAC Customer Test",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for non-courier)"
            )
        except Exception as e:
            self.log_test(
                "POST /api/courier/location - RBAC Customer Test",
                False,
                error=str(e)
            )

        # Test 3: RBAC - Business trying to update location (should fail)
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "POST /api/courier/location - RBAC Business Test",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for non-courier)"
            )
        except Exception as e:
            self.log_test(
                "POST /api/courier/location - RBAC Business Test",
                False,
                error=str(e)
            )

        # Test 4: Invalid location data
        try:
            invalid_data = {
                "lat": "invalid_latitude",
                "lng": 28.9784
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=invalid_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "POST /api/courier/location - Invalid Data Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for invalid data)"
            )
        except Exception as e:
            self.log_test(
                "POST /api/courier/location - Invalid Data Validation",
                False,
                error=str(e)
            )

        # Test 5: Missing required fields
        try:
            incomplete_data = {
                "lat": 41.0082
                # Missing lng
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=incomplete_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "POST /api/courier/location - Missing Required Fields",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing fields)"
            )
        except Exception as e:
            self.log_test(
                "POST /api/courier/location - Missing Required Fields",
                False,
                error=str(e)
            )

    def test_location_retrieval_endpoints(self):
        """Test location retrieval endpoints"""
        print("🔍 TESTING LOCATION RETRIEVAL ENDPOINTS...")
        
        if not self.test_courier_id:
            self.log_test(
                "Location Retrieval - Setup",
                False,
                error="No courier ID available for testing"
            )
            return

        # Test 1: Admin accessing courier location
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Admin Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}, Timestamp: {data.get('ts')}"
                )
            else:
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Admin Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "GET /api/courier/location/{courier_id} - Admin Access",
                False,
                error=str(e)
            )

        # Test 2: Customer accessing courier location (may be restricted)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Customer Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Customer Access",
                    True,
                    "Access denied (expected behavior for customer without active order)"
                )
            else:
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Customer Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "GET /api/courier/location/{courier_id} - Customer Access",
                False,
                error=str(e)
            )

        # Test 3: Business accessing courier location (may be restricted)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Business Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Business Access",
                    True,
                    "Access denied (expected behavior for business without active order)"
                )
            else:
                self.log_test(
                    "GET /api/courier/location/{courier_id} - Business Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "GET /api/courier/location/{courier_id} - Business Access",
                False,
                error=str(e)
            )

        # Test 4: Non-existent courier ID
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/non-existent-courier-id",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "GET /api/courier/location/{courier_id} - Non-existent ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for non-existent courier)"
            )
        except Exception as e:
            self.log_test(
                "GET /api/courier/location/{courier_id} - Non-existent ID",
                False,
                error=str(e)
            )

        # Test 5: Unauthorized access (no token)
        try:
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                timeout=10
            )
            
            self.log_test(
                "GET /api/courier/location/{courier_id} - No Authorization",
                response.status_code == 401,
                f"Status: {response.status_code} (Expected 401 for no authorization)"
            )
        except Exception as e:
            self.log_test(
                "GET /api/courier/location/{courier_id} - No Authorization",
                False,
                error=str(e)
            )

    def test_redis_integration(self):
        """Test Redis caching functionality"""
        print("🔴 TESTING REDIS INTEGRATION...")
        
        # Test Redis by updating location and immediately retrieving it
        try:
            # Update location with specific coordinates
            test_lat = 41.0123456
            test_lng = 28.9876543
            location_data = {
                "lat": test_lat,
                "lng": test_lng,
                "heading": 90.0,
                "speed": 30.0,
                "accuracy": 5.0,
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            update_response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            if update_response.status_code == 200:
                # Immediately retrieve location to test Redis caching
                time.sleep(1)  # Small delay
                
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                get_response = requests.get(
                    f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                    headers=headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    data = get_response.json()
                    # Check if we got the exact location we just updated
                    lat_match = abs(data.get('lat', 0) - test_lat) < 0.0001
                    lng_match = abs(data.get('lng', 0) - test_lng) < 0.0001
                    is_realtime = data.get('source') == 'realtime'
                    
                    self.log_test(
                        "Redis Integration - Real-time Cache",
                        lat_match and lng_match,
                        f"Location match: {lat_match and lng_match}, Source: {data.get('source')}, Real-time: {is_realtime}, Retrieved lat: {data.get('lat')}, lng: {data.get('lng')}"
                    )
                else:
                    self.log_test(
                        "Redis Integration - Real-time Cache",
                        False,
                        f"Get status: {get_response.status_code}",
                        get_response.text
                    )
            else:
                self.log_test(
                    "Redis Integration - Real-time Cache",
                    False,
                    f"Update status: {update_response.status_code}",
                    update_response.text
                )
        except Exception as e:
            self.log_test(
                "Redis Integration - Real-time Cache",
                False,
                error=str(e)
            )

    def test_location_data_validation(self):
        """Test location data validation and edge cases"""
        print("📊 TESTING LOCATION DATA VALIDATION...")
        
        # Test 1: Extreme coordinates (valid but edge case)
        try:
            location_data = {
                "lat": 89.999999,  # Near North Pole
                "lng": 179.999999,  # Near International Date Line
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Validation - Extreme Coordinates",
                response.status_code == 200,
                f"Status: {response.status_code}, Lat: {location_data['lat']}, Lng: {location_data['lng']}"
            )
        except Exception as e:
            self.log_test(
                "Location Validation - Extreme Coordinates",
                False,
                error=str(e)
            )

        # Test 2: Invalid coordinates (out of range)
        try:
            location_data = {
                "lat": 91.0,  # Invalid latitude (> 90)
                "lng": 28.9784,
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Validation - Invalid Latitude",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for lat > 90)"
            )
        except Exception as e:
            self.log_test(
                "Location Validation - Invalid Latitude",
                False,
                error=str(e)
            )

        # Test 3: High accuracy location
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "accuracy": 1.0,  # Very high accuracy
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Validation - High Accuracy",
                response.status_code == 200,
                f"Status: {response.status_code}, Accuracy: {location_data['accuracy']}m"
            )
        except Exception as e:
            self.log_test(
                "Location Validation - High Accuracy",
                False,
                error=str(e)
            )

        # Test 4: Low accuracy location
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "accuracy": 1000.0,  # Very low accuracy
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Validation - Low Accuracy",
                response.status_code == 200,
                f"Status: {response.status_code}, Accuracy: {location_data['accuracy']}m"
            )
        except Exception as e:
            self.log_test(
                "Location Validation - Low Accuracy",
                False,
                error=str(e)
            )

    def run_focused_test(self):
        """Run focused courier location system tests"""
        print("🎯 STARTING FOCUSED COURIER LOCATION SYSTEM TESTING")
        print("=" * 60)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not all(role in self.tokens for role in ["admin", "courier", "customer", "business"]):
            print("❌ CRITICAL: Authentication failed for required roles. Cannot proceed.")
            return
        
        # Step 2: Test courier location endpoints
        self.test_courier_location_endpoints()
        
        # Step 3: Test location retrieval endpoints
        self.test_location_retrieval_endpoints()
        
        # Step 4: Test Redis integration
        self.test_redis_integration()
        
        # Step 5: Test location data validation
        self.test_location_data_validation()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED COURIER LOCATION SYSTEM TEST SUMMARY")
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
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            if " - " in result["test"]:
                category = result["test"].split(" - ")[0]
            else:
                category = "General"
            
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
            categories[category]["tests"].append(result)
        
        # Print category summaries
        for category, data in categories.items():
            total = data["passed"] + data["failed"]
            rate = (data["passed"] / total * 100) if total > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 75 else "❌"
            print(f"{status} {category}: {data['passed']}/{total} ({rate:.1f}%)")
        
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
        print("📋 FINAL ASSESSMENT")
        print("=" * 60)
        
        if success_rate >= 95:
            print("🎉 EXCELLENT: Courier location system is working perfectly")
        elif success_rate >= 85:
            print("✅ VERY GOOD: Courier location system is working well with minor issues")
        elif success_rate >= 75:
            print("⚠️ GOOD: Courier location system is mostly functional")
        elif success_rate >= 50:
            print("⚠️ NEEDS ATTENTION: Courier location system has significant issues")
        else:
            print("❌ CRITICAL: Courier location system has major problems")

if __name__ == "__main__":
    tester = FocusedCourierLocationTester()
    tester.run_focused_test()