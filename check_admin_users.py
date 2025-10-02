#!/usr/bin/env python3
"""
Check all admin users
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_admin_users():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client.kuryecini_database
    
    # Find all admin users
    users = await db.users.find({"role": "admin"}).to_list(None)
    print(f"Found {len(users)} admin users:")
    
    for i, user in enumerate(users):
        print(f"\nAdmin user {i+1}:")
        print(f"  Email: {user.get('email')}")
        print(f"  ID: {user.get('id')}")
        print(f"  Fields: {list(user.keys())}")
        print(f"  Has password_hash: {'password_hash' in user}")
        print(f"  Has password: {'password' in user}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_admin_users())