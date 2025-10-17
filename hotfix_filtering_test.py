#!/usr/bin/env python3
"""
Test business filtering with city normalization
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"

async def test_business_filtering():
    """Test business filtering with normalized cities"""
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Testing Business Filtering with City Normalization")
        print("=" * 60)
        
        # First, let's approve the test businesses we just created
        print("\n🔧 Setting up test data - approving businesses...")
        
        # Get admin token
        admin_login = {
            "email": "admin@kuryecini.com",
            "password": "6851"
        }
        
        admin_token = None
        try:
            async with session.post(f"{BACKEND_URL}/auth/login", json=admin_login) as response:
                if response.status == 200:
                    data = await response.json()
                    admin_token = data.get("access_token")
                    print("✅ Admin login successful")
                else:
                    print(f"❌ Admin login failed: {response.status}")
        except Exception as e:
            print(f"❌ Admin login exception: {str(e)}")
        
        if admin_token:
            # Get all users to find our test businesses
            headers = {"Authorization": f"Bearer {admin_token}"}
            try:
                async with session.get(f"{BACKEND_URL}/admin/users", headers=headers) as response:
                    if response.status == 200:
                        users = await response.json()
                        test_businesses = [
                            user for user in users 
                            if user.get("role") == "business" and 
                            user.get("email", "").startswith(("aksary_business", "istanbul_business", "gaziantep_business"))
                        ]
                        
                        print(f"Found {len(test_businesses)} test businesses to approve")
                        
                        # Approve each test business
                        for business in test_businesses:
                            business_id = business.get("id")
                            if business_id:
                                try:
                                    async with session.patch(
                                        f"{BACKEND_URL}/admin/users/{business_id}/approve",
                                        headers=headers
                                    ) as approve_response:
                                        if approve_response.status == 200:
                                            print(f"✅ Approved business: {business.get('business_name')} ({business.get('city')})")
                                        else:
                                            print(f"⚠️  Failed to approve business {business_id}: {approve_response.status}")
                                except Exception as e:
                                    print(f"⚠️  Exception approving business {business_id}: {str(e)}")
                    else:
                        print(f"❌ Failed to get users: {response.status}")
            except Exception as e:
                print(f"❌ Exception getting users: {str(e)}")
        
        print("\n🔍 Testing Business Filtering")
        print("-" * 40)
        
        # Test cases for filtering
        test_cases = [
            {
                "name": "All businesses (no filter)",
                "url": f"{BACKEND_URL}/businesses",
                "expected_min": 1
            },
            {
                "name": "Filter by normalized city: aksaray",
                "url": f"{BACKEND_URL}/businesses?city=aksaray",
                "expected_min": 1
            },
            {
                "name": "Filter by misspelled city: Aksary",
                "url": f"{BACKEND_URL}/businesses?city=Aksary",
                "expected_min": 1
            },
            {
                "name": "Filter by normalized city: ıstanbul",
                "url": f"{BACKEND_URL}/businesses?city=ıstanbul",
                "expected_min": 1
            },
            {
                "name": "Filter by non-Turkish city: Istanbul",
                "url": f"{BACKEND_URL}/businesses?city=Istanbul",
                "expected_min": 1
            },
            {
                "name": "Filter by normalized city: gaziantep",
                "url": f"{BACKEND_URL}/businesses?city=gaziantep",
                "expected_min": 1
            },
            {
                "name": "Filter by misspelled city: Gaziantap",
                "url": f"{BACKEND_URL}/businesses?city=Gaziantap",
                "expected_min": 1
            },
            {
                "name": "Geolocation filter (Aksaray coordinates)",
                "url": f"{BACKEND_URL}/businesses?lat=38.3687&lng=34.0370&radius_km=50",
                "expected_min": 0  # May not have location data
            },
            {
                "name": "Combined filter (city + location)",
                "url": f"{BACKEND_URL}/businesses?city=aksaray&lat=38.3687&lng=34.0370&radius_km=50",
                "expected_min": 0  # May not have location data
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📋 {test_case['name']}")
            try:
                async with session.get(test_case["url"]) as response:
                    if response.status == 200:
                        businesses = await response.json()
                        count = len(businesses)
                        
                        if count >= test_case["expected_min"]:
                            print(f"✅ Found {count} businesses (expected >= {test_case['expected_min']})")
                            
                            # Show details of found businesses
                            for business in businesses[:3]:  # Show first 3
                                name = business.get("name", "Unknown")
                                city = business.get("location", {}).get("name", "Unknown location")
                                print(f"   - {name} ({city})")
                        else:
                            print(f"⚠️  Found {count} businesses (expected >= {test_case['expected_min']})")
                    else:
                        print(f"❌ Request failed with status: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text}")
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎯 Business Filtering Test Complete")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_business_filtering())