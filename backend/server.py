from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import shutil
import json
import math
import hashlib
from enum import Enum
import bcrypt
import random

# Import phone validation function
try:
    from models import validate_turkish_phone
except ImportError:
    # Fallback phone validation function
    def validate_turkish_phone(phone: str) -> str:
        import re
        cleaned = re.sub(r'[^\d+]', '', phone)
        patterns = [
            r'^\+90[5-9]\d{9}$',  # +90 5xx xxx xx xx
            r'^90[5-9]\d{9}$',    # 90 5xx xxx xx xx  
            r'^0[5-9]\d{9}$',     # 0 5xx xxx xx xx
            r'^[5-9]\d{9}$'       # 5xx xxx xx xx
        ]
        for pattern in patterns:
            if re.match(pattern, cleaned):
                if cleaned.startswith('+90'):
                    return cleaned
                elif cleaned.startswith('90'):
                    return '+' + cleaned
                elif cleaned.startswith('0'):
                    return '+90' + cleaned[1:]
                else:
                    return '+90' + cleaned
        raise ValueError('Invalid Turkish phone number format')

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client.kuryecini_database

# Create uploads directory
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create the main app with comprehensive API documentation
app = FastAPI(
    title="Kuryecini API",
    description="""
    🚀 **Kuryecini - Türkiye'nin En Hızlı Teslimat Platformu API**
    
    Bu API, Kuryecini food delivery platform için geliştirilen RESTful servislerini içerir.
    
    ## 🏗️ **Ana Özellikler**
    
    * **👤 Kullanıcı Yönetimi**: Müşteri, kurye, işletme ve admin rolleri
    * **🏪 İşletme Yönetimi**: Restoran kaydı, menü yönetimi, sipariş takibi
    * **🚚 Kurye Sistemi**: KYC onay süreci, harita entegrasyonu, kazanç takibi  
    * **📦 Sipariş Yönetimi**: Sepet, ödeme, teslimat süreci
    * **📍 Lokasyon Servisleri**: Adres yönetimi, mesafe hesaplama
    * **⚙️ Admin Paneli**: Sistem konfigürasyonu, komisyon ayarları
    
    ## 🔐 **Authentication**
    
    API JWT (JSON Web Token) tabanlı authentication kullanır:
    
    1. `/api/auth/login` endpoint'i ile giriş yapın
    2. Dönen `access_token`'ı `Authorization: Bearer <token>` header'ında kullanın
    3. Token'lar role-based access control (RBAC) içerir
    
    ## 🎯 **Roller ve Yetkiler**
    
    * **customer**: Sipariş verme, adres yönetimi, geçmiş görüntüleme
    * **courier**: Sipariş kabul etme, teslimat yapma, kazanç görüntüleme
    * **business**: Menü yönetimi, sipariş yönetimi, istatistik görüntüleme
    * **admin**: Tüm sistem yönetimi, kullanıcı onayları, konfigürasyon
    
    ## 🌐 **Deployment Bilgileri**
    
    * **Frontend**: Vercel (React SPA)
    * **Backend**: Render (FastAPI + MongoDB)
    * **Database**: MongoDB Atlas
    
    ## 📞 **Destek**
    
    API ile ilgili sorularınız için: admin@kuryecini.com
    """,
    version="1.0.0",
    contact={
        "name": "Kuryecini API Destek",
        "email": "admin@kuryecini.com",
        "url": "https://kuryecini.com/destek",
    },
    license_info={
        "name": "Kuryecini Proprietary License",
        "url": "https://kuryecini.com/lisans",
    },
    servers=[
        {
            "url": "https://api.kuryecini.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.kuryecini.com", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8001",
            "description": "Development server"
        }
    ],
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# Health check endpoint (required for deployment)
@app.get("/healthz")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {"status": "ok"}

# Legacy health endpoint alias
@app.get("/health")
async def health_check_legacy():
    """Legacy health check endpoint alias"""
    return {"status": "ok"}

# Add required menus endpoint
@app.get("/menus", 
    tags=["Public", "Menus"],
    summary="All Menu Items",
    description="Get all menu items from approved businesses in standardized format."
)
async def get_menus():
    """
    **Legacy Menu Endpoint**
    
    Returns all menu items from approved businesses in a standardized format.
    Use `/api/menus/public` for enhanced restaurant structure.
    """
    try:
        # Get all products from all businesses
        businesses = await db.businesses.find({"kyc_status": "approved"}).to_list(None)
        all_menu_items = []
        
        for business in businesses:
            # Get products for this business
            products = await db.products.find({"business_id": business["id"]}).to_list(None)
            for product in products:
                menu_item = {
                    "id": product.get("id", str(product.get("_id", ""))),
                    "title": product.get("name", ""),
                    "price": float(product.get("price", 0)),
                    "imageUrl": product.get("image_url", ""),
                    "category": product.get("category", "uncategorized")
                }
                all_menu_items.append(menu_item)
        
        return all_menu_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public menu endpoint with enhanced filtering
@app.get("/menus/public",
    tags=["Public", "Restaurants"],
    summary="Public Restaurant Menus", 
    description="Get public menus from active and approved restaurants with full business information."
)
async def get_public_menus():
    """
    **Public Restaurant Menus**
    
    Returns detailed restaurant information with their complete menus.
    Only shows approved and active restaurants with available products.
    
    **Response Structure:**
    ```json
    {
        "restaurants": [
            {
                "id": "restaurant-uuid",
                "name": "Restaurant Name",
                "description": "Restaurant description", 
                "address": "Full address",
                "city": "Istanbul",
                "rating": 4.8,
                "delivery_time": "25-35 dk",
                "min_order": 50.0,
                "menu": [
                    {
                        "id": "product-uuid",
                        "name": "Product Name",
                        "description": "Product description",
                        "price": 25.50,
                        "image_url": "https://...",
                        "category": "Ana Yemek",
                        "preparation_time": 15
                    }
                ]
            }
        ],
        "count": 5,
        "message": "5 aktif restoran bulundu."
    }
    ```
    
    **Filtering:**
    - Only `kyc_status: "approved"` businesses
    - Only `is_active: true` businesses  
    - Only `is_available: true` products
    - Restaurants without available products are excluded
    """
    try:
        # Get only approved and active businesses
        businesses = await db.businesses.find({
            "kyc_status": "approved",
            "is_active": True
        }).to_list(None)
        
        if not businesses:
            return {
                "restaurants": [],
                "message": "Şu an aktif restoran bulunmamaktadır.",
                "count": 0
            }
        
        restaurants_with_menus = []
        
        for business in businesses:
            # Get active products for this business
            products = await db.products.find({
                "business_id": business["id"],
                "is_available": True
            }).to_list(None)
            
            if products:  # Only include restaurants with available products
                restaurant_data = {
                    "id": business.get("id"),
                    "name": business.get("business_name", ""),
                    "description": business.get("description", ""),
                    "address": business.get("address", ""),
                    "city": business.get("city", ""),
                    "rating": business.get("rating", 5.0),
                    "delivery_time": business.get("delivery_time", "30-45 dk"),
                    "min_order": business.get("min_order_amount", 50.0),
                    "menu": []
                }
                
                for product in products:
                    menu_item = {
                        "id": product.get("id", str(product.get("_id", ""))),
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "price": float(product.get("price", 0)),
                        "image_url": product.get("image_url", ""),
                        "category": product.get("category", "Ana Yemek"),
                        "preparation_time": product.get("preparation_time_minutes", 15)
                    }
                    restaurant_data["menu"].append(menu_item)
                
                restaurants_with_menus.append(restaurant_data)
        
        return {
            "restaurants": restaurants_with_menus,
            "count": len(restaurants_with_menus),
            "message": f"{len(restaurants_with_menus)} aktif restoran bulundu." if restaurants_with_menus else "Aktif restoran bulunamadı."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menü yüklenirken hata: {str(e)}")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix and comprehensive tagging
api_router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)

# Security
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kuryecini-super-secret-key-2024-turkey-delivery")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", f"{JWT_SECRET_KEY}_refresh")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MIN", 15))  # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TTL_DAY", 7))  # Long-lived
security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://order-platform-1.preview.emergentagent.com"  # Current deployment URL
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CourierRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str  # araba, motor, elektrikli_motor, bisiklet
    vehicle_model: str
    license_class: str  # A, A1, A2, B, C, D
    license_number: str
    city: str
    license_photo_url: Optional[str] = None
    vehicle_photo_url: Optional[str] = None
    profile_photo_url: Optional[str] = None

class BusinessRegistration(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    tax_number: str
    address: str
    city: str
    business_category: str  # gida, nakliye
    description: Optional[str] = None

class BusinessRegister(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    tax_number: str
    address: str
    city: str
    business_category: str
    description: Optional[str] = None

class CustomerRegistration(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    city: str

class User(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
    is_active: bool = True
    
    # Common fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    
    # Courier specific
    iban: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    license_class: Optional[str] = None
    license_number: Optional[str] = None
    license_photo_url: Optional[str] = None
    vehicle_photo_url: Optional[str] = None
    profile_photo_url: Optional[str] = None
    kyc_status: Optional[str] = "pending"  # pending, approved, rejected
    balance: Optional[float] = 0.0
    is_online: Optional[bool] = False
    
    # Business specific
    business_name: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    business_category: Optional[str] = None
    description: Optional[str] = None

# Product Models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    preparation_time_minutes: int = 30
    photo_url: Optional[str] = None
    is_available: bool = True

class Product(BaseModel):
    id: str
    business_id: str
    business_name: str
    name: str
    description: str
    price: float
    category: str
    preparation_time_minutes: int
    photo_url: Optional[str] = None
    is_available: bool
    created_at: datetime

# Order Models
class OrderStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned" 
    ON_ROUTE = "on_route"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

class OrderCreate(BaseModel):
    delivery_address: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    items: List[OrderItem]
    total_amount: float
    notes: Optional[str] = None

class PriceBreakdown(BaseModel):
    """Detailed price breakdown for transparency"""
    subtotal: float  # Net product prices
    restaurant_fee: float  # Restaurant's portion (95% of subtotal)
    courier_fee: float  # Courier commission (5% of subtotal)  
    platform_commission: float  # Platform commission (5% of subtotal)
    service_fee: float = 0.0  # No service fee for customers
    delivery_fee: float = 0.0  # No delivery fee for customers
    total: float  # Final total amount

class Order(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    business_id: str
    business_name: str
    courier_id: Optional[str] = None
    courier_name: Optional[str] = None
    status: OrderStatus
    delivery_address: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    items: List[OrderItem]
    total_amount: float
    commission_amount: float  # Platform commission
    price_breakdown: Optional[PriceBreakdown] = None
    notes: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

# Admin Login Model
class AdminLogin(BaseModel):
    password: str

# Enums and Constants
class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"

# Helper Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("Invalid token type")
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Handle special admin case - support both old and new admin emails
    if (email in ["admin@delivertr.com", "admin@kuryecini.com"]) and payload.get("role") == "admin":
        return {
            "id": "admin",
            "email": email,  # Return the email from token
            "role": "admin",
            "first_name": "Admin",
            "last_name": "User",
            "is_active": True
        }
    
    # Handle test users for demo purposes (same as in login endpoint)
    test_users = {
        "testcustomer@example.com": {
            "id": "customer-001",
            "email": "testcustomer@example.com", 
            "first_name": "Test",
            "last_name": "Customer",
            "role": "customer",
            "is_active": True
        },
        "testkurye@example.com": {
            "id": "courier-001",
            "email": "testkurye@example.com",
            "first_name": "Test", 
            "last_name": "Courier",
            "role": "courier",
            "is_active": True,
            "kyc_status": "approved"  # Important: approve test courier for testing
        },
        "testbusiness@example.com": {
            "id": "business-001",
            "email": "testbusiness@example.com",
            "first_name": "Test",
            "last_name": "Business",
            "role": "business", 
            "business_name": "Test Restaurant",
            "is_active": True
        }
    }
    
    # Check if it's a test user
    if email in test_users:
        return test_users[email]
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    return user

# Authentication Endpoints
@api_router.post("/auth/login", 
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate user with email and password. Returns JWT token for API access.",
    response_description="JWT access token and user information"
)
async def login(login_data: LoginRequest):
    """
    **User Authentication Endpoint**
    
    Authenticates users across all roles (customer, courier, business, admin) and returns a JWT token.
    
    **Supported Roles:**
    - `customer`: Regular customers who place orders
    - `courier`: Delivery personnel who fulfill orders  
    - `business`: Restaurant/business owners who manage menus
    - `admin`: Platform administrators with full access
    
    **Authentication Flow:**
    1. Submit email and password via this endpoint
    2. Receive JWT `access_token` in response
    3. Include token in `Authorization: Bearer <token>` header for protected endpoints
    
    **Example Usage:**
    ```json
    {
        "email": "customer@example.com",
        "password": "userpassword123"
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "user": {
            "id": "user-uuid",
            "email": "customer@example.com", 
            "role": "customer",
            "first_name": "John"
        }
    }
    ```
    """
    
    # Test users for demo purposes
    test_users = {
        "testcustomer@example.com": {
            "id": "customer-001",
            "email": "testcustomer@example.com", 
            "first_name": "Test",
            "last_name": "Customer",
            "role": "customer",
            "is_active": True,
            "password": "test123"
        },
        "testkurye@example.com": {
            "id": "courier-001",
            "email": "testkurye@example.com",
            "first_name": "Test", 
            "last_name": "Courier",
            "role": "courier",
            "is_active": True,
            "password": "test123"
        },
        "testbusiness@example.com": {
            "id": "business-001",
            "email": "testbusiness@example.com",
            "first_name": "Test",
            "last_name": "Business",
            "role": "business", 
            "business_name": "Test Restaurant",
            "is_active": True,
            "password": "test123"
        }
    }
    
    # Check test users
    if login_data.email in test_users:
        test_user = test_users[login_data.email]
        if login_data.password == test_user["password"]:
            access_token = create_access_token(data={"sub": login_data.email, "role": test_user["role"]})
            refresh_token = create_refresh_token(data={"sub": login_data.email, "role": test_user["role"]})
            user_data = test_user.copy()
            del user_data["password"]  # Remove password from response
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer", 
                "user": user_data
            }
        else:
            raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    # Real user lookup (unchanged from original)
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    if not verify_password(login_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    access_token = create_access_token(data={"sub": user["email"], "role": user.get("role", "customer")})
    refresh_token = create_refresh_token(data={"sub": user["email"], "role": user.get("role", "customer")})
    
    user["id"] = str(user["_id"]) if "_id" in user else str(uuid.uuid4())
    if "_id" in user:
        del user["_id"] 
    if "password_hash" in user:
        del user["password_hash"]
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@api_router.post("/auth/refresh",
    tags=["Authentication"],
    summary="Refresh Access Token",
    description="Generate a new access token using a valid refresh token.",
    response_description="New JWT access token"
)
async def refresh_access_token(refresh_token: str):
    """
    **Refresh Access Token**
    
    Generate a new access token using a valid refresh token.
    This allows users to stay logged in without re-entering credentials.
    
    **Usage:**
    ```json
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "new_jwt_token_here",
        "token_type": "bearer"
    }
    ```
    """
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Create new access token with same user data
    new_access_token = create_access_token(
        data={"sub": payload.get("sub"), "role": payload.get("role")}
    )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@api_router.post("/auth/logout",
    tags=["Authentication"],
    summary="User Logout",
    description="Logout user and invalidate tokens.",
    response_description="Logout confirmation"
)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    **User Logout**
    
    Logout the current user. In a production environment, this would
    invalidate the refresh token in the database.
    
    **Note:** Currently returns success without token invalidation.
    In production, implement token blacklisting or database cleanup.
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user.get("id")
    }
@api_router.post("/register/courier")
async def register_courier(courier_data: CourierRegistration):
    """Register a new courier"""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": courier_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new courier user
    hashed_password = hash_password(courier_data.password)
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": courier_data.email,
        "password": hashed_password,
        "role": "courier",
        "first_name": courier_data.first_name,
        "last_name": courier_data.last_name,
        "iban": courier_data.iban,
        "vehicle_type": courier_data.vehicle_type,
        "vehicle_model": courier_data.vehicle_model,
        "license_class": courier_data.license_class,
        "license_number": courier_data.license_number,
        "city": courier_data.city,
        "license_photo_url": courier_data.license_photo_url,
        "vehicle_photo_url": courier_data.vehicle_photo_url,
        "profile_photo_url": courier_data.profile_photo_url,
        "kyc_status": "pending",
        "balance": 0.0,
        "is_online": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": courier_data.email})
    
    # Remove password from response and convert datetime to string
    del user_doc["password"]
    if "_id" in user_doc:
        del user_doc["_id"]
    user_doc["created_at"] = user_doc["created_at"].isoformat()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "courier",
        "user_data": user_doc
    }

@api_router.post("/register/business")
async def register_business(business_data: BusinessRegister):
    """Register a new business"""
    # Check if email already exists
    existing_user = await db.users.find_one({"email": business_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new business user with pending status for KYC approval
    hashed_password = hash_password(business_data.password)
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": business_data.email,
        "password": hashed_password,
        "role": "business",
        "business_name": business_data.business_name,
        "tax_number": business_data.tax_number,
        "address": business_data.address,
        "city": business_data.city,
        "business_category": business_data.business_category,
        "description": business_data.description,
        "is_active": True,
        "business_status": "pending",  # pending, approved, rejected
        "approved_at": None,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": business_data.email})
    
    # Remove password from response and convert datetime to string
    del user_doc["password"]
    if "_id" in user_doc:
        del user_doc["_id"]
    user_doc["created_at"] = user_doc["created_at"].isoformat()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "business",
        "user_data": user_doc
    }

@api_router.post("/register/customer",
    tags=["Authentication", "Customer"],
    summary="Customer Registration",
    description="Register a new customer account with email verification.",
    status_code=201
)
async def register_customer(customer_data: CustomerRegistration):
    """
    **Customer Registration**
    
    Creates a new customer account for placing food orders.
    
    **Required Fields:**
    - `email`: Valid email address (will be username)
    - `password`: Secure password (min 6 characters)
    - `first_name`: Customer's first name
    - `last_name`: Customer's last name
    - `city`: Customer's city (from 81 Turkish cities)
    
    **Features:**
    - Automatic email validation
    - Password hashing for security
    - Turkish city validation
    - Duplicate email prevention
    """
    # Check if email already exists
    existing_user = await db.users.find_one({"email": customer_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new customer user
    hashed_password = hash_password(customer_data.password)
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": customer_data.email,
        "password": hashed_password,
        "role": "customer",
        "first_name": customer_data.first_name,
        "last_name": customer_data.last_name,
        "city": customer_data.city,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": customer_data.email})
    
    # Remove password from response and convert datetime to string
    del user_doc["password"]
    if "_id" in user_doc:
        del user_doc["_id"]
    user_doc["created_at"] = user_doc["created_at"].isoformat()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "customer",
        "user_data": user_doc
    }

# File Upload Endpoint
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file (images, documents)"""
    # Validate file type
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'image/heic', 'image/heif'
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 10MB)"
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Return file URL
    file_url = f"/uploads/{unique_filename}"
    
    return {
        "success": True,
        "file_url": file_url,
        "filename": unique_filename,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": len(file_content)
    }

# Get current user info
@api_router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    # Convert ObjectId to string
    current_user["id"] = str(current_user["_id"])
    del current_user["_id"]
    del current_user["password"]  # Don't send password
    
    return current_user

# Legacy Admin Authentication (DEPRECATED - Use standard /auth/login)
@api_router.post("/auth/admin")
async def admin_login(admin_data: AdminLogin):
    """DEPRECATED: Admin login endpoint - Use standard /auth/login instead"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Admin endpoint deprecated. Use /auth/login with admin credentials."
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "admin",
        "user_data": admin_user
    }

# Admin dependency
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin role - JWT token based authentication only"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Business dependency
async def get_business_user(current_user: dict = Depends(get_current_user)):
    """Require business role"""
    if current_user.get("role") != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business access required"
        )
    return current_user

# BUSINESS MANAGEMENT ENDPOINTS

@api_router.put("/business/status")
async def update_business_status(status_data: dict, current_user: dict = Depends(get_current_user)):
    """Update business status (open/closed)"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # For demo purposes, return success with mock data
        return {
            "success": True,
            "status": status_data.get("isOpen", True),
            "message": "Restaurant status updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Status update failed")

@api_router.get("/business/stats")
async def get_business_stats(current_user: dict = Depends(get_current_user)):
    """Get business statistics and analytics"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # Return mock statistics data
        return {
            "today": {
                "orders": 23,
                "revenue": 1247.50,
                "avgOrderValue": 54.24,
                "completionRate": 96.5
            },
            "week": {
                "orders": 187,
                "revenue": 9876.25,
                "growth": 12.5
            },
            "month": {
                "orders": 756,
                "revenue": 42315.75,
                "growth": 18.7
            },
            "topProducts": [
                {"name": "Chicken Burger", "sales": 245, "revenue": 11025.00},
                {"name": "Margarita Pizza", "sales": 189, "revenue": 12285.00},
                {"name": "Adana Kebap", "sales": 156, "revenue": 8580.00}
            ],
            "customerSatisfaction": 4.6
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Stats retrieval failed")

@api_router.get("/business/orders/incoming")
async def get_incoming_orders(current_user: dict = Depends(get_current_user)):
    """Get incoming orders for business"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # Return mock incoming orders
        mock_orders = [
            {
                "id": "ORD-001",
                "customer_name": "Ahmet Yılmaz",
                "customer_phone": "+90 532 123 4567",
                "items": [
                    {"name": "Chicken Burger", "quantity": 2, "price": 45.00},
                    {"name": "Patates Kızartması", "quantity": 1, "price": 15.00}
                ],
                "total_amount": 105.00,
                "delivery_address": {"address": "Kadıköy, Moda Cad. No:15"},
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        return {"orders": mock_orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Orders retrieval failed")

# Product Management Endpoints
@api_router.post("/products")
async def create_product(product_data: ProductCreate, current_user: dict = Depends(get_business_user)):
    """Create new product (Business only)"""
    product_doc = {
        "id": str(uuid.uuid4()),
        "business_id": current_user["id"],
        "business_name": current_user.get("business_name", "Unknown Business"),
        "name": product_data.name,
        "description": product_data.description,
        "price": product_data.price,
        "category": product_data.category,
        "preparation_time_minutes": product_data.preparation_time_minutes,
        "photo_url": product_data.photo_url,
        "is_available": product_data.is_available,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.products.insert_one(product_doc)
    
    # Convert datetime to string
    product_doc["created_at"] = product_doc["created_at"].isoformat()
    del product_doc["_id"]
    
    return product_doc

@api_router.get("/products")
async def get_products(business_id: Optional[str] = None, category: Optional[str] = None):
    """Get products (optionally filtered by business or category)"""
    filter_query = {"is_available": True}
    
    if business_id:
        filter_query["business_id"] = business_id
    if category:
        filter_query["category"] = category
    
    products = await db.products.find(filter_query).to_list(length=None)
    
    # Convert datetime and ObjectId
    for product in products:
        product["id"] = str(product["_id"])
        del product["_id"]
        
        # Handle datetime conversion safely
        if "created_at" in product:
            if isinstance(product["created_at"], str):
                # Already a string, keep as is
                pass
            elif hasattr(product["created_at"], 'isoformat'):
                # It's a datetime object, convert to string
                product["created_at"] = product["created_at"].isoformat()
            else:
                # Fallback for any other type
                product["created_at"] = str(product["created_at"])
    
    return products

@api_router.get("/products/my")
async def get_my_products(current_user: dict = Depends(get_business_user)):
    """Get products for current business"""
    products = await db.products.find({"business_id": current_user["id"]}).to_list(length=None)
    
    # Convert datetime and ObjectId
    for product in products:
        product["id"] = str(product["_id"])
        del product["_id"]
        
        # Handle datetime conversion safely
        if "created_at" in product:
            if isinstance(product["created_at"], str):
                # Already a string, keep as is
                pass
            elif hasattr(product["created_at"], 'isoformat'):
                # It's a datetime object, convert to string
                product["created_at"] = product["created_at"].isoformat()
            else:
                # Fallback for any other type
                product["created_at"] = str(product["created_at"])
    
    return products

@api_router.put("/products/{product_id}")
async def update_product(product_id: str, product_data: ProductCreate, current_user: dict = Depends(get_business_user)):
    """Update product (Business owner only)"""
    # Check if product belongs to current business
    product = await db.products.find_one({"id": product_id, "business_id": current_user["id"]})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    update_data = product_data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Product updated successfully"}

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_business_user)):
    """Delete product (Business owner only)"""
    # Check if product belongs to current business
    product = await db.products.find_one({"id": product_id, "business_id": current_user["id"]})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    
    await db.products.delete_one({"id": product_id})
    
    return {"success": True, "message": "Product deleted successfully"}

# Order Management Endpoints
@api_router.post("/orders")
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    """Create new order (Customer only)"""
    if current_user.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create orders"
        )
    
    # Calculate commission (3%)
    commission_amount = order_data.total_amount * 0.03
    
    order_doc = {
        "id": str(uuid.uuid4()),
        "customer_id": current_user["id"],
        "customer_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        "business_id": "",  # Will be set from product lookup
        "business_name": "",  # We'll need to get this from product
        "courier_id": None,
        "courier_name": None,
        "status": OrderStatus.CREATED,
        "delivery_address": order_data.delivery_address,
        "delivery_lat": order_data.delivery_lat,
        "delivery_lng": order_data.delivery_lng,
        "items": [item.dict() for item in order_data.items],
        "total_amount": order_data.total_amount,
        "commission_amount": commission_amount,
        "notes": order_data.notes,
        "created_at": datetime.now(timezone.utc),
        "assigned_at": None,
        "picked_up_at": None,
        "delivered_at": None
    }
    
    # Get business info from first product
    if order_data.items:
        first_product = await db.products.find_one({"id": order_data.items[0].product_id})
        if first_product:
            order_doc["business_id"] = first_product["business_id"]
            order_doc["business_name"] = first_product["business_name"]
    
    await db.orders.insert_one(order_doc)
    
    # Convert datetime to string
    order_doc["created_at"] = order_doc["created_at"].isoformat()
    del order_doc["_id"]
    
    return order_doc

@api_router.get("/orders")
async def get_orders(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get orders based on user role"""
    filter_query = {}
    
    if status:
        filter_query["status"] = status
    
    # Filter by role
    if current_user.get("role") == "customer":
        filter_query["customer_id"] = current_user["id"]
    elif current_user.get("role") == "business":
        filter_query["business_id"] = current_user["id"]
    elif current_user.get("role") == "courier":
        # Couriers see unassigned orders or orders assigned to them
        if not status:
            filter_query = {
                "$or": [
                    {"status": "created", "courier_id": None},
                    {"courier_id": current_user["id"]}
                ]
            }
        else:
            filter_query["courier_id"] = current_user["id"]
    
    orders = await db.orders.find(filter_query).to_list(length=None)
    
    # Convert datetime and ObjectId
    for order in orders:
        order["id"] = str(order["_id"])
        del order["_id"]
        order["created_at"] = order["created_at"].isoformat()
        if order.get("assigned_at"):
            order["assigned_at"] = order["assigned_at"].isoformat()
        if order.get("picked_up_at"):
            order["picked_up_at"] = order["picked_up_at"].isoformat()
        if order.get("delivered_at"):
            order["delivered_at"] = order["delivered_at"].isoformat()
    
    return orders

@api_router.get("/orders/nearby")
async def get_nearby_orders(current_user: dict = Depends(get_current_user)):
    """Get all available orders for couriers (city-wide, not just nearby)"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access nearby orders"
        )
    
    # Check if courier is KYC approved
    if current_user.get("kyc_status") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC approval required to view orders"
        )
    
    # Get orders that are created (available for pickup) and not assigned yet
    # CHANGED: Show all city-wide orders, not just nearby
    available_orders = await db.orders.find({
        "status": "created",
        "courier_id": None  # Not assigned to any courier yet (courier_id is null)
    }).to_list(length=None)
    
    # Process orders for courier display
    orders_for_courier = []
    
    # İstanbul merkez koordinatları (daha gerçekçi alanlar)
    istanbul_districts = [
        (41.0082, 28.9784),  # Sultanahmet
        (41.0369, 28.9850),  # Beyoğlu 
        (41.0498, 28.9662),  # Şişli
        (41.0766, 28.9688),  # Beşiktaş
        (41.0058, 29.0281),  # Kadıköy
        (40.9969, 29.0833),  # Ataşehir
        (41.0431, 29.0088),  # Üsküdar
        (41.1058, 29.0074),  # Sarıyer
        (40.9517, 29.1248),  # Maltepe
        (41.0796, 28.9948),  # Etiler
    ]
    
    for i, order in enumerate(available_orders):
        # Her sipariş için rastgele bir İstanbul ilçesi seç
        district = istanbul_districts[i % len(istanbul_districts)]
        
        # İlçe merkezine yakın küçük offset ekle (maksimum 2km)
        lat_offset = (hash(str(order["_id"])) % 200 - 100) * 0.00002  # ~±2km
        lng_offset = (hash(str(order["_id"])) % 200 - 100) * 0.00003  # ~±2km
        
        pickup_lat = district[0] + lat_offset
        pickup_lng = district[1] + lng_offset
        
        # Teslimat adresi pickup'a yakın (100m - 1km arası)
        delivery_offset_lat = (hash(str(order["_id"]) + "delivery") % 100 - 50) * 0.00001
        delivery_offset_lng = (hash(str(order["_id"]) + "delivery") % 100 - 50) * 0.000015
        
        delivery_lat = pickup_lat + delivery_offset_lat
        delivery_lng = pickup_lng + delivery_offset_lng
        
        order_data = {
            "id": order.get("id", str(order["_id"])),
            "customer_name": order.get("customer_name", "Müşteri"),
            "business_name": order.get("business_name", "İşletme"),
            "pickup_address": {
                "lat": pickup_lat,
                "lng": pickup_lng,
                "address": f"İşletme Adresi - {istanbul_districts[i % len(istanbul_districts)]}"
            },
            "delivery_address": {
                "lat": delivery_lat, 
                "lng": delivery_lng,
                "address": order.get("delivery_address", "Teslimat adresi")
            },
            "total_amount": order.get("total_amount", 0),
            "items": order.get("items", []),
            "created_at": order["created_at"].isoformat(),
            "commission_amount": order.get("commission_amount", order.get("total_amount", 0) * 0.03),
            "preparation_time": f"{15 + (i * 2)} dk",  # Dynamic prep time
            "priority": "high" if order.get("total_amount", 0) > 300 else "normal"
        }
        orders_for_courier.append(order_data)
    
    return orders_for_courier

@api_router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, new_status: OrderStatus, current_user: dict = Depends(get_current_user)):
    """Update order status"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permissions
    user_role = current_user.get("role")
    if user_role == "business" and order["business_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role == "courier" and order.get("courier_id") != current_user["id"] and new_status != OrderStatus.ASSIGNED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif user_role not in ["admin", "business", "courier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    update_data = {"status": new_status}
    
    # Update timestamps based on status
    current_time = datetime.now(timezone.utc)
    if new_status == OrderStatus.ASSIGNED:
        update_data["assigned_at"] = current_time
        update_data["courier_id"] = current_user["id"]
        update_data["courier_name"] = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
    elif new_status == OrderStatus.ON_ROUTE:
        update_data["picked_up_at"] = current_time
    elif new_status == OrderStatus.DELIVERED:
        update_data["delivered_at"] = current_time
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": f"Order status updated to {new_status}"}

@api_router.post("/orders/{order_id}/accept")
async def accept_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """Accept an order (Courier only)"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can accept orders"
        )
    
    # Check if courier is KYC approved
    if current_user.get("kyc_status") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC approval required to accept orders"
        )
    
    # Find the order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if order is available for assignment
    if order.get("status") != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not available for assignment"
        )
    
    if order.get("courier_id") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already assigned to another courier"
        )
    
    # Assign order to courier
    update_data = {
        "status": "assigned",
        "courier_id": current_user["id"],
        "courier_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        "assigned_at": datetime.now(timezone.utc)
    }
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    return {
        "success": True, 
        "message": "Order successfully accepted",
        "order_id": order_id,
        "courier_name": update_data["courier_name"]
    }

# Admin Management Endpoints
@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_admin_user)):
    """Get all users (Admin only)"""
    users = await db.users.find({}).to_list(length=None)
    
    # Convert ObjectId and remove passwords
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
        if "password" in user:
            del user["password"]
        
        # Handle datetime conversion safely - handle both string and datetime types
        if "created_at" in user:
            if hasattr(user["created_at"], 'isoformat'):
                # It's a datetime object, convert to string
                user["created_at"] = user["created_at"].isoformat()
            # If it's already a string, leave it as is
            elif isinstance(user["created_at"], str):
                pass
            else:
                # If it's neither datetime nor string, convert to current time
                user["created_at"] = datetime.now(timezone.utc).isoformat()
    
    return users

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete user (Admin only) - Supports both UUID and ObjectId formats"""
    # Try to find user by both formats
    user = None
    
    # First try as ObjectId (for older users)
    try:
        from bson import ObjectId
        object_id = ObjectId(user_id)
        user = await db.users.find_one({"_id": object_id})
        if user:
            # Delete using ObjectId
            result = await db.users.delete_one({"_id": object_id})
            if result.deleted_count > 0:
                return {"message": "User deleted successfully", "user_id": user_id, "format": "ObjectId"}
    except:
        pass
    
    # Then try as UUID string (for newer users created via registration)
    user = await db.users.find_one({"id": user_id})
    if user:
        # Delete using id field
        result = await db.users.delete_one({"id": user_id})
        if result.deleted_count > 0:
            return {"message": "User deleted successfully", "user_id": user_id, "format": "UUID"}
    
    # If not found by either method
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@api_router.get("/admin/products")
async def get_all_products(current_user: dict = Depends(get_admin_user)):
    """Get all products (Admin only)"""
    products = await db.products.find({}).to_list(length=None)
    
    # Convert datetime and ObjectId
    for product in products:
        product["id"] = str(product["_id"])
        del product["_id"]
        
        # Handle datetime conversion safely
        if "created_at" in product:
            if isinstance(product["created_at"], str):
                # Already a string, keep as is
                pass
            elif hasattr(product["created_at"], 'isoformat'):
                # It's a datetime object, convert to string
                product["created_at"] = product["created_at"].isoformat()
            else:
                # Fallback for any other type
                product["created_at"] = str(product["created_at"])
    
    return products

@api_router.get("/admin/orders")
async def get_all_orders(current_user: dict = Depends(get_admin_user)):
    """Get all orders (Admin only)"""
    orders = await db.orders.find({}).to_list(length=None)
    
    # Convert datetime and ObjectId
    for order in orders:
        order["id"] = str(order["_id"])
        del order["_id"]
        # Handle datetime conversion safely
        if isinstance(order["created_at"], str):
            pass  # Already converted
        else:
            order["created_at"] = order["created_at"].isoformat()
        
        if order.get("assigned_at"):
            if isinstance(order["assigned_at"], str):
                pass  # Already converted
            else:
                order["assigned_at"] = order["assigned_at"].isoformat()
        
        if order.get("picked_up_at"):
            if isinstance(order["picked_up_at"], str):
                pass  # Already converted
            else:
                order["picked_up_at"] = order["picked_up_at"].isoformat()
        
        if order.get("delivered_at"):
            if isinstance(order["delivered_at"], str):
                pass  # Already converted
            else:
                order["delivered_at"] = order["delivered_at"].isoformat()
    
    return orders

# KYC Management Endpoints
@api_router.post("/couriers/kyc")
async def upload_kyc_documents(
    license_photo: UploadFile = File(None),
    vehicle_registration: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload KYC documents for courier (license and vehicle registration)"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Only couriers can upload KYC documents")
    
    courier_id = current_user["id"]
    upload_results = {}
    
    # Validate file types
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
    
    if license_photo:
        file_ext = Path(license_photo.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Ehliyet fotoğrafı için sadece JPG, PNG veya PDF dosyaları kabul edilir")
        
        # Save license photo
        license_filename = f"kyc_license_{courier_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        license_path = UPLOAD_DIR / license_filename
        
        with open(license_path, "wb") as buffer:
            shutil.copyfileobj(license_photo.file, buffer)
        
        upload_results["license_photo_url"] = f"/uploads/{license_filename}"
    
    if vehicle_registration:
        file_ext = Path(vehicle_registration.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Ruhsat fotoğrafı için sadece JPG, PNG veya PDF dosyaları kabul edilir")
        
        # Save vehicle registration
        vehicle_filename = f"kyc_vehicle_{courier_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        vehicle_path = UPLOAD_DIR / vehicle_filename
        
        with open(vehicle_path, "wb") as buffer:
            shutil.copyfileobj(vehicle_registration.file, buffer)
        
        upload_results["vehicle_registration_url"] = f"/uploads/{vehicle_filename}"
    
    # Update courier record with uploaded document URLs
    if upload_results:
        update_data = {}
        if "license_photo_url" in upload_results:
            update_data["license_photo_url"] = upload_results["license_photo_url"]
        if "vehicle_registration_url" in upload_results:
            update_data["vehicle_registration_url"] = upload_results["vehicle_registration_url"]
        
        update_data["kyc_documents_updated_at"] = datetime.now(timezone.utc)
        update_data["kyc_status"] = "pending"  # Reset to pending when new documents are uploaded
        
        await db.users.update_one(
            {"id": courier_id},
            {"$set": update_data}
        )
    
    return {
        "message": "KYC belgeleri başarıyla yüklendi",
        "uploaded_documents": upload_results
    }

@api_router.get("/admin/couriers/kyc")
async def get_couriers_for_kyc(current_user: dict = Depends(get_admin_user)):
    """Get all couriers with their KYC documents for approval"""
    couriers = await db.users.find({"role": "courier"}).to_list(length=None)
    
    # Clean up data and use proper ID field
    for courier in couriers:
        # Remove MongoDB ObjectId field 
        if "_id" in courier:
            del courier["_id"]
        # Remove password for security
        if "password" in courier:
            del courier["password"]
        # Convert datetime to string
        if "created_at" in courier:
            courier["created_at"] = courier["created_at"].isoformat()
    
    return couriers

@api_router.patch("/admin/couriers/{courier_id}/kyc")
async def update_courier_kyc_status(
    courier_id: str, 
    kyc_status: str,  # approved, rejected, pending
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Update courier KYC status (Admin only)"""
    if kyc_status not in ["approved", "rejected", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid KYC status"
        )
    
    # Check if courier exists
    courier = await db.users.find_one({"id": courier_id, "role": "courier"})
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier not found"
        )
    
    # Get notes from request body if available
    notes = None
    try:
        body = await request.json()
        notes = body.get("notes", "")
    except:
        pass
    
    update_data = {
        "kyc_status": kyc_status,
        "kyc_reviewed_at": datetime.now(timezone.utc),
        "kyc_reviewed_by": current_user["id"],
        "updated_at": datetime.now(timezone.utc)
    }
    
    if notes and notes.strip():
        update_data["kyc_notes"] = notes.strip()
    
    await db.users.update_one(
        {"id": courier_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": f"KYC status updated to {kyc_status}"}

# Public Business Endpoints for Customers
@api_router.get("/businesses")
async def get_public_businesses():
    """Get all active businesses for customers"""
    try:
        businesses = await db.users.find({
            "role": "business",
            "kyc_status": "approved"  # Only show approved businesses
        }).to_list(length=None)
        
        business_list = []
        for business in businesses:
            # Add location data (Istanbul districts for demo)
            istanbul_districts = [
                {"name": "Sultanahmet", "lat": 41.0082, "lng": 28.9784},
                {"name": "Beyoğlu", "lat": 41.0369, "lng": 28.9850},
                {"name": "Şişli", "lat": 41.0498, "lng": 28.9662},
                {"name": "Beşiktaş", "lat": 41.0766, "lng": 28.9688},
                {"name": "Kadıköy", "lat": 41.0058, "lng": 29.0281},
                {"name": "Ataşehir", "lat": 40.9969, "lng": 29.0833},
                {"name": "Üsküdar", "lat": 41.0431, "lng": 29.0088},
                {"name": "Sarıyer", "lat": 41.1058, "lng": 29.0074},
            ]
            
            # Assign location based on business ID
            district = istanbul_districts[hash(business["id"]) % len(istanbul_districts)]
            
            business_data = {
                "id": business.get("id"),
                "name": business.get("business_name", "İsimsiz İşletme"),
                "category": business.get("business_category", "gida"),
                "description": business.get("description", "Lezzetli yemekler sizi bekliyor..."),
                "rating": round(4.0 + (hash(business["id"]) % 15) / 10, 1),
                "delivery_time": f"{20 + (hash(business['id']) % 20)}-{35 + (hash(business['id']) % 15)}",
                "min_order": 50 + (hash(business["id"]) % 50),
                "location": district,
                "is_open": True,
                "phone": business.get("phone"),
                "address": f"{district['name']}, İstanbul",
                "image_url": f"/api/placeholder/restaurant-{hash(business['id']) % 10}.jpg"
            }
            business_list.append(business_data)
        
        return business_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching businesses: {str(e)}")

@api_router.patch("/admin/users/{user_id}/approve")
async def approve_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Approve any user (business, courier) for KYC"""
    try:
        # Update user with approved status
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"kyc_status": "approved"}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"success": True, "message": f"User {user_id} approved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving user: {str(e)}")

@api_router.get("/businesses/{business_id}/products")
async def get_business_products(business_id: str):
    """Get products for a specific business"""
    try:
        products = await db.products.find({"business_id": business_id}).to_list(length=None)
        return [Product(**product).dict() for product in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

    INACTIVE = "inactive"
    BANNED = "banned"

class OrderType(str, Enum):
    FOOD = "food"
    PACKAGE = "package"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class SystemStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    LIMITED = "limited"

# Configuration Model
class SystemConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    value: Any
    description: Optional[str] = None
    category: str = "general"
    updated_by: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Audit Log Model
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str
    target_type: str  # user, order, payment, etc.
    target_id: str
    user_id: str
    user_role: str
    ip_address: str
    user_agent: Optional[str] = None
    old_data: Optional[dict] = None
    new_data: Optional[dict] = None
    description: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Ticket System Models
class SupportTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str
    user_id: str
    order_id: Optional[str] = None
    subject: str
    description: str
    category: str  # payment, delivery, account, refund
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    assigned_to: Optional[str] = None
    tags: List[str] = []
    attachments: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TicketMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    sender_id: str
    sender_type: str  # customer, admin, system
    message: str
    attachments: List[str] = []
    is_internal: bool = False  # Internal admin notes
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Financial Report Models
class CommissionReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_orders: int
    total_revenue: float
    total_commission: float
    courier_payments: float
    business_payments: float
    breakdown_by_category: dict
    top_performing_couriers: List[dict]
    top_businesses: List[dict]

# WebSocket connection manager (enhanced)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.admin_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user_type: str = "user"):
        await websocket.accept()
        if user_type == "admin":
            self.admin_connections[user_id] = websocket
        else:
            self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str, user_type: str = "user"):
        connections = self.admin_connections if user_type == "admin" else self.active_connections
        if user_id in connections:
            del connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_to_admins(self, message: dict):
        """Broadcast message to all connected admin users"""
        disconnected = []
        for admin_id, connection in self.admin_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(admin_id)
        
        # Clean up disconnected admin connections
        for admin_id in disconnected:
            del self.admin_connections[admin_id]

manager = ConnectionManager()

# Location & Distance Utils
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula ile iki nokta arasındaki mesafeyi km olarak hesaplar"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# Simple password hashing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_v2(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        
        # Get user from database to check current status
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
        
        if user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Hesabınız askıya alınmış")
        
        return user  # Return full user object, not just ID
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

async def get_admin_user_v2(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin yetkisi kontrolü"""
    user = await get_current_user(credentials)  # Use the first get_current_user function
    
    if not user or user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    return user

# Audit logging function
async def log_action(action_type: str, target_type: str, target_id: str, 
                    user_id: str, ip_address: str, description: str,
                    old_data: dict = None, new_data: dict = None, user_agent: str = None):
    """Audit log kaydı oluştur"""
    user = await db.users.find_one({"id": user_id})
    user_role = user.get("user_type", "unknown") if user else "unknown"
    
    audit_log = AuditLog(
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        user_id=user_id,
        user_role=user_role,
        ip_address=ip_address,
        user_agent=user_agent,
        old_data=old_data,
        new_data=new_data,
        description=description
    )
    
    audit_dict = audit_log.dict()
    audit_dict["timestamp"] = audit_log.timestamp.isoformat()
    await db.audit_logs.insert_one(audit_dict)

# System configuration management
async def get_system_config(key: str, default_value: Any = None) -> Any:
    """Sistem konfigürasyonu al"""
    config = await db.system_configs.find_one({"key": key})
    return config.get("value", default_value) if config else default_value

async def set_system_config(key: str, value: Any, user_id: str, description: str = None):
    """Sistem konfigürasyonu ayarla"""
    existing_config = await db.system_configs.find_one({"key": key})
    
    config = SystemConfig(
        key=key,
        value=value,
        description=description,
        updated_by=user_id
    )
    
    if existing_config:
        await db.system_configs.update_one(
            {"key": key},
            {"$set": config.dict()}
        )
    else:
        await db.system_configs.insert_one(config.dict())

# Initialize default commission settings
async def initialize_default_configs():
    """Initialize default system configurations"""
    defaults = [
        ("platform_commission_rate", 0.05, "Platform komisyon oranı (varsayılan %5)"),
        ("courier_commission_rate", 0.05, "Kurye komisyon oranı (varsayılan %5)"),
        ("restaurant_fee_rate", 0.95, "Restoran gelir oranı (varsayılan %95)"),
        ("service_fee_enabled", False, "Müşteri servis bedeli (kapalı)"),
        ("delivery_fee_enabled", False, "Teslimat ücreti (kapalı)"),
    ]
    
    for key, value, description in defaults:
        existing = await db.system_configs.find_one({"key": key})
        if not existing:
            await set_system_config(key, value, "system", description)

# Initialize default admin user
async def initialize_admin_user():
    """Create default admin user if not exists"""
    admin_email = "admin@kuryecini.com"
    existing_admin = await db.users.find_one({"email": admin_email})
    
    if not existing_admin:
        # Create secure admin user
        admin_password = "KuryeciniAdmin2024!"  # Strong default password
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": password_hash.decode('utf-8'),  # Fixed: use password_hash instead of password
            "first_name": "Admin",
            "last_name": "Kuryecini",
            "role": "admin",
            "is_active": True,
            "kyc_status": "approved",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(admin_user)
        print(f"✅ Default admin user created: {admin_email} / {admin_password}")
        return admin_password
    else:
        print(f"ℹ️ Admin user already exists: {admin_email}")
        return None

# Call initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    await initialize_default_configs()
    await initialize_admin_user()

# EXISTING MODELS (keeping previous models)
class Location(BaseModel):
    lat: float
    lon: float
    address: str
    city: str

class CourierRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    iban: str
    vehicle_type: str
    vehicle_model: str
    license_class: str
    city: str

class CustomerRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    city: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_data: dict

# ADMIN MODELS
class AdminCreateTicketRequest(BaseModel):
    user_id: str
    order_id: Optional[str] = None
    subject: str
    description: str
    category: str
    priority: TicketPriority = TicketPriority.MEDIUM

class UpdateUserStatusRequest(BaseModel):
    status: UserStatus
    reason: str
    notes: Optional[str] = None

class CourierDocumentReview(BaseModel):
    action: str  # approve, reject, request_resubmission
    notes: str
    reviewed_documents: List[str] = []

class BusinessMenuApproval(BaseModel):
    menu_item_id: str
    action: str  # approve, reject
    notes: Optional[str] = None

class SLAViolationReport(BaseModel):
    order_id: str
    violation_type: str  # late_pickup, late_delivery, no_show
    expected_time: datetime
    actual_time: Optional[datetime] = None
    severity: str  # minor, major, critical
    notes: str

class RefundProcessRequest(BaseModel):
    order_id: str
    refund_amount: float
    refund_reason: str
    refund_type: str  # full, partial
    notify_customer: bool = True

# DUPLICATE LOGIN ENDPOINT REMOVED - Using the first login endpoint instead

# EXISTING REGISTRATION ENDPOINTS (keeping previous implementation)
@api_router.post("/register/courier", response_model=LoginResponse)
async def register_courier(courier_data: CourierRegister, request: Request):
    """Kurye kaydı"""
    existing_user = await db.users.find_one({"email": courier_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    password_hash = hash_password(courier_data.password)
    user = {
        "id": str(uuid.uuid4()),
        "email": courier_data.email,
        "password_hash": password_hash,
        "user_type": "courier",
        "is_verified": True,
        "is_active": False,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    courier = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "first_name": courier_data.first_name,
        "last_name": courier_data.last_name,
        "iban": courier_data.iban,
        "vehicle_type": courier_data.vehicle_type,
        "vehicle_model": courier_data.vehicle_model,
        "license_class": courier_data.license_class,
        "city": courier_data.city,
        "kyc_status": "pending",
        "is_online": False,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.couriers.insert_one(courier)
    
    # Create initial balance
    balance = {
        "courier_id": courier["id"],
        "available_balance": 0.0,
        "pending_balance": 0.0,
        "total_earnings": 0.0,
        "total_deliveries": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.courier_balances.insert_one(balance)
    
    # Log registration
    await log_action(
        action_type="register",
        target_type="courier",
        target_id=courier["id"],
        user_id=user["id"],
        ip_address=request.client.host,
        description=f"Courier registration: {courier_data.email}",
        new_data={"courier_id": courier["id"], "name": f"{courier_data.first_name} {courier_data.last_name}"}
    )
    
    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="courier",
        user_data={
            "email": user["email"],
            "name": f"{courier['first_name']} {courier['last_name']}",
            "city": courier["city"],
            "kyc_status": "pending",
            "balance": 0,
            "status": "active"
        }
    )

# ADMIN USER MANAGEMENT ENDPOINTS - DUPLICATE (COMMENTED OUT)
# @api_router.get("/admin/users")
# async def get_all_users_paginated(
#     user_type: Optional[str] = None,
#     status: Optional[str] = None,
#     city: Optional[str] = None,
#     page: int = 1,
#     limit: int = 50,
#     current_user_id: str = Depends(get_admin_user)
# ):
#     """Tüm kullanıcıları listele"""
#     query = {}
#     if user_type:
#         query["user_type"] = user_type
#     if status:
#         query["status"] = status
#     
#     skip = (page - 1) * limit
#     users = await db.users.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(length=None)
#     total_count = await db.users.count_documents(query)
#     
#     # Enrich user data
#     enriched_users = []
#     for user in users:
#         user_info = {
#             "id": user["id"],
#             "email": user["email"],
#             "user_type": user["user_type"],
#             "status": user.get("status", "active"),
#             "created_at": user["created_at"],
#             "last_login": user.get("last_login")
#         }
#         
#         if user["user_type"] == "courier":
#             courier = await db.couriers.find_one({"user_id": user["id"]})
#             if courier:
#                 balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
#                 user_info.update({
#                     "name": f"{courier['first_name']} {courier['last_name']}",
#                     "city": courier["city"],
#                     "vehicle_type": courier["vehicle_type"],
#                     "kyc_status": courier["kyc_status"],
#                     "is_online": courier.get("is_online", False),
#                     "total_deliveries": balance.get("total_deliveries", 0) if balance else 0,
#                     "total_earnings": balance.get("total_earnings", 0) if balance else 0
#                 })
#         elif user["user_type"] == "business":
#             business = await db.businesses.find_one({"user_id": user["id"]})
#             if business:
#                 user_info.update({
#                     "business_name": business["business_name"],
#                     "city": business["city"],
#                     "category": business["business_category"],
#                     "is_open": business.get("is_open", False)
#                 })
#         elif user["user_type"] == "customer":
#             customer = await db.customers.find_one({"user_id": user["id"]})
#             if customer:
#                 user_info.update({
#                     "name": f"{customer['first_name']} {customer['last_name']}",
#                     "city": customer["city"]
#                 })
#         
#         enriched_users.append(user_info)
#     
#     return {
#         "users": enriched_users,
#         "pagination": {
#             "page": page,
#             "limit": limit,
#             "total": total_count,
#             "pages": math.ceil(total_count / limit)
#         }
#     }

@api_router.post("/admin/users/{user_id}/update-status")
async def update_user_status(
    user_id: str,
    status_update: UpdateUserStatusRequest,
    request: Request,
    current_user_id: str = Depends(get_admin_user)
):
    """Kullanıcı durumunu güncelle (askıya alma, aktivasyon)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    old_status = user.get("status", "active")
    
    # Update user status
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "status": status_update.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log action
    await log_action(
        action_type="status_update",
        target_type="user",
        target_id=user_id,
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"User status changed from {old_status} to {status_update.status}: {status_update.reason}",
        old_data={"status": old_status},
        new_data={"status": status_update.status, "reason": status_update.reason}
    )
    
    # Notify user if suspended
    if status_update.status == "suspended":
        # Send notification (implementation would depend on notification service)
        pass
    
    return {"success": True, "message": "Kullanıcı durumu güncellendi"}

@api_router.post("/admin/couriers/{courier_id}/document-review")
async def review_courier_documents(
    courier_id: str,
    review_data: CourierDocumentReview,
    request: Request,
    current_user_id: str = Depends(get_admin_user)
):
    """Kurye belgelerini incele ve onayla/reddet"""
    courier = await db.couriers.find_one({"id": courier_id})
    if not courier:
        raise HTTPException(status_code=404, detail="Kurye bulunamadı")
    
    old_status = courier.get("kyc_status", "pending")
    
    if review_data.action == "approve":
        new_status = "approved"
        # Activate user
        await db.users.update_one(
            {"id": courier["user_id"]},
            {"$set": {"is_active": True}}
        )
    elif review_data.action == "reject":
        new_status = "rejected"
    else:
        new_status = "pending"
    
    # Update courier KYC status
    await db.couriers.update_one(
        {"id": courier_id},
        {"$set": {
            "kyc_status": new_status,
            "kyc_notes": review_data.notes,
            "document_review_date": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": current_user_id
        }}
    )
    
    # Log document review
    await log_action(
        action_type="document_review",
        target_type="courier",
        target_id=courier_id,
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"Courier documents {review_data.action}: {review_data.notes}",
        old_data={"kyc_status": old_status},
        new_data={
            "kyc_status": new_status, 
            "action": review_data.action,
            "reviewed_documents": review_data.reviewed_documents
        }
    )
    
    return {"success": True, "message": f"Kurye belgeleri {review_data.action} edildi"}

# FINANCIAL MANAGEMENT ENDPOINTS
@api_router.get("/admin/financial/commission-report")
async def get_commission_report(
    start_date: str,
    end_date: str,
    current_user_id: str = Depends(get_admin_user)
):
    """Komisyon raporu oluştur"""
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get orders in date range
        orders = await db.orders.find({
            "created_at": {
                "$gte": start_dt.isoformat(),
                "$lte": end_dt.isoformat()
            },
            "status": "delivered"
        }).to_list(length=None)
        
        # Calculate totals
        total_orders = len(orders)
        total_revenue = sum(order.get("total", 0) for order in orders)
        total_commission = sum(order.get("commission", 0) for order in orders)
        courier_payments = sum(order.get("courier_earning", 0) for order in orders)
        
        # Breakdown by category
        category_breakdown = {}
        for order in orders:
            if order.get("business_id"):
                business = await db.businesses.find_one({"id": order["business_id"]})
                category = business.get("business_category", "unknown") if business else "unknown"
                
                if category not in category_breakdown:
                    category_breakdown[category] = {
                        "orders": 0,
                        "revenue": 0,
                        "commission": 0
                    }
                
                category_breakdown[category]["orders"] += 1
                category_breakdown[category]["revenue"] += order.get("total", 0)
                category_breakdown[category]["commission"] += order.get("commission", 0)
        
        # Top performing couriers
        courier_stats = {}
        for order in orders:
            if order.get("courier_id"):
                courier_id = order["courier_id"]
                if courier_id not in courier_stats:
                    courier_stats[courier_id] = {
                        "deliveries": 0,
                        "earnings": 0
                    }
                
                courier_stats[courier_id]["deliveries"] += 1
                courier_stats[courier_id]["earnings"] += order.get("courier_earning", 0)
        
        # Get courier names
        top_couriers = []
        for courier_id, stats in sorted(courier_stats.items(), key=lambda x: x[1]["earnings"], reverse=True)[:10]:
            courier = await db.couriers.find_one({"id": courier_id})
            if courier:
                top_couriers.append({
                    "courier_id": courier_id,
                    "name": f"{courier['first_name']} {courier['last_name']}",
                    "deliveries": stats["deliveries"],
                    "earnings": round(stats["earnings"], 2)
                })
        
        return CommissionReport(
            period_start=start_dt,
            period_end=end_dt,
            total_orders=total_orders,
            total_revenue=round(total_revenue, 2),
            total_commission=round(total_commission, 2),
            courier_payments=round(courier_payments, 2),
            business_payments=round(total_revenue - total_commission - courier_payments, 2),
            breakdown_by_category=category_breakdown,
            top_performing_couriers=top_couriers,
            top_businesses=[]  # Would be calculated similarly
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulamadı: {str(e)}")

@api_router.get("/admin/financial/courier-balances")
async def get_all_courier_balances(
    city: Optional[str] = None,
    min_balance: Optional[float] = None,
    current_user_id: str = Depends(get_admin_user)
):
    """Tüm kurye bakiyelerini listele"""
    query = {}
    if city:
        # First get couriers from that city
        couriers_in_city = await db.couriers.find({"city": city}).to_list(length=None)
        courier_ids = [c["id"] for c in couriers_in_city]
        query["courier_id"] = {"$in": courier_ids}
    
    balances = await db.courier_balances.find(query).to_list(length=None)
    
    enriched_balances = []
    for balance in balances:
        courier = await db.couriers.find_one({"id": balance["courier_id"]})
        if courier and (not min_balance or balance.get("available_balance", 0) >= min_balance):
            enriched_balances.append({
                "courier_id": balance["courier_id"],
                "courier_name": f"{courier['first_name']} {courier['last_name']}",
                "city": courier["city"],
                "available_balance": balance.get("available_balance", 0),
                "pending_balance": balance.get("pending_balance", 0),
                "total_earnings": balance.get("total_earnings", 0),
                "total_deliveries": balance.get("total_deliveries", 0),
                "last_updated": balance.get("last_updated")
            })
    
    return {"courier_balances": enriched_balances}

# LIVE ORDER TRACKING AND SLA MONITORING
@api_router.get("/admin/orders/live-map")
async def get_live_order_map(current_user_id: str = Depends(get_admin_user)):
    """Canlı sipariş haritası için veri"""
    # Get active orders
    active_orders = await db.orders.find({
        "status": {"$in": ["confirmed", "preparing", "ready", "picked_up", "delivering"]}
    }).to_list(length=None)
    
    # Get online couriers
    online_couriers = await db.couriers.find({
        "is_online": True,
        "current_location": {"$exists": True}
    }).to_list(length=None)
    
    # Enrich data for map display
    map_data = {
        "orders": [],
        "couriers": []
    }
    
    for order in active_orders:
        order_info = {
            "order_id": order["id"],
            "status": order["status"],
            "pickup_location": order.get("pickup_location", {}),
            "delivery_location": order.get("delivery_location", {}),
            "courier_id": order.get("courier_id"),
            "estimated_delivery": order.get("estimated_delivery_time"),
            "sla_status": "on_time"  # Would calculate based on timestamps
        }
        
        # Calculate SLA status
        if order["status"] in ["picked_up", "delivering"]:
            # Check if delivery is late
            pickup_time = order.get("picked_up_at")
            if pickup_time:
                pickup_dt = datetime.fromisoformat(pickup_time)
                expected_delivery = pickup_time + timedelta(minutes=order.get("estimated_delivery_time", 30))
                if datetime.now(timezone.utc) > expected_delivery:
                    order_info["sla_status"] = "late"
        
        map_data["orders"].append(order_info)
    
    for courier in online_couriers:
        user = await db.users.find_one({"id": courier["user_id"]})
        if user:
            courier_info = {
                "courier_id": courier["id"],
                "name": f"{courier['first_name']} {courier['last_name']}",
                "location": courier.get("current_location", {}),
                "vehicle_type": courier["vehicle_type"],
                "current_order": None,  # Would check for assigned orders
                "status": "available"  # available, busy, unavailable
            }
            
            # Check if courier has active order
            active_courier_order = await db.orders.find_one({
                "courier_id": courier["id"],
                "status": {"$in": ["picked_up", "delivering"]}
            })
            
            if active_courier_order:
                courier_info["current_order"] = active_courier_order["id"]
                courier_info["status"] = "busy"
            
            map_data["couriers"].append(courier_info)
    
    return map_data

@api_router.post("/admin/orders/{order_id}/sla-violation")
async def report_sla_violation(
    order_id: str,
    violation_data: SLAViolationReport,
    request: Request,
    current_user_id: str = Depends(get_admin_user)
):
    """SLA ihlali rapor et"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    
    # Create SLA violation record
    sla_violation = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "courier_id": order.get("courier_id"),
        "business_id": order.get("business_id"),
        "violation_type": violation_data.violation_type,
        "expected_time": violation_data.expected_time.isoformat(),
        "actual_time": violation_data.actual_time.isoformat() if violation_data.actual_time else None,
        "severity": violation_data.severity,
        "notes": violation_data.notes,
        "reported_by": current_user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False
    }
    
    await db.sla_violations.insert_one(sla_violation)
    
    # Log SLA violation
    await log_action(
        action_type="sla_violation",
        target_type="order",
        target_id=order_id,
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"SLA violation reported: {violation_data.violation_type} - {violation_data.notes}",
        new_data=sla_violation
    )
    
    # Notify relevant parties
    await manager.broadcast_to_admins({
        "type": "sla_violation",
        "order_id": order_id,
        "violation_type": violation_data.violation_type,
        "severity": violation_data.severity
    })
    
    return {"success": True, "message": "SLA ihlali kaydedildi"}

# SUPPORT TICKET SYSTEM
@api_router.post("/tickets/create")
async def create_support_ticket(
    ticket_data: AdminCreateTicketRequest,
    request: Request,
    current_user_id: str = Depends(get_current_user)
):
    """Destek bileti oluştur"""
    ticket_number = f"TKT{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
    
    ticket = SupportTicket(
        ticket_number=ticket_number,
        user_id=ticket_data.user_id,
        order_id=ticket_data.order_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority
    )
    
    ticket_dict = ticket.dict()
    ticket_dict["created_at"] = ticket.created_at.isoformat()
    ticket_dict["updated_at"] = ticket.updated_at.isoformat()
    
    await db.support_tickets.insert_one(ticket_dict)
    
    # Log ticket creation
    await log_action(
        action_type="ticket_create",
        target_type="ticket",
        target_id=ticket.id,
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"Support ticket created: {ticket_data.subject}",
        new_data={"ticket_number": ticket_number, "category": ticket_data.category}
    )
    
    return {"success": True, "ticket_id": ticket.id, "ticket_number": ticket_number}

@api_router.get("/admin/tickets")
async def get_support_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    limit: int = 25,
    current_user_id: str = Depends(get_admin_user)
):
    """Destek biletlerini listele"""
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if priority:
        query["priority"] = priority
    
    skip = (page - 1) * limit
    tickets = await db.support_tickets.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(length=None)
    total_count = await db.support_tickets.count_documents(query)
    
    # Enrich with user data
    enriched_tickets = []
    for ticket in tickets:
        user = await db.users.find_one({"id": ticket["user_id"]})
        ticket_info = {
            "id": ticket["id"],
            "ticket_number": ticket["ticket_number"],
            "subject": ticket["subject"],
            "category": ticket["category"],
            "priority": ticket["priority"],
            "status": ticket["status"],
            "created_at": ticket["created_at"],
            "user_email": user["email"] if user else "Unknown",
            "user_type": user["user_type"] if user else "Unknown",
            "order_id": ticket.get("order_id")
        }
        enriched_tickets.append(ticket_info)
    
    return {
        "tickets": enriched_tickets,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": math.ceil(total_count / limit)
        }
    }

@api_router.post("/orders/{order_id}/refund")
async def process_refund(
    order_id: str,
    refund_data: RefundProcessRequest,
    request: Request,
    current_user_id: str = Depends(get_admin_user)
):
    """İade işlemi gerçekleştir"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    
    if order["status"] not in ["delivered", "cancelled"]:
        raise HTTPException(status_code=400, detail="Bu sipariş durumunda iade yapılamaz")
    
    # Create refund record
    refund = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "customer_id": order["customer_id"],
        "refund_amount": refund_data.refund_amount,
        "refund_reason": refund_data.refund_reason,
        "refund_type": refund_data.refund_type,
        "processed_by": current_user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "processed"
    }
    
    await db.refunds.insert_one(refund)
    
    # Update order status
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": "refunded",
            "refund_amount": refund_data.refund_amount,
            "refunded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log refund process
    await log_action(
        action_type="refund_process",
        target_type="order",
        target_id=order_id,
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"Refund processed: {refund_data.refund_amount} TRY - {refund_data.refund_reason}",
        new_data=refund
    )
    
    return {"success": True, "message": "İade işlemi tamamlandı", "refund_id": refund["id"]}

# SYSTEM CONFIGURATION ENDPOINTS
@api_router.get("/admin/config")
async def get_system_configurations(current_user: dict = Depends(get_admin_user)):
    """Sistem konfigürasyonlarını getir"""
    configs = await db.system_configs.find().to_list(length=None)
    
    config_dict = {}
    for config in configs:
        config_dict[config["key"]] = {
            "value": config["value"],
            "description": config.get("description"),
            "category": config.get("category", "general"),
            "updated_by": config["updated_by"],
            "updated_at": config["updated_at"]
        }
    
    return {"configurations": config_dict}

@api_router.post("/admin/config/update")
async def update_system_configuration(
    config_key: str,
    config_value: Any,
    request: Request,
    description: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Sistem konfigürasyonu güncelle"""
    old_config = await db.system_configs.find_one({"key": config_key})
    old_value = old_config.get("value") if old_config else None
    
    await set_system_config(config_key, config_value, current_user["id"], description)
    
    # Log configuration change
    await log_action(
        action_type="config_update",
        target_type="system_config",
        target_id=config_key,
        user_id=current_user["id"],
        ip_address=request.client.host,
        description=f"System configuration updated: {config_key}",
        old_data={"value": old_value},
        new_data={"value": config_value, "description": description}
    )
    
    return {"success": True, "message": "Konfigürasyon güncellendi"}

# AUDIT LOG ENDPOINTS
@api_router.get("/admin/audit-logs")
async def get_audit_logs(
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user_id: str = Depends(get_admin_user)
):
    """Audit loglarını getir"""
    query = {}
    
    if action_type:
        query["action_type"] = action_type
    if target_type:
        query["target_type"] = target_type
    if user_id:
        query["user_id"] = user_id
    if start_date and end_date:
        query["timestamp"] = {
            "$gte": start_date,
            "$lte": end_date
        }
    
    skip = (page - 1) * limit
    logs = await db.audit_logs.find(query).skip(skip).limit(limit).sort("timestamp", -1).to_list(length=None)
    total_count = await db.audit_logs.count_documents(query)
    
    # Enrich with user names
    enriched_logs = []
    for log in logs:
        user = await db.users.find_one({"id": log["user_id"]})
        log_info = {
            "id": log["id"],
            "action_type": log["action_type"],
            "target_type": log["target_type"],
            "target_id": log["target_id"],
            "user_email": user["email"] if user else "Unknown",
            "user_role": log["user_role"],
            "ip_address": log["ip_address"],
            "description": log["description"],
            "timestamp": log["timestamp"],
            "has_data_changes": bool(log.get("old_data") or log.get("new_data"))
        }
        enriched_logs.append(log_info)
    
    return {
        "audit_logs": enriched_logs,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": math.ceil(total_count / limit)
        }
    }

# SYSTEM RULES MANAGEMENT
@api_router.post("/admin/rules/delivery-distance")
async def update_delivery_distance_rules(
    min_distance: float,
    max_distance: float,
    request: Request,
    current_user_id: str = Depends(get_admin_user)
):
    """Teslimat mesafesi kurallarını güncelle"""
    await set_system_config("min_delivery_distance", min_distance, current_user_id, "Minimum teslimat mesafesi (km)")
    await set_system_config("max_delivery_distance", max_distance, current_user_id, "Maximum teslimat mesafesi (km)")
    
    await log_action(
        action_type="rules_update",
        target_type="system_rules",
        target_id="delivery_distance",
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"Delivery distance rules updated: {min_distance}km - {max_distance}km"
    )
    
    return {"success": True, "message": "Teslimat mesafe kuralları güncellendi"}

@api_router.post("/admin/system/maintenance-mode")
async def toggle_maintenance_mode(
    enabled: bool,
    request: Request,
    message: Optional[str] = None,
    current_user_id: str = Depends(get_admin_user)
):
    """Bakım modunu aç/kapat"""
    await set_system_config("maintenance_mode", enabled, current_user_id, "Bakım modu durumu")
    await set_system_config("maintenance_message", message or "Sistem bakımda", current_user_id, "Bakım modu mesajı")
    
    await log_action(
        action_type="maintenance_mode",
        target_type="system",
        target_id="maintenance",
        user_id=current_user_id,
        ip_address=request.client.host,
        description=f"Maintenance mode {'enabled' if enabled else 'disabled'}: {message}"
    )
    
    # Notify all admin users
    await manager.broadcast_to_admins({
        "type": "maintenance_mode_changed",
        "enabled": enabled,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": f"Bakım modu {'açıldı' if enabled else 'kapatıldı'}"}

@api_router.post("/admin/config/commission")
async def update_commission_settings(
    platform_commission: float,
    courier_commission: float,
    request: Request,
    current_user: dict = Depends(get_admin_user)
):
    """Update commission settings (Admin only)"""
    # Validate commission rates
    if not (0.0 <= platform_commission <= 0.2):
        raise HTTPException(status_code=400, detail="Platform komisyonu 0% ile 20% arasında olmalıdır")
    
    if not (0.0 <= courier_commission <= 0.2):
        raise HTTPException(status_code=400, detail="Kurye komisyonu 0% ile 20% arasında olmalıdır")
    
    # Calculate restaurant fee rate (remaining after platform and courier commissions)
    restaurant_fee_rate = 1.0 - platform_commission - courier_commission
    
    if restaurant_fee_rate < 0.6:  # Ensure restaurant gets at least 60%
        raise HTTPException(status_code=400, detail="Restoran payı minimum %60 olmalıdır")
    
    # Update configuration
    user_id = current_user["id"]
    await set_system_config("platform_commission_rate", platform_commission, user_id, "Platform komisyon oranı")
    await set_system_config("courier_commission_rate", courier_commission, user_id, "Kurye komisyon oranı") 
    await set_system_config("restaurant_fee_rate", restaurant_fee_rate, user_id, "Restoran gelir oranı")
    
    # Log the change
    await log_action(
        action_type="commission_update",
        target_type="system_config", 
        target_id="commission_rates",
        user_id=user_id,
        ip_address=request.client.host,
        description=f"Komisyon oranları güncellendi: Platform {platform_commission*100:.1f}%, Kurye {courier_commission*100:.1f}%, Restoran {restaurant_fee_rate*100:.1f}%"
    )
    
    return {
        "message": "Komisyon oranları başarıyla güncellendi",
        "platform_commission": f"{platform_commission*100:.1f}%",
        "courier_commission": f"{courier_commission*100:.1f}%", 
        "restaurant_fee": f"{restaurant_fee_rate*100:.1f}%"
    }

@api_router.get("/admin/config/commission")
async def get_commission_settings(current_user: dict = Depends(get_admin_user)):
    """Get current commission settings"""
    platform_rate = await get_system_config("platform_commission_rate", 0.05)
    courier_rate = await get_system_config("courier_commission_rate", 0.05)
    restaurant_rate = await get_system_config("restaurant_fee_rate", 0.9)
    
    return {
        "platform_commission_rate": platform_rate,
        "courier_commission_rate": courier_rate,
        "restaurant_fee_rate": restaurant_rate,
        "platform_commission_percent": f"{platform_rate*100:.1f}%",
        "courier_commission_percent": f"{courier_rate*100:.1f}%",
        "restaurant_fee_percent": f"{restaurant_rate*100:.1f}%"
    }

# EXISTING ENDPOINTS (keeping all previous functionality)
# ... (all previous registration, order, location endpoints remain the same)

# File Upload
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Dosya yükleme endpoint'i"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya seçilmedi")
    
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Sadece JPEG, PNG dosyaları yüklenebilir")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/uploads/{unique_filename}"
    return {"file_url": file_url}

# Campaign Management Endpoints
@api_router.get("/campaigns")
async def get_active_campaigns():
    """Get all active campaigns"""
    campaigns = await db.campaigns.find({
        "status": "active",
        "start_date": {"$lte": datetime.now(timezone.utc)},
        "end_date": {"$gte": datetime.now(timezone.utc)}
    }).to_list(length=None)
    
    for campaign in campaigns:
        campaign["id"] = str(campaign["_id"])
        del campaign["_id"]
        campaign["start_date"] = campaign["start_date"].isoformat()
        campaign["end_date"] = campaign["end_date"].isoformat()
        campaign["created_at"] = campaign["created_at"].isoformat()
    
    return campaigns

@api_router.post("/campaigns")
async def create_campaign(campaign_data: dict, current_user: dict = Depends(get_current_user)):
    """Create new campaign (Business owners only)"""
    if current_user.get("role") != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only business owners can create campaigns"
        )
    
    campaign_data["business_id"] = current_user["id"]
    campaign_data["id"] = str(uuid.uuid4())
    campaign_data["created_at"] = datetime.now(timezone.utc)
    campaign_data["start_date"] = datetime.fromisoformat(campaign_data["start_date"].replace('Z', '+00:00'))
    campaign_data["end_date"] = datetime.fromisoformat(campaign_data["end_date"].replace('Z', '+00:00'))
    
    await db.campaigns.insert_one(campaign_data)
    return {"message": "Campaign created successfully", "campaign_id": campaign_data["id"]}

# Loyalty System Endpoints
@api_router.get("/loyalty/points")
async def get_user_loyalty_points(current_user: dict = Depends(get_current_user)):
    """Get user's loyalty points"""
    loyalty = await db.user_loyalty.find_one({"user_id": current_user["id"]})
    
    if not loyalty:
        # Create initial loyalty record
        loyalty = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "total_points": 0,
            "lifetime_points": 0,
            "tier_level": "Bronze",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_loyalty.insert_one(loyalty)
    
    return {
        "total_points": loyalty["total_points"],
        "lifetime_points": loyalty["lifetime_points"],
        "tier_level": loyalty["tier_level"]
    }

@api_router.post("/loyalty/earn")
async def earn_loyalty_points(order_id: str, current_user: dict = Depends(get_current_user)):
    """Earn loyalty points from order"""
    # Get order details
    order = await db.orders.find_one({"id": order_id, "customer_id": current_user["id"]})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Calculate points (1 point per 10₺)
    points_earned = int(order.get("total_amount", 0) / 10)
    
    if points_earned <= 0:
        return {"message": "No points earned", "points": 0}
    
    # Check if points already earned for this order
    existing_transaction = await db.loyalty_transactions.find_one({
        "user_id": current_user["id"],
        "order_id": order_id,
        "transaction_type": "earned"
    })
    
    if existing_transaction:
        return {"message": "Points already earned for this order", "points": 0}
    
    # Record loyalty transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "points": points_earned,
        "transaction_type": "earned",
        "order_id": order_id,
        "description": f"Sipariş #{order_id} için kazanılan puan",
        "created_at": datetime.now(timezone.utc)
    }
    await db.loyalty_transactions.insert_one(transaction)
    
    # Update user loyalty
    await db.user_loyalty.update_one(
        {"user_id": current_user["id"]},
        {
            "$inc": {
                "total_points": points_earned,
                "lifetime_points": points_earned
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    return {"message": f"{points_earned} puan kazandınız!", "points": points_earned}

# Business Approval System Endpoints
@api_router.get("/admin/businesses/pending")
async def get_pending_businesses(current_user: dict = Depends(get_admin_user)):
    """Get all businesses pending approval (Admin only)"""
    businesses = await db.users.find({
        "role": "business",
        "business_status": "pending"
    }).to_list(length=None)
    
    for business in businesses:
        business["id"] = str(business["_id"])
        del business["_id"]
        if "password" in business:
            del business["password"]
        business["created_at"] = business["created_at"].isoformat()
    
    return businesses

@api_router.post("/admin/businesses/{business_id}/approve")
async def approve_business(business_id: str, current_user: dict = Depends(get_admin_user)):
    """Approve a business (Admin only)"""
    try:
        # Try UUID format first
        business = await db.users.find_one({"id": business_id, "role": "business"})
        
        if not business:
            # Try ObjectId format
            from bson import ObjectId
            object_id = ObjectId(business_id)
            business = await db.users.find_one({"_id": object_id, "role": "business"})
            business_id_filter = {"_id": object_id}
        else:
            business_id_filter = {"id": business_id}
            
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Update business status to approved
        await db.users.update_one(
            business_id_filter,
            {
                "$set": {
                    "business_status": "approved",
                    "approved_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {"message": "Business approved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/admin/businesses/{business_id}/reject")
async def reject_business(business_id: str, reason: str, current_user: dict = Depends(get_admin_user)):
    """Reject a business with reason (Admin only)"""
    try:
        # Try UUID format first
        business = await db.users.find_one({"id": business_id, "role": "business"})
        
        if not business:
            # Try ObjectId format
            from bson import ObjectId
            object_id = ObjectId(business_id)
            business = await db.users.find_one({"_id": object_id, "role": "business"})
            business_id_filter = {"_id": object_id}
        else:
            business_id_filter = {"id": business_id}
            
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Update business status to rejected
        await db.users.update_one(
            business_id_filter,
            {
                "$set": {
                    "business_status": "rejected",
                    "rejection_reason": reason,
                    "rejected_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {"message": "Business rejected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Coupon Management Endpoints
@api_router.get("/coupons/active")
async def get_active_coupons():
    """Get all active coupons"""
    coupons = await db.coupons.find({
        "is_active": True,
        "valid_from": {"$lte": datetime.now(timezone.utc)},
        "valid_until": {"$gte": datetime.now(timezone.utc)}
    }).to_list(length=None)
    
    for coupon in coupons:
        coupon["id"] = str(coupon["_id"])
        del coupon["_id"]
        coupon["valid_from"] = coupon["valid_from"].isoformat()
        coupon["valid_until"] = coupon["valid_until"].isoformat()
        coupon["created_at"] = coupon["created_at"].isoformat()
    
    return coupons

@api_router.post("/coupons/validate")
async def validate_coupon(coupon_code: str, order_amount: float, current_user: dict = Depends(get_current_user)):
    """Validate coupon code and calculate discount"""
    coupon = await db.coupons.find_one({
        "code": coupon_code.upper(),
        "is_active": True,
        "valid_from": {"$lte": datetime.now(timezone.utc)},
        "valid_until": {"$gte": datetime.now(timezone.utc)}
    })
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş kupon kodu")
    
    # Check usage limit
    if coupon.get("usage_limit") and coupon.get("used_count", 0) >= coupon["usage_limit"]:
        raise HTTPException(status_code=400, detail="Kupon kullanım limiti doldu")
    
    # Check minimum order amount
    if coupon.get("min_order_amount", 0) > order_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum sipariş tutarı {coupon['min_order_amount']}₺ olmalıdır"
        )
    
    # Calculate discount
    discount_amount = 0
    if coupon["coupon_type"] == "percentage":
        discount_amount = (order_amount * coupon["discount_value"]) / 100
        if coupon.get("max_discount_amount"):
            discount_amount = min(discount_amount, coupon["max_discount_amount"])
    elif coupon["coupon_type"] == "fixed_amount":
        discount_amount = coupon["discount_value"]
    elif coupon["coupon_type"] == "free_delivery":
        discount_amount = 5.0  # Delivery fee
    
    return {
        "valid": True,
        "coupon_id": str(coupon["_id"]),
        "discount_amount": round(discount_amount, 2),
        "coupon_type": coupon["coupon_type"],
        "title": coupon["title"]
    }

# CUSTOMER PROFILE MANAGEMENT ENDPOINTS

@api_router.get("/profile/me")
async def get_customer_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile information"""
    if current_user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only customers can access this endpoint")
    
    # Get profile from customer_profiles collection or user data
    profile = await db.customer_profiles.find_one({"user_id": current_user["id"]})
    
    if not profile:
        # Create profile from user data
        user = await db.users.find_one({"id": current_user["id"]})
        if user:
            profile_data = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "phone": user.get("phone", ""),
                "email": user.get("email"),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "birth_date": None,
                "gender": None,
                "profile_image_url": None,
                "notification_preferences": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "marketing_emails": False
                },
                "preferred_language": "tr",
                "theme_preference": "light",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.customer_profiles.insert_one(profile_data)
            profile = profile_data
    
    # Remove MongoDB ObjectId field
    if "_id" in profile:
        del profile["_id"]
    
    # Convert datetime fields
    if profile.get("created_at"):
        profile["created_at"] = profile["created_at"].isoformat() if hasattr(profile["created_at"], 'isoformat') else profile["created_at"]
    if profile.get("updated_at"):
        profile["updated_at"] = profile["updated_at"].isoformat() if hasattr(profile["updated_at"], 'isoformat') else profile["updated_at"]
    if profile.get("birth_date"):
        profile["birth_date"] = profile["birth_date"].isoformat() if hasattr(profile["birth_date"], 'isoformat') else profile["birth_date"]
    
    return profile

@api_router.put("/profile/me")
async def update_customer_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile information"""
    if current_user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only customers can access this endpoint")
    
    # Update allowed fields only
    allowed_fields = [
        "first_name", "last_name", "email", "birth_date", "gender",
        "notification_preferences", "preferred_language", "theme_preference"
    ]
    
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # Handle birth_date conversion
    if "birth_date" in update_data and update_data["birth_date"]:
        if isinstance(update_data["birth_date"], str):
            update_data["birth_date"] = datetime.fromisoformat(update_data["birth_date"].replace('Z', '+00:00'))
    
    await db.customer_profiles.update_one(
        {"user_id": current_user["id"]},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Profil başarıyla güncellendi"}

# ADDRESS MANAGEMENT ENDPOINTS

@api_router.get("/addresses")
async def get_user_addresses(current_user: dict = Depends(get_current_user)):
    """Get all addresses for current user"""
    addresses = await db.addresses.find({"user_id": current_user["id"]}).to_list(length=None)
    
    for address in addresses:
        address["id"] = str(address["_id"])
        del address["_id"]
        if address.get("created_at"):
            address["created_at"] = address["created_at"].isoformat() if hasattr(address["created_at"], 'isoformat') else address["created_at"]
        if address.get("updated_at"):
            address["updated_at"] = address["updated_at"].isoformat() if hasattr(address["updated_at"], 'isoformat') else address["updated_at"]
    
    return addresses

@api_router.post("/addresses")
async def create_address(
    address_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create new address for current user"""
    # If this is set as default, unset other default addresses
    if address_data.get("is_default"):
        await db.addresses.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"is_default": False}}
        )
    
    new_address = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "title": address_data["title"],
        "address_line": address_data["address_line"],
        "district": address_data.get("district"),
        "city": address_data["city"],
        "postal_code": address_data.get("postal_code"),
        "latitude": address_data.get("latitude"),
        "longitude": address_data.get("longitude"),
        "is_default": address_data.get("is_default", False),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.addresses.insert_one(new_address)
    return {"message": "Adres başarıyla eklendi", "address_id": new_address["id"]}

@api_router.put("/addresses/{address_id}")
async def update_address(
    address_id: str,
    address_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update existing address"""
    # Check if address belongs to current user
    existing_address = await db.addresses.find_one({
        "id": address_id,
        "user_id": current_user["id"]
    })
    
    if not existing_address:
        raise HTTPException(status_code=404, detail="Adres bulunamadı")
    
    # If setting as default, unset other defaults
    if address_data.get("is_default"):
        await db.addresses.update_many(
            {"user_id": current_user["id"], "id": {"$ne": address_id}},
            {"$set": {"is_default": False}}
        )
    
    update_data = {k: v for k, v in address_data.items() if k in [
        "title", "address_line", "district", "city", "postal_code",
        "latitude", "longitude", "is_default"
    ]}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.addresses.update_one(
        {"id": address_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Adres başarıyla güncellendi"}

@api_router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete address"""
    result = await db.addresses.delete_one({
        "id": address_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Adres bulunamadı")
    
    return {"message": "Adres başarıyla silindi"}

@api_router.post("/addresses/{address_id}/set-default")
async def set_default_address(
    address_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Set address as default"""
    # Check if address exists and belongs to user
    address = await db.addresses.find_one({
        "id": address_id,
        "user_id": current_user["id"]
    })
    
    if not address:
        raise HTTPException(status_code=404, detail="Adres bulunamadı")
    
    # Unset all other defaults
    await db.addresses.update_many(
        {"user_id": current_user["id"]},
        {"$set": {"is_default": False}}
    )
    
    # Set this address as default
    await db.addresses.update_one(
        {"id": address_id},
        {"$set": {"is_default": True, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Varsayılan adres güncellendi"}

# ORDER HISTORY AND RATINGS ENDPOINTS

@api_router.get("/orders/history")
async def get_order_history(
    page: int = 1,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get customer's order history with pagination"""
    if current_user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only customers can access this endpoint")
    
    skip = (page - 1) * limit
    
    orders = await db.orders.find({
        "customer_id": current_user["id"]
    }).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
    
    total_orders = await db.orders.count_documents({"customer_id": current_user["id"]})
    
    # Enrich orders with business and rating information
    enriched_orders = []
    for order in orders:
        # Get business info
        business = await db.users.find_one({"id": order.get("business_id")})
        
        # Get rating info
        rating = await db.order_ratings.find_one({
            "order_id": order["id"],
            "customer_id": current_user["id"]
        })
        
        # Get order items
        order_items = []
        if "items" in order:
            for item in order["items"]:
                product = await db.products.find_one({"id": item.get("product_id")})
                if product:
                    order_items.append({
                        "product_name": product.get("name", "Unknown Product"),
                        "quantity": item.get("quantity", 1),
                        "price": item.get("price", 0),
                        "total": item.get("quantity", 1) * item.get("price", 0)
                    })
        
        order_info = {
            "id": order["id"],
            "status": order["status"],
            "total_amount": order.get("total_amount", 0),
            "created_at": order["created_at"].isoformat() if hasattr(order.get("created_at"), 'isoformat') else order.get("created_at"),
            "delivery_address": order.get("delivery_address"),
            "business_name": business.get("business_name", "Unknown Business") if business else "Unknown Business",
            "business_id": order.get("business_id"),
            "courier_id": order.get("courier_id"),
            "items": order_items,
            "can_reorder": order["status"] == "delivered",
            "can_rate": order["status"] == "delivered" and not rating,
            "rating_given": bool(rating),
            "my_rating": {
                "business_rating": rating.get("business_rating") if rating else None,
                "courier_rating": rating.get("courier_rating") if rating else None,
                "business_comment": rating.get("business_comment") if rating else None,
                "courier_comment": rating.get("courier_comment") if rating else None
            } if rating else None
        }
        enriched_orders.append(order_info)
    
    return {
        "orders": enriched_orders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_orders,
            "pages": math.ceil(total_orders / limit) if total_orders > 0 else 1
        }
    }

@api_router.post("/orders/{order_id}/reorder")
async def reorder_items(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Reorder items from a previous order"""
    # Get the original order
    original_order = await db.orders.find_one({
        "id": order_id,
        "customer_id": current_user["id"],
        "status": "delivered"
    })
    
    if not original_order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı veya tekrar sipariş verilemez")
    
    # Check if business is still active
    business = await db.users.find_one({
        "id": original_order["business_id"],
        "role": "business",
        "is_active": True
    })
    
    if not business:
        raise HTTPException(status_code=400, detail="Restoran artık aktif değil")
    
    # Get available products from the original order
    available_items = []
    unavailable_items = []
    
    if "items" in original_order:
        for item in original_order["items"]:
            product = await db.products.find_one({
                "id": item["product_id"],
                "is_available": True
            })
            
            if product:
                available_items.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "quantity": item["quantity"],
                    "price": product["price"],  # Use current price
                    "original_price": item["price"]
                })
            else:
                unavailable_items.append({
                    "product_name": item.get("product_name", "Unknown Product"),
                    "quantity": item["quantity"]
                })
    
    return {
        "business_id": original_order["business_id"],
        "business_name": business.get("business_name"),
        "available_items": available_items,
        "unavailable_items": unavailable_items,
        "message": f"{len(available_items)} ürün tekrar sipariş edilebilir"
    }

@api_router.post("/orders/{order_id}/rate")
async def rate_order(
    order_id: str,
    rating_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Rate an order (business and courier)"""
    # Verify order belongs to customer and is delivered
    order = await db.orders.find_one({
        "id": order_id,
        "customer_id": current_user["id"],
        "status": "delivered"
    })
    
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı veya değerlendirilemez")
    
    # Check if already rated
    existing_rating = await db.order_ratings.find_one({
        "order_id": order_id,
        "customer_id": current_user["id"]
    })
    
    if existing_rating:
        raise HTTPException(status_code=400, detail="Bu sipariş zaten değerlendirilmiş")
    
    # Create rating record
    new_rating = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "customer_id": current_user["id"],
        "business_id": order["business_id"],
        "courier_id": order.get("courier_id"),
        "business_rating": rating_data.get("business_rating"),
        "courier_rating": rating_data.get("courier_rating"),
        "business_comment": rating_data.get("business_comment"),
        "courier_comment": rating_data.get("courier_comment"),
        "food_quality_rating": rating_data.get("food_quality_rating"),
        "delivery_speed_rating": rating_data.get("delivery_speed_rating"),
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.order_ratings.insert_one(new_rating)
    
    # Update business and courier average ratings
    if rating_data.get("business_rating"):
        await update_business_rating(order["business_id"])
    
    if rating_data.get("courier_rating") and order.get("courier_id"):
        await update_courier_rating(order["courier_id"])
    
    return {"message": "Değerlendirmeniz kaydedildi"}

async def update_business_rating(business_id: str):
    """Update business average rating"""
    ratings = await db.order_ratings.find({
        "business_id": business_id,
        "business_rating": {"$ne": None}
    }).to_list(length=None)
    
    if ratings:
        avg_rating = sum(r["business_rating"] for r in ratings) / len(ratings)
        await db.users.update_one(
            {"id": business_id},
            {"$set": {
                "average_rating": round(avg_rating, 1),
                "total_ratings": len(ratings)
            }}
        )

async def update_courier_rating(courier_id: str):
    """Update courier average rating"""
    ratings = await db.order_ratings.find({
        "courier_id": courier_id,
        "courier_rating": {"$ne": None}
    }).to_list(length=None)
    
    if ratings:
        avg_rating = sum(r["courier_rating"] for r in ratings) / len(ratings)
        await db.users.update_one(
            {"id": courier_id},
            {"$set": {
                "average_rating": round(avg_rating, 1),
                "total_ratings": len(ratings)
            }}
        )

# GOOGLE OAUTH AUTHENTICATION (Emergent Integration)

@api_router.post("/auth/google/session")
async def google_auth_session(session_data: dict):
    """Process Google OAuth session from Emergent Auth"""
    try:
        session_id = session_data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Call Emergent Auth API to get session data
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            auth_data = response.json()
            
            # Extract user information
            google_user_id = auth_data.get("id")
            email = auth_data.get("email")
            name = auth_data.get("name", "")
            picture = auth_data.get("picture")
            session_token = auth_data.get("session_token")
            
            if not google_user_id or not email:
                raise HTTPException(status_code=400, detail="Incomplete user data")
            
            # Check if user already exists
            existing_user = await db.users.find_one({"email": email})
            
            if existing_user:
                # Update existing user with Google info
                user_id = existing_user["id"]
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {
                        "google_id": google_user_id,
                        "profile_image_url": picture,
                        "last_login": datetime.now(timezone.utc),
                        "oauth_provider": "google"
                    }}
                )
                user = existing_user
                user["google_id"] = google_user_id
                user["profile_image_url"] = picture
            else:
                # Create new user from Google data
                name_parts = name.split(" ", 1)
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                user = {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "google_id": google_user_id,
                    "role": "customer",
                    "first_name": first_name,
                    "last_name": last_name,
                    "profile_image_url": picture,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                    "last_login": datetime.now(timezone.utc),
                    "oauth_provider": "google",
                    "profile_completed": True
                }
                
                await db.users.insert_one(user)
                user_id = user["id"]
            
            # Store session token in our database
            session_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
                "created_at": datetime.now(timezone.utc),
                "provider": "google"
            }
            
            await db.oauth_sessions.insert_one(session_record)
            
            # Generate our own access token
            token_data = {
                "sub": user_id,
                "email": email,
                "role": user["role"],
                "exp": datetime.now(timezone.utc) + timedelta(hours=24)
            }
            
            access_token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": user_id,
                    "email": email,
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "profile_image_url": picture,
                    "role": user["role"],
                    "oauth_provider": "google",
                    "profile_completed": user.get("profile_completed", True)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.post("/auth/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout user and invalidate session"""
    try:
        # Remove OAuth sessions if any
        await db.oauth_sessions.delete_many({"user_id": current_user["id"]})
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return {"message": "Logout completed"}

# PHONE AUTHENTICATION ENDPOINTS

@api_router.post("/auth/phone/request-otp")
async def request_phone_otp(phone_data: dict):
    """Request OTP for phone authentication"""
    
    try:
        formatted_phone = validate_turkish_phone(phone_data["phone"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate OTP (6 digits)
    import random
    otp_code = str(random.randint(100000, 999999))
    
    # Store OTP in database with expiration
    otp_record = {
        "id": str(uuid.uuid4()),
        "phone": formatted_phone,
        "otp_code": otp_code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "created_at": datetime.now(timezone.utc),
        "used": False
    }
    
    await db.phone_otps.insert_one(otp_record)
    
    # TODO: Send SMS (for now return mock OTP in development)
    return {
        "success": True,
        "message": "OTP kodu gönderildi",
        "mock_otp": otp_code,  # Remove in production
        "formatted_phone": formatted_phone,
        "expires_in": 300  # 5 minutes
    }

@api_router.post("/auth/phone/verify-otp")
async def verify_phone_otp(verify_data: dict):
    """Verify OTP and create/login user"""
    phone = verify_data["phone"]
    otp_code = verify_data["otp_code"]
    
    # Find valid OTP
    otp_record = await db.phone_otps.find_one({
        "phone": phone,
        "otp_code": otp_code,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş OTP")
    
    # Mark OTP as used
    await db.phone_otps.update_one(
        {"id": otp_record["id"]},
        {"$set": {"used": True}}
    )
    
    # Check if user already exists
    user = await db.users.find_one({"phone": phone})
    
    if not user:
        # Create new customer user
        user_data = {
            "id": str(uuid.uuid4()),
            "phone": phone,
            "email": None,
            "role": "customer",
            "first_name": "",
            "last_name": "",
            "is_active": True,
            "profile_completed": False,
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_data)
        user = user_data
    
    # Generate JWT token
    token_data = {
        "sub": user["id"],
        "phone": user["phone"],
        "role": user.get("role", "customer"),  # Default to customer if role not set
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    
    access_token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_data": {
            "id": user["id"],
            "phone": user["phone"],
            "email": user.get("email"),
            "role": user.get("role", "customer"),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "profile_completed": user.get("profile_completed", False)
        }
    }

# ADVERTISEMENT MANAGEMENT ENDPOINTS

@api_router.get("/ads/active")
async def get_active_ads(city: str = None, category: str = None):
    """Get active advertisements with targeting"""
    try:
        # Build query for active ads
        query = {
            "active": True,
            "schedule.startAt": {"$lte": datetime.now(timezone.utc)},
            "schedule.endAt": {"$gte": datetime.now(timezone.utc)}
        }
        
        # Add targeting filters
        if city:
            query["$or"] = [
                {"targeting.city": city},
                {"targeting.city": {"$exists": False}}  # Global ads
            ]
        
        if category:
            if "$or" in query:
                # Combine with city targeting
                query["$and"] = [
                    {"$or": query.pop("$or")},
                    {"$or": [
                        {"targeting.category": category},
                        {"targeting.category": {"$exists": False}}
                    ]}
                ]
            else:
                query["$or"] = [
                    {"targeting.category": category},
                    {"targeting.category": {"$exists": False}}
                ]
        
        # Get ads sorted by order
        ads = await db.advertisements.find(query).sort("order", 1).to_list(length=None)
        
        # Convert ObjectId and datetime fields
        for ad in ads:
            ad["id"] = str(ad["_id"])
            del ad["_id"]
            if ad.get("schedule"):
                if ad["schedule"].get("startAt"):
                    ad["schedule"]["startAt"] = ad["schedule"]["startAt"].isoformat() if hasattr(ad["schedule"]["startAt"], 'isoformat') else ad["schedule"]["startAt"]
                if ad["schedule"].get("endAt"):
                    ad["schedule"]["endAt"] = ad["schedule"]["endAt"].isoformat() if hasattr(ad["schedule"]["endAt"], 'isoformat') else ad["schedule"]["endAt"]
        
        return ads
        
    except Exception as e:
        logging.error(f"Error fetching ads: {e}")
        return []

@api_router.post("/ads/{ad_id}/impression")
async def track_ad_impression(ad_id: str):
    """Track advertisement impression"""
    try:
        # Increment impression count
        await db.advertisements.update_one(
            {"id": ad_id},
            {"$inc": {"impressions": 1}}
        )
        
        # Log impression with timestamp
        impression_log = {
            "id": str(uuid.uuid4()),
            "ad_id": ad_id,
            "type": "impression",
            "timestamp": datetime.now(timezone.utc),
            "user_agent": "web",  # Could be enhanced with request headers
            "ip_address": "unknown"  # Could be enhanced with request IP
        }
        
        await db.ad_analytics.insert_one(impression_log)
        
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Error tracking impression: {e}")
        return {"success": False}

@api_router.post("/ads/{ad_id}/click")
async def track_ad_click(ad_id: str):
    """Track advertisement click"""
    try:
        # Increment click count
        await db.advertisements.update_one(
            {"id": ad_id},
            {"$inc": {"clicks": 1}}
        )
        
        # Log click with timestamp
        click_log = {
            "id": str(uuid.uuid4()),
            "ad_id": ad_id,
            "type": "click",
            "timestamp": datetime.now(timezone.utc),
            "user_agent": "web",
            "ip_address": "unknown"
        }
        
        await db.ad_analytics.insert_one(click_log)
        
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Error tracking click: {e}")
        return {"success": False}

# ADMIN AD MANAGEMENT ENDPOINTS

@api_router.get("/admin/ads")
async def get_all_ads(current_user: dict = Depends(get_current_user)):
    """Get all advertisements for admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        ads = await db.advertisements.find().sort("created_at", -1).to_list(length=None)
        
        for ad in ads:
            ad["id"] = str(ad["_id"])
            del ad["_id"]
            # Convert datetime fields
            for field in ["created_at", "updated_at"]:
                if ad.get(field):
                    ad[field] = ad[field].isoformat() if hasattr(ad[field], 'isoformat') else ad[field]
            
            if ad.get("schedule"):
                if ad["schedule"].get("startAt"):
                    ad["schedule"]["startAt"] = ad["schedule"]["startAt"].isoformat() if hasattr(ad["schedule"]["startAt"], 'isoformat') else ad["schedule"]["startAt"]
                if ad["schedule"].get("endAt"):
                    ad["schedule"]["endAt"] = ad["schedule"]["endAt"].isoformat() if hasattr(ad["schedule"]["endAt"], 'isoformat') else ad["schedule"]["endAt"]
        
        return ads
        
    except Exception as e:
        logging.error(f"Error fetching all ads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ads")

@api_router.post("/admin/ads")
async def create_ad(ad_data: dict, current_user: dict = Depends(get_current_user)):
    """Create new advertisement"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        new_ad = {
            "id": str(uuid.uuid4()),
            "title": ad_data["title"],
            "description": ad_data.get("description", ""),
            "imgUrl": ad_data.get("imgUrl"),
            "targetUrl": ad_data.get("targetUrl"),
            "ctaText": ad_data.get("ctaText", "Daha Fazla"),
            "type": ad_data.get("type", "general"),
            "targeting": {
                "city": ad_data.get("targeting", {}).get("city"),
                "category": ad_data.get("targeting", {}).get("category")
            },
            "schedule": {
                "startAt": datetime.fromisoformat(ad_data["schedule"]["startAt"].replace('Z', '+00:00')) if ad_data.get("schedule", {}).get("startAt") else datetime.now(timezone.utc),
                "endAt": datetime.fromisoformat(ad_data["schedule"]["endAt"].replace('Z', '+00:00')) if ad_data.get("schedule", {}).get("endAt") else datetime.now(timezone.utc) + timedelta(days=30)
            },
            "active": ad_data.get("active", True),
            "order": ad_data.get("order", 0),
            "clicks": 0,
            "impressions": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.advertisements.insert_one(new_ad)
        
        return {"message": "Reklam başarıyla oluşturuldu", "ad_id": new_ad["id"]}
        
    except Exception as e:
        logging.error(f"Error creating ad: {e}")
        raise HTTPException(status_code=500, detail="Reklam oluşturulamadı")

@api_router.put("/admin/ads/{ad_id}")
async def update_ad(ad_id: str, ad_data: dict, current_user: dict = Depends(get_current_user)):
    """Update advertisement"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        update_data = {}
        
        # Update allowed fields
        allowed_fields = ["title", "description", "imgUrl", "targetUrl", "ctaText", "type", "active", "order"]
        for field in allowed_fields:
            if field in ad_data:
                update_data[field] = ad_data[field]
        
        # Handle targeting
        if "targeting" in ad_data:
            update_data["targeting"] = ad_data["targeting"]
        
        # Handle schedule
        if "schedule" in ad_data:
            schedule = {}
            if ad_data["schedule"].get("startAt"):
                schedule["startAt"] = datetime.fromisoformat(ad_data["schedule"]["startAt"].replace('Z', '+00:00'))
            if ad_data["schedule"].get("endAt"):
                schedule["endAt"] = datetime.fromisoformat(ad_data["schedule"]["endAt"].replace('Z', '+00:00'))
            update_data["schedule"] = schedule
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.advertisements.update_one(
            {"id": ad_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Reklam bulunamadı")
        
        return {"message": "Reklam başarıyla güncellendi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating ad: {e}")
        raise HTTPException(status_code=500, detail="Reklam güncellenemedi")

@api_router.delete("/admin/ads/{ad_id}")
async def delete_ad(ad_id: str, current_user: dict = Depends(get_current_user)):
    """Delete advertisement"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.advertisements.delete_one({"id": ad_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Reklam bulunamadı")
        
        # Also delete analytics data
        await db.ad_analytics.delete_many({"ad_id": ad_id})
        
        return {"message": "Reklam başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting ad: {e}")
        raise HTTPException(status_code=500, detail="Reklam silinemedi")

@api_router.get("/admin/ads/{ad_id}/analytics")
async def get_ad_analytics(ad_id: str, current_user: dict = Depends(get_current_user)):
    """Get advertisement analytics"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get ad info
        ad = await db.advertisements.find_one({"id": ad_id})
        if not ad:
            raise HTTPException(status_code=404, detail="Reklam bulunamadı")
        
        # Get analytics data
        analytics = await db.ad_analytics.find({"ad_id": ad_id}).to_list(length=None)
        
        # Calculate metrics
        total_impressions = len([a for a in analytics if a["type"] == "impression"])
        total_clicks = len([a for a in analytics if a["type"] == "click"])
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        # Group by date for charts
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {"impressions": 0, "clicks": 0})
        
        for event in analytics:
            date_str = event["timestamp"].strftime("%Y-%m-%d") if hasattr(event["timestamp"], 'strftime') else str(event["timestamp"])[:10]
            daily_stats[date_str][event["type"] + "s"] += 1
        
        return {
            "ad_info": {
                "id": ad_id,
                "title": ad["title"],
                "active": ad["active"]
            },
            "metrics": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "ctr": round(ctr, 2)
            },
            "daily_stats": dict(daily_stats)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Analitik veriler alınamadı")

# COURIER PANEL ENHANCEMENTS

@api_router.get("/courier/orders/available")
async def get_available_orders(current_user: dict = Depends(get_current_user)):
    """Get available orders for courier based on location"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    # Check if courier is online and KYC approved
    courier = await db.users.find_one({"id": current_user["id"]})
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    if not courier.get("kyc_approved"):
        raise HTTPException(status_code=403, detail="KYC approval required")
    
    if not courier.get("is_online", False):
        return {"orders": [], "message": "Çevrimiçi olmanız gerekiyor"}
    
    try:
        # Get pending orders
        query = {
            "status": "pending",
            "courier_id": {"$exists": False}  # Not assigned to any courier yet
        }
        
        orders = await db.orders.find(query).sort("created_at", 1).to_list(length=20)  # Max 20 orders
        
        # Enrich orders with business and customer info
        enriched_orders = []
        for order in orders:
            # Get business info
            business = await db.users.find_one({"id": order.get("business_id")})
            
            # Calculate estimated delivery time and distance
            order_info = {
                "id": order["id"],
                "created_at": order["created_at"].isoformat() if hasattr(order["created_at"], 'isoformat') else order["created_at"],
                "business_name": business.get("business_name", "Unknown Business") if business else "Unknown Business",
                "business_address": business.get("address", "Address not available") if business else "Address not available",
                "delivery_address": order.get("delivery_address", "Delivery address not specified"),
                "total_amount": order.get("total_amount", 0),
                "commission": round(order.get("total_amount", 0) * 0.05, 2),  # 5% commission
                "estimated_distance": order.get("estimated_distance", "Unknown"),
                "estimated_prep_time": order.get("estimated_prep_time", 15),  # Default 15 min
                "priority": order.get("priority", "normal"),
                "payment_method": order.get("payment_method", "online")
            }
            enriched_orders.append(order_info)
        
        return {
            "orders": enriched_orders,
            "total_available": len(enriched_orders),
            "message": f"{len(enriched_orders)} sipariş mevcut"
        }
        
    except Exception as e:
        logging.error(f"Error fetching available orders: {e}")
        raise HTTPException(status_code=500, detail="Siparişler yüklenemedi")

@api_router.post("/courier/orders/{order_id}/accept")
async def accept_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """Accept an order as courier"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        # Check if order is still available
        order = await db.orders.find_one({
            "id": order_id,
            "status": "pending",
            "courier_id": {"$exists": False}
        })
        
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı veya başka kurye tarafından alındı")
        
        # Assign order to courier
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {
                "courier_id": current_user["id"],
                "status": "accepted",
                "accepted_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # Create order tracking entry
        tracking_entry = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "courier_id": current_user["id"],
            "status": "accepted",
            "location": None,  # Can be updated with GPS coordinates
            "timestamp": datetime.now(timezone.utc),
            "notes": "Sipariş kurye tarafından kabul edildi"
        }
        
        await db.order_tracking.insert_one(tracking_entry)
        
        return {"message": "Sipariş başarıyla kabul edildi", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error accepting order: {e}")
        raise HTTPException(status_code=500, detail="Sipariş kabul edilemedi")

@api_router.post("/courier/orders/{order_id}/update-status")
async def update_order_status(order_id: str, status_data: dict, current_user: dict = Depends(get_current_user)):
    """Update order status (PICKED_UP, DELIVERED)"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    allowed_statuses = ["picked_up", "delivered"]
    new_status = status_data.get("status")
    
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    try:
        # Check if order belongs to this courier
        order = await db.orders.find_one({
            "id": order_id,
            "courier_id": current_user["id"]
        })
        
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
        
        # Update order status
        update_data = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if new_status == "picked_up":
            update_data["picked_up_at"] = datetime.now(timezone.utc)
        elif new_status == "delivered":
            update_data["delivered_at"] = datetime.now(timezone.utc)
        
        await db.orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        # Create tracking entry
        tracking_entry = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "courier_id": current_user["id"],
            "status": new_status,
            "location": status_data.get("location"),  # GPS coordinates
            "timestamp": datetime.now(timezone.utc),
            "notes": status_data.get("notes", "")
        }
        
        await db.order_tracking.insert_one(tracking_entry)
        
        status_messages = {
            "picked_up": "Sipariş alındı olarak işaretlendi",
            "delivered": "Sipariş teslim edildi olarak işaretlendi"
        }
        
        return {"message": status_messages[new_status], "order_id": order_id, "status": new_status}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail="Durum güncellenemedi")

@api_router.get("/courier/orders/history")
async def get_courier_order_history(
    page: int = 1,
    limit: int = 20,
    status_filter: str = None,
    date_filter: str = None,  # today, week, month
    current_user: dict = Depends(get_current_user)
):
    """Get courier's order history with filters"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        skip = (page - 1) * limit
        
        # Build query
        query = {"courier_id": current_user["id"]}
        
        if status_filter:
            query["status"] = status_filter
        
        if date_filter:
            now = datetime.now(timezone.utc)
            if date_filter == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == "week":
                start_date = now - timedelta(days=7)
            elif date_filter == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = None
            
            if start_date:
                query["created_at"] = {"$gte": start_date}
        
        # Get orders
        orders = await db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
        total_orders = await db.orders.count_documents(query)
        
        # Enrich orders
        enriched_orders = []
        total_earnings = 0
        
        for order in orders:
            # Get business info
            business = await db.users.find_one({"id": order.get("business_id")})
            
            commission = round(order.get("total_amount", 0) * 0.05, 2)
            total_earnings += commission
            
            order_info = {
                "id": order["id"],
                "created_at": order["created_at"].isoformat() if hasattr(order["created_at"], 'isoformat') else order["created_at"],
                "business_name": business.get("business_name", "Unknown") if business else "Unknown",
                "delivery_address": order.get("delivery_address", ""),
                "total_amount": order.get("total_amount", 0),
                "commission": commission,
                "status": order["status"],
                "delivered_at": order.get("delivered_at").isoformat() if order.get("delivered_at") and hasattr(order.get("delivered_at"), 'isoformat') else order.get("delivered_at")
            }
            enriched_orders.append(order_info)
        
        return {
            "orders": enriched_orders,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_orders,
                "pages": math.ceil(total_orders / limit) if total_orders > 0 else 1
            },
            "summary": {
                "total_earnings": round(total_earnings, 2),
                "total_orders": len(enriched_orders)
            }
        }
        
    except Exception as e:
        logging.error(f"Error fetching courier history: {e}")
        raise HTTPException(status_code=500, detail="Geçmiş siparişler yüklenemedi")

@api_router.post("/courier/status/toggle")
async def toggle_courier_status(current_user: dict = Depends(get_current_user)):
    """Toggle courier online/offline status"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        courier = await db.users.find_one({"id": current_user["id"]})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        new_status = not courier.get("is_online", False)
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "is_online": new_status,
                "last_status_change": datetime.now(timezone.utc)
            }}
        )
        
        status_text = "çevrimiçi" if new_status else "çevrimdışı"
        return {
            "is_online": new_status,
            "message": f"Durum {status_text} olarak güncellendi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error toggling courier status: {e}")
        raise HTTPException(status_code=500, detail="Durum değiştirilemedi")

# COURIER MESSAGING AND NOTIFICATIONS

@api_router.get("/courier/notifications")
async def get_courier_notifications(current_user: dict = Depends(get_current_user)):
    """Get courier notifications"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        # Get unread notifications
        notifications = await db.courier_notifications.find({
            "courier_id": current_user["id"],
            "read": False
        }).sort("created_at", -1).limit(50).to_list(length=None)
        
        for notification in notifications:
            notification["id"] = str(notification["_id"])
            del notification["_id"]
            notification["created_at"] = notification["created_at"].isoformat() if hasattr(notification["created_at"], 'isoformat') else notification["created_at"]
        
        return {
            "notifications": notifications,
            "unread_count": len(notifications)
        }
        
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Bildirimler yüklenemedi")

@api_router.post("/courier/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        await db.courier_notifications.update_one(
            {"_id": notification_id, "courier_id": current_user["id"]},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
        )
        
        return {"message": "Bildirim okundu olarak işaretlendi"}
        
    except Exception as e:
        logging.error(f"Error marking notification read: {e}")
        raise HTTPException(status_code=500, detail="Bildirim güncellenemedi")

@api_router.get("/courier/messages")
async def get_courier_messages(current_user: dict = Depends(get_current_user)):
    """Get admin messages for courier"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        messages = await db.courier_messages.find({
            "$or": [
                {"courier_id": current_user["id"]},  # Direct messages
                {"courier_id": None}  # Broadcast messages
            ]
        }).sort("created_at", -1).limit(50).to_list(length=None)
        
        for message in messages:
            message["id"] = str(message["_id"])
            del message["_id"]
            message["created_at"] = message["created_at"].isoformat() if hasattr(message["created_at"], 'isoformat') else message["created_at"]
        
        return {"messages": messages}
        
    except Exception as e:
        logging.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Mesajlar yüklenemedi")

# ADDITIONAL COURIER ENDPOINTS

@api_router.post("/courier/location/update")
async def update_courier_location(location_data: dict, current_user: dict = Depends(get_current_user)):
    """Update courier's current location"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "current_location": {
                    "lat": location_data.get("lat"),
                    "lng": location_data.get("lng")
                },
                "location_updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return {"status": "Location updated successfully"}
        
    except Exception as e:
        logging.error(f"Error updating location: {e}")
        raise HTTPException(status_code=500, detail="Konum güncellenemedi")

@api_router.get("/courier/earnings")
async def get_courier_earnings(current_user: dict = Depends(get_current_user)):
    """Get courier earnings breakdown"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        # Get completed orders for earnings calculation
        completed_orders = await db.orders.find({
            "courier_id": current_user["id"],
            "status": "delivered"
        }).to_list(length=None)
        
        # Calculate earnings
        now = datetime.now(timezone.utc)
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        daily_earnings = 0
        weekly_earnings = 0
        monthly_earnings = 0
        total_earnings = 0
        
        for order in completed_orders:
            if order.get("delivered_at"):
                commission = order.get("commission_amount", order.get("total_amount", 0) * 0.05)
                total_earnings += commission
                
                # Convert datetime for comparison
                delivered_date = order["delivered_at"]
                if isinstance(delivered_date, str):
                    delivered_date = datetime.fromisoformat(delivered_date).date()
                elif hasattr(delivered_date, 'date'):
                    delivered_date = delivered_date.date()
                
                if delivered_date == today:
                    daily_earnings += commission
                if delivered_date >= week_start:
                    weekly_earnings += commission
                if delivered_date >= month_start:
                    monthly_earnings += commission
        
        return {
            "daily": daily_earnings,
            "weekly": weekly_earnings,
            "monthly": monthly_earnings,
            "total": total_earnings
        }
        
    except Exception as e:
        logging.error(f"Error calculating earnings: {e}")
        raise HTTPException(status_code=500, detail="Kazanç bilgisi alınamadı")

@api_router.get("/courier/stats")
async def get_courier_stats(current_user: dict = Depends(get_current_user)):
    """Get courier statistics"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        # Get all courier orders
        all_orders = await db.orders.find({
            "courier_id": current_user["id"]
        }).to_list(length=None)
        
        completed_orders = [o for o in all_orders if o.get("status") == "delivered"]
        cancelled_orders = [o for o in all_orders if o.get("status") == "cancelled"]
        
        # Calculate average delivery time
        total_delivery_time = 0
        delivery_count = 0
        
        for order in completed_orders:
            if order.get("accepted_at") and order.get("delivered_at"):
                accepted = order["accepted_at"]
                delivered = order["delivered_at"]
                
                if isinstance(accepted, str):
                    accepted = datetime.fromisoformat(accepted)
                if isinstance(delivered, str):
                    delivered = datetime.fromisoformat(delivered)
                    
                delivery_time = (delivered - accepted).total_seconds() / 60  # minutes
                total_delivery_time += delivery_time
                delivery_count += 1
        
        avg_delivery_time = total_delivery_time / delivery_count if delivery_count > 0 else 0
        
        # Get courier rating (mock for now)
        rating = 4.5  # Mock rating - could be calculated from actual ratings
        
        return {
            "totalOrders": len(all_orders),
            "completedOrders": len(completed_orders),
            "cancelledOrders": len(cancelled_orders),
            "avgDeliveryTime": round(avg_delivery_time),
            "rating": rating,
            "totalDistance": 150  # Mock distance - would need GPS tracking
        }
        
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="İstatistik bilgisi alınamadı")

@api_router.get("/courier/profile")
async def get_courier_profile(current_user: dict = Depends(get_current_user)):
    """Get courier profile"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        courier = await db.users.find_one({"id": current_user["id"]})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        profile = {
            "firstName": courier.get("first_name", ""),
            "lastName": courier.get("last_name", ""),
            "phone": courier.get("phone", ""),
            "email": courier.get("email", ""),
            "iban": courier.get("iban", ""),
            "workingHours": courier.get("working_hours", {
                "start": "09:00",
                "end": "22:00",
                "workDays": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            }),
            "notifications": courier.get("notifications", {
                "sound": True,
                "push": True,
                "email": False
            })
        }
        
        return profile
        
    except Exception as e:
        logging.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail="Profil bilgisi alınamadı")

@api_router.put("/courier/profile")
async def update_courier_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    """Update courier profile"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    try:
        update_data = {}
        
        if "firstName" in profile_data:
            update_data["first_name"] = profile_data["firstName"]
        if "lastName" in profile_data:
            update_data["last_name"] = profile_data["lastName"]
        if "phone" in profile_data:
            update_data["phone"] = profile_data["phone"]
        if "iban" in profile_data:
            update_data["iban"] = profile_data["iban"]
        if "workingHours" in profile_data:
            update_data["working_hours"] = profile_data["workingHours"]
        if "notifications" in profile_data:
            update_data["notifications"] = profile_data["notifications"]
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
        
        return {"message": "Profil güncellendi"}
        
    except Exception as e:
        logging.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Profil güncellenemedi")

@api_router.get("/courier/report/{report_type}")
async def generate_courier_report(report_type: str, current_user: dict = Depends(get_current_user)):
    """Generate courier report (PDF)"""
    if current_user.get("role") != "courier":
        raise HTTPException(status_code=403, detail="Courier access required")
    
    # Mock PDF generation - would need actual PDF library
    return {"message": "Report generation not implemented yet"}

# ADMIN COURIER MESSAGING

@api_router.post("/admin/courier/message")
async def send_courier_message(message_data: dict, current_user: dict = Depends(get_current_user)):
    """Send message to couriers (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        courier_ids = message_data.get("courier_ids", [])  # Empty array = broadcast to all
        message_text = message_data.get("message", "")
        title = message_data.get("title", "Yönetici Mesajı")
        
        if not message_text:
            raise HTTPException(status_code=400, detail="Message text required")
        
        if not courier_ids:
            # Broadcast to all active couriers
            couriers = await db.users.find({"role": "courier", "is_active": True}).to_list(length=None)
            courier_ids = [courier["id"] for courier in couriers]
        
        # Send message to each courier
        messages_sent = 0
        for courier_id in courier_ids:
            # Get courier name for personalized message
            courier = await db.users.find_one({"id": courier_id})
            courier_name = f"{courier.get('first_name', '')} {courier.get('last_name', '')}".strip() if courier else "Kurye"
            
            personalized_message = f"{courier_name}, {message_text}"
            
            # Create message record
            message_record = {
                "id": str(uuid.uuid4()),
                "courier_id": courier_id,
                "title": title,
                "message": personalized_message,
                "sent_by": current_user["id"],
                "created_at": datetime.now(timezone.utc),
                "read": False
            }
            
            await db.courier_messages.insert_one(message_record)
            
            # Create notification
            notification = {
                "id": str(uuid.uuid4()),
                "courier_id": courier_id,
                "type": "admin_message",
                "title": title,
                "message": f"Yeni admin mesajı: {message_text[:50]}...",
                "created_at": datetime.now(timezone.utc),
                "read": False
            }
            
            await db.courier_notifications.insert_one(notification)
            messages_sent += 1
        
        return {
            "message": f"{messages_sent} kuryeye mesaj gönderildi",
            "recipients": messages_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error sending courier message: {e}")
        raise HTTPException(status_code=500, detail="Mesaj gönderilemedi")

# BUSINESS PANEL ENHANCEMENTS

@api_router.get("/business/restaurant-view")
async def get_restaurant_public_view(current_user: dict = Depends(get_current_user)):
    """Get public view data for restaurant (for 'View My Restaurant' feature)"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # Get business info
        business = await db.users.find_one({"id": current_user["id"]})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Get products
        products = await db.products.find({
            "business_id": current_user["id"],
            "is_available": True
        }).to_list(length=None)
        
        # Convert ObjectIds and datetime fields
        for product in products:
            product["id"] = str(product["_id"])
            del product["_id"]
            if product.get("created_at"):
                product["created_at"] = product["created_at"].isoformat() if hasattr(product["created_at"], 'isoformat') else product["created_at"]
        
        # Get ratings and reviews
        ratings = await db.order_ratings.find({
            "business_id": current_user["id"],
            "business_rating": {"$ne": None}
        }).to_list(length=None)
        
        avg_rating = sum(r["business_rating"] for r in ratings) / len(ratings) if ratings else 0
        
        # Check if featured
        featured_status = await db.featured_businesses.find_one({
            "business_id": current_user["id"],
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        restaurant_data = {
            "business_info": {
                "id": business["id"],
                "business_name": business.get("business_name", ""),
                "description": business.get("description", ""),
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "phone": business.get("phone", ""),
                "email": business.get("email", ""),
                "business_category": business.get("business_category", ""),
                "average_rating": round(avg_rating, 1),
                "total_ratings": len(ratings),
                "is_featured": bool(featured_status)
            },
            "products": products,
            "categories": list(set(p.get("category", "other") for p in products)),
            "recent_reviews": [
                {
                    "rating": r["business_rating"],
                    "comment": r.get("business_comment", ""),
                    "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], 'isoformat') else r["created_at"]
                }
                for r in sorted(ratings, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:10]
            ]
        }
        
        return restaurant_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching restaurant view: {e}")
        raise HTTPException(status_code=500, detail="Restaurant data could not be loaded")

@api_router.get("/business/featured-status")
async def get_featured_status(current_user: dict = Depends(get_current_user)):
    """Get current featured status for business"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        featured_record = await db.featured_businesses.find_one({
            "business_id": current_user["id"],
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if featured_record:
            return {
                "is_featured": True,
                "plan": featured_record["plan"],
                "expires_at": featured_record["expires_at"].isoformat() if hasattr(featured_record["expires_at"], 'isoformat') else featured_record["expires_at"],
                "remaining_days": (featured_record["expires_at"] - datetime.now(timezone.utc)).days if hasattr(featured_record["expires_at"], 'days') else 0
            }
        else:
            return {
                "is_featured": False,
                "available_plans": [
                    {"id": "daily", "name": "1 Gün", "price": 50, "duration_days": 1},
                    {"id": "weekly", "name": "1 Hafta", "price": 300, "duration_days": 7},
                    {"id": "monthly", "name": "1 Ay", "price": 1000, "duration_days": 30}
                ]
            }
    except Exception as e:
        logging.error(f"Error fetching featured status: {e}")
        raise HTTPException(status_code=500, detail="Featured status could not be loaded")

@api_router.post("/business/request-featured")
async def request_featured_promotion(plan_data: dict, current_user: dict = Depends(get_current_user)):
    """Request featured promotion for business"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    plan_id = plan_data.get("plan")
    if plan_id not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_configs = {
        "daily": {"price": 50, "duration_days": 1, "name": "1 Gün"},
        "weekly": {"price": 300, "duration_days": 7, "name": "1 Hafta"},
        "monthly": {"price": 1000, "duration_days": 30, "name": "1 Ay"}
    }
    
    plan_config = plan_configs[plan_id]
    
    try:
        # Check if already featured
        existing_featured = await db.featured_businesses.find_one({
            "business_id": current_user["id"],
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if existing_featured:
            raise HTTPException(status_code=400, detail="Business is already featured")
        
        # Create featured request (pending admin approval)
        featured_request = {
            "id": str(uuid.uuid4()),
            "business_id": current_user["id"],
            "plan": plan_id,
            "plan_name": plan_config["name"],
            "price": plan_config["price"],
            "duration_days": plan_config["duration_days"],
            "status": "pending",  # pending, approved, rejected
            "requested_at": datetime.now(timezone.utc),
            "active": False
        }
        
        await db.featured_requests.insert_one(featured_request)
        
        # Create notification for admin
        admin_notification = {
            "id": str(uuid.uuid4()),
            "type": "featured_request",
            "business_id": current_user["id"],
            "message": f"Yeni öne çıkarma talebi: {plan_config['name']} planı",
            "created_at": datetime.now(timezone.utc),
            "read": False
        }
        
        await db.admin_notifications.insert_one(admin_notification)
        
        return {
            "message": "Öne çıkarma talebiniz gönderildi",
            "request_id": featured_request["id"],
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error requesting featured promotion: {e}")
        raise HTTPException(status_code=500, detail="Featured request could not be processed")

@api_router.get("/business/products/categories") 
async def get_business_product_categories(current_user: dict = Depends(get_current_user)):
    """Get product categories for business with food/drinks classification"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        products = await db.products.find({"business_id": current_user["id"]}).to_list(length=None)
        
        # Classify products into food and drinks
        categories = {
            "food_categories": set(),
            "drink_categories": set(),
            "all_categories": set()
        }
        
        food_keywords = ['ana yemek', 'başlangıç', 'pizza', 'burger', 'döner', 'kebap', 'pasta', 'çorba', 'salata', 'tatlı', 'yemek']
        drink_keywords = ['içecek', 'kahve', 'çay', 'su', 'kola', 'fanta', 'sprite', 'ayran', 'meyve suyu', 'smoothie']
        
        for product in products:
            category = product.get("category", "other").lower()
            categories["all_categories"].add(category)
            
            # Classify as food or drink
            is_drink = any(keyword in category or keyword in product.get("name", "").lower() for keyword in drink_keywords)
            
            if is_drink:
                categories["drink_categories"].add(category)
            else:
                categories["food_categories"].add(category)
        
        return {
            "food_categories": sorted(list(categories["food_categories"])),
            "drink_categories": sorted(list(categories["drink_categories"])),
            "all_categories": sorted(list(categories["all_categories"])),
            "total_products": len(products)
        }
        
    except Exception as e:
        logging.error(f"Error fetching product categories: {e}")
        raise HTTPException(status_code=500, detail="Categories could not be loaded")

# ADMIN FEATURED BUSINESS MANAGEMENT

@api_router.get("/admin/featured-requests")
async def get_featured_requests(current_user: dict = Depends(get_current_user)):
    """Get all featured promotion requests (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        requests = await db.featured_requests.find().sort("requested_at", -1).to_list(length=None)
        
        # Enrich with business info
        enriched_requests = []
        for request in requests:
            business = await db.users.find_one({"id": request["business_id"]})
            
            request_info = {
                "id": str(request["_id"]),
                "request_id": request["id"],
                "business_id": request["business_id"],
                "business_name": business.get("business_name", "Unknown") if business else "Unknown",
                "plan": request["plan"],
                "plan_name": request["plan_name"],
                "price": request["price"],
                "duration_days": request["duration_days"],
                "status": request["status"],
                "requested_at": request["requested_at"].isoformat() if hasattr(request["requested_at"], 'isoformat') else request["requested_at"],
                "approved_at": request.get("approved_at").isoformat() if request.get("approved_at") and hasattr(request.get("approved_at"), 'isoformat') else request.get("approved_at")
            }
            enriched_requests.append(request_info)
        
        return {"requests": enriched_requests}
        
    except Exception as e:
        logging.error(f"Error fetching featured requests: {e}")
        raise HTTPException(status_code=500, detail="Featured requests could not be loaded")

@api_router.post("/admin/featured-requests/{request_id}/approve")
async def approve_featured_request(request_id: str, current_user: dict = Depends(get_current_user)):
    """Approve featured promotion request (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get the request
        request_record = await db.featured_requests.find_one({"id": request_id})
        if not request_record:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request_record["status"] != "pending":
            raise HTTPException(status_code=400, detail="Request already processed")
        
        # Update request status
        await db.featured_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc),
                "approved_by": current_user["id"]
            }}
        )
        
        # Create featured business record
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=request_record["duration_days"])
        
        featured_business = {
            "id": str(uuid.uuid4()),
            "business_id": request_record["business_id"],
            "plan": request_record["plan"],
            "plan_name": request_record["plan_name"],
            "price": request_record["price"],
            "starts_at": start_date,
            "expires_at": end_date,
            "active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.featured_businesses.insert_one(featured_business)
        
        return {
            "message": "Featured promotion approved and activated",
            "expires_at": end_date.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error approving featured request: {e}")
        raise HTTPException(status_code=500, detail="Request could not be approved")

@api_router.post("/admin/featured-requests/{request_id}/reject")
async def reject_featured_request(request_id: str, rejection_data: dict, current_user: dict = Depends(get_current_user)):
    """Reject featured promotion request (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Update request status
        await db.featured_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "rejected",
                "rejected_at": datetime.now(timezone.utc),
                "rejected_by": current_user["id"],
                "rejection_reason": rejection_data.get("reason", "No reason provided")
            }}
        )
        
        return {"message": "Featured promotion request rejected"}
        
    except Exception as e:
        logging.error(f"Error rejecting featured request: {e}")
        raise HTTPException(status_code=500, detail="Request could not be rejected")

@api_router.get("/admin/featured-businesses")
async def get_active_featured_businesses(current_user: dict = Depends(get_current_user)):
    """Get all active featured businesses (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        featured = await db.featured_businesses.find({
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        }).sort("expires_at", 1).to_list(length=None)
        
        # Enrich with business info
        enriched_featured = []
        for item in featured:
            business = await db.users.find_one({"id": item["business_id"]})
            
            featured_info = {
                "id": str(item["_id"]),
                "business_id": item["business_id"],
                "business_name": business.get("business_name", "Unknown") if business else "Unknown",
                "plan": item["plan"],
                "plan_name": item["plan_name"],
                "price": item["price"],
                "starts_at": item["starts_at"].isoformat() if hasattr(item["starts_at"], 'isoformat') else item["starts_at"],
                "expires_at": item["expires_at"].isoformat() if hasattr(item["expires_at"], 'isoformat') else item["expires_at"],
                "remaining_days": (item["expires_at"] - datetime.now(timezone.utc)).days if hasattr(item["expires_at"], 'days') else 0
            }
            enriched_featured.append(featured_info)
        
        return {"featured_businesses": enriched_featured}
        
    except Exception as e:
        logging.error(f"Error fetching featured businesses: {e}")
        raise HTTPException(status_code=500, detail="Featured businesses could not be loaded")

# ENHANCED ADMIN PANEL FEATURES

@api_router.post("/admin/login-simple")
async def admin_simple_login():
    """DEPRECATED: Simple admin login - Use standard /auth/login instead"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Simple admin login deprecated. Use /auth/login with admin credentials."
    )
    
    # Generate admin token
    token_data = {
        "sub": "admin@kuryecini.com",  # Fixed: use email as subject
        "role": "admin",
        "email": "admin@kuryecini.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    
    access_token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user_data": {
            "id": "admin",
            "role": "admin",
            "email": "admin@kuryecini.com",
            "first_name": "Admin",
            "last_name": "User"
        }
    }

# DUMMY DATA CREATION FOR TESTING

@api_router.post("/admin/generate-dummy-data")
async def generate_dummy_data(current_user: dict = Depends(get_current_user)):
    """Generate dummy data for testing (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        created_items = {
            "customers": 0,
            "couriers": 0,
            "businesses": 0,
            "products": 0,
            "orders": 0
        }
        
        # Create dummy customers
        dummy_customers = [
            {"email": "alice@test.com", "first_name": "Alice", "last_name": "Johnson", "city": "İstanbul"},
            {"email": "bob@test.com", "first_name": "Bob", "last_name": "Smith", "city": "Ankara"},
            {"email": "carol@test.com", "first_name": "Carol", "last_name": "Brown", "city": "İzmir"}
        ]
        
        for customer_data in dummy_customers:
            customer = {
                "id": str(uuid.uuid4()),
                "email": customer_data["email"],
                "password": bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "role": "customer",
                "first_name": customer_data["first_name"],
                "last_name": customer_data["last_name"],
                "city": customer_data["city"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc)
            }
            
            # Check if exists
            existing = await db.users.find_one({"email": customer_data["email"]})
            if not existing:
                await db.users.insert_one(customer)
                created_items["customers"] += 1
        
        # Create dummy couriers
        dummy_couriers = [
            {"email": "david@courier.com", "first_name": "David", "last_name": "Wilson", "city": "İstanbul"},
            {"email": "emma@courier.com", "first_name": "Emma", "last_name": "Davis", "city": "Ankara"}
        ]
        
        for courier_data in dummy_couriers:
            courier = {
                "id": str(uuid.uuid4()),
                "email": courier_data["email"],
                "password": bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "role": "courier",
                "first_name": courier_data["first_name"],
                "last_name": courier_data["last_name"],
                "city": courier_data["city"],
                "vehicle_type": "motor",
                "vehicle_model": "Honda CB150R",
                "is_active": True,
                "kyc_approved": True,
                "is_online": False,
                "created_at": datetime.now(timezone.utc)
            }
            
            existing = await db.users.find_one({"email": courier_data["email"]})
            if not existing:
                await db.users.insert_one(courier)
                created_items["couriers"] += 1
        
        # Create dummy businesses
        dummy_businesses = [
            {"email": "pizza@business.com", "business_name": "Pizza Palace", "city": "İstanbul", "category": "gida"},
            {"email": "burger@business.com", "business_name": "Burger House", "city": "Ankara", "category": "gida"}
        ]
        
        for business_data in dummy_businesses:
            business = {
                "id": str(uuid.uuid4()),
                "email": business_data["email"],
                "password": bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "role": "business",
                "business_name": business_data["business_name"],
                "city": business_data["city"],
                "business_category": business_data["category"],
                "tax_number": f"123456789{created_items['businesses']}",
                "address": f"Test Address {created_items['businesses']}, {business_data['city']}",
                "description": f"Test restaurant - {business_data['business_name']}",
                "is_active": True,
                "is_approved": True,
                "created_at": datetime.now(timezone.utc)
            }
            
            existing = await db.users.find_one({"email": business_data["email"]})
            if not existing:
                await db.users.insert_one(business)
                created_items["businesses"] += 1
                
                # Create dummy products for this business
                dummy_products = [
                    {"name": f"Margherita Pizza", "category": "pizza", "price": 45.0, "type": "food"},
                    {"name": f"Cola", "category": "içecek", "price": 8.0, "type": "drink"},
                    {"name": f"Chicken Burger", "category": "burger", "price": 35.0, "type": "food"}
                ]
                
                for product_data in dummy_products:
                    product = {
                        "id": str(uuid.uuid4()),
                        "business_id": business["id"],
                        "name": product_data["name"],
                        "category": product_data["category"],
                        "price": product_data["price"],
                        "description": f"Delicious {product_data['name']} from {business['business_name']}",
                        "is_available": True,
                        "preparation_time_minutes": 15,
                        "created_at": datetime.now(timezone.utc)
                    }
                    
                    await db.products.insert_one(product)
                    created_items["products"] += 1
        
        return {
            "message": "Dummy data generated successfully",
            "created": created_items
        }
        
    except Exception as e:
        logging.error(f"Error generating dummy data: {e}")
        raise HTTPException(status_code=500, detail="Dummy data could not be generated")

# Test endpoint
@api_router.get("/")
async def root():
    return {"message": "Kuryecini API v11.0 - Business Panel & Admin Enhancements"}

# Add health check and menus endpoints to API router for production deployment
@api_router.get("/healthz")
async def api_health_check():
    """Health check endpoint for deployment monitoring (API version)"""
    return {"status": "ok"}

@api_router.get("/menus")
async def api_get_menus():
    """Get all menu items in standardized format (API version)"""
    try:
        # Get all products from all businesses
        businesses = await db.businesses.find({"kyc_status": "approved"}).to_list(None)
        all_menu_items = []
        
        for business in businesses:
            # Get products for this business
            products = await db.products.find({"business_id": business["id"]}).to_list(None)
            for product in products:
                menu_item = {
                    "id": product.get("id", str(product.get("_id", ""))),
                    "title": product.get("name", ""),
                    "price": float(product.get("price", 0)),
                    "imageUrl": product.get("image_url", ""),
                    "category": product.get("category", "uncategorized")
                }
                all_menu_items.append(menu_item)
        
        return all_menu_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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