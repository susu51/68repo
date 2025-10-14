#!/usr/bin/env python3
"""
Debug Cookie Authentication Test
Simple test to debug cookie authentication issues
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://express-track-2.preview.emergentagent.com"
AUTH_BASE_URL = f"{BASE_URL}/api/auth"

async def debug_cookie_auth():
    print("🔍 Debug Cookie Authentication Test")
    print("=" * 50)
    
    # Create session with cookie jar
    jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'Content-Type': 'application/json'},
        cookie_jar=jar
    )
    
    try:
        # Test 1: Check if auth endpoints exist
        print("\n1. Testing endpoint availability...")
        
        async with session.get(f"{AUTH_BASE_URL}/me") as response:
            print(f"   GET /api/auth/me: {response.status}")
            if response.status == 401:
                print("   ✅ Endpoint exists (returns 401 as expected without auth)")
            else:
                print(f"   ❌ Unexpected status: {response.status}")
        
        # Test 2: Try login
        print("\n2. Testing login...")
        login_data = {"email": "testcustomer@example.com", "password": "test123"}
        
        async with session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
            print(f"   POST /api/auth/login: {response.status}")
            
            if response.status == 200:
                response_data = await response.json()
                print(f"   Response: {response_data}")
                
                # Check cookies
                print(f"   Cookies received: {len(response.cookies)}")
                for cookie_name, cookie_value in response.cookies.items():
                    print(f"   Cookie: {cookie_name} = {str(cookie_value)[:20]}...")
                    
            else:
                try:
                    error_data = await response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.status}")
        
        # Test 3: Check session cookies
        print("\n3. Checking session cookies...")
        print(f"   Session cookies: {len(session.cookie_jar)}")
        for cookie in session.cookie_jar:
            print(f"   Session cookie: {cookie.key} = {str(cookie.value)[:20]}...")
        
        # Test 4: Try /me with cookies
        print("\n4. Testing /me with cookies...")
        async with session.get(f"{AUTH_BASE_URL}/me") as response:
            print(f"   GET /api/auth/me (with cookies): {response.status}")
            if response.status == 200:
                user_data = await response.json()
                print(f"   User data: {user_data}")
            else:
                try:
                    error_data = await response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.status}")
        
        # Test 5: Try refresh
        print("\n5. Testing refresh...")
        async with session.post(f"{AUTH_BASE_URL}/refresh") as response:
            print(f"   POST /api/auth/refresh: {response.status}")
            if response.status == 200:
                response_data = await response.json()
                print(f"   Response: {response_data}")
            else:
                try:
                    error_data = await response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.status}")
        
        # Test 6: Try logout
        print("\n6. Testing logout...")
        async with session.post(f"{AUTH_BASE_URL}/logout") as response:
            print(f"   POST /api/auth/logout: {response.status}")
            if response.status == 200:
                response_data = await response.json()
                print(f"   Response: {response_data}")
            else:
                try:
                    error_data = await response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.status}")
        
    finally:
        await session.close()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(debug_cookie_auth())