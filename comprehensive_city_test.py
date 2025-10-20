#!/usr/bin/env python3
"""
Comprehensive City Registration Testing
Testing the complete flow including KYC approval to verify cities are preserved throughout the process
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"

class ComprehensiveCityTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
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
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
            
        try:
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
                    self.admin_token = data.get("access_token")
                    print(f"✅ Admin authenticated with {creds['email']}")
                    return self.admin_token
            
            print("❌ Failed to authenticate as admin")
            return None
            
        except Exception as e:
            print(f"❌ Error getting admin token: {e}")
            return None
    
    def register_and_approve_business(self, city_name):
        """Register a business and approve it via admin"""
        try:
            # Step 1: Register business
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
            
            response = self.session.post(
                f"{BACKEND_URL}/register/business",
                json=business_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test(
                    f"Business Registration - {city_name}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None
            
            response_data = response.json()
            business_id = response_data.get("user_data", {}).get("id")
            saved_city = response_data.get("user_data", {}).get("city")
            saved_city_normalized = response_data.get("user_data", {}).get("city_normalized")
            
            # Check if city was saved correctly during registration
            city_correct = saved_city == city_name
            
            self.log_test(
                f"Business Registration - {city_name}",
                city_correct,
                f"Business ID: {business_id}, Requested: '{city_name}', Saved: '{saved_city}', Normalized: '{saved_city_normalized}'"
            )
            
            if not city_correct:
                return None
            
            # Step 2: Approve business via admin
            admin_token = self.get_admin_token()
            if not admin_token:
                self.log_test(
                    f"Business Approval - {city_name}",
                    False,
                    "",
                    "Could not get admin token"
                )
                return None
            
            print(f"🔄 Approving business {business_id}...")
            
            approval_response = self.session.patch(
                f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                json={"kyc_status": "approved"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if approval_response.status_code == 200:
                self.log_test(
                    f"Business Approval - {city_name}",
                    True,
                    f"Business {business_id} approved successfully"
                )
                
                # Store for later verification
                self.registered_businesses.append({
                    "id": business_id,
                    "email": business_data["email"],
                    "city": city_name,
                    "saved_city": saved_city,
                    "saved_city_normalized": saved_city_normalized,
                    "business_name": business_data["business_name"],
                    "approved": True
                })
                
                return business_id
            else:
                self.log_test(
                    f"Business Approval - {city_name}",
                    False,
                    f"Status: {approval_response.status_code}",
                    approval_response.text
                )
                return None
                
        except Exception as e:
            self.log_test(
                f"Business Registration/Approval - {city_name}",
                False,
                "",
                str(e)
            )
            return None
    
    def verify_approved_business_city(self, business_id, expected_city):
        """Verify approved business still has correct city"""
        try:
            admin_token = self.get_admin_token()
            if not admin_token:
                return False
            
            response = self.session.get(
                f"{BACKEND_URL}/admin/businesses/{business_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code == 200:
                business_data = response.json()
                saved_city = business_data.get("city", "")
                saved_city_normalized = business_data.get("city_normalized", "")
                kyc_status = business_data.get("kyc_status", "")
                
                city_correct = saved_city == expected_city
                approved = kyc_status == "approved"
                
                self.log_test(
                    f"Approved Business City Verification - {expected_city}",
                    city_correct and approved,
                    f"City: '{saved_city}', Normalized: '{saved_city_normalized}', KYC: '{kyc_status}', Expected: '{expected_city}'"
                )
                
                return city_correct and approved
            else:
                self.log_test(
                    f"Approved Business City Verification - {expected_city}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Approved Business City Verification - {expected_city}",
                False,
                "",
                str(e)
            )
            return False
    
    def test_public_approved_businesses(self):
        """Test if approved businesses appear in public listing with correct cities"""
        try:
            print(f"\n🌐 Testing public business listing...")
            
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                print(f"Found {len(businesses)} businesses in public listing")
                
                for registered in self.registered_businesses:
                    if registered.get("approved"):
                        found_business = None
                        for business in businesses:
                            if (business.get("id") == registered["id"] or 
                                business.get("business_name") == registered["business_name"]):
                                found_business = business
                                break
                        
                        if found_business:
                            saved_city = found_business.get("city", "")
                            expected_city = registered["city"]
                            city_correct = saved_city == expected_city
                            
                            self.log_test(
                                f"Public Listing City Check - {expected_city}",
                                city_correct,
                                f"Business: {registered['business_name']}, Public city: '{saved_city}', Expected: '{expected_city}'"
                            )
                        else:
                            self.log_test(
                                f"Public Listing City Check - {registered['city']}",
                                False,
                                f"Approved business not found in public listing: {registered['business_name']}"
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
    
    def test_city_based_filtering(self):
        """Test city-based filtering for approved businesses"""
        try:
            print(f"\n🔍 Testing city-based filtering...")
            
            admin_token = self.get_admin_token()
            if not admin_token:
                return
            
            cities_to_test = ["Niğde", "Ankara", "İzmir", "Bursa"]
            
            for city in cities_to_test:
                # Test admin filtering
                response = self.session.get(
                    f"{BACKEND_URL}/admin/businesses",
                    params={"city": city.lower()},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                if response.status_code == 200:
                    businesses = response.json()
                    
                    # Check if our registered business appears
                    found_our_business = False
                    expected_business = None
                    
                    for registered in self.registered_businesses:
                        if registered["city"] == city and registered.get("approved"):
                            expected_business = registered
                            for business in businesses:
                                if (business.get("id") == registered["id"] or 
                                    business.get("email") == registered["email"]):
                                    found_our_business = True
                                    break
                    
                    if expected_business:
                        self.log_test(
                            f"Admin City Filtering - {city}",
                            found_our_business,
                            f"Found {len(businesses)} businesses, Expected: {expected_business['business_name']}, Found: {found_our_business}"
                        )
                    else:
                        self.log_test(
                            f"Admin City Filtering - {city}",
                            True,  # No business expected for this city
                            f"Found {len(businesses)} businesses, No test business expected for this city"
                        )
                else:
                    self.log_test(
                        f"Admin City Filtering - {city}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
                    
        except Exception as e:
            self.log_test(
                "City-based Filtering",
                False,
                "",
                str(e)
            )
    
    def run_comprehensive_test(self):
        """Run comprehensive city registration test"""
        print("🚀 Starting Comprehensive City Registration Testing")
        print("=" * 70)
        
        test_cities = ["Niğde", "Ankara", "İzmir", "Bursa"]
        
        # Step 1: Register and approve businesses
        print("\n📝 STEP 1: Register and approve businesses in different cities")
        for city in test_cities:
            business_id = self.register_and_approve_business(city)
            if business_id:
                time.sleep(1)  # Brief pause
                self.verify_approved_business_city(business_id, city)
        
        # Step 2: Test public listing
        print("\n🌐 STEP 2: Test public business listing")
        time.sleep(2)  # Allow time for database consistency
        self.test_public_approved_businesses()
        
        # Step 3: Test city filtering
        print("\n🔍 STEP 3: Test city-based filtering")
        self.test_city_based_filtering()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
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
                    print(f"   • {result['test']}: {result['error'] or 'See details above'}")
        
        print(f"\n🏢 REGISTERED & APPROVED BUSINESSES:")
        for business in self.registered_businesses:
            status = "✅ Approved" if business.get("approved") else "⏳ Pending"
            print(f"   • {business['business_name']} in {business['city']} - {status}")
            print(f"     ID: {business['id']}")
            print(f"     Saved City: '{business['saved_city']}' (Normalized: '{business['saved_city_normalized']}')")
        
        # Final conclusion
        print(f"\n🎯 FINAL CONCLUSION:")
        
        # Check if any cities were incorrectly saved as Istanbul
        istanbul_issue_found = False
        for business in self.registered_businesses:
            if business['saved_city'].lower() == 'istanbul' and business['city'].lower() != 'istanbul':
                istanbul_issue_found = True
                break
        
        if istanbul_issue_found:
            print("❌ CRITICAL ISSUE CONFIRMED: Cities are being saved as Istanbul!")
            print("   This confirms the user-reported issue.")
        elif success_rate >= 80:
            print("✅ CITY REGISTRATION WORKING CORRECTLY")
            print("   Cities are being saved with their correct values, not defaulting to Istanbul.")
            print("   The user-reported issue may be resolved or may be a frontend issue.")
        else:
            print("⚠️  MIXED RESULTS - Some issues detected but not the Istanbul default issue")
            print("   Further investigation needed.")

if __name__ == "__main__":
    tester = ComprehensiveCityTester()
    tester.run_comprehensive_test()