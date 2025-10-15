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
    lat: float = Query(..., description="Latitude (required)"),
    lng: float = Query(..., description="Longitude (required)"), 
    city: str = Query(..., description="City slug (required)"),
    district: Optional[str] = Query(None, description="District slug (optional)"),
    limit: int = Query(30, le=100, description="Max results")
):
    """
    Get nearby businesses in SAME CITY ONLY
    CRITICAL: Cross-city results are FORBIDDEN
    """
    
    # Validate required parameters
    if lat is None or lng is None or not city:
        raise HTTPException(
            status_code=422,
            detail="lat, lng, and city are required parameters"
        )
    
    print(f"🎯 City-strict search: city={city}, district={district}, radius={NEARBY_RADIUS_M}m")
    
    try:
        # MongoDB aggregation pipeline
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "spherical": True,
                    "distanceField": "dist",
                    "maxDistance": NEARBY_RADIUS_M,
                    "query": {
                        "is_active": True,
                        "address.city_slug": city  # CRITICAL: City filter
                    }
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