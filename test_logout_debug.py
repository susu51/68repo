#!/usr/bin/env python3
"""
Debug logout endpoint specifically
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://express-track-2.preview.emergentagent.com"
AUTH_BASE_URL = f"{BASE_URL}/api/auth"

async def test_logout_debug():
    print("🔍 Debug Logout Endpoint")
    print("=" * 30)
    
    # Create session with cookie jar
    jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'Content-Type': 'application/json'},
        cookie_jar=jar
    )
    
    try:
        # Step 1: Login first
        print("1. Login...")
        login_data = {"email": "testcustomer@example.com", "password": "test123"}
        
        async with session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
            print(f"   Login status: {response.status}")
            if response.status == 200:
                print("   ✅ Login successful")
            else:
                print("   ❌ Login failed")
                return
        
        # Step 2: Verify we're authenticated
        print("\n2. Verify authentication...")
        async with session.get(f"{AUTH_BASE_URL}/me") as response:
            print(f"   /me status: {response.status}")
            if response.status == 200:
                user_data = await response.json()
                print(f"   ✅ Authenticated as: {user_data.get('email')}")
            else:
                print("   ❌ Not authenticated")
                return
        
        # Step 3: Try logout with detailed error info
        print("\n3. Testing logout...")
        async with session.post(f"{AUTH_BASE_URL}/logout") as response:
            print(f"   Logout status: {response.status}")
            print(f"   Response headers: {dict(response.headers)}")
            
            try:
                response_data = await response.json()
                print(f"   Response data: {response_data}")
            except:
                response_text = await response.text()
                print(f"   Response text: {response_text}")
        
        # Step 4: Try logout without any cookies (fresh session)
        print("\n4. Testing logout without cookies...")
        fresh_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
        async with fresh_session.post(f"{AUTH_BASE_URL}/logout") as response:
            print(f"   Fresh logout status: {response.status}")
            try:
                response_data = await response.json()
                print(f"   Fresh response data: {response_data}")
            except:
                response_text = await response.text()
                print(f"   Fresh response text: {response_text}")
        
        await fresh_session.close()
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_logout_debug())