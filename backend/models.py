"""
MongoDB Data Models for Kuryecini
All persistent data structures for localStorage migration
"""

"""
MongoDB Collections and Models for Kuryecini Platform
Real Database Schema - No Mock Data
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    PREPARING = "preparing" 
    READY = "ready"
    READY_FOR_PICKUP = "ready_for_pickup"  # Phase 1: For courier map
    COURIER_PENDING = "courier_pending"
    COURIER_ASSIGNED = "courier_assigned"
    PICKED_UP = "picked_up"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    CUSTOMER = "customer"
    BUSINESS = "business"  
    COURIER = "courier"
    ADMIN = "admin"

# MongoDB Collections Schema Definitions

class BusinessLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lng, lat]

class Business(BaseModel):
    owner_user_id: str
    name: str
    address: str
    city: str  # Required for location-based filtering
    district: str  # Required for location-based filtering
    location: BusinessLocation
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MenuItem(BaseModel):
    business_id: str
    title: str
    description: str
    price: float
    is_available: bool = True
    photo_url: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    menu_item_id: str
    qty: int
    unit_price: float

class OrderTotals(BaseModel):
    subtotal: float
    commission_business_pct: float
    courier_earning: float
    grand_total: float

class DeliveryLocation(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lng, lat]

class OrderDelivery(BaseModel):
    address: str
    location: DeliveryLocation

class StatusHistory(BaseModel):
    status: OrderStatus
    at: datetime
    by_role: UserRole
    by_user_id: str

class Order(BaseModel):
    customer_id: str
    business_id: str
    courier_id: Optional[str] = None
    items: List[OrderItem]
    totals: OrderTotals
    delivery: OrderDelivery
    status: OrderStatus = OrderStatus.CREATED
    status_history: List[StatusHistory] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CourierLocationPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lng, lat]

class CourierLocation(BaseModel):
    courier_id: str
    point: CourierLocationPoint
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy: Optional[float] = None
    ts: int  # timestamp in milliseconds
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GlobalSettings(BaseModel):
    _id: str = "global"
    courier_rate_per_package: float = 20.0
    business_commission_pct: float = 5.0
    nearby_radius_m: int = 5000
    courier_update_sec: int = 5
    courier_timeout_sec: int = 10
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

class Earning(BaseModel):
    courier_id: str
    order_id: str
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

# MongoDB Index Definitions
INDEXES = {
    "businesses": [
        {"location": "2dsphere"},  # Geospatial queries
        {"owner_user_id": 1},
        {"is_active": 1}
    ],
    "menu_items": [
        {"business_id": 1},
        {"is_available": 1},
        {"business_id": 1, "is_available": 1}
    ],
    "orders": [
        {"customer_id": 1},
        {"business_id": 1}, 
        {"courier_id": 1},
        {"status": 1},
        {"created_at": -1},
        {"business_id": 1, "status": 1},
        {"courier_id": 1, "status": 1}
    ],
    "courier_locations": [
        {"courier_id": 1, "ts": -1},  # Latest first
        {"point": "2dsphere"},  # Geospatial queries
        {"created_at": -1}  # TTL index potential
    ],
    "earnings": [
        {"courier_id": 1},
        {"order_id": 1},
        {"created_at": -1}
    ]
}

# Status Transition Rules
STATUS_TRANSITIONS = {
    OrderStatus.CREATED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.COURIER_PENDING, OrderStatus.CANCELLED],
    OrderStatus.COURIER_PENDING: [OrderStatus.COURIER_ASSIGNED, OrderStatus.CANCELLED],
    OrderStatus.COURIER_ASSIGNED: [OrderStatus.PICKED_UP, OrderStatus.COURIER_PENDING],
    OrderStatus.PICKED_UP: [OrderStatus.DELIVERING],
    OrderStatus.DELIVERING: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],  # Terminal state
    OrderStatus.CANCELLED: []   # Terminal state
}

# Role-based transition permissions
ROLE_TRANSITIONS = {
    UserRole.BUSINESS: {
        OrderStatus.CREATED: [OrderStatus.PREPARING],
        OrderStatus.PREPARING: [OrderStatus.READY],
        OrderStatus.READY: [OrderStatus.COURIER_PENDING]
    },
    UserRole.COURIER: {
        OrderStatus.COURIER_PENDING: [OrderStatus.COURIER_ASSIGNED],
        OrderStatus.COURIER_ASSIGNED: [OrderStatus.PICKED_UP],
        OrderStatus.PICKED_UP: [OrderStatus.DELIVERING],
        OrderStatus.DELIVERING: [OrderStatus.DELIVERED]
    },
    UserRole.ADMIN: {
        # Admin can transition between any valid states
        **STATUS_TRANSITIONS
    }
}

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

# PRODUCTION DATA MODELS - NO localStorage MIGRATION

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


# ==================== ADMIN PANEL MODELS ====================

class ContentBlockType(str, Enum):
    """Content block types for CMS"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    CTA = "cta"

class ContentBlock(BaseModel):
    """Content block for CMS"""
    id: str = Field(default_factory=generate_id, alias="_id")
    page: str  # "dashboard", "landing", "about"
    section: str  # "hero", "features", "testimonials"
    type: ContentBlockType
    content: Dict[str, Any]  # Flexible content structure
    order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True

class AdBoardCTA(BaseModel):
    """Call-to-action for ad board"""
    text: str
    href: str

class AdBoard(BaseModel):
    """Advertisement board/banner"""
    id: str = Field(default_factory=generate_id, alias="_id")
    title: str
    subtitle: Optional[str] = None
    image: str  # URL or file path
    cta: Optional[AdBoardCTA] = None
    order: int = 0  # Display order (lower = higher priority)
    is_active: bool = True
    impressions: int = 0
    clicks: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True

class PromotionTarget(str, Enum):
    """Promotion target type"""
    ALL = "all"
    BUSINESS = "business"
    CUSTOMER = "customer"

class Promotion(BaseModel):
    """Promotion/Coupon code"""
    id: str = Field(default_factory=generate_id, alias="_id")
    code: str  # Coupon code (e.g., "KUPON10")
    title: str
    description: str
    discount_pct: float = Field(ge=0, le=100)  # Percentage discount
    discount_amount: Optional[float] = Field(None, ge=0)  # Fixed discount
    target: PromotionTarget = PromotionTarget.ALL
    target_id: Optional[str] = None  # business_id if target=BUSINESS
    min_order: float = Field(default=0, ge=0)  # Minimum order amount
    usage_limit: Optional[int] = Field(None, ge=1)  # Total usage limit
    usage_per_user: int = Field(default=1, ge=1)  # Per user limit
    used_count: int = 0
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True

class PromotionUsage(BaseModel):
    """Track promotion usage"""
    id: str = Field(default_factory=generate_id, alias="_id")
    promotion_id: str
    user_id: str
    order_id: str
    discount_applied: float
    used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class MessageRecipientType(str, Enum):
    """Message recipient type"""
    COURIER = "courier"
    BUSINESS = "business"
    CUSTOMER = "customer"
    ALL_COURIERS = "all_couriers"
    ALL_BUSINESSES = "all_businesses"

class MessageStatus(str, Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"

class Message(BaseModel):
    """Admin to Courier/Business messaging"""
    id: str = Field(default_factory=generate_id, alias="_id")
    sender_type: str = "admin"  # Always admin for now
    sender_id: str  # Admin user ID
    recipient_type: MessageRecipientType
    recipient_id: Optional[str] = None  # null for broadcast messages
    subject: str
    message: str
    status: MessageStatus = MessageStatus.SENT
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

# Update collection names
COLLECTION_NAMES.update({
    "content_blocks": "content_blocks",
    "ad_boards": "ad_boards",
    "promotions": "promotions",
    "promotion_usage": "promotion_usage",
    "messages": "messages"
})

# Update indexes
MONGODB_INDEXES.update({
    "content_blocks": [
        {"page": 1, "section": 1, "order": 1},
        {"is_active": 1}
    ],
    "ad_boards": [
        {"is_active": 1, "order": 1}
    ],
    "promotions": [
        {"code": 1},
        {"is_active": 1},
        {"start_date": 1, "end_date": 1},
        {"target": 1, "target_id": 1}
    ],
    "promotion_usage": [
        {"promotion_id": 1, "user_id": 1},
        {"order_id": 1}
    ],
    "messages": [
        {"recipient_type": 1, "recipient_id": 1, "created_at": -1},
        {"is_read": 1}
    ]
})
