"""
City-Strict Migration: Schema & Index Setup
- Add city_slug and district_slug fields
- Create geo indexes
- Backfill existing data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Turkish slug normalization
def normalize_turkish_slug(text):
    """Convert Turkish text to URL-safe slug"""
    if not text:
        return ""
    
    char_map = {
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g', 
        'ı': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u'
    }
    
    result = ""
    for char in text:
        result += char_map.get(char, char)
    
    return result.lower().replace(' ', '-')

async def run_migration():
    # MongoDB connection (simplified for local development)
    MONGO_URL = "mongodb://localhost:27017/kuryecini"
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    print("🚀 Starting City-Strict Migration...")
    
    # 1. Create indexes
    print("\n📁 Creating indexes...")
    
    try:
        # Business indexes
        await db.business.create_index([("location", "2dsphere")])
        print("✅ business.location 2dsphere index created")
        
        await db.business.create_index([
            ("address.city_slug", 1), 
            ("address.district_slug", 1)
        ])
        print("✅ business city_slug+district_slug index created")
        
        # Addresses indexes  
        await db.addresses.create_index([("location", "2dsphere")])
        print("✅ addresses.location 2dsphere index created")
        
        await db.addresses.create_index([("user_id", 1)])
        print("✅ addresses.user_id index created")
        
    except Exception as e:
        print(f"⚠️ Index creation (expected if exists): {e}")
    
    # 2. Backfill business collection
    print("\n🏢 Backfilling business collection...")
    
    business_count = 0
    async for business in db.business.find({}):
        update_needed = False
        update_doc = {}
        
        # Check if address needs slug fields
        if 'address' in business:
            address = business['address']
            
            if 'city' in address and 'city_slug' not in address:
                city_slug = normalize_turkish_slug(address['city'])
                update_doc['address.city_slug'] = city_slug
                update_needed = True
                
            if 'district' in address and 'district_slug' not in address:
                district_slug = normalize_turkish_slug(address['district'])
                update_doc['address.district_slug'] = district_slug
                update_needed = True
        
        if update_needed:
            await db.business.update_one(
                {'_id': business['_id']}, 
                {'$set': update_doc}
            )
            business_count += 1
            print(f"  Updated business: {business.get('name', 'Unknown')} -> {update_doc}")
    
    print(f"✅ Updated {business_count} business records")
    
    # 3. Backfill addresses collection
    print("\n📍 Backfilling addresses collection...")
    
    address_count = 0
    async for address in db.addresses.find({}):
        update_needed = False
        update_doc = {}
        
        if 'city' in address and 'city_slug' not in address:
            city_slug = normalize_turkish_slug(address['city'])
            update_doc['city_slug'] = city_slug
            update_needed = True
            
        if 'district' in address and 'district_slug' not in address:
            district_slug = normalize_turkish_slug(address['district'])
            update_doc['district_slug'] = district_slug
            update_needed = True
        
        if update_needed:
            await db.addresses.update_one(
                {'_id': address['_id']}, 
                {'$set': update_doc}
            )
            address_count += 1
            print(f"  Updated address: {address.get('label', 'Unknown')} -> {update_doc}")
    
    print(f"✅ Updated {address_count} address records")
    
    # 4. Verify migration
    print("\n🔍 Verifying migration...")
    
    # Check business
    business_total = await db.business.count_documents({})
    business_with_slugs = await db.business.count_documents({
        'address.city_slug': {'$exists': True},
        'address.district_slug': {'$exists': True}
    })
    
    # Check addresses
    address_total = await db.addresses.count_documents({})
    address_with_slugs = await db.addresses.count_documents({
        'city_slug': {'$exists': True},
        'district_slug': {'$exists': True}
    })
    
    print(f"📊 Business: {business_with_slugs}/{business_total} have slugs")
    print(f"📊 Addresses: {address_with_slugs}/{address_total} have slugs")
    
    if business_with_slugs == business_total and address_with_slugs == address_total:
        print("🎉 Migration completed successfully!")
    else:
        print("⚠️ Some records missing slug fields")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(run_migration())