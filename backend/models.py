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

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_type: str
    user_data: dict

class OTPResponse(BaseModel):
    success: bool
    message: str
    otp_id: Optional[str] = None
    expires_in: Optional[int] = None
    formatted_phone: Optional[str] = None
    mock_otp: Optional[str] = None  # Only in development mode
    retry_after: Optional[int] = None
    error_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    phone: str
    email: Optional[str]
    role: UserRole
    first_name: Optional[str]
    last_name: Optional[str]
    profile_completed: bool
    kyc_status: Optional[KYCStatus]
    created_at: datetime
    
    # Role-specific fields
    city: Optional[str] = None
    
    # Courier fields
    iban: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_model: Optional[str] = None
    license_class: Optional[str] = None
    balance: Optional[float] = None
    is_online: Optional[bool] = None
    
    # Business fields
    business_name: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    business_category: Optional[BusinessCategory] = None
    description: Optional[str] = None

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None

# Phone validation function
def validate_turkish_phone(phone: str) -> str:
    """Validate and format Turkish phone number"""
    import re
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Turkish phone patterns
    patterns = [
        r'^\+90[5-9]\d{9}$',  # +90 5xx xxx xx xx
        r'^90[5-9]\d{9}$',    # 90 5xx xxx xx xx  
        r'^0[5-9]\d{9}$',     # 0 5xx xxx xx xx
        r'^[5-9]\d{9}$'       # 5xx xxx xx xx
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            # Normalize to +90 format
            if cleaned.startswith('+90'):
                return cleaned
            elif cleaned.startswith('90'):
                return '+' + cleaned
            elif cleaned.startswith('0'):
                return '+90' + cleaned[1:]
            else:
                return '+90' + cleaned
    
    raise ValueError('Invalid Turkish phone number format')

# Marketing & Loyalty Models
class CampaignType(str, Enum):
    PERCENTAGE_DISCOUNT = "percentage_discount"  # %20 indirim
    FIXED_DISCOUNT = "fixed_discount"            # 10₺ indirim
    FREE_DELIVERY = "free_delivery"              # Ücretsiz kargo
    BUY_X_GET_Y = "buy_x_get_y"                 # 2 al 1 öde

class CampaignStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class Campaign(BaseModel):
    id: Optional[str] = None
    business_id: str
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    campaign_type: CampaignType
    discount_value: float = Field(..., gt=0)  # % or ₺ amount
    min_order_amount: Optional[float] = 0
    max_discount_amount: Optional[float] = None  # For percentage discounts
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = None  # Total usage limit
    used_count: int = 0
    status: CampaignStatus = CampaignStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)

class LoyaltyTransaction(BaseModel):
    id: Optional[str] = None
    user_id: str
    points: int  # Positive for earning, negative for spending
    transaction_type: str  # "earned", "spent", "expired"
    order_id: Optional[str] = None
    description: str
    created_at: datetime = Field(default_factory=datetime.now)

class UserLoyalty(BaseModel):
    id: Optional[str] = None
    user_id: str
    total_points: int = 0
    lifetime_points: int = 0  # Total points ever earned
    tier_level: str = "Bronze"  # Bronze, Silver, Gold, Platinum
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CouponType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_DELIVERY = "free_delivery"

class Coupon(BaseModel):
    id: Optional[str] = None
    code: str = Field(..., min_length=3, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    coupon_type: CouponType
    discount_value: float = Field(..., gt=0)
    min_order_amount: Optional[float] = 0
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: int = 0
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True
    created_by: Optional[str] = None  # Admin or business_id
    created_at: datetime = Field(default_factory=datetime.now)

class CouponUsage(BaseModel):
    id: Optional[str] = None
    coupon_id: str
    user_id: str
    order_id: str
    discount_amount: float
    used_at: datetime = Field(default_factory=datetime.now)

# Customer Profile Management Models
class Address(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str = Field(..., min_length=1, max_length=50)  # "Ev", "İş", "Diğer"
    address_line: str = Field(..., min_length=1, max_length=200)
    district: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=50)
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CustomerProfile(BaseModel):
    id: Optional[str] = None
    user_id: str
    phone: str
    email: Optional[str] = None
    first_name: str
    last_name: str
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None  # "male", "female", "other"
    profile_image_url: Optional[str] = None
    notification_preferences: Dict[str, bool] = Field(default={
        "email_notifications": True,
        "sms_notifications": True,
        "push_notifications": True,
        "marketing_emails": False
    })
    preferred_language: str = "tr"
    theme_preference: str = "light"  # "light", "dark", "auto"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class OrderRating(BaseModel):
    id: Optional[str] = None
    order_id: str
    customer_id: str
    business_id: str
    courier_id: Optional[str] = None
    business_rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 stars
    courier_rating: Optional[int] = Field(None, ge=1, le=5)   # 1-5 stars
    business_comment: Optional[str] = Field(None, max_length=500)
    courier_comment: Optional[str] = Field(None, max_length=500)
    food_quality_rating: Optional[int] = Field(None, ge=1, le=5)
    delivery_speed_rating: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.now)

# Phone Authentication Models
class PhoneAuthRequest(BaseModel):
    phone: str = Field(..., description="Turkish phone number")
    
    @validator('phone')
    def validate_phone_format(cls, v):
        return validate_turkish_phone(v)

class PhoneAuthVerify(BaseModel):
    phone: str
    otp_code: str = Field(..., min_length=6, max_length=6)
    
class PhoneAuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_data: dict

# Profile Update Models
class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    notification_preferences: Optional[Dict[str, bool]] = None
    preferred_language: Optional[str] = Field(None, pattern="^(tr|en)$")
    theme_preference: Optional[str] = Field(None, pattern="^(light|dark|auto)$")

class AddressRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    address_line: str = Field(..., min_length=1, max_length=200)
    district: Optional[str] = Field(None, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_default: bool = False