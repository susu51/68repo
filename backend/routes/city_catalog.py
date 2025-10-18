"""
City-Strict Catalog - ONLY same city businesses allowed
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import os

# Get environment variables
# Customer requirement: 70km max radius, 10km priority zone
NEARBY_RADIUS_M = int(os.environ.get('NEARBY_RADIUS_M', '70000'))  # 70km max
PRIORITY_RADIUS_M = int(os.environ.get('PRIORITY_RADIUS_M', '10000'))  # 10km priority

router = APIRouter(prefix="/catalog", tags=["catalog"])

# Global database client
db = None

def set_db_client(database):
    global db
    db = database

class MenuSnippet(BaseModel):
    title: str
    price: float
    photo_url: Optional[str] = None

class BusinessNearby(BaseModel):
    id: str
    name: str
    address: dict
    distance: float  # in meters
    menu_snippet: List[MenuSnippet]

@router.get("/city-nearby", response_model=List[BusinessNearby])
async def get_city_nearby_businesses(
    lat: Optional[float] = Query(None, description="Latitude (required for GPS search)"),
    lng: Optional[float] = Query(None, description="Longitude (required for GPS search)"),
    city: Optional[str] = Query(None, description="City slug (optional - for filtering by city)"),
    district: Optional[str] = Query(None, description="District slug (optional)"),
    radius_km: int = Query(50, description="Search radius in kilometers (default: 50km)"),
    limit: int = Query(30, le=100, description="Max results")
):
    """
    Get nearby businesses based on GPS coordinates
    - If city provided: returns businesses only in that city (city-strict search)
    - If city NOT provided: returns businesses nationwide within radius (GPS-only search)
    - Dynamic radius based on GPS availability
    """
    
    # Validate GPS coordinates
    if lat is None or lng is None:
        raise HTTPException(
            status_code=422,
            detail="lat and lng are required for GPS-based search"
        )
    
    # Convert radius_km to meters
    radius_m = radius_km * 1000
    max_radius_m = min(radius_m, NEARBY_RADIUS_M)  # Cap at 70km max
    
    has_city_filter = city is not None
    print(f"🎯 GPS search: lat={lat}, lng={lng}, city={city}, district={district}, radius={radius_km}km, city_filter={has_city_filter}")
    
    try:
        # Build query based on city filter
        base_query = {"is_active": True}
        if has_city_filter:
            base_query["address.city_slug"] = city  # City-strict filter
            print(f"   🏙️ City filter active: {city}")
        else:
            print(f"   🌍 Nationwide GPS search (no city filter)")
        
        # GPS-based search with distance sorting
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "spherical": True,
                    "distanceField": "dist",
                    "maxDistance": max_radius_m,
                    "query": base_query
                }
            },
                {
                    "$addFields": {
                        "district_match": (
                            {"$eq": ["$address.district_slug", district]} if district 
                            else {"$literal": False}
                        ),
                        "is_priority_zone": {
                            "$lte": ["$dist", PRIORITY_RADIUS_M]  # Within 10km priority zone
                        }
                    }
                },
                {
                    "$sort": {
                        "is_priority_zone": -1,  # Priority zone first
                        "district_match": -1,     # Then same district
                        "dist": 1                 # Finally by distance
                    }
                },
                {
                    "$lookup": {
                        "from": "menu_items", 
                        "let": {"bid": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$business_id", "$$bid"]},
                                    "is_available": True
                                }
                            },
                            {"$project": {"title": 1, "price": 1, "photo_url": 1}},
                            {"$limit": 3}
                        ],
                        "as": "menu_snippet"
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "address": 1,
                        "dist": 1,
                        "menu_snippet": 1
                    }
                },
                {"$limit": limit}
            ]
        else:
            # City/district-based search without GPS (no distance sorting)
            match_query = {
                "is_active": True,
                "address.city_slug": city
            }
            
            if district:
                match_query["address.district_slug"] = district
            
            pipeline = [
                {"$match": match_query},
                {
                    "$addFields": {
                        "district_match": (
                            {"$eq": ["$address.district_slug", district]} if district 
                            else {"$literal": False}
                        ),
                        "dist": 0  # No GPS, so distance is 0
                    }
                },
                {
                    "$sort": {
                        "district_match": -1,  # Same district first
                        "name": 1              # Then by name
                    }
                },
                {
                    "$lookup": {
                        "from": "menu_items", 
                        "let": {"bid": "$_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$eq": ["$business_id", "$$bid"]},
                                    "is_available": True
                                }
                            },
                            {"$project": {"title": 1, "price": 1, "photo_url": 1}},
                            {"$limit": 3}
                        ],
                        "as": "menu_snippet"
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "address": 1,
                        "dist": 1,
                        "menu_snippet": 1
                    }
                },
                {"$limit": limit}
            ]
        
        # Execute aggregation
        results = await db.business.aggregate(pipeline).to_list(length=None)
        
        # CRITICAL SECURITY CHECK: Verify no cross-city data
        for business in results:
            business_city = business.get("address", {}).get("city_slug")
            if business_city != city:
                error_msg = f"SECURITY VIOLATION: Cross-city data detected! Expected: {city}, Found: {business_city}"
                print(f"🚨 {error_msg}")
                raise HTTPException(status_code=500, detail="City filter violation detected")
        
        print(f"✅ Found {len(results)} businesses in {city}, all city-validated")
        
        # Format response
        businesses = []
        for business in results:
            businesses.append(BusinessNearby(
                id=business["_id"],
                name=business["name"],
                address=business["address"], 
                distance=business["dist"],
                menu_snippet=[
                    MenuSnippet(
                        title=item["title"],
                        price=item["price"],
                        photo_url=item.get("photo_url")
                    )
                    for item in business.get("menu_snippet", [])
                ]
            ))
        
        return businesses
        
    except Exception as e:
        print(f"❌ City-nearby error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving nearby businesses: {str(e)}"
        )