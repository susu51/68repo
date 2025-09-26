from pydantic import BaseModel, validator, Field
from typing import Optional, List
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