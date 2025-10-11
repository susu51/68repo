#!/usr/bin/env python3
"""
Script to approve the testbusiness@example.com user for KYC testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import uuid
from datetime import datetime, timezone

async def approve_business_user():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017/kuryecini")
    db = client.kuryecini
    
    print("🔍 Looking for testbusiness@example.com...")
    
    # Find the business user
    business_user = await db.users.find_one({"email": "testbusiness@example.com"})
    
    if business_user:
        print(f"✅ Found business user: {business_user['email']}")
        print(f"   Current KYC status: {business_user.get('kyc_status', 'not set')}")
        
        # Update KYC status to approved
        result = await db.users.update_one(
            {"email": "testbusiness@example.com"},
            {"$set": {
                "kyc_status": "approved",
                "approved_at": datetime.now(timezone.utc)
            }}
        )
        
        if result.modified_count > 0:
            print("✅ Business user approved successfully!")
        else:
            print("⚠️ No changes made (user might already be approved)")
    else:
        print("❌ Business user not found. Creating new approved business user...")
        
        # Create new approved business user
        hashed_password = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        business_user_doc = {
            "id": str(uuid.uuid4()),
            "email": "testbusiness@example.com",
            "password_hash": hashed_password,
            "role": "business",
            "business_name": "Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address, Istanbul",
            "city": "Istanbul",
            "city_normalized": "istanbul",
            "district": "Kadıköy",
            "business_category": "gida",
            "description": "Test restaurant for KYC testing",
            "is_active": True,
            "kyc_status": "approved",  # Pre-approved for testing
            "business_status": "approved",
            "approved_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(business_user_doc)
        print("✅ Created new approved business user!")
    
    # Verify the approval
    updated_user = await db.users.find_one({"email": "testbusiness@example.com"})
    if updated_user:
        print(f"🔍 Verification - KYC Status: {updated_user.get('kyc_status')}")
        print(f"   User ID: {updated_user.get('id')}")
        print(f"   Role: {updated_user.get('role')}")
    
    client.close()
    print("✅ Business user approval complete!")

if __name__ == "__main__":
    asyncio.run(approve_business_user())