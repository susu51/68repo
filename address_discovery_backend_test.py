#!/usr/bin/env python3
"""
URGENT USER ISSUE INVESTIGATION - Customer Address & Restaurant Discovery Problem

The user reports: "Adres giriyorum henüz kayıtlı adresiniz yok diyor keşfet kısmında gözükmüyor" 
(Adding address but says "no registered address yet" and doesn't appear in discovery section)

Test Coverage:
1. Customer Authentication System
2. Customer Address Management (POST/GET/PUT/DELETE /api/user/addresses)
3. Restaurant Discovery System (GET /api/businesses with location parameters)
4. Address-Discovery Integration (how addresses affect restaurant visibility)
5. Data Verification (database consistency checks)
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://mockless-api.preview.emergentagent.com/api"
CUSTOMER_EMAIL = "testcustomer@example.com"
CUSTOMER_PASSWORD = "test123"

class AddressDiscoveryTester:
    def __init__(self):
        self.session = requests.Session()
        self.customer_token = None
        self.customer_id = None
        self.test_results = []
        self.created_addresses = []  # Track addresses created during testing
        
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

    def authenticate_customer(self):
        """Authenticate as customer user"""
        print("🔐 AUTHENTICATING CUSTOMER USER...")
        
        try:
            login_data = {
                "email": CUSTOMER_EMAIL,
                "password": CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                user_data = data.get("user", {})
                self.customer_id = user_data.get("id")
                
                if self.customer_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.customer_token}"
                    })
                    self.log_test("Customer Authentication", True, 
                                f"Successfully authenticated customer, token length: {len(self.customer_token)}, user_id: {self.customer_id}")
                    return True
                else:
                    self.log_test("Customer Authentication", False, "No access token in response")
            else:
                self.log_test("Customer Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Authentication error: {str(e)}")
        
        return False

    def test_jwt_token_validation(self):
        """Test JWT token validation via /me endpoint"""
        print("\n🔍 TESTING JWT TOKEN VALIDATION")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/me")
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("id")
                email = data.get("email")
                role = data.get("role")
                
                self.log_test("JWT Token Validation", True, 
                            f"Token valid - User ID: {user_id}, Email: {email}, Role: {role}")
                
                # Update customer_id if not set
                if not self.customer_id:
                    self.customer_id = user_id
                    
            elif response.status_code == 401:
                self.log_test("JWT Token Validation", False, 
                            "Token invalid or expired - 401 Unauthorized")
            else:
                self.log_test("JWT Token Validation", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("JWT Token Validation", False, f"Request error: {str(e)}")

    def test_address_retrieval(self):
        """Test GET /api/user/addresses - Address listing"""
        print("\n📍 TESTING ADDRESS RETRIEVAL")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            if response.status_code == 200:
                data = response.json()
                addresses = data if isinstance(data, list) else data.get("addresses", [])
                
                self.log_test("GET /api/user/addresses", True, 
                            f"Successfully retrieved {len(addresses)} addresses for customer")
                
                # Log address details for debugging
                if addresses:
                    print("   📋 EXISTING ADDRESSES:")
                    for i, addr in enumerate(addresses[:3]):  # Show first 3
                        print(f"      {i+1}. {addr.get('label', 'No Label')} - {addr.get('description', 'No Description')}")
                        print(f"         City: {addr.get('city', 'N/A')}, Coords: ({addr.get('lat', 'N/A')}, {addr.get('lng', 'N/A')})")
                
                return addresses
                
            elif response.status_code == 403:
                self.log_test("GET /api/user/addresses", False, 
                            "Access denied - authentication may not be working properly")
            elif response.status_code == 404:
                self.log_test("GET /api/user/addresses", False, 
                            "Endpoint not found - address API not implemented")
            else:
                self.log_test("GET /api/user/addresses", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/user/addresses", False, f"Request error: {str(e)}")
        
        return []

    def test_address_creation(self):
        """Test POST /api/user/addresses - Address creation"""
        print("\n➕ TESTING ADDRESS CREATION")
        
        # Test address data with realistic Turkish locations
        test_addresses = [
            {
                "label": "Ev Adresim",
                "description": "Kadıköy Moda Mahallesi, İstanbul",
                "city": "İstanbul",
                "lat": 40.9876,
                "lng": 29.0256
            },
            {
                "label": "İş Yerim", 
                "description": "Levent Plaza, Beşiktaş, İstanbul",
                "city": "İstanbul",
                "lat": 41.0814,
                "lng": 29.0092
            }
        ]
        
        created_count = 0
        
        for i, address_data in enumerate(test_addresses):
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=address_data)
                
                if response.status_code == 200 or response.status_code == 201:
                    data = response.json()
                    address_id = data.get("id") or data.get("address_id")
                    
                    if address_id:
                        self.created_addresses.append(address_id)
                        created_count += 1
                        
                        self.log_test(f"POST /api/user/addresses (Test {i+1})", True, 
                                    f"Successfully created address '{address_data['label']}' with ID: {address_id}")
                    else:
                        self.log_test(f"POST /api/user/addresses (Test {i+1})", False, 
                                    f"Address created but no ID returned: {data}")
                        
                elif response.status_code == 403:
                    self.log_test(f"POST /api/user/addresses (Test {i+1})", False, 
                                "Access denied - authentication may not be working properly")
                elif response.status_code == 422:
                    self.log_test(f"POST /api/user/addresses (Test {i+1})", False, 
                                f"Validation error - {response.text}")
                else:
                    self.log_test(f"POST /api/user/addresses (Test {i+1})", False, 
                                f"Unexpected response: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"POST /api/user/addresses (Test {i+1})", False, f"Request error: {str(e)}")
        
        return created_count

    def test_address_persistence(self):
        """Test if created addresses are properly saved and retrievable"""
        print("\n💾 TESTING ADDRESS PERSISTENCE")
        
        try:
            # Retrieve addresses again to verify persistence
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                data = response.json()
                addresses = data if isinstance(data, list) else data.get("addresses", [])
                
                # Check if our created addresses are present
                found_addresses = 0
                for created_id in self.created_addresses:
                    for addr in addresses:
                        if addr.get("id") == created_id:
                            found_addresses += 1
                            break
                
                if found_addresses == len(self.created_addresses):
                    self.log_test("Address Persistence Check", True, 
                                f"All {found_addresses} created addresses found in database")
                else:
                    self.log_test("Address Persistence Check", False, 
                                f"Only {found_addresses}/{len(self.created_addresses)} created addresses found in database")
                
                return addresses
                
            else:
                self.log_test("Address Persistence Check", False, 
                            f"Failed to retrieve addresses for persistence check: {response.status_code}")
                
        except Exception as e:
            self.log_test("Address Persistence Check", False, f"Request error: {str(e)}")
        
        return []

    def test_restaurant_discovery_basic(self):
        """Test GET /api/businesses - Basic restaurant discovery"""
        print("\n🍽️ TESTING BASIC RESTAURANT DISCOVERY")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                self.log_test("GET /api/businesses (Basic)", True, 
                            f"Successfully retrieved {len(businesses)} restaurants")
                
                # Log restaurant details for debugging
                if businesses:
                    print("   🏪 AVAILABLE RESTAURANTS:")
                    for i, business in enumerate(businesses[:5]):  # Show first 5
                        name = business.get("business_name") or business.get("name", "Unknown")
                        city = business.get("city", "N/A")
                        kyc_status = business.get("kyc_status", "N/A")
                        print(f"      {i+1}. {name} - {city} (KYC: {kyc_status})")
                
                return businesses
                
            elif response.status_code == 404:
                self.log_test("GET /api/businesses (Basic)", False, 
                            "Endpoint not found - businesses API not implemented")
            else:
                self.log_test("GET /api/businesses (Basic)", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/businesses (Basic)", False, f"Request error: {str(e)}")
        
        return []

    def test_restaurant_discovery_with_location(self):
        """Test GET /api/businesses with location parameters"""
        print("\n📍 TESTING LOCATION-BASED RESTAURANT DISCOVERY")
        
        # Test with Istanbul coordinates (where our test addresses are)
        test_locations = [
            {"lat": 40.9876, "lng": 29.0256, "name": "Kadıköy Area"},
            {"lat": 41.0814, "lng": 29.0092, "name": "Levent Area"}
        ]
        
        for location in test_locations:
            try:
                params = {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "radius": 5000  # 5km radius
                }
                
                response = self.session.get(f"{BACKEND_URL}/businesses", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    businesses = data if isinstance(data, list) else data.get("businesses", [])
                    
                    self.log_test(f"GET /api/businesses (Location: {location['name']})", True, 
                                f"Found {len(businesses)} restaurants near {location['name']}")
                    
                elif response.status_code == 404:
                    self.log_test(f"GET /api/businesses (Location: {location['name']})", False, 
                                "Endpoint not found - location-based discovery not implemented")
                else:
                    self.log_test(f"GET /api/businesses (Location: {location['name']})", False, 
                                f"Unexpected response: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"GET /api/businesses (Location: {location['name']})", False, f"Request error: {str(e)}")

    def test_restaurant_discovery_with_city_filter(self):
        """Test GET /api/businesses with city filtering"""
        print("\n🏙️ TESTING CITY-BASED RESTAURANT DISCOVERY")
        
        test_cities = ["İstanbul", "istanbul", "ISTANBUL"]
        
        for city in test_cities:
            try:
                params = {"city": city}
                response = self.session.get(f"{BACKEND_URL}/businesses", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    businesses = data if isinstance(data, list) else data.get("businesses", [])
                    
                    self.log_test(f"GET /api/businesses (City: {city})", True, 
                                f"Found {len(businesses)} restaurants in {city}")
                    
                elif response.status_code == 500:
                    self.log_test(f"GET /api/businesses (City: {city})", False, 
                                f"Server error - possible city normalization issue: {response.text}")
                elif response.status_code == 404:
                    self.log_test(f"GET /api/businesses (City: {city})", False, 
                                "Endpoint not found - city filtering not implemented")
                else:
                    self.log_test(f"GET /api/businesses (City: {city})", False, 
                                f"Unexpected response: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"GET /api/businesses (City: {city})", False, f"Request error: {str(e)}")

    def test_address_discovery_integration(self):
        """Test the integration between saved addresses and restaurant discovery"""
        print("\n🔗 TESTING ADDRESS-DISCOVERY INTEGRATION")
        
        # Get current addresses
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            if response.status_code != 200:
                self.log_test("Address-Discovery Integration", False, 
                            "Cannot test integration - address retrieval failed")
                return
            
            data = response.json()
            addresses = data if isinstance(data, list) else data.get("addresses", [])
            
            if not addresses:
                self.log_test("Address-Discovery Integration", False, 
                            "Cannot test integration - no addresses found")
                return
            
            # Test discovery using coordinates from saved addresses
            integration_tests_passed = 0
            total_integration_tests = 0
            
            for i, address in enumerate(addresses[:2]):  # Test first 2 addresses
                lat = address.get("lat")
                lng = address.get("lng")
                label = address.get("label", f"Address {i+1}")
                
                if lat and lng:
                    total_integration_tests += 1
                    
                    try:
                        params = {"lat": lat, "lng": lng, "radius": 3000}
                        response = self.session.get(f"{BACKEND_URL}/businesses", params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            businesses = data if isinstance(data, list) else data.get("businesses", [])
                            
                            integration_tests_passed += 1
                            print(f"   ✅ Address '{label}' → Found {len(businesses)} nearby restaurants")
                        else:
                            print(f"   ❌ Address '{label}' → Discovery failed: {response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ Address '{label}' → Error: {str(e)}")
                else:
                    print(f"   ⚠️ Address '{label}' → Missing coordinates (lat: {lat}, lng: {lng})")
            
            if total_integration_tests > 0:
                success_rate = (integration_tests_passed / total_integration_tests) * 100
                if success_rate >= 100:
                    self.log_test("Address-Discovery Integration", True, 
                                f"Perfect integration - {integration_tests_passed}/{total_integration_tests} address-based discoveries successful")
                elif success_rate >= 50:
                    self.log_test("Address-Discovery Integration", True, 
                                f"Partial integration - {integration_tests_passed}/{total_integration_tests} address-based discoveries successful ({success_rate:.1f}%)")
                else:
                    self.log_test("Address-Discovery Integration", False, 
                                f"Poor integration - {integration_tests_passed}/{total_integration_tests} address-based discoveries successful ({success_rate:.1f}%)")
            else:
                self.log_test("Address-Discovery Integration", False, 
                            "No addresses with valid coordinates found for integration testing")
                
        except Exception as e:
            self.log_test("Address-Discovery Integration", False, f"Integration test error: {str(e)}")

    def test_data_consistency_checks(self):
        """Test data consistency between addresses and businesses"""
        print("\n🔍 TESTING DATA CONSISTENCY")
        
        consistency_issues = []
        
        # Check if addresses have required fields
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            if response.status_code == 200:
                data = response.json()
                addresses = data if isinstance(data, list) else data.get("addresses", [])
                
                missing_coords = 0
                missing_cities = 0
                
                for addr in addresses:
                    if not addr.get("lat") or not addr.get("lng"):
                        missing_coords += 1
                    if not addr.get("city"):
                        missing_cities += 1
                
                if missing_coords > 0:
                    consistency_issues.append(f"{missing_coords} addresses missing coordinates")
                if missing_cities > 0:
                    consistency_issues.append(f"{missing_cities} addresses missing city information")
                    
        except Exception as e:
            consistency_issues.append(f"Address consistency check failed: {str(e)}")
        
        # Check if businesses have location data
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                missing_location = 0
                missing_city = 0
                pending_kyc = 0
                
                for business in businesses:
                    if not business.get("lat") and not business.get("lng") and not business.get("location"):
                        missing_location += 1
                    if not business.get("city"):
                        missing_city += 1
                    if business.get("kyc_status") == "pending":
                        pending_kyc += 1
                
                if missing_location > 0:
                    consistency_issues.append(f"{missing_location} businesses missing location data")
                if missing_city > 0:
                    consistency_issues.append(f"{missing_city} businesses missing city information")
                if pending_kyc > 0:
                    consistency_issues.append(f"{pending_kyc} businesses have pending KYC status (may not appear to customers)")
                    
        except Exception as e:
            consistency_issues.append(f"Business consistency check failed: {str(e)}")
        
        if not consistency_issues:
            self.log_test("Data Consistency Check", True, 
                        "No major data consistency issues found")
        else:
            self.log_test("Data Consistency Check", False, 
                        f"Found {len(consistency_issues)} consistency issues: {'; '.join(consistency_issues)}")

    def diagnose_user_issue(self):
        """Diagnose the specific user issue based on test results"""
        print("\n🔬 DIAGNOSING USER ISSUE")
        print("=" * 50)
        
        # Analyze test results to identify the root cause
        auth_working = any(r["success"] and "authentication" in r["test"].lower() for r in self.test_results)
        address_creation_working = any(r["success"] and "post /api/user/addresses" in r["test"].lower() for r in self.test_results)
        address_retrieval_working = any(r["success"] and "get /api/user/addresses" in r["test"].lower() for r in self.test_results)
        restaurant_discovery_working = any(r["success"] and "businesses" in r["test"].lower() for r in self.test_results)
        integration_working = any(r["success"] and "integration" in r["test"].lower() for r in self.test_results)
        
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        if not auth_working:
            print("❌ CRITICAL: Customer authentication is not working")
            print("   → User cannot save addresses without proper authentication")
            print("   → Fix: Check JWT token generation and validation")
        
        elif not address_creation_working:
            print("❌ CRITICAL: Address creation (POST /api/user/addresses) is not working")
            print("   → User's addresses are not being saved to database")
            print("   → Fix: Check address creation endpoint implementation")
        
        elif not address_retrieval_working:
            print("❌ CRITICAL: Address retrieval (GET /api/user/addresses) is not working")
            print("   → User cannot see their saved addresses")
            print("   → Fix: Check address listing endpoint implementation")
        
        elif not restaurant_discovery_working:
            print("❌ CRITICAL: Restaurant discovery (GET /api/businesses) is not working")
            print("   → No restaurants appear in discovery section")
            print("   → Fix: Check business listing endpoint implementation")
        
        elif not integration_working:
            print("❌ CRITICAL: Address-Discovery integration is broken")
            print("   → Addresses exist but don't affect restaurant discovery")
            print("   → Fix: Check location-based filtering in business endpoints")
        
        else:
            print("✅ BACKEND SYSTEMS APPEAR TO BE WORKING")
            print("   → The issue may be in the frontend implementation")
            print("   → Check frontend API calls and state management")
        
        # Additional specific checks
        consistency_issues = [r for r in self.test_results if not r["success"] and "consistency" in r["test"].lower()]
        if consistency_issues:
            print("\n⚠️ DATA CONSISTENCY ISSUES DETECTED:")
            for issue in consistency_issues:
                print(f"   → {issue['details']}")

    def cleanup_test_data(self):
        """Clean up addresses created during testing"""
        print("\n🧹 CLEANING UP TEST DATA")
        
        if not self.created_addresses:
            print("   No test addresses to clean up")
            return
        
        cleaned_count = 0
        for address_id in self.created_addresses:
            try:
                response = self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}")
                if response.status_code in [200, 204, 404]:  # 404 is OK (already deleted)
                    cleaned_count += 1
            except Exception as e:
                print(f"   Failed to delete address {address_id}: {str(e)}")
        
        print(f"   Cleaned up {cleaned_count}/{len(self.created_addresses)} test addresses")

    def run_all_tests(self):
        """Run all address and discovery tests"""
        print("🚀 STARTING ADDRESS & RESTAURANT DISCOVERY INVESTIGATION")
        print("=" * 70)
        print("🎯 USER ISSUE: 'Adres giriyorum henüz kayıtlı adresiniz yok diyor keşfet kısmında gözükmüyor'")
        print("=" * 70)
        
        # Step 1: Authentication
        auth_success = self.authenticate_customer()
        if not auth_success:
            print("\n❌ CRITICAL: Cannot proceed without customer authentication")
            return
        
        # Step 2: JWT Token Validation
        self.test_jwt_token_validation()
        
        # Step 3: Address Management Tests
        existing_addresses = self.test_address_retrieval()
        created_count = self.test_address_creation()
        if created_count > 0:
            self.test_address_persistence()
        
        # Step 4: Restaurant Discovery Tests
        self.test_restaurant_discovery_basic()
        self.test_restaurant_discovery_with_location()
        self.test_restaurant_discovery_with_city_filter()
        
        # Step 5: Integration Tests
        self.test_address_discovery_integration()
        
        # Step 6: Data Consistency
        self.test_data_consistency_checks()
        
        # Step 7: Diagnosis
        self.diagnose_user_issue()
        
        # Step 8: Generate Summary
        self.generate_summary()
        
        # Step 9: Cleanup
        self.cleanup_test_data()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 ADDRESS & RESTAURANT DISCOVERY TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    → {result['details']}")
        
        print(f"\n📝 FINAL CONCLUSION:")
        if success_rate >= 90:
            print("✅ EXCELLENT: Address & Discovery system working correctly")
            print("   → User issue likely in frontend implementation")
        elif success_rate >= 70:
            print("⚠️ GOOD: Most functionality working with minor issues")
            print("   → Some backend fixes needed")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Significant issues detected")
            print("   → Multiple backend fixes required")
        else:
            print("❌ CRITICAL: Major system failures detected")
            print("   → Extensive backend fixes required")

if __name__ == "__main__":
    tester = AddressDiscoveryTester()
    tester.run_all_tests()