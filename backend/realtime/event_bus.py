"""
Real-time Event Bus for Order Notifications
Simple in-memory pub/sub for MVP (can be upgraded to Redis later)
"""
from typing import Dict, List, Callable, Any
import asyncio
from datetime import datetime, timezone
import json

class EventBus:
    """Simple event bus for real-time notifications"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)
            print(f"✅ Subscribed to topic: {topic}")
    
    async def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        async with self._lock:
            if topic in self._subscribers:
                try:
                    self._subscribers[topic].remove(callback)
                    print(f"✅ Unsubscribed from topic: {topic}")
                except ValueError:
                    pass
    
    async def publish(self, topic: str, data: Dict[str, Any]):
        """Publish event to all subscribers"""
        print(f"📡 Publishing to topic '{topic}': {data.get('event_type', 'unknown')}")
        
        async with self._lock:
            subscribers = self._subscribers.get(topic, []).copy()
        
        # Call all subscribers asynchronously
        tasks = []
        for callback in subscribers:
            try:
                task = asyncio.create_task(callback(data))
                tasks.append(task)
            except Exception as e:
                print(f"❌ Error calling subscriber: {e}")
        
        # Wait for all callbacks (with timeout)
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                print(f"⚠️ Some subscribers timed out for topic: {topic}")
        
        print(f"✅ Published to {len(subscribers)} subscribers on topic '{topic}'")
    
    def get_topics(self) -> List[str]:
        """Get all active topics"""
        return list(self._subscribers.keys())
    
    def get_subscriber_count(self, topic: str) -> int:
        """Get subscriber count for a topic"""
        return len(self._subscribers.get(topic, []))

# Global event bus instance
event_bus = EventBus()

# Helper functions for order events
async def publish_order_created(order_id: str, restaurant_id: str, business_id: str, order_data: Dict = None):
    """Publish order created event"""
    event = {
        "event_type": "order.created",
        "order_id": order_id,
        "restaurant_id": restaurant_id,
        "business_id": business_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": order_data or {}
    }
    
    # Publish to multiple topics
    await event_bus.publish(f"business:{business_id}", event)
    await event_bus.publish(f"restaurant:{restaurant_id}", event)
    await event_bus.publish("orders:all", event)

async def publish_order_status_changed(order_id: str, old_status: str, new_status: str, business_id: str = None):
    """Publish order status change event"""
    event = {
        "event_type": "order.status_changed",
        "order_id": order_id,
        "old_status": old_status,
        "new_status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await event_bus.publish("orders:all", event)
    if business_id:
        await event_bus.publish(f"business:{business_id}", event)
