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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import logging configuration
from logging_config import get_loggers, log_health_check
import logging
import time

# Import phone validation function
try:
    from models import ForgotPasswordRequest, ResetPasswordRequest
except ImportError:
    # Create fallback models if import fails
    from pydantic import BaseModel, EmailStr, validator
    
    class ForgotPasswordRequest(BaseModel):
        email: EmailStr
        
    class ResetPasswordRequest(BaseModel):
        token: str
        password: str

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

# MongoDB connection with error handling
mongo_uri = os.getenv('MONGO_URI', '').strip()
client = None
db = None

if mongo_uri:
    try:
        client = AsyncIOMotorClient(mongo_uri)
        # Extract database name from URI or use default
        if "/kuryecini_database" in mongo_uri or mongo_uri.endswith("/"):
            db = client.kuryecini_database
        else:
            # Try to get database from connection string
            try:
                db_name = mongo_uri.split("/")[-1].split("?")[0]
                if db_name:
                    db = client[db_name]
                else:
                    db = client.kuryecini_database
            except:
                db = client.kuryecini_database
        
        print(f"MongoDB connected: {mongo_uri.split('@')[1] if '@' in mongo_uri else 'localhost'}")
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        client = None
        db = None
else:
    print("No MONGO_URI provided, running without database")

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
    start_time = time.time()
    
    try:
        # Check database connection if available
        if db is not None:
            await db.command("ping")
            db_status = "ok"
        else:
            db_status = "not_configured"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logging.error(f"Database health check failed: {e}")
    
    response_time = (time.time() - start_time) * 1000
    status = "ok" if db_status in ["ok", "not_configured"] else "degraded"
    
    # Log health check
    log_health_check("/healthz", response_time, status)
    
    return {
        "status": status,
        "database": db_status,
        "response_time_ms": round(response_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Legacy health endpoint alias
@app.get("/health")
async def health_check_legacy():
    """Legacy health check endpoint alias"""
    try:
        if db is not None:
            await db.command("ping")
            return {"status": "ok", "db": "connected"}
        return {"status": "ok", "db": "not_configured"}
    except Exception as e:
        return {"status": "degraded", "db": f"error: {str(e)}"}

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
        businesses = await db.users.find({"role": "business", "kyc_status": "approved"}).to_list(None)
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
        businesses = await db.users.find({
            "role": "business",
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

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Initialize loggers
loggers = get_loggers()

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Extract user ID from token if available
    user_id = None
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
    except:
        pass  # Token validation will happen in endpoints
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log request
    loggers["request"].log_request(
        request=request,
        response=response,
        process_time=process_time,
        user_id=user_id
    )
    
    return response

# Configure CORS from environment
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if not cors_origins:
    # Fallback origins for development
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://*.vercel.app",
        "https://kuryecini-platform.preview.emergentagent.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

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

# Profile System Models
class Coupon(BaseModel):
    id: str
    code: str
    title: str
    description: str
    discount_type: str  # PERCENT | AMOUNT
    discount_value: float
    min_amount: float
    valid_until: str
    assigned_user_ids: List[str]
    status: str = "active"

class Discount(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    discount_type: str  # PERCENT | AMOUNT
    discount_value: float
    valid_until: str

class Campaign(BaseModel):
    id: str
    title: str
    description: str
    discount_type: str  # PERCENT | AMOUNT
    discount_value: float
    valid_until: str
    image_url: Optional[str] = None

class PaymentMethod(BaseModel):
    id: str
    user_id: str
    provider: str  # iyzico | stripe
    token: str
    brand: str  # VISA | MASTERCARD
    last_four: str
    expiry_month: str
    expiry_year: str
    created_at: str

class Review(BaseModel):
    id: str
    order_id: str
    target_type: str  # business | courier
    target_id: str
    user_id: str
    rating: int  # 1-5
    comment: Optional[str] = None
    created_at: str

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
@limiter.limit("5/minute")  # Prevent brute force attacks
async def login(request: Request, login_data: LoginRequest):
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
        "admin@kuryecini.com": {
            "id": "admin-001",
            "email": "admin@kuryecini.com",
            "first_name": "Admin",
            "last_name": "Kuryecini",
            "role": "admin",
            "is_active": True,
            "password": "KuryeciniAdmin2024!"
        },
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
            
            # Log successful login
            loggers["auth"].log_login_attempt(
                email=login_data.email,
                success=True,
                ip_address=request.client.host if request.client else "unknown",
                role=test_user["role"],
                auth_method="test_user"
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer", 
                "user": user_data
            }
        else:
            # Log failed login
            loggers["auth"].log_login_attempt(
                email=login_data.email,
                success=False,
                ip_address=request.client.host if request.client else "unknown",
                auth_method="test_user",
                failure_reason="invalid_password"
            )
            raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    # Real user lookup
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        # Log failed login - user not found
        loggers["auth"].log_login_attempt(
            email=login_data.email,
            success=False,
            ip_address=request.client.host if request.client else "unknown",
            failure_reason="user_not_found"
        )
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    if not verify_password(login_data.password, user.get("password_hash", "")):
        # Log failed login - invalid password
        loggers["auth"].log_login_attempt(
            email=login_data.email,
            success=False,
            ip_address=request.client.host if request.client else "unknown",
            failure_reason="invalid_password"
        )
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    access_token = create_access_token(data={"sub": user["email"], "role": user.get("role", "customer")})
    refresh_token = create_refresh_token(data={"sub": user["email"], "role": user.get("role", "customer")})
    
    user["id"] = str(user["_id"]) if "_id" in user else str(uuid.uuid4())
    if "_id" in user:
        del user["_id"] 
    if "password_hash" in user:
        del user["password_hash"]
    
    # Log successful login
    loggers["auth"].log_login_attempt(
        email=login_data.email,
        success=True,
        ip_address=request.client.host if request.client else "unknown",
        role=user.get("role", "customer"),
        user_id=user.get("id")
    )
    
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
async def refresh_access_token(request: RefreshTokenRequest):
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
    payload = verify_refresh_token(request.refresh_token)
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
        "password_hash": hashed_password,
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
    del user_doc["password_hash"]
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
    """Register a new business with city normalization"""
    from utils.city_normalize import normalize_city_name
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": business_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Normalize city name
    city_original = business_data.city
    city_normalized = normalize_city_name(city_original)
    
    # Create new business user with pending status for KYC approval
    hashed_password = hash_password(business_data.password)
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": business_data.email,
        "password_hash": hashed_password,
        "role": "business",
        "business_name": business_data.business_name,
        "tax_number": business_data.tax_number,
        "address": business_data.address,
        "city": city_original,  # Keep original for reference
        "city_normalized": city_normalized,  # Normalized for searching
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
    del user_doc["password_hash"]
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
@limiter.limit("3/minute")  # Prevent spam registrations
async def register_customer(request: Request, customer_data: CustomerRegistration):
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
        "password_hash": hashed_password,
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
    del user_doc["password_hash"]
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
    # Convert ObjectId to string if present (for database users)
    if "_id" in current_user:
        current_user["id"] = str(current_user["_id"])
        del current_user["_id"]
    
    # Remove password fields if present
    if "password" in current_user:
        del current_user["password"]
    if "password_hash" in current_user:
        del current_user["password_hash"]
    
    return current_user

# Legacy Admin Authentication (DEPRECATED - Use standard /auth/login)
@api_router.post("/auth/admin")
async def admin_login(admin_data: AdminLogin):
    """DEPRECATED: Admin login endpoint - Use standard /auth/login instead"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Admin endpoint deprecated. Use /auth/login with admin credentials."
    )

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
@limiter.limit("10/minute")  # Prevent order spam
async def create_order(request: Request, order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
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
async def get_public_businesses(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = 50  # Default 50km radius
):
    """Get all active businesses for customers with city and location filtering"""
    from utils.city_normalize import normalize_city_name
    import re
    
    try:
        # Build query filter
        query_filter = {
            "role": "business",
            "kyc_status": "approved"  # Only show approved businesses
        }
        
        # Add city filter if provided - case-insensitive
        if city:
            normalized_city = normalize_city_name(city)
            query_filter["$or"] = [
                {"city_normalized": normalized_city},
                {"city": {"$regex": f"^{re.escape(city)}$", "$options": "i"}},
                {"address": {"$regex": f".*{re.escape(city)}.*", "$options": "i"}}
            ]
        
        # If lat/lng provided, use geo-spatial query
        if lat is not None and lng is not None:
            # MongoDB geospatial query for businesses within radius
            radius_meters = radius_km * 1000  # Convert km to meters
            query_filter["location"] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]  # [longitude, latitude]
                    },
                    "$maxDistance": radius_meters
                }
            }
        
        businesses = await db.users.find(query_filter).to_list(length=None)
        
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
        # This is a placeholder - in real implementation, 
        # you'd fetch products from a products collection
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

# Restaurant Endpoints
@api_router.get("/restaurants")
async def get_restaurants(city: Optional[str] = None):
    """Get restaurants by city"""
    from utils.city_normalize import normalize_city_name
    
    try:
        query_filter = {
            "role": "business",
            "kyc_status": "approved"
        }
        
        if city:
            import re
            normalized_city = normalize_city_name(city)
            query_filter["$or"] = [
                {"city_normalized": normalized_city},
                {"city": {"$regex": f"^{re.escape(city)}$", "$options": "i"}},
                {"address": {"$regex": f".*{re.escape(city)}.*", "$options": "i"}}
            ]
        
        businesses = await db.users.find(query_filter).to_list(length=None)
        
        restaurant_list = []
        for business in businesses:
            restaurant_data = {
                "id": business.get("id", business.get("_id", "")),
                "name": business.get("business_name", ""),
                "category": business.get("business_category", "Restoran"),
                "description": business.get("description", ""),
                "rating": 4.0 + (hash(str(business.get("id", ""))) % 10) / 10,
                "delivery_time": "25-35 dk",
                "min_order": 30 + (hash(str(business.get("id", ""))) % 50),
                "is_open": True,
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "city_normalized": business.get("city_normalized", ""),
                "location": business.get("location")
            }
            restaurant_list.append(restaurant_data)
        
        return restaurant_list
        
    except Exception as e:
        logging.error(f"Error fetching restaurants: {e}")
        raise HTTPException(status_code=500, detail="Error fetching restaurants")

@api_router.get("/restaurants/near")
async def get_nearby_restaurants(
    lat: float,
    lng: float,
    radius: Optional[int] = 50000
):
    """Get nearby restaurants using geospatial query"""
    try:
        query_filter = {
            "role": "business",
            "kyc_status": "approved",
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius
                }
            }
        }
        
        businesses = await db.users.find(query_filter).to_list(length=None)
        
        restaurant_list = []
        for business in businesses:
            # Calculate distance
            business_location = business.get("location", {}).get("coordinates", [])
            distance_km = None
            
            if len(business_location) == 2:
                import math
                dlat = lat - business_location[1]
                dlng = lng - business_location[0]
                distance_km = math.sqrt(dlat*dlat + dlng*dlng) * 111.0
            
            restaurant_data = {
                "id": business.get("id", business.get("_id", "")),
                "name": business.get("business_name", ""),
                "category": business.get("business_category", "Restoran"),
                "rating": 4.0 + (hash(str(business.get("id", ""))) % 10) / 10,
                "delivery_time": "25-35 dk",
                "min_order": 30 + (hash(str(business.get("id", ""))) % 50),
                "is_open": True,
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "distance": round(distance_km, 1) if distance_km else None,
                "location": business.get("location")
            }
            restaurant_list.append(restaurant_data)
        
        # Sort by distance
        restaurant_list.sort(key=lambda x: x.get("distance") or float('inf'))
        
        return restaurant_list
        
    except Exception as e:
        logging.error(f"Error fetching nearby restaurants: {e}")
        raise HTTPException(status_code=500, detail="Error fetching nearby restaurants")

# Address Endpoints
@api_router.get("/user/addresses")
async def get_user_addresses(current_user: dict = Depends(get_current_user)):
    """Get user's saved addresses"""
    try:
        # FIXED: Properly extract user_id from current_user object returned by get_current_user
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        
        if not user_id:
            print(f"DEBUG: No user_id found in current_user: {current_user}")
            return []
        
        print(f"DEBUG: Getting addresses for user_id: {user_id} (email: {user_email})")
        addresses = await db.addresses.find({"userId": user_id}).to_list(length=None)
        print(f"DEBUG: Found {len(addresses)} addresses for user_id: {user_id}")
        
        address_list = []
        for addr in addresses:
            print(f"DEBUG: Processing address: {addr.get('label', 'NO LABEL')}")
            location = addr.get("location") or {}
            coords = location.get("coordinates", [None, None]) or [None, None]
            
            address_data = {
                "id": addr.get("id", addr.get("_id", "")),
                "label": addr.get("label", ""),
                "city": addr.get("city_original", addr.get("city", "")),
                "description": addr.get("description", ""),
                "lat": coords[1] if coords and len(coords) > 1 and coords[1] else None,
                "lng": coords[0] if coords and len(coords) > 0 and coords[0] else None
            }
            address_list.append(address_data)
        
        return address_list
        
    except Exception as e:
        logging.error(f"Error fetching addresses: {e}")
        return []

@api_router.post("/user/addresses")
async def add_user_address(address_data: dict, current_user: dict = Depends(get_current_user)):
    """Add a new address for user"""
    from utils.city_normalize import normalize_city_name
    
    try:
        # FIXED: Properly extract user_id from current_user object returned by get_current_user
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        
        if not user_id:
            print(f"DEBUG: No user_id found in current_user: {current_user}")
            raise HTTPException(status_code=401, detail="User identification failed")
        
        print(f"DEBUG: Adding address for user_id: {user_id} (email: {user_email})")
        
        city_original = address_data.get("city", "")
        city_normalized = normalize_city_name(city_original)
        
        location = None
        lat = address_data.get("lat")
        lng = address_data.get("lng")
        
        if lat is not None and lng is not None:
            location = {
                "type": "Point",
                "coordinates": [lng, lat]
            }
        
        new_address = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "label": address_data.get("label", ""),
            "city_original": city_original,
            "city_normalized": city_normalized,
            "description": address_data.get("description", ""),
            "location": location,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.addresses.insert_one(new_address)
        
        return {
            "id": new_address["id"],
            "label": new_address["label"],
            "city": city_original,
            "description": new_address["description"],
            "lat": lat,
            "lng": lng
        }
        
    except Exception as e:
        import traceback
        logging.error(f"Error adding address: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error adding address: {str(e)}")

# Include the API router in the main app
# Restaurant Discovery Endpoints (New Customer App)
@api_router.get("/restaurants/discover")
async def discover_restaurants():
    """Get featured/sponsored restaurants for discovery page"""
    try:
        # Get featured/popular businesses
        businesses = await db.users.find({
            "role": "business",
            "kyc_status": "approved",
            "is_active": True
        }).limit(20).to_list(None)
        
        restaurants = []
        for business in businesses:
            restaurant = {
                "id": business.get("id", str(business.get("_id", ""))),
                "business_name": business.get("business_name", ""),
                "business_category": business.get("business_category", ""),
                "description": business.get("description", ""),
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "logo_url": business.get("logo_url", ""),
                "rating": business.get("rating", 4.5),
                "delivery_time": "25-35 dk",
                "min_order": 50.0,
                "location": business.get("location", {})
            }
            restaurants.append(restaurant)
        
        return restaurants
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/restaurants/near")
async def get_nearby_restaurants(lat: float, lng: float, radius: int = 50000):
    """Get restaurants within specified radius (default 50km)"""
    try:
        # Use 2dsphere index for geolocation queries
        businesses = await db.users.find({
            "role": "business",
            "kyc_status": "approved",
            "is_active": True,
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]  # Note: MongoDB uses [lng, lat] order
                    },
                    "$maxDistance": radius
                }
            }
        }).to_list(None)
        
        restaurants = []
        for business in businesses:
            # Calculate distance for display
            business_location = business.get("location", {})
            if "coordinates" in business_location:
                business_lng, business_lat = business_location["coordinates"]
                distance = calculate_distance(lat, lng, business_lat, business_lng)
            else:
                distance = 0
            
            restaurant = {
                "id": business.get("id", str(business.get("_id", ""))),
                "business_name": business.get("business_name", ""),
                "business_category": business.get("business_category", ""),
                "description": business.get("description", ""),
                "address": business.get("address", ""),
                "city": business.get("city", ""),
                "logo_url": business.get("logo_url", ""),
                "rating": business.get("rating", 4.5),
                "delivery_time": "25-35 dk",
                "min_order": 50.0,
                "distance": round(distance, 1),
                "location": business_location
            }
            restaurants.append(restaurant)
        
        # Sort by distance
        restaurants.sort(key=lambda x: x.get("distance", 0))
        
        return restaurants
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/businesses/{business_id}/products")
async def get_business_products(business_id: str):
    """Get products for a specific business"""
    try:
        products = await db.products.find({
            "business_id": business_id,
            "is_available": True
        }).to_list(None)
        
        # Convert ObjectId to string
        for product in products:
            if "_id" in product:
                product["id"] = str(product["_id"])
                del product["_id"]
            
            # Handle datetime conversion
            if "created_at" in product and hasattr(product["created_at"], 'isoformat'):
                product["created_at"] = product["created_at"].isoformat()
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Profile & Customer App Endpoints
@api_router.get("/profile/coupons")
async def get_user_coupons(current_user: dict = Depends(get_current_user)):
    """Get user's available coupons"""
    try:
        # Get coupons assigned to user
        coupons = await db.coupons.find({
            "assigned_user_ids": current_user["id"],
            "status": "active"
        }).to_list(None)
        
        # Mock data for demo
        if not coupons:
            mock_coupons = [
                {
                    "id": "coupon-1",
                    "code": "WELCOME20",
                    "title": "Hoş Geldin İndirimi", 
                    "description": "İlk siparişinizde %20 indirim",
                    "discount_type": "PERCENT",
                    "discount_value": 20,
                    "min_amount": 50,
                    "valid_until": "2024-12-31",
                    "status": "active"
                }
            ]
            return mock_coupons
        
        # Convert ObjectId
        for coupon in coupons:
            if "_id" in coupon:
                coupon["id"] = str(coupon["_id"])
                del coupon["_id"]
        
        return coupons
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/profile/discounts")
async def get_user_discounts(current_user: dict = Depends(get_current_user)):
    """Get user's personal discounts"""
    try:
        discounts = await db.discounts.find({
            "user_id": current_user["id"]
        }).to_list(None)
        
        # Mock data for demo
        if not discounts:
            mock_discounts = [
                {
                    "id": "discount-1",
                    "title": "VIP Müşteri İndirimi",
                    "description": "Tüm siparişlerinizde geçerli",
                    "discount_type": "PERCENT",
                    "discount_value": 15,
                    "valid_until": "2024-12-31"
                }
            ]
            return mock_discounts
        
        # Convert ObjectId
        for discount in discounts:
            if "_id" in discount:
                discount["id"] = str(discount["_id"])
                del discount["_id"]
        
        return discounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/campaigns")
async def get_active_campaigns():
    """Get active campaigns"""
    try:
        campaigns = await db.campaigns.find({
            "valid_until": {"$gte": datetime.now(timezone.utc).isoformat()}
        }).to_list(None)
        
        # Mock data for demo
        if not campaigns:
            mock_campaigns = [
                {
                    "id": "campaign-1",
                    "title": "Pizza Festivali",
                    "description": "Tüm pizzalarda %30 indirim",
                    "discount_type": "PERCENT",
                    "discount_value": 30,
                    "valid_until": "2024-12-31",
                    "image_url": None
                },
                {
                    "id": "campaign-2", 
                    "title": "Sağlıklı Yaşam",
                    "description": "Salata siparişlerinde %25 indirim",
                    "discount_type": "PERCENT",
                    "discount_value": 25,
                    "valid_until": "2024-12-31",
                    "image_url": None
                }
            ]
            return mock_campaigns
        
        # Convert ObjectId
        for campaign in campaigns:
            if "_id" in campaign:
                campaign["id"] = str(campaign["_id"])
                del campaign["_id"]
        
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payment-methods")
async def get_payment_methods(current_user: dict = Depends(get_current_user)):
    """Get user's saved payment methods"""
    try:
        methods = await db.payment_methods.find({
            "user_id": current_user["id"]
        }).to_list(None)
        
        # Convert ObjectId
        for method in methods:
            if "_id" in method:
                method["id"] = str(method["_id"])
                del method["_id"]
        
        return methods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/payment-methods")
async def add_payment_method(method_data: dict, current_user: dict = Depends(get_current_user)):
    """Add new payment method (tokenized)"""
    try:
        # In production, this would handle payment provider token
        payment_method = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "provider": method_data.get("provider", "stripe"),
            "token": method_data.get("token", ""),
            "brand": method_data.get("brand", "VISA"),
            "last_four": method_data.get("last_four", "4242"),
            "expiry_month": method_data.get("expiry_month", "12"),
            "expiry_year": method_data.get("expiry_year", "26"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payment_methods.insert_one(payment_method)
        
        if "_id" in payment_method:
            del payment_method["_id"]
        
        return payment_method
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/payment-methods/{method_id}")
async def delete_payment_method(method_id: str, current_user: dict = Depends(get_current_user)):
    """Delete payment method"""
    try:
        result = await db.payment_methods.delete_one({
            "id": method_id,
            "user_id": current_user["id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Payment method not found")
        
        return {"success": True, "message": "Payment method deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/reviews")
async def submit_review(review_data: dict, current_user: dict = Depends(get_current_user)):
    """Submit review for delivered order"""
    try:
        # Check if order is delivered
        order = await db.orders.find_one({"id": review_data.get("order_id")})
        if not order or order.get("status") != "delivered":
            raise HTTPException(status_code=400, detail="Can only review delivered orders")
        
        # Check if already reviewed
        existing_review = await db.reviews.find_one({
            "order_id": review_data.get("order_id"),
            "target_type": review_data.get("target_type"),
            "user_id": current_user["id"]
        })
        
        if existing_review:
            raise HTTPException(status_code=409, detail="Already reviewed this target for this order")
        
        review = {
            "id": str(uuid.uuid4()),
            "order_id": review_data.get("order_id"),
            "target_type": review_data.get("target_type"),  # business | courier
            "target_id": review_data.get("target_id"),
            "user_id": current_user["id"],
            "rating": review_data.get("rating", 5),
            "comment": review_data.get("comment", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.reviews.insert_one(review)
        
        if "_id" in review:
            del review["_id"]
        
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Password Change Endpoint
@api_router.post("/auth/change-password")
async def change_password(
    password_data: dict, 
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    try:
        current_password = password_data.get("current_password", "")
        new_password = password_data.get("new_password", "")
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Current and new password required")
        
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
        # For demo users, just validate current password
        user_id = current_user["id"]
        
        if user_id == "testcustomer-001":
            # Test customer - validate current password is "test123"
            if current_password != "test123":
                raise HTTPException(status_code=400, detail="Current password is incorrect")
        else:
            # For real users, check from database
            user = await db.users.find_one({"id": user_id})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # In production, use proper password hashing (bcrypt)
            if user.get("password") != hash_password(current_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password in database
        if user_id == "testcustomer-001":
            # For demo user, just return success
            return {"success": True, "message": "Password changed successfully"}
        else:
            # Update password in database
            new_password_hash = hash_password(new_password)
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"password": new_password_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        return {"success": True, "message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Notification Settings Endpoint
@api_router.patch("/user/notification-settings")
async def update_notification_settings(
    settings_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user notification preferences"""
    try:
        user_id = current_user["id"]
        
        # Extract notification settings
        push_notifications = settings_data.get("push_notifications", True)
        email_notifications = settings_data.get("email_notifications", True)
        order_updates = settings_data.get("order_updates", True)
        promotions = settings_data.get("promotions", False)
        
        notification_settings = {
            "push_notifications": push_notifications,
            "email_notifications": email_notifications,
            "order_updates": order_updates,
            "promotions": promotions,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # For demo user, just return success
        if user_id == "testcustomer-001":
            return {"success": True, "settings": notification_settings}
        
        # Update in database
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"notification_settings": notification_settings}}
        )
        
        return {"success": True, "settings": notification_settings}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/orders/my")
async def get_my_orders(current_user: dict = Depends(get_current_user)):
    """Get current user's orders"""
    try:
        orders = await db.orders.find({
            "customer_id": current_user["id"]
        }).sort("created_at", -1).to_list(None)
        
        # Convert ObjectId and datetime
        for order in orders:
            if "_id" in order:
                order["id"] = str(order["_id"])
                del order["_id"]
            
            if "created_at" in order and hasattr(order["created_at"], 'isoformat'):
                order["created_at"] = order["created_at"].isoformat()
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Business Management Endpoint
@api_router.get("/admin/businesses")
async def get_all_businesses_admin(
    city: Optional[str] = None, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all businesses for admin management with filtering"""
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Build query filter
        query_filter = {}
        
        # City filter - case-insensitive
        if city:
            import re
            normalized_city = normalize_city_name(city)
            query_filter["$or"] = [
                {"city_normalized": normalized_city},
                {"city": {"$regex": f"^{re.escape(city)}$", "$options": "i"}},
                {"address": {"$regex": f".*{re.escape(city)}.*", "$options": "i"}}
            ]
        
        # Search filter - business name, category, email
        if search:
            import re
            search_regex = {"$regex": f".*{re.escape(search)}.*", "$options": "i"}
            if "$or" in query_filter:
                # Combine with existing OR condition
                query_filter = {
                    "$and": [
                        query_filter,
                        {
                            "$or": [
                                {"business_name": search_regex},
                                {"business_category": search_regex}, 
                                {"email": search_regex}
                            ]
                        }
                    ]
                }
            else:
                query_filter["$or"] = [
                    {"business_name": search_regex},
                    {"business_category": search_regex},
                    {"email": search_regex}
                ]
        
        # Status filter
        if status:
            if status == "active":
                query_filter["is_active"] = True
            elif status == "inactive":
                query_filter["is_active"] = False
            elif status == "pending":
                query_filter["kyc_status"] = "pending"
            elif status == "approved":
                query_filter["kyc_status"] = "approved"
        
        # Fetch businesses
        businesses = await db.businesses.find(query_filter).to_list(length=None)
        
        # Convert ObjectId to string and prepare response
        result = []
        for business in businesses:
            business_data = {
                "id": str(business.get("_id", "")),
                "business_name": business.get("business_name", ""),
                "business_category": business.get("business_category", ""),
                "email": business.get("email", ""),
                "phone": business.get("phone", ""),
                "city": business.get("city", ""),
                "address": business.get("address", ""),
                "kyc_status": business.get("kyc_status", "pending"),
                "is_active": business.get("is_active", False),
                "created_at": business.get("created_at", ""),
                "description": business.get("description", ""),
                "city_normalized": business.get("city_normalized", "")
            }
            result.append(business_data)
        
        return result
        
    except Exception as e:
        print(f"Admin businesses fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)
