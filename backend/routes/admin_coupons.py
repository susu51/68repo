"""
Admin Coupon Management Routes - Phase 3
CRUD operations for discount coupons
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid

from auth_dependencies import get_admin_user
from models_package.coupons import (
    Coupon, CouponCreate, CouponUpdate, CouponType, CouponScope
)

router = APIRouter(prefix="/admin/coupons", tags=["admin-coupons"])

# Admin dependency wrapper
async def require_admin(current_user: dict = Depends(get_admin_user)):
    """Ensure user is admin"""
    return current_user

@router.get("", response_model=List[Coupon])
async def get_coupons(
    current_user: dict = Depends(require_admin)
):
    """Get all coupons"""
    from server import db
    
    try:
        coupons = await db.coupons.find({}).sort("created_at", -1).to_list(length=None)
        
        result = []
        for coupon in coupons:
            result.append(Coupon(
                id=coupon.get("_id"),
                code=coupon.get("code"),
                title=coupon.get("title"),
                description=coupon.get("description", ""),
                type=coupon.get("type"),
                scope=coupon.get("scope"),
                value=coupon.get("value"),
                min_basket=coupon.get("min_basket"),
                valid_from=coupon.get("valid_from"),
                valid_to=coupon.get("valid_to"),
                per_user_limit=coupon.get("per_user_limit"),
                global_limit=coupon.get("global_limit"),
                current_uses=coupon.get("current_uses", 0),
                applicable_restaurants=coupon.get("applicable_restaurants", []),
                applicable_categories=coupon.get("applicable_categories", []),
                is_active=coupon.get("is_active", True),
                created_at=coupon.get("created_at", datetime.now(timezone.utc)),
                updated_at=coupon.get("updated_at", datetime.now(timezone.utc))
            ))
        
        return result
        
    except Exception as e:
        print(f"❌ Error fetching coupons: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch coupons: {str(e)}")

@router.post("", response_model=Coupon)
async def create_coupon(
    coupon_data: CouponCreate,
    current_user: dict = Depends(get_admin_user_from_cookie)
):
    """Create new coupon"""
    from server import db
    
    try:
        # Check if code already exists
        existing = await db.coupons.find_one({"code": coupon_data.code.upper()})
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Bu kupon kodu zaten kullanılıyor."
            )
        
        # Validation
        if coupon_data.value <= 0:
            raise HTTPException(
                status_code=400,
                detail="Kupon değeri 0'dan büyük olmalıdır."
            )
        
        if coupon_data.type == CouponType.PERCENT and coupon_data.value > 100:
            raise HTTPException(
                status_code=400,
                detail="Yüzdelik indirim 100'den fazla olamaz."
            )
        
        if coupon_data.valid_from >= coupon_data.valid_to:
            raise HTTPException(
                status_code=400,
                detail="Başlangıç tarihi bitiş tarihinden önce olmalıdır."
            )
        
        # Create coupon document
        now = datetime.now(timezone.utc)
        coupon_id = str(uuid.uuid4())
        
        coupon_doc = {
            "_id": coupon_id,
            "code": coupon_data.code.upper(),
            "title": coupon_data.title,
            "description": coupon_data.description,
            "type": coupon_data.type.value,
            "scope": coupon_data.scope.value,
            "value": coupon_data.value,
            "min_basket": coupon_data.min_basket,
            "valid_from": coupon_data.valid_from,
            "valid_to": coupon_data.valid_to,
            "per_user_limit": coupon_data.per_user_limit,
            "global_limit": coupon_data.global_limit,
            "current_uses": 0,
            "applicable_restaurants": coupon_data.applicable_restaurants,
            "applicable_categories": coupon_data.applicable_categories,
            "is_active": coupon_data.is_active,
            "created_at": now,
            "updated_at": now
        }
        
        await db.coupons.insert_one(coupon_doc)
        
        print(f"✅ Created coupon: {coupon_id} ({coupon_data.code})")
        
        return Coupon(**{**coupon_doc, "id": coupon_id})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating coupon: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create coupon: {str(e)}")

@router.put("/{coupon_id}", response_model=Coupon)
async def update_coupon(
    coupon_id: str,
    coupon_data: CouponUpdate,
    current_user: dict = Depends(get_admin_user_from_cookie)
):
    """Update coupon"""
    from server import db
    
    try:
        # Check if coupon exists
        coupon = await db.coupons.find_one({"_id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Kupon bulunamadı.")
        
        # Build update document
        update_doc = {}
        if coupon_data.title is not None:
            update_doc["title"] = coupon_data.title
        if coupon_data.description is not None:
            update_doc["description"] = coupon_data.description
        if coupon_data.value is not None:
            if coupon_data.value <= 0:
                raise HTTPException(status_code=400, detail="Kupon değeri 0'dan büyük olmalıdır.")
            update_doc["value"] = coupon_data.value
        if coupon_data.min_basket is not None:
            update_doc["min_basket"] = coupon_data.min_basket
        if coupon_data.valid_from is not None:
            update_doc["valid_from"] = coupon_data.valid_from
        if coupon_data.valid_to is not None:
            update_doc["valid_to"] = coupon_data.valid_to
        if coupon_data.per_user_limit is not None:
            update_doc["per_user_limit"] = coupon_data.per_user_limit
        if coupon_data.global_limit is not None:
            update_doc["global_limit"] = coupon_data.global_limit
        if coupon_data.applicable_restaurants is not None:
            update_doc["applicable_restaurants"] = coupon_data.applicable_restaurants
        if coupon_data.applicable_categories is not None:
            update_doc["applicable_categories"] = coupon_data.applicable_categories
        if coupon_data.is_active is not None:
            update_doc["is_active"] = coupon_data.is_active
        
        update_doc["updated_at"] = datetime.now(timezone.utc)
        
        await db.coupons.update_one({"_id": coupon_id}, {"$set": update_doc})
        
        # Fetch updated coupon
        updated_coupon = await db.coupons.find_one({"_id": coupon_id})
        
        return Coupon(**{**updated_coupon, "id": coupon_id})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating coupon: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update coupon: {str(e)}")

@router.delete("/{coupon_id}")
async def delete_coupon(
    coupon_id: str,
    current_user: dict = Depends(get_admin_user_from_cookie)
):
    """Delete coupon"""
    from server import db
    
    try:
        result = await db.coupons.delete_one({"_id": coupon_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Kupon bulunamadı.")
        
        return {"success": True, "message": "Kupon silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting coupon: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete coupon: {str(e)}")
