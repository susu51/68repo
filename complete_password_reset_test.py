#!/usr/bin/env python3
"""
Complete Password Reset Flow Test
=================================

Test the complete password reset cycle with real tokens extracted from console logs.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class CompletePasswordResetTest:
    def __init__(self):
        self.base_url = "https://kuryecini-auth.preview.emergentagent.com/api"
        self.session = None
        self.test_email = "admin@kuryecini.com"
        self.current_password = "KuryeciniAdmin2024!"
        self.new_password = "NewSecurePassword123!"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: dict = None):
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(method, url, json=data) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                return response.status, response_data
        except Exception as e:
            return 0, {"error": str(e)}

    async def test_complete_flow(self):
        """Test complete password reset flow"""
        print("🔄 COMPLETE PASSWORD RESET FLOW TEST")
        print("=" * 50)
        
        # Step 1: Request password reset
        print("Step 1: Requesting password reset...")
        status, response = await self.make_request(
            "POST", "/auth/forgot", 
            {"email": self.test_email}
        )
        print(f"✅ Forgot password request: {status} - {response.get('message', response)}")
        
        # Step 2: Get token from logs (manual step)
        print("\nStep 2: Extract token from backend logs...")
        print("🔍 Check the backend logs above for the latest reset token")
        
        # Use the most recent token from the logs
        # From the logs, I can see: a8171b0179c89b7c-ecba4587-5b21-45a1-8006-54caba1ecedb
        reset_token = "a8171b0179c89b7c-ecba4587-5b21-45a1-8006-54caba1ecedb"
        print(f"Using token: {reset_token}")
        
        # Step 3: Reset password with real token
        print("\nStep 3: Resetting password with real token...")
        status, response = await self.make_request(
            "POST", "/auth/reset",
            {
                "token": reset_token,
                "password": self.new_password
            }
        )
        
        if status == 200 and response.get("success"):
            print(f"✅ Password reset successful: {response.get('message')}")
            password_reset_success = True
        else:
            print(f"❌ Password reset failed: {status} - {response}")
            password_reset_success = False
        
        # Step 4: Test login with old password (should fail)
        print("\nStep 4: Testing login with old password (should fail)...")
        status, response = await self.make_request(
            "POST", "/auth/login",
            {
                "email": self.test_email,
                "password": self.current_password
            }
        )
        
        if status != 200:
            print(f"✅ Old password correctly rejected: {status}")
            old_password_rejected = True
        else:
            print(f"❌ Old password still works: {status} - This is unexpected!")
            old_password_rejected = False
        
        # Step 5: Test login with new password (should work)
        if password_reset_success:
            print("\nStep 5: Testing login with new password (should work)...")
            status, response = await self.make_request(
                "POST", "/auth/login",
                {
                    "email": self.test_email,
                    "password": self.new_password
                }
            )
            
            if status == 200 and response.get("access_token"):
                print(f"✅ New password login successful!")
                new_password_works = True
            else:
                print(f"❌ New password login failed: {status} - {response}")
                new_password_works = False
        else:
            print("\nStep 5: Skipping new password test (reset failed)")
            new_password_works = False
        
        # Step 6: Reset password back to original (cleanup)
        if password_reset_success and new_password_works:
            print("\nStep 6: Resetting password back to original (cleanup)...")
            
            # Request another reset
            status, response = await self.make_request(
                "POST", "/auth/forgot", 
                {"email": self.test_email}
            )
            
            print("⏳ Waiting for new reset token... (check logs)")
            await asyncio.sleep(2)  # Give time for email to be sent
            
            # Note: In a real scenario, we'd extract the new token from logs
            print("📝 Manual step: Extract new token from logs and reset to original password")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 COMPLETE FLOW TEST SUMMARY")
        print("=" * 50)
        
        if password_reset_success and old_password_rejected and new_password_works:
            print("🎉 COMPLETE SUCCESS: Full password reset cycle working perfectly!")
            print("✅ Password reset with valid token: SUCCESS")
            print("✅ Old password rejected: SUCCESS") 
            print("✅ New password works: SUCCESS")
        elif password_reset_success:
            print("⚠️  PARTIAL SUCCESS: Password reset works but verification incomplete")
            print(f"✅ Password reset with valid token: SUCCESS")
            print(f"{'✅' if old_password_rejected else '❌'} Old password rejected: {'SUCCESS' if old_password_rejected else 'FAILED'}")
            print(f"{'✅' if new_password_works else '❌'} New password works: {'SUCCESS' if new_password_works else 'FAILED'}")
        else:
            print("❌ FAILED: Password reset with valid token failed")
            print("This indicates an issue with the reset endpoint or token validation")

async def main():
    async with CompletePasswordResetTest() as tester:
        await tester.test_complete_flow()

if __name__ == "__main__":
    asyncio.run(main())