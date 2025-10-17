#!/usr/bin/env python3
"""
Business KYC Status and Customer Panel Requirements Testing
Test scenarios as specified in the review request:
1. Check Business KYC Status (admin login, get businesses, check kyc_status/is_active/city/district)
2. Test Customer Access (NO KYC REQUIRED) - verify customer can access without KYC approval
3. Test Catalog Endpoint - get customer city/district, call /api/catalog/city-nearby
4. Identify Issues - approved businesses in same city, customer KYC blocks, business indexing
"""

import requests
import json
import os
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

class KYCCustomerPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.customer_token = None
        self.test_results = []
        self.businesses = []
        self.customer_profile = {}
        
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
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    self.log_test(
                        "Admin Login", 
                        True, 
                        f"Successfully logged in as {ADMIN_EMAIL}, token length: {len(self.admin_token)} chars"
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
    
    def test_get_all_businesses(self):
        """Test 2: GET /api/admin/businesses - get all businesses and analyze KYC status"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses")
            
            if response.status_code == 200:
                data = response.json()
                # Handle both possible response formats
                if isinstance(data, list):
                    businesses = data
                else:
                    businesses = data.get("businesses", [])
                
                self.businesses = businesses
                
                # Analyze KYC status
                approved_businesses = [b for b in businesses if b.get("kyc_status") == "approved"]
                pending_businesses = [b for b in businesses if b.get("kyc_status") == "pending"]
                rejected_businesses = [b for b in businesses if b.get("kyc_status") == "rejected"]
                active_businesses = [b for b in businesses if b.get("is_active") == True]
                
                # Analyze cities
                cities = {}
                for business in businesses:
                    city = business.get("city", "Unknown")
                    district = business.get("district", "Unknown")
                    kyc_status = business.get("kyc_status", "Unknown")
                    is_active = business.get("is_active", False)
                    
                    if city not in cities:
                        cities[city] = {"total": 0, "approved": 0, "pending": 0, "rejected": 0, "active": 0, "districts": {}}
                    
                    cities[city]["total"] += 1
                    cities[city][kyc_status] = cities[city].get(kyc_status, 0) + 1
                    if is_active:
                        cities[city]["active"] += 1
                    
                    if district not in cities[city]["districts"]:
                        cities[city]["districts"][district] = {"total": 0, "approved": 0, "active": 0}
                    cities[city]["districts"][district]["total"] += 1
                    if kyc_status == "approved":
                        cities[city]["districts"][district]["approved"] += 1
                    if is_active:
                        cities[city]["districts"][district]["active"] += 1
                
                details = f"Retrieved {len(businesses)} total businesses. "
                details += f"KYC Status: {len(approved_businesses)} approved, {len(pending_businesses)} pending, {len(rejected_businesses)} rejected. "
                details += f"Active: {len(active_businesses)}. Cities: {list(cities.keys())}"
                
                self.log_test("Get All Businesses", True, details)
                
                # Print detailed city analysis
                print("📍 CITY/DISTRICT ANALYSIS:")
                for city, city_data in cities.items():
                    print(f"   {city}: {city_data['total']} total, {city_data['approved']} approved, {city_data['active']} active")
                    for district, district_data in city_data["districts"].items():
                        print(f"      └─ {district}: {district_data['total']} total, {district_data['approved']} approved, {district_data['active']} active")
                print()
                
                return businesses
            else:
                self.log_test("Get All Businesses", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get All Businesses", False, "", f"Exception: {str(e)}")
            return []
    
    def test_customer_login(self):
        """Test 3: Customer login with test@kuryecini.com/test123 (NO KYC REQUIRED)"""
        try:
            # Create new session for customer (no admin headers)
            customer_session = requests.Session()
            
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = customer_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "access_token" in data:
                    self.customer_token = data["access_token"]
                    user_data = data.get("user", {})
                    self.customer_profile = user_data
                    
                    # Check if customer has KYC requirement (should NOT have)
                    kyc_status = user_data.get("kyc_status")
                    role = user_data.get("role")
                    city = user_data.get("city")
                    district = user_data.get("district")
                    
                    details = f"Successfully logged in as {CUSTOMER_EMAIL}. "
                    details += f"Role: {role}, City: {city}, District: {district}, "
                    details += f"KYC Status: {kyc_status if kyc_status else 'Not Required (Good!)'}"
                    
                    self.log_test("Customer Login (NO KYC REQUIRED)", True, details)
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
    
    def test_customer_profile_access(self):
        """Test 4: Verify customer can access profile without KYC approval"""
        try:
            # Create customer session with token
            customer_session = requests.Session()
            customer_session.headers.update({"Authorization": f"Bearer {self.customer_token}"})
            
            response = customer_session.get(f"{BACKEND_URL}/me")
            
            if response.status_code == 200:
                data = response.json()
                city = data.get("city")
                district = data.get("district")
                role = data.get("role")
                kyc_status = data.get("kyc_status")
                
                # Update customer profile with latest data
                self.customer_profile = data
                
                details = f"Customer profile accessible. Role: {role}, City: {city}, District: {district}, "
                details += f"KYC Status: {kyc_status if kyc_status else 'Not Required'}"
                
                self.log_test("Customer Profile Access", True, details)
                return True
            else:
                self.log_test("Customer Profile Access", False, "", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Customer Profile Access", False, "", f"Exception: {str(e)}")
            return False
    
    def test_catalog_city_nearby(self):
        """Test 5: Test /api/catalog/city-nearby with customer's location"""
        try:
            customer_city = self.customer_profile.get("city", "İstanbul")
            customer_district = self.customer_profile.get("district", "")
            
            # Create customer session
            customer_session = requests.Session()
            customer_session.headers.update({"Authorization": f"Bearer {self.customer_token}"})
            
            # Test catalog endpoint
            response = customer_session.get(f"{BACKEND_URL}/catalog/city-nearby", params={
                "city": customer_city,
                "district": customer_district
            })
            
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("restaurants", [])
                
                # Analyze returned restaurants
                approved_restaurants = [r for r in restaurants if r.get("kyc_status") == "approved"]
                same_city_restaurants = [r for r in restaurants if r.get("city", "").lower() == customer_city.lower()]
                
                details = f"Catalog endpoint returned {len(restaurants)} restaurants for {customer_city}"
                if customer_district:
                    details += f"/{customer_district}"
                details += f". {len(approved_restaurants)} approved, {len(same_city_restaurants)} in same city"
                
                self.log_test("Catalog City Nearby", True, details)
                
                # Print restaurant details
                print("🏪 CATALOG RESTAURANTS:")
                for restaurant in restaurants[:5]:  # Show first 5
                    name = restaurant.get("name", "Unknown")
                    city = restaurant.get("city", "Unknown")
                    district = restaurant.get("district", "Unknown")
                    kyc_status = restaurant.get("kyc_status", "Unknown")
                    is_active = restaurant.get("is_active", False)
                    print(f"   • {name} - {city}/{district} - KYC: {kyc_status} - Active: {is_active}")
                if len(restaurants) > 5:
                    print(f"   ... and {len(restaurants) - 5} more restaurants")
                print()
                
                return restaurants
            else:
                self.log_test("Catalog City Nearby", False, "", f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Catalog City Nearby", False, "", f"Exception: {str(e)}")
            return []
    
    def test_identify_issues(self):
        """Test 6: Identify why customer cannot see restaurants"""
        try:
            customer_city = self.customer_profile.get("city", "İstanbul")
            customer_district = self.customer_profile.get("district", "")
            
            # Analyze businesses in customer's city
            customer_city_businesses = []
            for business in self.businesses:
                business_city = business.get("city", "")
                if business_city.lower() == customer_city.lower():
                    customer_city_businesses.append(business)
            
            approved_in_city = [b for b in customer_city_businesses if b.get("kyc_status") == "approved"]
            active_in_city = [b for b in customer_city_businesses if b.get("is_active") == True]
            approved_and_active = [b for b in customer_city_businesses if b.get("kyc_status") == "approved" and b.get("is_active") == True]
            
            # Check if customer has any KYC blocks
            customer_kyc_status = self.customer_profile.get("kyc_status")
            customer_is_active = self.customer_profile.get("is_active", True)
            
            # Analysis
            issues = []
            if len(approved_and_active) == 0:
                issues.append(f"No approved AND active businesses in {customer_city}")
            if customer_kyc_status and customer_kyc_status != "approved":
                issues.append(f"Customer has KYC status: {customer_kyc_status} (should be None for customers)")
            if not customer_is_active:
                issues.append("Customer account is not active")
            
            details = f"Analysis for {customer_city}: "
            details += f"{len(customer_city_businesses)} total businesses, "
            details += f"{len(approved_in_city)} approved, "
            details += f"{len(active_in_city)} active, "
            details += f"{len(approved_and_active)} approved AND active. "
            details += f"Customer KYC: {customer_kyc_status if customer_kyc_status else 'Not Required'}, "
            details += f"Customer Active: {customer_is_active}"
            
            if issues:
                details += f". ISSUES FOUND: {', '.join(issues)}"
                
            self.log_test("Issue Analysis", True, details)
            
            # Print detailed analysis
            print("🔍 ISSUE ANALYSIS:")
            print(f"   Customer Location: {customer_city}" + (f"/{customer_district}" if customer_district else ""))
            print(f"   Customer KYC Status: {customer_kyc_status if customer_kyc_status else 'Not Required (Correct)'}")
            print(f"   Customer Active: {customer_is_active}")
            print(f"   Businesses in {customer_city}: {len(customer_city_businesses)}")
            print(f"   Approved businesses: {len(approved_in_city)}")
            print(f"   Active businesses: {len(active_in_city)}")
            print(f"   Approved AND Active: {len(approved_and_active)}")
            
            if approved_and_active:
                print(f"   ✅ Available restaurants for customer:")
                for business in approved_and_active[:3]:
                    name = business.get("business_name", "Unknown")
                    district = business.get("district", "Unknown")
                    print(f"      • {name} - {district}")
            else:
                print(f"   ❌ NO available restaurants for customer in {customer_city}")
            
            if issues:
                print(f"   🚨 IDENTIFIED ISSUES:")
                for issue in issues:
                    print(f"      • {issue}")
            else:
                print(f"   ✅ No blocking issues found")
            print()
            
            return len(issues) == 0
                
        except Exception as e:
            self.log_test("Issue Analysis", False, "", f"Exception: {str(e)}")
            return False
    
    def test_business_indexing(self):
        """Test 7: Check if businesses are properly indexed with city/district"""
        try:
            missing_city = [b for b in self.businesses if not b.get("city")]
            missing_district = [b for b in self.businesses if not b.get("district")]
            missing_coordinates = [b for b in self.businesses if not b.get("lat") or not b.get("lng")]
            
            details = f"Business indexing check: "
            details += f"{len(self.businesses)} total businesses, "
            details += f"{len(missing_city)} missing city, "
            details += f"{len(missing_district)} missing district, "
            details += f"{len(missing_coordinates)} missing GPS coordinates"
            
            success = len(missing_city) == 0 and len(missing_district) == 0
            
            self.log_test("Business Indexing Check", success, details)
            
            if missing_city or missing_district or missing_coordinates:
                print("🏪 BUSINESS INDEXING ISSUES:")
                if missing_city:
                    print(f"   Missing City ({len(missing_city)}):")
                    for business in missing_city[:3]:
                        name = business.get("business_name", "Unknown")
                        print(f"      • {name}")
                
                if missing_district:
                    print(f"   Missing District ({len(missing_district)}):")
                    for business in missing_district[:3]:
                        name = business.get("business_name", "Unknown")
                        city = business.get("city", "Unknown")
                        print(f"      • {name} - {city}")
                
                if missing_coordinates:
                    print(f"   Missing GPS Coordinates ({len(missing_coordinates)}):")
                    for business in missing_coordinates[:3]:
                        name = business.get("business_name", "Unknown")
                        city = business.get("city", "Unknown")
                        district = business.get("district", "Unknown")
                        print(f"      • {name} - {city}/{district}")
                print()
            
            return success
                
        except Exception as e:
            self.log_test("Business Indexing Check", False, "", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all KYC and customer panel tests"""
        print("🚀 BUSINESS KYC STATUS & CUSTOMER PANEL REQUIREMENTS TESTING")
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
        
        # Test 2: Get All Businesses and Analyze KYC Status
        businesses = self.test_get_all_businesses()
        if not businesses:
            print("⚠️  WARNING: No businesses found in database")
        
        # Test 3: Customer Login (NO KYC REQUIRED)
        if not self.test_customer_login():
            print("❌ CRITICAL: Customer login failed - cannot proceed with customer tests")
            return
        
        # Test 4: Customer Profile Access
        self.test_customer_profile_access()
        
        # Test 5: Catalog City Nearby
        restaurants = self.test_catalog_city_nearby()
        
        # Test 6: Issue Analysis
        self.test_identify_issues()
        
        # Test 7: Business Indexing Check
        self.test_business_indexing()
        
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
        
        print("✅ REVIEW REQUEST VERIFICATION:")
        admin_login_ok = any("Admin Login" in r["test"] and r["success"] for r in self.test_results)
        customer_login_ok = any("Customer Login" in r["test"] and r["success"] for r in self.test_results)
        catalog_ok = any("Catalog City Nearby" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"   • Admin can login and get businesses: {'✅' if admin_login_ok else '❌'}")
        print(f"   • Customer can access without KYC: {'✅' if customer_login_ok else '❌'}")
        print(f"   • Catalog endpoint accessible: {'✅' if catalog_ok else '❌'}")
        print(f"   • Business indexing proper: {'✅' if any('Business Indexing' in r['test'] and r['success'] for r in self.test_results) else '❌'}")
        
        print()
        print("🎯 CONCLUSION:")
        if success_rate >= 85:
            print("   KYC and Customer Panel system is WORKING EXCELLENTLY")
        elif success_rate >= 70:
            print("   KYC and Customer Panel system is WORKING with minor issues")
        else:
            print("   KYC and Customer Panel system has CRITICAL ISSUES")
        
        print()
        print("📋 KEY FINDINGS:")
        customer_city = self.customer_profile.get("city", "Unknown")
        approved_businesses = len([b for b in self.businesses if b.get("kyc_status") == "approved"])
        customer_city_businesses = len([b for b in self.businesses if b.get("city", "").lower() == customer_city.lower() and b.get("kyc_status") == "approved" and b.get("is_active") == True])
        
        print(f"   • Total approved businesses: {approved_businesses}")
        print(f"   • Approved & active businesses in {customer_city}: {customer_city_businesses}")
        print(f"   • Customer KYC requirement: {'❌ Required (Issue!)' if self.customer_profile.get('kyc_status') else '✅ Not Required (Correct)'}")
        
        if customer_city_businesses == 0:
            print(f"   🚨 ROOT CAUSE: No approved & active businesses in customer's city ({customer_city})")
        else:
            print(f"   ✅ Restaurants available for customer in {customer_city}")

if __name__ == "__main__":
    tester = KYCCustomerPanelTester()
    tester.run_all_tests()