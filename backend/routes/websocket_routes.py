"""
Phase 3: WebSocket Routes for Real-time Communication
ws://ws/order/{order_id} and ws://ws/courier/{courier_id}
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
import jwt
import os
from websocket_manager import websocket_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])

async def get_user_from_token(token: str = Query(..., description="JWT token for authentication")):
    """Extract user info from JWT token for WebSocket authentication"""
    try:
        secret_key = os.environ.get("JWT_SECRET", "kuryecini_secret_key_2024")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        user_email = payload.get("sub")
        
        # Handle test users (same as auth_dependencies.py)
        test_users = {
            "testcustomer@example.com": {
                "id": "customer-001",
                "email": "testcustomer@example.com",
                "role": "customer"
            },
            "testkurye@example.com": {
                "id": "courier-001",
                "email": "testkurye@example.com", 
                "role": "courier"
            },
            "testbusiness@example.com": {
                "id": "business-001",
                "email": "testbusiness@example.com",
                "role": "business"
            }
        }
        
        if user_email in test_users:
            return test_users[user_email]
        
        # Try database lookup
        from server import db
        user = await db.users.find_one({"email": user_email})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "id": user.get("id", str(user.get("_id", ""))),
            "email": user["email"],
            "role": user.get("role", "customer")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/order/{order_id}")
async def websocket_order_tracking(
    websocket: WebSocket, 
    order_id: str,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for order tracking
    ws://ws/order/{order_id}?token=JWT_TOKEN
    
    Durum değişimleri + kurye snapshotları
    """
    connection_id = None
    try:
        # Authenticate user
        user_info = await get_user_from_token(token)
        
        # Verify order access permission
        from server import db
        order = await db.orders.find_one({"_id": order_id})
        
        if not order:
            await websocket.close(code=4004, reason="Order not found")
            return
        
        # Check if user has permission to track this order
        user_role = user_info.get("role")
        user_id = user_info.get("id")
        
        allowed = False
        
        if user_role == "customer" and order.get("customer_id") == user_id:
            allowed = True  # Customer can track their own orders
        elif user_role == "courier" and order.get("courier_id") == user_id:
            allowed = True  # Courier can track assigned orders
        elif user_role == "business":
            # Business can track their own orders
            business = await db.businesses.find_one({"owner_user_id": user_id})
            if business and str(business["_id"]) == order["business_id"]:
                allowed = True
        elif user_role == "admin":
            allowed = True  # Admin can track any order
        
        if not allowed:
            await websocket.close(code=4003, reason="Access denied - cannot track this order")
            return
        
        # Connect to WebSocket
        connection_id = await websocket_manager.connect_order_tracking(
            websocket, order_id, user_info
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (ping/pong or client requests)
                data = await websocket.receive_text()
                
                # Handle client requests
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "get_status":
                    # Send current order status
                    current_order = await db.orders.find_one({"_id": order_id})
                    if current_order:
                        await websocket.send_text(json.dumps({
                            "type": "order_status",
                            "order_id": order_id,
                            "status": current_order["status"],
                            "updated_at": current_order.get("updated_at", current_order["created_at"]).isoformat()
                        }))
                
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket order tracking error: {e}")
        try:
            await websocket.close(code=4000, reason=f"Server error: {str(e)}")
        except:
            pass
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

@router.websocket("/courier/{courier_id}")
async def websocket_courier_tracking(
    websocket: WebSocket,
    courier_id: str,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for courier tracking  
    ws://ws/courier/{courier_id}?token=JWT_TOKEN
    
    Kurye kendi konumunu doğrulama
    """
    connection_id = None
    try:
        # Authenticate user
        user_info = await get_user_from_token(token)
        
        # Verify courier access permission
        user_role = user_info.get("role")
        user_id = user_info.get("id")
        
        allowed = False
        
        if user_role == "courier" and user_id == courier_id:
            allowed = True  # Courier can track their own location
        elif user_role == "admin":
            allowed = True  # Admin can track any courier
        
        if not allowed:
            await websocket.close(code=4003, reason="Access denied - cannot track this courier")
            return
        
        # Connect to WebSocket
        connection_id = await websocket_manager.connect_courier_tracking(
            websocket, courier_id, user_info
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages
                data = await websocket.receive_text()
                
                # Handle client requests
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "get_location":
                    # Send current location
                    try:
                        from routes.courier_location import get_courier_location
                        # This would need to be adapted for WebSocket context
                        await websocket.send_text(json.dumps({
                            "type": "location_request_received",
                            "courier_id": courier_id,
                            "message": "Use REST API /courier/location/{courier_id} for location data"
                        }))
                    except Exception as loc_error:
                        logger.error(f"Error getting location: {loc_error}")
                
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket courier tracking error: {e}")
        try:
            await websocket.close(code=4000, reason=f"Server error: {str(e)}")
        except:
            pass
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)

@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()