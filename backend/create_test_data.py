#!/usr/bin/env python3
"""
Create test data for Kuryecini Customer App
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def create_test_data():
    """Create test data for the Customer App"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/kuryecini_database')
    client = AsyncIOMotorClient(mongo_uri)
    
    if "/kuryecini_database" in mongo_uri:
        db = client.kuryecini_database
    else:
        try:
            db_name = mongo_uri.split("/")[-1].split("?")[0]
            db = client[db_name] if db_name else client.kuryecini_database
        except:
            db = client.kuryecini_database
    
    print(f"Creating test data for database: {db.name}")
    
    try:
        # 1. Create test businesses with proper geolocation
        print("Creating test businesses...")
        
        businesses = [
            {
                "id": str(uuid.uuid4()),
                "business_name": "Test Restoranı",
                "business_category": "gida",
                "description": "Geleneksel Türk mutfağı",
                "address": "Kadıköy, İstanbul",
                "city": "İstanbul",
                "city_normalized": "istanbul",
                "email": "test@testrestaurant.com",
                "kyc_status": "approved",
                "is_active": True,
                "rating": 4.8,
                "delivery_time": "25-35 dk",
                "min_order_amount": 50.0,
                "location": {
                    "type": "Point",
                    "coordinates": [29.0281, 41.0058]  # Kadıköy coordinates [lng, lat]
                },
                "logo_url": "",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_name": "Pizza Palace İstanbul",
                "business_category": "gida",
                "description": "İtalyan mutfağı ve pizzalar",
                "address": "Beyoğlu, İstanbul",
                "city": "İstanbul",
                "city_normalized": "istanbul",
                "email": "info@pizzapalace.com",
                "kyc_status": "approved",
                "is_active": True,
                "rating": 4.6,
                "delivery_time": "20-30 dk",
                "min_order_amount": 60.0,
                "location": {
                    "type": "Point",
                    "coordinates": [28.9850, 41.0369]  # Beyoğlu coordinates [lng, lat]
                },
                "logo_url": "",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_name": "Burger Deluxe",
                "business_category": "gida", 
                "description": "Gourmet burgerler ve fast food",
                "address": "Şişli, İstanbul",
                "city": "İstanbul",
                "city_normalized": "istanbul",
                "email": "orders@burgerdeluxe.com",
                "kyc_status": "approved",
                "is_active": True,
                "rating": 4.9,
                "delivery_time": "15-25 dk",
                "min_order_amount": 45.0,
                "location": {
                    "type": "Point",
                    "coordinates": [28.9662, 41.0498]  # Şişli coordinates [lng, lat]
                },
                "logo_url": "",
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        # Clear existing businesses
        await db.businesses.delete_many({"kyc_status": "approved"})
        
        # Insert new businesses
        await db.businesses.insert_many(businesses)
        print(f"✅ Created {len(businesses)} test businesses")
        
        # 2. Create products for each business
        print("Creating test products...")
        
        test_products = []
        
        # Products for Test Restoranı
        business_1_products = [
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[0]["id"],
                "business_name": businesses[0]["business_name"],
                "name": "Döner Kebap",
                "description": "Geleneksel döner kebap, lavash ekmek içinde",
                "price": 35.50,
                "category": "Ana Yemek",
                "preparation_time_minutes": 15,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[0]["id"],
                "business_name": businesses[0]["business_name"],
                "name": "Adana Kebap",
                "description": "Acılı kıyma kebap, pilav ve salata ile",
                "price": 48.00,
                "category": "Ana Yemek",
                "preparation_time_minutes": 20,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[0]["id"],
                "business_name": businesses[0]["business_name"],
                "name": "Künefe",
                "description": "Taze peynirli künefe, şerbet ve fıstık ile",
                "price": 28.00,
                "category": "Tatlı",
                "preparation_time_minutes": 10,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[0]["id"],
                "business_name": businesses[0]["business_name"],
                "name": "Ayran",
                "description": "Taze ayran",
                "price": 8.00,
                "category": "İçecek",
                "preparation_time_minutes": 2,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        # Products for Pizza Palace
        business_2_products = [
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[1]["id"],
                "business_name": businesses[1]["business_name"],
                "name": "Margherita Pizza",
                "description": "Klasik margherita pizza, domates sosu ve mozzarella",
                "price": 65.00,
                "category": "Pizza",
                "preparation_time_minutes": 18,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[1]["id"],
                "business_name": businesses[1]["business_name"],
                "name": "Pepperoni Pizza",
                "description": "Pepperoni sosisli pizza",
                "price": 72.00,
                "category": "Pizza",
                "preparation_time_minutes": 18,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[1]["id"],
                "business_name": businesses[1]["business_name"],
                "name": "Sezar Salata",
                "description": "Taze marul, parmesan peyniri ve kruton",
                "price": 35.00,
                "category": "Salata",
                "preparation_time_minutes": 8,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[1]["id"],
                "business_name": businesses[1]["business_name"],
                "name": "Coca Cola",
                "description": "330ml kutu kola",
                "price": 12.00,
                "category": "İçecek",
                "preparation_time_minutes": 1,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        # Products for Burger Deluxe
        business_3_products = [
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[2]["id"],
                "business_name": businesses[2]["business_name"],
                "name": "Cheeseburger",
                "description": "Sığır eti burger, cheddar peyniri ve sebzeler",
                "price": 45.00,
                "category": "Burger",
                "preparation_time_minutes": 12,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[2]["id"],
                "business_name": businesses[2]["business_name"],
                "name": "Chicken Burger",
                "description": "Izgara tavuk göğsü burger",
                "price": 42.00,
                "category": "Burger",
                "preparation_time_minutes": 12,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[2]["id"],
                "business_name": businesses[2]["business_name"],
                "name": "Patates Kızartması",
                "description": "Çıtır patates kızartması",
                "price": 18.00,
                "category": "Yan Ürün",
                "preparation_time_minutes": 8,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "business_id": businesses[2]["id"],
                "business_name": businesses[2]["business_name"],
                "name": "Milkshake",
                "description": "Vanilyalı milkshake",
                "price": 22.00,
                "category": "İçecek",
                "preparation_time_minutes": 5,
                "image_url": "",
                "is_available": True,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        all_products = business_1_products + business_2_products + business_3_products
        
        # Clear existing products and insert new ones
        business_ids = [b["id"] for b in businesses]
        await db.products.delete_many({"business_id": {"$in": business_ids}})
        await db.products.insert_many(all_products)
        
        print(f"✅ Created {len(all_products)} test products")
        
        # 3. Create some test addresses for customer
        print("Creating test addresses...")
        
        test_addresses = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "customer-001",  # Test customer ID
                "label": "Ev",
                "description": "Kadıköy Moda Caddesi No:15",
                "city": "İstanbul",
                "lat": 41.0058,
                "lng": 29.0281,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "customer-001",
                "label": "İş",
                "description": "Beşiktaş Barbaros Bulvarı No:85",
                "city": "İstanbul",
                "lat": 41.0766,
                "lng": 28.9688,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        await db.user_addresses.delete_many({"user_id": "customer-001"})
        await db.user_addresses.insert_many(test_addresses)
        
        print(f"✅ Created {len(test_addresses)} test addresses")
        
        print("\n🎉 Test data created successfully!")
        
        # Print summary
        business_count = await db.businesses.count_documents({"kyc_status": "approved"})
        product_count = await db.products.count_documents({"is_available": True})
        address_count = await db.user_addresses.count_documents({"user_id": "customer-001"})
        
        print(f"""
📊 Test Data Summary:
   • Businesses: {business_count}
   • Products: {product_count}  
   • Test Addresses: {address_count}
   
🏪 Test Businesses:
   • Test Restoranı (Kadıköy) - 4 products
   • Pizza Palace İstanbul (Beyoğlu) - 4 products  
   • Burger Deluxe (Şişli) - 4 products
   
👤 Test Login:
   • Email: testcustomer@example.com
   • Password: test123
        """)
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_data())