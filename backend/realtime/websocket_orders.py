"""
WebSocket endpoint for real-time order notifications with heartbeat & reconnection support
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Dict, Set, Optional
import json
import asyncio
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # business_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Admin connections (receive ALL orders)
        self.admin_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, client_id: str, role: str = "business"):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        if role == "admin":
            self.admin_connections.add(websocket)
            print(f"✅ WebSocket connected: role=admin, total_admins={len(self.admin_connections)}")
        else:
            # Business connection
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            
            self.active_connections[client_id].add(websocket)
            print(f"✅ WebSocket connected: business_id={client_id}, total={len(self.active_connections[client_id])}")
    
    def disconnect(self, websocket: WebSocket, client_id: str = None, role: str = "business"):
        """Disconnect a WebSocket client"""
        if role == "admin":
            self.admin_connections.discard(websocket)
            print(f"✅ WebSocket disconnected: role=admin")
        elif client_id and client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            
            if len(self.active_connections[client_id]) == 0:
                del self.active_connections[client_id]
            
            print(f"✅ WebSocket disconnected: business_id={client_id}")
    
    async def send_to_business(self, business_id: str, message: dict):
        """Send message to all connections of a business"""
        if business_id not in self.active_connections:
            return
        
        # Make a copy to avoid modification during iteration
        connections = self.active_connections[business_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to WebSocket: {e}")
                # Remove failed connection
                self.disconnect(connection, business_id, role="business")
    
    async def send_to_admins(self, message: dict):
        """Send message to all admin connections"""
        # Make a copy to avoid modification during iteration
        connections = self.admin_connections.copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to admin WebSocket: {e}")
                # Remove failed connection
                self.admin_connections.discard(connection)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients (businesses + admins)"""
        # Send to all businesses
        for business_id in list(self.active_connections.keys()):
            await self.send_to_business(business_id, message)
        
        # Send to all admins
        await self.send_to_admins(message)
    
    def get_connection_count(self, business_id: str = None, role: str = None) -> int:
        """Get total connections or connections for a business/role"""
        if role == "admin":
            return len(self.admin_connections)
        if business_id:
            return len(self.active_connections.get(business_id, set()))
        return sum(len(conns) for conns in self.active_connections.values()) + len(self.admin_connections)

# Global connection manager
manager = ConnectionManager()

async def websocket_order_notifications(
    websocket: WebSocket,
    business_id: str = Query(None, description="Business ID to subscribe to (for businesses)"),
    role: str = Query("business", description="Role: 'business' or 'admin'"),
    token: Optional[str] = Query(None, description="Optional JWT token for authentication")
):
    """
    WebSocket endpoint for real-time order notifications with heartbeat support
    Business: wss://domain/api/ws/orders?business_id={business_id}&role=business&token={token}
    Admin: wss://domain/api/ws/orders?role=admin&token={token}
    
    Heartbeat: Client sends ping every 25s, server responds with pong
    Timeout: Connection closes after 75s of inactivity (proxy compatibility)
    """
    client_id = business_id if role == "business" else "admin"
    
    # Validate parameters
    if role == "business" and not business_id:
        await websocket.close(code=1008, reason="business_id is required for business role")
        return
    
    # TODO: Add token validation if needed
    # if token:
    #     try:
    #         validate_token(token)
    #     except Exception as e:
    #         await websocket.close(code=1008, reason="Invalid token")
    #         return
    
    await manager.connect(websocket, client_id, role)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "role": role,
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Sipariş bildirimleri aktif" if role == "business" else "Admin sipariş takibi aktif"
        })
        
        # Subscribe to event bus
        try:
            from realtime.event_bus import event_bus
            
            async def on_order_event(data: dict):
                """Callback for order events"""
                try:
                    if role == "admin":
                        # Admin receives all orders
                        await manager.send_to_admins({
                            "type": "order_notification",
                            "data": data
                        })
                    else:
                        # Business receives only their orders
                        await manager.send_to_business(business_id, {
                            "type": "order_notification",
                            "data": data
                        })
                except Exception as e:
                    print(f"❌ Error in order event callback: {e}")
            
            # Subscribe to appropriate topic
            if role == "admin":
                # Subscribe to all order events
                await event_bus.subscribe("orders:all", on_order_event)
                print(f"✅ Admin subscribed to orders:all topic")
            else:
                # Subscribe to business-specific topic
                await event_bus.subscribe(f"business:{business_id}", on_order_event)
                print(f"✅ Business {business_id} subscribed to business:{business_id} topic")
        except Exception as e:
            print(f"❌ Error subscribing to event bus: {e}")
            # Don't close connection - keep it alive even if subscription fails
            await websocket.send_json({
                "type": "error",
                "message": "Event subscription failed, but connection maintained"
            })
        
        # Keep connection alive with heartbeat monitoring
        logger.info(f"🔄 Entering message loop for {role}:{client_id}")
        last_message_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Wait for messages with 75s timeout (proxy-compatible)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=75.0
                )
                
                last_message_time = asyncio.get_event_loop().time()
                logger.debug(f"📨 Received message from {role}:{client_id}: {data[:100]}")
                
                # Handle different message types
                if data == "ping":
                    await websocket.send_text("pong")
                    logger.debug(f"🏓 Sent pong to {role}:{client_id}")
                elif data.startswith("{"):
                    # JSON message - parse and handle
                    try:
                        msg_data = json.loads(data)
                        
                        # Handle subscribe message (for re-subscription after reconnect)
                        if msg_data.get("type") == "subscribe":
                            logger.info(f"📡 Re-subscription request from {role}:{client_id}")
                            await websocket.send_json({
                                "type": "subscribed",
                                "role": role,
                                "client_id": client_id,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Invalid JSON from {role}:{client_id}: {data[:100]}")
                    
            except asyncio.TimeoutError:
                # 75s timeout - check if client is still responsive
                current_time = asyncio.get_event_loop().time()
                idle_time = current_time - last_message_time
                
                if idle_time > 90:
                    # Client hasn't sent anything in 90s (including ping) - close connection
                    logger.warning(f"⏱️ Idle timeout for {role}:{client_id} ({idle_time:.0f}s)")
                    await websocket.close(code=1000, reason="Idle timeout")
                    break
                else:
                    # Normal timeout - continue waiting
                    continue
                    
            except WebSocketDisconnect:
                logger.info(f"🔌 Client disconnected normally: {role}:{client_id}")
                break
            except Exception as loop_error:
                logger.error(f"❌ Error in message loop for {role}:{client_id}: {loop_error}")
                break
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, role)
        logger.info(f"🔌 Client disconnected normally: role={role}, client_id={client_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {role}:{client_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(websocket, client_id, role)
        
        # Close with appropriate code
        try:
            if isinstance(e, asyncio.TimeoutError):
                await websocket.close(code=1000, reason="Timeout")
            else:
                await websocket.close(code=1011, reason="Server error")
        except:
            pass
