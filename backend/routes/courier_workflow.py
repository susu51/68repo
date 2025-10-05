"""
Phase 3: Courier Workflow & Order Management
Kurye Erişimi & İş Akışı
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import math
import asyncio
import uuid
from models import OrderStatus
from auth_dependencies import get_courier_user

router = APIRouter(prefix="/orders", tags=["courier-workflow"])

class AvailableOrderResponse(BaseModel):
    id: str
    business_id: str
    business_name: str
    business_address: str
    business_location: dict  # {lat, lng}
    distance_m: float
    total_amount: float
    delivery_address: dict
    estimated_pickup_time: str
    created_at: datetime

class OrderAcceptResponse(BaseModel):
    id: str
    status: str
    courier_id: str
    accepted_at: datetime
    pickup_address: dict

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

@router.get("/available", response_model=List[AvailableOrderResponse])
async def get_available_orders(
    lat: float = Query(..., description="Courier current latitude"),
    lng: float = Query(..., description="Courier current longitude"),
    radius_m: Optional[int] = Query(5000, description="Search radius in meters"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get available orders for courier - courier_pending status only
    Sorted by proximity to business location (yakınlık sırasıyla)
    """
    try:
        from server import db
        
        print(f"🚚 COURIER {current_user['id']} requesting available orders at ({lat}, {lng})")
        
        # Find orders with courier_pending status
        available_orders = await db.orders.find({
            "status": "courier_pending"
        }).to_list(length=None)
        
        print(f"📦 Found {len(available_orders)} courier_pending orders")
        
        if not available_orders:
            return []
        
        # Get business locations and calculate distances
        order_responses = []
        
        for order in available_orders:
            try:
                # Get business location
                business = await db.businesses.find_one({"_id": order["business_id"]})
                if not business or not business.get("location"):
                    continue
                
                # Calculate distance from courier to business
                business_coords = business["location"]["coordinates"]  # [lng, lat]
                business_lat, business_lng = business_coords[1], business_coords[0]
                
                distance = calculate_distance(lat, lng, business_lat, business_lng)
                
                # Skip if outside radius
                if distance > radius_m:
                    continue
                
                # Estimated pickup time (5 minutes + travel time based on distance)
                travel_time_minutes = max(5, int(distance / 1000 * 3))  # 3 minutes per km minimum
                pickup_time = f"{travel_time_minutes} dakika"
                
                order_responses.append(AvailableOrderResponse(
                    id=str(order["_id"]),
                    business_id=order["business_id"],
                    business_name=business.get("name", "Unknown Business"),
                    business_address=business.get("address", "Address not available"),
                    business_location={
                        "lat": business_lat,
                        "lng": business_lng
                    },
                    distance_m=round(distance, 0),
                    total_amount=order["total_amount"],
                    delivery_address=order["delivery_address"],
                    estimated_pickup_time=pickup_time,
                    created_at=order["created_at"]
                ))
                
            except Exception as e:
                print(f"⚠️ Error processing order {order.get('_id')}: {e}")
                continue
        
        # Sort by distance (closest first - yakınlık sırasıyla)
        order_responses.sort(key=lambda x: x.distance_m)
        
        print(f"✅ Returning {len(order_responses)} available orders sorted by distance")
        
        return order_responses
        
    except Exception as e:
        print(f"❌ Error fetching available orders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching available orders: {str(e)}"
        )

@router.post("/{order_id}/accept", response_model=OrderAcceptResponse)
async def accept_order(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Accept order - Atomik kilitle: yalnızca courier_pending'se courier_assigned + courier_id set
    Çift kabulda 409 (Conflict) döner
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        print(f"🤝 COURIER {courier_id} attempting to accept order {order_id}")
        
        # Atomic accept operation with CAS (Compare-And-Swap)
        result = await db.orders.find_one_and_update(
            {
                "_id": order_id,
                "status": "courier_pending",  # Must be courier_pending
                "courier_id": {"$exists": False}  # No courier assigned yet
            },
            {
                "$set": {
                    "status": "courier_assigned",
                    "courier_id": courier_id,
                    "accepted_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": courier_id,
                    "updated_by_role": "courier"
                }
            },
            return_document=True
        )
        
        if not result:
            # Check if order exists but is already assigned
            existing_order = await db.orders.find_one({"_id": order_id})
            if not existing_order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found"
                )
            elif existing_order.get("courier_id"):
                raise HTTPException(
                    status_code=409,  # Conflict - Çift kabul
                    detail=f"Order already accepted by courier {existing_order['courier_id']}"
                )
            elif existing_order["status"] != "courier_pending":
                raise HTTPException(
                    status_code=409,  # Conflict
                    detail=f"Order status is {existing_order['status']}, cannot accept"
                )
            else:
                raise HTTPException(
                    status_code=409,  # General conflict
                    detail="Order could not be accepted - may have been taken by another courier"
                )
        
        # Get business info for pickup address
        business = await db.businesses.find_one({"_id": result["business_id"]})
        pickup_address = {
            "address": business.get("address", "Address not available") if business else "Business not found",
            "lat": business["location"]["coordinates"][1] if business and business.get("location") else 0,
            "lng": business["location"]["coordinates"][0] if business and business.get("location") else 0
        }
        
        print(f"✅ ORDER ACCEPTED: {order_id} by courier {courier_id}")
        
        return OrderAcceptResponse(
            id=order_id,
            status=result["status"],
            courier_id=result["courier_id"],
            accepted_at=result["accepted_at"],
            pickup_address=pickup_address
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error accepting order {order_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error accepting order: {str(e)}"
        )

@router.post("/{order_id}/pickup")
async def pickup_order(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Pickup order: courier_assigned → picked_up
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Atomic update with CAS
        result = await db.orders.find_one_and_update(
            {
                "_id": order_id,
                "status": "courier_assigned",
                "courier_id": courier_id
            },
            {
                "$set": {
                    "status": "picked_up",
                    "picked_up_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": courier_id,
                    "updated_by_role": "courier"
                }
            },
            return_document=True
        )
        
        if not result:
            order = await db.orders.find_one({"_id": order_id})
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            elif order.get("courier_id") != courier_id:
                raise HTTPException(status_code=403, detail="Order not assigned to you")
            elif order["status"] != "courier_assigned":
                raise HTTPException(
                    status_code=409, 
                    detail=f"Cannot pickup order in status: {order['status']}"
                )
            else:
                raise HTTPException(status_code=409, detail="Pickup failed - status changed")
        
        print(f"📦 ORDER PICKED UP: {order_id} by courier {courier_id}")
        
        return {
            "id": order_id,
            "status": result["status"],
            "picked_up_at": result["picked_up_at"],
            "message": "Order picked up successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error picking up order: {str(e)}"
        )

@router.post("/{order_id}/start_delivery")
async def start_delivery(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Start delivery: picked_up → delivering
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Atomic update with CAS
        result = await db.orders.find_one_and_update(
            {
                "_id": order_id,
                "status": "picked_up",
                "courier_id": courier_id
            },
            {
                "$set": {
                    "status": "delivering",
                    "delivery_started_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": courier_id,
                    "updated_by_role": "courier"
                }
            },
            return_document=True
        )
        
        if not result:
            order = await db.orders.find_one({"_id": order_id})
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            elif order.get("courier_id") != courier_id:
                raise HTTPException(status_code=403, detail="Order not assigned to you")
            elif order["status"] != "picked_up":
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot start delivery from status: {order['status']}"
                )
            else:
                raise HTTPException(status_code=409, detail="Start delivery failed - status changed")
        
        print(f"🚚 DELIVERY STARTED: {order_id} by courier {courier_id}")
        
        return {
            "id": order_id,
            "status": result["status"],
            "delivery_started_at": result["delivery_started_at"],
            "message": "Delivery started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting delivery: {str(e)}"
        )

@router.post("/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Deliver order: delivering → delivered
    
    Teslimde:
    - earnings.insert({courier_id, order_id, amount: settings.courier_rate_per_package, created_at})
    - orders.totals.courier_earning = amount güncelle
    """
    try:
        from server import db
        
        courier_id = current_user["id"]
        
        # Get global settings for courier rate
        settings = await db.settings.find_one({"_id": "global"})
        courier_rate = settings.get("courier_rate_per_package", 20) if settings else 20
        
        # Atomic update with CAS
        result = await db.orders.find_one_and_update(
            {
                "_id": order_id,
                "status": "delivering",
                "courier_id": courier_id
            },
            {
                "$set": {
                    "status": "delivered",
                    "delivered_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": courier_id,
                    "updated_by_role": "courier",
                    "totals.courier_earning": courier_rate
                }
            },
            return_document=True
        )
        
        if not result:
            order = await db.orders.find_one({"_id": order_id})
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            elif order.get("courier_id") != courier_id:
                raise HTTPException(status_code=403, detail="Order not assigned to you")
            elif order["status"] != "delivering":
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot deliver order from status: {order['status']}"
                )
            else:
                raise HTTPException(status_code=409, detail="Delivery failed - status changed")
        
        # Create earnings record
        earnings_record = {
            "_id": str(uuid.uuid4()),
            "courier_id": courier_id,
            "order_id": order_id,
            "amount": courier_rate,
            "created_at": datetime.now(timezone.utc),
            "order_total": result["total_amount"],
            "business_id": result["business_id"]
        }
        
        await db.earnings.insert_one(earnings_record)
        
        print(f"✅ ORDER DELIVERED: {order_id} by courier {courier_id} | Earning: ₺{courier_rate}")
        
        return {
            "id": order_id,
            "status": result["status"],
            "delivered_at": result["delivered_at"],
            "courier_earning": courier_rate,
            "earnings_id": earnings_record["_id"],
            "message": "Order delivered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error delivering order: {str(e)}"
        )