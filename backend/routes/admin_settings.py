"""
Phase 3: Admin Settings Management  
Admin Ayarları - courier earnings & radius management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from auth_dependencies import get_admin_user

router = APIRouter(prefix="/admin", tags=["admin-settings"])

class GlobalSettings(BaseModel):
    courier_rate_per_package: Optional[float] = None    # Kurye kazancı per teslimat
    nearby_radius_m: Optional[int] = None               # Yakınlık yarıçapı (metre)
    business_commission_pct: Optional[float] = None     # İşletme komisyonu (%)
    min_order_amount: Optional[float] = None            # Minimum sipariş tutarı
    delivery_fee: Optional[float] = None                # Teslimat ücreti
    max_delivery_distance_km: Optional[int] = None      # Maksimum teslimat mesafesi

class SettingsResponse(BaseModel):
    courier_rate_per_package: float
    nearby_radius_m: int
    business_commission_pct: float
    min_order_amount: float
    delivery_fee: float
    max_delivery_distance_km: int
    last_updated: datetime
    updated_by: Optional[str] = None

@router.get("/settings", response_model=SettingsResponse)
async def get_global_settings(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get current global settings
    """
    try:
        from server import db
        
        settings = await db.settings.find_one({"_id": "global"})
        
        if not settings:
            # Return default settings if none exist
            default_settings = {
                "courier_rate_per_package": 20.0,
                "nearby_radius_m": 5000,
                "business_commission_pct": 5.0,
                "min_order_amount": 30.0,
                "delivery_fee": 10.0,
                "max_delivery_distance_km": 15,
                "last_updated": datetime.now(timezone.utc)
            }
            
            # Create default settings in database
            await db.settings.insert_one({
                "_id": "global",
                **default_settings
            })
            
            return SettingsResponse(**default_settings)
        
        return SettingsResponse(
            courier_rate_per_package=settings.get("courier_rate_per_package", 20.0),
            nearby_radius_m=settings.get("nearby_radius_m", 5000),
            business_commission_pct=settings.get("business_commission_pct", 5.0),
            min_order_amount=settings.get("min_order_amount", 30.0),
            delivery_fee=settings.get("delivery_fee", 10.0),
            max_delivery_distance_km=settings.get("max_delivery_distance_km", 15),
            last_updated=settings.get("last_updated", settings.get("created_at", datetime.now(timezone.utc))),
            updated_by=settings.get("updated_by")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching settings: {str(e)}"
        )

@router.patch("/settings", response_model=SettingsResponse)
async def update_global_settings(
    settings_update: GlobalSettings,
    current_user: dict = Depends(get_admin_user)
):
    """
    Update global settings
    
    Alanlar: courier_rate_per_package, nearby_radius_m, business_commission_pct
    Ayar Etkisi: courier_rate_per_package admin'den değişince sonraki teslim bu yeni değerle yazılır
    """
    try:
        from server import db
        
        # Prepare update data (only include non-None fields)
        update_data = {}
        
        if settings_update.courier_rate_per_package is not None:
            if settings_update.courier_rate_per_package < 0:
                raise HTTPException(status_code=400, detail="Courier rate cannot be negative")
            update_data["courier_rate_per_package"] = settings_update.courier_rate_per_package
        
        if settings_update.nearby_radius_m is not None:
            if settings_update.nearby_radius_m < 100 or settings_update.nearby_radius_m > 50000:
                raise HTTPException(status_code=400, detail="Nearby radius must be between 100m and 50km")
            update_data["nearby_radius_m"] = settings_update.nearby_radius_m
        
        if settings_update.business_commission_pct is not None:
            if settings_update.business_commission_pct < 0 or settings_update.business_commission_pct > 50:
                raise HTTPException(status_code=400, detail="Business commission must be between 0% and 50%")
            update_data["business_commission_pct"] = settings_update.business_commission_pct
            
        if settings_update.min_order_amount is not None:
            if settings_update.min_order_amount < 0:
                raise HTTPException(status_code=400, detail="Minimum order amount cannot be negative")
            update_data["min_order_amount"] = settings_update.min_order_amount
            
        if settings_update.delivery_fee is not None:
            if settings_update.delivery_fee < 0:
                raise HTTPException(status_code=400, detail="Delivery fee cannot be negative")
            update_data["delivery_fee"] = settings_update.delivery_fee
            
        if settings_update.max_delivery_distance_km is not None:
            if settings_update.max_delivery_distance_km < 1 or settings_update.max_delivery_distance_km > 100:
                raise HTTPException(status_code=400, detail="Max delivery distance must be between 1km and 100km")
            update_data["max_delivery_distance_km"] = settings_update.max_delivery_distance_km
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")
        
        # Add metadata
        update_data.update({
            "last_updated": datetime.now(timezone.utc),
            "updated_by": current_user["id"]
        })
        
        # Update settings (upsert if doesn't exist)
        result = await db.settings.find_one_and_update(
            {"_id": "global"},
            {"$set": update_data},
            upsert=True,
            return_document=True
        )
        
        # Log significant changes
        if "courier_rate_per_package" in update_data:
            print(f"💰 COURIER RATE UPDATED: ₺{update_data['courier_rate_per_package']} per package by admin {current_user['id']}")
            
        if "nearby_radius_m" in update_data:
            print(f"📍 NEARBY RADIUS UPDATED: {update_data['nearby_radius_m']}m by admin {current_user['id']}")
            
        if "business_commission_pct" in update_data:
            print(f"💼 BUSINESS COMMISSION UPDATED: {update_data['business_commission_pct']}% by admin {current_user['id']}")
        
        return SettingsResponse(
            courier_rate_per_package=result.get("courier_rate_per_package", 20.0),
            nearby_radius_m=result.get("nearby_radius_m", 5000),
            business_commission_pct=result.get("business_commission_pct", 5.0),
            min_order_amount=result.get("min_order_amount", 30.0),
            delivery_fee=result.get("delivery_fee", 10.0),
            max_delivery_distance_km=result.get("max_delivery_distance_km", 15),
            last_updated=result.get("last_updated"),
            updated_by=result.get("updated_by")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating settings: {str(e)}"
        )

@router.get("/earnings/summary")
async def get_earnings_summary(
    current_user: dict = Depends(get_admin_user)
):
    """
    Get earnings summary statistics for admin dashboard
    """
    try:
        from server import db
        
        # Total earnings paid out
        total_earnings = await db.earnings.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$amount"},
                    "total_orders": {"$sum": 1}
                }
            }
        ]).to_list(length=1)
        
        # Earnings by courier (top 10)
        top_couriers = await db.earnings.aggregate([
            {
                "$group": {
                    "_id": "$courier_id",
                    "total_earned": {"$sum": "$amount"},
                    "orders_completed": {"$sum": 1},
                    "last_delivery": {"$max": "$created_at"}
                }
            },
            {"$sort": {"total_earned": -1}},
            {"$limit": 10}
        ]).to_list(length=10)
        
        # Recent earnings (last 24h)
        from datetime import timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        recent_earnings = await db.earnings.aggregate([
            {
                "$match": {
                    "created_at": {"$gte": yesterday}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": "$amount"},
                    "total_orders": {"$sum": 1}
                }
            }
        ]).to_list(length=1)
        
        return {
            "total_earnings": total_earnings[0] if total_earnings else {"total_amount": 0, "total_orders": 0},
            "top_couriers": top_couriers,
            "recent_earnings_24h": recent_earnings[0] if recent_earnings else {"total_amount": 0, "total_orders": 0},
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching earnings summary: {str(e)}"
        )