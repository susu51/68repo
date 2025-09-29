#!/usr/bin/env python3
"""
Fix courier KYC approval status
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def fix_courier_kyc():
    # Load environment
    load_dotenv('/app/backend/.env')
    mongo_url = os.environ['MONGO_URL']
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client.delivertr_database
    
    # Find test courier
    courier = await db.users.find_one({"email": "testcourier@courier.com"})
    
    if courier:
        print(f"Found courier: {courier['id']}")
        print(f"Current kyc_status: {courier.get('kyc_status')}")
        print(f"Current kyc_approved: {courier.get('kyc_approved')}")
        
        # Update courier to set kyc_approved = True
        result = await db.users.update_one(
            {"id": courier["id"]},
            {"$set": {
                "kyc_approved": True,
                "kyc_status": "approved",
                "is_online": True  # Also set online for testing
            }}
        )
        
        print(f"Update result: {result.modified_count} documents modified")
        
        # Verify update
        updated_courier = await db.users.find_one({"id": courier["id"]})
        print(f"Updated kyc_approved: {updated_courier.get('kyc_approved')}")
        print(f"Updated is_online: {updated_courier.get('is_online')}")
        
    else:
        print("Courier not found")
    
    # Also check if we have any orders with status 'created' or 'pending'
    orders = await db.orders.find({"status": {"$in": ["created", "pending"]}}).to_list(length=10)
    print(f"Found {len(orders)} orders with created/pending status")
    
    for order in orders:
        print(f"Order {order['id']}: status={order['status']}, courier_id={order.get('courier_id')}")
    
    # Update order status to 'pending' if it's 'created'
    if orders:
        for order in orders:
            if order['status'] == 'created':
                await db.orders.update_one(
                    {"id": order["id"]},
                    {"$set": {"status": "pending"}}
                )
                print(f"Updated order {order['id']} status to pending")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_courier_kyc())