"""
Phase 2: Customer Profile & Ratings System
Profile update, order ratings for courier/business
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Literal
from datetime import datetime, timezone
from auth_cookie import get_current_user_from_cookie_or_bearer

router = APIRouter(prefix="/customer", tags=["customer-profile"])

# === MODELS ===

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+90'):
            v = '+90' + v.lstrip('0')
        return v

class RatingRequest(BaseModel):
    targetType: Literal["courier", "business"]
    targetId: str
    orderId: str
    stars: int
    comment: Optional[str] = None
    
    @validator('stars')
    def validate_stars(cls, v):
        if v < 1 or v > 5:
            raise ValueError('stars must be between 1 and 5')
        return v

# === AUTHENTICATION HELPER ===

async def get_customer_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get current customer user with role validation"""
    if current_user.get("role") != "customer":
        raise HTTPException(
            status_code=403,
            detail="Customer access required"
        )
    return current_user

# === ENDPOINTS ===

@router.put("/profile")
async def update_customer_profile(
    profile: ProfileUpdateRequest,
    current_user: dict = Depends(get_customer_user)
):
    """Update customer profile information"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Build update dict (only include non-None values)
        update_data = {}
        if profile.name is not None:
            update_data['first_name'] = profile.name
        if profile.surname is not None:
            update_data['last_name'] = profile.surname
        if profile.email is not None:
            update_data['email'] = profile.email
        if profile.phone is not None:
            update_data['phone'] = profile.phone
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        # Update in database
        result = await db.users.update_one(
            {"_id": customer_id, "role": "customer"},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Fetch updated profile
        updated_customer = await db.users.find_one({"_id": customer_id})
        
        return {
            "success": True,
            "message": "Profil başarıyla güncellendi",
            "profile": {
                "id": customer_id,
                "name": updated_customer.get('first_name', ''),
                "surname": updated_customer.get('last_name', ''),
                "email": updated_customer.get('email', ''),
                "phone": updated_customer.get('phone', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating customer profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Profil güncelleme hatası: {str(e)}"
        )

@router.post("/ratings")
async def create_rating(
    rating: RatingRequest,
    current_user: dict = Depends(get_customer_user)
):
    """Create rating for courier or business after order delivery"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Verify order exists and belongs to customer
        order = await db.orders.find_one({"_id": rating.orderId})
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
        
        if order.get('customer_id') != customer_id:
            raise HTTPException(status_code=403, detail="Bu sipariş size ait değil")
        
        # Check if order is delivered
        if order.get('status') != 'delivered':
            raise HTTPException(status_code=400, detail="Sadece teslim edilmiş siparişler değerlendirilebilir")
        
        # Check if already rated
        existing_rating = await db.ratings.find_one({
            "order_id": rating.orderId,
            "customer_id": customer_id,
            "target_type": rating.targetType
        })
        
        if existing_rating:
            raise HTTPException(status_code=400, detail="Bu sipariş için zaten değerlendirme yaptınız")
        
        # Create rating
        rating_doc = {
            "target_type": rating.targetType,
            "target_id": rating.targetId,
            "order_id": rating.orderId,
            "customer_id": customer_id,
            "stars": rating.stars,
            "comment": rating.comment,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = await db.ratings.insert_one(rating_doc)
        
        # Update target's average rating
        await update_target_rating(db, rating.targetType, rating.targetId)
        
        return {
            "success": True,
            "message": "Değerlendirmeniz kaydedildi, teşekkürler!",
            "rating_id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating rating: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Değerlendirme kaydedilemedi: {str(e)}"
        )

async def update_target_rating(db, target_type: str, target_id: str):
    """Update average rating and priority score for courier/business"""
    try:
        # Calculate average rating
        pipeline = [
            {"$match": {"target_type": target_type, "target_id": target_id}},
            {"$group": {
                "_id": None,
                "avg_rating": {"$avg": "$stars"},
                "count": {"$sum": 1}
            }}
        ]
        
        result = await db.ratings.aggregate(pipeline).to_list(length=1)
        
        if result:
            avg_rating = result[0]['avg_rating']
            count = result[0]['count']
            
            # Update target document
            collection = db.users if target_type == "courier" else db.businesses
            
            update_doc = {
                "rating": {
                    "avg": round(avg_rating, 2),
                    "count": count
                },
                "updated_at": datetime.now(timezone.utc)
            }
            
            # For couriers, also update priority score
            if target_type == "courier":
                # Get courier stats
                courier = await db.users.find_one({"_id": target_id, "role": "courier"})
                
                if courier:
                    # Calculate completion rate (last 30 days)
                    thirty_days_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                    thirty_days_ago = thirty_days_ago.replace(day=thirty_days_ago.day - 30)
                    
                    total_assigned = await db.orders.count_documents({
                        "courier_id": target_id,
                        "created_at": {"$gte": thirty_days_ago}
                    })
                    
                    completed = await db.orders.count_documents({
                        "courier_id": target_id,
                        "status": "delivered",
                        "created_at": {"$gte": thirty_days_ago}
                    })
                    
                    completion_rate = completed / total_assigned if total_assigned > 0 else 0
                    
                    # Calculate on-time rate (simplified: if delivered within 1 hour)
                    on_time = await db.orders.count_documents({
                        "courier_id": target_id,
                        "status": "delivered",
                        "created_at": {"$gte": thirty_days_ago},
                        "$expr": {
                            "$lte": [
                                {"$divide": [{"$subtract": ["$delivered_at", "$created_at"]}, 3600000]},
                                1
                            ]
                        }
                    })
                    
                    on_time_rate = on_time / completed if completed > 0 else 0
                    
                    # Priority score formula
                    priority_score = (avg_rating / 5.0 * 0.7) + (completion_rate * 0.2) + (on_time_rate * 0.1)
                    
                    update_doc['priority_score'] = round(priority_score, 3)
            
            await collection.update_one(
                {"_id": target_id},
                {"$set": update_doc}
            )
            
            print(f"✅ Updated {target_type} {target_id} rating: {avg_rating:.2f} ({count} reviews)")
            
    except Exception as e:
        print(f"⚠️ Error updating target rating: {e}")
        # Don't raise, this is background update
