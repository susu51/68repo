#!/usr/bin/env python3
"""
Create MongoDB indexes for orders collection
Phase 1: Critical indexes for order routing and business queries
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def create_indexes():
    """Create indexes for orders collection"""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/kuryecini")
    
    print(f"🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    print("📊 Creating indexes for 'orders' collection...")
    
    # Index 1: business_id + status + created_at (for business incoming orders)
    await db.orders.create_index([
        ("business_id", 1),
        ("status", 1),
        ("created_at", -1)
    ], name="business_status_created")
    print("✅ Created: business_id + status + created_at")
    
    # Index 2: restaurant_id + status + updated_at (for restaurant queries)
    await db.orders.create_index([
        ("restaurant_id", 1),
        ("status", 1),
        ("updated_at", -1)
    ], name="restaurant_status_updated")
    print("✅ Created: restaurant_id + status + updated_at")
    
    # Index 3: customer_id + created_at (for customer order history)
    await db.orders.create_index([
        ("customer_id", 1),
        ("created_at", -1)
    ], name="customer_created")
    print("✅ Created: customer_id + created_at")
    
    # Index 4: status + created_at (for admin queries)
    await db.orders.create_index([
        ("status", 1),
        ("created_at", -1)
    ], name="status_created")
    print("✅ Created: status + created_at")
    
    # Index 5: _id lookup (already exists by default, but ensure it's there)
    await db.orders.create_index([("_id", 1)], name="_id_index", unique=True)
    print("✅ Ensured: _id index")
    
    # Show all indexes
    indexes = await db.orders.list_indexes().to_list(length=None)
    print("\n📋 All indexes on 'orders' collection:")
    for idx in indexes:
        print(f"   - {idx['name']}: {idx['key']}")
    
    print("\n✅ Index creation completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
