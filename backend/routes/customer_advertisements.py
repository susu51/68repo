"""
Customer Advertisement Routes
Get active advertisements based on customer's city
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

router = APIRouter()

@router.get("/active")
async def get_active_advertisements(city: Optional[str] = None):
    """
    Get active advertisements for customer's city
    If city is not provided, returns all active advertisements
    Supports both city-only and city-district format matching
    """
    from server import db
    
    try:
        # Build query
        query = {"is_active": True}
        
        if city:
            # Normalize city name for case-insensitive matching
            normalized_city = city.strip().title()
            
            # Match ads that:
            # 1. Exact city match (e.g., "İstanbul" matches "İstanbul")
            # 2. City-district match (e.g., "İstanbul" matches "İstanbul - Kadıköy")
            # 3. Starts with city name (for flexibility)
            query["$or"] = [
                {"city": normalized_city},  # Exact match
                {"city": {"$regex": f"^{normalized_city}\\s*-", "$options": "i"}},  # Starts with city + " -"
                {"city": {"$regex": f"^{normalized_city}$", "$options": "i"}}  # Case-insensitive exact
            ]
        
        # Fetch active advertisements
        advertisements = await db.advertisements.find(query).sort("created_at", -1).to_list(length=50)
        
        # Remove MongoDB _id
        for ad in advertisements:
            ad.pop("_id", None)
        
        return {
            "success": True,
            "advertisements": advertisements,
            "count": len(advertisements),
            "city": city if city else "all"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error fetching advertisements: {str(e)}")
