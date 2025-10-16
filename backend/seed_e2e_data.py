"""
E2E Test Data Seeder
Seeds database with test users, business, products for E2E testing
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import bcrypt

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/kuryecini")

async def seed_database():
    """Seed E2E test data"""
    print("🌱 Starting E2E database seeding...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database()
    
    # Hash password helper
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    try:
        # ============================================
        # 1. SEED TEST USERS
        # ============================================
        print("\n📝 Seeding test users...")
        
        test_users = [
            {
                "_id": "admin-e2e-001",
                "id": "admin-e2e-001",
                "email": "admin@demo.com",
                "password": hash_password("Admin!234"),
                "name": "Admin User",
                "role": "admin",
                "phone": "+905001234567",
                "is_active": True,
                "is_verified": True,
                "kyc_status": "approved",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "business-e2e-001",
                "id": "business-e2e-001",
                "email": "business@demo.com",
                "password": hash_password("Biz!234"),
                "name": "Niğde Lezzet İşletme",
                "role": "business",
                "phone": "+905001234568",
                "is_active": True,
                "is_verified": True,
                "kyc_status": "approved",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "courier-e2e-001",
                "id": "courier-e2e-001",
                "email": "courier@demo.com",
                "password": hash_password("Kurye!234"),
                "name": "Ahmet Kurye",
                "role": "courier",
                "phone": "+905001234569",
                "is_active": True,
                "is_verified": True,
                "kyc_status": "approved",
                "vehicle_type": "motorbike",
                "vehicle_plate": "06 ABC 123",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "customer-e2e-001",
                "id": "customer-e2e-001",
                "email": "customer@demo.com",
                "password": hash_password("Musteri!234"),
                "name": "Ayşe Müşteri",
                "role": "customer",
                "phone": "+905001234570",
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        for user in test_users:
            await db.users.update_one(
                {"email": user["email"]},
                {"$set": user},
                upsert=True
            )
            print(f"  ✅ {user['role'].upper()}: {user['email']}")
        
        # ============================================
        # 2. SEED BUSINESS (Restaurant)
        # ============================================
        print("\n🏪 Seeding business/restaurant...")
        
        business = {
            "_id": "business-e2e-001",
            "id": "business-e2e-001",
            "owner_user_id": "business-e2e-001",
            "name": "Niğde Lezzet",
            "email": "business@demo.com",
            "phone": "+905001234568",
            "description": "Niğde'nin en lezzetli restoranı",
            "address": "Niğde Merkez, Bor Yolu No:123",
            "city": "Niğde",
            "city_normalized": "niğde",
            "district": "Merkez",
            "postal_code": "51100",
            "location": {
                "type": "Point",
                "coordinates": [34.68, 37.97]  # [longitude, latitude] for Niğde
            },
            "cuisine_type": "Türk Mutfağı",
            "rating": 4.5,
            "review_count": 42,
            "is_active": True,
            "is_approved": True,
            "kyc_status": "approved",
            "operating_hours": {
                "monday": {"open": "09:00", "close": "23:00"},
                "tuesday": {"open": "09:00", "close": "23:00"},
                "wednesday": {"open": "09:00", "close": "23:00"},
                "thursday": {"open": "09:00", "close": "23:00"},
                "friday": {"open": "09:00", "close": "23:00"},
                "saturday": {"open": "09:00", "close": "23:00"},
                "sunday": {"open": "09:00", "close": "23:00"}
            },
            "delivery_zones": ["Niğde Merkez", "Bor", "Altunhisar"],
            "min_order_amount": 30.0,
            "delivery_fee": 10.0,
            "average_delivery_time": 30,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.businesses.update_one(
            {"_id": business["_id"]},
            {"$set": business},
            upsert=True
        )
        print(f"  ✅ Business: {business['name']} (Niğde)")
        
        # ============================================
        # 3. SEED MENU ITEMS (Products)
        # ============================================
        print("\n🍽️  Seeding menu items...")
        
        menu_items = [
            {
                "_id": "product-e2e-001",
                "id": "product-e2e-001",
                "business_id": "business-e2e-001",
                "name": "Adana Kebap",
                "description": "Acılı kıyma kebap, lavaş ekmek, közlenmiş domates ve biber ile",
                "category": "Yemek",
                "price": 85.0,
                "currency": "TRY",
                "vat_rate": 0.10,
                "preparation_time": 20,
                "tags": ["kebap", "et", "acılı"],
                "image_url": "https://images.unsplash.com/photo-1529042410759-befb1204b468?w=400",
                "is_available": True,
                "in_stock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "product-e2e-002",
                "id": "product-e2e-002",
                "business_id": "business-e2e-001",
                "name": "Mantı",
                "description": "El açması mantı, yoğurt ve tereyağlı sos ile",
                "category": "Yemek",
                "price": 65.0,
                "currency": "TRY",
                "vat_rate": 0.10,
                "preparation_time": 25,
                "tags": ["mantı", "yoğurtlu", "hamur işi"],
                "image_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400",
                "is_available": True,
                "in_stock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "product-e2e-003",
                "id": "product-e2e-003",
                "business_id": "business-e2e-001",
                "name": "Lahmacun",
                "description": "İnce hamur, baharatlı kıyma ile",
                "category": "Yemek",
                "price": 25.0,
                "currency": "TRY",
                "vat_rate": 0.10,
                "preparation_time": 15,
                "tags": ["lahmacun", "hamur işi"],
                "image_url": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=400",
                "is_available": True,
                "in_stock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "product-e2e-004",
                "id": "product-e2e-004",
                "business_id": "business-e2e-001",
                "name": "Ayran",
                "description": "Soğuk, taze ayran",
                "category": "İçecek",
                "price": 8.0,
                "currency": "TRY",
                "vat_rate": 0.10,
                "preparation_time": 2,
                "tags": ["içecek", "soğuk"],
                "image_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=400",
                "is_available": True,
                "in_stock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": "product-e2e-005",
                "id": "product-e2e-005",
                "business_id": "business-e2e-001",
                "name": "Baklava",
                "description": "Antep fıstıklı, taze baklava",
                "category": "Atıştırmalık",
                "price": 45.0,
                "currency": "TRY",
                "vat_rate": 0.10,
                "preparation_time": 5,
                "tags": ["tatlı", "baklava", "fıstıklı"],
                "image_url": "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=400",
                "is_available": True,
                "in_stock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        for item in menu_items:
            # Insert to menu_items collection
            await db.menu_items.update_one(
                {"_id": item["_id"]},
                {"$set": item},
                upsert=True
            )
            # Also insert to products collection for backward compatibility
            await db.products.update_one(
                {"_id": item["_id"]},
                {"$set": item},
                upsert=True
            )
            print(f"  ✅ Product: {item['name']} - ₺{item['price']}")
        
        # ============================================
        # 4. SEED CUSTOMER ADDRESS
        # ============================================
        print("\n📍 Seeding customer address...")
        
        address = {
            "_id": "address-e2e-001",
            "id": "address-e2e-001",
            "user_id": "customer-e2e-001",
            "label": "Evim",
            "il": "Niğde",
            "ilce": "Merkez",
            "mahalle": "Yeni Mahalle",
            "sokak": "Atatürk Caddesi",
            "bina_no": "42",
            "kat": "3",
            "daire": "5",
            "full_address": "Yeni Mahalle, Atatürk Caddesi No:42 Kat:3 Daire:5, Merkez/Niğde",
            "lat": 37.97,
            "lng": 34.68,
            "location": {
                "type": "Point",
                "coordinates": [34.68, 37.97]  # [longitude, latitude]
            },
            "is_default": True,
            "phone": "+905001234570",
            "recipient_name": "Ayşe Müşteri",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.addresses.update_one(
            {"_id": address["_id"]},
            {"$set": address},
            upsert=True
        )
        print(f"  ✅ Address: {address['label']} - {address['il']}/{address['ilce']}")
        
        # ============================================
        # 5. CREATE INDEXES
        # ============================================
        print("\n🔍 Creating indexes...")
        
        # 2dsphere indexes for geospatial queries
        await db.businesses.create_index([("location", "2dsphere")])
        await db.addresses.create_index([("location", "2dsphere")])
        print("  ✅ Created 2dsphere indexes")
        
        # Other useful indexes
        await db.users.create_index("email", unique=True)
        await db.orders.create_index("customer_id")
        await db.orders.create_index("business_id")
        await db.orders.create_index("status")
        await db.menu_items.create_index("business_id")
        print("  ✅ Created additional indexes")
        
        print("\n✅ E2E database seeding completed successfully!")
        print("\n📋 TEST CREDENTIALS:")
        print("=" * 50)
        print("Admin:     admin@demo.com / Admin!234")
        print("Business:  business@demo.com / Biz!234")
        print("Courier:   courier@demo.com / Kurye!234")
        print("Customer:  customer@demo.com / Musteri!234")
        print("=" * 50)
        print("\n📍 Test Restaurant: Niğde Lezzet (Niğde)")
        print("📦 Menu Items: 5 products (Kebap, Mantı, Lahmacun, Ayran, Baklava)")
        print("🏠 Customer Address: Niğde Merkez")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

async def reset_dev_database():
    """Reset development database - DANGEROUS! Only for dev"""
    print("⚠️  WARNING: This will DELETE ALL DATA in development database!")
    response = input("Type 'RESET' to confirm: ")
    
    if response != "RESET":
        print("❌ Reset cancelled")
        return
    
    print("\n🗑️  Resetting development database...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database()
    
    try:
        # Drop collections
        collections = ["users", "businesses", "menu_items", "products", "addresses", "orders"]
        for collection in collections:
            await db[collection].drop()
            print(f"  ✅ Dropped collection: {collection}")
        
        print("\n✅ Database reset completed!")
        print("💡 Run seed command to create test data")
        
    except Exception as e:
        print(f"\n❌ Error during reset: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        asyncio.run(reset_dev_database())
    else:
        asyncio.run(seed_database())
