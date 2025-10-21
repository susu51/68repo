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
from auth_dependencies import get_business_user, get_courier_user, get_current_user

router = APIRouter(prefix="/orders", tags=["order-status"])

class OrderStatusUpdate(BaseModel):
    from_: Optional[str] = None  # Compare-And-Swap - mevcut durum kontrolü (named 'from_' due to Python keyword)
    to: str                      # Hedef durum
    
    class Config:
        # Map 'from' in JSON to 'from_' in Python (Pydantic V2)
        populate_by_name = True
        # Pydantic V2: Use Field alias instead of 'fields'
    
    # Alternatively, use Field with alias (Pydantic V2 style)
    # from_: Optional[str] = Field(None, alias='from')

class OrderStatusResponse(BaseModel):
    id: str
    status: str
    updated_at: datetime
    updated_by: str
    updated_by_role: str

# İzinli Durum Geçişleri - Business Chain
BUSINESS_TRANSITIONS = {
    "created": ["confirmed"],  # First: Business confirms the order
    "pending": ["confirmed"],  # Pending orders can be confirmed
    "placed": ["confirmed"],   # Placed orders can be confirmed
    "confirmed": ["preparing"],  # Then: Start preparing (creates courier task)
    "preparing": ["ready", "ready_for_pickup"],  # Phase 1: Can go to ready or ready_for_pickup
    "ready": ["courier_pending", "ready_for_pickup"],  # Phase 1: Can transition to ready_for_pickup
    "ready_for_pickup": ["courier_pending"]  # Phase 1: Courier can see on map, then becomes courier_pending when accepted
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
    current_user: dict = Depends(get_current_user)  # Allow both business and courier
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
                
            if status_update.to not in BUSINESS_TRANSITIONS[current_status]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transition: {current_status} → {status_update.to}"
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
                
            if status_update.to not in COURIER_TRANSITIONS[current_status]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid transition: {current_status} → {status_update.to}"
                )
        else:
            raise HTTPException(
                status_code=403,
                detail="Only business or courier can update order status"
            )
        
        # CAS (Compare-And-Swap) Operation
        current_status = order["status"]
        
        # If from_ is specified, verify it matches current status (CAS)
        if status_update.from_ and status_update.from_ != current_status:
            raise HTTPException(
                status_code=409,  # Conflict - CAS failed
                detail=f"Status mismatch: expected '{status_update.from_}', found '{current_status}'"
            )
        
        # Atomic update with CAS
        update_data = {
            "status": status_update.to,
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
        
        print(f"🔄 ORDER STATUS UPDATE: {order_id} | {current_status} → {status_update.to} | By: {user_role} {current_user['id']}")
        
        # Broadcast status update via WebSocket
        try:
            from websocket_manager import websocket_manager
            await websocket_manager.send_order_status_update(order_id, {
                "type": "status_changed",
                "from_status": current_status,
                "to_status": status_update.to,
                "updated_by": current_user["id"],
                "updated_by_role": user_role
            })
        except Exception as ws_error:
            print(f"⚠️ WebSocket broadcast failed: {ws_error}")
        
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


# No need for separate courier endpoint - single endpoint handles both roles