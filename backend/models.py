"""
MongoDB Data Models for Kuryecini
All persistent data structures for localStorage migration
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

def generate_id() -> str:
    """Generate unique ID for documents"""
    return str(uuid.uuid4())

class ResetTokenStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"

class PasswordReset(BaseModel):
    """Password reset token document"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    token: str
    status: ResetTokenStatus = ResetTokenStatus.ACTIVE
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used_at: Optional[datetime] = None

class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Request model for password reset"""
    token: str
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Parola en az 8 karakter olmalıdır')
        if not any(c.isdigit() for c in v):
            raise ValueError('Parola en az bir rakam içermelidir')
        if not any(c.isalpha() for c in v):
            raise ValueError('Parola en az bir harf içermelidir')
        return v

def generate_id() -> str:
    """Generate unique ID for documents"""
    return str(uuid.uuid4())

class UserRole(str, Enum):
    CUSTOMER = "customer"
    COURIER = "courier"
    BUSINESS = "business"
    ADMIN = "admin"

class User(BaseModel):
    """User document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    role: UserRole
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    loyalty_points: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Auth fields
    password_hash: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    
    # Additional profile fields
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+90'):
            v = f"+90{v.lstrip('+').lstrip('90').lstrip('0')}"
        return v
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Address(BaseModel):
    """Address document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    label: str  # "Ev", "İş", "Diğer"
    full_address: str
    city: str
    district: Optional[str] = None
    loc: Dict[str, float]  # {"lat": 41.0082, "lng": 28.9784}
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    @validator('loc')
    def validate_location(cls, v):
        if 'lat' not in v or 'lng' not in v:
            raise ValueError('Location must have lat and lng keys')
        return v
    
    class Config:
        populate_by_name = True

class CartItem(BaseModel):
    """Cart item model"""
    product_id: str
    qty: int = Field(ge=1)
    price: Optional[float] = None  # Server-validated price
    product_name: Optional[str] = None  # Cached for display

class Cart(BaseModel):
    """Cart document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    items: List[CartItem] = []
    city: Optional[str] = None  # For delivery validation
    business_id: Optional[str] = None  # Lock cart to specific business
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderTotals(BaseModel):
    """Order financial totals"""
    gross: float = Field(ge=0)
    delivery_fee: float = Field(default=0, ge=0)
    service_fee: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)
    net: float = Field(ge=0)
    commission: float = Field(default=0, ge=0)  # Platform commission

class RoutePoint(BaseModel):
    """Route waypoint"""
    lat: float
    lng: float
    address: str
    timestamp: Optional[datetime] = None

class Order(BaseModel):
    """Order document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    order_number: str = Field(default_factory=lambda: f"KUR{int(datetime.now().timestamp())}")
    
    # Participants
    customer_id: str
    business_id: str
    courier_id: Optional[str] = None
    
    # Items and pricing
    items: List[CartItem]
    totals: OrderTotals
    
    # Status and tracking
    status: OrderStatus = OrderStatus.PENDING
    route: List[RoutePoint] = []
    
    # Delivery information
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    customer_phone: str
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Additional fields
    notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    
    class Config:
        populate_by_name = True

class NotificationPreferences(BaseModel):
    """Notification preferences model"""
    sms: bool = True
    email: bool = True
    push: bool = True

class MarketingPreferences(BaseModel):
    """Marketing preferences model"""
    city: Optional[str] = None
    categories: List[str] = []
    allow_promotional: bool = True

class UserPreferences(BaseModel):
    """User preferences document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    notifications: NotificationPreferences = NotificationPreferences()
    marketing: MarketingPreferences = MarketingPreferences()
    theme: str = "auto"  # "light", "dark", "auto"
    language: str = "tr"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class BannerTargeting(BaseModel):
    """Banner targeting criteria"""
    cities: List[str] = []
    user_roles: List[UserRole] = []
    age_range: Optional[Dict[str, int]] = None  # {"min": 18, "max": 65}

class BannerSchedule(BaseModel):
    """Banner schedule model"""
    start_date: datetime
    end_date: datetime
    active_hours: Optional[Dict[str, str]] = None  # {"start": "09:00", "end": "22:00"}

class Banner(BaseModel):
    """Banner document model"""
    id: str = Field(default_factory=generate_id, alias="_id")
    title: str
    img_url: str
    target_url: Optional[str] = None
    targeting: BannerTargeting = BannerTargeting()
    schedule: BannerSchedule
    active: bool = True
    order: int = 0  # Display order
    clicks: int = 0
    impressions: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class CourierReportTotals(BaseModel):
    """Courier monthly report totals"""
    order_count: int = 0
    gross_earnings: float = 0.0
    commission: float = 0.0
    net_earnings: float = 0.0
    distance_km: float = 0.0
    average_delivery_time: float = 0.0  # minutes

class CourierReport(BaseModel):
    """Courier monthly report document"""
    id: str = Field(default_factory=generate_id, alias="_id")
    courier_id: str
    month: str  # Format: "YYYY-MM"
    totals: CourierReportTotals
    pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class LoyaltyTransaction(BaseModel):
    """Loyalty points transaction"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    points: int  # Positive for earning, negative for spending
    transaction_type: str  # "order_reward", "referral", "spend", "expire"
    reference_id: Optional[str] = None  # Order ID, referral ID, etc.
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

# Migration models for localStorage data
class MigrationData(BaseModel):
    """Model for localStorage migration data"""
    cart: Optional[List[Dict[str, Any]]] = None
    addresses: Optional[List[Dict[str, Any]]] = None
    preferences: Optional[Dict[str, Any]] = None
    loyalty_points: Optional[int] = None

class MigrationStatus(BaseModel):
    """Track migration status per user"""
    id: str = Field(default_factory=generate_id, alias="_id")
    user_id: str
    migrated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_types: List[str] = []  # ["cart", "addresses", "preferences"]
    
    class Config:
        populate_by_name = True

# MongoDB collection names
COLLECTION_NAMES = {
    "users": "users",
    "addresses": "addresses", 
    "carts": "carts",
    "orders": "orders",
    "preferences": "user_preferences",
    "banners": "banners",
    "courier_reports": "courier_reports",
    "loyalty_transactions": "loyalty_transactions",
    "migration_status": "migration_status"
}

# Indexes for optimal performance
MONGODB_INDEXES = {
    "users": [
        {"email": 1},
        {"phone": 1},
        {"role": 1}
    ],
    "addresses": [
        {"user_id": 1},
        {"user_id": 1, "is_default": -1}
    ],
    "carts": [
        {"user_id": 1}
    ],
    "orders": [
        {"customer_id": 1, "created_at": -1},
        {"business_id": 1, "created_at": -1},
        {"courier_id": 1, "created_at": -1},
        {"status": 1},
        {"order_number": 1}
    ],
    "preferences": [
        {"user_id": 1}
    ],
    "banners": [
        {"active": 1, "order": 1},
        {"schedule.start_date": 1, "schedule.end_date": 1}
    ],
    "courier_reports": [
        {"courier_id": 1, "month": -1}
    ],
    "loyalty_transactions": [
        {"user_id": 1, "created_at": -1}
    ],
    "migration_status": [
        {"user_id": 1}
    ]
}