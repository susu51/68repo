"""
WebSocket endpoint for real-time order notifications
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import json
from datetime import datetime, timezone

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
    role: str = Query("business", description="Role: 'business' or 'admin'")
):
    """
    WebSocket endpoint for real-time order notifications
    Business: ws://domain/api/ws/orders?business_id={business_id}&role=business
    Admin: ws://domain/api/ws/orders?role=admin
    """
    client_id = business_id if role == "business" else "admin"
    
    # Validate parameters
    if role == "business" and not business_id:
        await websocket.close(code=1008, reason="business_id is required for business role")
        return
    
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
        from realtime.event_bus import event_bus
        
        async def on_order_event(data: dict):
            """Callback for order events"""
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
        
        # Subscribe to appropriate topic
        if role == "admin":
            # Subscribe to all order events
            await event_bus.subscribe("orders:all", on_order_event)
        else:
            # Subscribe to business-specific topic
            await event_bus.subscribe(f"business:{business_id}", on_order_event)
        
        # Keep connection alive
        while True:
            # Wait for ping/pong or client messages
            data = await websocket.receive_text()
            
            # Echo back for keepalive
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, role)
        print(f"Client disconnected: role={role}, client_id={client_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket, client_id, role)
