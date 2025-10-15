#!/usr/bin/env python3
"""
Test Password Reset with Regular User
=====================================
"""

import asyncio
import aiohttp
import json

async def test_regular_user():
    base_url = "https://biz-panel.preview.emergentagent.com/api"
    test_email = "testuser@example.com"
    test_password = "TestPassword123!"
    new_password = "NewTestPassword456!"
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 TESTING PASSWORD RESET WITH REGULAR USER")
        print("=" * 50)
        
        # Step 1: Create a regular user first
        print("Step 1: Creating regular user...")
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
        
        if reg_status != 201 and "already registered" not in str(reg_data):
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
        
        print("\n📧 Check backend logs for reset token!")
        print("Look for the latest 'Reset Token: [token]' for testuser@example.com")
        
        # For now, let's simulate the rest of the flow
        print("\n📝 MANUAL STEPS TO COMPLETE:")
        print("1. Extract reset token from backend logs")
        print("2. Test password reset with extracted token")
        print("3. Verify old password no longer works")
        print("4. Verify new password works")
        
        print(f"\nTest commands:")
        print(f"Reset: POST /api/auth/reset {{\"token\": \"EXTRACTED_TOKEN\", \"password\": \"{new_password}\"}}")
        print(f"Old login: POST /api/auth/login {{\"email\": \"{test_email}\", \"password\": \"{test_password}\"}}")
        print(f"New login: POST /api/auth/login {{\"email\": \"{test_email}\", \"password\": \"{new_password}\"}}")

if __name__ == "__main__":
    asyncio.run(test_regular_user())