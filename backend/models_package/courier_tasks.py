"""
Courier Task Model - Phase 1
Represents a delivery task for couriers
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class CourierTaskStatus(str, Enum):
    WAITING = "waiting"  # Waiting for courier to accept
    ASSIGNED = "assigned"  # Accepted by courier
    PICKED_UP = "picked_up"  # Courier picked up from restaurant
    DELIVERING = "delivering"  # On the way to customer
    DELIVERED = "delivered"  # Delivered successfully
    CANCELLED = "cancelled"  # Cancelled

class Coordinates(BaseModel):
    lat: float
    lng: float

class CourierTask(BaseModel):
    id: str
    order_id: str
    restaurant_id: str
    business_id: str
    pickup_coords: Coordinates
    dropoff_coords: Coordinates
    pickup_address: str
    dropoff_address: str
    unit_delivery_fee: float
    status: CourierTaskStatus = CourierTaskStatus.WAITING
    courier_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class TaskCreateRequest(BaseModel):
    order_id: str
    unit_delivery_fee: float
