#!/usr/bin/env python3
"""
MongoDB Index Setup Script for Kuryecini Customer App
Creates necessary indexes for geolocation and performance optimization
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT

async def setup_indexes():
    """Setup MongoDB indexes for the Customer App"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_uri)
    
    # Extract database name
    if "/kuryecini_database" in mongo_uri or mongo_uri.endswith("/"):
        db = client.kuryecini_database
    else:
        try:
            db_name = mongo_uri.split("/")[-1].split("?")[0]
            if db_name:
                db = client[db_name]
            else:
                db = client.kuryecini_database
        except:
            db = client.kuryecini_database
    
    print(f"Setting up indexes for database: {db.name}")
    
    try:
        # 1. Businesses collection indexes
        print("Creating businesses collection indexes...")
        
        # Geospatial index for location-based queries (2dsphere for MongoDB 2.4+)
        await db.businesses.create_index([("location", "2dsphere")])
        print("✅ Created 2dsphere index on businesses.location")
        
        # City normalization index
        await db.businesses.create_index([("city_normalized", ASCENDING)])
        print("✅ Created index on businesses.city_normalized")
        
        # KYC status and active status compound index
        await db.businesses.create_index([
            ("kyc_status", ASCENDING),
            ("is_active", ASCENDING)
        ])
        print("✅ Created compound index on businesses.kyc_status + is_active")
        
        # Business category index
        await db.businesses.create_index([("business_category", ASCENDING)])
        print("✅ Created index on businesses.business_category")
        
        # 2. Products collection indexes
        print("\nCreating products collection indexes...")
        
        # Business ID index for product lookups
        await db.products.create_index([("business_id", ASCENDING)])
        print("✅ Created index on products.business_id")
        
        # Availability index
        await db.products.create_index([("is_available", ASCENDING)])
        print("✅ Created index on products.is_available")
        
        # Category index for filtering
        await db.products.create_index([("category", ASCENDING)])
        print("✅ Created index on products.category")
        
        # Compound index for business + availability
        await db.products.create_index([
            ("business_id", ASCENDING),
            ("is_available", ASCENDING)
        ])
        print("✅ Created compound index on products.business_id + is_available")
        
        # 3. Orders collection indexes
        print("\nCreating orders collection indexes...")
        
        # Customer orders index
        await db.orders.create_index([("customer_id", ASCENDING)])
        print("✅ Created index on orders.customer_id")
        
        # Order status index
        await db.orders.create_index([("status", ASCENDING)])
        print("✅ Created index on orders.status")
        
        # Created date index (for recent orders)
        await db.orders.create_index([("created_at", DESCENDING)])
        print("✅ Created index on orders.created_at")
        
        # Compound index for customer + status
        await db.orders.create_index([
            ("customer_id", ASCENDING),
            ("status", ASCENDING)
        ])
        print("✅ Created compound index on orders.customer_id + status")
        
        # 4. User addresses collection indexes
        print("\nCreating user_addresses collection indexes...")
        
        # User ID index
        await db.user_addresses.create_index([("user_id", ASCENDING)])
        print("✅ Created index on user_addresses.user_id")
        
        # Location index for addresses
        await db.user_addresses.create_index([("lat", ASCENDING), ("lng", ASCENDING)])
        print("✅ Created compound index on user_addresses.lat + lng")
        
        # 5. Profile system indexes
        print("\nCreating profile system indexes...")
        
        # Coupons - assigned users index
        await db.coupons.create_index([("assigned_user_ids", ASCENDING)])
        print("✅ Created index on coupons.assigned_user_ids")
        
        # Coupons - status and validity
        await db.coupons.create_index([
            ("status", ASCENDING),
            ("valid_until", ASCENDING)
        ])
        print("✅ Created compound index on coupons.status + valid_until")
        
        # Discounts - user specific
        await db.discounts.create_index([("user_id", ASCENDING)])
        print("✅ Created index on discounts.user_id")
        
        # Payment methods - user specific
        await db.payment_methods.create_index([("user_id", ASCENDING)])
        print("✅ Created index on payment_methods.user_id")
        
        # Reviews - compound indexes for uniqueness
        await db.reviews.create_index([
            ("order_id", ASCENDING),
            ("target_type", ASCENDING),
            ("user_id", ASCENDING)
        ], unique=True)
        print("✅ Created unique compound index on reviews.order_id + target_type + user_id")
        
        # Reviews - target lookup
        await db.reviews.create_index([
            ("target_type", ASCENDING),
            ("target_id", ASCENDING)
        ])
        print("✅ Created compound index on reviews.target_type + target_id")
        
        # 6. Performance indexes
        print("\nCreating performance optimization indexes...")
        
        # Users collection indexes
        await db.users.create_index([("email", ASCENDING)], unique=True)
        print("✅ Created unique index on users.email")
        
        await db.users.create_index([("role", ASCENDING)])
        print("✅ Created index on users.role")
        
        # Text search index for business names (optional)
        await db.businesses.create_index([
            ("business_name", TEXT),
            ("description", TEXT),
            ("business_category", TEXT)
        ])
        print("✅ Created text search index on businesses")
        
        print("\n🎉 All indexes created successfully!")
        
        # Verify indexes
        print("\n📋 Index verification:")
        collections = ['businesses', 'products', 'orders', 'user_addresses', 'users']
        
        for collection_name in collections:
            collection = getattr(db, collection_name)
            indexes = await collection.list_indexes().to_list(None)
            print(f"\n{collection_name}: {len(indexes)} indexes")
            for idx in indexes:
                print(f"  - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_indexes())