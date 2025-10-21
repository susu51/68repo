"""
Courier Tasks Routes - Phase 2
Handles courier task listing and acceptance
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from auth_cookie import get_current_user_from_cookie_or_bearer
from models_package.courier_tasks import CourierTaskStatus

router = APIRouter(prefix="/courier/tasks", tags=["courier-tasks"])

# Courier user validation
async def get_courier_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Validate that current user is a courier"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Only couriers can access this endpoint")
    return current_user

class TaskResponse(BaseModel):
    id: str
    order_id: str
    restaurant_id: str
    restaurant_name: Optional[str] = None
    pickup_coords: dict
    dropoff_coords: dict
    pickup_address: str
    dropoff_address: str
    unit_delivery_fee: float
    status: str
    courier_id: Optional[str] = None
    created_at: str

class AcceptTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: str

@router.get("/nearby-businesses")
async def get_nearby_businesses(
    lng: float = Query(..., description="Courier longitude"),
    lat: float = Query(..., description="Courier latitude"),
    radius_m: int = Query(7000, description="Search radius in meters"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get nearby businesses with ready orders count for map display
    Returns: [{business_id, name, location, pending_ready_count, address_short}]
    """
    from server import db
    
    try:
        # Find businesses within radius using geospatial query
        businesses_cursor = db.businesses.aggregate([
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "distanceField": "distance",
                    "spherical": True,
                    "maxDistance": radius_m
                }
            },
            {
                "$lookup": {
                    "from": "orders",
                    "let": {"bid": "$id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$eq": ["$business_id", "$$bid"]},
                                "status": "ready"
                            }
                        },
                        {"$count": "ready_count"}
                    ],
                    "as": "readyAgg"
                }
            },
            {
                "$addFields": {
                    "pending_ready_count": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$readyAgg.ready_count", 0]},
                            0
                        ]
                    }
                }
            },
            {
                "$match": {
                    "pending_ready_count": {"$gt": 0}  # Only businesses with ready orders
                }
            },
            {
                "$project": {
                    "business_id": "$id",
                    "name": "$business_name",
                    "location": "$location",
                    "pending_ready_count": 1,
                    "address_short": "$address",
                    "distance": 1,
                    "readyAgg": 0
                }
            }
        ])
        
        results = await businesses_cursor.to_list(length=100)
        
        print(f"✅ Found {len(results)} nearby businesses with ready orders")
        return results
        
    except Exception as e:
        print(f"❌ Error fetching nearby businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/businesses/{business_id}/available-orders")
async def get_business_available_orders(
    business_id: str,
    limit: int = Query(50, description="Max orders to return"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get available (ready) orders for a specific business
    Returns order summary for courier to select and claim
    """
    from server import db
    
    try:
        # Get ready orders for this business
        orders = await db.orders.find({
            "business_id": business_id,
            "status": "ready"
        }).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Format for courier view
        formatted = []
        for order in orders:
            # Get customer info
            customer = await db.users.find_one({"id": order.get("customer_id")})
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() if customer else "Müşteri"
            
            # Parse delivery address
            delivery_addr = order.get("delivery_address", {})
            if isinstance(delivery_addr, dict):
                address_text = delivery_addr.get("label") or delivery_addr.get("address", "")
                delivery_lat = delivery_addr.get("lat")
                delivery_lng = delivery_addr.get("lng")
            else:
                address_text = str(delivery_addr) if delivery_addr else ""
                delivery_lat = order.get("delivery_lat")
                delivery_lng = order.get("delivery_lng")
            
            formatted.append({
                "order_id": order.get("id"),
                "order_code": order.get("id")[:8],
                "customer_name": customer_name,
                "delivery_address": address_text,
                "delivery_location": {
                    "lat": delivery_lat,
                    "lng": delivery_lng
                },
                "total_amount": float(order.get("total_amount", 0)),
                "delivery_fee": float(order.get("delivery_fee", 0)),
                "grand_total": float(order.get("total_amount", 0)) + float(order.get("delivery_fee", 0)),
                "items_count": len(order.get("items", [])),
                "created_at": order.get("created_at"),
                "notes": order.get("notes") or ""
            })
        
        return formatted
        
    except Exception as e:
        print(f"❌ Error fetching available orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/claim")
async def claim_order(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Courier claims a ready order (atomic operation)
    Returns 200 if successful, 409 if already taken
    """
    from server import db
    from datetime import datetime, timezone
    
    try:
        courier_id = current_user["id"]
        courier_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        
        # Atomic update: only if status=ready and no courier assigned
        result = await db.orders.update_one(
            {
                "id": order_id,
                "status": "ready",
                "assigned_courier_id": None
            },
            {
                "$set": {
                    "assigned_courier_id": courier_id,
                    "courier_name": courier_name,
                    "status": "assigned",
                    "assigned_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            # Already claimed by another courier
            raise HTTPException(
                status_code=409,
                detail="Bu sipariş başka bir kurye tarafından alındı"
            )
        
        # Get full order details
        order = await db.orders.find_one({"id": order_id})
        
        # Broadcast WebSocket events
        try:
            from realtime.event_bus import broadcast_event
            
            # Notify business
            await broadcast_event(
                f"business:{order.get('business_id')}",
                {
                    "event_type": "order_assigned",
                    "order_id": order_id,
                    "courier_id": courier_id,
                    "courier_name": courier_name
                }
            )
            
            # Notify courier
            await broadcast_event(
                f"courier:{courier_id}",
                {
                    "event_type": "order_claimed",
                    "order_id": order_id,
                    "status": "assigned"
                }
            )
        except Exception as ws_error:
            print(f"⚠️ WebSocket broadcast failed: {ws_error}")
        
        # Return order details
        return {
            "success": True,
            "order_id": order_id,
            "status": "assigned",
            "message": "Sipariş başarıyla alındı"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Claim error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[TaskResponse])
async def get_courier_tasks(
    status: Optional[str] = Query(None, description="Filter by status: waiting, assigned, picked_up, delivering, delivered"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get courier tasks
    
    Filters:
    - status=waiting: Tasks waiting for courier acceptance
    - status=assigned: Tasks assigned to this courier
    - No status: All tasks for this courier
    """
    from server import db
    
    try:
        courier_id = current_user["id"]
        
        # Build query
        query = {}
        
        if status:
            if status == "waiting":
                # Waiting tasks are not assigned yet
                query["status"] = CourierTaskStatus.WAITING.value
                query["courier_id"] = None
            elif status == "assigned":
                # Assigned to this courier
                query["courier_id"] = courier_id
                query["status"] = {"$in": [
                    CourierTaskStatus.ASSIGNED.value,
                    CourierTaskStatus.PICKED_UP.value,
                    CourierTaskStatus.DELIVERING.value
                ]}
            else:
                query["status"] = status
        else:
            # Show all tasks for this courier + waiting tasks
            query = {
                "$or": [
                    {"courier_id": courier_id},
                    {"status": CourierTaskStatus.WAITING.value, "courier_id": None}
                ]
            }
        
        # Fetch tasks
        tasks = await db.courier_tasks.find(query).sort("created_at", -1).to_list(length=100)
        
        # Format response
        result = []
        for task in tasks:
            # Get restaurant name from order
            order = await db.orders.find_one({"_id": task.get("order_id")})
            restaurant_name = order.get("business_name", "") if order else ""
            
            result.append(TaskResponse(
                id=task.get("_id"),
                order_id=task.get("order_id"),
                restaurant_id=task.get("restaurant_id"),
                restaurant_name=restaurant_name,
                pickup_coords=task.get("pickup_coords", {}),
                dropoff_coords=task.get("dropoff_coords", {}),
                pickup_address=task.get("pickup_address", ""),
                dropoff_address=task.get("dropoff_address", ""),
                unit_delivery_fee=task.get("unit_delivery_fee", 0),
                status=task.get("status", ""),
                courier_id=task.get("courier_id"),
                created_at=task.get("created_at", datetime.now(timezone.utc)).isoformat()
            ))
        
        print(f"✅ Found {len(result)} tasks for courier {courier_id} (status={status})")
        return result
        
    except Exception as e:
        print(f"❌ Error fetching courier tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@router.put("/{task_id}/accept", response_model=AcceptTaskResponse)
async def accept_task(
    task_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """
    Accept a courier task
    
    Changes task status from 'waiting' to 'assigned'.
    Updates courier_id to current user.
    Publishes WebSocket events.
    """
    from server import db
    from realtime.event_bus import event_bus
    
    try:
        courier_id = current_user["id"]
        courier_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        
        # Find task
        task = await db.courier_tasks.find_one({"_id": task_id})
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Paket bulunamadı."
            )
        
        # Check if task is still waiting
        if task.get("status") != CourierTaskStatus.WAITING.value:
            current_status = task.get("status")
            if current_status == CourierTaskStatus.ASSIGNED.value and task.get("courier_id") == courier_id:
                # Already assigned to this courier
                return AcceptTaskResponse(
                    success=True,
                    message="Bu paket zaten size atanmış.",
                    task_id=task_id
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bu paket artık müsait değil. (Durum: {current_status})"
                )
        
        # Check if already assigned to another courier
        if task.get("courier_id") and task.get("courier_id") != courier_id:
            raise HTTPException(
                status_code=400,
                detail="Bu paket başka bir kurye tarafından alındı."
            )
        
        # Update task
        now = datetime.now(timezone.utc)
        
        await db.courier_tasks.update_one(
            {"_id": task_id},
            {
                "$set": {
                    "status": CourierTaskStatus.ASSIGNED.value,
                    "courier_id": courier_id,
                    "assigned_at": now,
                    "updated_at": now
                }
            }
        )
        
        print(f"✅ Task {task_id} assigned to courier {courier_id} ({courier_name})")
        
        # Publish WebSocket events
        order_id = task.get("order_id")
        business_id = task.get("business_id")
        
        try:
            # Notify business
            await event_bus.publish(f"business:{business_id}", {
                "type": "task.assigned",
                "task_id": task_id,
                "order_id": order_id,
                "courier_id": courier_id,
                "courier_name": courier_name,
                "timestamp": now.isoformat()
            })
            
            # Notify order channel
            await event_bus.publish(f"order:{order_id}", {
                "type": "task.assigned",
                "task_id": task_id,
                "courier_id": courier_id,
                "courier_name": courier_name
            })
            
            # Notify other couriers (remove from available)
            await event_bus.publish("courier:global", {
                "type": "task.assigned",
                "task_id": task_id,
                "courier_id": courier_id
            })
            
            print(f"📡 Published task.assigned events")
        except Exception as ws_error:
            print(f"⚠️ Failed to publish WebSocket events: {ws_error}")
        
        return AcceptTaskResponse(
            success=True,
            message=f"Paket başarıyla alındı!",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error accepting task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Paket kabul edilirken hata oluştu: {str(e)}"
        )
