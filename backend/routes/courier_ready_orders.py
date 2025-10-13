"""
Courier Ready Orders - Real-time map system
GET endpoint for initial load + WebSocket for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import json
from auth_dependencies import get_courier_user
from pydantic import BaseModel

router = APIRouter(prefix="/courier", tags=["courier-ready-orders"])

class ReadyOrderResponse(BaseModel):
    id: str
    business_id: str
    business_name: str
    business_address: str
    business_location: Dict[str, Any]  # {lat, lng}
    items_count: int
    total_amount: float
    delivery_address: Dict[str, Any]
    city: str
    estimated_time: str
    created_at: datetime

# Store active WebSocket connections for couriers
active_courier_connections: Dict[str, List[WebSocket]] = {}

@router.get("/orders/ready", response_model=List[ReadyOrderResponse])
async def get_ready_orders(
    city: Optional[str] = Query(None, description="Filter by city"),
    current_user: dict = Depends(get_courier_user)
):
    """
    Get orders with status='ready_for_pickup' for courier map
    Initial load endpoint (polling fallback: call every 10s)
    """
    try:
        from server import db
        
        courier_city = current_user.get('city', '')
        
        # Build query - only ready_for_pickup orders
        query = {"status": "ready_for_pickup"}
        
        # City filter (same city restriction)
        if city:
            query["city"] = city
        elif courier_city:
            query["city"] = courier_city
        
        # Fetch ready orders
        orders = await db.orders.find(query).sort("created_at", 1).to_list(length=None)
        
        # Enrich with business info
        ready_orders = []
        for order in orders:
            business_id = order.get('business_id')
            if not business_id:
                continue
            
            business = await db.businesses.find_one({"_id": business_id})
            if not business:
                continue
            
            # Get business location
            business_location = business.get('location', {})
            if business_location:
                coords = business_location.get('coordinates', [0, 0])
                business_loc = {"lng": coords[0], "lat": coords[1]}
            else:
                business_loc = {"lng": 0, "lat": 0}
            
            # Calculate estimated time (5-10 minutes for preparation)
            created_at = order.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            ready_orders.append(ReadyOrderResponse(
                id=str(order["_id"]),
                business_id=business_id,
                business_name=business.get('name', 'Bilinmiyor'),
                business_address=business.get('address', ''),
                business_location=business_loc,
                items_count=len(order.get('items', [])),
                total_amount=order.get('total_amount', 0),
                delivery_address=order.get('delivery_address', {}),
                city=order.get('city', ''),
                estimated_time="5-10 dakika",
                created_at=created_at
            ))
        
        return ready_orders
        
    except Exception as e:
        print(f"❌ Error fetching ready orders: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Hazır siparişler alınamadı: {str(e)}"
        )

@router.websocket("/ws/ready")
async def websocket_ready_orders(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time ready order updates
    ws://localhost:8001/api/courier/ws/ready?token=JWT_TOKEN
    
    Broadcasts when:
    - Order status changes to 'ready_for_pickup'
    - Order is accepted by another courier (removed from ready list)
    """
    courier_id = None
    try:
        # Authenticate courier
        import jwt
        import os
        
        try:
            secret_key = os.environ.get("JWT_SECRET", "kuryecini_secret_key_2024")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_email = payload.get("sub")
            
            from server import db
            user = await db.users.find_one({"email": user_email, "role": "courier"})
            
            if not user:
                await websocket.close(code=4003, reason="Not a courier")
                return
            
            courier_id = str(user.get("_id", user.get("id", "")))
            courier_city = user.get('city', '')
            
        except Exception as auth_error:
            print(f"⚠️ WebSocket auth failed: {auth_error}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Store connection
        if courier_id not in active_courier_connections:
            active_courier_connections[courier_id] = []
        active_courier_connections[courier_id].append(websocket)
        
        print(f"✅ Courier {courier_id} connected to ready orders WebSocket")
        
        # Send initial ready orders
        from server import db
        query = {"status": "ready_for_pickup"}
        if courier_city:
            query["city"] = courier_city
        
        initial_orders = await db.orders.find(query).to_list(length=None)
        
        await websocket.send_json({
            "type": "initial",
            "count": len(initial_orders),
            "orders": [{"id": str(o["_id"]), "business_id": o.get("business_id")} for o in initial_orders]
        })
        
        # Keep connection alive and listen for updates
        try:
            while True:
                # Wait for messages from client (ping/pong for keep-alive)
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                
        except WebSocketDisconnect:
            print(f"📴 Courier {courier_id} disconnected from ready orders WebSocket")
        
    except Exception as e:
        print(f"❌ WebSocket error for courier {courier_id}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Remove connection
        if courier_id and courier_id in active_courier_connections:
            if websocket in active_courier_connections[courier_id]:
                active_courier_connections[courier_id].remove(websocket)
            if not active_courier_connections[courier_id]:
                del active_courier_connections[courier_id]

async def broadcast_ready_order_update(order_id: str, event_type: str, order_data: Optional[Dict] = None):
    """
    Broadcast ready order updates to all connected couriers
    
    event_type: 'new_ready' | 'order_accepted' | 'order_cancelled'
    """
    if not active_courier_connections:
        return
    
    message = {
        "type": event_type,
        "order_id": order_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": order_data or {}
    }
    
    # Send to all connected couriers
    disconnected = []
    for courier_id, connections in active_courier_connections.items():
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"⚠️ Failed to send to courier {courier_id}: {e}")
                disconnected.append((courier_id, ws))
    
    # Clean up disconnected connections
    for courier_id, ws in disconnected:
        if courier_id in active_courier_connections and ws in active_courier_connections[courier_id]:
            active_courier_connections[courier_id].remove(ws)
            if not active_courier_connections[courier_id]:
                del active_courier_connections[courier_id]

# Export broadcast function for use in other modules
__all__ = ['router', 'broadcast_ready_order_update']
