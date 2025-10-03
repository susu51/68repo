#!/usr/bin/env python3
"""
Migration script for city normalization and geospatial indexing
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from utils.city_normalize import normalize_city_name

async def migrate_cities():
    """Migrate existing businesses to add city_normalized field and location"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_uri)
    
    # Extract database name from URI
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
    
    print("🚀 Starting city normalization migration...")
    
    # Find all business users without city_normalized
    businesses = await db.users.find({
        "role": "business",
        "city_normalized": {"$exists": False}
    }).to_list(length=None)
    
    print(f"📊 Found {len(businesses)} businesses to migrate")
    
    updated_count = 0
    for business in businesses:
        city_original = business.get("city", "")
        if city_original:
            city_normalized = normalize_city_name(city_original)
            
            # Default location coordinates for major Turkish cities
            city_coordinates = {
                "ıstanbul": [28.9784, 41.0082],
                "ankara": [32.8597, 39.9334], 
                "ızmir": [27.1428, 38.4192],
                "bursa": [29.0661, 40.2669],
                "antalya": [30.7133, 36.8969],
                "gaziantep": [37.3781, 37.0662],
                "konya": [32.4846, 37.8715],
                "aksaray": [34.0370, 38.3687],  # Aksaray coordinates
                "kayseri": [35.4787, 38.7312],
                "trabzon": [39.7178, 41.0015],
                "samsun": [36.3360, 41.2867],
                "adana": [35.3213, 37.0000],
            }
            
            # Get coordinates for city (default to Istanbul if not found)
            coordinates = city_coordinates.get(city_normalized, [28.9784, 41.0082])
            
            # Create location object for GeoJSON Point
            location = {
                "type": "Point",
                "coordinates": coordinates  # [longitude, latitude]
            }
            
            # Update business with normalized city and location
            result = await db.users.update_one(
                {"_id": business["_id"]},
                {
                    "$set": {
                        "city_normalized": city_normalized,
                        "location": location
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Updated: {business.get('business_name', 'Unknown')} | {city_original} → {city_normalized}")
            else:
                print(f"❌ Failed to update: {business.get('business_name', 'Unknown')}")
    
    print(f"\n📈 Migration complete: {updated_count} businesses updated")
    
    # Create geospatial index
    print("🔍 Creating geospatial indexes...")
    try:
        # Create 2dsphere index on location field
        await db.users.create_index([("location", "2dsphere")])
        print("✅ Created 2dsphere index on 'location' field")
        
        # Create index on city_normalized for faster city filtering
        await db.users.create_index("city_normalized")
        print("✅ Created index on 'city_normalized' field")
        
        # Create compound index for city + geospatial queries
        await db.users.create_index([("city_normalized", 1), ("location", "2dsphere")])
        print("✅ Created compound index on 'city_normalized' + 'location'")
        
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")
    
    # List existing indexes
    print("\n📋 Current indexes:")
    indexes = await db.users.list_indexes().to_list(length=None)
    for idx in indexes:
        print(f"   - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
    
    await client.close()
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_cities())