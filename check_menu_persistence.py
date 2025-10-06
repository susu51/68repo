#!/usr/bin/env python3
"""
Check menu items persistence in database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini')

async def check_menu_persistence():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    try:
        # Check all collections that might have menu items
        collections = ['menu_items', 'products', 'business_menu']
        
        for collection_name in collections:
            collection = getattr(db, collection_name)
            items = await collection.find().to_list(length=None)
            print(f"\n📋 Collection '{collection_name}': {len(items)} items")
            
            for item in items[:3]:  # Show first 3 items
                business_id = item.get('business_id', 'N/A')
                title = item.get('title') or item.get('name', 'N/A')
                print(f"   - {title} (Business: {business_id})")
        
        # Check specifically for business-001 items
        print(f"\n🔍 Searching for business-001 menu items...")
        
        for collection_name in collections:
            collection = getattr(db, collection_name)
            business_items = await collection.find({"business_id": "business-001"}).to_list(length=None)
            print(f"   {collection_name}: {len(business_items)} items for business-001")
            
            for item in business_items:
                title = item.get('title') or item.get('name', 'N/A')
                price = item.get('price', 'N/A')
                available = item.get('is_available', item.get('availability', 'N/A'))
                print(f"     - {title} (₺{price}) - Available: {available}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_menu_persistence())