#!/usr/bin/env python3
"""
Test business registration with city normalization specifically
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://kurye-platform.preview.emergentagent.com/api"

async def test_business_registration_city_normalization():
    """Test business registration with various city spellings"""
    
    async with aiohttp.ClientSession() as session:
        print("🏪 Testing Business Registration with City Normalization")
        print("=" * 60)
        
        test_cases = [
            {
                "email": "aksary_business_1@test.com",
                "city": "Aksary",
                "expected_normalized": "aksaray",
                "description": "Misspelled Aksaray"
            },
            {
                "email": "istanbul_business_1@test.com", 
                "city": "Istanbul",
                "expected_normalized": "ıstanbul",
                "description": "Istanbul without Turkish characters"
            },
            {
                "email": "gaziantep_business_1@test.com",
                "city": "Gaziantap", 
                "expected_normalized": "gaziantep",
                "description": "Misspelled Gaziantep"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print("-" * 40)
            
            registration_data = {
                "email": test_case["email"],
                "password": "test123",
                "business_name": f"Test İşletmesi {i}",
                "tax_number": f"123456789{i}",
                "address": f"Test Mahallesi, Test Sokak No:{i}",
                "city": test_case["city"],
                "business_category": "gida",
                "description": f"Test işletmesi {i} - şehir normalizasyonu testi"
            }
            
            try:
                async with session.post(
                    f"{BACKEND_URL}/register/business",
                    json=registration_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status in [200, 201]:
                        data = await response.json()
                        user_data = data.get("user_data", {})
                        
                        original_city = user_data.get("city")
                        normalized_city = user_data.get("city_normalized")
                        business_id = user_data.get("id")
                        
                        print(f"✅ Registration successful")
                        print(f"   Business ID: {business_id}")
                        print(f"   Original city: '{original_city}'")
                        print(f"   Normalized city: '{normalized_city}'")
                        
                        # Verify normalization
                        if original_city == test_case["city"]:
                            print(f"✅ Original city preserved correctly")
                        else:
                            print(f"❌ Original city mismatch: expected '{test_case['city']}', got '{original_city}'")
                            
                        if normalized_city == test_case["expected_normalized"]:
                            print(f"✅ City normalization working correctly")
                        else:
                            print(f"❌ City normalization failed: expected '{test_case['expected_normalized']}', got '{normalized_city}'")
                            
                    elif response.status == 400:
                        error_data = await response.json()
                        if "already registered" in error_data.get("detail", "").lower():
                            print(f"⚠️  Email already registered - testing with existing business")
                            
                            # Try to login and check the existing business
                            login_data = {
                                "email": test_case["email"],
                                "password": "test123"
                            }
                            
                            async with session.post(f"{BACKEND_URL}/auth/login", json=login_data) as login_response:
                                if login_response.status == 200:
                                    login_data = await login_response.json()
                                    user_data = login_data.get("user", {})
                                    print(f"✅ Login successful, checking existing business data")
                                    print(f"   Business ID: {user_data.get('id')}")
                                    print(f"   City: {user_data.get('city')}")
                                    print(f"   City Normalized: {user_data.get('city_normalized')}")
                                else:
                                    print(f"❌ Login failed: {login_response.status}")
                        else:
                            print(f"❌ Registration failed: {error_data.get('detail')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Registration failed with status {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"❌ Exception during registration: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_business_registration_city_normalization())