#!/usr/bin/env python3
"""
Address Management Fix Verification Test
========================================

This script tests the fixed address endpoints to verify they work correctly.
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://courier-stable.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

async def test_address_fixes():
    """Test the fixed address endpoints"""
    timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Authenticate customer
        login_data = {
            "email": "testcustomer@example.com",
            "password": "test123"
        }
        
        async with session.post(
            f"{BACKEND_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print("❌ Authentication failed")
                return
                
            data = await response.json()
            token = data.get("access_token")
            print(f"✅ Authentication successful (token: {len(token)} chars)")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test address
        test_address = {
            "label": "Fix Test Address",
            "city": "İstanbul",
            "district": "Beşiktaş",
            "description": "Address created to test the fixes",
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        print("\n🔧 Testing Fixed Address Endpoints")
        print("=" * 40)
        
        # Test POST (create address)
        async with session.post(
            f"{BACKEND_URL}/user/addresses",
            json=test_address,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                address_id = result.get("id")
                print(f"✅ POST /api/user/addresses: Created address {address_id}")
            else:
                error_text = await response.text()
                print(f"❌ POST /api/user/addresses: {response.status} - {error_text}")
                return
        
        # Test PUT (update address)
        updated_address = {
            "label": "Updated Fix Test Address",
            "city": "Ankara",
            "district": "Çankaya",
            "description": "Updated address to test the fixes",
            "lat": 39.9334,
            "lng": 32.8597
        }
        
        async with session.put(
            f"{BACKEND_URL}/user/addresses/{address_id}",
            json=updated_address,
            headers=headers
        ) as response:
            if response.status == 200:
                print(f"✅ PUT /api/user/addresses/{address_id}: Address updated successfully")
            else:
                error_text = await response.text()
                print(f"❌ PUT /api/user/addresses/{address_id}: {response.status} - {error_text}")
        
        # Test POST set-default
        async with session.post(
            f"{BACKEND_URL}/user/addresses/{address_id}/set-default",
            headers=headers
        ) as response:
            if response.status == 200:
                print(f"✅ POST /api/user/addresses/{address_id}/set-default: Set as default successfully")
            else:
                error_text = await response.text()
                print(f"❌ POST /api/user/addresses/{address_id}/set-default: {response.status} - {error_text}")
        
        # Test DELETE
        async with session.delete(
            f"{BACKEND_URL}/user/addresses/{address_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                print(f"✅ DELETE /api/user/addresses/{address_id}: Address deleted successfully")
            else:
                error_text = await response.text()
                print(f"❌ DELETE /api/user/addresses/{address_id}: {response.status} - {error_text}")
        
        print("\n🎉 Address endpoint fixes verification complete!")

if __name__ == "__main__":
    asyncio.run(test_address_fixes())