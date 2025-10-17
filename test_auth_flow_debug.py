#!/usr/bin/env python3
"""
Debug authentication flow issues
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://delivery-nexus-5.preview.emergentagent.com"
AUTH_BASE_URL = f"{BASE_URL}/api/auth"

async def test_auth_flow():
    print("🔍 Debug Authentication Flow")
    print("=" * 40)
    
    # Create session with cookie jar
    jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'Content-Type': 'application/json'},
        cookie_jar=jar
    )
    
    try:
        # Step 1: Login with admin user
        print("1. Admin Login...")
        login_data = {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}
        
        async with session.post(f"{AUTH_BASE_URL}/login", json=login_data) as response:
            print(f"   Login status: {response.status}")
            if response.status == 200:
                response_data = await response.json()
                print(f"   Response: {response_data}")
                print("   ✅ Admin login successful")
            else:
                print("   ❌ Admin login failed")
                error_data = await response.json()
                print(f"   Error: {error_data}")
                return
        
        # Step 2: Check cookies after login
        print("\n2. Check cookies after login...")
        print(f"   Session cookies: {len(session.cookie_jar)}")
        for cookie in session.cookie_jar:
            print(f"   Cookie: {cookie.key} = {str(cookie.value)[:30]}...")
        
        # Step 3: Verify authentication with /me
        print("\n3. Verify authentication...")
        async with session.get(f"{AUTH_BASE_URL}/me") as response:
            print(f"   /me status: {response.status}")
            if response.status == 200:
                user_data = await response.json()
                print(f"   User data: {user_data}")
                if user_data.get("role") == "admin":
                    print("   ✅ Admin authentication verified")
                else:
                    print(f"   ❌ Wrong role: {user_data.get('role')}")
            else:
                print("   ❌ Authentication failed")
                try:
                    error_data = await response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Status: {response.status}")
                return
        
        # Step 4: Logout
        print("\n4. Logout...")
        async with session.post(f"{AUTH_BASE_URL}/logout") as response:
            print(f"   Logout status: {response.status}")
            if response.status == 200:
                response_data = await response.json()
                print(f"   Response: {response_data}")
                print("   ✅ Logout successful")
            else:
                print("   ❌ Logout failed")
                return
        
        # Step 5: Verify logout (should fail to access /me)
        print("\n5. Verify logout...")
        async with session.get(f"{AUTH_BASE_URL}/me") as response:
            print(f"   /me after logout status: {response.status}")
            if response.status == 401:
                print("   ✅ Access denied after logout (correct)")
                return True
            else:
                print("   ❌ Still authenticated after logout")
                user_data = await response.json()
                print(f"   User data: {user_data}")
                return False
        
    finally:
        await session.close()

if __name__ == "__main__":
    result = asyncio.run(test_auth_flow())
    print(f"\n🎯 Overall result: {'✅ SUCCESS' if result else '❌ FAILED'}")