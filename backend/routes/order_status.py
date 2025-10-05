"""
Phase 3: Order Status Flow Management with CAS Locking
İşletme Durum Akışı & Kurye Sistemi
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from models import OrderStatus
from auth_dependencies import get_business_user, get_courier_user

router = APIRouter(prefix="/orders", tags=["order-status"])

class OrderStatusUpdate(BaseModel):
    from_status: str = None  # Compare-And-Swap - mevcut durum kontrolü
    to_status: str           # Hedef durum

class OrderStatusResponse(BaseModel):
    id: str
    status: str
    updated_at: datetime
    updated_by: str
    updated_by_role: str

# İzinli Durum Geçişleri - Business Chain
BUSINESS_TRANSITIONS = {
    "created": ["preparing"],
    "preparing": ["ready"], 
    "ready": ["courier_pending"]
}

# İzinli Durum Geçişleri - Courier Chain  
COURIER_TRANSITIONS = {
    "courier_assigned": ["picked_up"],
    "picked_up": ["delivering"],
    "delivering": ["delivered"]
}

@router.patch("/{order_id}/status", response_model=OrderStatusResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: dict = Depends(get_business_user)  # Default: business user
):
    """
    Update order status with CAS (Compare-And-Swap) locking
    İzinli geçişler:
    - Business: created → preparing → ready → courier_pending  
    - Courier: courier_assigned → picked_up → delivering → delivered
    """
    try:
        from server import db
        
        # Find order and verify ownership/access
        order = await db.orders.find_one({"_id": order_id})
        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )
        
        # Verify business ownership for business transitions
        user_role = current_user.get("role")
        if user_role == "business":
            # Business can only update their own orders
            business = await db.businesses.find_one({"owner_user_id": current_user["id"]})
            if not business or str(business["_id"]) != order["business_id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied - not your order"
                )
            
            # Check if transition is allowed for business
            current_status = order["status"]
            if current_status not in BUSINESS_TRANSITIONS:
                raise HTTPException(
                    status_code=403,
                    detail=f"Business cannot modify order in status: {current_status}"
                )
                
            if status_update.to_status not in BUSINESS_TRANSITIONS[current_status]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transition: {current_status} → {status_update.to_status}"
                )
        
        elif user_role == "courier":
            # Courier can only update orders assigned to them
            if order.get("courier_id") != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied - order not assigned to you"
                )
            
            # Check if transition is allowed for courier
            current_status = order["status"]
            if current_status not in COURIER_TRANSITIONS:
                raise HTTPException(
                    status_code=403,
                    detail=f"Courier cannot modify order in status: {current_status}"
                )
                
            if status_update.to_status not in COURIER_TRANSITIONS[current_status]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transition: {current_status} → {status_update.to_status}"
                )
        else:
            raise HTTPException(
                status_code=403,
                detail="Only business or courier can update order status"
            )
        
        # CAS (Compare-And-Swap) Operation
        current_status = order["status"]
        
        # If from_status is specified, verify it matches current status
        if status_update.from_status and status_update.from_status != current_status:
            raise HTTPException(
                status_code=409,  # Conflict - CAS failed
                detail=f"Status mismatch: expected '{status_update.from_status}', found '{current_status}'"
            )
        
        # Atomic update with CAS
        update_data = {
            "status": status_update.to_status,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user["id"],
            "updated_by_role": user_role
        }
        
        # Use atomic findOneAndUpdate for CAS
        result = await db.orders.find_one_and_update(
            {
                "_id": order_id,
                "status": current_status  # CAS condition
            },
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=409,  # Conflict - CAS failed (someone else updated)
                detail="Order status was modified by another user. Please refresh and try again."
            )
        
        print(f"🔄 ORDER STATUS UPDATE: {order_id} | {current_status} → {status_update.to_status} | By: {user_role} {current_user['id']}")
        
        return OrderStatusResponse(
            id=order_id,
            status=result["status"],
            updated_at=result["updated_at"],
            updated_by=result["updated_by"],
            updated_by_role=result["updated_by_role"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating order status: {str(e)}"
        )


# Override endpoint for courier access
@router.patch("/{order_id}/status")
async def update_order_status_courier(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: dict = Depends(get_courier_user)  # Courier version
):
    """Courier version of status update - same logic but with courier dependency"""
    # Use the same function but with courier user
    return await update_order_status(order_id, status_update, current_user)