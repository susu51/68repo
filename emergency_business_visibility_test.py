#!/usr/bin/env python3
"""
EMERGENCY BUSINESS VISIBILITY FIX TESTING
Critical test for user-reported issue: Customer can't see newly created restaurants

IMMEDIATE FOCUS:
1. GET /api/admin/businesses - Check existing businesses and KYC status
2. PATCH /api/admin/businesses/{business_id}/status - Approve pending businesses
3. GET /api/restaurants - Verify customer restaurant discovery
4. Test complete customer flow - login and verify restaurant visibility

TARGET: Get "Test Restoranı" and "Pizza Palace İstanbul" visible to customers
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration from environment
BACKEND_URL = "https://meal-dash-163.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"}
}

class EmergencyBusinessVisibilityTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.pending_businesses = []
        self.approved_count = 0
        
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
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        return success

    def authenticate_user(self, role):
        """Authenticate user and get JWT token"""
        try:
            creds = TEST_CREDENTIALS[role]
            response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                
                self.tokens[role] = token
                return self.log_test(
                    f"{role.title()} Authentication",
                    True,
                    f"Token: {len(token)} chars, User: {user_data.get('email')}, Role: {user_data.get('role')}"
                )
            else:
                return self.log_test(
                    f"{role.title()} Authentication",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            return self.log_test(f"{role.title()} Authentication", False, error=str(e))

    def get_admin_businesses(self):
        """Step 1: Get current business list and identify pending businesses"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{BACKEND_URL}/admin/businesses", headers=headers)
            
            if response.status_code == 200:
                businesses = response.json()
                total_businesses = len(businesses)
                
                # Identify pending businesses
                self.pending_businesses = [
                    b for b in businesses 
                    if b.get("kyc_status") == "pending"
                ]
                
                approved_businesses = [
                    b for b in businesses 
                    if b.get("kyc_status") == "approved"
                ]
                
                self.approved_count = len(approved_businesses)
                pending_count = len(self.pending_businesses)
                
                # Look for target businesses
                target_businesses = []
                for business in businesses:
                    name = business.get("business_name", "")
                    if "Test Restoranı" in name or "Pizza Palace İstanbul" in name:
                        target_businesses.append({
                            "name": name,
                            "id": business.get("id"),
                            "kyc_status": business.get("kyc_status")
                        })
                
                details = f"Total: {total_businesses}, Approved: {self.approved_count}, Pending: {pending_count}"
                if target_businesses:
                    details += f", Target businesses found: {[b['name'] + ' (' + b['kyc_status'] + ')' for b in target_businesses]}"
                
                return self.log_test(
                    "GET /api/admin/businesses",
                    True,
                    details
                )
            else:
                return self.log_test(
                    "GET /api/admin/businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            return self.log_test("GET /api/admin/businesses", False, error=str(e))

    def approve_pending_businesses(self):
        """Step 2: Approve all pending businesses"""
        if not self.pending_businesses:
            return self.log_test(
                "Approve Pending Businesses",
                True,
                "No pending businesses found - all already approved"
            )
        
        approved_count = 0
        failed_count = 0
        
        for business in self.pending_businesses:
            try:
                business_id = business.get("id")
                business_name = business.get("business_name", "Unknown")
                
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                payload = {"kyc_status": "approved"}
                
                response = requests.patch(
                    f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    approved_count += 1
                    print(f"   ✅ Approved: {business_name}")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to approve: {business_name} - Status: {response.status_code}")
                    
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error approving {business_name}: {str(e)}")
        
        success = failed_count == 0
        details = f"Approved: {approved_count}/{len(self.pending_businesses)} businesses"
        if failed_count > 0:
            details += f", Failed: {failed_count}"
            
        return self.log_test("Approve Pending Businesses", success, details)

    def verify_customer_restaurants(self):
        """Step 3: Verify customer-facing restaurant endpoint"""
        try:
            # Test without authentication first (public endpoint)
            response = requests.get(f"{BACKEND_URL}/restaurants")
            
            if response.status_code == 200:
                restaurants = response.json()
                restaurant_count = len(restaurants)
                
                # Look for target restaurants
                target_found = []
                for restaurant in restaurants:
                    name = restaurant.get("business_name") or restaurant.get("name", "")
                    if "Test Restoranı" in name or "Pizza Palace İstanbul" in name:
                        target_found.append(name)
                
                details = f"Found {restaurant_count} restaurants"
                if target_found:
                    details += f", Target restaurants visible: {target_found}"
                else:
                    details += ", Target restaurants NOT found"
                
                return self.log_test(
                    "GET /api/restaurants (Customer View)",
                    True,
                    details
                )
            else:
                return self.log_test(
                    "GET /api/restaurants (Customer View)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            return self.log_test("GET /api/restaurants (Customer View)", False, error=str(e))

    def test_customer_flow(self):
        """Step 4: Test complete customer flow"""
        try:
            # Customer login already done in authentication
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            
            # Test customer restaurant discovery
            response = requests.get(f"{BACKEND_URL}/restaurants", headers=headers)
            
            if response.status_code == 200:
                restaurants = response.json()
                restaurant_count = len(restaurants)
                
                # Check if restaurants have proper data structure
                valid_restaurants = []
                for restaurant in restaurants:
                    if restaurant.get("business_name") and restaurant.get("kyc_status") == "approved":
                        valid_restaurants.append(restaurant.get("business_name"))
                
                # Look for target restaurants specifically
                target_restaurants = []
                for restaurant in restaurants:
                    name = restaurant.get("business_name") or restaurant.get("name", "")
                    if "Test Restoranı" in name or "Pizza Palace İstanbul" in name:
                        target_restaurants.append({
                            "name": name,
                            "kyc_status": restaurant.get("kyc_status"),
                            "has_menu": len(restaurant.get("menu", [])) > 0 if "menu" in restaurant else "unknown"
                        })
                
                success = restaurant_count > 0 and len(target_restaurants) > 0
                details = f"Customer sees {restaurant_count} restaurants, {len(valid_restaurants)} approved"
                
                if target_restaurants:
                    target_info = [f"{r['name']} (status: {r['kyc_status']})" for r in target_restaurants]
                    details += f", Target restaurants: {target_info}"
                else:
                    details += ", TARGET RESTAURANTS NOT VISIBLE TO CUSTOMER"
                
                return self.log_test("Customer Restaurant Discovery Flow", success, details)
            else:
                return self.log_test(
                    "Customer Restaurant Discovery Flow",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            return self.log_test("Customer Restaurant Discovery Flow", False, error=str(e))

    def test_city_filtering(self):
        """Test city filtering functionality"""
        try:
            # Test with Istanbul filter
            response = requests.get(f"{BACKEND_URL}/restaurants?city=istanbul")
            
            if response.status_code == 200:
                istanbul_restaurants = response.json()
                istanbul_count = len(istanbul_restaurants)
                
                # Check if Pizza Palace İstanbul is in Istanbul results
                pizza_palace_found = any(
                    "Pizza Palace İstanbul" in (r.get("business_name") or r.get("name", ""))
                    for r in istanbul_restaurants
                )
                
                details = f"Istanbul filter: {istanbul_count} restaurants"
                if pizza_palace_found:
                    details += ", Pizza Palace İstanbul found"
                else:
                    details += ", Pizza Palace İstanbul NOT found"
                
                return self.log_test("City Filtering (Istanbul)", True, details)
            else:
                return self.log_test(
                    "City Filtering (Istanbul)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            return self.log_test("City Filtering (Istanbul)", False, error=str(e))

    def run_emergency_tests(self):
        """Run all emergency business visibility tests"""
        print("🚨 EMERGENCY BUSINESS VISIBILITY FIX TESTING")
        print("=" * 60)
        print("CRITICAL: Customer can't see newly created restaurants")
        print("TARGET: Make 'Test Restoranı' and 'Pizza Palace İstanbul' visible")
        print()
        
        # Step 1: Authenticate admin and customer
        print("STEP 1: Authentication")
        admin_auth = self.authenticate_user("admin")
        customer_auth = self.authenticate_user("customer")
        
        if not admin_auth or not customer_auth:
            print("❌ CRITICAL: Authentication failed - cannot proceed")
            return False
        
        print()
        
        # Step 2: Get current business list
        print("STEP 2: Get Current Business List")
        business_list = self.get_admin_businesses()
        print()
        
        # Step 3: Approve pending businesses
        print("STEP 3: Approve Pending Businesses")
        approval_result = self.approve_pending_businesses()
        print()
        
        # Step 4: Verify customer restaurant endpoint
        print("STEP 4: Verify Customer Restaurant Endpoint")
        restaurant_verification = self.verify_customer_restaurants()
        print()
        
        # Step 5: Test complete customer flow
        print("STEP 5: Test Customer Flow")
        customer_flow = self.test_customer_flow()
        print()
        
        # Step 6: Test city filtering
        print("STEP 6: Test City Filtering")
        city_filtering = self.test_city_filtering()
        print()
        
        # Summary
        print("=" * 60)
        print("🎯 EMERGENCY FIX SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Critical success criteria
        critical_success = (
            business_list and 
            approval_result and 
            restaurant_verification and 
            customer_flow
        )
        
        if critical_success:
            print("✅ EMERGENCY FIX STATUS: SUCCESS")
            print("   Customers should now be able to see approved restaurants")
        else:
            print("❌ EMERGENCY FIX STATUS: FAILED")
            print("   Customer visibility issue NOT resolved")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
            if result["error"]:
                print(f"   ERROR: {result['error']}")
        
        return critical_success

if __name__ == "__main__":
    tester = EmergencyBusinessVisibilityTester()
    success = tester.run_emergency_tests()
    
    if success:
        print("\n🎉 EMERGENCY FIX COMPLETED SUCCESSFULLY")
        print("Customers can now see approved restaurants in their dashboard")
    else:
        print("\n🚨 EMERGENCY FIX FAILED")
        print("Customer visibility issue requires further investigation")