#!/usr/bin/env python3
"""
Fresh Token Password Reset Test
===============================
"""

import asyncio
import aiohttp
import json

async def test_with_fresh_token():
    base_url = "https://delivery-nexus-5.preview.emergentagent.com/api"
    test_email = "admin@kuryecini.com"
    current_password = "KuryeciniAdmin2024!"
    new_password = "NewSecurePassword123!"
    
    # Use the fresh token from logs
    fresh_token = "86e11dffd9d3302b-cddff783-bd98-45fb-a7ea-0751b55e9bc0"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Reset password with fresh token
        print("🔄 Testing password reset with fresh token...")
        async with session.post(
            f"{base_url}/auth/reset",
            json={"token": fresh_token, "password": new_password}
        ) as response:
            status = response.status
            data = await response.json()
            print(f"Reset result: {status} - {data}")
        
        if status == 200:
            print("✅ Password reset successful!")
            
            # Test 2: Try login with old password
            print("\n🔐 Testing login with old password...")
            async with session.post(
                f"{base_url}/auth/login",
                json={"email": test_email, "password": current_password}
            ) as response:
                old_status = response.status
                old_data = await response.json()
                print(f"Old password login: {old_status} - {old_data.get('detail', 'Success')}")
            
            # Test 3: Try login with new password
            print("\n🔐 Testing login with new password...")
            async with session.post(
                f"{base_url}/auth/login",
                json={"email": test_email, "password": new_password}
            ) as response:
                new_status = response.status
                new_data = await response.json()
                print(f"New password login: {new_status} - {new_data.get('detail', 'Success')}")
            
            # Summary
            print("\n📊 RESULTS:")
            print(f"Password reset: {'✅ SUCCESS' if status == 200 else '❌ FAILED'}")
            print(f"Old password rejected: {'✅ SUCCESS' if old_status != 200 else '❌ FAILED (still works)'}")
            print(f"New password works: {'✅ SUCCESS' if new_status == 200 else '❌ FAILED'}")
            
        else:
            print("❌ Password reset failed, skipping login tests")

if __name__ == "__main__":
    asyncio.run(test_with_fresh_token())