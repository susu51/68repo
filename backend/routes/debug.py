"""
Debug Routes - Atlas TLS/DB Test
Geçici debug endpoint'i Atlas bağlantısı test için
"""
from fastapi import APIRouter, HTTPException, Depends
from auth_dependencies import get_admin_user
from datetime import datetime, timezone

router = APIRouter(prefix="/__debug", tags=["debug"])

@router.get("/db-ping")
async def db_ping():
    """
    Atlas ping test - admin koruması olmadan kolay test için
    Production'da silinebilir veya admin koruması eklenebilir
    """
    try:
        from server import db, client
        
        print("🔍 Testing MongoDB Atlas connection...")
        
        # Atlas ping test
        ping_result = await db.command("ping")
        print(f"✅ MongoDB ping successful: {ping_result}")
        
        # Database stats
        db_stats = await db.command("dbStats")
        db_name = db_stats.get("db", "unknown")
        
        # Collection count
        collections = await db.list_collection_names()
        
        # Test a simple operation
        test_doc = {
            "_id": f"test_{int(datetime.now().timestamp())}",
            "test": True,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Insert and delete test
        insert_result = await db.debug_test.insert_one(test_doc)
        await db.debug_test.delete_one({"_id": test_doc["_id"]})
        
        return {
            "ok": True,
            "db": db_name,
            "ping": ping_result,
            "collections": len(collections),
            "collection_names": collections,
            "test_insert_id": str(insert_result.inserted_id),
            "atlas_connection": "SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Atlas ping failed: {e}")
        return {
            "ok": False,
            "error": str(e),
            "atlas_connection": "FAILED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/db-ping-admin")
async def db_ping_admin(current_user: dict = Depends(get_admin_user)):
    """Admin korumalı versiyon"""
    return await db_ping()

@router.get("/connection-info") 
async def connection_info():
    """Connection bilgileri - Atlas vs Local detection"""
    try:
        import os
        mongo_url = os.getenv('MONGO_URL', 'Not set')
        
        is_atlas = 'mongodb+srv://' in mongo_url or 'mongodb.net' in mongo_url
        is_local = 'localhost' in mongo_url or '127.0.0.1' in mongo_url
        
        return {
            "connection_type": "Atlas" if is_atlas else "Local" if is_local else "Unknown",
            "is_atlas": is_atlas,
            "is_local": is_local,
            "url_preview": mongo_url[:50] + "...[HIDDEN]" if len(mongo_url) > 50 else mongo_url,
            "ssl_required": is_atlas
        }
        
    except Exception as e:
        return {"error": str(e)}