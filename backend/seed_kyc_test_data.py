"""
Seed test users with pending KYC for testing Admin KYC panel
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import bcrypt

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/kuryecini")

async def seed_kyc_test_data():
    """Seed KYC test data"""
    print("🌱 Starting KYC test data seeding...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database()
    
    # Hash password helper
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    try:
        # Create test users with pending KYC
        test_users = [
            {
                "id": "test-courier-kyc-001",
                "_id": "test-courier-kyc-001",
                "email": "test.courier@kyc.com",
                "password": hash_password("test123"),
                "name": "Mehmet Kurye Test",
                "role": "courier",
                "phone": "+905551234567",
                "city": "Ankara",
                "district": "Çankaya",
                "neighborhood": "Kızılay Mahallesi",
                "vehicle_type": "motorbike",
                "is_active": True,
                "is_verified": False,
                "kyc_status": "pending",
                "kyc_documents": [
                    {
                        "type": "license",
                        "filename": "ehliyet_mehmet.jpg",
                        "path": "/uploads/kyc/license_sample.jpg"
                    },
                    {
                        "type": "id_card",
                        "filename": "kimlik_mehmet.jpg",
                        "path": "/uploads/kyc/id_card_sample.jpg"
                    },
                    {
                        "type": "vehicle_registration",
                        "filename": "ruhsat_mehmet.jpg",
                        "path": "/uploads/kyc/vehicle_reg_sample.jpg"
                    }
                ],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": "test-business-kyc-001",
                "_id": "test-business-kyc-001",
                "email": "test.business@kyc.com",
                "password": hash_password("test123"),
                "name": "Fatma İşletme Sahibi",
                "business_name": "Test Lokantası",
                "business_tax_id": "1234567890",
                "role": "business",
                "phone": "+905559876543",
                "city": "İstanbul",
                "district": "Kadıköy",
                "neighborhood": "Moda Mahallesi",
                "is_active": True,
                "is_verified": False,
                "kyc_status": "pending",
                "kyc_documents": [
                    {
                        "type": "id_card",
                        "filename": "kimlik_fatma.jpg",
                        "path": "/uploads/kyc/id_card_sample.jpg"
                    },
                    {
                        "type": "business_photo",
                        "filename": "isletme_foto.jpg",
                        "path": "/uploads/kyc/business_photo_sample.jpg"
                    }
                ],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "id": "test-courier-kyc-002",
                "_id": "test-courier-kyc-002",
                "email": "test.courier2@kyc.com",
                "password": hash_password("test123"),
                "name": "Ali Bisiklet Kurye",
                "role": "courier",
                "phone": "+905551122334",
                "city": "İzmir",
                "district": "Konak",
                "neighborhood": "Alsancak Mahallesi",
                "vehicle_type": "bicycle",
                "is_active": True,
                "is_verified": False,
                "kyc_status": "pending",
                "kyc_documents": [
                    {
                        "type": "id_card",
                        "filename": "kimlik_ali.jpg",
                        "path": "/uploads/kyc/id_card_sample.jpg"
                    }
                ],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        for user in test_users:
            result = await db.users.update_one(
                {"$or": [{"id": user["id"]}, {"email": user["email"]}]},
                {"$set": user},
                upsert=True
            )
            if result.upserted_id:
                print(f"✅ Created user: {user['email']} ({user['role']})")
            else:
                print(f"🔄 Updated user: {user['email']} ({user['role']})")
        
        print("\n✅ KYC test data seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error seeding KYC test data: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_kyc_test_data())
