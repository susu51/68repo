from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import random
import string

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="DeliverTR API", description="Türkiye Teslimat Platformu")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'delivertr-secret-key-2024')
ALGORITHM = "HS256"

# Auth Models
class PhoneVerifyRequest(BaseModel):
    phone: str

class PhoneVerifyResponse(BaseModel):
    success: bool
    message: str
    verification_id: Optional[str] = None

class VerifyCodeRequest(BaseModel):
    phone: str
    code: str
    verification_id: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_data: dict

# User Models
class CourierRegister(BaseModel):
    phone: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str  # araba, motor, elektrikli_motor, bisiklet
    license_class: str
    license_photo_url: Optional[str] = None
    vehicle_document_url: Optional[str] = None
    profile_photo_url: Optional[str] = None

class BusinessRegister(BaseModel):
    phone: str
    business_name: str
    tax_number: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_type: str  # restaurant, market, store

class CustomerRegister(BaseModel):
    phone: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None

class Address(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False

# Database Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone: str
    user_type: str  # courier, business, customer
    is_verified: bool = False
    is_active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class Courier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str
    license_class: str
    license_photo_url: Optional[str] = None
    vehicle_document_url: Optional[str] = None
    profile_photo_url: Optional[str] = None
    kyc_status: str = "pending"  # pending, approved, rejected
    kyc_notes: Optional[str] = None
    is_online: bool = False
    current_location: Optional[dict] = None
    
class Business(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    business_name: str
    tax_number: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_type: str
    is_open: bool = False
    opening_hours: Optional[dict] = None
    
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    addresses: List[Address] = []

# Utility Functions
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

# Mock SMS Storage (In production, use Redis or proper cache)
verification_store = {}

# Auth Endpoints
@api_router.post("/auth/send-code", response_model=PhoneVerifyResponse)
async def send_verification_code(request: PhoneVerifyRequest):
    """Mock SMS gönderimi - gerçek uygulamada Twilio kullanılacak"""
    if not request.phone.startswith('+90'):
        raise HTTPException(status_code=400, detail="Geçerli Türkiye telefon numarası giriniz (+90...)")
    
    # Generate verification code and ID
    verification_code = generate_verification_code()
    verification_id = str(uuid.uuid4())
    
    # Store verification (in production use Redis with TTL)
    verification_store[verification_id] = {
        'phone': request.phone,
        'code': verification_code,
        'created_at': datetime.now(timezone.utc),
        'used': False
    }
    
    # Mock SMS - gerçekte Twilio'ya gönderilecek
    print(f"📱 SMS Mock: {request.phone} → Doğrulama kodu: {verification_code}")
    
    return PhoneVerifyResponse(
        success=True,
        message=f"Doğrulama kodu {request.phone} numarasına gönderildi",
        verification_id=verification_id
    )

@api_router.post("/auth/verify-code")
async def verify_code(request: VerifyCodeRequest):
    """Doğrulama kodu kontrolü"""
    verification = verification_store.get(request.verification_id)
    
    if not verification:
        raise HTTPException(status_code=400, detail="Geçersiz doğrulama ID'si")
    
    if verification['used']:
        raise HTTPException(status_code=400, detail="Bu doğrulama kodu zaten kullanıldı")
    
    if verification['phone'] != request.phone:
        raise HTTPException(status_code=400, detail="Telefon numarası eşleşmiyor")
    
    if verification['code'] != request.code:
        raise HTTPException(status_code=400, detail="Yanlış doğrulama kodu")
    
    # Check expiry (10 minutes)
    if datetime.now(timezone.utc) - verification['created_at'] > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Doğrulama kodu süresi doldu")
    
    # Mark as used
    verification_store[request.verification_id]['used'] = True
    
    # Check if user exists
    existing_user = await db.users.find_one({"phone": request.phone})
    
    if existing_user:
        # Login existing user
        access_token = create_access_token(data={"sub": existing_user["id"], "phone": existing_user["phone"]})
        
        # Get user profile based on type
        user_data = {"phone": existing_user["phone"], "user_type": existing_user["user_type"]}
        
        if existing_user["user_type"] == "courier":
            courier = await db.couriers.find_one({"user_id": existing_user["id"]})
            if courier:
                user_data.update({
                    "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}",
                    "kyc_status": courier.get("kyc_status", "pending")
                })
        elif existing_user["user_type"] == "business":
            business = await db.businesses.find_one({"user_id": existing_user["id"]})
            if business:
                user_data.update({
                    "business_name": business.get("business_name", ""),
                    "is_approved": existing_user.get("is_active", False)
                })
        elif existing_user["user_type"] == "customer":
            customer = await db.customers.find_one({"user_id": existing_user["id"]})
            if customer:
                user_data.update({
                    "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}"
                })
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_type=existing_user["user_type"],
            user_data=user_data
        )
    
    return {"success": True, "message": "Telefon numarası doğrulandı", "is_new_user": True}

# Registration Endpoints
@api_router.post("/register/courier")
async def register_courier(courier_data: CourierRegister):
    """Kurye kaydı"""
    # Check if user already exists
    existing_user = await db.users.find_one({"phone": courier_data.phone})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu telefon numarası zaten kayıtlı")
    
    # Create user
    user = User(phone=courier_data.phone, user_type="courier")
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    # Create courier profile
    courier = Courier(
        user_id=user.id,
        first_name=courier_data.first_name,
        last_name=courier_data.last_name,
        iban=courier_data.iban,
        vehicle_type=courier_data.vehicle_type,
        license_class=courier_data.license_class,
        license_photo_url=courier_data.license_photo_url,
        vehicle_document_url=courier_data.vehicle_document_url,
        profile_photo_url=courier_data.profile_photo_url
    )
    courier_dict = courier.dict()
    await db.couriers.insert_one(courier_dict)
    
    # Generate token
    access_token = create_access_token(data={"sub": user.id, "phone": user.phone})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="courier",
        user_data={
            "phone": user.phone,
            "name": f"{courier.first_name} {courier.last_name}",
            "kyc_status": "pending"
        }
    )

@api_router.post("/register/business")
async def register_business(business_data: BusinessRegister):
    """İşletme kaydı"""
    existing_user = await db.users.find_one({"phone": business_data.phone})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu telefon numarası zaten kayıtlı")
    
    user = User(phone=business_data.phone, user_type="business", is_active=True)
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    business = Business(
        user_id=user.id,
        business_name=business_data.business_name,
        tax_number=business_data.tax_number,
        address=business_data.address,
        latitude=business_data.latitude,
        longitude=business_data.longitude,
        business_type=business_data.business_type
    )
    business_dict = business.dict()
    await db.businesses.insert_one(business_dict)
    
    access_token = create_access_token(data={"sub": user.id, "phone": user.phone})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="business",
        user_data={
            "phone": user.phone,
            "business_name": business.business_name,
            "is_approved": True
        }
    )

@api_router.post("/register/customer")
async def register_customer(customer_data: CustomerRegister):
    """Müşteri kaydı"""
    existing_user = await db.users.find_one({"phone": customer_data.phone})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu telefon numarası zaten kayıtlı")
    
    user = User(phone=customer_data.phone, user_type="customer", is_active=True)
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    customer = Customer(
        user_id=user.id,
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        email=customer_data.email
    )
    customer_dict = customer.dict()
    await db.customers.insert_one(customer_dict)
    
    access_token = create_access_token(data={"sub": user.id, "phone": user.phone})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="customer",
        user_data={
            "phone": user.phone,
            "name": f"{customer.first_name} {customer.last_name}"
        }
    )

# Profile Endpoints
@api_router.get("/profile")
async def get_profile(current_user_id: str = Depends(get_current_user)):
    """Kullanıcı profili"""
    user = await db.users.find_one({"id": current_user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    profile_data = {"phone": user["phone"], "user_type": user["user_type"]}
    
    if user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": current_user_id})
        if courier:
            profile_data.update({
                "first_name": courier["first_name"],
                "last_name": courier["last_name"],
                "vehicle_type": courier["vehicle_type"],
                "kyc_status": courier["kyc_status"],
                "is_online": courier.get("is_online", False)
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": current_user_id})
        if business:
            profile_data.update({
                "business_name": business["business_name"],
                "address": business["address"],
                "business_type": business["business_type"],
                "is_open": business.get("is_open", False)
            })
    elif user["user_type"] == "customer":
        customer = await db.customers.find_one({"user_id": current_user_id})
        if customer:
            profile_data.update({
                "first_name": customer["first_name"],
                "last_name": customer["last_name"],
                "email": customer.get("email"),
                "addresses": customer.get("addresses", [])
            })
    
    return profile_data

# Admin Endpoints (KYC)
@api_router.get("/admin/couriers/pending")
async def get_pending_couriers():
    """Onay bekleyen kuryeler - Admin paneli için"""
    couriers = await db.couriers.find({"kyc_status": "pending"}).to_list(length=None)
    
    courier_list = []
    for courier in couriers:
        user = await db.users.find_one({"id": courier["user_id"]})
        courier_info = {
            "id": courier["id"],
            "name": f"{courier['first_name']} {courier['last_name']}",
            "phone": user["phone"] if user else "",
            "vehicle_type": courier["vehicle_type"],
            "license_class": courier["license_class"],
            "license_photo_url": courier.get("license_photo_url"),
            "vehicle_document_url": courier.get("vehicle_document_url"),
            "profile_photo_url": courier.get("profile_photo_url"),
            "created_at": user["created_at"] if user else None
        }
        courier_list.append(courier_info)
    
    return courier_list

@api_router.post("/admin/courier/{courier_id}/approve")
async def approve_courier(courier_id: str, notes: Optional[str] = None):
    """Kurye onaylama"""
    courier = await db.couriers.find_one({"id": courier_id})
    if not courier:
        raise HTTPException(status_code=404, detail="Kurye bulunamadı")
    
    # Update courier status
    await db.couriers.update_one(
        {"id": courier_id},
        {"$set": {"kyc_status": "approved", "kyc_notes": notes}}
    )
    
    # Activate user
    await db.users.update_one(
        {"id": courier["user_id"]},
        {"$set": {"is_active": True}}
    )
    
    return {"success": True, "message": "Kurye onaylandı"}

@api_router.post("/admin/courier/{courier_id}/reject")
async def reject_courier(courier_id: str, notes: str):
    """Kurye reddetme"""
    await db.couriers.update_one(
        {"id": courier_id},
        {"$set": {"kyc_status": "rejected", "kyc_notes": notes}}
    )
    
    return {"success": True, "message": "Kurye reddedildi"}

# Test endpoint
@api_router.get("/")
async def root():
    return {"message": "DeliverTR API v1.0 - Türkiye Teslimat Platformu"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()