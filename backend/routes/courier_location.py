"""
Phase 3: Courier Location System with Real-time Tracking
Kurye Konum Sistemi - POST /courier/location
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import json
import uuid
from auth_dependencies import get_courier_user

router = APIRouter(prefix="/courier", tags=["courier-location"])

class CourierLocationUpdate(BaseModel):
    lat: float
    lng: float
    heading: Optional[float] = None       # Yön (derece)
    speed: Optional[float] = None         # Hız (km/h)
    accuracy: Optional[float] = None      # GPS doğruluğu (metre)
    ts: Optional[datetime] = None         # Zaman damgası

class CourierLocationResponse(BaseModel):
    courier_id: str
    lat: float
    lng: float
    heading: Optional[float]
    speed: Optional[float] 
    accuracy: Optional[float]
    timestamp: datetime
    cached: bool
    
class CourierLocationHistory(BaseModel):
    courier_id: str
    locations: List[dict]
    total_count: int

@router.post("/location", response_model=CourierLocationResponse)
async def update_courier_location(
    location_data: CourierLocationUpdate,
    current_user: dict = Depends(get_courier_user)
):
    """
    Update courier location
    Periyot: 5 sn, timeout: 10 sn, enableHighAccuracy=true
    
    Depolama:
    - Son konum: cache (Redis varsa) courier:loc:{courier_id}
    - Geçmiş: courier_locations (son 100 nokta, ts index)
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        timestamp = location_data.ts or datetime.now(timezone.utc)
        
        # Prepare location data
        location_doc = {
            "_id": str(uuid.uuid4()),
            "courier_id": courier_id,
            "location": {
                "type": "Point",
                "coordinates": [location_data.lng, location_data.lat]  # GeoJSON format [lng, lat]
            },
            "lat": location_data.lat,
            "lng": location_data.lng,
            "heading": location_data.heading,
            "speed": location_data.speed,
            "accuracy": location_data.accuracy,
            "timestamp": timestamp
        }
        
        cached = False
        
        # Try Redis cache first (if available)
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=1)
            
            # Test Redis connection
            r.ping()
            
            # Cache latest location (expire in 10 minutes)
            cache_key = f"courier:loc:{courier_id}"
            cache_data = {
                "courier_id": courier_id,
                "lat": location_data.lat,
                "lng": location_data.lng,
                "heading": location_data.heading,
                "speed": location_data.speed,
                "accuracy": location_data.accuracy,
                "timestamp": timestamp.isoformat()
            }
            
            r.setex(cache_key, 600, json.dumps(cache_data))  # 10 minutes TTL
            cached = True
            
            print(f"📍 COURIER LOCATION CACHED: {courier_id} at ({location_data.lat}, {location_data.lng})")
            
        except Exception as redis_error:
            print(f"⚠️ Redis cache failed: {redis_error}")
            # Continue without Redis caching
        
        # Store in MongoDB history (keep last 100 locations)
        await db.courier_locations.insert_one(location_doc)
        
        # Maintain only last 100 locations per courier
        try:
            # Count total locations for this courier
            total_count = await db.courier_locations.count_documents({"courier_id": courier_id})
            
            if total_count > 100:
                # Remove oldest locations (keep most recent 100)
                oldest_locations = await db.courier_locations.find(
                    {"courier_id": courier_id}
                ).sort("timestamp", 1).limit(total_count - 100).to_list(length=None)
                
                if oldest_locations:
                    oldest_ids = [loc["_id"] for loc in oldest_locations]
                    await db.courier_locations.delete_many({"_id": {"$in": oldest_ids}})
                    print(f"🗑️ Cleaned up {len(oldest_ids)} old locations for courier {courier_id}")
                    
        except Exception as cleanup_error:
            print(f"⚠️ Location cleanup failed: {cleanup_error}")
            # Continue without cleanup
        
        print(f"📍 COURIER LOCATION UPDATED: {courier_id} at ({location_data.lat}, {location_data.lng}) | Accuracy: {location_data.accuracy}m")
        
        # TODO: WebSocket broadcast for real-time updates
        # This will be implemented in the WebSocket module
        
        return CourierLocationResponse(
            courier_id=courier_id,
            lat=location_data.lat,
            lng=location_data.lng,
            heading=location_data.heading,
            speed=location_data.speed,
            accuracy=location_data.accuracy,
            timestamp=timestamp,
            cached=cached
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating courier location: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating location: {str(e)}"
        )

@router.get("/location/{courier_id}")
async def get_courier_location(
    courier_id: str,
    current_user: dict = Depends(get_courier_user)  # Any authenticated user can read
):
    """
    Get current courier location (from cache or database)
    """
    try:
        from server import db
        
        location_data = None
        cached = False
        
        # Try Redis cache first
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=1)
            
            cache_key = f"courier:loc:{courier_id}"
            cached_location = r.get(cache_key)
            
            if cached_location:
                location_data = json.loads(cached_location)
                cached = True
                print(f"📍 COURIER LOCATION FROM CACHE: {courier_id}")
                
        except Exception as redis_error:
            print(f"⚠️ Redis read failed: {redis_error}")
        
        # Fallback to MongoDB if not cached
        if not location_data:
            latest_location = await db.courier_locations.find_one(
                {"courier_id": courier_id},
                sort=[("timestamp", -1)]
            )
            
            if latest_location:
                location_data = {
                    "courier_id": latest_location["courier_id"],
                    "lat": latest_location["lat"],
                    "lng": latest_location["lng"],
                    "heading": latest_location.get("heading"),
                    "speed": latest_location.get("speed"),
                    "accuracy": latest_location.get("accuracy"),
                    "timestamp": latest_location["timestamp"].isoformat()
                }
                print(f"📍 COURIER LOCATION FROM DB: {courier_id}")
        
        if not location_data:
            raise HTTPException(
                status_code=404,
                detail="No location data found for this courier"
            )
        
        # Parse timestamp
        if isinstance(location_data["timestamp"], str):
            timestamp = datetime.fromisoformat(location_data["timestamp"].replace('Z', '+00:00'))
        else:
            timestamp = location_data["timestamp"]
        
        return CourierLocationResponse(
            courier_id=location_data["courier_id"],
            lat=location_data["lat"],
            lng=location_data["lng"],
            heading=location_data.get("heading"),
            speed=location_data.get("speed"),
            accuracy=location_data.get("accuracy"),
            timestamp=timestamp,
            cached=cached
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching courier location: {str(e)}"
        )

@router.get("/location/{courier_id}/history", response_model=CourierLocationHistory)
async def get_courier_location_history(
    courier_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_courier_user)
):
    """
    Get courier location history (last N points)
    """
    try:
        from server import db
        
        # Get location history (most recent first)
        locations = await db.courier_locations.find(
            {"courier_id": courier_id}
        ).sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        # Convert to simple dict format
        location_list = []
        for loc in locations:
            location_list.append({
                "lat": loc["lat"],
                "lng": loc["lng"],
                "heading": loc.get("heading"),
                "speed": loc.get("speed"),
                "accuracy": loc.get("accuracy"),
                "timestamp": loc["timestamp"].isoformat()
            })
        
        total_count = await db.courier_locations.count_documents({"courier_id": courier_id})
        
        return CourierLocationHistory(
            courier_id=courier_id,
            locations=location_list,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching location history: {str(e)}"
        )