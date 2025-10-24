#!/usr/bin/env python3
"""
Hotfix Sprint Testing - City Normalization & Business Filtering
Tests the specific hotfix implementations mentioned in the review request
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com/api"
TEST_EMAIL = "aksary_test@example.com"
TEST_PASSWORD = "test123"

class HotfixSprintTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.admin_token = None
        self.test_business_id = None
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Hotfix Sprint Testing")
        print("=" * 60)
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_city_normalization_function(self):
        """Test 1: City Normalization Function Direct Testing"""
        print("\n📍 TEST 1: City Normalization Function")
        print("-" * 40)
        
        try:
            # Import the normalization function
            from utils.city_normalize import normalize_city_name
            
            # Test cases from review request
            test_cases = [
                ("Aksary", "aksaray"),
                ("aksary", "aksaray"), 
                ("Istanbul", "ıstanbul"),
                ("istanbul", "ıstanbul"),
                ("ıstanbul", "ıstanbul"),
                ("AKSARY", "aksaray"),
                ("akasray", "aksaray"),
                ("", ""),  # Edge case: empty string
                ("123Aksary!", "aksaray"),  # Edge case: special characters
                ("Gaziantap", "gaziantep"),
                ("Burssa", "bursa")
            ]
            
            passed = 0
            total = len(test_cases)
            
            for input_city, expected in test_cases:
                result = normalize_city_name(input_city)
                success = result == expected
                if success:
                    passed += 1
                self.log_test(f"Normalize '{input_city}' → '{expected}'", success, 
                            f"Got: '{result}'" if not success else "")
                            
            overall_success = passed == total
            self.log_test(f"City Normalization Function ({passed}/{total})", overall_success)
            
        except Exception as e:
            self.log_test("City Normalization Function", False, f"Import error: {str(e)}")
            
    async def test_business_registration_with_city_normalization(self):
        """Test 2: Business Registration with City Normalization"""
        print("\n🏪 TEST 2: Business Registration with City Normalization")
        print("-" * 40)
        
        try:
            # Test business registration with misspelled city
            registration_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "business_name": "Aksary Test İşletmesi",
                "tax_number": "1234567890",
                "address": "Test Mahallesi, Test Sokak No:1",
                "city": "Aksary",  # Misspelled city
                "business_category": "gida",
                "description": "Test işletmesi - şehir normalizasyonu testi"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/register/business",
                json=registration_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201 or response.status == 200:
                    data = await response.json()
                    self.test_business_id = data.get("user_data", {}).get("id")
                    
                    # Check if both city and city_normalized fields are present
                    user_data = data.get("user_data", {})
                    original_city = user_data.get("city")
                    normalized_city = user_data.get("city_normalized")
                    
                    self.log_test("Business Registration Success", True, 
                                f"Business ID: {self.test_business_id}")
                    
                    self.log_test("Original City Field Saved", original_city == "Aksary",
                                f"Expected: 'Aksary', Got: '{original_city}'")
                    
                    self.log_test("City Normalized Field Saved", normalized_city == "aksaray",
                                f"Expected: 'aksaray', Got: '{normalized_city}'")
                    
                elif response.status == 400:
                    # Email might already exist, try to login instead
                    await self.login_test_business()
                    
                else:
                    error_text = await response.text()
                    self.log_test("Business Registration", False, 
                                f"Status: {response.status}, Error: {error_text}")
                    
        except Exception as e:
            self.log_test("Business Registration", False, f"Exception: {str(e)}")
            
    async def login_test_business(self):
        """Login to test business if registration fails due to existing email"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_business_id = data.get("user", {}).get("id")
                    self.log_test("Test Business Login", True, f"Business ID: {self.test_business_id}")
                else:
                    self.log_test("Test Business Login", False, f"Status: {response.status}")
        except Exception as e:
            self.log_test("Test Business Login", False, f"Exception: {str(e)}")
            
    async def test_business_listing_with_filtering(self):
        """Test 3: Business Listing with City and Location Filtering"""
        print("\n🔍 TEST 3: Business Listing with Filtering")
        print("-" * 40)
        
        # Test 3a: Basic business listing
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses") as response:
                if response.status == 200:
                    businesses = await response.json()
                    self.log_test("Basic Business Listing", True, 
                                f"Found {len(businesses)} businesses")
                else:
                    self.log_test("Basic Business Listing", False, 
                                f"Status: {response.status}")
        except Exception as e:
            self.log_test("Basic Business Listing", False, f"Exception: {str(e)}")
            
        # Test 3b: City filtering with normalized city
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses?city=aksaray") as response:
                if response.status == 200:
                    businesses = await response.json()
                    self.log_test("City Filter (normalized)", True, 
                                f"Found {len(businesses)} businesses in aksaray")
                else:
                    self.log_test("City Filter (normalized)", False, 
                                f"Status: {response.status}")
        except Exception as e:
            self.log_test("City Filter (normalized)", False, f"Exception: {str(e)}")
            
        # Test 3c: City filtering with misspelled city
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses?city=Aksary") as response:
                if response.status == 200:
                    businesses = await response.json()
                    self.log_test("City Filter (misspelled)", True, 
                                f"Found {len(businesses)} businesses for 'Aksary'")
                else:
                    self.log_test("City Filter (misspelled)", False, 
                                f"Status: {response.status}")
        except Exception as e:
            self.log_test("City Filter (misspelled)", False, f"Exception: {str(e)}")
            
        # Test 3d: Geolocation filtering (Aksaray coordinates)
        try:
            aksaray_lat = 38.3687
            aksaray_lng = 34.0370
            radius_km = 50
            
            url = f"{BACKEND_URL}/businesses?lat={aksaray_lat}&lng={aksaray_lng}&radius_km={radius_km}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    businesses = await response.json()
                    self.log_test("Geolocation Filter", True, 
                                f"Found {len(businesses)} businesses within {radius_km}km of Aksaray")
                else:
                    self.log_test("Geolocation Filter", False, 
                                f"Status: {response.status}")
        except Exception as e:
            self.log_test("Geolocation Filter", False, f"Exception: {str(e)}")
            
        # Test 3e: Combined filtering (city + location)
        try:
            url = f"{BACKEND_URL}/businesses?city=aksaray&lat={aksaray_lat}&lng={aksaray_lng}&radius_km={radius_km}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    businesses = await response.json()
                    self.log_test("Combined Filter (city + location)", True, 
                                f"Found {len(businesses)} businesses")
                else:
                    self.log_test("Combined Filter (city + location)", False, 
                                f"Status: {response.status}")
        except Exception as e:
            self.log_test("Combined Filter (city + location)", False, f"Exception: {str(e)}")
            
    async def test_database_indexes(self):
        """Test 4: Database Indexes Verification"""
        print("\n🗄️ TEST 4: Database Indexes")
        print("-" * 40)
        
        try:
            # Import MongoDB client
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Connect to MongoDB
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/kuryecini_database')
            client = AsyncIOMotorClient(mongo_uri)
            db = client.kuryecini_database
            
            # Check indexes on users collection (where businesses are stored)
            indexes = await db.users.list_indexes().to_list(length=None)
            
            # Look for city_normalized index
            city_index_found = False
            location_index_found = False
            
            for index in indexes:
                index_keys = index.get('key', {})
                if 'city_normalized' in index_keys:
                    city_index_found = True
                if 'location' in index_keys:
                    location_index_found = True
                    
            self.log_test("City Normalized Index Exists", city_index_found,
                        "Index on city_normalized field" if city_index_found else "Missing city_normalized index")
            
            self.log_test("Location 2dsphere Index Exists", location_index_found,
                        "2dsphere index on location field" if location_index_found else "Missing location index")
            
            # Test geospatial query performance (basic test)
            start_time = datetime.now()
            
            # Simple geospatial query
            query = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [34.0370, 38.3687]  # Aksaray coordinates
                        },
                        "$maxDistance": 50000  # 50km in meters
                    }
                }
            }
            
            try:
                businesses = await db.users.find(query).limit(10).to_list(length=10)
                query_time = (datetime.now() - start_time).total_seconds()
                
                self.log_test("Geospatial Query Performance", query_time < 1.0,
                            f"Query took {query_time:.3f}s (should be < 1s)")
            except Exception as geo_e:
                self.log_test("Geospatial Query Performance", False,
                            f"Query failed: {str(geo_e)}")
            
            await client.close()
            
        except Exception as e:
            self.log_test("Database Indexes Check", False, f"Exception: {str(e)}")
            
    async def test_edge_cases(self):
        """Test 5: Edge Cases and Error Handling"""
        print("\n🧪 TEST 5: Edge Cases")
        print("-" * 40)
        
        # Test empty city parameter
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses?city=") as response:
                success = response.status in [200, 400]  # Either works or properly rejects
                self.log_test("Empty City Parameter", success, 
                            f"Status: {response.status}")
        except Exception as e:
            self.log_test("Empty City Parameter", False, f"Exception: {str(e)}")
            
        # Test invalid coordinates
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses?lat=invalid&lng=invalid") as response:
                success = response.status in [200, 400, 422]  # Should handle gracefully
                self.log_test("Invalid Coordinates", success, 
                            f"Status: {response.status}")
        except Exception as e:
            self.log_test("Invalid Coordinates", False, f"Exception: {str(e)}")
            
        # Test very large radius
        try:
            async with self.session.get(f"{BACKEND_URL}/businesses?lat=38.3687&lng=34.0370&radius_km=10000") as response:
                success = response.status == 200  # Should work but might return many results
                self.log_test("Large Radius Parameter", success, 
                            f"Status: {response.status}")
        except Exception as e:
            self.log_test("Large Radius Parameter", False, f"Exception: {str(e)}")
            
    async def run_all_tests(self):
        """Run all hotfix sprint tests"""
        await self.setup()
        
        try:
            # Run tests in sequence
            await self.test_city_normalization_function()
            await self.test_business_registration_with_city_normalization()
            await self.test_business_listing_with_filtering()
            await self.test_database_indexes()
            await self.test_edge_cases()
            
            # Print summary
            self.print_summary()
            
        finally:
            await self.cleanup()
            
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 HOTFIX SPRINT TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 Overall Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        # Group results by test category
        categories = {
            "City Normalization": [],
            "Business Registration": [],
            "Business Listing": [],
            "Database Indexes": [],
            "Edge Cases": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Normalize" in test_name or "Normalization" in test_name:
                categories["City Normalization"].append(result)
            elif "Registration" in test_name or "Login" in test_name:
                categories["Business Registration"].append(result)
            elif "Listing" in test_name or "Filter" in test_name:
                categories["Business Listing"].append(result)
            elif "Index" in test_name or "Performance" in test_name:
                categories["Database Indexes"].append(result)
            else:
                categories["Edge Cases"].append(result)
        
        for category, results in categories.items():
            if results:
                passed_cat = sum(1 for r in results if r["success"])
                total_cat = len(results)
                print(f"\n📋 {category}: {passed_cat}/{total_cat} passed")
                
                for result in results:
                    status = "✅" if result["success"] else "❌"
                    print(f"   {status} {result['test']}")
                    if result["details"] and not result["success"]:
                        print(f"      └─ {result['details']}")
        
        # Critical issues
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for result in failed_tests:
                print(f"   ❌ {result['test']}: {result['details']}")
        else:
            print(f"\n🎉 ALL HOTFIX REQUIREMENTS WORKING CORRECTLY!")
            
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    tester = HotfixSprintTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())