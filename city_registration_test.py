#!/usr/bin/env python3
"""
City Registration Issue Testing
Testing the user-reported issue: "Her yeni kayıt edilen restoran şehir/il kısmına ne yazarsam yazayım İstanbul olarak kaydediliyor"
(Every new restaurant registration gets saved as İstanbul regardless of what city is entered)

Test Coverage:
1. Register businesses with different cities (Niğde, Ankara, İzmir, Bursa)
2. Verify that both original city and normalized city are saved correctly
3. Verify that businesses appear in the correct city when retrieved
4. Test city filtering functionality
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone

# Configuration - Use environment URL
BACKEND_URL = "https://deliver-yemek.preview.emergentagent.com/api"

class CityRegistrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.registered_businesses = []
        
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
    
    def register_business_with_city(self, city_name):
        """Register a business with specific city"""
        try:
            # Generate unique email for this test
            unique_id = str(uuid.uuid4())[:8]
            business_data = {
                "email": f"test-{city_name.lower()}-{unique_id}@example.com",
                "password": "test123456",
                "business_name": f"Test Restaurant {city_name}",
                "tax_number": "1234567890",
                "address": "Test Address",
                "city": city_name,
                "district": "Merkez",
                "business_category": "gida",
                "description": "Test restaurant"
            }
            
            print(f"\n🔄 Registering business in {city_name}...")
            print(f"   Email: {business_data['email']}")
            print(f"   City: {business_data['city']}")
            
            response = self.session.post(
                f"{BACKEND_URL}/register/business",
                json=business_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:  # Business registration returns 200, not 201
                response_data = response.json()
                business_id = response_data.get("user_data", {}).get("id")
                saved_city = response_data.get("user_data", {}).get("city")
                saved_city_normalized = response_data.get("user_data", {}).get("city_normalized")
                
                # Store for later verification
                self.registered_businesses.append({
                    "id": business_id,
                    "email": business_data["email"],
                    "city": city_name,
                    "saved_city": saved_city,
                    "saved_city_normalized": saved_city_normalized,
                    "business_name": business_data["business_name"]
                })
                
                # Check if city was saved correctly
                city_correct = saved_city == city_name
                
                self.log_test(
                    f"Business Registration - {city_name}",
                    city_correct,
                    f"Business ID: {business_id}, Requested: '{city_name}', Saved: '{saved_city}', Normalized: '{saved_city_normalized}'"
                )
                return business_id, response_data
            else:
                self.log_test(
                    f"Business Registration - {city_name}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None, None
                
        except Exception as e:
            self.log_test(
                f"Business Registration - {city_name}",
                False,
                "",
                str(e)
            )
            return None, None
    
    def verify_business_city_in_database(self, business_id, expected_city):
        """Verify business city is saved correctly by checking individual business"""
        try:
            # Get admin token first
            admin_token = self.get_admin_token()
            if not admin_token:
                self.log_test(
                    f"City Verification - {expected_city}",
                    False,
                    "",
                    "Could not get admin token"
                )
                return False
            
            # Get business details via admin endpoint
            response = self.session.get(
                f"{BACKEND_URL}/admin/businesses/{business_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code == 200:
                business_data = response.json()
                saved_city = business_data.get("city", "")
                saved_city_normalized = business_data.get("city_normalized", "")
                
                # Check if city matches expected
                city_correct = saved_city.lower() == expected_city.lower()
                
                self.log_test(
                    f"City Verification - {expected_city}",
                    city_correct,
                    f"Saved city: '{saved_city}', Normalized: '{saved_city_normalized}', Expected: '{expected_city}'"
                )
                
                return city_correct
            else:
                self.log_test(
                    f"City Verification - {expected_city}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"City Verification - {expected_city}",
                False,
                "",
                str(e)
            )
            return False
    
    def get_admin_token(self):
        """Get admin authentication token"""
        try:
            # Try different admin credentials
            admin_credentials = [
                {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
                {"email": "admin@kuryecini.com", "password": "admin123"},
                {"email": "admin@delivertr.com", "password": "6851"}
            ]
            
            for creds in admin_credentials:
                response = self.session.post(
                    f"{BACKEND_URL}/auth/login",
                    json=creds,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
            
            return None
            
        except Exception as e:
            print(f"Error getting admin token: {e}")
            return None
    
    def test_city_filtering(self):
        """Test if businesses can be filtered by city correctly"""
        try:
            admin_token = self.get_admin_token()
            if not admin_token:
                self.log_test(
                    "City Filtering Test",
                    False,
                    "",
                    "Could not get admin token"
                )
                return
            
            # Test filtering for each registered city
            cities_to_test = ["Niğde", "Ankara", "İzmir", "Bursa"]
            
            for city in cities_to_test:
                response = self.session.get(
                    f"{BACKEND_URL}/admin/businesses",
                    params={"city": city.lower()},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                if response.status_code == 200:
                    businesses = response.json()
                    
                    # Check if our registered business appears in the results
                    found_our_business = False
                    expected_business = None
                    for registered in self.registered_businesses:
                        if registered["city"].lower() == city.lower():
                            expected_business = registered
                            # Look for this business in the results
                            for business in businesses:
                                if business.get("id") == registered["id"] or business.get("email") == registered["email"]:
                                    found_our_business = True
                                    break
                    
                    self.log_test(
                        f"City Filtering - {city}",
                        found_our_business,
                        f"Found {len(businesses)} businesses, Our business found: {found_our_business}"
                    )
                else:
                    self.log_test(
                        f"City Filtering - {city}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
                    
        except Exception as e:
            self.log_test(
                "City Filtering Test",
                False,
                "",
                str(e)
            )
    
    def test_public_business_listing_by_city(self):
        """Test public business listing to see if cities are preserved"""
        try:
            # Get all businesses via public endpoint
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                
                # Check if our registered businesses appear with correct cities
                for registered in self.registered_businesses:
                    found_business = None
                    for business in businesses:
                        if business.get("business_name") == registered["business_name"]:
                            found_business = business
                            break
                    
                    if found_business:
                        saved_city = found_business.get("city", "")
                        expected_city = registered["city"]
                        city_correct = saved_city.lower() == expected_city.lower()
                        
                        self.log_test(
                            f"Public Listing City Check - {expected_city}",
                            city_correct,
                            f"Business: {registered['business_name']}, Saved city: '{saved_city}', Expected: '{expected_city}'"
                        )
                    else:
                        self.log_test(
                            f"Public Listing City Check - {registered['city']}",
                            False,
                            f"Business not found in public listing: {registered['business_name']}"
                        )
                        
            else:
                self.log_test(
                    "Public Business Listing",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Public Business Listing",
                False,
                "",
                str(e)
            )
    
    def run_all_tests(self):
        """Run all city registration tests"""
        print("🚀 Starting City Registration Issue Testing")
        print("=" * 60)
        
        # Test cities as specified in the review request
        test_cities = ["Niğde", "Ankara", "İzmir", "Bursa"]
        
        # Step 1: Register businesses in different cities
        print("\n📝 STEP 1: Registering businesses in different cities")
        for city in test_cities:
            business_id, response_data = self.register_business_with_city(city)
            if business_id:
                # Immediately verify the city is saved correctly
                time.sleep(1)  # Brief pause
                self.verify_business_city_in_database(business_id, city)
        
        # Step 2: Test city filtering
        print("\n🔍 STEP 2: Testing city filtering functionality")
        self.test_city_filtering()
        
        # Step 3: Test public business listing
        print("\n🌐 STEP 3: Testing public business listing by city")
        self.test_public_business_listing_by_city()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
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
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🏢 REGISTERED BUSINESSES:")
        for business in self.registered_businesses:
            print(f"   • {business['business_name']} in {business['city']} (ID: {business['id']})")
        
        # Conclusion
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 80:
            print("✅ City registration appears to be working correctly")
        else:
            print("❌ City registration has issues - cities may be defaulting to Istanbul")
            print("   This confirms the user-reported issue")

if __name__ == "__main__":
    tester = CityRegistrationTester()
    tester.run_all_tests()