"""
Stable Restaurant Discovery - Emergency Rollback
GET /restaurants with legacy stable projection
"""
from fastapi import APIRouter, Query
from typing import Optional
from math import radians, cos, sin, asin, sqrt

router = APIRouter(prefix="/restaurants", tags=["stable-discovery"])

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance in meters between two coordinates"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000  # Radius of earth in meters
    return c * r

@router.get("")
async def get_restaurants_stable(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Stable restaurant discovery endpoint
    Returns only open restaurants with essential fields
    """
    from server import db
    
    try:
        # Build query - only open restaurants
        query = {"is_open": True}
        
        # Text search if provided
        if q:
            query["$or"] = [
                {"name": {"$regex": q, "$options": "i"}},
                {"cuisine": {"$regex": q, "$options": "i"}}
            ]
        
        # Stable projection - only essential fields
        projection = {
            "_id": 1,
            "name": 1,
            "logo": 1,
            "cuisine": 1,
            "latitude": 1,
            "longitude": 1,
            "estimated_delivery_time": 1,
            "average_rating": 1,
            "min_order_amount": 1,
            "delivery_fee": 1,
            "is_open": 1,
            "address": 1
        }
        
        # Fetch restaurants
        restaurants = await db.businesses.find(query, projection).to_list(length=None)
        
        print(f"🔍 Found {len(restaurants)} open restaurants in DB")
        
        # Calculate distance if coords provided
        if lat is not None and lng is not None:
            for resto in restaurants:
                resto_lat = resto.get("latitude", 0)
                resto_lng = resto.get("longitude", 0)
                
                if resto_lat and resto_lng:
                    distance = haversine(lng, lat, resto_lng, resto_lat)
                    resto["distance_m"] = int(distance)
                else:
                    resto["distance_m"] = 999999
            
            # Sort by distance
            restaurants.sort(key=lambda x: x.get("distance_m", 999999))
            
            # Filter by max distance (6km)
            restaurants = [r for r in restaurants if r.get("distance_m", 999999) <= 6000]
        else:
            # No coords - sort by rating
            restaurants.sort(key=lambda x: x.get("average_rating", 0), reverse=True)
        
        # Pagination
        total = len(restaurants)
        restaurants = restaurants[skip:skip+limit]
        
        # Format response
        result = []
        for resto in restaurants:
            result.append({
                "id": resto.get("_id"),
                "name": resto.get("name", ""),
                "logo": resto.get("logo", ""),
                "cuisine": resto.get("cuisine", ""),
                "coords": {
                    "lat": resto.get("latitude", 0),
                    "lng": resto.get("longitude", 0)
                },
                "eta": resto.get("estimated_delivery_time", 30),
                "avg_rating": resto.get("average_rating", 0),
                "min_order": resto.get("min_order_amount", 0),
                "delivery_fee": resto.get("delivery_fee", 0),
                "is_open": resto.get("is_open", False),
                "distance_m": resto.get("distance_m")
            })
        
        print(f"✅ Returning {len(result)} restaurants (total: {total})")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in stable restaurant discovery: {e}")
        import traceback
        traceback.print_exc()
        # Return empty array on error - don't break the app
        return []
