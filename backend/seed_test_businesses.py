"""
Seed test businesses for city-strict testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

# Turkish slug normalization
def normalize_turkish_slug(text):
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

async def seed_businesses():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017/kuryecini")
    db = client.kuryecini
    
    print("🏢 Seeding test businesses...")
    
    # Test businesses for different cities
    businesses = [
        {
            "_id": str(uuid.uuid4()),
            "name": "İstanbul Kebab House",
            "description": "Authentic Turkish kebabs in Kadıköy",
            "category": "Turkish Cuisine",
            "address": {
                "full": "Kadıköy Moda Caddesi No:123, Kadıköy/İstanbul",
                "city": "İstanbul",
                "district": "Kadıköy",
                "city_slug": normalize_turkish_slug("İstanbul"),
                "district_slug": normalize_turkish_slug("Kadıköy")
            },
            "location": {
                "type": "Point", 
                "coordinates": [29.025, 40.99]  # Kadıköy coords
            },
            "is_active": True,
            "phone": "+905551234567",
            "email": "istanbul@kebabhouse.com"
        },
        {
            "_id": str(uuid.uuid4()),
            "name": "Beyoğlu Pizza",
            "description": "Italian pizzas in Beyoğlu district",
            "category": "Italian",
            "address": {
                "full": "İstiklal Caddesi No:456, Beyoğlu/İstanbul",
                "city": "İstanbul", 
                "district": "Beyoğlu",
                "city_slug": normalize_turkish_slug("İstanbul"),
                "district_slug": normalize_turkish_slug("Beyoğlu")
            },
            "location": {
                "type": "Point",
                "coordinates": [28.975, 41.036]  # Beyoğlu coords
            },
            "is_active": True,
            "phone": "+905551234568",
            "email": "beyoglu@pizza.com"
        },
        {
            "_id": str(uuid.uuid4()),
            "name": "Ankara Döner",
            "description": "Traditional döner in Çankaya",
            "category": "Turkish Cuisine",
            "address": {
                "full": "Kızılay Meydanı No:789, Çankaya/Ankara",
                "city": "Ankara",
                "district": "Çankaya", 
                "city_slug": normalize_turkish_slug("Ankara"),
                "district_slug": normalize_turkish_slug("Çankaya")
            },
            "location": {
                "type": "Point",
                "coordinates": [32.859, 39.925]  # Çankaya coords
            },
            "is_active": True,
            "phone": "+905551234569",
            "email": "ankara@doner.com"
        },
        {
            "_id": str(uuid.uuid4()),
            "name": "İzmir Balık",
            "description": "Fresh seafood in Konak",
            "category": "Seafood",
            "address": {
                "full": "Kordon Boyu No:321, Konak/İzmir",
                "city": "İzmir",
                "district": "Konak",
                "city_slug": normalize_turkish_slug("İzmir"),
                "district_slug": normalize_turkish_slug("Konak")
            },
            "location": {
                "type": "Point", 
                "coordinates": [27.129, 38.419]  # Konak coords
            },
            "is_active": True,
            "phone": "+905551234570",
            "email": "izmir@balik.com"
        }
    ]
    
    # Insert businesses
    for business in businesses:
        await db.business.replace_one(
            {"_id": business["_id"]},
            business,
            upsert=True
        )
        print(f"✅ Seeded: {business['name']} in {business['address']['city']}/{business['address']['district']}")
    
    # Add sample menu items
    print("\n🍽️ Seeding menu items...")
    
    menu_items = [
        # Istanbul Kebab House menu
        {
            "_id": str(uuid.uuid4()),
            "business_id": businesses[0]["_id"],
            "title": "Adana Kebab",
            "price": 45.0,
            "photo_url": "https://example.com/adana.jpg",
            "is_available": True,
            "category": "Kebabs"
        },
        {
            "_id": str(uuid.uuid4()), 
            "business_id": businesses[0]["_id"],
            "title": "Chicken Shish",
            "price": 38.0,
            "photo_url": "https://example.com/chicken.jpg",
            "is_available": True,
            "category": "Kebabs"
        },
        {
            "_id": str(uuid.uuid4()),
            "business_id": businesses[0]["_id"],
            "title": "Turkish Tea",
            "price": 5.0,
            "photo_url": "https://example.com/tea.jpg", 
            "is_available": True,
            "category": "Beverages"
        },
        # Beyoğlu Pizza menu
        {
            "_id": str(uuid.uuid4()),
            "business_id": businesses[1]["_id"],
            "title": "Margherita Pizza",
            "price": 32.0,
            "photo_url": "https://example.com/margherita.jpg",
            "is_available": True,
            "category": "Pizza"
        },
        {
            "_id": str(uuid.uuid4()),
            "business_id": businesses[1]["_id"],
            "title": "Pepperoni Pizza", 
            "price": 38.0,
            "photo_url": "https://example.com/pepperoni.jpg",
            "is_available": True,
            "category": "Pizza"
        },
        # Ankara Döner menu
        {
            "_id": str(uuid.uuid4()),
            "business_id": businesses[2]["_id"],
            "title": "Chicken Döner",
            "price": 25.0,
            "photo_url": "https://example.com/doner.jpg",
            "is_available": True,
            "category": "Döner"
        }
    ]
    
    for item in menu_items:
        await db.menu_items.replace_one(
            {"_id": item["_id"]},
            item,
            upsert=True
        )
        print(f"   Added menu item: {item['title']} - {item['price']}₺")
    
    print(f"\n🎉 Seeding completed! {len(businesses)} businesses and {len(menu_items)} menu items added.")
    
    # Verify city distribution
    cities = {}
    for business in businesses:
        city = business["address"]["city"]
        cities[city] = cities.get(city, 0) + 1
    
    print("\n📊 City distribution:")
    for city, count in cities.items():
        print(f"   {city}: {count} businesses")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_businesses())