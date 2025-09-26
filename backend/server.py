from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
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
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create the main app without a prefix
app = FastAPI(title="DeliverTR API", description="Türkiye Teslimat Platformu")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'delivertr-secret-key-2024')
ALGORITHM = "HS256"

# Şehirler listesi
CITIES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", 
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", 
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", 
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", 
    "Giresun", "Gümüşhane", "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", 
    "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", 
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", 
    "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", 
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", 
    "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", 
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", 
    "Karabük", "Kilis", "Osmaniye", "Düzce"
]

# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    user_type: str  # courier, business, customer
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_data: dict

# User Models
class CourierRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str  # araba, motor, elektrikli_motor, bisiklet
    vehicle_model: str
    license_class: str
    city: str

class BusinessRegister(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    tax_number: str
    address: str
    city: str
    business_category: str  # gida, nakliye
    description: Optional[str] = None

class CustomerRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    city: str

# Database Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    user_type: str  # courier, business, customer
    is_verified: bool = True  # Email verification için
    is_active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class Courier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str
    vehicle_model: str
    license_class: str
    city: str
    license_photo_url: Optional[str] = None
    vehicle_photo_url: Optional[str] = None
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
    city: str
    business_category: str  # gida, nakliye
    description: Optional[str] = None
    is_open: bool = False
    opening_hours: Optional[dict] = None
    
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    city: str
    addresses: List[dict] = []

import hashlib

# Simple password hashing (for demo purposes)
def hash_password(password: str) -> str:
    """Simple SHA-256 hash for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

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

# File Upload
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Dosya yükleme endpoint'i"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya seçilmedi")
    
    # Dosya türü kontrolü
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Sadece JPEG, PNG dosyaları yüklenebilir")
    
    # Dosya adı oluştur
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Dosyayı kaydet
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL döndür
    file_url = f"/uploads/{unique_filename}"
    return {"file_url": file_url}

# Auth Endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    """Kullanıcı girişi"""
    # Kullanıcıyı bul
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    # Şifre kontrolü
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    # Kullanıcı verilerini al
    user_data = {"email": user["email"], "user_type": user["user_type"]}
    
    if user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": user["id"]})
        if courier:
            user_data.update({
                "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}",
                "kyc_status": courier.get("kyc_status", "pending"),
                "city": courier.get("city", "")
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": user["id"]})
        if business:
            user_data.update({
                "business_name": business.get("business_name", ""),
                "city": business.get("city", ""),
                "category": business.get("business_category", ""),
                "is_approved": user.get("is_active", False)
            })
    elif user["user_type"] == "customer":
        customer = await db.customers.find_one({"user_id": user["id"]})
        if customer:
            user_data.update({
                "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}",
                "city": customer.get("city", "")
            })
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type=user["user_type"],
        user_data=user_data
    )

# Registration Endpoints
@api_router.post("/register/courier", response_model=LoginResponse)
async def register_courier(courier_data: CourierRegister):
    """Kurye kaydı"""
    # E-posta kontrolü
    existing_user = await db.users.find_one({"email": courier_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    # Şehir kontrolü
    if courier_data.city not in CITIES:
        raise HTTPException(status_code=400, detail="Geçersiz şehir seçimi")
    
    # Kullanıcı oluştur
    password_hash = hash_password(courier_data.password)
    user = User(
        email=courier_data.email, 
        password_hash=password_hash, 
        user_type="courier"
    )
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    # Kurye profili oluştur
    courier = Courier(
        user_id=user.id,
        first_name=courier_data.first_name,
        last_name=courier_data.last_name,
        iban=courier_data.iban,
        vehicle_type=courier_data.vehicle_type,
        vehicle_model=courier_data.vehicle_model,
        license_class=courier_data.license_class,
        city=courier_data.city
    )
    courier_dict = courier.dict()
    await db.couriers.insert_one(courier_dict)
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="courier",
        user_data={
            "email": user.email,
            "name": f"{courier.first_name} {courier.last_name}",
            "city": courier.city,
            "kyc_status": "pending"
        }
    )

@api_router.post("/register/business", response_model=LoginResponse)
async def register_business(business_data: BusinessRegister):
    """İşletme kaydı"""
    existing_user = await db.users.find_one({"email": business_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    if business_data.city not in CITIES:
        raise HTTPException(status_code=400, detail="Geçersiz şehir seçimi")
    
    if business_data.business_category not in ["gida", "nakliye"]:
        raise HTTPException(status_code=400, detail="Geçersiz kategori seçimi")
    
    password_hash = hash_password(business_data.password)
    user = User(
        email=business_data.email, 
        password_hash=password_hash, 
        user_type="business", 
        is_active=True
    )
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    business = Business(
        user_id=user.id,
        business_name=business_data.business_name,
        tax_number=business_data.tax_number,
        address=business_data.address,
        city=business_data.city,
        business_category=business_data.business_category,
        description=business_data.description
    )
    business_dict = business.dict()
    await db.businesses.insert_one(business_dict)
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="business",
        user_data={
            "email": user.email,
            "business_name": business.business_name,
            "city": business.city,
            "category": business.business_category,
            "is_approved": True
        }
    )

@api_router.post("/register/customer", response_model=LoginResponse)
async def register_customer(customer_data: CustomerRegister):
    """Müşteri kaydı"""
    existing_user = await db.users.find_one({"email": customer_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    if customer_data.city not in CITIES:
        raise HTTPException(status_code=400, detail="Geçersiz şehir seçimi")
    
    password_hash = hash_password(customer_data.password)
    user = User(
        email=customer_data.email, 
        password_hash=password_hash, 
        user_type="customer", 
        is_active=True
    )
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
    customer = Customer(
        user_id=user.id,
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        city=customer_data.city
    )
    customer_dict = customer.dict()
    await db.customers.insert_one(customer_dict)
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="customer",
        user_data={
            "email": user.email,
            "name": f"{customer.first_name} {customer.last_name}",
            "city": customer.city
        }
    )

# Profile Endpoints
@api_router.get("/profile")
async def get_profile(current_user_id: str = Depends(get_current_user)):
    """Kullanıcı profili"""
    user = await db.users.find_one({"id": current_user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    profile_data = {"email": user["email"], "user_type": user["user_type"]}
    
    if user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": current_user_id})
        if courier:
            profile_data.update({
                "first_name": courier["first_name"],
                "last_name": courier["last_name"],
                "vehicle_type": courier["vehicle_type"],
                "vehicle_model": courier["vehicle_model"],
                "city": courier["city"],
                "kyc_status": courier["kyc_status"],
                "license_photo_url": courier.get("license_photo_url"),
                "vehicle_photo_url": courier.get("vehicle_photo_url"),
                "is_online": courier.get("is_online", False)
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": current_user_id})
        if business:
            profile_data.update({
                "business_name": business["business_name"],
                "address": business["address"],
                "city": business["city"],
                "business_category": business["business_category"],
                "description": business.get("description"),
                "is_open": business.get("is_open", False)
            })
    elif user["user_type"] == "customer":
        customer = await db.customers.find_one({"user_id": current_user_id})
        if customer:
            profile_data.update({
                "first_name": customer["first_name"],
                "last_name": customer["last_name"],
                "city": customer["city"],
                "addresses": customer.get("addresses", [])
            })
    
    return profile_data

# Update courier photos
@api_router.put("/courier/update-photos")
async def update_courier_photos(
    license_photo_url: Optional[str] = None,
    vehicle_photo_url: Optional[str] = None,
    current_user_id: str = Depends(get_current_user)
):
    """Kurye fotoğraflarını güncelle"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler fotoğraf güncelleyebilir")
    
    update_data = {}
    if license_photo_url:
        update_data["license_photo_url"] = license_photo_url
    if vehicle_photo_url:
        update_data["vehicle_photo_url"] = vehicle_photo_url
    
    if update_data:
        await db.couriers.update_one(
            {"user_id": current_user_id},
            {"$set": update_data}
        )
    
    return {"success": True, "message": "Fotoğraflar güncellendi"}

# Şehirler listesi
@api_router.get("/cities")
async def get_cities():
    """Türkiye şehirleri listesi"""
    return {"cities": CITIES}

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
            "email": user["email"] if user else "",
            "vehicle_type": courier["vehicle_type"],
            "vehicle_model": courier["vehicle_model"],
            "license_class": courier["license_class"],
            "city": courier["city"],
            "license_photo_url": courier.get("license_photo_url"),
            "vehicle_photo_url": courier.get("vehicle_photo_url"),
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
    return {"message": "DeliverTR API v2.0 - E-posta ile Kayıt Sistemi"}

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