#!/usr/bin/env python3
"""
Direct MongoDB insert for test products
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini')

async def insert_test_products():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    # Products for approved businesses
    products = [
        # Fix Test Restaurant (6704e226-0d67-4c6b-ad0f-030c026540f3)
        {
            "_id": str(uuid.uuid4()),
            "business_id": "6704e226-0d67-4c6b-ad0f-030c026540f3",
            "name": "Margherita Pizza",
            "description": "Domates sosu, mozzarella, fesleğen",
            "price": 45.0,
            "category": "pizza",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1604382354936-07c5b6f67692?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": str(uuid.uuid4()),
            "business_id": "6704e226-0d67-4c6b-ad0f-030c026540f3",
            "name": "Chicken Burger",
            "description": "Izgara tavuk, salata, patates",
            "price": 35.0,
            "category": "main",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": str(uuid.uuid4()),
            "business_id": "6704e226-0d67-4c6b-ad0f-030c026540f3",
            "name": "Caesar Salad",
            "description": "Marul, parmesan, kruton",
            "price": 25.0,
            "category": "salad",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        
        # New Test Restaurant (45b3c904-c138-4e3a-acef-832b2c80cd3c)
        {
            "_id": str(uuid.uuid4()),
            "business_id": "45b3c904-c138-4e3a-acef-832b2c80cd3c",
            "name": "Döner Kebap",
            "description": "Et döner, lavash, salata",
            "price": 30.0,
            "category": "main",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": str(uuid.uuid4()),
            "business_id": "45b3c904-c138-4e3a-acef-832b2c80cd3c",
            "name": "Lahmacun",
            "description": "İnce hamur, kıyma, sebze",
            "price": 15.0,
            "category": "main",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        
        # Dönercioo (23b59e66-0ad3-468c-b3a4-296bd4af63d7)
        {
            "_id": str(uuid.uuid4()),
            "business_id": "23b59e66-0ad3-468c-b3a4-296bd4af63d7",
            "name": "Adana Kebap",
            "description": "Acılı Adana kebap",
            "price": 40.0,
            "category": "main",
            "availability": True,
            "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=300",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    try:
        # Insert products
        result = await db.products.insert_many(products)
        print(f"✅ Inserted {len(result.inserted_ids)} products")
        
        # Verify insertion
        for product in products:
            count = await db.products.count_documents({"business_id": product["business_id"]})
            business_name = product["business_id"][:8] + "..."
            print(f"   Business {business_name}: {count} products")
            
    except Exception as e:
        print(f"❌ Error inserting products: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(insert_test_products())