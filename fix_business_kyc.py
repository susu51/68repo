#!/usr/bin/env python3
"""
Fix business-001 KYC status
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini')

async def fix_business_kyc():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    try:
        # Check business-001 first
        business = await db.users.find_one({"id": "business-001"})
        print(f"Found business: {business}")
        
        # Update business-001 with KYC approved status
        result = await db.users.update_one(
            {"id": "business-001"},
            {
                "$set": {
                    "kyc_status": "approved",
                    "kyc_updated_at": datetime.now(timezone.utc),
                    "business_name": "Test İşletmesi",
                    "business_category": "gida",
                    "city": "İstanbul",
                    "city_normalized": "istanbul",
                    "address": "Test Address, İstanbul",
                    "tax_number": "1234567890"
                }
            }
        )
        
        if result.modified_count > 0:
            print("✅ business-001 KYC status updated to approved")
            print("✅ Added missing business fields")
        else:
            print("❌ No business found or already updated")
            
        # Verify update
        business = await db.users.find_one({"id": "business-001"})
        if business:
            print(f"📋 Business Name: {business.get('business_name', 'N/A')}")
            print(f"📋 KYC Status: {business.get('kyc_status', 'N/A')}")
            print(f"📋 Category: {business.get('business_category', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_business_kyc())