#!/usr/bin/env python3
"""
Migration: Fix Order Schema
- Ensure all orders have restaurant_id and business_id
- Set default status to 'created' if missing
- Create snapshots for address and items
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

async def migrate_orders():
    """Migrate existing orders to new schema"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    print("🔧 Starting order schema migration...")
    
    # Get all orders
    orders = await db.orders.find({}).to_list(length=None)
    print(f"📊 Found {len(orders)} orders to check")
    
    fixed_count = 0
    
    for order in orders:
        updates = {}
        needs_update = False
        
        # 1. Fix missing business_id
        if not order.get('business_id'):
            # Try to get from restaurant
            restaurant_id = order.get('restaurant_id')
            if restaurant_id:
                restaurant = await db.users.find_one({"id": restaurant_id, "role": "business"})
                if restaurant:
                    updates['business_id'] = restaurant['id']
                    needs_update = True
                    print(f"  ✅ Added business_id to order {order.get('id')}")
        
        # 2. Fix missing/invalid status
        if not order.get('status') or order.get('status') not in [
            'created', 'confirmed', 'preparing', 'ready', 
            'picked_up', 'delivering', 'delivered', 'cancelled'
        ]:
            updates['status'] = 'created'
            needs_update = True
            print(f"  ✅ Set status='created' for order {order.get('id')}")
        
        # 3. Ensure payment_status exists
        if not order.get('payment_status'):
            updates['payment_status'] = 'unpaid'
            needs_update = True
        
        # 4. Ensure payment_method exists
        if not order.get('payment_method'):
            updates['payment_method'] = 'cash'
            needs_update = True
        
        # 5. Create timeline if not exists
        if not order.get('timeline'):
            updates['timeline'] = [{
                'event': 'created',
                'at': order.get('created_at', datetime.now(timezone.utc)),
                'meta': {'note': 'Order created'}
            }]
            needs_update = True
        
        # 6. Ensure totals structure
        if not order.get('totals'):
            total_amount = order.get('total_amount', 0)
            updates['totals'] = {
                'sub': total_amount,
                'delivery': 0,
                'discount': 0,
                'grand': total_amount
            }
            needs_update = True
        
        # 7. Create address_snapshot if not exists
        if not order.get('address_snapshot') and order.get('delivery_address'):
            updates['address_snapshot'] = {
                'full': order.get('delivery_address'),
                'lat': order.get('delivery_lat'),
                'lng': order.get('delivery_lng'),
                'city': order.get('city'),
                'district': order.get('district')
            }
            needs_update = True
        
        # 8. Rename items to items_snapshot if needed
        if order.get('items') and not order.get('items_snapshot'):
            updates['items_snapshot'] = order['items']
            needs_update = True
        
        # Apply updates
        if needs_update:
            await db.orders.update_one(
                {'_id': order['_id']},
                {'$set': updates}
            )
            fixed_count += 1
    
    print(f"\n✅ Migration complete: Fixed {fixed_count}/{len(orders)} orders")
    
    # Create indexes
    print("\n📑 Creating indexes...")
    try:
        await db.orders.create_index([("business_id", 1), ("status", 1), ("created_at", -1)])
        print("  ✅ Index: business_id + status + created_at")
        
        await db.orders.create_index([("restaurant_id", 1), ("status", 1), ("updated_at", -1)])
        print("  ✅ Index: restaurant_id + status + updated_at")
        
        await db.orders.create_index([("user_id", 1), ("created_at", -1)])
        print("  ✅ Index: user_id + created_at")
        
        await db.orders.create_index([("customer_id", 1), ("created_at", -1)])
        print("  ✅ Index: customer_id + created_at")
    except Exception as e:
        print(f"  ⚠️ Index creation warning: {e}")
    
    client.close()
    print("\n🎉 Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_orders())
