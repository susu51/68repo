#!/usr/bin/env python3
"""
Debug products in database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini')

async def debug_products():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    try:
        # Check all products
        all_products = await db.products.find().to_list(length=None)
        print(f"Total products in DB: {len(all_products)}")
        
        for product in all_products:
            print(f"Product: {product.get('name')} | Business ID: {product.get('business_id')}")
        
        # Check specific business
        business_id = "6704e226-0d67-4c6b-ad0f-030c026540f3"
        specific_products = await db.products.find({"business_id": business_id}).to_list(length=None)
        print(f"\nProducts for business {business_id}: {len(specific_products)}")
        
        for product in specific_products:
            print(f"  - {product.get('name')} (₺{product.get('price')})")
            
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_products())