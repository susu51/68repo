#!/usr/bin/env python3
"""
Test with Latest Token
======================
"""

import asyncio
import aiohttp

async def test_latest_token():
    base_url = "https://delivery-nexus-5.preview.emergentagent.com/api"
    test_email = "admin@kuryecini.com"
    current_password = "KuryeciniAdmin2024!"
    new_password = "NewSecurePassword123!"
    
    # Latest token from logs
    latest_token = "6a16806a5c46fd1a-2f43c891-93da-4bbf-9703-dd8cbfb56233"
    
    async with aiohttp.ClientSession() as session:
        
        print("🔄 TESTING WITH LATEST TOKEN")
        print("=" * 40)
        print(f"Token: {latest_token}")
        print()
        
        # Step 1: Reset password with latest token
        print("Step 1: Resetting password with latest token...")
        async with session.post(
            f"{base_url}/auth/reset",
            json={"token": latest_token, "password": new_password}
        ) as response:
            reset_status = response.status
            reset_data = await response.json()
            print(f"Reset result: {reset_status} - {reset_data}")
        
        if reset_status == 200:
            print("✅ Password reset successful!")
            
            # Step 2: Test login with old password (should fail)
            print("\nStep 2: Testing login with old password (should fail)...")
            async with session.post(
                f"{base_url}/auth/login",
                json={"email": test_email, "password": current_password}
            ) as response:
                old_status = response.status
                old_data = await response.json()
                print(f"Old password: {old_status} - {old_data.get('detail', 'Success')}")
            
            # Step 3: Test login with new password (should work)
            print("\nStep 3: Testing login with new password (should work)...")
            async with session.post(
                f"{base_url}/auth/login",
                json={"email": test_email, "password": new_password}
            ) as response:
                new_status = response.status
                new_data = await response.json()
                print(f"New password: {new_status} - {new_data.get('detail', 'Success')}")
                if new_status == 200:
                    print(f"✅ Login successful! User: {new_data.get('user', {}).get('email')}")
            
            # Summary
            print("\n" + "=" * 40)
            print("📊 FINAL TEST RESULTS")
            print("=" * 40)
            print(f"✅ Password reset: SUCCESS")
            print(f"{'✅' if old_status != 200 else '❌'} Old password rejected: {'SUCCESS' if old_status != 200 else 'FAILED'}")
            print(f"{'✅' if new_status == 200 else '❌'} New password works: {'SUCCESS' if new_status == 200 else 'FAILED'}")
            
            if old_status != 200 and new_status == 200:
                print("\n🎉 COMPLETE SUCCESS: Password reset cycle working perfectly!")
            elif new_status == 200:
                print("\n⚠️  PARTIAL SUCCESS: New password works but old password not rejected")
            else:
                print("\n❌ FAILED: New password doesn't work")
                
        else:
            print(f"❌ Password reset failed: {reset_data}")

if __name__ == "__main__":
    asyncio.run(test_latest_token())