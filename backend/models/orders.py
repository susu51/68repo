"""
Enhanced Order Models for Kuryecini Platform
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    CASH = "cash"
    POS = "pos"
    ONLINE_MOCK = "online_mock"

class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID_MOCK = "paid_mock"
    PAID = "paid"

class AddressSnapshot(BaseModel):
    """Snapshot of delivery address at order time"""
    full: str
    city: Optional[str] = None
    district: Optional[str] = None
    neighborhood: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class ItemSnapshot(BaseModel):
    """Snapshot of menu item at order time"""
    id: str
    name: str
    price: float
    quantity: int
    notes: Optional[str] = None
    
    @property
    def subtotal(self) -> float:
        return self.price * self.quantity

class OrderTotals(BaseModel):
    """Order financial totals"""
    sub: float = Field(description="Subtotal (items only)")
    delivery: float = Field(default=0, description="Delivery fee")
    discount: float = Field(default=0, description="Discount amount")
    grand: float = Field(description="Grand total")
    
    @validator('grand', always=True)
    def calculate_grand_total(cls, v, values):
        if v is None or v == 0:
            return values.get('sub', 0) + values.get('delivery', 0) - values.get('discount', 0)
        return v

class TimelineEvent(BaseModel):
    """Order timeline event"""
    event: str  # created, confirmed, preparing, etc.
    at: datetime
    meta: Optional[Dict[str, Any]] = {}

class OrderCreate(BaseModel):
    """Schema for creating a new order"""
    restaurant_id: str = Field(description="Restaurant/Business ID")
    address_id: str = Field(description="Customer's delivery address ID")
    items: List[Dict[str, Any]] = Field(description="Cart items with id, quantity, notes")
    payment_method: PaymentMethod = PaymentMethod.CASH
    special_instructions: Optional[str] = None
    
    @validator('items')
    def validate_items_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Sepet boş olamaz")
        return v

class OrderResponse(BaseModel):
    """Order response model"""
    id: str
    user_id: str
    customer_name: str
    restaurant_id: str
    business_id: str
    business_name: Optional[str] = None
    address_snapshot: AddressSnapshot
    items_snapshot: List[ItemSnapshot]
    totals: OrderTotals
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    status: OrderStatus
    timeline: List[TimelineEvent]
    courier_id: Optional[str] = None
    eta: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    special_instructions: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    """Schema for updating order status"""
    status: OrderStatus
    note: Optional[str] = None
