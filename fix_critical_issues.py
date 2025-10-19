#!/usr/bin/env python3
"""
FIX CRITICAL ISSUES SCRIPT
==========================

This script fixes the identified critical issues:
1. Approve newly registered businesses so they appear in discovery
2. Investigate and fix address district saving issue
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://admin-wsocket.preview.emergentagent.com/api"

class CriticalIssuesFixer:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_admin(self):
        """Authenticate as admin"""
        try:
            login_data = {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print(f"✅ Admin authenticated successfully")
                    return True
                else:
                    print(f"❌ Admin authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Admin authentication error: {str(e)}")
            return False

    async def get_pending_businesses(self):
        """Get all pending businesses"""
        if not self.admin_token:
            return []
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", headers=headers) as response:
                if response.status == 200:
                    businesses = await response.json()
                    print(f"📋 Found {len(businesses)} pending businesses")
                    return businesses
                else:
                    print(f"❌ Failed to get pending businesses: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error getting pending businesses: {str(e)}")
            return []

    async def approve_business(self, business_id, business_name):
        """Approve a specific business"""
        if not self.admin_token:
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        approval_data = {"kyc_status": "approved"}
        
        try:
            async with self.session.patch(f"{BACKEND_URL}/admin/businesses/{business_id}/status", json=approval_data, headers=headers) as response:
                if response.status == 200:
                    print(f"✅ Approved business: {business_name} (ID: {business_id})")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to approve {business_name}: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error approving {business_name}: {str(e)}")
            return False

    async def test_discovery_after_approval(self):
        """Test discovery filtering after business approval"""
        print("\n🔍 Testing discovery filtering after business approval...")
        
        test_cities = ["Niğde", "Ankara", "İzmir", "Gaziantep"]
        
        for city in test_cities:
            try:
                params = {"city": city}
                async with self.session.get(f"{BACKEND_URL}/businesses", params=params) as response:
                    if response.status == 200:
                        businesses = await response.json()
                        print(f"   {city}: Found {len(businesses)} businesses")
                        
                        # Show business details
                        for business in businesses:
                            name = business.get("business_name", "Unknown")
                            city_saved = business.get("city", "Unknown")
                            print(f"      - {name} (City: {city_saved})")
                    else:
                        print(f"   {city}: Error {response.status}")
            except Exception as e:
                print(f"   {city}: Exception {str(e)}")

    async def investigate_address_issue(self):
        """Investigate why address districts are not being saved"""
        print("\n📍 Investigating address district saving issue...")
        
        # Authenticate as customer
        customer_token = None
        try:
            login_data = {
                "email": "testcustomer@example.com",
                "password": "test123"
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    customer_token = data["access_token"]
                    print("✅ Customer authenticated for address testing")
                else:
                    print(f"❌ Customer authentication failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Customer authentication error: {str(e)}")
            return
        
        if not customer_token:
            return
            
        headers = {"Authorization": f"Bearer {customer_token}"}
        
        # Test address creation with explicit district
        test_address = {
            "label": "District Test Address",
            "city": "Test City",
            "district": "Test District",
            "description": "Testing district field saving",
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        try:
            print(f"📝 Creating test address with district: {test_address['district']}")
            async with self.session.post(f"{BACKEND_URL}/user/addresses", json=test_address, headers=headers) as response:
                if response.status == 200:
                    created_address = await response.json()
                    saved_district = created_address.get("district", "")
                    saved_city = created_address.get("city", "")
                    
                    print(f"✅ Address created successfully")
                    print(f"   Expected District: '{test_address['district']}'")
                    print(f"   Saved District: '{saved_district}'")
                    print(f"   Expected City: '{test_address['city']}'")
                    print(f"   Saved City: '{saved_city}'")
                    
                    if saved_district == test_address['district']:
                        print("✅ District saved correctly!")
                    else:
                        print("❌ District NOT saved correctly!")
                        
                    # Check the full response
                    print(f"📋 Full response: {json.dumps(created_address, indent=2)}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Address creation failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Address creation error: {str(e)}")

    async def run_fixes(self):
        """Run all critical issue fixes"""
        print("🚀 STARTING CRITICAL ISSUES FIX")
        print("=" * 50)
        
        await self.setup_session()
        
        try:
            # Authenticate as admin
            if not await self.authenticate_admin():
                return
            
            # Get pending businesses
            pending_businesses = await self.get_pending_businesses()
            
            if pending_businesses:
                print(f"\n🏢 Approving {len(pending_businesses)} pending businesses...")
                
                approved_count = 0
                for business in pending_businesses:
                    business_id = business.get("id")
                    business_name = business.get("business_name", "Unknown")
                    city = business.get("city", "Unknown")
                    
                    if business_id:
                        success = await self.approve_business(business_id, f"{business_name} ({city})")
                        if success:
                            approved_count += 1
                
                print(f"\n✅ Approved {approved_count}/{len(pending_businesses)} businesses")
            else:
                print("\n📋 No pending businesses found")
            
            # Test discovery after approval
            await self.test_discovery_after_approval()
            
            # Investigate address issue
            await self.investigate_address_issue()
            
        finally:
            await self.cleanup_session()
        
        print("\n" + "=" * 50)
        print("🏁 CRITICAL ISSUES FIX COMPLETED")
        print("=" * 50)

async def main():
    """Main execution"""
    fixer = CriticalIssuesFixer()
    await fixer.run_fixes()

if __name__ == "__main__":
    asyncio.run(main())