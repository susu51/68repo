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

@router.get("/map", response_model=List[dict])
async def get_tasks_for_map(
    current_user: dict = Depends(get_courier_user)
):
    """
    Get waiting tasks grouped by business location for map display
    Returns business locations with count of waiting tasks
    """
    from server import db
    
    try:
        # Get all waiting tasks
        waiting_tasks = await db.courier_tasks.find({
            "status": CourierTaskStatus.WAITING.value,
            "courier_id": None
        }).to_list(length=None)
        
        if not waiting_tasks:
            return []
        
        # Group by restaurant_id (business_id)
        business_groups = {}
        for task in waiting_tasks:
            business_id = task.get("restaurant_id")
            if business_id:
                if business_id not in business_groups:
                    business_groups[business_id] = {
                        "business_id": business_id,
                        "business_name": task.get("restaurant_name", "İşletme"),
                        "location": task.get("pickup_coords", {}),
                        "address": task.get("pickup_address", ""),
                        "task_count": 0,
                        "task_ids": []
                    }
                business_groups[business_id]["task_count"] += 1
                business_groups[business_id]["task_ids"].append(task.get("id"))
        
        # Return as list
        return list(business_groups.values())
        
    except Exception as e:
        print(f"❌ Error fetching tasks for map: {e}")
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
