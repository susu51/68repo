#!/usr/bin/env python3
"""
CRITICAL LOCATION & INTEGRATION ISSUES BACKEND TESTING
======================================================

Testing 4 critical user-reported problems:
1. Business Registration City Issue - cities defaulting to İstanbul
2. Menu Visibility Issue - restaurant menus not showing to customers  
3. Address Registration Issue - city/district saving incorrectly
4. Discovery Filtering Issue - location-based restaurant filtering not working

Focus Areas:
- City normalization and storage
- Business-menu integration
- Address creation and persistence
- Location-based discovery filtering
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
import sys
import os

# Backend URL from environment
BACKEND_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"

class LocationIntegrationTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.customer_token = None
        self.business_tokens = {}
        self.test_results = []
        self.created_businesses = []
        self.created_addresses = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name, success, details="", data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and data:
            print(f"    Data: {data}")
        print()
        
    async def authenticate_admin(self):
        """Authenticate as admin"""
        try:
            login_data = {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    self.log_result("Admin Authentication", True, f"Token length: {len(self.admin_token)} chars")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Admin Authentication", False, f"Status: {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
            
    async def authenticate_customer(self):
        """Authenticate as test customer"""
        try:
            login_data = {
                "email": "testcustomer@example.com",
                "password": "test123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.customer_token = data["access_token"]
                    self.log_result("Customer Authentication", True, f"Token length: {len(self.customer_token)} chars")
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Customer Authentication", False, f"Status: {response.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("Customer Authentication", False, f"Exception: {str(e)}")
            return False

    async def test_business_registration_cities(self):
        """
        CRITICAL TEST 1: Business Registration City Issue
        Test if cities are being saved correctly or defaulting to İstanbul
        """
        print("🏢 TESTING BUSINESS REGISTRATION CITY ISSUE")
        print("=" * 60)
        
        test_cities = [
            {"city": "Niğde", "district": "Merkez", "expected": "Niğde"},
            {"city": "Ankara", "district": "Çankaya", "expected": "Ankara"},
            {"city": "İzmir", "district": "Konak", "expected": "İzmir"},
            {"city": "Gaziantep", "district": "Şahinbey", "expected": "Gaziantep"},
            {"city": "Bursa", "district": "Osmangazi", "expected": "Bursa"}
        ]
        
        for i, test_case in enumerate(test_cities):
            city = test_case["city"]
            district = test_case["district"]
            expected = test_case["expected"]
            
            # Create unique business registration
            business_email = f"test-{city.lower()}-{i}@example.com"
            business_data = {
                "email": business_email,
                "password": "test123",
                "business_name": f"{city} Test Restoranı {i}",
                "tax_number": f"123456789{i:02d}",
                "address": f"{city} Test Adresi {i}",
                "city": city,
                "district": district,
                "business_category": "gida",
                "description": f"Test restaurant in {city}"
            }
            
            try:
                # Register business
                async with self.session.post(f"{BACKEND_URL}/register/business", json=business_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        business_id = data["user_data"]["id"]
                        self.created_businesses.append(business_id)
                        
                        # Store business token for later use
                        self.business_tokens[business_id] = data["access_token"]
                        
                        # Check if city was saved correctly
                        saved_city = data["user_data"]["city"]
                        saved_district = data["user_data"].get("district", "")
                        city_normalized = data["user_data"].get("city_normalized", "")
                        
                        if saved_city == expected:
                            self.log_result(
                                f"Business Registration - {city} City Storage", 
                                True, 
                                f"City saved correctly: '{saved_city}', District: '{saved_district}', Normalized: '{city_normalized}'"
                            )
                        else:
                            self.log_result(
                                f"Business Registration - {city} City Storage", 
                                False, 
                                f"City INCORRECT: Expected '{expected}', Got '{saved_city}', District: '{saved_district}'"
                            )
                            
                        # Verify in database by fetching business details
                        if self.admin_token:
                            headers = {"Authorization": f"Bearer {self.admin_token}"}
                            async with self.session.get(f"{BACKEND_URL}/admin/businesses/{business_id}", headers=headers) as verify_response:
                                if verify_response.status == 200:
                                    verify_data = await verify_response.json()
                                    db_city = verify_data.get("city", "")
                                    db_district = verify_data.get("district", "")
                                    db_city_normalized = verify_data.get("city_normalized", "")
                                    
                                    if db_city == expected:
                                        self.log_result(
                                            f"Database Verification - {city} City Persistence", 
                                            True, 
                                            f"DB City: '{db_city}', District: '{db_district}', Normalized: '{db_city_normalized}'"
                                        )
                                    else:
                                        self.log_result(
                                            f"Database Verification - {city} City Persistence", 
                                            False, 
                                            f"DB City INCORRECT: Expected '{expected}', Got '{db_city}'"
                                        )
                                        
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Business Registration - {city}", 
                            False, 
                            f"Registration failed: {response.status}", 
                            error_text
                        )
                        
            except Exception as e:
                self.log_result(f"Business Registration - {city}", False, f"Exception: {str(e)}")

    async def test_menu_visibility_integration(self):
        """
        CRITICAL TEST 2: Menu Visibility Issue
        Test if business menus are visible to customers
        """
        print("🍽️ TESTING MENU VISIBILITY INTEGRATION")
        print("=" * 60)
        
        # First, create products for registered businesses
        for business_id, token in self.business_tokens.items():
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create test products for this business
            test_products = [
                {
                    "name": "Test Döner Kebap",
                    "description": "Lezzetli döner kebap",
                    "price": 45.0,
                    "category": "Ana Yemek",
                    "preparation_time_minutes": 20,
                    "is_available": True
                },
                {
                    "name": "Test Pizza Margherita",
                    "description": "Klasik margherita pizza",
                    "price": 65.0,
                    "category": "Pizza",
                    "preparation_time_minutes": 25,
                    "is_available": True
                },
                {
                    "name": "Test Ayran",
                    "description": "Soğuk ayran",
                    "price": 8.0,
                    "category": "İçecek",
                    "preparation_time_minutes": 2,
                    "is_available": True
                }
            ]
            
            created_products = []
            for product in test_products:
                try:
                    async with self.session.post(f"{BACKEND_URL}/products", json=product, headers=headers) as response:
                        if response.status == 200:
                            product_data = await response.json()
                            created_products.append(product_data)
                            self.log_result(
                                f"Product Creation - {product['name']}", 
                                True, 
                                f"Business: {business_id}, Product ID: {product_data.get('id', 'N/A')}"
                            )
                        else:
                            error_text = await response.text()
                            self.log_result(
                                f"Product Creation - {product['name']}", 
                                False, 
                                f"Status: {response.status}", 
                                error_text
                            )
                except Exception as e:
                    self.log_result(f"Product Creation - {product['name']}", False, f"Exception: {str(e)}")
            
            # Test menu visibility for this business
            try:
                async with self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products") as response:
                    if response.status == 200:
                        menu_data = await response.json()
                        product_count = len(menu_data) if isinstance(menu_data, list) else 0
                        
                        if product_count > 0:
                            self.log_result(
                                f"Menu Visibility - Business {business_id}", 
                                True, 
                                f"Found {product_count} products in menu"
                            )
                        else:
                            self.log_result(
                                f"Menu Visibility - Business {business_id}", 
                                False, 
                                f"No products found in menu (expected {len(created_products)})"
                            )
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Menu Visibility - Business {business_id}", 
                            False, 
                            f"Menu fetch failed: {response.status}", 
                            error_text
                        )
            except Exception as e:
                self.log_result(f"Menu Visibility - Business {business_id}", False, f"Exception: {str(e)}")

        # Test customer-side menu visibility
        if self.customer_token:
            headers = {"Authorization": f"Bearer {self.customer_token}"}
            
            # Test public businesses endpoint
            try:
                async with self.session.get(f"{BACKEND_URL}/businesses", headers=headers) as response:
                    if response.status == 200:
                        businesses_data = await response.json()
                        businesses = businesses_data if isinstance(businesses_data, list) else []
                        
                        visible_businesses = 0
                        businesses_with_menus = 0
                        
                        for business in businesses:
                            visible_businesses += 1
                            business_id = business.get("id")
                            
                            # Check if this business has a menu
                            try:
                                async with self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products") as menu_response:
                                    if menu_response.status == 200:
                                        menu_data = await menu_response.json()
                                        product_count = len(menu_data) if isinstance(menu_data, list) else 0
                                        if product_count > 0:
                                            businesses_with_menus += 1
                            except:
                                pass
                        
                        self.log_result(
                            "Customer Menu Visibility", 
                            True, 
                            f"Visible businesses: {visible_businesses}, With menus: {businesses_with_menus}"
                        )
                        
                    else:
                        error_text = await response.text()
                        self.log_result(
                            "Customer Menu Visibility", 
                            False, 
                            f"Businesses fetch failed: {response.status}", 
                            error_text
                        )
            except Exception as e:
                self.log_result("Customer Menu Visibility", False, f"Exception: {str(e)}")

    async def test_address_registration_cities(self):
        """
        CRITICAL TEST 3: Address Registration Issue
        Test if user addresses are saving city/district correctly
        """
        print("📍 TESTING ADDRESS REGISTRATION CITY ISSUE")
        print("=" * 60)
        
        if not self.customer_token:
            self.log_result("Address Testing", False, "Customer authentication required")
            return
            
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        test_addresses = [
            {
                "label": "Niğde Ev Adresi",
                "city": "Niğde",
                "district": "Merkez",
                "description": "Niğde merkez test adresi",
                "lat": 37.9667,
                "lng": 34.6833
            },
            {
                "label": "Ankara İş Adresi", 
                "city": "Ankara",
                "district": "Çankaya",
                "description": "Ankara Çankaya test adresi",
                "lat": 39.9334,
                "lng": 32.8597
            },
            {
                "label": "İzmir Tatil Adresi",
                "city": "İzmir", 
                "district": "Konak",
                "description": "İzmir Konak test adresi",
                "lat": 38.4192,
                "lng": 27.1287
            },
            {
                "label": "Gaziantep Aile Adresi",
                "city": "Gaziantep",
                "district": "Şahinbey", 
                "description": "Gaziantep Şahinbey test adresi",
                "lat": 37.0662,
                "lng": 37.3833
            }
        ]
        
        for address_data in test_addresses:
            expected_city = address_data["city"]
            expected_district = address_data["district"]
            
            try:
                # Create address
                async with self.session.post(f"{BACKEND_URL}/user/addresses", json=address_data, headers=headers) as response:
                    if response.status == 200:
                        created_address = await response.json()
                        address_id = created_address.get("id")
                        self.created_addresses.append(address_id)
                        
                        saved_city = created_address.get("city", "")
                        saved_district = created_address.get("district", "")
                        saved_lat = created_address.get("lat")
                        saved_lng = created_address.get("lng")
                        
                        # Check city correctness
                        city_correct = saved_city == expected_city
                        district_correct = saved_district == expected_district
                        coords_correct = saved_lat is not None and saved_lng is not None
                        
                        if city_correct and district_correct and coords_correct:
                            self.log_result(
                                f"Address Creation - {expected_city}/{expected_district}", 
                                True, 
                                f"City: '{saved_city}', District: '{saved_district}', Coords: ({saved_lat}, {saved_lng})"
                            )
                        else:
                            issues = []
                            if not city_correct:
                                issues.append(f"City wrong: expected '{expected_city}', got '{saved_city}'")
                            if not district_correct:
                                issues.append(f"District wrong: expected '{expected_district}', got '{saved_district}'")
                            if not coords_correct:
                                issues.append(f"Coordinates missing: lat={saved_lat}, lng={saved_lng}")
                                
                            self.log_result(
                                f"Address Creation - {expected_city}/{expected_district}", 
                                False, 
                                "; ".join(issues)
                            )
                            
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Address Creation - {expected_city}/{expected_district}", 
                            False, 
                            f"Creation failed: {response.status}", 
                            error_text
                        )
                        
            except Exception as e:
                self.log_result(f"Address Creation - {expected_city}/{expected_district}", False, f"Exception: {str(e)}")
        
        # Verify addresses persistence by fetching them back
        try:
            async with self.session.get(f"{BACKEND_URL}/user/addresses", headers=headers) as response:
                if response.status == 200:
                    addresses = await response.json()
                    address_count = len(addresses) if isinstance(addresses, list) else 0
                    
                    self.log_result(
                        "Address Persistence Verification", 
                        True, 
                        f"Retrieved {address_count} addresses from database"
                    )
                    
                    # Check each address for correct city/district data
                    for address in addresses:
                        city = address.get("city", "")
                        district = address.get("district", "")
                        label = address.get("label", "")
                        
                        if city and district:
                            self.log_result(
                                f"Address Data Integrity - {label}", 
                                True, 
                                f"City: '{city}', District: '{district}'"
                            )
                        else:
                            self.log_result(
                                f"Address Data Integrity - {label}", 
                                False, 
                                f"Missing data - City: '{city}', District: '{district}'"
                            )
                            
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Address Persistence Verification", 
                        False, 
                        f"Fetch failed: {response.status}", 
                        error_text
                    )
        except Exception as e:
            self.log_result("Address Persistence Verification", False, f"Exception: {str(e)}")

    async def test_discovery_filtering(self):
        """
        CRITICAL TEST 4: Discovery Filtering Issue  
        Test if location-based restaurant filtering works correctly
        """
        print("🔍 TESTING DISCOVERY FILTERING ISSUE")
        print("=" * 60)
        
        # Test city-based filtering
        test_cities = ["Niğde", "Ankara", "İzmir", "Gaziantep", "İstanbul"]
        
        for city in test_cities:
            try:
                # Test businesses endpoint with city filter
                params = {"city": city}
                async with self.session.get(f"{BACKEND_URL}/businesses", params=params) as response:
                    if response.status == 200:
                        businesses_data = await response.json()
                        businesses = businesses_data if isinstance(businesses_data, list) else []
                        
                        city_businesses = []
                        for business in businesses:
                            business_city = business.get("city", "")
                            if business_city.lower() == city.lower():
                                city_businesses.append(business)
                        
                        total_count = len(businesses)
                        city_count = len(city_businesses)
                        
                        if total_count > 0:
                            self.log_result(
                                f"Discovery Filtering - {city}", 
                                True, 
                                f"Found {total_count} businesses, {city_count} from {city}"
                            )
                        else:
                            self.log_result(
                                f"Discovery Filtering - {city}", 
                                False, 
                                f"No businesses found for city filter: {city}"
                            )
                            
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Discovery Filtering - {city}", 
                            False, 
                            f"Filter failed: {response.status}", 
                            error_text
                        )
                        
            except Exception as e:
                self.log_result(f"Discovery Filtering - {city}", False, f"Exception: {str(e)}")
        
        # Test location-based filtering with coordinates
        test_locations = [
            {"name": "Niğde Center", "lat": 37.9667, "lng": 34.6833, "radius": 10000},
            {"name": "Ankara Center", "lat": 39.9334, "lng": 32.8597, "radius": 10000},
            {"name": "İzmir Center", "lat": 38.4192, "lng": 27.1287, "radius": 10000}
        ]
        
        for location in test_locations:
            try:
                params = {
                    "lat": location["lat"],
                    "lng": location["lng"], 
                    "radius": location["radius"]
                }
                
                async with self.session.get(f"{BACKEND_URL}/businesses", params=params) as response:
                    if response.status == 200:
                        businesses_data = await response.json()
                        businesses = businesses_data if isinstance(businesses_data, list) else []
                        
                        self.log_result(
                            f"Location-Based Discovery - {location['name']}", 
                            True, 
                            f"Found {len(businesses)} businesses within {location['radius']}m"
                        )
                        
                    else:
                        error_text = await response.text()
                        self.log_result(
                            f"Location-Based Discovery - {location['name']}", 
                            False, 
                            f"Location filter failed: {response.status}", 
                            error_text
                        )
                        
            except Exception as e:
                self.log_result(f"Location-Based Discovery - {location['name']}", False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all critical location and integration tests"""
        print("🚀 STARTING CRITICAL LOCATION & INTEGRATION TESTING")
        print("=" * 80)
        print("Testing 4 critical user-reported issues:")
        print("1. Business Registration City Issue")
        print("2. Menu Visibility Issue") 
        print("3. Address Registration Issue")
        print("4. Discovery Filtering Issue")
        print("=" * 80)
        print()
        
        await self.setup_session()
        
        try:
            # Setup authentication
            await self.authenticate_admin()
            await self.authenticate_customer()
            
            # Run critical tests
            await self.test_business_registration_cities()
            await self.test_menu_visibility_integration()
            await self.test_address_registration_cities()
            await self.test_discovery_filtering()
            
        finally:
            await self.cleanup_session()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 CRITICAL LOCATION & INTEGRATION TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Group results by test category
        categories = {
            "Business Registration City": [],
            "Menu Visibility": [],
            "Address Registration": [],
            "Discovery Filtering": [],
            "Authentication": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Business Registration" in test_name or "Database Verification" in test_name:
                categories["Business Registration City"].append(result)
            elif "Menu" in test_name or "Product" in test_name:
                categories["Menu Visibility"].append(result)
            elif "Address" in test_name:
                categories["Address Registration"].append(result)
            elif "Discovery" in test_name or "Location-Based" in test_name:
                categories["Discovery Filtering"].append(result)
            elif "Authentication" in test_name:
                categories["Authentication"].append(result)
        
        for category, results in categories.items():
            if results:
                passed = len([r for r in results if r["success"]])
                total = len(results)
                print(f"🔍 {category}: {passed}/{total} tests passed")
                
                # Show failed tests
                failed = [r for r in results if not r["success"]]
                if failed:
                    print("   ❌ FAILED TESTS:")
                    for fail in failed:
                        print(f"      - {fail['test']}: {fail['details']}")
                print()
        
        # Critical issues summary
        print("🚨 CRITICAL ISSUES ANALYSIS:")
        print()
        
        # Issue 1: Business Registration City
        business_reg_results = categories["Business Registration City"]
        business_reg_failed = [r for r in business_reg_results if not r["success"]]
        if business_reg_failed:
            print("❌ ISSUE 1 - Business Registration City Problem CONFIRMED:")
            print("   Cities are not being saved correctly during business registration")
            for fail in business_reg_failed:
                if "City Storage" in fail["test"] or "City Persistence" in fail["test"]:
                    print(f"   - {fail['details']}")
        else:
            print("✅ ISSUE 1 - Business Registration City: WORKING CORRECTLY")
        print()
        
        # Issue 2: Menu Visibility
        menu_results = categories["Menu Visibility"]
        menu_failed = [r for r in menu_results if not r["success"]]
        if menu_failed:
            print("❌ ISSUE 2 - Menu Visibility Problem CONFIRMED:")
            print("   Restaurant menus are not visible to customers")
            for fail in menu_failed:
                print(f"   - {fail['details']}")
        else:
            print("✅ ISSUE 2 - Menu Visibility: WORKING CORRECTLY")
        print()
        
        # Issue 3: Address Registration
        address_results = categories["Address Registration"]
        address_failed = [r for r in address_results if not r["success"]]
        if address_failed:
            print("❌ ISSUE 3 - Address Registration Problem CONFIRMED:")
            print("   User addresses are not saving city/district correctly")
            for fail in address_failed:
                print(f"   - {fail['details']}")
        else:
            print("✅ ISSUE 3 - Address Registration: WORKING CORRECTLY")
        print()
        
        # Issue 4: Discovery Filtering
        discovery_results = categories["Discovery Filtering"]
        discovery_failed = [r for r in discovery_results if not r["success"]]
        if discovery_failed:
            print("❌ ISSUE 4 - Discovery Filtering Problem CONFIRMED:")
            print("   Location-based restaurant filtering is not working")
            for fail in discovery_failed:
                print(f"   - {fail['details']}")
        else:
            print("✅ ISSUE 4 - Discovery Filtering: WORKING CORRECTLY")
        print()
        
        print("=" * 80)
        print(f"🏁 TESTING COMPLETED: {datetime.now().isoformat()}")
        print("=" * 80)

async def main():
    """Main test execution"""
    tester = LocationIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())