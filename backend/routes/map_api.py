"""
Map API for Courier - Business markers with custom icons
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from auth_dependencies import get_current_user

router = APIRouter(prefix="/map", tags=["map"])

@router.get("/businesses")
async def get_map_businesses(
    bbox: Optional[str] = Query(None, description="Bounding box: minLng,minLat,maxLng,maxLat"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get businesses for map display with custom icons and active order counts
    """
    from server import db
    
    try:
        # Parse bbox if provided
        filter_query = {"role": "business", "kyc_status": "approved"}
        
        if bbox:
            try:
                min_lng, min_lat, max_lng, max_lat = map(float, bbox.split(','))
                filter_query.update({
                    "lat": {"$gte": min_lat, "$lte": max_lat},
                    "lng": {"$gte": min_lng, "$lte": max_lng}
                })
            except:
                pass  # Ignore invalid bbox
        
        # Get businesses
        businesses = await db.users.find(filter_query).to_list(length=500)
        
        result = []
        for business in businesses:
            # Count active orders (ready status)
            active_count = await db.orders.count_documents({
                "business_id": business.get("id"),
                "status": {"$in": ["ready", "confirmed"]}
            })
            
            # Get icon URLs
            package_photo = business.get("package_photo_url")
            icon_url = business.get("icon_url") or package_photo or "/static/icons/box-default.png"
            icon2x_url = business.get("icon2x_url") or package_photo or "/static/icons/box-default.png"
            
            result.append({
                "id": business.get("id"),
                "name": business.get("business_name"),
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "district": business.get("district", ""),
                "location": {
                    "lat": business.get("lat"),
                    "lng": business.get("lng")
                },
                "active_order_count": active_count,
                "icon_url": icon_url,
                "icon2x_url": icon2x_url,
                "package_photo_url": package_photo
            })
        
        return result
        
    except Exception as e:
        print(f"❌ Map businesses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
