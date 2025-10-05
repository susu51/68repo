"""
Database Initialization and Index Setup
Real MongoDB Implementation - No Mock Data
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from models import INDEXES, GlobalSettings

async def init_database():
    """Initialize MongoDB database with proper collections and indexes"""
    
    # Get MongoDB connection
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kuryecini')
    client = AsyncIOMotorClient(mongo_url)
    
    # Extract database name from URL
    db_name = mongo_url.split('/')[-1] or 'kuryecini'
    db = client[db_name]
    
    print(f"🔗 Initializing database: {db_name}")
    
    try:
        # Create indexes for all collections
        for collection_name, indexes in INDEXES.items():
            collection = db[collection_name]
            
            print(f"📊 Setting up indexes for {collection_name}...")
            
            for index_spec in indexes:
                try:
                    if isinstance(index_spec, dict):
                        # Handle compound indexes and options
                        if len(index_spec) == 1:
                            field_name = list(index_spec.keys())[0]
                            index_type = list(index_spec.values())[0]
                            
                            if index_type == "2dsphere":
                                await collection.create_index([(field_name, "2dsphere")])
                                print(f"  ✅ Created 2dsphere index on {field_name}")
                            elif index_type == 1:
                                await collection.create_index([(field_name, 1)])
                                print(f"  ✅ Created ascending index on {field_name}")
                            elif index_type == -1:
                                await collection.create_index([(field_name, -1)])
                                print(f"  ✅ Created descending index on {field_name}")
                        else:
                            # Compound index
                            index_list = [(k, v) for k, v in index_spec.items()]
                            await collection.create_index(index_list)
                            print(f"  ✅ Created compound index: {index_spec}")
                            
                except Exception as e:
                    print(f"  ⚠️  Index creation warning for {collection_name}: {e}")
        
        # Initialize global settings if not exists
        settings_collection = db.settings
        existing_settings = await settings_collection.find_one({"_id": "global"})
        
        if not existing_settings:
            default_settings = {
                "_id": "global",
                "courier_rate_per_package": float(os.getenv('COURIER_RATE_PER_PACKAGE', 20)),
                "business_commission_pct": float(os.getenv('BUSINESS_COMMISSION_PCT', 5)),
                "nearby_radius_m": int(os.getenv('NEARBY_RADIUS_M', 5000)),
                "courier_update_sec": int(os.getenv('COURIER_UPDATE_SEC', 5)),
                "courier_timeout_sec": int(os.getenv('COURIER_TIMEOUT_SEC', 10)),
                "updated_at": datetime.utcnow(),
                "updated_by": "system_init"
            }
            
            await settings_collection.insert_one(default_settings)
            print("⚙️  Initialized global settings")
        else:
            print("⚙️  Global settings already exist")
        
        print("✅ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    finally:
        client.close()

async def get_database():
    """Get database connection for application use"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kuryecini')
    client = AsyncIOMotorClient(mongo_url)
    db_name = mongo_url.split('/')[-1] or 'kuryecini'
    return client[db_name]

async def health_check():
    """Database health check"""
    try:
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kuryecini')
        client = AsyncIOMotorClient(mongo_url)
        
        # Test connection
        await client.admin.command('ping')
        
        db_name = mongo_url.split('/')[-1] or 'kuryecini'
        db = client[db_name]
        
        # Check settings collection
        settings = await db.settings.find_one({"_id": "global"})
        
        client.close()
        
        return {
            "database": "connected",
            "settings": "initialized" if settings else "missing",
            "collections": ["businesses", "menu_items", "orders", "courier_locations", "earnings", "settings"]
        }
    except Exception as e:
        return {
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    # Run initialization
    asyncio.run(init_database())