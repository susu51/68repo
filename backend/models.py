from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    COURIER = "courier" 
    BUSINESS = "business"
    ADMIN = "admin"

class KYCStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class VehicleType(str, Enum):
    CAR = "araba"
    MOTORCYCLE = "motor"
    ELECTRIC_MOTORCYCLE = "elektrikli_motor"
    BICYCLE = "bisiklet"

class BusinessCategory(str, Enum):
    FOOD = "gida"
    SHIPPING = "nakliye"

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Request Models
class OTPRequestModel(BaseModel):
    phone: str = Field(..., description="Turkish phone number (+90xxxxxxxxxx)")
    device_id: Optional[str] = Field(None, description="Device identifier for tracking")
    
    @validator('phone')
    def validate_phone(cls, v):
        # Basic validation - detailed validation happens in service layer
        if not v or len(v.strip()) < 10:
            raise ValueError('Phone number is required and must be valid')
        return v.strip()

class OTPVerifyModel(BaseModel):
    phone: str = Field(..., description="Turkish phone number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class RefreshTokenModel(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")

class UserUpdateModel(BaseModel):
    email: Optional[str] = Field(None, description="Email address (optional)")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class CourierRegistrationModel(BaseModel):
    phone: str = Field(..., description="Phone number (verified via OTP)")
    email: Optional[str] = Field(None, description="Email address (optional)")
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    iban: str = Field(..., description="Turkish IBAN for payments")
    vehicle_type: VehicleType
    vehicle_model: str = Field(..., max_length=100)
    license_class: str = Field(..., max_length=10, description="Driver license class")
    city: str = Field(..., max_length=50)

class BusinessRegistrationModel(BaseModel):
    phone: str = Field(..., description="Phone number (verified via OTP)")
    email: Optional[str] = Field(None, description="Email address (optional)")
    business_name: str = Field(..., max_length=100)
    tax_number: str = Field(..., description="Turkish tax number")
    address: str = Field(..., max_length=500)
    city: str = Field(..., max_length=50)
    business_category: BusinessCategory
    description: Optional[str] = Field(None, max_length=1000)

class CustomerRegistrationModel(BaseModel):
    phone: str = Field(..., description="Phone number (verified via OTP)")
    email: Optional[str] = Field(None, description="Email address (optional)")
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    city: str = Field(..., max_length=50)

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
    gender: Optional[str] = Field(None, regex="^(male|female|other)$")
    notification_preferences: Optional[Dict[str, bool]] = None
    preferred_language: Optional[str] = Field(None, regex="^(tr|en)$")
    theme_preference: Optional[str] = Field(None, regex="^(light|dark|auto)$")

class AddressRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    address_line: str = Field(..., min_length=1, max_length=200)
    district: Optional[str] = Field(None, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_default: bool = False