"""
Phase 3: WebSocket Manager for Real-time Updates
Canlı yayın (tercih WS, fallback SSE)
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Order tracking connections: order_id -> set of websocket_ids
        self.order_subscribers: Dict[str, Set[str]] = {}
        
        # Courier tracking connections: courier_id -> set of websocket_ids  
        self.courier_subscribers: Dict[str, Set[str]] = {}
        
        # WebSocket ID to user info mapping
        self.connection_info: Dict[str, dict] = {}

    async def connect_order_tracking(self, websocket: WebSocket, order_id: str, user_info: dict):
        """Connect to order tracking channel: ws://ws/order/{order_id}"""
        try:
            await websocket.accept()
            
            # Generate unique connection ID
            connection_id = str(uuid.uuid4())
            
            # Store connection
            self.active_connections[connection_id] = websocket
            self.connection_info[connection_id] = {
                "type": "order_tracking",
                "order_id": order_id,
                "user_id": user_info.get("id"),
                "user_role": user_info.get("role"),
                "connected_at": datetime.now(timezone.utc)
            }
            
            # Add to order subscribers
            if order_id not in self.order_subscribers:
                self.order_subscribers[order_id] = set()
            self.order_subscribers[order_id].add(connection_id)
            
            logger.info(f"🔌 ORDER WS CONNECTED: {connection_id} tracking order {order_id} by {user_info.get('role')} {user_info.get('id')}")
            
            # Send initial order status
            await self.send_order_status_update(order_id, {
                "type": "connection_established",
                "order_id": order_id,
                "message": "Connected to order tracking",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ Error connecting to order tracking: {e}")
            raise

    async def connect_courier_tracking(self, websocket: WebSocket, courier_id: str, user_info: dict):
        """Connect to courier tracking channel: ws://ws/courier/{courier_id}"""
        try:
            await websocket.accept()
            
            # Generate unique connection ID
            connection_id = str(uuid.uuid4())
            
            # Store connection
            self.active_connections[connection_id] = websocket
            self.connection_info[connection_id] = {
                "type": "courier_tracking", 
                "courier_id": courier_id,
                "user_id": user_info.get("id"),
                "user_role": user_info.get("role"),
                "connected_at": datetime.now(timezone.utc)
            }
            
            # Add to courier subscribers
            if courier_id not in self.courier_subscribers:
                self.courier_subscribers[courier_id] = set()
            self.courier_subscribers[courier_id].add(connection_id)
            
            logger.info(f"🔌 COURIER WS CONNECTED: {connection_id} tracking courier {courier_id} by {user_info.get('role')} {user_info.get('id')}")
            
            # Send initial connection confirmation
            await self.send_courier_update(courier_id, {
                "type": "connection_established",
                "courier_id": courier_id,
                "message": "Connected to courier tracking",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ Error connecting to courier tracking: {e}")
            raise

    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket and clean up"""
        try:
            if connection_id in self.active_connections:
                connection_info = self.connection_info.get(connection_id, {})
                
                # Remove from subscribers
                if connection_info.get("type") == "order_tracking":
                    order_id = connection_info.get("order_id")
                    if order_id and order_id in self.order_subscribers:
                        self.order_subscribers[order_id].discard(connection_id)
                        if not self.order_subscribers[order_id]:
                            del self.order_subscribers[order_id]
                
                elif connection_info.get("type") == "courier_tracking":
                    courier_id = connection_info.get("courier_id")
                    if courier_id and courier_id in self.courier_subscribers:
                        self.courier_subscribers[courier_id].discard(connection_id)
                        if not self.courier_subscribers[courier_id]:
                            del self.courier_subscribers[courier_id]
                
                # Clean up connection
                del self.active_connections[connection_id]
                del self.connection_info[connection_id]
                
                logger.info(f"🔌 WS DISCONNECTED: {connection_id}")
                
        except Exception as e:
            logger.error(f"❌ Error disconnecting WebSocket: {e}")

    async def send_order_status_update(self, order_id: str, data: dict):
        """
        Broadcast order status update to all subscribers
        Durum değişimleri + kurye snapshotları
        """
        if order_id not in self.order_subscribers:
            return
        
        message = {
            "channel": "order_status",
            "order_id": order_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        
        # Send to all order subscribers
        disconnected = []
        for connection_id in self.order_subscribers[order_id].copy():
            try:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    await websocket.send_text(json.dumps(message))
                    logger.info(f"📡 ORDER UPDATE SENT: {order_id} to {connection_id}")
                else:
                    disconnected.append(connection_id)
            except Exception as e:
                logger.error(f"❌ Error sending order update to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def send_courier_update(self, courier_id: str, data: dict):
        """
        Broadcast courier update (location, status) to subscribers
        Kurye kendi konumunu doğrulama + müşteri tracking
        """
        if courier_id not in self.courier_subscribers:
            return
        
        message = {
            "channel": "courier_location",
            "courier_id": courier_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        
        # Send to all courier subscribers
        disconnected = []
        for connection_id in self.courier_subscribers[courier_id].copy():
            try:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    await websocket.send_text(json.dumps(message))
                    logger.info(f"📡 COURIER UPDATE SENT: {courier_id} to {connection_id}")
                else:
                    disconnected.append(connection_id)
            except Exception as e:
                logger.error(f"❌ Error sending courier update to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def send_courier_location_to_order_subscribers(self, order_id: str, courier_location: dict):
        """
        Send courier location updates to order tracking subscribers
        Sipariş takip eden müşteriler kurye konumunu görür
        """
        await self.send_order_status_update(order_id, {
            "type": "courier_location_update",
            "courier_location": courier_location
        })

    def get_connection_stats(self):
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "order_tracking_channels": len(self.order_subscribers),
            "courier_tracking_channels": len(self.courier_subscribers),
            "active_order_subscribers": sum(len(subs) for subs in self.order_subscribers.values()),
            "active_courier_subscribers": sum(len(subs) for subs in self.courier_subscribers.values())
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()