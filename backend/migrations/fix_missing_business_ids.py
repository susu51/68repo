#!/usr/bin/env python3
"""
Migration: Fix orders with missing business_id
Phase 1: Populate business_id from restaurant owner_id
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def fix_missing_business_ids():
    """Fix orders with missing business_id by looking up restaurant owner"""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/kuryecini")
    
    print(f"🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_database()
    
    print("\n🔍 Finding orders with missing business_id...")
    
    # Find orders without business_id
    orders_without_business = await db.orders.find({
        "$or": [
            {"business_id": {"$exists": False}},
            {"business_id": None},
            {"business_id": ""}
        ]
    }).to_list(length=None)
    
    print(f"📊 Found {len(orders_without_business)} orders without business_id")
    
    if len(orders_without_business) == 0:
        print("✅ All orders have business_id. No migration needed.")
        client.close()
        return
    
    fixed_count = 0
    failed_count = 0
    
    for order in orders_without_business:
        order_id = order.get("_id")
        restaurant_id = order.get("restaurant_id")
        
        if not restaurant_id:
            print(f"⚠️  Order {order_id}: No restaurant_id, skipping")
            failed_count += 1
            continue
        
        # Look up restaurant
        restaurant = await db.businesses.find_one({"_id": restaurant_id})
        
        if not restaurant:
            print(f"⚠️  Order {order_id}: Restaurant {restaurant_id} not found, skipping")
            failed_count += 1
            continue
        
        business_id = restaurant.get("owner_id") or restaurant.get("_id")
        
        if not business_id:
            print(f"⚠️  Order {order_id}: Restaurant has no owner_id, using restaurant _id")
            business_id = restaurant_id
        
        # Update order with business_id
        update_result = await db.orders.update_one(
            {"_id": order_id},
            {
                "$set": {
                    "business_id": business_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if update_result.modified_count > 0:
            print(f"✅ Order {order_id}: Set business_id = {business_id}")
            fixed_count += 1
        else:
            print(f"❌ Order {order_id}: Update failed")
            failed_count += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📦 Total: {len(orders_without_business)}")
    
    # Also fix missing created_at/updated_at
    print("\n🔍 Fixing missing timestamps...")
    now = datetime.now(timezone.utc)
    
    result = await db.orders.update_many(
        {"created_at": {"$exists": False}},
        {"$set": {"created_at": now}}
    )
    print(f"✅ Fixed {result.modified_count} orders with missing created_at")
    
    result = await db.orders.update_many(
        {"updated_at": {"$exists": False}},
        {"$set": {"updated_at": now}}
    )
    print(f"✅ Fixed {result.modified_count} orders with missing updated_at")
    
    print("\n✅ Migration completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_missing_business_ids())
