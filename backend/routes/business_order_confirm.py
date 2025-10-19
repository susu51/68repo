"""
Business Order Confirmation Routes - Phase 1
Handles order confirmation and courier task creation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from auth_cookie import get_approved_business_user_from_cookie
from models_package.courier_tasks import CourierTaskStatus, Coordinates
from models import OrderStatus

router = APIRouter(prefix="/business/orders", tags=["business-orders"])

class ConfirmOrderRequest(BaseModel):
    unit_delivery_fee: float

class ConfirmOrderResponse(BaseModel):
    success: bool
    message: str
    order_id: str
    task_id: Optional[str] = None

@router.put("/{order_id}/confirm", response_model=ConfirmOrderResponse)
async def confirm_order(
    order_id: str,
    request: ConfirmOrderRequest,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """
    Confirm order and create courier task
    
    Business confirms order with unit delivery fee.
    Creates a courier task in 'waiting' status.
    Publishes WebSocket event to courier:global topic.
    """
    from server import db
    from realtime.event_bus import event_bus
    
    try:
        business_id = current_user["id"]
        
        # Validation: unit_delivery_fee must be positive
        if request.unit_delivery_fee <= 0:
            raise HTTPException(
                status_code=400,
                detail="Geçerli bir paket ücreti giriniz."
            )
        
        # Find order - try both _id and id fields
        from bson import ObjectId
        order = None
        
        # Try to find by ObjectId first
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            pass
        
        # If not found, try by custom id field
        if not order:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(
                status_code=404,
                detail="Sipariş bulunamadı."
            )
        
        # RBAC: Business can only confirm their own orders
        if order.get("business_id") != business_id:
            raise HTTPException(
                status_code=403,
                detail="Bu siparişi onaylama yetkiniz yok."
            )
        
        # Check if order is in correct status
        if order.get("status") not in ["created", "pending", "placed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Bu sipariş zaten onaylandı veya tamamlandı. (Durum: {order.get('status')})"
            )
        
        # Update order status to 'confirmed'
        now = datetime.now(timezone.utc)
        
        # Update using the same query that found the order
        query = {"id": order_id}
        try:
            # Try ObjectId first
            query = {"_id": ObjectId(order_id)}
        except:
            query = {"id": order_id}
        
        await db.orders.update_one(
            query,
            {
                "$set": {
                    "status": "confirmed",
                    "unit_delivery_fee": request.unit_delivery_fee,
                    "updated_at": now,
                    "confirmed_at": now
                },
                "$push": {
                    "timeline": {
                        "event": "confirmed",
                        "at": now.isoformat(),
                        "by": business_id
                    }
                }
            }
        )
        
        # Get restaurant/business location for pickup coordinates
        restaurant = await db.businesses.find_one({"_id": order.get("restaurant_id") or order.get("business_id")})
        
        pickup_coords = {
            "lat": restaurant.get("latitude", 38.3687) if restaurant else 38.3687,
            "lng": restaurant.get("longitude", 34.0254) if restaurant else 34.0254
        }
        
        # Get delivery coordinates from order
        delivery_address = order.get("delivery_address", {})
        if isinstance(delivery_address, dict):
            dropoff_coords = {
                "lat": delivery_address.get("lat", 0),
                "lng": delivery_address.get("lng", 0)
            }
            dropoff_address = delivery_address.get("address", "")
        else:
            # Old format - just string
            dropoff_coords = {"lat": 0, "lng": 0}
            dropoff_address = str(delivery_address)
        
        # Create courier task
        task_id = str(uuid.uuid4())
        task_doc = {
            "_id": task_id,
            "order_id": order_id,
            "restaurant_id": order.get("restaurant_id") or order.get("business_id"),
            "business_id": business_id,
            "pickup_coords": pickup_coords,
            "dropoff_coords": dropoff_coords,
            "pickup_address": restaurant.get("address", "") if restaurant else "",
            "dropoff_address": dropoff_address,
            "unit_delivery_fee": request.unit_delivery_fee,
            "status": CourierTaskStatus.WAITING.value,
            "courier_id": None,
            "assigned_at": None,
            "picked_up_at": None,
            "delivered_at": None,
            "created_at": now,
            "updated_at": now
        }
        
        await db.courier_tasks.insert_one(task_doc)
        
        print(f"✅ Created courier task: {task_id} for order {order_id}")
        
        # Publish WebSocket event to courier:global
        try:
            await event_bus.publish("courier:global", {
                "type": "task.created",
                "task_id": task_id,
                "order_id": order_id,
                "restaurant_id": order.get("restaurant_id") or order.get("business_id"),
                "restaurant_name": order.get("business_name", ""),
                "pickup_coords": pickup_coords,
                "dropoff_coords": dropoff_coords,
                "unit_delivery_fee": request.unit_delivery_fee,
                "timestamp": now.isoformat()
            })
            print(f"📡 Published task.created event to courier:global")
        except Exception as ws_error:
            print(f"⚠️ Failed to publish WebSocket event: {ws_error}")
            # Don't fail the request if WebSocket fails
        
        # Also publish to business and order topics
        try:
            await event_bus.publish(f"business:{business_id}", {
                "type": "order.confirmed",
                "order_id": order_id,
                "task_id": task_id
            })
            
            await event_bus.publish(f"order:{order_id}", {
                "type": "order.confirmed",
                "task_id": task_id
            })
        except Exception as ws_error:
            print(f"⚠️ Failed to publish order confirmation events: {ws_error}")
        
        return ConfirmOrderResponse(
            success=True,
            message="Sipariş onaylandı. Kurye bekleniyor.",
            order_id=order_id,
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error confirming order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sipariş onaylanırken hata oluştu: {str(e)}"
        )
