#!/usr/bin/env python3
"""
Test admin login directly
"""

import asyncio
import os
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

async def test_admin_login():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client.delivertr_database
    
    admin_email = "admin@kuryecini.com"
    admin_password = "KuryeciniAdmin2024!"
    
    # Find admin user
    user = await db.users.find_one({"email": admin_email})
    if user:
        print(f"Found admin user: {user['email']}")
        print(f"User fields: {list(user.keys())}")
        print(f"Role: {user.get('role')}")
        
        # Test password verification
        if "password_hash" in user:
            password_hash = user["password_hash"]
            is_valid = bcrypt.checkpw(admin_password.encode('utf-8'), password_hash.encode('utf-8'))
            print(f"Password verification: {is_valid}")
        else:
            print("No password_hash field found!")
    else:
        print("Admin user not found!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_admin_login())