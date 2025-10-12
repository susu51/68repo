#!/usr/bin/env python3
"""
Update existing business users with GPS coordinates based on their city/district
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from utils.turkish_cities_coordinates import get_city_coordinates

async def update_business_coordinates():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kuryecini')
    client = AsyncIOMotorClient(mongo_url)
    db = client['kuryecini']
    
    print("🔄 Updating business GPS coordinates...")
    
    # Find all business users
    businesses = await db.users.find({"role": "business"}).to_list(length=None)
    
    print(f"📊 Found {len(businesses)} business users")
    
    updated_count = 0
    skipped_count = 0
    not_found_count = 0
    
    for business in businesses:
        business_id = business.get("_id") or business.get("id")
        city = business.get("city")
        district = business.get("district")
        business_name = business.get("business_name", "Unknown")
        
        # Skip if already has coordinates
        if business.get("lat") and business.get("lng"):
            print(f"⏭️  Skipping {business_name} - already has coordinates")
            skipped_count += 1
            continue
        
        if not city:
            print(f"⚠️  Skipping {business_name} - no city information")
            not_found_count += 1
            continue
        
        # Get coordinates
        coordinates = get_city_coordinates(city, district)
        
        if coordinates:
            lat = coordinates["lat"]
            lng = coordinates["lng"]
            
            # Update business with coordinates
            await db.users.update_one(
                {"_id": business_id},
                {"$set": {
                    "lat": lat,
                    "lng": lng
                }}
            )
            
            print(f"✅ Updated {business_name} ({city}/{district}): {lat}, {lng}")
            updated_count += 1
        else:
            print(f"❌ No coordinates found for {business_name} ({city}/{district})")
            not_found_count += 1
    
    print("\n" + "="*50)
    print(f"📊 Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ⏭️  Skipped (already has coords): {skipped_count}")
    print(f"  ❌ Not found: {not_found_count}")
    print(f"  📈 Total processed: {len(businesses)}")
    print("="*50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_business_coordinates())
