"""
Nearby Businesses with 2dsphere Geospatial Queries
Phase 2: Real Database Geospatial Implementation
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import math
from models import UserRole
from auth_dependencies import get_current_user

router = APIRouter(prefix="/nearby", tags=["geospatial"])

# Response Models
class BusinessMenuSnippet(BaseModel):
    id: str
    title: str
    price: float
    category: str

class NearbyBusinessResponse(BaseModel):
    id: str
    name: str
    address: str
    distance_m: float
    location: dict  # {lat, lng}
    menu_items: List[BusinessMenuSnippet]
    is_active: bool

async def get_settings():
    """Get global settings from database"""
    try:
        from server import db
        settings = await db.settings.find_one({"_id": "global"})
        return settings or {
            "nearby_radius_m": 5000,
            "courier_rate_per_package": 20,
            "business_commission_pct": 5
        }
    except:
        return {
            "nearby_radius_m": 5000,
            "courier_rate_per_package": 20,
            "business_commission_pct": 5
        }

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

@router.get("/businesses", response_model=List[NearbyBusinessResponse])
async def get_nearby_businesses(
    lat: float = Query(..., description="Customer latitude"),
    lng: float = Query(..., description="Customer longitude"),
    radius_m: Optional[int] = Query(None, description="Search radius in meters"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get nearby businesses using MongoDB 2dsphere geospatial query
    Real database implementation - NO MOCK DATA
    """
    try:
        from server import db
        
        # Get search radius from settings or parameter
        settings = await get_settings()
        search_radius = radius_m or settings.get("nearby_radius_m", 5000)
        
        print(f"🔍 Searching businesses within {search_radius}m of ({lat}, {lng})")
        
        # MongoDB 2dsphere geospatial query
        # Convert meters to radians (MongoDB requirement)
        radius_radians = search_radius / 6371000.0  # Earth radius in meters
        
        geospatial_query = {
            "location": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius_radians]
                }
            },
            "is_active": True
        }
        
        # Find nearby businesses from users collection (role: business)
        geospatial_query["role"] = "business"
        businesses = await db.users.find(geospatial_query).to_list(length=None)
        
        print(f"📍 Found {len(businesses)} businesses in radius")
        
        nearby_businesses = []
        
        for business in businesses:
            try:
                # Calculate precise distance
                biz_coords = business["location"]["coordinates"]  # [lng, lat]
                distance = calculate_distance(lat, lng, biz_coords[1], biz_coords[0])
                
                # Get menu items for this business (limit to 5 for preview)
                menu_items = await db.menu_items.find({
                    "business_id": str(business["_id"]),
                    "is_available": True
                }).limit(5).to_list(length=5)
                
                # Build menu snippets
                menu_snippets = [
                    BusinessMenuSnippet(
                        id=str(item["_id"]),
                        title=item["title"],
                        price=item["price"],
                        category=item.get("category", "Ana Yemek")
                    )
                    for item in menu_items
                ]
                
                nearby_businesses.append(
                    NearbyBusinessResponse(
                        id=business.get("id", str(business["_id"])),
                        name=business.get("business_name", business.get("name", "Unknown Business")),
                        address=business.get("full_address", business.get("address", "")),
                        distance_m=round(distance, 0),
                        location={
                            "lat": biz_coords[1],
                            "lng": biz_coords[0]
                        },
                        menu_items=menu_snippets,
                        is_active=business.get("is_active", True)
                    )
                )
                
            except Exception as e:
                print(f"⚠️ Error processing business {business.get('name', 'Unknown')}: {e}")
                continue
        
        # Sort by distance (closest first)
        nearby_businesses.sort(key=lambda x: x.distance_m)
        
        print(f"✅ Returning {len(nearby_businesses)} processed businesses")
        
        return nearby_businesses
        
    except Exception as e:
        print(f"❌ Nearby businesses error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error finding nearby businesses: {str(e)}"
        )

@router.get("/businesses/{business_id}/menu", response_model=List[BusinessMenuSnippet])
async def get_business_full_menu(
    business_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get full menu for a specific business"""
    try:
        from server import db
        
        # Verify business exists and is active
        business = await db.businesses.find_one({
            "_id": business_id,
            "is_active": True
        })
        
        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business not found or inactive"
            )
        
        # Get all available menu items
        menu_items = await db.menu_items.find({
            "business_id": business_id,
            "is_available": True
        }).sort("category", 1).to_list(length=None)
        
        return [
            BusinessMenuSnippet(
                id=str(item["_id"]),
                title=item["title"],
                price=item["price"],
                category=item.get("category", "Ana Yemek")
            )
            for item in menu_items
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching business menu: {str(e)}"
        )