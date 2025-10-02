#!/usr/bin/env python3
"""
Fix admin user database field mismatch
"""

import asyncio
import os
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def fix_admin_user():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client.kuryecini_database
    
    admin_email = "admin@kuryecini.com"
    admin_password = "KuryeciniAdmin2024!"
    
    # Delete existing admin user
    result = await db.users.delete_one({"email": admin_email})
    print(f"Deleted {result.deleted_count} existing admin user(s)")
    
    # Create new admin user with correct field name
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
    
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": admin_email,
        "password_hash": password_hash.decode('utf-8'),  # Correct field name
        "first_name": "Admin",
        "last_name": "Kuryecini",
        "role": "admin",
        "is_active": True,
        "kyc_status": "approved",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(admin_user)
    print(f"✅ Admin user recreated with correct field: {admin_email} / {admin_password}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_admin_user())