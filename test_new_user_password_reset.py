#!/usr/bin/env python3
"""
Test Password Reset with New User
=================================
"""

import asyncio
import aiohttp
import json
import time

async def test_new_user():
    base_url = "https://kurye-express-2.preview.emergentagent.com/api"
    test_email = f"testuser{int(time.time())}@example.com"  # Unique email
    test_password = "TestPassword123!"
    new_password = "NewTestPassword456!"
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 TESTING PASSWORD RESET WITH NEW USER")
        print("=" * 50)
        print(f"Test email: {test_email}")
        print()
        
        # Step 1: Create a new user
        print("Step 1: Creating new user...")
        async with session.post(
            f"{base_url}/register/customer",
            json={
                "email": test_email,
                "password": test_password,
                "first_name": "Test",
                "last_name": "User",
                "city": "Istanbul"
            }
        ) as response:
            reg_status = response.status
            reg_data = await response.json()
            print(f"Registration: {reg_status} - {reg_data.get('user_type', reg_data.get('detail', 'Success'))}")
        
        if reg_status != 201:
            print("❌ Failed to create user")
            return
        
        # Step 2: Verify user can login with original password
        print("\nStep 2: Verifying login with original password...")
        async with session.post(
            f"{base_url}/auth/login",
            json={"email": test_email, "password": test_password}
        ) as response:
            login_status = response.status
            login_data = await response.json()
            print(f"Original login: {login_status} - {'Success' if login_status == 200 else login_data.get('detail')}")
        
        if login_status != 200:
            print("❌ User cannot login with original password")
            return
        
        print("✅ User created and can login successfully!")
        
        # Step 3: Request password reset
        print("\nStep 3: Requesting password reset...")
        async with session.post(
            f"{base_url}/auth/forgot",
            json={"email": test_email}
        ) as response:
            forgot_status = response.status
            forgot_data = await response.json()
            print(f"Forgot password: {forgot_status} - {forgot_data.get('message')}")
        
        if forgot_status != 200:
            print("❌ Failed to request password reset")
            return
        
        print("\n⏳ Waiting for email to be sent...")
        await asyncio.sleep(2)
        
        print("\n📧 Extracting token from backend logs...")
        
        # Get the latest token from logs
        import subprocess
        try:
            result = subprocess.run([
                "sudo", "tail", "-n", "50", "/var/log/supervisor/backend.out.log"
            ], capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            reset_token = None
            
            for line in reversed(lines):
                if "Reset Token:" in line and test_email.split('@')[0] in line:
                    # Extract token from line like "Reset Token: abc123-def456..."
                    token_part = line.split("Reset Token: ")[1].strip()
                    reset_token = token_part
                    break
                elif "Reset Token:" in line:
                    # Get the most recent token
                    token_part = line.split("Reset Token: ")[1].strip()
                    reset_token = token_part
            
            if reset_token:
                print(f"Found reset token: {reset_token}")
                
                # Step 4: Reset password with token
                print("\nStep 4: Resetting password with token...")
                async with session.post(
                    f"{base_url}/auth/reset",
                    json={"token": reset_token, "password": new_password}
                ) as response:
                    reset_status = response.status
                    reset_data = await response.json()
                    print(f"Reset result: {reset_status} - {reset_data}")
                
                if reset_status == 200:
                    print("✅ Password reset successful!")
                    
                    # Step 5: Test login with old password (should fail)
                    print("\nStep 5: Testing login with old password (should fail)...")
                    async with session.post(
                        f"{base_url}/auth/login",
                        json={"email": test_email, "password": test_password}
                    ) as response:
                        old_status = response.status
                        old_data = await response.json()
                        print(f"Old password: {old_status} - {old_data.get('detail', 'Success')}")
                    
                    # Step 6: Test login with new password (should work)
                    print("\nStep 6: Testing login with new password (should work)...")
                    async with session.post(
                        f"{base_url}/auth/login",
                        json={"email": test_email, "password": new_password}
                    ) as response:
                        new_status = response.status
                        new_data = await response.json()
                        print(f"New password: {new_status} - {new_data.get('detail', 'Success')}")
                        if new_status == 200:
                            print(f"✅ Login successful! User: {new_data.get('user', {}).get('email')}")
                    
                    # Final Summary
                    print("\n" + "=" * 50)
                    print("📊 COMPLETE PASSWORD RESET TEST RESULTS")
                    print("=" * 50)
                    print(f"✅ User registration: SUCCESS")
                    print(f"✅ Original login: SUCCESS")
                    print(f"✅ Password reset request: SUCCESS")
                    print(f"✅ Password reset with token: SUCCESS")
                    print(f"{'✅' if old_status != 200 else '❌'} Old password rejected: {'SUCCESS' if old_status != 200 else 'FAILED'}")
                    print(f"{'✅' if new_status == 200 else '❌'} New password works: {'SUCCESS' if new_status == 200 else 'FAILED'}")
                    
                    if old_status != 200 and new_status == 200:
                        print("\n🎉 COMPLETE SUCCESS: Password reset cycle working perfectly!")
                        print("✅ Full forgot → email → reset → login flow verified")
                        print("✅ Old password no longer works")
                        print("✅ New password works for login")
                    elif new_status == 200:
                        print("\n⚠️  PARTIAL SUCCESS: New password works but old password not rejected")
                    else:
                        print("\n❌ FAILED: New password doesn't work")
                        
                else:
                    print(f"❌ Password reset failed: {reset_data}")
            else:
                print("❌ Could not find reset token in logs")
                
        except Exception as e:
            print(f"❌ Error extracting token: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_user())