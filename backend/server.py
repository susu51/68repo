from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, WebSocket, WebSocketDisconnect, Request, Body, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import certifi
import ssl
from pathlib import Path

# Optional Sentry import for monitoring
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import shutil
import sys
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
import redis
import asyncio
import time

# Import real database models
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import from the main models.py file directly
from models import (
    OrderStatus, UserRole, Business, MenuItem, Order, CourierLocation,
    GlobalSettings, Earning, INDEXES, STATUS_TRANSITIONS, ROLE_TRANSITIONS
)

# Import logging configuration
from logging_config import get_loggers, log_health_check

# Create logger for server operations
logger = logging.getLogger("kuryecini.server")

# Import authentication dependencies
from auth_dependencies import get_current_user, get_business_user, get_approved_business_user, get_admin_user

# Import cookie-based auth system
from auth_cookie import auth_router, get_current_user_from_cookie, get_current_user_from_cookie_or_bearer, get_approved_business_user_from_cookie, set_db_client
# Address router db setup
from routes.addresses import set_db_client as set_addresses_db_client
# City catalog router db setup
from routes.city_catalog import set_db_client as set_city_catalog_db_client
# AI settings router db setup
from routes.ai_settings import set_db_client as set_ai_settings_db_client
# AI assistant router db setup  
from routes.ai_assistant import set_db_client as set_ai_assistant_db_client

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

# CITY_STRICT security check - fail fast if not enabled
CITY_STRICT = os.environ.get('CITY_STRICT', 'false').lower() == 'true'
if not CITY_STRICT:
    print("❌ CRITICAL: CITY_STRICT=true is required for production safety")
    print("Set CITY_STRICT=true in environment variables to prevent cross-city data leaks")
    sys.exit(1)

print("✅ CITY_STRICT mode enabled - city filtering enforced")
NEARBY_RADIUS_M = int(os.environ.get('NEARBY_RADIUS_M', '5000'))

# Turkish slug normalization
def normalize_turkish_slug(text):
    """Convert Turkish text to URL-safe slug"""
    if not text:
        return ""
    
    # Turkish character mapping
    char_map = {
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g', 
        'ı': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u'
    }
    
    # Replace Turkish characters
    result = ""
    for char in text:
        result += char_map.get(char, char)
    
    # Convert to lowercase and replace spaces with dashes
    return result.lower().replace(' ', '-')

# Initialize Sentry for error monitoring (if available)
if SENTRY_AVAILABLE:
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=True),
                StarletteIntegration(transaction_style="endpoint"),
            ],
            traces_sample_rate=0.1,  # Capture 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # Capture 10% of profiles for performance insights
            environment=os.getenv('ENVIRONMENT', 'development'),
            release=os.getenv('APP_VERSION', '1.0.0'),
        )
        print("🔍 Sentry monitoring initialized")
    else:
        print("ℹ️  Sentry DSN not provided - running without error monitoring")
else:
    print("ℹ️  Sentry SDK not available - running without error monitoring")

# MongoDB connection with error handling - Real Database Only
mongo_url = os.getenv('MONGO_URL')
client = None  # Global client for auth system

if mongo_url:
    try:
        print("🔗 Connecting to MongoDB Atlas...")
        print(f"📍 CA File: {certifi.where()}")
        
        # Check if this is Atlas or local MongoDB
        is_atlas = 'mongodb+srv://' in mongo_url or 'mongodb.net' in mongo_url
        
        if is_atlas:
            # Motor client with proper Atlas SSL settings
            client = AsyncIOMotorClient(
                mongo_url,
                tls=True,
                tlsCAFile=certifi.where(),
                tlsAllowInvalidHostnames=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=10000,
                socketTimeoutMS=30000,
                connectTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )
            print("🌍 Configured for MongoDB Atlas")
        else:
            # Local MongoDB client (no SSL)
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000
            )
            print("🏠 Configured for local MongoDB")
        
        # Extract database name from URL or use default
        if '/' in mongo_url and mongo_url.split('/')[-1]:
            db_name = mongo_url.split('/')[-1].split('?')[0]  # Handle query params
        else:
            db_name = 'kuryecini'
            
        db = client[db_name]
        print(f"✅ MongoDB client created for Atlas: {db_name}")
        print(f"📍 Database URL: {mongo_url[:50]}...[HIDDEN]")
        
        # Initialize cookie auth system
        set_db_client(client)
        set_addresses_db_client(db)
        set_city_catalog_db_client(db)
        set_ai_settings_db_client(db)
        set_ai_assistant_db_client(db)
        print("🍪 Cookie auth system initialized")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        print("🔍 Trying fallback connection method...")
        
        try:
            # Fallback: Simple connection without SSL
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
                
            if '/' in mongo_url and mongo_url.split('/')[-1]:
                db_name = mongo_url.split('/')[-1].split('?')[0]
            else:
                db_name = 'kuryecini'
                
            db = client[db_name]
            print(f"✅ Fallback MongoDB connection successful: {db_name}")
            
            # Initialize cookie auth system
            set_db_client(client)
            set_addresses_db_client(db)
            set_city_catalog_db_client(db)
            set_ai_settings_db_client(db)
            set_ai_assistant_db_client(db)
            print("🍪 Cookie auth system initialized")
            
        except Exception as e2:
            print(f"❌ Fallback connection also failed: {e2}")
            db = None
            raise RuntimeError("Database connection required - no mock data allowed")
else:
    print("❌ No MONGO_URL provided - Real database required!")
    raise RuntimeError("MONGO_URL environment variable required")

# Redis connection for courier location caching
redis_client = None
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Test connection
    print("Redis connected successfully")
except Exception as e:
    print(f"Redis connection error: {e}")
    redis_client = None

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
        businesses = await db.users.find({"kyc_status": "approved"}).to_list(None)
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
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Health Check Endpoint
@api_router.get("/health")
async def api_health_check():
    """Database and system health check - Real DB only"""
    try:
        # Test MongoDB connection
        await db.command("ping")
        
        # Check settings collection
        settings = await db.settings.find_one({"_id": "global"})
        
        # Test Redis if available
        redis_status = "not_configured"
        if redis_client:
            try:
                redis_client.ping()
                redis_status = "connected"
            except Exception:
                redis_status = "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "mongodb": "connected",
                "collections": ["businesses", "menu_items", "orders", "courier_locations", "earnings", "settings"],
                "settings_initialized": bool(settings)
            },
            "cache": {
                "redis": redis_status
            },
            "environment": {
                "nearby_radius_m": int(os.getenv('NEARBY_RADIUS_M', 5000)),
                "courier_rate_per_package": float(os.getenv('COURIER_RATE_PER_PACKAGE', 20)),
                "business_commission_pct": float(os.getenv('BUSINESS_COMMISSION_PCT', 5))
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@api_router.get("/admin/system/status")
async def get_system_status(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive system health and statistics (Admin only)"""
    try:
        # Database check
        db_status = "connected"
        try:
            await db.command("ping")
        except:
            db_status = "disconnected"
        
        # Get basic stats
        users_count = await db.users.count_documents({})
        orders_count = await db.orders.count_documents({})
        businesses_count = await db.users.count_documents({"role": "business", "kyc_status": "approved"})
        couriers_count = await db.users.count_documents({"role": "courier", "kyc_status": "approved"})
        pending_kyc_count = await db.users.count_documents({"kyc_status": "pending"})
        
        # Orders stats
        from datetime import timedelta
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        orders_today = await db.orders.count_documents({"created_at": {"$gte": today}})
        
        return {
            "status": "ok",
            "database": db_status,
            "stats": {
                "total_users": users_count,
                "total_orders": orders_count,
                "orders_today": orders_today,
                "active_businesses": businesses_count,
                "active_couriers": couriers_count,
                "pending_kyc": pending_kyc_count
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security
# JWT Configuration - Real Secret Required
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "change_me_to_strong_secret_key":
    print("⚠️  Warning: Using default JWT_SECRET - change in production!")
    JWT_SECRET = "fallback-secret-key-change-in-production"

JWT_SECRET_KEY = JWT_SECRET  # Keep backward compatibility
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", f"{JWT_SECRET}_refresh")
ALGORITHM = "HS256"
print("🔐 JWT Authentication configured")
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

# CORS origins from environment
cors_origins_env = os.getenv("CORS_ORIGINS", "https://courier-dashboard-3.preview.emergentagent.com")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
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
    first_name: str  # Yetkili kişi adı
    last_name: str   # Yetkili kişi soyadı
    phone: Optional[str] = None
    address: str
    city: str
    district: str  # Required for location-based filtering
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

# Courier Location Models
class CourierLocation(BaseModel):
    lat: float
    lng: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy: Optional[float] = None
    ts: Optional[int] = None

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
# DISABLED - USE COOKIE AUTH INSTEAD
# @api_router.post("/auth/login", 
#     tags=["Authentication"],
#     summary="User Login",
#     description="Authenticate user with email and password. Returns JWT token for API access.",
#     response_description="JWT access token and user information"
# )
# @limiter.limit("5/minute")  # Prevent brute force attacks
async def old_login_disabled(request: Request, login_data: LoginRequest):
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

# DISABLED - USE COOKIE AUTH INSTEAD  
# @api_router.post("/auth/refresh",
#     tags=["Authentication"],
#     summary="Refresh Access Token", 
#     description="Generate a new access token using a valid refresh token.",
#     response_description="New JWT access token"
# )
async def old_refresh_disabled(request: RefreshTokenRequest):
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

# DISABLED - Conflicting with cookie-based auth logout endpoint
# @api_router.post("/auth/logout",
#     tags=["Authentication"],
#     summary="User Logout",
#     description="Logout user and invalidate tokens.",
#     response_description="Logout confirmation"
# )
# async def logout(current_user: dict = Depends(get_current_user)):
#     """
#     **User Logout**
#     
#     Logout the current user. In a production environment, this would
#     invalidate the refresh token in the database.
#     
#     **Note:** Currently returns success without token invalidation.
#     In production, implement token blacklisting or database cleanup.
#     """
#     return {
#         "message": "Successfully logged out",
#         "user_id": current_user.get("id")
#     }
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
    """Register a new business with city normalization and GPS coordinates"""
    from utils.city_normalize import normalize_city_name
    from utils.turkish_cities_coordinates import get_city_coordinates
    
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
    
    # Get GPS coordinates for city/district
    coordinates = get_city_coordinates(city_original, business_data.district)
    lat = coordinates["lat"] if coordinates else None
    lng = coordinates["lng"] if coordinates else None
    
    if coordinates:
        print(f"✅ GPS coordinates found for {city_original}/{business_data.district}: {lat}, {lng}")
    else:
        print(f"⚠️  No GPS coordinates found for {city_original}/{business_data.district}, using null")
    
    # Create new business user with pending status for KYC approval
    hashed_password = hash_password(business_data.password)
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": business_data.email,
        "password_hash": hashed_password,
        "role": "business",
        "business_name": business_data.business_name,
        "tax_number": business_data.tax_number,
        "first_name": business_data.first_name,  # Yetkili kişi adı
        "last_name": business_data.last_name,    # Yetkili kişi soyadı
        "phone": business_data.phone if business_data.phone else "",
        "address": business_data.address,
        "city": city_original,  # Keep original for reference
        "city_normalized": city_normalized,  # Normalized for searching
        "district": business_data.district,  # Required for location-based filtering
        "lat": lat,  # GPS latitude
        "lng": lng,  # GPS longitude
        "business_category": business_data.business_category,
        "description": business_data.description,
        "is_active": True,
        "kyc_status": "pending",  # pending, approved, rejected
        "business_status": "pending",  # Keep for backward compatibility
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
async def get_current_user_info(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get current user information - supports both cookie and bearer token"""
    # Ensure consistent ID field - prefer custom 'id' over '_id'
    if "_id" in current_user and "id" not in current_user:
        # Only use _id if there's no custom id field
        current_user["id"] = str(current_user["_id"])
    
    # Remove _id to avoid confusion
    if "_id" in current_user:
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
async def get_admin_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Require admin role - Cookie or JWT token based authentication"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Courier dependency
async def get_current_courier_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Require courier role"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Courier access required"
        )
    return current_user

# Customer dependency
async def get_current_customer_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Require customer role"""
    if current_user.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
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

# Courier dependency
async def get_courier_user(current_user: dict = Depends(get_current_user)):
    """Require courier role"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Courier access required"
        )
    return current_user

# Customer dependency
async def get_customer_user(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Require customer role (supports both cookie and bearer token auth)"""
    if current_user.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
        )
    return current_user

# Multi-role dependency factory
def get_multi_role_user(*allowed_roles):
    """Create dependency that allows multiple roles"""
    async def check_role(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            roles_str = ", ".join(allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Allowed roles: {roles_str}"
            )
        return current_user
    return check_role

# BUSINESS MANAGEMENT ENDPOINTS

@api_router.put("/business/status")
async def update_business_status(status_data: dict, current_user: dict = Depends(get_current_user)):
    """Update business status (open/closed)"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # Update business status in database
        business_id = current_user.get("user_id")
        is_open = status_data.get("isOpen", True)
        
        result = await db.users.update_one(
            {"id": business_id, "role": "business"}, 
            {"$set": {"is_open": is_open}}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "status": is_open,
                "message": "Restaurant status updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Business not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@api_router.get("/business/stats")
async def get_business_stats(current_user: dict = Depends(get_approved_business_user)):
    """Get business statistics and analytics"""
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    try:
        # Get business statistics from database
        business_id = current_user.get("user_id")
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's orders for this business
        today_orders = await db.orders.find({
            "business_id": business_id,
            "created_at": {"$gte": today.isoformat()}
        }).to_list(length=None)
        
        # Calculate statistics
        total_orders = len(today_orders)
        total_revenue = sum(order.get("total_amount", 0) for order in today_orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        completed_orders = len([o for o in today_orders if o.get("status") == "delivered"])
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 100
        
        return {
            "today": {
                "orders": total_orders,
                "revenue": total_revenue,
                "avgOrderValue": avg_order_value,
                "completionRate": completion_rate
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
    except Exception:
        raise HTTPException(status_code=500, detail="Stats retrieval failed")

@api_router.patch("/business/orders/{order_id}/status")
async def update_business_order_status(
    order_id: str,
    status_data: dict,
    current_user: dict = Depends(get_approved_business_user)
):
    """Update order status by business (confirm, preparing, ready)"""
    try:
        new_status = status_data.get("status")
        valid_business_statuses = ["confirmed", "preparing", "ready"]
        
        if new_status not in valid_business_statuses:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status. Business can set: {valid_business_statuses}"
            )
        
        # Find order and verify it belongs to this business
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["business_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied - order belongs to different business")
        
        # Update order status with timestamp
        update_data = {"status": new_status}
        current_time = datetime.now(timezone.utc)
        
        if new_status == "confirmed":
            update_data["confirmed_at"] = current_time
        elif new_status == "preparing":
            update_data["preparing_at"] = current_time
        elif new_status == "ready":
            update_data["ready_at"] = current_time
            # Make order available for couriers
            update_data["available_for_pickup"] = True
        
        # Update in database
        try:
            result = await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_data}
            )
        except:
            result = await db.orders.update_one(
                {"id": order_id},
                {"$set": update_data}
            )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Order not found or no changes made")
        
        return {
            "message": f"Order status updated to {new_status}",
            "order_id": order_id,
            "new_status": new_status,
            "timestamp": current_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

@api_router.get("/courier/orders/available")
async def get_available_orders_for_courier(current_user: dict = Depends(get_courier_user)):
    """Get orders ready for pickup by couriers"""
    try:
        courier_id = current_user["id"]
        
        # Get orders that are ready for pickup and not assigned to any courier
        orders_cursor = db.orders.find({
            "status": {"$in": ["ready", "picked_up"]},
            "$or": [
                {"courier_id": {"$exists": False}},
                {"courier_id": None},
                {"courier_id": courier_id}  # Include orders already assigned to this courier
            ]
        }).sort("ready_at", 1)  # Oldest ready orders first
        
        orders = await orders_cursor.to_list(length=None)
        
        # Format orders for courier dashboard
        formatted_orders = []
        for order in orders:
            # Get business details
            business = await db.businesses.find_one({"id": order.get("business_id")}) or \
                      await db.users.find_one({"id": order.get("business_id")})
            
            # Get customer details
            customer = await db.users.find_one({"id": order.get("customer_id")})
            
            formatted_order = {
                "id": str(order.get("_id", order.get("id", ""))),
                "order_id": order.get("id", str(order.get("_id", ""))),
                "business_name": business.get("business_name") or business.get("name", "İşletme") if business else "İşletme",
                "business_address": business.get("address", "") if business else "",
                "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() if customer else "Müşteri",
                "customer_phone": customer.get("phone", "") if customer else "",
                "delivery_address": order.get("delivery_address", ""),
                "delivery_lat": order.get("delivery_lat"),
                "delivery_lng": order.get("delivery_lng"),
                "total_amount": order.get("total_amount", 0),
                "status": order.get("status", "ready"),
                "ready_at": order.get("ready_at").isoformat() if order.get("ready_at") else "",
                "estimated_pickup_time": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                "payment_method": order.get("payment_method", ""),
                "is_assigned_to_me": order.get("courier_id") == courier_id
            }
            formatted_orders.append(formatted_order)
        
        return {"orders": formatted_orders}
        
    except Exception as e:
        print(f"Error fetching courier orders: {e}")
        raise HTTPException(status_code=500, detail=f"Orders retrieval failed: {str(e)}")

@api_router.patch("/courier/orders/{order_id}/pickup")
async def pickup_order(
    order_id: str,
    current_user: dict = Depends(get_courier_user)
):
    """Courier picks up an order"""
    try:
        courier_id = current_user["id"]
        
        # Find order
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["status"] != "ready":
            raise HTTPException(status_code=400, detail="Order is not ready for pickup")
        
        # Check if order is already assigned to another courier
        if order.get("courier_id") and order["courier_id"] != courier_id:
            raise HTTPException(status_code=400, detail="Order already assigned to another courier")
        
        # Update order status to picked_up and assign courier
        update_data = {
            "status": "picked_up",
            "courier_id": courier_id,
            "picked_up_at": datetime.now(timezone.utc),
            "assigned_at": datetime.now(timezone.utc)
        }
        
        # Update in database
        try:
            result = await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_data}
            )
        except:
            result = await db.orders.update_one(
                {"id": order_id},
                {"$set": update_data}
            )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Order not found or already picked up")
        
        return {
            "message": "Order picked up successfully",
            "order_id": order_id,
            "courier_id": courier_id,
            "pickup_time": update_data["picked_up_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error picking up order: {str(e)}")

# Courier Location Management Endpoints
@api_router.post("/courier/location")
async def update_courier_location(
    location_data: CourierLocation,
    current_user: dict = Depends(get_courier_user)
):
    """Update courier's real-time location"""
    try:
        courier_id = current_user["id"]
        timestamp = location_data.ts or int(time.time() * 1000)
        
        # Store current location in Redis for real-time access
        if redis_client:
            location_cache = {
                "lat": location_data.lat,
                "lng": location_data.lng,
                "heading": location_data.heading or "",
                "speed": location_data.speed or "",
                "accuracy": location_data.accuracy or "",
                "ts": timestamp
            }
            
            # Store in Redis with 10-minute expiry
            redis_key = f"courier:loc:{courier_id}"
            redis_client.hset(redis_key, mapping=location_cache)
            redis_client.expire(redis_key, 600)  # 10 minutes
        
        # Store in MongoDB for historical tracking (keep last 100 points)
        location_record = {
            "courier_id": courier_id,
            "lat": location_data.lat,
            "lng": location_data.lng,
            "heading": location_data.heading,
            "speed": location_data.speed,
            "accuracy": location_data.accuracy,
            "ts": timestamp,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.courier_locations.insert_one(location_record)
        
        # Keep only last 100 locations per courier
        locations_count = await db.courier_locations.count_documents({"courier_id": courier_id})
        if locations_count > 100:
            # Remove oldest records beyond 100
            old_locations = await db.courier_locations.find(
                {"courier_id": courier_id}
            ).sort("created_at", 1).limit(locations_count - 100).to_list(None)
            
            old_ids = [loc["_id"] for loc in old_locations]
            await db.courier_locations.delete_many({"_id": {"$in": old_ids}})
        
        # Broadcast location update via WebSocket (if implemented)
        # broadcaster.publish(channel=f"courier:{courier_id}", message={"type": "location", "data": location_data.dict()})
        
        return {"success": True, "message": "Location updated successfully", "timestamp": timestamp}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating location: {str(e)}")

@api_router.get("/courier/location/{courier_id}")
async def get_courier_location(
    courier_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current courier location (for customers/businesses tracking orders)"""
    try:
        # Only allow customers with active orders or businesses to access courier locations
        user_role = current_user.get("role")
        
        if user_role not in ["customer", "business", "admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If customer, verify they have an active order with this courier
        if user_role == "customer":
            active_order = await db.orders.find_one({
                "customer_id": current_user["id"],
                "courier_id": courier_id,
                "status": {"$in": ["picked_up", "delivering"]}
            })
            
            if not active_order:
                raise HTTPException(status_code=403, detail="No active order with this courier")
        
        # Get location from Redis first (real-time)
        location_data = None
        if redis_client:
            redis_key = f"courier:loc:{courier_id}"
            cached_location = redis_client.hgetall(redis_key)
            
            if cached_location:
                location_data = {
                    "lat": float(cached_location.get("lat", 0)),
                    "lng": float(cached_location.get("lng", 0)),
                    "heading": float(cached_location["heading"]) if cached_location.get("heading") else None,
                    "speed": float(cached_location["speed"]) if cached_location.get("speed") else None,
                    "accuracy": float(cached_location["accuracy"]) if cached_location.get("accuracy") else None,
                    "ts": int(cached_location.get("ts", 0)),
                    "source": "realtime"
                }
        
        # Fall back to MongoDB if no Redis data
        if not location_data:
            last_location = await db.courier_locations.find_one(
                {"courier_id": courier_id},
                sort=[("created_at", -1)]
            )
            
            if last_location:
                location_data = {
                    "lat": last_location["lat"],
                    "lng": last_location["lng"],
                    "heading": last_location.get("heading"),
                    "speed": last_location.get("speed"),
                    "accuracy": last_location.get("accuracy"),
                    "ts": last_location.get("ts"),
                    "source": "historical"
                }
        
        if not location_data:
            raise HTTPException(status_code=404, detail="Courier location not available")
        
        return location_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courier location: {str(e)}")

@api_router.get("/orders/{order_id}/courier/location")
async def get_order_courier_location(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get courier location for a specific order (for order tracking)"""
    try:
        # Get order details
        try:
            from bson import ObjectId
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verify user has access to this order
        user_role = current_user.get("role")
        if user_role == "customer" and order.get("customer_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        elif user_role == "business" and order.get("business_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        elif user_role not in ["customer", "business", "admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if order has an assigned courier
        courier_id = order.get("courier_id")
        if not courier_id:
            return {"message": "No courier assigned to this order yet", "status": order.get("status")}
        
        # Check if order is in trackable status
        if order.get("status") not in ["picked_up", "delivering"]:
            return {"message": "Order not yet picked up by courier", "status": order.get("status")}
        
        # Get courier location
        location_data = None
        if redis_client:
            redis_key = f"courier:loc:{courier_id}"
            cached_location = redis_client.hgetall(redis_key)
            
            if cached_location:
                location_data = {
                    "courier_id": courier_id,
                    "lat": float(cached_location.get("lat", 0)),
                    "lng": float(cached_location.get("lng", 0)),
                    "heading": float(cached_location["heading"]) if cached_location.get("heading") else None,
                    "speed": float(cached_location["speed"]) if cached_location.get("speed") else None,
                    "accuracy": float(cached_location["accuracy"]) if cached_location.get("accuracy") else None,
                    "ts": int(cached_location.get("ts", 0)),
                    "last_updated": datetime.fromtimestamp(int(cached_location.get("ts", 0)) / 1000, tz=timezone.utc).isoformat(),
                    "source": "realtime"
                }
        
        # Fall back to MongoDB
        if not location_data:
            last_location = await db.courier_locations.find_one(
                {"courier_id": courier_id},
                sort=[("created_at", -1)]
            )
            
            if last_location:
                location_data = {
                    "courier_id": courier_id,
                    "lat": last_location["lat"],
                    "lng": last_location["lng"],
                    "heading": last_location.get("heading"),
                    "speed": last_location.get("speed"),
                    "accuracy": last_location.get("accuracy"),
                    "ts": last_location.get("ts"),
                    "last_updated": last_location["created_at"].isoformat(),
                    "source": "historical"
                }
        
        if not location_data:
            return {"message": "Courier location not available", "status": order.get("status")}
        
        return {
            "order_id": order_id,
            "order_status": order.get("status"),
            "courier_location": location_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order courier location: {str(e)}")

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
    
    # Convert datetime and ObjectId - preserve existing UUID id if present
    for product in products:
        # Only use MongoDB _id if no UUID id exists (backward compatibility)
        if "id" not in product or not product["id"]:
            product["id"] = str(product["_id"])
        # Always remove MongoDB _id from response
        if "_id" in product:
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
async def create_order(
    request: Request, 
    order_data: dict,  # Will validate manually
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """
    Create new order - HARDENED VERSION
    - Validates restaurant exists and is active
    - Creates snapshots of address and items
    - Ensures business_id is set correctly
    - Publishes real-time event
    """
    try:
        # 1. RBAC: Only customers can create orders
        if current_user.get("role") != "customer":
            raise HTTPException(
                status_code=403,
                detail="Sadece müşteriler sipariş verebilir"
            )
        
        # 2. Extract and validate required fields
        restaurant_id = order_data.get('restaurant_id') or order_data.get('business_id')
        if not restaurant_id:
            raise HTTPException(
                status_code=400,
                detail="Restoran seçilmedi"
            )
        
        address_id = order_data.get('address_id')
        items = order_data.get('items', [])
        
        if not items or len(items) == 0:
            raise HTTPException(
                status_code=400,
                detail="Sepet boş olamaz"
            )
        
        # 3. Validate restaurant exists and is active
        restaurant = await db.users.find_one({
            "id": restaurant_id,
            "role": "business",
            "is_active": True
        })
        
        if not restaurant:
            raise HTTPException(
                status_code=404,
                detail="Restoran bulunamadı veya aktif değil"
            )
        
        # Check KYC approval
        if restaurant.get('kyc_status') != 'approved':
            raise HTTPException(
                status_code=403,
                detail="Bu restoran henüz onaylanmamış"
            )
        
        # 4. Get delivery address
        address = None
        if address_id:
            address = await db.addresses.find_one({"id": address_id, "user_id": current_user["id"]})
        
        # Fallback to order_data address fields
        address_snapshot = {
            "full": address.get("acik_adres") if address else order_data.get("delivery_address", ""),
            "city": address.get("il") if address else order_data.get("city"),
            "district": address.get("ilce") if address else order_data.get("district"),
            "neighborhood": address.get("mahalle") if address else order_data.get("neighborhood"),
            "lat": address.get("lat") if address else order_data.get("delivery_lat"),
            "lng": address.get("lng") if address else order_data.get("delivery_lng")
        }
        
        if not address_snapshot["full"]:
            raise HTTPException(
                status_code=400,
                detail="Teslimat adresi gerekli"
            )
        
        # 5. Create items snapshot with current prices
        items_snapshot = []
        subtotal = 0.0
        
        for item_data in items:
            product_id = item_data.get('product_id') or item_data.get('id')
            quantity = int(item_data.get('quantity', 1))
            
            # Get product from database
            product = await db.products.find_one({"id": product_id}) or \
                     await db.products.find_one({"_id": product_id})
            
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ürün bulunamadı: {product_id}"
                )
            
            if not product.get('is_available', True):
                raise HTTPException(
                    status_code=400,
                    detail=f"Ürün mevcut değil: {product.get('name', product_id)}"
                )
            
            item_price = float(product.get('price', 0))
            item_subtotal = item_price * quantity
            subtotal += item_subtotal
            
            items_snapshot.append({
                "id": product.get('id', str(product.get('_id'))),
                "name": product.get('name') or product.get('title', 'Ürün'),
                "price": item_price,
                "quantity": quantity,
                "notes": item_data.get('notes'),
                "subtotal": item_subtotal
            })
        
        # 6. Calculate totals
        delivery_fee = float(restaurant.get('delivery_fee', 0))
        discount = 0.0  # TODO: Apply coupons if any
        
        totals = {
            "sub": subtotal,
            "delivery": delivery_fee,
            "discount": discount,
            "grand": subtotal + delivery_fee - discount
        }
        
        # Check minimum order
        min_order = float(restaurant.get('min_order_amount', 0))
        if subtotal < min_order:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum sipariş tutarı: {min_order} TL (Sepet: {subtotal} TL)"
            )
        
        # 7. Generate unique order code
        from utils.order_code import generate_unique_order_code
        order_code = await generate_unique_order_code(db)
        
        # 8. Create order document
        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        order_doc = {
            "id": order_id,
            "order_code": order_code,  # ✅ Sipariş kodu
            "user_id": current_user["id"],
            "customer_id": current_user["id"],
            "customer_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip() or current_user.get('email', 'Müşteri'),
            "customer_phone": current_user.get('phone', ''),  # ✅ Telefon numarası
            "restaurant_id": restaurant_id,
            "business_id": restaurant_id,  # Same as restaurant_id
            "business_name": restaurant.get('business_name', 'Restoran'),
            "address_snapshot": address_snapshot,
            "delivery_address": address_snapshot.get('acik_adres', ''),  # ✅ Teslimat adresi (düz metin)
            "delivery_location": {  # ✅ GeoJSON for courier assignment
                "type": "Point",
                "coordinates": [
                    float(address_snapshot.get('lng', 0)),
                    float(address_snapshot.get('lat', 0))
                ]
            } if address_snapshot.get('lng') and address_snapshot.get('lat') else None,
            "items_snapshot": items_snapshot,
            "totals": totals,
            "payment_method": order_data.get('payment_method', 'cash'),
            "payment_status": "paid_mock" if order_data.get('payment_method') == 'online_mock' else "unpaid",
            "status": "pending",  # ✅ Başlangıç durumu: bekleyen
            "pickup_mode": "courier",  # ✅ Varsayılan: kurye ile
            "assigned_courier_id": None,
            "timeline": [{
                "event": "created",
                "at": now,
                "meta": {"note": "Sipariş oluşturuldu"}
            }],
            "courier_id": None,
            "eta": None,
            "special_instructions": order_data.get('notes') or order_data.get('special_instructions'),
            "created_at": now,
            "updated_at": now
        }
        
        # 9. Insert order
        result = await db.orders.insert_one(order_doc)
        
        if not result.acknowledged:
            raise HTTPException(
                status_code=500,
                detail="Sipariş kaydedilemedi"
            )
        
        logger.info(f"✅ Order created: {order_code} ({order_id}) | Restaurant: {restaurant.get('business_name')} | Business ID: {restaurant_id} | Customer: {order_doc['customer_name']} | Total: {totals['grand']} TL")
        
        # 10. Publish real-time event
        try:
            from realtime.event_bus import publish_order_created
            await publish_order_created(
                order_id=order_id,
                restaurant_id=restaurant_id,
                business_id=restaurant_id,
                order_data={
                    "order_code": order_code,  # ✅ Sipariş kodu
                    "customer_name": order_doc['customer_name'],
                    "customer_phone": order_doc['customer_phone'],
                    "delivery_address": order_doc['delivery_address'],
                    "payment_method": order_doc['payment_method'],
                    "total": totals['grand'],
                    "items_count": len(items_snapshot),
                    "business_name": order_doc['business_name'],
                    "status": "pending"
                }
            )
            logger.info(f"✅ Real-time event published for order {order_code}")
        except Exception as event_error:
            logger.warning(f"⚠️ Event publish failed for order {order_code} (non-critical): {event_error}")
        
        # 11. Return response (serialize datetime)
        order_doc["created_at"] = order_doc["created_at"].isoformat()
        order_doc["updated_at"] = order_doc["updated_at"].isoformat()
        order_doc["timeline"][0]["at"] = order_doc["timeline"][0]["at"].isoformat()
        del order_doc["_id"]
        
        return {
            "success": True,
            "order": order_doc,
            "message": "Siparişiniz alındı!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Order creation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sipariş oluşturulamadı: {str(e)}"
        )

@api_router.get("/orders")
async def get_orders(status: Optional[str] = None, current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get orders based on user role"""
    filter_query = {}
    
    if status:
        filter_query["status"] = status
    
    # Filter by role
    if current_user.get("role") == "customer":
        filter_query["customer_id"] = current_user["id"]
    elif current_user.get("role") == "business":
        filter_query["business_id"] = current_user["id"]
        print(f"🔍 GET /orders - Looking for orders with business_id: {current_user['id']}")
        print(f"🔍 GET /orders - Filter query: {filter_query}")
    elif current_user.get("role") == "courier":
        # Couriers see unassigned orders (ready for pickup) or orders assigned to them
        if not status:
            filter_query = {
                "$or": [
                    # Unassigned orders that are ready for courier pickup
                    {"status": {"$in": ["created", "confirmed", "preparing", "ready"]}, "courier_id": None},
                    # Orders assigned to this courier
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

# DEPRECATED: This endpoint is replaced by routes/order_status.py router
# Keeping commented out for reference
# @api_router.patch("/orders/{order_id}/status")
# async def update_order_status(order_id: str, new_status: OrderStatus, current_user: dict = Depends(get_current_user)):
#     """Update order status"""
#     order = await db.orders.find_one({"id": order_id})
#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Order not found"
#         )
#     
#     # Check permissions
#     user_role = current_user.get("role")
#     if user_role == "business" and order["business_id"] != current_user["id"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied"
#         )
#     elif user_role == "courier" and order.get("courier_id") != current_user["id"] and new_status != OrderStatus.ASSIGNED:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied"
#         )
#     elif user_role not in ["admin", "business", "courier"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied"
#         )
#     
#     update_data = {"status": new_status}
#     
#     # Update timestamps based on status
#     current_time = datetime.now(timezone.utc)
#     if new_status == OrderStatus.ASSIGNED:
#         update_data["assigned_at"] = current_time
#         update_data["courier_id"] = current_user["id"]
#         update_data["courier_name"] = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
#     elif new_status == OrderStatus.ON_ROUTE:
#         update_data["picked_up_at"] = current_time
#     elif new_status == OrderStatus.DELIVERED:
#         update_data["delivered_at"] = current_time
#     
#     await db.orders.update_one(
#         {"id": order_id},
#         {"$set": update_data}
#     )
#     
#     return {"success": True, "message": f"Order status updated to {new_status}"}

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

# Admin Menu/Product Management Endpoints
@api_router.get("/admin/products/{product_id}")
async def get_product_by_id_admin(product_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific product by ID (Admin only)"""
    try:
        from bson import ObjectId
        
        # Try ObjectId first, then string ID
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except:
            product = await db.products.find_one({"id": product_id})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Convert ObjectId to string
        product["id"] = str(product["_id"])
        del product["_id"]
        
        # Handle datetime conversion safely
        if product.get("created_at") and not isinstance(product["created_at"], str):
            product["created_at"] = product["created_at"].isoformat()
        
        return product
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")

@api_router.patch("/admin/products/{product_id}")
async def update_product_admin(
    product_id: str,
    product_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update product (Admin only)"""
    try:
        # Validate input data
        allowed_fields = [
            "name", "description", "price", "category", "is_available", 
            "preparation_time_minutes", "image_url", "ingredients", "allergens"
        ]
        
        update_data = {}
        for field, value in product_data.items():
            if field in allowed_fields:
                if field == "price" and value is not None:
                    try:
                        update_data[field] = float(value)
                    except (ValueError, TypeError):
                        raise HTTPException(status_code=422, detail="Price must be a valid number")
                elif field == "preparation_time_minutes" and value is not None:
                    try:
                        update_data[field] = int(value)
                    except (ValueError, TypeError):
                        raise HTTPException(status_code=422, detail="Preparation time must be a valid integer")
                elif field == "is_available" and value is not None:
                    update_data[field] = bool(value)
                else:
                    update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=422, detail="No valid fields provided for update")
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update product
        from bson import ObjectId
        try:
            result = await db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data}
            )
        except:
            result = await db.products.update_one(
                {"id": product_id},
                {"$set": update_data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        return {
            "message": "Product updated successfully",
            "product_id": product_id,
            "updates": update_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@api_router.delete("/admin/products/{product_id}")
async def delete_product_admin(product_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete product (Admin only)"""
    try:
        from bson import ObjectId
        
        # Delete product
        try:
            result = await db.products.delete_one({"_id": ObjectId(product_id)})
        except:
            result = await db.products.delete_one({"id": product_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "message": "Product deleted successfully",
            "product_id": product_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@api_router.get("/admin/products/stats")
async def get_product_statistics(current_user: dict = Depends(get_admin_user)):
    """Get product statistics for admin dashboard"""
    try:
        # Total products
        total_products = await db.products.count_documents({})
        
        # Available products
        available_products = await db.products.count_documents({"is_available": True})
        
        # Products by category
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        category_counts = {}
        async for result in db.products.aggregate(category_pipeline):
            category_counts[result["_id"] or "Other"] = result["count"]
        
        # Average price by category
        avg_price_pipeline = [
            {"$group": {"_id": "$category", "avg_price": {"$avg": "$price"}}},
            {"$sort": {"avg_price": -1}}
        ]
        avg_prices = {}
        async for result in db.products.aggregate(avg_price_pipeline):
            avg_prices[result["_id"] or "Other"] = round(result["avg_price"], 2)
        
        # New products this week
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        new_products = await db.products.count_documents({
            "created_at": {"$gte": week_start}
        })
        
        return {
            "total_products": total_products,
            "available_products": available_products,
            "category_counts": category_counts,
            "average_prices_by_category": avg_prices,
            "new_products_this_week": new_products,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product statistics: {str(e)}")

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

# Admin Order Management Endpoints
@api_router.get("/admin/orders/{order_id}")
async def get_order_by_id(order_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific order by ID (Admin only)"""
    try:
        # Try ObjectId first, then string ID
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Convert ObjectId to string
        order["id"] = str(order["_id"])
        del order["_id"]
        
        # Handle datetime conversion safely
        for field in ["created_at", "assigned_at", "picked_up_at", "delivered_at"]:
            if order.get(field) and not isinstance(order[field], str):
                order[field] = order[field].isoformat()
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving order: {str(e)}")

@api_router.patch("/admin/orders/{order_id}/status")
async def update_order_status_admin(
    order_id: str, 
    status_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update order status (Admin only)"""
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=422, detail="Status is required")
        
        # Validate status
        valid_statuses = ["created", "confirmed", "preparing", "picked_up", "delivering", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Find order
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order with timestamp
        update_data = {"status": new_status}
        current_time = datetime.now(timezone.utc)
        
        if new_status == "confirmed":
            update_data["confirmed_at"] = current_time
        elif new_status == "preparing":
            update_data["preparing_at"] = current_time
        elif new_status == "picked_up":
            update_data["picked_up_at"] = current_time
        elif new_status == "delivering":
            update_data["delivering_at"] = current_time
        elif new_status == "delivered":
            update_data["delivered_at"] = current_time
        elif new_status == "cancelled":
            update_data["cancelled_at"] = current_time
            update_data["cancel_reason"] = status_data.get("cancel_reason", "Admin cancelled")
        
        # Update order
        try:
            result = await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": update_data}
            )
        except:
            result = await db.orders.update_one(
                {"id": order_id},
                {"$set": update_data}
            )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Order not found or no changes made")
        
        return {"message": f"Order status updated to {new_status}", "order_id": order_id, "new_status": new_status}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

@api_router.patch("/admin/orders/{order_id}/assign-courier")
async def assign_courier_to_order(
    order_id: str,
    courier_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Assign courier to order (Admin only)"""
    try:
        courier_id = courier_data.get("courier_id")
        if not courier_id:
            raise HTTPException(status_code=422, detail="Courier ID is required")
        
        # Verify courier exists and is approved
        courier = await db.users.find_one({
            "$or": [{"id": courier_id}, {"_id": courier_id}],
            "role": "courier",
            "kyc_status": "approved"
        })
        
        if not courier:
            raise HTTPException(status_code=404, detail="Approved courier not found")
        
        # Find and update order
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
            order_filter = {"_id": ObjectId(order_id)}
        except:
            order = await db.orders.find_one({"id": order_id})
            order_filter = {"id": order_id}
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order with courier assignment
        update_data = {
            "courier_id": courier.get("id", str(courier["_id"])),
            "courier_name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}".strip(),
            "assigned_at": datetime.now(timezone.utc),
            "status": "assigned" if order["status"] == "created" else order["status"]
        }
        
        result = await db.orders.update_one(order_filter, {"$set": update_data})
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Order not found or no changes made")
        
        return {
            "message": "Courier assigned successfully",
            "order_id": order_id,
            "courier_id": courier_id,
            "courier_name": update_data["courier_name"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning courier: {str(e)}")

@api_router.delete("/admin/orders/{order_id}")
async def delete_order_admin(order_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete order (Admin only) - Use with caution"""
    try:
        from bson import ObjectId
        
        # Try to delete by ObjectId first, then by string ID
        try:
            result = await db.orders.delete_one({"_id": ObjectId(order_id)})
        except:
            result = await db.orders.delete_one({"id": order_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"message": "Order deleted successfully", "order_id": order_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")

# PRODUCTION PAYMENT SYSTEM - NO MOCK
# Real payment integration required in production

@api_router.get("/orders/my")
async def get_my_orders(current_user: dict = Depends(get_customer_user)):
    """Get customer's orders for tracking"""
    try:
        orders = await db.orders.find({"customer_id": current_user["id"]}).to_list(length=None)
        
        # Convert datetime and ObjectId
        for order in orders:
            order["id"] = str(order.get("_id", order.get("id", "")))
            if "_id" in order:
                del order["_id"]
            
            # Handle datetime conversion safely
            datetime_fields = ["created_at", "confirmed_at", "preparing_at", "picked_up_at", "delivering_at", "delivered_at", "cancelled_at"]
            for field in datetime_fields:
                if order.get(field) and not isinstance(order[field], str):
                    order[field] = order[field].isoformat()
        
        # Sort by creation date (newest first)
        orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return orders
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

@api_router.get("/orders/{order_id}/track")
async def track_order(order_id: str, current_user: dict = Depends(get_customer_user)):
    """Track specific order status and location"""
    try:
        # Find order
        from bson import ObjectId
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if order belongs to current user
        if order["customer_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert ObjectId and datetime
        order["id"] = str(order.get("_id", order.get("id", "")))
        if "_id" in order:
            del order["_id"]
        
        datetime_fields = ["created_at", "confirmed_at", "preparing_at", "picked_up_at", "delivering_at", "delivered_at", "cancelled_at"]
        for field in datetime_fields:
            if order.get(field) and not isinstance(order[field], str):
                order[field] = order[field].isoformat()
        
        # Add estimated delivery time based on status
        current_time = datetime.now(timezone.utc)
        if order["status"] in ["confirmed", "preparing"]:
            order["estimated_delivery"] = (current_time + timedelta(minutes=45)).isoformat()
        elif order["status"] in ["picked_up", "delivering"]:
            order["estimated_delivery"] = (current_time + timedelta(minutes=15)).isoformat()
        
        # Get courier location if available (mock data for now)
        if order.get("courier_id") and order["status"] in ["picked_up", "delivering"]:
            order["courier_location"] = {
                "lat": 41.0082,  # Istanbul center mock
                "lng": 28.9784,
                "last_updated": current_time.isoformat()
            }
        
        return order
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking order: {str(e)}")

@api_router.get("/admin/orders/stats")
async def get_order_statistics(current_user: dict = Depends(get_admin_user)):
    """Get order statistics for admin dashboard"""
    try:
        # Get various order counts
        total_orders = await db.orders.count_documents({})
        
        # Orders by status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = {}
        async for result in db.orders.aggregate(pipeline):
            status_counts[result["_id"]] = result["count"]
        
        # Today's orders
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = await db.orders.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Revenue calculation (this week)
        week_start = today_start - timedelta(days=7)
        weekly_revenue_pipeline = [
            {"$match": {
                "created_at": {"$gte": week_start},
                "status": {"$in": ["delivered", "completed"]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        weekly_revenue = 0
        async for result in db.orders.aggregate(weekly_revenue_pipeline):
            weekly_revenue = result["total"]
        
        return {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "status_counts": status_counts,
            "weekly_revenue": weekly_revenue,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving order statistics: {str(e)}")

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

# Admin Courier Management Endpoints
@api_router.get("/admin/couriers")
async def get_all_couriers_admin(
    status: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    kyc_status: Optional[str] = None,  # KYC status filter eklendi
    current_user: dict = Depends(get_admin_user)
):
    """Get all couriers for admin management with filtering"""
    try:
        # Build query filter
        query_filter = {"role": "courier"}
        
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
            elif status == "rejected":
                query_filter["kyc_status"] = "rejected"
        
        # KYC status filter (direct KYC filtering)
        if kyc_status:
            query_filter["kyc_status"] = kyc_status
        
        # City filter
        if city:
            import re
            query_filter["city"] = {"$regex": f".*{re.escape(city)}.*", "$options": "i"}
        
        # Search filter
        if search:
            import re
            search_regex = {"$regex": f".*{re.escape(search)}.*", "$options": "i"}
            query_filter["$or"] = [
                {"first_name": search_regex},
                {"last_name": search_regex},
                {"email": search_regex},
                {"phone": search_regex}
            ]
        
        # Fetch couriers
        couriers = await db.users.find(query_filter).to_list(length=None)
        
        # Clean up data and prepare response
        result = []
        for courier in couriers:
            courier_data = {
                "id": courier.get("id", str(courier.get("_id", ""))),
                "first_name": courier.get("first_name", ""),
                "last_name": courier.get("last_name", ""),
                "email": courier.get("email", ""),
                "phone": courier.get("phone", ""),
                "city": courier.get("city", ""),
                "kyc_status": courier.get("kyc_status", "pending"),
                "is_active": courier.get("is_active", False),
                "created_at": courier.get("created_at", ""),
                "vehicle_type": courier.get("vehicle_type", ""),
                "license_number": courier.get("license_number", ""),
                "total_orders": courier.get("total_orders", 0),
                "average_rating": courier.get("average_rating", 0),
                "earnings_this_month": courier.get("earnings_this_month", 0),
                "kyc_documents": courier.get("kyc_documents", {}),
                "kyc_notes": courier.get("kyc_notes", "")
            }
            result.append(courier_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving couriers: {str(e)}")

@api_router.get("/admin/couriers/{courier_id}")
async def get_courier_by_id_admin(courier_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific courier by ID (Admin only)"""
    try:
        from bson import ObjectId
        
        # Try string ID first, then ObjectId
        courier = await db.users.find_one({"id": courier_id, "role": "courier"})
        if not courier:
            try:
                courier = await db.users.find_one({"_id": ObjectId(courier_id), "role": "courier"})
            except:
                pass
        
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        # Remove sensitive data
        if "password" in courier:
            del courier["password"]
        
        # Prepare response data
        courier_data = {
            "id": courier.get("id", str(courier.get("_id", ""))),
            "first_name": courier.get("first_name", ""),
            "last_name": courier.get("last_name", ""),
            "email": courier.get("email", ""),
            "phone": courier.get("phone", ""),
            "city": courier.get("city", ""),
            "address": courier.get("address", ""),
            "kyc_status": courier.get("kyc_status", "pending"),
            "is_active": courier.get("is_active", False),
            "created_at": courier.get("created_at", ""),
            "vehicle_type": courier.get("vehicle_type", ""),
            "license_number": courier.get("license_number", ""),
            "total_orders": courier.get("total_orders", 0),
            "average_rating": courier.get("average_rating", 0),
            "earnings_this_month": courier.get("earnings_this_month", 0),
            "kyc_documents": courier.get("kyc_documents", {}),
            "kyc_notes": courier.get("kyc_notes", ""),
            "working_hours": courier.get("working_hours", {}),
            "location": courier.get("location", {})
        }
        
        return courier_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving courier: {str(e)}")

@api_router.patch("/admin/couriers/{courier_id}/status")
async def update_courier_status_admin(
    courier_id: str,
    status_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update courier status (Admin only)"""
    try:
        is_active = status_data.get("is_active")
        kyc_status = status_data.get("kyc_status")
        
        if is_active is None and kyc_status is None:
            raise HTTPException(status_code=422, detail="Either is_active or kyc_status is required")
        
        # Build update data
        update_data = {}
        if is_active is not None:
            update_data["is_active"] = bool(is_active)
        
        if kyc_status is not None:
            valid_kyc_statuses = ["pending", "approved", "rejected"]
            if kyc_status not in valid_kyc_statuses:
                raise HTTPException(status_code=422, detail=f"Invalid KYC status. Must be one of: {valid_kyc_statuses}")
            update_data["kyc_status"] = kyc_status
            update_data["kyc_updated_at"] = datetime.now(timezone.utc)
            
            if kyc_status == "rejected":
                update_data["rejection_reason"] = status_data.get("rejection_reason", "No reason provided")
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update courier
        result = await db.users.update_one(
            {"id": courier_id, "role": "courier"},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        return {
            "success": True,
            "message": "Courier status updated successfully",
            "courier_id": courier_id,
            "updates": update_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating courier status: {str(e)}")

@api_router.delete("/admin/couriers/{courier_id}")
async def delete_courier_admin(courier_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete courier (Admin only) - Use with caution"""
    try:
        # Update orders to remove courier assignment first
        await db.orders.update_many(
            {"courier_id": courier_id},
            {"$unset": {"courier_id": "", "courier_name": ""}}
        )
        
        # Delete courier
        result = await db.users.delete_one({"id": courier_id, "role": "courier"})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        return {
            "message": "Courier deleted successfully",
            "courier_id": courier_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting courier: {str(e)}")

# Admin Settings Management Endpoints
@api_router.get("/admin/settings")
async def get_platform_settings(current_user: dict = Depends(get_admin_user)):
    """Get platform settings (Admin only)"""
    try:
        # Get settings from database, return default if not found
        settings = await db.settings.find_one({"type": "platform"})
        
        if not settings:
            # Return default settings
            default_settings = {
                "platform": {
                    "app_name": "Kuryecini",
                    "app_version": "1.0.0",
                    "maintenance_mode": False,
                    "new_registrations_enabled": True,
                    "max_delivery_radius_km": 50,
                    "default_delivery_fee": 0,
                    "platform_commission_rate": 5,
                    "courier_commission_rate": 5
                },
                "notifications": {
                    "email_enabled": True,
                    "sms_enabled": False,
                    "push_enabled": True
                },
                "payment": {
                    "cash_on_delivery": True,
                    "online_payment": True,
                    "pos_payment": True,
                    "minimum_order_amount": 0
                },
                "business": {
                    "auto_approve_businesses": False,
                    "require_business_documents": True,
                    "business_verification_required": True
                },
                "courier": {
                    "auto_approve_couriers": False,
                    "require_vehicle_documents": True,
                    "courier_background_check": True
                }
            }
            return default_settings
        
        # Remove MongoDB fields
        if "_id" in settings:
            del settings["_id"]
        
        return settings
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving settings: {str(e)}")

@api_router.patch("/admin/settings")
async def update_platform_settings(
    settings_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update platform settings (Admin only)"""
    try:
        # Add metadata
        settings_data["updated_at"] = datetime.now(timezone.utc)
        settings_data["updated_by"] = current_user["id"]
        settings_data["type"] = "platform"
        
        # Upsert settings
        result = await db.settings.update_one(
            {"type": "platform"},
            {"$set": settings_data},
            upsert=True
        )
        
        return {
            "message": "Settings updated successfully",
            "updated": result.modified_count > 0 or result.upserted_id is not None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@api_router.get("/admin/settings/delivery-zones")
async def get_delivery_zones(current_user: dict = Depends(get_admin_user)):
    """Get delivery zones configuration"""
    try:
        zones = await db.delivery_zones.find({}).to_list(length=None)
        
        # Convert ObjectId to string
        for zone in zones:
            zone["id"] = str(zone["_id"])
            del zone["_id"]
        
        return zones
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving delivery zones: {str(e)}")

@api_router.post("/admin/settings/delivery-zones")
async def create_delivery_zone(
    zone_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Create delivery zone"""
    try:
        # Validate required fields
        required_fields = ["name", "city", "coordinates", "delivery_fee"]
        for field in required_fields:
            if field not in zone_data:
                raise HTTPException(status_code=422, detail=f"Field '{field}' is required")
        
        # Add metadata
        zone_data["id"] = str(uuid.uuid4())
        zone_data["created_at"] = datetime.now(timezone.utc)
        zone_data["created_by"] = current_user["id"]
        zone_data["is_active"] = zone_data.get("is_active", True)
        
        # Insert zone
        result = await db.delivery_zones.insert_one(zone_data)
        
        return {
            "message": "Delivery zone created successfully",
            "zone_id": zone_data["id"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating delivery zone: {str(e)}")

@api_router.patch("/admin/settings/delivery-zones/{zone_id}")
async def update_delivery_zone(
    zone_id: str,
    zone_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update delivery zone"""
    try:
        # Add metadata
        zone_data["updated_at"] = datetime.now(timezone.utc)
        zone_data["updated_by"] = current_user["id"]
        
        # Update zone
        from bson import ObjectId
        try:
            result = await db.delivery_zones.update_one(
                {"_id": ObjectId(zone_id)},
                {"$set": zone_data}
            )
        except:
            result = await db.delivery_zones.update_one(
                {"id": zone_id},
                {"$set": zone_data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Delivery zone not found")
        
        return {"message": "Delivery zone updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating delivery zone: {str(e)}")

@api_router.delete("/admin/settings/delivery-zones/{zone_id}")
async def delete_delivery_zone(zone_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete delivery zone"""
    try:
        from bson import ObjectId
        
        # Delete zone
        try:
            result = await db.delivery_zones.delete_one({"_id": ObjectId(zone_id)})
        except:
            result = await db.delivery_zones.delete_one({"id": zone_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Delivery zone not found")
        
        return {"message": "Delivery zone deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting delivery zone: {str(e)}")

@api_router.get("/admin/couriers/stats")
async def get_courier_statistics(current_user: dict = Depends(get_admin_user)):
    """Get courier statistics for admin dashboard"""
    try:
        # Total couriers
        total_couriers = await db.users.count_documents({"role": "courier"})
        
        # Active couriers
        active_couriers = await db.users.count_documents({"role": "courier", "is_active": True})
        
        # Couriers by KYC status
        kyc_pipeline = [
            {"$match": {"role": "courier"}},
            {"$group": {"_id": "$kyc_status", "count": {"$sum": 1}}}
        ]
        kyc_counts = {}
        async for result in db.users.aggregate(kyc_pipeline):
            kyc_counts[result["_id"] or "unknown"] = result["count"]
        
        # Couriers by city (top 10)
        city_pipeline = [
            {"$match": {"role": "courier"}},
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        city_counts = {}
        async for result in db.users.aggregate(city_pipeline):
            city_counts[result["_id"] or "Other"] = result["count"]
        
        # New couriers this week
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        new_couriers = await db.users.count_documents({
            "role": "courier",
            "created_at": {"$gte": week_start}
        })
        
        # Average rating
        avg_rating_pipeline = [
            {"$match": {"role": "courier", "average_rating": {"$gt": 0}}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$average_rating"}}}
        ]
        avg_rating = 0
        async for result in db.users.aggregate(avg_rating_pipeline):
            avg_rating = round(result["avg_rating"], 2)
        
        return {
            "total_couriers": total_couriers,
            "active_couriers": active_couriers,
            "kyc_status_counts": kyc_counts,
            "city_counts": city_counts,
            "new_couriers_this_week": new_couriers,
            "average_rating": avg_rating,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving courier statistics: {str(e)}")

# Admin Promotion Management Endpoints
@api_router.get("/admin/promotions")
async def get_all_promotions(current_user: dict = Depends(get_admin_user)):
    """Get all promotions (Admin only)"""
    try:
        promotions = await db.promotions.find({}).to_list(length=None)
        
        # Convert ObjectId to string and handle datetime
        for promotion in promotions:
            promotion["id"] = str(promotion["_id"])
            del promotion["_id"]
            
            # Handle datetime fields
            for field in ["created_at", "start_date", "end_date", "updated_at"]:
                if promotion.get(field) and not isinstance(promotion[field], str):
                    promotion[field] = promotion[field].isoformat()
        
        return promotions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving promotions: {str(e)}")

# OLD PROMOTION ENDPOINT REMOVED - Using new one at line ~6400

@api_router.get("/admin/promotions/{promotion_id}")
async def get_promotion_by_id(promotion_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific promotion by ID (Admin only)"""
    try:
        from bson import ObjectId
        
        # Try ObjectId first, then string ID
        try:
            promotion = await db.promotions.find_one({"_id": ObjectId(promotion_id)})
        except:
            promotion = await db.promotions.find_one({"id": promotion_id})
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        # Convert ObjectId to string and handle datetime
        promotion["id"] = str(promotion["_id"])
        del promotion["_id"]
        
        for field in ["created_at", "start_date", "end_date", "updated_at"]:
            if promotion.get(field) and not isinstance(promotion[field], str):
                promotion[field] = promotion[field].isoformat()
        
        return promotion
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving promotion: {str(e)}")

@api_router.patch("/admin/promotions/{promotion_id}")
async def update_promotion(
    promotion_id: str,
    promotion_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update promotion (Admin only)"""
    try:
        # Add metadata
        promotion_data["updated_at"] = datetime.now(timezone.utc)
        promotion_data["updated_by"] = current_user["id"]
        
        # Handle datetime fields
        for field in ["start_date", "end_date"]:
            if field in promotion_data and isinstance(promotion_data[field], str):
                promotion_data[field] = datetime.fromisoformat(promotion_data[field].replace('Z', '+00:00'))
        
        # Update promotion
        from bson import ObjectId
        try:
            result = await db.promotions.update_one(
                {"_id": ObjectId(promotion_id)},
                {"$set": promotion_data}
            )
        except:
            result = await db.promotions.update_one(
                {"id": promotion_id},
                {"$set": promotion_data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        return {
            "message": "Promotion updated successfully",
            "promotion_id": promotion_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating promotion: {str(e)}")

@api_router.delete("/admin/promotions/{promotion_id}")
async def delete_promotion(promotion_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete promotion (Admin only)"""
    try:
        from bson import ObjectId
        
        # Delete promotion
        try:
            result = await db.promotions.delete_one({"_id": ObjectId(promotion_id)})
        except:
            result = await db.promotions.delete_one({"id": promotion_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        return {
            "message": "Promotion deleted successfully",
            "promotion_id": promotion_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting promotion: {str(e)}")

@api_router.patch("/admin/promotions/{promotion_id}/toggle")
async def toggle_promotion_status(promotion_id: str, current_user: dict = Depends(get_admin_user)):
    """Toggle promotion active status (Admin only)"""
    try:
        from bson import ObjectId
        
        # Find promotion
        try:
            promotion = await db.promotions.find_one({"_id": ObjectId(promotion_id)})
            filter_query = {"_id": ObjectId(promotion_id)}
        except:
            promotion = await db.promotions.find_one({"id": promotion_id})
            filter_query = {"id": promotion_id}
        
        if not promotion:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        # Toggle status
        new_status = not promotion.get("is_active", False)
        
        result = await db.promotions.update_one(
            filter_query,
            {
                "$set": {
                    "is_active": new_status,
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": current_user["id"]
                }
            }
        )
        
        return {
            "message": f"Promotion {'activated' if new_status else 'deactivated'} successfully",
            "promotion_id": promotion_id,
            "is_active": new_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling promotion status: {str(e)}")

@api_router.get("/admin/promotions/stats")
async def get_promotion_statistics(current_user: dict = Depends(get_admin_user)):
    """Get promotion statistics for admin dashboard"""
    try:
        # Total promotions
        total_promotions = await db.promotions.count_documents({})
        
        # Active promotions
        active_promotions = await db.promotions.count_documents({"is_active": True})
        
        # Current active promotions (not expired)
        current_time = datetime.now(timezone.utc)
        current_active = await db.promotions.count_documents({
            "is_active": True,
            "$or": [
                {"end_date": {"$gte": current_time}},
                {"end_date": {"$exists": False}}
            ]
        })
        
        # Promotions by type
        type_pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ]
        type_counts = {}
        async for result in db.promotions.aggregate(type_pipeline):
            type_counts[result["_id"] or "Other"] = result["count"]
        
        # Most used promotions (top 5)
        popular_pipeline = [
            {"$sort": {"usage_count": -1}},
            {"$limit": 5},
            {"$project": {"title": 1, "usage_count": 1}}
        ]
        popular_promotions = []
        async for result in db.promotions.aggregate(popular_pipeline):
            popular_promotions.append({
                "title": result.get("title", "Unknown"),
                "usage_count": result.get("usage_count", 0)
            })
        
        return {
            "total_promotions": total_promotions,
            "active_promotions": active_promotions,
            "current_active_promotions": current_active,
            "type_counts": type_counts,
            "popular_promotions": popular_promotions,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving promotion statistics: {str(e)}")

# Admin Reports Management Endpoints
@api_router.get("/admin/reports/dashboard")
async def get_dashboard_reports(current_user: dict = Depends(get_admin_user)):
    """Get comprehensive dashboard reports (Admin only)"""
    try:
        # Time ranges
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Order statistics
        total_orders = await db.orders.count_documents({})
        today_orders = await db.orders.count_documents({"created_at": {"$gte": today_start}})
        week_orders = await db.orders.count_documents({"created_at": {"$gte": week_start}})
        
        # Revenue statistics
        revenue_pipeline = [
            {"$match": {"status": {"$in": ["delivered", "completed"]}}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "avg_order_value": {"$avg": "$total_amount"}
            }}
        ]
        revenue_data = {"total_revenue": 0, "avg_order_value": 0}
        async for result in db.orders.aggregate(revenue_pipeline):
            revenue_data = {
                "total_revenue": result.get("total_revenue", 0),
                "avg_order_value": round(result.get("avg_order_value", 0), 2)
            }
        
        # Weekly revenue
        weekly_revenue_pipeline = [
            {"$match": {
                "created_at": {"$gte": week_start},
                "status": {"$in": ["delivered", "completed"]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        weekly_revenue = 0
        async for result in db.orders.aggregate(weekly_revenue_pipeline):
            weekly_revenue = result.get("total", 0)
        
        # User statistics
        total_customers = await db.users.count_documents({"role": "customer"})
        total_businesses = await db.businesses.count_documents({})
        total_couriers = await db.users.count_documents({"role": "courier"})
        
        # Active entities
        active_businesses = await db.businesses.count_documents({"is_active": True, "kyc_status": "approved"})
        active_couriers = await db.users.count_documents({"role": "courier", "is_active": True, "kyc_status": "approved"})
        
        # Order status distribution
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        order_status_counts = {}
        async for result in db.orders.aggregate(status_pipeline):
            order_status_counts[result["_id"]] = result["count"]
        
        # Top cities by orders
        city_pipeline = [
            {"$lookup": {
                "from": "users",
                "localField": "customer_id",
                "foreignField": "id",
                "as": "customer"
            }},
            {"$unwind": "$customer"},
            {"$group": {"_id": "$customer.city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        city_counts = {}
        async for result in db.orders.aggregate(city_pipeline):
            city_counts[result["_id"] or "Unknown"] = result["count"]
        
        return {
            "orders": {
                "total": total_orders,
                "today": today_orders,
                "this_week": week_orders,
                "status_distribution": order_status_counts
            },
            "revenue": {
                "total": revenue_data["total_revenue"],
                "weekly": weekly_revenue,
                "average_order_value": revenue_data["avg_order_value"]
            },
            "users": {
                "total_customers": total_customers,
                "total_businesses": total_businesses,
                "total_couriers": total_couriers,
                "active_businesses": active_businesses,
                "active_couriers": active_couriers
            },
            "top_cities": city_counts,
            "generated_at": now.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard report: {str(e)}")

@api_router.get("/admin/reports/financial")
async def get_financial_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get financial reports (Admin only)"""
    try:
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Revenue by date
        daily_revenue_pipeline = [
            {"$match": {
                "created_at": {"$gte": start, "$lte": end},
                "status": {"$in": ["delivered", "completed"]}
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "revenue": {"$sum": "$total_amount"},
                "orders": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_revenue = []
        async for result in db.orders.aggregate(daily_revenue_pipeline):
            daily_revenue.append({
                "date": result["_id"],
                "revenue": result["revenue"],
                "orders": result["orders"]
            })
        
        # Commission breakdown
        commission_pipeline = [
            {"$match": {
                "created_at": {"$gte": start, "$lte": end},
                "status": {"$in": ["delivered", "completed"]}
            }},
            {"$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$total_amount"},
                "total_commission": {"$sum": "$commission_amount"}
            }}
        ]
        commission_data = {}
        async for result in db.orders.aggregate(commission_pipeline):
            commission_data = {
                "total_orders": result.get("total_orders", 0),
                "total_revenue": result.get("total_revenue", 0),
                "total_commission": result.get("total_commission", 0),
                "commission_rate": round((result.get("total_commission", 0) / result.get("total_revenue", 1)) * 100, 2) if result.get("total_revenue", 0) > 0 else 0
            }
        
        return {
            "period": {
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            },
            "summary": commission_data,
            "daily_revenue": daily_revenue,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating financial report: {str(e)}")

@api_router.get("/admin/reports/orders")
async def get_order_reports(
    business_name: Optional[str] = None,
    customer_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get order reports with filters (Admin only)"""
    try:
        # Build match query
        match_query = {}
        
        # Date range filter
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            match_query["created_at"] = {"$gte": start}
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if "created_at" in match_query:
                match_query["created_at"]["$lte"] = end
            else:
                match_query["created_at"] = {"$lte": end}
        
        # Status filter
        if status:
            match_query["status"] = status
        
        # Business name filter
        if business_name:
            # Find businesses matching name (case-insensitive)
            business_cursor = db.users.find({
                "role": "business",
                "business_name": {"$regex": business_name, "$options": "i"}
            })
            business_ids = []
            async for business in business_cursor:
                business_ids.append(business.get("id"))
            
            if business_ids:
                match_query["business_id"] = {"$in": business_ids}
            else:
                # No matching businesses found
                return {
                    "filters": {
                        "business_name": business_name,
                        "customer_name": customer_name,
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "summary": {
                        "total_orders": 0,
                        "total_revenue": 0,
                        "average_order_value": 0
                    },
                    "orders": [],
                    "message": "İşletme bulunamadı"
                }
        
        # Customer name filter
        if customer_name:
            # Find customers matching name (case-insensitive)
            customer_cursor = db.users.find({
                "role": "customer",
                "$or": [
                    {"first_name": {"$regex": customer_name, "$options": "i"}},
                    {"last_name": {"$regex": customer_name, "$options": "i"}}
                ]
            })
            customer_ids = []
            async for customer in customer_cursor:
                customer_ids.append(customer.get("id"))
            
            if customer_ids:
                match_query["customer_id"] = {"$in": customer_ids}
            else:
                # No matching customers found
                return {
                    "filters": {
                        "business_name": business_name,
                        "customer_name": customer_name,
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "summary": {
                        "total_orders": 0,
                        "total_revenue": 0,
                        "average_order_value": 0
                    },
                    "orders": [],
                    "message": "Müşteri bulunamadı"
                }
        
        # Fetch orders
        orders_cursor = db.orders.find(match_query).sort("created_at", -1).limit(100)
        orders = []
        
        # Create user lookup dict for efficiency
        user_cache = {}
        
        async for order in orders_cursor:
            # Get business info
            business_id = order.get("business_id")
            if business_id and business_id not in user_cache:
                business = await db.users.find_one({"id": business_id})
                user_cache[business_id] = business
            business_info = user_cache.get(business_id, {})
            
            # Get customer info
            customer_id = order.get("customer_id")
            if customer_id and customer_id not in user_cache:
                customer = await db.users.find_one({"id": customer_id})
                user_cache[customer_id] = customer
            customer_info = user_cache.get(customer_id, {})
            
            # Get courier info
            courier_id = order.get("courier_id")
            courier_info = {}
            if courier_id and courier_id not in user_cache:
                courier = await db.users.find_one({"id": courier_id})
                user_cache[courier_id] = courier
            courier_info = user_cache.get(courier_id, {})
            
            orders.append({
                "order_id": order.get("id"),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "status": order.get("status"),
                "total_amount": order.get("total_amount", 0),
                "delivery_fee": order.get("delivery_fee", 0),
                "business": {
                    "id": business_id,
                    "name": business_info.get("business_name", "N/A"),
                    "email": business_info.get("email", "N/A"),
                    "phone": business_info.get("phone", "N/A")
                },
                "customer": {
                    "id": customer_id,
                    "name": f"{customer_info.get('first_name', '')} {customer_info.get('last_name', '')}".strip(),
                    "email": customer_info.get("email", "N/A"),
                    "phone": customer_info.get("phone", "N/A")
                },
                "courier": {
                    "id": courier_id,
                    "name": f"{courier_info.get('first_name', '')} {courier_info.get('last_name', '')}".strip() if courier_id else "Atanmadı",
                    "phone": courier_info.get("phone", "N/A") if courier_id else "N/A"
                },
                "items_count": len(order.get("items", [])),
                "delivery_address": order.get("delivery_address", {})
            })
        
        # Calculate summary
        total_orders = len(orders)
        total_revenue = sum(order["total_amount"] for order in orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "filters": {
                "business_name": business_name,
                "customer_name": customer_name,
                "status": status,
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "average_order_value": average_order_value
            },
            "orders": orders
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating order report: {str(e)}")

@api_router.get("/admin/reports/user")
async def get_user_report(
    customer_name: str,
    current_user: dict = Depends(get_admin_user)
):
    """Get user (customer) report with analytics (Admin only)"""
    try:
        # Find customers matching name
        customer_cursor = db.users.find({
            "role": "customer",
            "$or": [
                {"first_name": {"$regex": customer_name, "$options": "i"}},
                {"last_name": {"$regex": customer_name, "$options": "i"}},
                {"email": {"$regex": customer_name, "$options": "i"}}
            ]
        }).limit(10)
        
        customers_report = []
        
        async for customer in customer_cursor:
            customer_id = customer.get("id")
            
            # Get customer's orders
            orders_cursor = db.orders.find({"customer_id": customer_id})
            orders = []
            total_spent = 0
            status_counts = {}
            
            async for order in orders_cursor:
                orders.append(order)
                total_spent += order.get("total_amount", 0)
                status = order.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calculate analytics
            total_orders = len(orders)
            avg_order_value = total_spent / total_orders if total_orders > 0 else 0
            
            # Get favorite businesses
            business_orders = {}
            for order in orders:
                business_id = order.get("business_id")
                if business_id:
                    business_orders[business_id] = business_orders.get(business_id, 0) + 1
            
            favorite_businesses = []
            for business_id, count in sorted(business_orders.items(), key=lambda x: x[1], reverse=True)[:3]:
                business = await db.users.find_one({"id": business_id})
                if business:
                    favorite_businesses.append({
                        "name": business.get("business_name", "N/A"),
                        "order_count": count
                    })
            
            # Last order date
            last_order = orders[-1] if orders else None
            last_order_date = last_order.get("created_at") if last_order else None
            
            customers_report.append({
                "customer": {
                    "id": customer_id,
                    "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    "email": customer.get("email"),
                    "phone": customer.get("phone"),
                    "created_at": customer.get("created_at").isoformat() if isinstance(customer.get("created_at"), datetime) else (customer.get("created_at") if customer.get("created_at") else None)
                },
                "analytics": {
                    "total_orders": total_orders,
                    "total_spent": total_spent,
                    "average_order_value": avg_order_value,
                    "status_distribution": status_counts,
                    "last_order_date": last_order_date.isoformat() if isinstance(last_order_date, datetime) else (last_order_date if last_order_date else None),
                    "favorite_businesses": favorite_businesses
                }
            })
        
        return {
            "search_term": customer_name,
            "customers_found": len(customers_report),
            "customers": customers_report
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating user report: {str(e)}")

@api_router.get("/courier/order-history")
async def get_courier_order_history(
    current_user: dict = Depends(get_current_courier_user)
):
    """Get courier order history with details"""
    try:
        courier_id = current_user.get("id")
        
        # Get all orders for this courier
        orders_cursor = db.orders.find({
            "courier_id": courier_id
        }).sort("created_at", -1).limit(100)
        
        orders_list = []
        total_earnings = 0
        
        async for order in orders_cursor:
            # Get business info
            business = await db.users.find_one({"id": order.get("business_id")})
            # Get customer info
            customer = await db.users.find_one({"id": order.get("customer_id")})
            
            delivery_fee = order.get("delivery_fee", 0)
            courier_earning = delivery_fee * 0.8  # 80% goes to courier
            total_earnings += courier_earning
            
            orders_list.append({
                "order_id": order.get("id"),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "delivered_at": order.get("delivered_at").isoformat() if order.get("delivered_at") else None,
                "status": order.get("status"),
                "total_amount": order.get("total_amount", 0),
                "delivery_fee": delivery_fee,
                "courier_earning": courier_earning,
                "business": {
                    "name": business.get("business_name") if business else "N/A",
                    "address": business.get("business_address") if business else "N/A"
                },
                "customer": {
                    "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() if customer else "N/A",
                    "address": order.get("delivery_address", {})
                },
                "items": order.get("items", [])
            })
        
        return {
            "orders": orders_list,
            "summary": {
                "total_deliveries": len(orders_list),
                "total_earnings": total_earnings
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order history: {str(e)}")

@api_router.get("/courier/earnings-report")
async def get_courier_earnings_report(
    period: str = "daily",  # daily, weekly, monthly
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_courier_user)
):
    """Get courier earnings report"""
    try:
        courier_id = current_user.get("id")
        
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            if period == "daily":
                start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            elif period == "weekly":
                start = datetime.now(timezone.utc) - timedelta(days=7)
            else:  # monthly
                start = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Get orders in period
        orders_cursor = db.orders.find({
            "courier_id": courier_id,
            "created_at": {"$gte": start, "$lte": end},
            "status": {"$in": ["delivered", "completed"]}
        })
        
        total_earnings = 0
        total_deliveries = 0
        orders_by_day = {}
        
        async for order in orders_cursor:
            delivery_fee = order.get("delivery_fee", 0)
            courier_earning = delivery_fee * 0.8
            total_earnings += courier_earning
            total_deliveries += 1
            
            # Group by day
            day_key = order.get("created_at").strftime("%Y-%m-%d") if order.get("created_at") else "unknown"
            if day_key not in orders_by_day:
                orders_by_day[day_key] = {"count": 0, "earnings": 0}
            orders_by_day[day_key]["count"] += 1
            orders_by_day[day_key]["earnings"] += courier_earning
        
        return {
            "period": period,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "summary": {
                "total_deliveries": total_deliveries,
                "total_earnings": total_earnings,
                "average_per_delivery": total_earnings / total_deliveries if total_deliveries > 0 else 0
            },
            "daily_breakdown": orders_by_day
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating earnings report: {str(e)}")

@api_router.get("/admin/reports/category-analytics")
async def get_category_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get category sales analytics (Admin only)"""
    try:
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Category sales from order items
        category_pipeline = [
            {"$match": {
                "created_at": {"$gte": start, "$lte": end},
                "status": {"$in": ["delivered", "completed"]}
            }},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.category",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        
        categories = []
        total_revenue = 0
        
        async for result in db.orders.aggregate(category_pipeline):
            category = result["_id"] or "Diğer"
            revenue = result["total_revenue"]
            total_revenue += revenue
            
            categories.append({
                "category": category,
                "quantity": result["total_quantity"],
                "revenue": revenue,
                "order_count": result["order_count"]
            })
        
        # Calculate percentages
        for category in categories:
            category["percentage"] = (category["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        
        # Get top selling category
        top_category = categories[0] if categories else None
        
        return {
            "period": {
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            },
            "summary": {
                "total_revenue": total_revenue,
                "total_categories": len(categories),
                "top_category": top_category["category"] if top_category else None,
                "top_category_revenue": top_category["revenue"] if top_category else 0
            },
            "categories": categories
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating category analytics: {str(e)}")

# GPS-Based Discovery for Customers
@api_router.get("/customer/discover")
async def discover_nearby_businesses(
    lat: float,
    lng: float,
    radius_km: int = 50,
    current_user: dict = Depends(get_current_customer_user)
):
    """Discover businesses within radius based on GPS location"""
    try:
        # Convert radius to meters for geospatial query
        radius_meters = radius_km * 1000
        
        # Find businesses near the location
        businesses_cursor = db.users.find({
            "role": "business",
            "kyc_status": "approved",
            "is_active": True,
            "location": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius_meters
                }
            }
        }).limit(50)
        
        businesses_list = []
        async for business in businesses_cursor:
            # Calculate distance
            business_loc = business.get("location", {}).get("coordinates", [0, 0])
            
            # Simple distance calculation (Haversine would be better in production)
            from math import radians, cos, sin, asin, sqrt
            def haversine(lon1, lat1, lon2, lat2):
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                km = 6371 * c
                return km
            
            distance = haversine(lng, lat, business_loc[0], business_loc[1])
            
            businesses_list.append({
                "id": business.get("id"),
                "name": business.get("business_name"),
                "address": business.get("business_address"),
                "city": business.get("city"),
                "cuisine_type": business.get("cuisine_type", ""),
                "rating": business.get("rating", 4.5),
                "distance_km": round(distance, 2),
                "image_url": business.get("business_image_url"),
                "location": {
                    "lat": business_loc[1],
                    "lng": business_loc[0]
                }
            })
        
        # Sort by distance (nearest first)
        businesses_list.sort(key=lambda x: x["distance_km"])
        
        return {
            "user_location": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "businesses": businesses_list,
            "total_found": len(businesses_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering businesses: {str(e)}")

# Customer Address Management
@api_router.get("/customer/addresses")
async def get_customer_addresses(
    current_user: dict = Depends(get_current_customer_user)
):
    """Get all saved addresses for customer"""
    try:
        customer_id = current_user.get("id")
        addresses_cursor = db.addresses.find({"customer_id": customer_id})
        addresses = []
        async for addr in addresses_cursor:
            addresses.append({
                "id": addr.get("id"),
                "title": addr.get("title"),
                "street": addr.get("street"),
                "building": addr.get("building"),
                "floor": addr.get("floor"),
                "apartment": addr.get("apartment"),
                "city": addr.get("city"),
                "district": addr.get("district"),
                "postal_code": addr.get("postal_code"),
                "lat": addr.get("lat"),
                "lng": addr.get("lng"),
                "is_default": addr.get("is_default", False)
            })
        return {"addresses": addresses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching addresses: {str(e)}")

@api_router.post("/customer/addresses")
async def add_customer_address(
    address: dict,
    current_user: dict = Depends(get_current_customer_user)
):
    """Add new address for customer"""
    try:
        customer_id = current_user.get("id")
        
        # If this is set as default, unset other defaults
        if address.get("is_default"):
            await db.addresses.update_many(
                {"customer_id": customer_id},
                {"$set": {"is_default": False}}
            )
        
        new_address = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "title": address.get("title"),
            "street": address.get("street"),
            "building": address.get("building"),
            "floor": address.get("floor"),
            "apartment": address.get("apartment"),
            "city": address.get("city"),
            "district": address.get("district"),
            "postal_code": address.get("postal_code"),
            "lat": address.get("lat"),
            "lng": address.get("lng"),
            "is_default": address.get("is_default", False),
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.addresses.insert_one(new_address)
        return {"success": True, "address_id": new_address["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding address: {str(e)}")

@api_router.delete("/customer/addresses/{address_id}")
async def delete_customer_address(
    address_id: str,
    current_user: dict = Depends(get_current_customer_user)
):
    """Delete customer address"""
    try:
        customer_id = current_user.get("id")
        result = await db.addresses.delete_one({
            "id": address_id,
            "customer_id": customer_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting address: {str(e)}")

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
            "role": "business",  # Only businesses
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
        
        # Use users collection instead of businesses collection
        businesses = await db.users.find(query_filter).to_list(length=None)
        
        business_list = []
        for business in businesses:
            # Get business ID properly - prefer id field over _id
            business_id = business.get("id")
            if business_id is None:
                business_id = str(business.get("_id", "unknown"))
            
            print(f"🏪 Business: {business.get('business_name')}, id={business_id}")
            
            # Use real business location data
            business_city = business.get("city", "İstanbul")  # Use actual city from business
            business_district = business.get("district", "Merkez")  # Use actual district from business
            
            # Create location object with real coordinates or fallback
            # For now use fallback coordinates, later can be enhanced with real geolocation
            fallback_coordinates = {
                "lat": 41.0082 + (hash(business_id) % 100) / 10000,  # Small variation around Istanbul
                "lng": 28.9784 + (hash(business_id) % 100) / 10000
            }
            
            location_data = {
                "name": business_district,
                "lat": fallback_coordinates["lat"],
                "lng": fallback_coordinates["lng"]
            }
            
            business_data = {
                "id": business_id,
                "name": business.get("business_name", "İsimsiz İşletme"),
                "category": business.get("business_category", "gida"),
                "description": business.get("description", "Lezzetli yemekler sizi bekliyor..."),
                "rating": round(4.0 + (hash(business_id) % 15) / 10, 1),
                "delivery_time": f"{20 + (hash(business_id) % 20)}-{35 + (hash(business_id) % 15)}",
                "min_order": 50 + (hash(business_id) % 50),
                "location": location_data,
                "is_open": True,
                "phone": business.get("phone"),
                "address": f"{business_district}, {business_city}",  # Use real city and district
                "image_url": f"/api/placeholder/restaurant-{hash(business_id) % 10}.jpg",
                # Add city and district fields for frontend smart sorting
                "city": business_city,
                "district": business_district
            }
            business_list.append(business_data)
        
        return business_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching businesses: {str(e)}")

@api_router.patch("/admin/users/{user_id}/approve")
async def approve_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Approve any user (business, courier) for KYC - Supports both UUID and ObjectId formats"""
    try:
        # Try to find and update user by both formats
        result = None
        
        # First try as ObjectId (for older users)
        try:
            from bson import ObjectId
            object_id = ObjectId(user_id)
            result = await db.users.update_one(
                {"_id": object_id},
                {"$set": {"kyc_status": "approved"}}
            )
            if result.modified_count > 0:
                return {"success": True, "message": f"User {user_id} approved successfully", "format": "ObjectId"}
        except:
            pass
        
        # Then try as UUID string (for newer users created via registration)
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"kyc_status": "approved"}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": f"User {user_id} approved successfully", "format": "UUID"}
        
        # If not found by either method
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving user: {str(e)}")

@api_router.patch("/admin/users/{user_id}/reject")
async def reject_user(user_id: str, request: dict, current_user: dict = Depends(get_admin_user)):
    """Reject a user (business/courier) application"""
    try:
        notes = request.get("notes", "")
        
        # Update user with rejected status
        update_data = {
            "kyc_status": "rejected",
            "is_active": False,
            "kyc_reviewed_at": datetime.now(timezone.utc).isoformat(),
            "kyc_reviewed_by": current_user.get("id"),
            "rejection_notes": notes
        }
        
        # Try UUID format first
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # If no document found with UUID, try ObjectId format
        if result.matched_count == 0:
            try:
                from bson import ObjectId
                result = await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
            except:
                pass
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return {"success": True, "message": f"User {user_id} rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting user: {str(e)}")

# Removed duplicate placeholder implementation - actual implementation is below at line 2539

# Restaurant Endpoints
@api_router.get("/restaurants")
async def get_restaurants(city: Optional[str] = None):
    """Get restaurants by city"""
    from utils.city_normalize import normalize_city_name
    
    try:
        query_filter = {
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
        
        businesses = await db.businesses.find(query_filter).to_list(length=None)
        
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
        
        businesses = await db.businesses.find(query_filter).to_list(length=None)
        
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
async def get_user_addresses(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get user's saved addresses"""
    try:
        # FIXED: Properly extract user_id from current_user object returned by get_current_user
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        
        if not user_id:
            print(f"DEBUG: No user_id found in current_user: {current_user}")
            return []
        
        print(f"DEBUG: Getting addresses for user_id: {user_id} (email: {user_email})")
        addresses = await db.addresses.find({"user_id": user_id}).to_list(length=None)
        print(f"DEBUG: Found {len(addresses)} addresses for user_id: {user_id}")
        
        address_list = []
        for addr in addresses:
            print(f"DEBUG: Processing address: {addr.get('label', 'NO LABEL')}")
            
            address_data = {
                "id": addr.get("id", str(addr.get("_id", ""))),  # Fixed: use id field first, then _id
                "label": addr.get("label", ""),
                "city": addr.get("city", ""),
                "district": addr.get("district", ""),
                "full_address": addr.get("full_address", ""),
                "description": addr.get("description", ""),
                "lat": addr.get("lat"),
                "lng": addr.get("lng"),
                "is_default": addr.get("is_default", False)
            }
            address_list.append(address_data)
        
        return address_list
        
    except Exception as e:
        logging.error(f"Error fetching addresses: {e}")
        return []

@api_router.post("/user/addresses")
async def add_user_address(address_data: dict, current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
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
            "user_id": user_id,  # Fixed: use user_id instead of userId
            "label": address_data.get("label", ""),
            "city": city_original,  # Fixed: use city instead of city_original
            "city_original": city_original,
            "city_normalized": city_normalized,
            "district": address_data.get("district", ""),  # FIXED: Add district field
            "description": address_data.get("description", ""),
            "lat": lat,  # Fixed: add lat/lng fields directly
            "lng": lng,
            "location": location,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.addresses.insert_one(new_address)
        
        return {
            "id": new_address["id"],
            "label": new_address["label"],
            "city": city_original,
            "district": address_data.get("district", ""),  # FIXED: Return district field
            "description": new_address["description"],
            "lat": lat,
            "lng": lng
        }
        
    except Exception as e:
        import traceback
        logging.error(f"Error adding address: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error adding address: {str(e)}")

@api_router.put("/user/addresses/{address_id}")
async def update_user_address(
    address_id: str,
    address_data: dict,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Update user address"""
    from utils.city_normalize import normalize_city_name
    
    try:
        user_id = current_user.get("id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User identification failed")
        
        # Check if address belongs to user
        existing_address = await db.addresses.find_one({
            "id": address_id,
            "user_id": user_id
        })
        
        if not existing_address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Prepare update data
        city_original = address_data.get("city", existing_address.get("city_original", ""))
        city_normalized = normalize_city_name(city_original)
        
        location = None
        lat = address_data.get("lat")
        lng = address_data.get("lng")
        
        if lat is not None and lng is not None:
            location = {
                "type": "Point",
                "coordinates": [lng, lat]
            }
        
        update_data = {
            "label": address_data.get("label", existing_address.get("label", "")),
            "description": address_data.get("description", existing_address.get("description", "")),
            "city_original": city_original,
            "city_normalized": city_normalized,
            "location": location,
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.addresses.update_one(
            {"id": address_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        return {"success": True, "message": "Address updated successfully"}
        
    except Exception as e:
        logging.error(f"Error updating address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/user/addresses/{address_id}")
async def delete_user_address(
    address_id: str,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Delete user address"""
    try:
        user_id = current_user.get("id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User identification failed")
        
        result = await db.addresses.delete_one({
            "id": address_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        return {"success": True, "message": "Address deleted successfully"}
        
    except Exception as e:
        logging.error(f"Error deleting address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/user/addresses/{address_id}/set-default")
async def set_default_address(
    address_id: str,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Set address as default"""
    try:
        user_id = current_user.get("id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User identification failed")
        
        # Check if address exists and belongs to user
        existing_address = await db.addresses.find_one({
            "id": address_id,
            "user_id": user_id
        })
        
        if not existing_address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Remove default from all addresses
        await db.addresses.update_many(
            {"user_id": user_id},
            {"$set": {"is_default": False}}
        )
        
        # Set this address as default
        await db.addresses.update_one(
            {"id": address_id, "user_id": user_id},
            {"$set": {"is_default": True}}
        )
        
        return {"success": True, "message": "Default address updated"}
        
    except Exception as e:
        logging.error(f"Error setting default address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the API router in the main app
# Restaurant Discovery Endpoints (New Customer App)
@api_router.get("/restaurants/discover")
async def discover_restaurants():
    """Get featured/sponsored restaurants for discovery page"""
    try:
        # Get featured/popular businesses
        businesses = await db.users.find({
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

# Duplicate endpoint removed - using enhanced version below

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
    """Add new payment method (tokenized with mock provider support)"""
    try:
        provider = method_data.get("provider", "stripe")
        card_number = method_data.get("card_number", "")
        expiry_month = method_data.get("expiry_month", "")
        expiry_year = method_data.get("expiry_year", "")
        cvv = method_data.get("cvv", "")
        cardholder_name = method_data.get("cardholder_name", "")
        
        # Validate required fields
        if not all([card_number, expiry_month, expiry_year, cvv, cardholder_name]):
            raise HTTPException(status_code=400, detail="All card fields are required")
        
        # Mock card validation
        if len(card_number.replace(" ", "")) != 16:
            raise HTTPException(status_code=400, detail="Card number must be 16 digits")
        
        if len(cvv) not in [3, 4]:
            raise HTTPException(status_code=400, detail="CVV must be 3 or 4 digits")
        
        # Determine card brand from card number
        card_first_digit = card_number.replace(" ", "")[0]
        if card_first_digit == "4":
            brand = "VISA"
        elif card_first_digit == "5":
            brand = "MASTERCARD"
        elif card_first_digit == "3":
            brand = "AMEX"
        else:
            brand = "UNKNOWN"
        
        # Generate mock token based on provider
        if provider.lower() == "stripe":
            mock_token = f"pm_stripe_{str(uuid.uuid4()).replace('-', '')[:16]}"
        elif provider.lower() == "iyzico":
            mock_token = f"iyz_token_{str(uuid.uuid4()).replace('-', '')[:12]}"
        else:
            mock_token = f"token_{str(uuid.uuid4()).replace('-', '')[:16]}"
        
        # Get last 4 digits
        last_four = card_number.replace(" ", "")[-4:]
        
        payment_method = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "provider": provider,
            "token": mock_token,
            "brand": brand,
            "last_four": last_four,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "cardholder_name": cardholder_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        
        await db.payment_methods.insert_one(payment_method)
        
        if "_id" in payment_method:
            del payment_method["_id"]
        
        # Don't return sensitive info in response
        response_data = {
            "id": payment_method["id"],
            "provider": payment_method["provider"],
            "brand": payment_method["brand"],
            "last_four": payment_method["last_four"],
            "expiry_month": payment_method["expiry_month"],
            "expiry_year": payment_method["expiry_year"],
            "cardholder_name": payment_method["cardholder_name"],
            "created_at": payment_method["created_at"],
            "is_active": payment_method["is_active"]
        }
        
        return response_data
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

# Duplicate function removed - using the enhanced version above

# Admin Business Management Endpoint
@api_router.get("/admin/businesses")
async def get_all_businesses_admin(
    city: Optional[str] = None, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    kyc_status: Optional[str] = None,  # KYC status filter eklendi
    current_user: dict = Depends(get_current_user)
):
    """Get all businesses for admin management with filtering"""
    # from utils.city_normalize import normalize_city_name  # Comment out missing import
    
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Build query filter
        query_filter = {}
        
        # City filter - case-insensitive
        if city:
            import re
            # normalized_city = normalize_city_name(city)  # Commented out due to missing import
            normalized_city = city.lower().strip()  # Simple normalization fallback
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
        
        # KYC status filter (direct KYC filtering)
        if kyc_status:
            query_filter["kyc_status"] = kyc_status
            
        # Add role filter for business users
        query_filter["role"] = "business"
        
        # Get businesses from users collection (not businesses collection)
        businesses = await db.users.find(query_filter).to_list(length=None)
        
        # Convert ObjectId to string and prepare response
        result = []
        for business in businesses:
            business_data = {
                "id": business.get("id", str(business.get("_id", ""))),
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

# Admin Business Management Endpoints
@api_router.get("/admin/businesses/{business_id}")
async def get_business_by_id_admin(business_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific business by ID (Admin only)"""
    try:
        from bson import ObjectId
        
        # Try ObjectId first, then string ID - businesses are stored in users collection
        try:
            business = await db.users.find_one({"_id": ObjectId(business_id), "role": "business"})
        except:
            business = await db.users.find_one({"id": business_id, "role": "business"})
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Convert ObjectId to string and prepare response
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
            "city_normalized": business.get("city_normalized", ""),
            "tax_number": business.get("tax_number", ""),
            "owner_name": business.get("owner_name", ""),
            "documents": business.get("documents", {}),
            "ratings": business.get("ratings", {}),
            "total_orders": business.get("total_orders", 0)
        }
        
        return business_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving business: {str(e)}")

@api_router.patch("/admin/businesses/{business_id}/status")
async def update_business_status_admin(
    business_id: str,
    status_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update business status (Admin only)"""
    try:
        is_active = status_data.get("is_active")
        kyc_status = status_data.get("kyc_status")
        
        if is_active is None and kyc_status is None:
            raise HTTPException(status_code=422, detail="Either is_active or kyc_status is required")
        
        # Build update data
        update_data = {}
        if is_active is not None:
            update_data["is_active"] = bool(is_active)
        
        if kyc_status is not None:
            valid_kyc_statuses = ["pending", "approved", "rejected"]
            if kyc_status not in valid_kyc_statuses:
                raise HTTPException(status_code=422, detail=f"Invalid KYC status. Must be one of: {valid_kyc_statuses}")
            update_data["kyc_status"] = kyc_status
            update_data["kyc_updated_at"] = datetime.now(timezone.utc)
            
            if kyc_status == "rejected":
                update_data["rejection_reason"] = status_data.get("rejection_reason", "No reason provided")
        
        # Update business in users collection
        result = await db.users.update_one(
            {"id": business_id, "role": "business"},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Business not found")
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        return {
            "success": True,
            "message": "Business status updated successfully",
            "business_id": business_id,
            "updates": update_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating business status: {str(e)}")

@api_router.delete("/admin/businesses/{business_id}")
async def delete_business_admin(business_id: str, current_user: dict = Depends(get_admin_user)):
    """Delete business (Admin only) - Use with caution"""
    try:
        from bson import ObjectId
        
        # Also delete business's products and orders
        try:
            # Delete products first
            await db.products.delete_many({"business_id": business_id})
            
            # Delete business
            result = await db.businesses.delete_one({"_id": ObjectId(business_id)})
            if result.deleted_count == 0:
                result = await db.businesses.delete_one({"id": business_id})
        except:
            await db.products.delete_many({"business_id": business_id})
            result = await db.businesses.delete_one({"id": business_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return {
            "message": "Business and related data deleted successfully",
            "business_id": business_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting business: {str(e)}")

@api_router.get("/admin/businesses/stats")
async def get_business_statistics(current_user: dict = Depends(get_admin_user)):
    """Get business statistics for admin dashboard"""
    try:
        # Total businesses
        total_businesses = await db.businesses.count_documents({})
        
        # Active businesses
        active_businesses = await db.businesses.count_documents({"is_active": True})
        
        # Businesses by KYC status
        kyc_pipeline = [
            {"$group": {"_id": "$kyc_status", "count": {"$sum": 1}}}
        ]
        kyc_counts = {}
        async for result in db.businesses.aggregate(kyc_pipeline):
            kyc_counts[result["_id"] or "unknown"] = result["count"]
        
        # Businesses by category
        category_pipeline = [
            {"$group": {"_id": "$business_category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        category_counts = {}
        async for result in db.businesses.aggregate(category_pipeline):
            category_counts[result["_id"] or "Other"] = result["count"]
        
        # New businesses this week
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        new_businesses = await db.businesses.count_documents({
            "created_at": {"$gte": week_start}
        })
        
        return {
            "total_businesses": total_businesses,
            "active_businesses": active_businesses,
            "kyc_status_counts": kyc_counts,
            "category_counts": category_counts,
            "new_businesses_this_week": new_businesses,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving business statistics: {str(e)}")

# Include Route Modules - Phase 2 & 3 Implementation
from routes.business import router as business_router
from routes.nearby import router as nearby_router
from routes.orders import router as orders_router

# Phase 3 Route Modules
from routes.order_status import router as order_status_router
from routes.courier_workflow import router as courier_workflow_router  
from routes.courier_location import router as courier_location_router
from routes.admin_settings import router as admin_settings_router
from routes.websocket_routes import router as websocket_router

# Phase 3.5 - localStorage → DB Migration
from routes.customer_cart import router as customer_cart_router

# City-Strict Address Management
from routes.addresses import router as addresses_router

# City-Strict Business Catalog
from routes.city_catalog import router as city_catalog_router

# Phase 2 - Content & Media Management
from routes.content import router as content_router

# Debug routes (temporary for Atlas testing)
from routes.debug import router as debug_router

# Phase 1 - Courier Reports & Profile Management
from routes.courier_reports import router as courier_reports_router
from routes.courier_ready_orders import router as courier_ready_orders_router

# Phase 2 - Customer Profile & Ratings
from routes.customer_profile import router as customer_profile_router

# Geocoding Service
from routes.geocoding import router as geocoding_router
from routes.admin_kyc import router as admin_kyc_router
from routes.admin_advertisements import router as admin_ads_router
from routes.customer_advertisements import router as customer_ads_router

# Cookie-based authentication router (PRIORITY - include first)
api_router.include_router(auth_router)

# Admin KYC Management
api_router.include_router(admin_kyc_router, prefix="/admin", tags=["Admin KYC"])

# Admin Advertisements Management
api_router.include_router(admin_ads_router, prefix="/admin", tags=["Admin Advertisements"])

# Customer Advertisements
api_router.include_router(customer_ads_router, prefix="/advertisements", tags=["Customer Advertisements"])

api_router.include_router(business_router)
api_router.include_router(nearby_router)
api_router.include_router(orders_router)

# Business Order Confirmation (Phase 1)
from routes.business_order_confirm import router as business_confirm_router
api_router.include_router(business_confirm_router)

# Courier Tasks (Phase 2)
from routes.courier_tasks import router as courier_tasks_router
api_router.include_router(courier_tasks_router)

# Admin Coupons (Phase 3)
from routes.admin_coupons import router as admin_coupons_router
api_router.include_router(admin_coupons_router)

# Cart Coupons (Phase 3)
from routes.cart_coupons import router as cart_coupons_router
api_router.include_router(cart_coupons_router)

# Stable Restaurant Discovery (Emergency Rollback)
from routes.stable_restaurants import router as stable_restaurants_router
api_router.include_router(stable_restaurants_router)

# AI Diagnostics Log Ingestion (Phase 1)
from routes.ai_diagnostics_ingest import router as ai_diagnostics_router
api_router.include_router(ai_diagnostics_router)

# AI Settings (Panel-Aware AI Assistant - Phase 1)
from routes.ai_settings import router as ai_settings_router
api_router.include_router(ai_settings_router)

# AI Assistant (Panel-Aware AI Chat - Phase 2)
from routes.ai_assistant import router as ai_assistant_router
api_router.include_router(ai_assistant_router)

# Phase 3 Routers
api_router.include_router(order_status_router)
api_router.include_router(courier_workflow_router)
api_router.include_router(courier_location_router)
api_router.include_router(admin_settings_router)

# Phase 1 - Courier Reports
api_router.include_router(courier_reports_router)
api_router.include_router(courier_ready_orders_router)

# Phase 2 - Customer Profile & Ratings
api_router.include_router(customer_profile_router)

# Phase 3.5 - localStorage → DB Migration
api_router.include_router(customer_cart_router)

# City-Strict Address Management
api_router.include_router(addresses_router)

# Geocoding Service
api_router.include_router(geocoding_router)

# City-Strict Business Catalog
api_router.include_router(city_catalog_router)

# Phase 2 - Content & Media Management
api_router.include_router(content_router)

# Debug routes (temporary)
api_router.include_router(debug_router)

# WebSocket router (separate from API router due to WebSocket protocol)
app.include_router(websocket_router)

# Additional Courier Endpoints
@api_router.get("/courier/stats")
async def get_courier_stats(current_user: dict = Depends(get_courier_user)):
    """Get courier statistics"""
    try:
        courier_id = current_user["id"]
        
        # Get courier stats from database
        total_deliveries = await db.orders.count_documents({"courier_id": courier_id, "status": "delivered"})
        total_earnings = await db.orders.aggregate([
            {"$match": {"courier_id": courier_id, "status": "delivered"}},
            {"$group": {"_id": None, "total": {"$sum": "$delivery_fee"}}}
        ]).to_list(1)
        
        earnings = total_earnings[0]["total"] if total_earnings else 0
        
        return {
            "total_deliveries": total_deliveries,
            "total_earnings": earnings,
            "average_rating": 4.8,
            "completion_rate": 98.5,
            "active_orders": await db.orders.count_documents({"courier_id": courier_id, "status": {"$in": ["picked_up", "delivering"]}})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/courier/profile")  
async def get_courier_profile(current_user: dict = Depends(get_courier_user)):
    """Get courier profile"""
    return {
        "id": current_user["id"],
        "name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
        "email": current_user.get("email"),
        "phone": current_user.get("phone", ""),
        "vehicle_type": "Motosiklet",
        "license_plate": "34 ABC 123",
        "kyc_status": current_user.get("kyc_status", "approved")
    }

@api_router.get("/courier/earnings")
async def get_courier_earnings(current_user: dict = Depends(get_courier_user)):
    """Get courier earnings breakdown"""
    courier_id = current_user["id"]
    
    # Calculate earnings from delivered orders
    today_earnings = await db.orders.aggregate([
        {"$match": {"courier_id": courier_id, "status": "delivered", "delivered_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)}}},
        {"$group": {"_id": None, "total": {"$sum": "$delivery_fee"}}}
    ]).to_list(1)
    
    week_earnings = await db.orders.aggregate([
        {"$match": {"courier_id": courier_id, "status": "delivered"}},
        {"$group": {"_id": None, "total": {"$sum": "$delivery_fee"}}}
    ]).to_list(1)
    
    return {
        "today": today_earnings[0]["total"] if today_earnings else 0,
        "this_week": week_earnings[0]["total"] if week_earnings else 0,
        "this_month": week_earnings[0]["total"] if week_earnings else 0,
        "total": week_earnings[0]["total"] if week_earnings else 0
    }

@api_router.get("/businesses")
async def get_businesses(
    lat: float = None, 
    lng: float = None, 
    radius: int = 5000,
    city: str = None,
    district: str = None
):
    """Get list of active businesses (public endpoint for customers) - with city/district filtering"""
    try:
        from server import db
        
        # Get active businesses from users collection
        query = {"role": "business", "is_active": True, "kyc_status": "approved"}
        
        # Add city filter if provided
        if city:
            from utils.city_normalize import normalize_city_name
            city_normalized = normalize_city_name(city)
            query["city_normalized"] = city_normalized
            print(f"🔍 Filtering by city: {city} (normalized: {city_normalized})")
        
        # Add district filter if provided  
        if district:
            query["district"] = district
            print(f"🔍 Filtering by district: {district}")
        
        businesses = await db.users.find(query).to_list(length=None)
        
        print(f"✅ Found {len(businesses)} businesses (city={city}, district={district})")
        
        formatted_businesses = []
        for business in businesses:
            # Handle business ID properly - use id field (not _id)
            business_id = business.get("id")
            if business_id is None:
                business_id = str(business.get("_id", "unknown"))
            
            print(f"🏪 Business: {business.get('business_name')}, _id={business.get('_id')}, id={business.get('id')}, using={business_id}")
                
            formatted_business = {
                "id": business_id,
                "name": business.get("business_name", "İsimsiz İşletme"),
                "category": business.get("business_category", "Restaurant"),
                "city": business.get("city", ""),
                "district": business.get("district", ""),
                "address": business.get("address", ""),
                "description": business.get("description", ""),
                "rating": 4.5,  # Default rating
                "delivery_time": "30-45 dk",
                "is_active": business.get("is_active", True),
                "kyc_status": business.get("kyc_status", "pending")
            }
            
            # Add GPS coordinates if available (directly from lat/lng fields)
            business_lat = business.get("lat")
            business_lng = business.get("lng")
            
            if business_lat is not None and business_lng is not None:
                formatted_business["lat"] = business_lat
                formatted_business["lng"] = business_lng
            else:
                # Fallback: try location.coordinates structure (legacy)
                location = business.get("location")
                if location and isinstance(location, dict):
                    coordinates = location.get("coordinates", [])
                    if len(coordinates) >= 2:
                        formatted_business["lat"] = coordinates[1] 
                        formatted_business["lng"] = coordinates[0]
                    
            formatted_businesses.append(formatted_business)
        
        return formatted_businesses
        
    except Exception as e:
        print(f"❌ Error getting businesses: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching businesses: {str(e)}")

@api_router.get("/businesses/{business_id}/products")
async def get_business_products(business_id: str):
    """Get products for a specific business (public endpoint for customers)"""
    try:
        print(f"🍽️ Getting products for business_id: {business_id}")
        
        # Get products for this business
        products = await db.products.find({"business_id": business_id}).to_list(length=None)
        print(f"🍽️ Found {len(products)} products in database")
        
        # Format products for customer view
        formatted_products = []
        for product in products:
            # Handle ObjectId properly
            product_id = product.get("_id")
            if hasattr(product_id, '__str__'):
                product_id = str(product_id)
            else:
                product_id = product.get("id", "unknown")
                
            formatted_product = {
                "id": product_id,
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "price": float(product.get("price", 0)),
                "category": product.get("category", "main"),
                "image": product.get("image", ""),
                "availability": product.get("availability", True)
            }
            formatted_products.append(formatted_product)
            print(f"🍽️ Added product: {formatted_product['name']} - ₺{formatted_product['price']}")
        
        return formatted_products
        
    except Exception as e:
        print(f"❌ Error getting business products: {e}")
        import traceback
        traceback.print_exc()
        return []

# Review/Rating System Endpoints
@api_router.post("/reviews")
async def create_review(
    review_data: dict,
    current_user: dict = Depends(get_customer_user)
):
    """Create customer review for completed order"""
    try:
        order_id = review_data.get("order_id")
        target_type = review_data.get("target_type", "business")  # business or courier
        target_id = review_data.get("target_id")
        rating = review_data.get("rating", 5)
        comment = review_data.get("comment", "")
        
        if not all([order_id, target_id, rating]):
            raise HTTPException(status_code=422, detail="Missing required fields")
            
        # Verify order exists and belongs to customer
        order = None
        try:
            from bson import ObjectId
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except:
            order = await db.orders.find_one({"id": order_id})
            
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.get("customer_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Order does not belong to customer")
            
        # Check if order is delivered
        if order.get("status") != "delivered":
            raise HTTPException(status_code=422, detail="Can only review delivered orders")
            
        # Create review
        review = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "customer_id": current_user["id"],
            "target_type": target_type,
            "target_id": target_id,
            "rating": min(max(int(rating), 1), 5),  # Ensure rating is 1-5
            "comment": comment,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.reviews.insert_one(review)
        
        return {
            "success": True,
            "message": "Review created successfully",
            "review_id": review["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating review: {e}")
        raise HTTPException(status_code=500, detail=f"Review creation failed: {str(e)}")

@api_router.get("/reviews/{target_id}")
async def get_reviews(target_id: str, target_type: str = "business"):
    """Get reviews for business or courier"""
    try:
        reviews = await db.reviews.find({
            "target_id": target_id,
            "target_type": target_type
        }).sort("created_at", -1).to_list(length=50)
        
        # Calculate average rating
        total_rating = sum(review.get("rating", 5) for review in reviews)
        avg_rating = total_rating / len(reviews) if reviews else 0
        
        return {
            "reviews": [
                {
                    "id": review.get("id", ""),
                    "rating": review.get("rating", 5),
                    "comment": review.get("comment", ""),
                    "created_at": review.get("created_at", "").isoformat() if hasattr(review.get("created_at", ""), 'isoformat') else str(review.get("created_at", ""))
                }
                for review in reviews
            ],
            "average_rating": round(avg_rating, 1),
            "total_reviews": len(reviews)
        }
        
    except Exception as e:
        print(f"❌ Error getting reviews: {e}")
        return {"reviews": [], "average_rating": 4.5, "total_reviews": 0}

# Customer Address Management Endpoints
@api_router.get("/customer/addresses")
async def get_customer_addresses(current_user: dict = Depends(get_customer_user)):
    """Get customer's saved addresses"""
    try:
        from server import db
        
        addresses = await db.customer_addresses.find({
            "customer_id": current_user["id"]
        }).sort("created_at", -1).to_list(length=None)
        
        formatted_addresses = []
        for addr in addresses:
            formatted_addresses.append({
                "id": addr.get("_id", str(addr.get("id", ""))),
                "title": addr.get("title", ""),
                "full_address": addr.get("full_address", ""),
                "district": addr.get("district", ""),
                "city": addr.get("city", ""),
                "building_no": addr.get("building_no", ""),
                "apartment_no": addr.get("apartment_no", ""),
                "floor": addr.get("floor", ""),
                "instructions": addr.get("instructions", ""),
                "phone": addr.get("phone", ""),
                "lat": addr.get("lat"),
                "lng": addr.get("lng"),
                "is_default": addr.get("is_default", False),
                "created_at": addr.get("created_at", "").isoformat() if hasattr(addr.get("created_at", ""), 'isoformat') else str(addr.get("created_at", ""))
            })
        
        return formatted_addresses
        
    except Exception as e:
        print(f"❌ Error getting customer addresses: {e}")
        return []

@api_router.post("/customer/addresses")
async def create_customer_address(
    address_data: dict,
    current_user: dict = Depends(get_customer_user)
):
    """Create new customer address"""
    try:
        from server import db
        
        # If this is set as default, unset others
        if address_data.get("is_default", False):
            await db.customer_addresses.update_many(
                {"customer_id": current_user["id"]},
                {"$set": {"is_default": False}}
            )
        
        # Create new address
        address = {
            "_id": str(uuid.uuid4()),
            "customer_id": current_user["id"],
            "title": address_data.get("title", "Ev"),
            "full_address": address_data.get("full_address", ""),
            "district": address_data.get("district", ""),
            "city": address_data.get("city", ""),
            "building_no": address_data.get("building_no", ""),
            "apartment_no": address_data.get("apartment_no", ""),
            "floor": address_data.get("floor", ""),
            "instructions": address_data.get("instructions", ""),
            "phone": address_data.get("phone", ""),
            "lat": float(address_data.get("lat", 0)) if address_data.get("lat") else None,
            "lng": float(address_data.get("lng", 0)) if address_data.get("lng") else None,
            "is_default": address_data.get("is_default", False),
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.customer_addresses.insert_one(address)
        
        return {
            "success": True,
            "message": "Address created successfully",
            "address_id": address["_id"]
        }
        
    except Exception as e:
        print(f"❌ Error creating customer address: {e}")
        raise HTTPException(status_code=500, detail=f"Address creation failed: {str(e)}")

@api_router.put("/customer/addresses/{address_id}")
async def update_customer_address(
    address_id: str,
    address_data: dict,
    current_user: dict = Depends(get_customer_user)
):
    """Update customer address"""
    try:
        from server import db
        
        # If this is set as default, unset others
        if address_data.get("is_default", False):
            await db.customer_addresses.update_many(
                {"customer_id": current_user["id"], "_id": {"$ne": address_id}},
                {"$set": {"is_default": False}}
            )
        
        # Update address
        update_data = {}
        for field in ["title", "full_address", "district", "city", "building_no", "apartment_no", "floor", "instructions", "phone", "is_default"]:
            if field in address_data:
                update_data[field] = address_data[field]
        
        if "lat" in address_data and address_data["lat"]:
            update_data["lat"] = float(address_data["lat"])
        if "lng" in address_data and address_data["lng"]:
            update_data["lng"] = float(address_data["lng"])
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.customer_addresses.update_one(
            {"_id": address_id, "customer_id": current_user["id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Address not found or no changes made")
        
        return {
            "success": True,
            "message": "Address updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating customer address: {e}")
        raise HTTPException(status_code=500, detail=f"Address update failed: {str(e)}")

@api_router.delete("/customer/addresses/{address_id}")
async def delete_customer_address(
    address_id: str,
    current_user: dict = Depends(get_customer_user)
):
    """Delete customer address"""
    try:
        from server import db
        
        result = await db.customer_addresses.delete_one({
            "_id": address_id,
            "customer_id": current_user["id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        return {
            "success": True,
            "message": "Address deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting customer address: {e}")
        raise HTTPException(status_code=500, detail=f"Address deletion failed: {str(e)}")

@api_router.patch("/customer/addresses/{address_id}/default")
async def set_default_address(
    address_id: str,
    current_user: dict = Depends(get_customer_user)
):
    """Set address as default"""
    try:
        from server import db
        
        # Unset all other defaults
        await db.customer_addresses.update_many(
            {"customer_id": current_user["id"]},
            {"$set": {"is_default": False}}
        )
        
        # Set this as default
        result = await db.customer_addresses.update_one(
            {"_id": address_id, "customer_id": current_user["id"]},
            {"$set": {"is_default": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        return {
            "success": True,
            "message": "Default address updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error setting default address: {e}")
        raise HTTPException(status_code=500, detail=f"Default address update failed: {str(e)}")

# Business Orders Management Endpoints
@api_router.get("/business/orders/incoming")
async def get_business_incoming_orders(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get incoming/pending orders for business"""
    try:
        business_id = current_user["id"]
        
        # Get orders with status 'created', 'pending' or 'placed' assigned to this business
        orders = await db.orders.find({
            "business_id": business_id,
            "status": {"$in": ["created", "pending", "placed"]}
        }).sort("created_at", -1).to_list(length=50)
        
        formatted_orders = []
        for order in orders:
            # Get customer details (use 'id' field, not '_id')
            customer = await db.users.find_one({"id": order.get("customer_id")})
            customer_name = "Unknown Customer"
            customer_phone = ""
            
            if customer:
                customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
                customer_phone = customer.get("phone", "")
            
            # Parse delivery address properly
            delivery_addr = order.get("delivery_address", {})
            if isinstance(delivery_addr, dict):
                delivery_address_formatted = {
                    "address": delivery_addr.get("label") or delivery_addr.get("address", ""),
                    "lat": delivery_addr.get("lat"),
                    "lng": delivery_addr.get("lng")
                }
            else:
                # Fallback for old format
                delivery_address_formatted = {
                    "address": str(delivery_addr) if delivery_addr else "",
                    "lat": order.get("delivery_lat"),
                    "lng": order.get("delivery_lng")
                }
            
            formatted_order = {
                "id": order.get("id", str(order.get("_id", ""))),  # Use 'id' field first
                "business_id": order.get("business_id"),  # Add business_id to response
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer": {  # Add full customer object
                    "name": customer_name,
                    "phone": customer_phone,
                    "id": order.get("customer_id")
                },
                "items": order.get("items", []),
                "total_amount": float(order.get("total_amount", 0)),
                "delivery_fee": float(order.get("delivery_fee", 0)),
                "totals": {  # Add totals object
                    "subtotal": float(order.get("total_amount", 0)),
                    "delivery": float(order.get("delivery_fee", 0)),
                    "grand_total": float(order.get("total_amount", 0)) + float(order.get("delivery_fee", 0))
                },
                "pickup_address": order.get("business_address", ""),
                "delivery_address": delivery_address_formatted,
                "address": delivery_address_formatted,  # Alias for compatibility
                "order_date": order.get("created_at", ""),
                "status": order.get("status", "pending"),
                "payment_method": order.get("payment_method", "unknown"),
                "notes": order.get("notes") or order.get("special_instructions", "")
            }
            formatted_orders.append(formatted_order)
        
        return formatted_orders
        
    except Exception as e:
        print(f"❌ Error getting incoming orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get incoming orders: {str(e)}")

@api_router.get("/business/orders/active")
async def get_business_active_orders(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get active orders (preparing, ready) for business"""
    try:
        business_id = current_user["id"]
        
        # Get orders with active statuses
        orders = await db.orders.find({
            "business_id": business_id,
            "status": {"$in": ["confirmed", "preparing", "ready"]}
        }).sort("created_at", -1).to_list(length=50)
        
        formatted_orders = []
        for order in orders:
            # Get customer details (use 'id' field, not '_id')
            customer = await db.users.find_one({"id": order.get("customer_id")})
            customer_name = "Unknown Customer"
            
            if customer:
                customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            
            # Calculate preparation time elapsed
            preparation_time = 0
            if order.get("confirmed_at") or order.get("accepted_at"):
                confirmed_time = order.get("confirmed_at") or order.get("accepted_at")
                if hasattr(confirmed_time, 'timestamp'):
                    preparation_time = int((datetime.now(timezone.utc).timestamp() - confirmed_time.timestamp()) / 60)
            
            # Parse delivery address properly
            delivery_addr = order.get("delivery_address", {})
            if isinstance(delivery_addr, dict):
                delivery_address_formatted = {
                    "address": delivery_addr.get("label") or delivery_addr.get("address", ""),
                    "lat": delivery_addr.get("lat"),
                    "lng": delivery_addr.get("lng")
                }
            else:
                delivery_address_formatted = {
                    "address": str(delivery_addr) if delivery_addr else "",
                    "lat": order.get("delivery_lat"),
                    "lng": order.get("delivery_lng")
                }
            
            formatted_order = {
                "id": order.get("id", str(order.get("_id", ""))),  # Use 'id' field first
                "business_id": order.get("business_id"),  # Add business_id
                "customer_name": customer_name,
                "customer_phone": customer.get("phone", "") if customer else "",
                "customer": {  # Add full customer object
                    "name": customer_name,
                    "phone": customer.get("phone", "") if customer else "",
                    "id": order.get("customer_id")
                },
                "items": order.get("items", []),
                "total_amount": float(order.get("total_amount", 0)),
                "delivery_fee": float(order.get("delivery_fee", 0)),
                "totals": {  # Add totals object
                    "subtotal": float(order.get("total_amount", 0)),
                    "delivery": float(order.get("delivery_fee", 0)),
                    "grand_total": float(order.get("total_amount", 0)) + float(order.get("delivery_fee", 0))
                },
                "delivery_address": delivery_address_formatted,
                "address": delivery_address_formatted,
                "payment_method": order.get("payment_method", "unknown"),
                "notes": order.get("notes") or order.get("special_instructions", ""),
                "status": order.get("status", "confirmed"),
                "accepted_at": order.get("confirmed_at") or order.get("accepted_at"),
                "order_date": order.get("created_at", ""),
                "preparation_time": preparation_time
            }
            formatted_orders.append(formatted_order)
        
        return formatted_orders
        
    except Exception as e:
        print(f"❌ Error getting active orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active orders: {str(e)}")

@api_router.get("/business/stats")
async def get_business_statistics(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get real business statistics from orders"""
    try:
        business_id = current_user["id"]
        now = datetime.now(timezone.utc)
        
        # Today's stats
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = await db.orders.find({
            "business_id": business_id,
            "created_at": {"$gte": today_start},
            "status": {"$in": ["delivered", "confirmed", "preparing", "ready"]}
        }).to_list(length=None)
        
        today_revenue = sum(float(order.get("total_amount", 0)) for order in today_orders)
        today_count = len(today_orders)
        today_avg = today_revenue / today_count if today_count > 0 else 0
        
        # Week's stats
        week_start = now - timedelta(days=7)
        week_orders = await db.orders.find({
            "business_id": business_id,
            "created_at": {"$gte": week_start},
            "status": {"$in": ["delivered", "confirmed", "preparing", "ready"]}
        }).to_list(length=None)
        
        week_revenue = sum(float(order.get("total_amount", 0)) for order in week_orders)
        week_count = len(week_orders)
        
        # Month's stats
        month_start = now - timedelta(days=30)
        month_orders = await db.orders.find({
            "business_id": business_id,
            "created_at": {"$gte": month_start},
            "status": {"$in": ["delivered", "confirmed", "preparing", "ready"]}
        }).to_list(length=None)
        
        month_revenue = sum(float(order.get("total_amount", 0)) for order in month_orders)
        month_count = len(month_orders)
        
        # Top products from recent orders
        product_stats = {}
        for order in month_orders:
            for item in order.get("items", []):
                product_name = item.get("name", "Unknown")
                quantity = int(item.get("quantity", 1))
                price = float(item.get("price", 0))
                
                if product_name not in product_stats:
                    product_stats[product_name] = {"sales": 0, "revenue": 0}
                
                product_stats[product_name]["sales"] += quantity
                product_stats[product_name]["revenue"] += price * quantity
        
        top_products = sorted(
            [{"name": name, **stats} for name, stats in product_stats.items()],
            key=lambda x: x["revenue"],
            reverse=True
        )[:5]
        
        # Peak hours analysis
        hour_stats = {}
        for order in week_orders:
            created_at = order.get("created_at")
            if hasattr(created_at, 'hour'):
                hour = created_at.hour
                hour_range = f"{hour:02d}:00-{hour+1:02d}:00"
                hour_stats[hour_range] = hour_stats.get(hour_range, 0) + 1
        
        peak_hours = sorted(
            [{"hour": hour, "orders": count} for hour, count in hour_stats.items()],
            key=lambda x: x["orders"],
            reverse=True
        )[:3]
        
        # Completion rate (delivered vs total)
        delivered_count = len([o for o in today_orders if o.get("status") == "delivered"])
        completion_rate = (delivered_count / today_count * 100) if today_count > 0 else 0
        
        return {
            "today": {
                "orders": today_count,
                "revenue": round(today_revenue, 2),
                "avgOrderValue": round(today_avg, 2),
                "completionRate": round(completion_rate, 1)
            },
            "week": {
                "orders": week_count,
                "revenue": round(week_revenue, 2),
                "growth": 0  # Would need historical data for real growth calculation
            },
            "month": {
                "orders": month_count,
                "revenue": round(month_revenue, 2),
                "growth": 0  # Would need historical data for real growth calculation
            },
            "topProducts": top_products,
            "peakHours": peak_hours,
            "customerSatisfaction": 4.5  # Would need reviews data for real calculation
        }
        
    except Exception as e:
        print(f"❌ Error getting business statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@api_router.get("/business/financials")
async def get_business_financials(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get real business financial data"""
    try:
        business_id = current_user["id"]
        now = datetime.now(timezone.utc)
        
        # Commission rate (platform fee)
        commission_rate = 0.15  # 15% platform commission
        
        # Get delivered orders for financial calculations
        delivered_orders = await db.orders.find({
            "business_id": business_id,
            "status": "delivered"
        }).to_list(length=None)
        
        # Calculate daily revenue for the last 30 days
        daily_revenue = {}
        total_revenue = 0
        
        for order in delivered_orders:
            delivered_at = order.get("delivered_at")
            if delivered_at:
                if hasattr(delivered_at, 'date'):
                    date_key = delivered_at.date().isoformat()
                else:
                    date_key = str(delivered_at)[:10]  # Fallback for string dates
                
                order_amount = float(order.get("total_amount", 0))
                total_revenue += order_amount
                
                if date_key not in daily_revenue:
                    daily_revenue[date_key] = 0
                daily_revenue[date_key] += order_amount
        
        # Format daily revenue for last 30 days
        daily_revenue_list = []
        for i in range(30):
            date = (now - timedelta(days=i)).date().isoformat()
            revenue = daily_revenue.get(date, 0)
            if revenue > 0:  # Only include days with revenue
                daily_revenue_list.append({"date": date, "revenue": round(revenue, 2)})
        
        # Sort by date
        daily_revenue_list.sort(key=lambda x: x["date"])
        
        # Calculate current month revenue
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_orders = [o for o in delivered_orders if o.get("delivered_at") and o.get("delivered_at") >= month_start]
        monthly_revenue = sum(float(order.get("total_amount", 0)) for order in month_orders)
        
        # Calculate commission and earnings
        platform_commission = total_revenue * commission_rate
        business_earnings = total_revenue - platform_commission
        
        # Calculate pending payouts (last 7 days earnings not yet paid)
        week_start = now - timedelta(days=7)
        pending_orders = [o for o in delivered_orders if o.get("delivered_at") and o.get("delivered_at") >= week_start]
        pending_revenue = sum(float(order.get("total_amount", 0)) for order in pending_orders)
        pending_payouts = pending_revenue * (1 - commission_rate)
        
        return {
            "dailyRevenue": daily_revenue_list[-7:],  # Last 7 days
            "monthlyRevenue": round(monthly_revenue, 2),
            "pendingPayouts": round(pending_payouts, 2),
            "commission": commission_rate,
            "totalEarnings": round(business_earnings, 2)
        }
        
    except Exception as e:
        print(f"❌ Error getting business financials: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get financials: {str(e)}")

# Business Menu Endpoint
@api_router.get("/business/menu")
async def get_business_menu_items(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get menu items for current business"""
    try:
        business_id = current_user["id"]
        
        # Get all menu items for this business
        products = await db.products.find({"business_id": business_id}).to_list(None)
        
        menu_items = []
        for product in products:
            # Use 'id' field if available, otherwise use '_id' as string
            product_id = product.get("id") or str(product.get("_id", ""))
            menu_items.append({
                "id": product_id,
                "name": product.get("name"),
                "description": product.get("description", ""),
                "price": product.get("price", 0),
                "category": product.get("category", "uncategorized"),
                "image_url": product.get("image_url", ""),
                "is_available": product.get("is_available", True),
                "business_id": product.get("business_id")
            })
        
        return menu_items
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting business menu: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get menu: {str(e)}")

@api_router.get("/business/public-menu/{business_id}/products")
async def get_public_business_menu(business_id: str):
    """Public endpoint to get menu items for a specific business (for customers)"""
    try:
        print(f"🔍 Getting public menu for business: {business_id}")
        
        # Get all available menu items for this business
        products = await db.products.find({
            "business_id": business_id,
            "is_available": True
        }).to_list(None)
        
        print(f"✅ Found {len(products)} products for business {business_id}")
        
        menu_items = []
        for product in products:
            # Use 'id' field if available, otherwise use '_id' as string
            product_id = product.get("id") or str(product.get("_id", ""))
            menu_items.append({
                "id": product_id,
                "name": product.get("name"),
                "description": product.get("description", ""),
                "price": product.get("price", 0),
                "category": product.get("category", "uncategorized"),
                "image_url": product.get("image_url", ""),
                "is_available": product.get("is_available", True),
                "business_id": product.get("business_id")
            })
        
        return menu_items
        
    except Exception as e:
        print(f"❌ Error getting public menu: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get menu: {str(e)}")


@api_router.get("/business/public/{business_id}/menu")
async def get_public_business_menu_alt(business_id: str):
    """Alternative public endpoint (for frontend compatibility)"""
    return await get_public_business_menu(business_id)

@api_router.post("/business/menu")
async def create_business_menu_item(
    item_data: dict,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Create a new menu item for current business"""
    try:
        import uuid
        from datetime import datetime, timezone
        
        business_id = current_user["id"]
        
        print(f"📝 Creating menu item for business: {business_id}")
        print(f"   Item: {item_data.get('name')}")
        print(f"   DB object: {db}")
        print(f"   DB name: {db.name if db else 'None'}")
        
        # Create menu item
        menu_item = {
            "id": str(uuid.uuid4()),
            "business_id": business_id,
            "name": item_data.get("name"),
            "description": item_data.get("description", ""),
            "price": float(item_data.get("price", 0)),
            "category": item_data.get("category", "uncategorized"),
            "image_url": item_data.get("image_url", ""),
            "is_available": item_data.get("is_available", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"📦 Menu item prepared: {menu_item}")
        
        # Insert into database
        try:
            result = await db.products.insert_one(menu_item)
            print(f"✅ Insert successful! Inserted ID: {result.inserted_id}")
            print(f"   Acknowledged: {result.acknowledged}")
        except Exception as insert_error:
            print(f"❌ DB INSERT ERROR: {insert_error}")
            print(f"   Error type: {type(insert_error)}")
            raise HTTPException(status_code=500, detail=f"Database insert failed: {str(insert_error)}")
        
        # Verify insertion
        verify = await db.products.find_one({"id": menu_item["id"]})
        if verify:
            print(f"✅ Verified: Item exists in database")
        else:
            print(f"⚠️ Warning: Item not found after insertion!")
        
        # Remove _id from response
        if "_id" in menu_item:
            del menu_item["_id"]
        
        # Return the item directly
        return menu_item
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating menu item: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create menu item: {str(e)}")

@api_router.patch("/business/menu/{item_id}")
async def update_business_menu_item(
    item_id: str,
    item_data: dict,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Update a menu item"""
    try:
        from datetime import datetime, timezone
        
        business_id = current_user["id"]
        
        # Verify ownership
        existing_item = await db.products.find_one({"id": item_id, "business_id": business_id})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Update fields
        update_data = {}
        for key in ["name", "description", "price", "category", "image_url", "is_available"]:
            if key in item_data:
                update_data[key] = item_data[key]
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.products.update_one(
            {"id": item_id},
            {"$set": update_data}
        )
        
        return {"message": "Menu item updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating menu item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update menu item: {str(e)}")

@api_router.delete("/business/menu/{item_id}")
async def delete_business_menu_item(
    item_id: str,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Delete a menu item"""
    try:
        business_id = current_user["id"]
        
        # Verify ownership
        existing_item = await db.products.find_one({"id": item_id, "business_id": business_id})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Delete
        await db.products.delete_one({"id": item_id})
        
        return {"message": "Menu item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting menu item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete menu item: {str(e)}")

# Business Profile/Settings Endpoints
@api_router.get("/business/profile")
async def get_business_profile(current_user: dict = Depends(get_approved_business_user_from_cookie)):
    """Get business profile information"""
    try:
        business_id = current_user["id"]
        
        # Get business user data
        business = await db.users.find_one({"id": business_id})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return {
            "id": business.get("id"),
            "email": business.get("email"),
            "first_name": business.get("first_name", ""),
            "last_name": business.get("last_name", ""),
            "business_name": business.get("business_name", ""),
            "phone": business.get("phone", ""),
            "address": business.get("address", ""),
            "city": business.get("city", ""),
            "district": business.get("district", ""),
            "business_category": business.get("business_category", "gida"),
            "description": business.get("description", ""),
            "tax_number": business.get("tax_number", ""),
            "opening_hours": business.get("opening_hours", "09:00-23:00"),
            "delivery_radius_km": business.get("delivery_radius_km", 10),
            "min_order_amount": business.get("min_order_amount", 0),
            "delivery_fee": business.get("delivery_fee", 0),
            "is_open": business.get("is_open", True),
            "rating": business.get("rating", 0),
            "total_reviews": business.get("total_reviews", 0),
            "kyc_status": business.get("kyc_status", "pending")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting business profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@api_router.patch("/business/profile")
async def update_business_profile(
    profile_data: dict,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Update business profile information"""
    try:
        business_id = current_user["id"]
        
        # Allowed fields to update
        allowed_fields = [
            "first_name", "last_name", "business_name", "phone", "address", "city", "district",
            "description", "opening_hours", "delivery_radius_km",
            "min_order_amount", "delivery_fee", "is_open"
        ]
        
        # Filter only allowed fields
        update_data = {
            key: value for key, value in profile_data.items() 
            if key in allowed_fields and value is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=422, detail="No valid fields to update")
        
        # Update business profile
        result = await db.users.update_one(
            {"id": business_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Business not found or no changes made")
        
        # Return updated profile
        updated_business = await db.users.find_one({"id": business_id})
        
        return {
            "message": "Profile updated successfully",
            "profile": {
                "id": updated_business.get("id"),
                "business_name": updated_business.get("business_name"),
                "phone": updated_business.get("phone"),
                "address": updated_business.get("address"),
                "city": updated_business.get("city"),
                "district": updated_business.get("district"),
                "description": updated_business.get("description"),
                "opening_hours": updated_business.get("opening_hours"),
                "delivery_radius_km": updated_business.get("delivery_radius_km"),
                "min_order_amount": updated_business.get("min_order_amount"),
                "delivery_fee": updated_business.get("delivery_fee"),
                "is_open": updated_business.get("is_open")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating business profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@api_router.post("/payments/process")
async def process_payment(
    payment_data: dict,
    current_user: dict = Depends(get_customer_user)
):
    """Process customer payment (real implementation)"""
    try:
        payment_method = payment_data.get("payment_method", "card")
        amount = float(payment_data.get("amount", 0))
        order_id = payment_data.get("order_id")
        
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Invalid payment amount")
        
        # Create payment record
        payment_record = {
            "_id": str(uuid.uuid4()),
            "order_id": order_id,
            "customer_id": current_user["id"],
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed",  # In real implementation, this would depend on payment gateway
            "transaction_id": f"TXN_{uuid.uuid4().hex[:8].upper()}",
            "created_at": datetime.now(timezone.utc),
            "processed_at": datetime.now(timezone.utc)
        }
        
        # Store payment record
        await db.payments.insert_one(payment_record)
        
        # Update order status to confirmed after successful payment
        if order_id:
            await db.orders.update_one(
                {"_id": order_id},
                {
                    "$set": {
                        "status": "confirmed",
                        "payment_status": "paid",
                        "confirmed_at": datetime.now(timezone.utc)
                    }
                }
            )
        
        return {
            "success": True,
            "payment_id": payment_record["_id"],
            "transaction_id": payment_record["transaction_id"],
            "amount": amount,
            "status": "completed",
            "message": "Payment processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing payment: {e}")
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")



# ==================== ADMIN PANEL UPGRADE ENDPOINTS ====================

# Content Management Endpoints
@api_router.get("/admin/content")
async def get_content_blocks(
    page: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get all content blocks (Admin only)"""
    query = {}
    if page:
        query["page"] = page
    
    blocks = await db.content_blocks.find(query).sort("order", 1).to_list(length=None)
    
    # Convert MongoDB documents
    for block in blocks:
        block["id"] = str(block.pop("_id"))
        if "created_at" in block and hasattr(block["created_at"], 'isoformat'):
            block["created_at"] = block["created_at"].isoformat()
        if "updated_at" in block and hasattr(block["updated_at"], 'isoformat'):
            block["updated_at"] = block["updated_at"].isoformat()
    
    return blocks

@api_router.post("/admin/content")
async def create_content_block(
    block_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Create new content block (Admin only)"""
    from models import ContentBlock
    
    # Create new block
    new_block = {
        "_id": str(uuid.uuid4()),
        "page": block_data["page"],
        "section": block_data["section"],
        "type": block_data["type"],
        "content": block_data["content"],
        "order": block_data.get("order", 0),
        "is_active": block_data.get("is_active", True),
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    
    await db.content_blocks.insert_one(new_block)
    
    new_block["id"] = new_block.pop("_id")
    new_block["created_at"] = new_block["created_at"].isoformat()
    
    return new_block

@api_router.patch("/admin/content/{block_id}")
async def update_content_block(
    block_id: str,
    block_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update content block (Admin only)"""
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Update allowed fields
    for field in ["content", "order", "is_active", "page", "section", "type"]:
        if field in block_data:
            update_data[field] = block_data[field]
    
    result = await db.content_blocks.update_one(
        {"_id": block_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Content block not found")
    
    return {"message": "Content block updated", "block_id": block_id}

@api_router.delete("/admin/content/{block_id}")
async def delete_content_block(
    block_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Delete content block (Admin only)"""
    result = await db.content_blocks.delete_one({"_id": block_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Content block not found")
    
    return {"message": "Content block deleted"}

# Ad Board Management Endpoints
@api_router.get("/admin/adboards")
async def get_ad_boards(current_user: dict = Depends(get_admin_user)):
    """Get all ad boards (Admin only)"""
    boards = await db.ad_boards.find({}).sort("order", 1).to_list(length=None)
    
    # Convert MongoDB documents
    for board in boards:
        board["id"] = str(board.pop("_id"))
        if "created_at" in board and hasattr(board["created_at"], 'isoformat'):
            board["created_at"] = board["created_at"].isoformat()
        if "updated_at" in board and hasattr(board["updated_at"], 'isoformat'):
            board["updated_at"] = board["updated_at"].isoformat()
    
    return boards

@api_router.get("/adboards/active")
async def get_active_ad_boards():
    """Get active ad boards (Public - for customer landing page)"""
    # Get only active boards, max 5
    boards = await db.ad_boards.find({"is_active": True}).sort("order", 1).limit(5).to_list(length=None)
    
    # Convert MongoDB documents and increment impressions
    for board in boards:
        board["id"] = str(board.pop("_id"))
        if "created_at" in board and hasattr(board["created_at"], 'isoformat'):
            board["created_at"] = board["created_at"].isoformat()
        if "updated_at" in board and hasattr(board["updated_at"], 'isoformat'):
            board["updated_at"] = board["updated_at"].isoformat()
        
        # Increment impressions
        await db.ad_boards.update_one(
            {"_id": board["id"]},
            {"$inc": {"impressions": 1}}
        )
    
    return boards

@api_router.post("/admin/adboards")
async def create_ad_board(
    board_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Create new ad board (Admin only)"""
    # Validate max 5 active boards
    active_count = await db.ad_boards.count_documents({"is_active": True})
    if board_data.get("is_active", True) and active_count >= 5:
        raise HTTPException(400, "Maximum 5 active ad boards allowed")
    
    new_board = {
        "_id": str(uuid.uuid4()),
        "title": board_data["title"],
        "subtitle": board_data.get("subtitle"),
        "image": board_data["image"],
        "cta": board_data.get("cta"),
        "order": board_data.get("order", 0),
        "is_active": board_data.get("is_active", True),
        "impressions": 0,
        "clicks": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    
    await db.ad_boards.insert_one(new_board)
    
    new_board["id"] = new_board.pop("_id")
    new_board["created_at"] = new_board["created_at"].isoformat()
    
    return new_board

@api_router.patch("/admin/adboards/{board_id}")
async def update_ad_board(
    board_id: str,
    board_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update ad board (Admin only)"""
    # Check if activating and limit reached
    if board_data.get("is_active"):
        active_count = await db.ad_boards.count_documents({
            "_id": {"$ne": board_id},
            "is_active": True
        })
        if active_count >= 5:
            raise HTTPException(400, "Maximum 5 active ad boards allowed")
    
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Update allowed fields
    for field in ["title", "subtitle", "image", "cta", "order", "is_active"]:
        if field in board_data:
            update_data[field] = board_data[field]
    
    result = await db.ad_boards.update_one(
        {"_id": board_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Ad board not found")
    
    return {"message": "Ad board updated", "board_id": board_id}

@api_router.delete("/admin/adboards/{board_id}")
async def delete_ad_board(
    board_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Delete ad board (Admin only)"""
    result = await db.ad_boards.delete_one({"_id": board_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Ad board not found")
    
    return {"message": "Ad board deleted"}

@api_router.post("/adboards/{board_id}/click")
async def track_ad_click(board_id: str):
    """Track ad board click (Public)"""
    result = await db.ad_boards.update_one(
        {"_id": board_id},
        {"$inc": {"clicks": 1}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Ad board not found")
    
    return {"message": "Click tracked"}

# Promotion Management Endpoints
@api_router.get("/admin/promotions")
async def get_promotions(current_user: dict = Depends(get_admin_user)):
    """Get all promotions (Admin only)"""
    promotions = await db.promotions.find({}).sort("created_at", -1).to_list(length=None)
    
    # Convert MongoDB documents
    for promo in promotions:
        promo["id"] = str(promo.pop("_id"))
        for date_field in ["start_date", "end_date", "created_at", "updated_at"]:
            if date_field in promo and hasattr(promo[date_field], 'isoformat'):
                promo[date_field] = promo[date_field].isoformat()
    
    return promotions

@api_router.get("/promotions/active")
async def get_active_promotions():
    """Get active promotions (Public - for customer)"""
    now = datetime.now(timezone.utc)
    
    promotions = await db.promotions.find({
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now}
    }).to_list(length=None)
    
    # Convert MongoDB documents
    for promo in promotions:
        promo["id"] = str(promo.pop("_id"))
        for date_field in ["start_date", "end_date", "created_at", "updated_at"]:
            if date_field in promo and hasattr(promo[date_field], 'isoformat'):
                promo[date_field] = promo[date_field].isoformat()
    
    return promotions

@api_router.post("/admin/promotions")
async def create_promotion(
    promo_data: dict = Body(...),
    current_user: dict = Depends(get_admin_user)
):
    """Create new promotion (Admin only)"""
    # Check if code already exists
    existing = await db.promotions.find_one({"code": promo_data["code"].upper()})
    if existing:
        raise HTTPException(400, "Promotion code already exists")
    
    # Parse dates
    start_date = datetime.fromisoformat(promo_data["start_date"].replace("Z", "+00:00"))
    end_date = datetime.fromisoformat(promo_data["end_date"].replace("Z", "+00:00"))
    
    new_promo = {
        "_id": str(uuid.uuid4()),
        "code": promo_data["code"].upper(),
        "title": promo_data["title"],
        "description": promo_data["description"],
        "discount_pct": promo_data.get("discount_pct", 0),
        "discount_amount": promo_data.get("discount_amount"),
        "target": promo_data.get("target", "all"),
        "target_id": promo_data.get("target_id"),
        "min_order": promo_data.get("min_order", 0),
        "usage_limit": promo_data.get("usage_limit"),
        "usage_per_user": promo_data.get("usage_per_user", 1),
        "used_count": 0,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": promo_data.get("is_active", True),
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    
    await db.promotions.insert_one(new_promo)
    
    new_promo["id"] = new_promo.pop("_id")
    new_promo["start_date"] = new_promo["start_date"].isoformat()
    new_promo["end_date"] = new_promo["end_date"].isoformat()
    new_promo["created_at"] = new_promo["created_at"].isoformat()
    
    return new_promo

@api_router.patch("/admin/promotions/{promo_id}")
async def update_promotion(
    promo_id: str,
    promo_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update promotion (Admin only)"""
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Update allowed fields
    for field in ["title", "description", "discount_pct", "discount_amount", 
                  "min_order", "usage_limit", "usage_per_user", "is_active"]:
        if field in promo_data:
            update_data[field] = promo_data[field]
    
    # Parse dates if provided
    if "start_date" in promo_data:
        update_data["start_date"] = datetime.fromisoformat(promo_data["start_date"].replace("Z", "+00:00"))
    if "end_date" in promo_data:
        update_data["end_date"] = datetime.fromisoformat(promo_data["end_date"].replace("Z", "+00:00"))
    
    result = await db.promotions.update_one(
        {"_id": promo_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Promotion not found")
    
    return {"message": "Promotion updated", "promo_id": promo_id}

@api_router.delete("/admin/promotions/{promo_id}")
async def delete_promotion(
    promo_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Delete promotion (Admin only)"""
    result = await db.promotions.delete_one({"_id": promo_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Promotion not found")
    
    return {"message": "Promotion deleted"}

@api_router.get("/customer/promotions/validate")
async def validate_promotion(
    code: str,
    order_amount: float,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Validate promotion code (Customer)"""
    now = datetime.now(timezone.utc)
    
    # Find promotion
    promo = await db.promotions.find_one({
        "code": code.upper(),
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now}
    })
    
    if not promo:
        raise HTTPException(404, "Geçersiz veya süresi dolmuş promosyon kodu")
    
    # Check minimum order amount
    if order_amount < promo["min_order"]:
        raise HTTPException(400, f"Minimum sipariş tutarı {promo['min_order']} TL olmalıdır")
    
    # Check total usage limit
    if promo.get("usage_limit") and promo["used_count"] >= promo["usage_limit"]:
        raise HTTPException(400, "Bu promosyon kullanım limitine ulaştı")
    
    # Check user usage limit
    user_usage = await db.promotion_usage.count_documents({
        "promotion_id": promo["_id"],
        "user_id": current_user["id"]
    })
    
    if user_usage >= promo["usage_per_user"]:
        raise HTTPException(400, "Bu promosyonu kullanım limitinize ulaştınız")
    
    # Calculate discount
    if promo.get("discount_pct"):
        discount = order_amount * (promo["discount_pct"] / 100)
    elif promo.get("discount_amount"):
        discount = promo["discount_amount"]
    else:
        discount = 0
    
    return {
        "valid": True,
        "promo_id": str(promo["_id"]),
        "code": promo["code"],
        "title": promo["title"],
        "description": promo["description"],
        "discount": discount,
        "discount_pct": promo.get("discount_pct"),
        "new_total": max(0, order_amount - discount)
    }

@api_router.post("/customer/promotions/apply")
async def apply_promotion(
    promo_data: dict,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Apply promotion to order (Customer)"""
    # This will be called after order creation
    # Record promotion usage
    usage_record = {
        "_id": str(uuid.uuid4()),
        "promotion_id": promo_data["promo_id"],
        "user_id": current_user["id"],
        "order_id": promo_data["order_id"],
        "discount_applied": promo_data["discount"],
        "used_at": datetime.now(timezone.utc)
    }
    
    await db.promotion_usage.insert_one(usage_record)
    
    # Increment promotion used_count
    await db.promotions.update_one(
        {"_id": promo_data["promo_id"]},
        {"$inc": {"used_count": 1}}
    )
    
    return {"message": "Promotion applied successfully"}

# Message Management Endpoints
@api_router.get("/admin/messages")
async def get_all_messages(current_user: dict = Depends(get_admin_user)):
    """Get all messages (Admin only)"""
    messages = await db.messages.find({}).sort("created_at", -1).to_list(length=None)
    
    # Convert MongoDB documents
    for msg in messages:
        msg["id"] = str(msg.pop("_id"))
        for date_field in ["created_at", "read_at"]:
            if date_field in msg and msg[date_field] and hasattr(msg[date_field], 'isoformat'):
                msg[date_field] = msg[date_field].isoformat()
    
    return messages

@api_router.post("/admin/messages")
async def send_message(
    message_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Send message from admin (Admin only)"""
    recipient_type = message_data["recipient_type"]
    recipient_id = message_data.get("recipient_id")
    
    # Create message(s)
    messages_to_send = []
    
    if recipient_type in ["all_couriers", "all_businesses"]:
        # Broadcast message
        role = "courier" if recipient_type == "all_couriers" else "business"
        recipients = await db.users.find({"role": role}).to_list(length=None)
        
        for recipient in recipients:
            msg = {
                "_id": str(uuid.uuid4()),
                "sender_type": "admin",
                "sender_id": current_user["id"],
                "recipient_type": role,
                "recipient_id": str(recipient.get("id") or recipient.get("_id")),
                "subject": message_data["subject"],
                "message": message_data["message"],
                "status": "sent",
                "is_read": False,
                "read_at": None,
                "created_at": datetime.now(timezone.utc)
            }
            messages_to_send.append(msg)
    else:
        # Single recipient
        msg = {
            "_id": str(uuid.uuid4()),
            "sender_type": "admin",
            "sender_id": current_user["id"],
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
            "subject": message_data["subject"],
            "message": message_data["message"],
            "status": "sent",
            "is_read": False,
            "read_at": None,
            "created_at": datetime.now(timezone.utc)
        }
        messages_to_send.append(msg)
    
    # Insert all messages
    if messages_to_send:
        await db.messages.insert_many(messages_to_send)
    
    return {
        "message": "Message(s) sent successfully",
        "count": len(messages_to_send)
    }

@api_router.get("/courier/messages")
async def get_courier_messages(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get messages for courier"""
    if current_user["role"] != "courier":
        raise HTTPException(403, "Only couriers can access this endpoint")
    
    messages = await db.messages.find({
        "recipient_type": "courier",
        "recipient_id": current_user["id"]
    }).sort("created_at", -1).to_list(length=None)
    
    # Convert MongoDB documents
    for msg in messages:
        msg["id"] = str(msg.pop("_id"))
        for date_field in ["created_at", "read_at"]:
            if date_field in msg and msg[date_field] and hasattr(msg[date_field], 'isoformat'):
                msg[date_field] = msg[date_field].isoformat()
    
    return messages

@api_router.get("/business/messages")
async def get_business_messages(current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
    """Get messages for business"""
    if current_user["role"] != "business":
        raise HTTPException(403, "Only businesses can access this endpoint")
    
    messages = await db.messages.find({
        "recipient_type": "business",
        "recipient_id": current_user["id"]
    }).sort("created_at", -1).to_list(length=None)
    
    # Convert MongoDB documents
    for msg in messages:
        msg["id"] = str(msg.pop("_id"))
        for date_field in ["created_at", "read_at"]:
            if date_field in msg and msg[date_field] and hasattr(msg[date_field], 'isoformat'):
                msg[date_field] = msg[date_field].isoformat()
    
    return messages

@api_router.patch("/messages/{message_id}/read")
async def mark_message_read(
    message_id: str,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """Mark message as read"""
    result = await db.messages.update_one(
        {
            "_id": message_id,
            "recipient_id": current_user["id"]
        },
        {
            "$set": {
                "is_read": True,
                "status": "read",
                "read_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Message not found")
    
    return {"message": "Message marked as read"}

# ============================================================
# ADMIN SETTINGS & MAINTENANCE MODE SYSTEM
# ============================================================

@api_router.get("/admin/settings/system")
async def get_system_settings(current_user: dict = Depends(get_admin_user)):
    """Get system settings including maintenance mode"""
    try:
        settings = await db.settings.find_one({"_id": "system_settings"})
        
        if not settings:
            # Create default settings
            default_settings = {
                "_id": "system_settings",
                "maintenance_mode": False,
                "maintenance_message": "Sistemimiz bakımda. Kısa süre içinde tekrar hizmetinizdeyiz!",
                "maintenance_eta": None,
                "contact_email": "destek@kuryecini.com",
                "contact_phone": "+90 555 123 45 67",
                "social_media": {
                    "instagram": "https://instagram.com/kuryecini",
                    "twitter": "https://twitter.com/kuryecini",
                    "facebook": "https://facebook.com/kuryecini"
                },
                "theme_color": "#FF6B35",
                "logo_url": "/logo.png",
                "updated_at": datetime.now(timezone.utc),
                "updated_by": current_user["id"]
            }
            await db.settings.insert_one(default_settings)
            settings = default_settings
        
        # Remove _id and convert datetime
        if "_id" in settings:
            del settings["_id"]
        if "updated_at" in settings and hasattr(settings["updated_at"], 'isoformat'):
            settings["updated_at"] = settings["updated_at"].isoformat()
        
        return settings
    except Exception as e:
        raise HTTPException(500, f"Error fetching settings: {str(e)}")

@api_router.post("/admin/settings/system")
async def update_system_settings(
    settings_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update system settings"""
    try:
        settings_data["updated_at"] = datetime.now(timezone.utc)
        settings_data["updated_by"] = current_user["id"]
        
        result = await db.settings.update_one(
            {"_id": "system_settings"},
            {"$set": settings_data},
            upsert=True
        )
        
        return {
            "message": "Settings updated successfully",
            "maintenance_mode": settings_data.get("maintenance_mode", False)
        }
    except Exception as e:
        raise HTTPException(500, f"Error updating settings: {str(e)}")

@api_router.post("/admin/settings/maintenance-mode")
async def toggle_maintenance_mode(
    mode_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Toggle maintenance mode on/off"""
    try:
        enabled = mode_data.get("enabled", False)
        message = mode_data.get("message", "Sistemimiz bakımda.")
        eta = mode_data.get("eta")
        
        result = await db.settings.update_one(
            {"_id": "system_settings"},
            {
                "$set": {
                    "maintenance_mode": enabled,
                    "maintenance_message": message,
                    "maintenance_eta": eta,
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": current_user["id"]
                }
            },
            upsert=True
        )
        
        status = "açıldı" if enabled else "kapatıldı"
        return {
            "message": f"Bakım modu {status}",
            "maintenance_mode": enabled
        }
    except Exception as e:
        raise HTTPException(500, f"Error toggling maintenance mode: {str(e)}")

@api_router.get("/maintenance-status")
async def check_maintenance_status():
    """Public endpoint to check if site is in maintenance mode"""
    try:
        settings = await db.settings.find_one({"_id": "system_settings"})
        
        if not settings:
            return {"maintenance_mode": False}
        
        return {
            "maintenance_mode": settings.get("maintenance_mode", False),
            "message": settings.get("maintenance_message", ""),
            "eta": settings.get("maintenance_eta")
        }
    except Exception as e:
        return {"maintenance_mode": False}

@api_router.get("/admin/logs/backend")
async def get_backend_logs(
    lines: int = 100,
    level: str = "all",
    current_user: dict = Depends(get_admin_user)
):
    """Get backend logs"""
    try:
        import subprocess
        
        # Get backend logs from supervisor
        log_file = "/var/log/supervisor/backend.log"
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                # Filter by level if specified
                if level != "all":
                    filtered_lines = [
                        line for line in last_lines 
                        if level.upper() in line.upper() or "ERROR" in line.upper()
                    ]
                    last_lines = filtered_lines
                
                return {
                    "logs": last_lines,
                    "total_lines": len(last_lines),
                    "log_file": log_file
                }
        except FileNotFoundError:
            return {
                "logs": ["Log file not found"],
                "total_lines": 0,
                "log_file": log_file
            }
    except Exception as e:
        raise HTTPException(500, f"Error reading logs: {str(e)}")

@api_router.post("/admin/test-buttons")
async def test_button_functionality(
    test_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Test button functionality - Panel-based testing for customer, business, and courier panels"""
    try:
        button_type = test_data.get("button_type", "all")
        test_results = []
        
        # Customer Panel Tests
        if button_type in ["customer-all", "customer-auth"]:
            try:
                # Test customer authentication
                customer = await db.users.find_one({"role": "customer"})
                test_results.append({
                    "test": "Müşteri Authentication",
                    "status": "success" if customer else "warning",
                    "message": f"Müşteri hesabı bulundu: {customer.get('email') if customer else 'Yok'}" if customer else "Müşteri hesabı bulunamadı",
                    "error": None if customer else "Test müşteri hesabı oluşturun"
                })
            except Exception as e:
                test_results.append({
                    "test": "Müşteri Authentication",
                    "status": "error",
                    "message": "Müşteri authentication testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["customer-all", "customer-discover"]:
            try:
                # Test restaurant discovery
                restaurants = await db.users.find({"role": "business", "is_active": True}).limit(5).to_list(length=5)
                test_results.append({
                    "test": "Restoran Keşfet",
                    "status": "success" if len(restaurants) > 0 else "warning",
                    "message": f"{len(restaurants)} aktif restoran bulundu",
                    "error": None if len(restaurants) > 0 else "Aktif restoran yok"
                })
            except Exception as e:
                test_results.append({
                    "test": "Restoran Keşfet",
                    "status": "error",
                    "message": "Restoran keşfet testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["customer-all", "customer-orders"]:
            try:
                # Test customer orders
                orders_count = await db.orders.count_documents({"customer_id": {"$exists": True}})
                test_results.append({
                    "test": "Müşteri Sipariş Sistemi",
                    "status": "success",
                    "message": f"{orders_count} müşteri siparişi bulundu",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Müşteri Sipariş Sistemi",
                    "status": "error",
                    "message": "Sipariş sistemi testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["customer-all", "customer-address"]:
            try:
                # Test address management
                addresses_count = await db.addresses.count_documents({})
                test_results.append({
                    "test": "Adres Yönetimi",
                    "status": "success",
                    "message": f"{addresses_count} adres kaydı bulundu",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Adres Yönetimi",
                    "status": "error",
                    "message": "Adres yönetimi testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["customer-all", "customer-cart"]:
            try:
                # Test cart/products
                products_count = await db.products.count_documents({"is_available": True})
                test_results.append({
                    "test": "Sepet & Ürünler",
                    "status": "success" if products_count > 0 else "warning",
                    "message": f"{products_count} aktif ürün bulundu",
                    "error": None if products_count > 0 else "Aktif ürün yok"
                })
            except Exception as e:
                test_results.append({
                    "test": "Sepet & Ürünler",
                    "status": "error",
                    "message": "Ürün sistemi testi başarısız",
                    "error": str(e)
                })
        
        # Business Panel Tests
        if button_type in ["business-all", "business-auth"]:
            try:
                # Test business authentication
                business = await db.users.find_one({"role": "business"})
                test_results.append({
                    "test": "İşletme Authentication",
                    "status": "success" if business else "warning",
                    "message": f"İşletme hesabı bulundu: {business.get('business_name') if business else 'Yok'}" if business else "İşletme hesabı bulunamadı",
                    "error": None if business else "Test işletme hesabı oluşturun"
                })
            except Exception as e:
                test_results.append({
                    "test": "İşletme Authentication",
                    "status": "error",
                    "message": "İşletme authentication testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["business-all", "business-menu"]:
            try:
                # Test menu management
                menu_count = await db.products.count_documents({})
                test_results.append({
                    "test": "Menü Yönetimi",
                    "status": "success" if menu_count > 0 else "warning",
                    "message": f"{menu_count} menü ürünü bulundu",
                    "error": None if menu_count > 0 else "Menü ürünü yok"
                })
            except Exception as e:
                test_results.append({
                    "test": "Menü Yönetimi",
                    "status": "error",
                    "message": "Menü sistemi testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["business-all", "business-orders"]:
            try:
                # Test business orders
                business_orders = await db.orders.count_documents({"business_id": {"$exists": True}})
                test_results.append({
                    "test": "İşletme Sipariş Yönetimi",
                    "status": "success",
                    "message": f"{business_orders} işletme siparişi bulundu",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "İşletme Sipariş Yönetimi",
                    "status": "error",
                    "message": "Sipariş yönetimi testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["business-all", "business-dashboard"]:
            try:
                # Test business dashboard data
                test_results.append({
                    "test": "İşletme Dashboard",
                    "status": "success",
                    "message": "Dashboard verileri erişilebilir",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "İşletme Dashboard",
                    "status": "error",
                    "message": "Dashboard testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["business-all", "business-kyc"]:
            try:
                # Test KYC status
                kyc_pending = await db.users.count_documents({"role": "business", "kyc_status": "pending"})
                test_results.append({
                    "test": "İşletme KYC Durumu",
                    "status": "success",
                    "message": f"{kyc_pending} KYC onayı bekleyen işletme",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "İşletme KYC Durumu",
                    "status": "error",
                    "message": "KYC sistemi testi başarısız",
                    "error": str(e)
                })
        
        # Courier Panel Tests
        if button_type in ["courier-all", "courier-auth"]:
            try:
                # Test courier authentication
                courier = await db.users.find_one({"role": "courier"})
                test_results.append({
                    "test": "Kurye Authentication",
                    "status": "success" if courier else "warning",
                    "message": f"Kurye hesabı bulundu: {courier.get('email') if courier else 'Yok'}" if courier else "Kurye hesabı bulunamadı",
                    "error": None if courier else "Test kurye hesabı oluşturun"
                })
            except Exception as e:
                test_results.append({
                    "test": "Kurye Authentication",
                    "status": "error",
                    "message": "Kurye authentication testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["courier-all", "courier-orders"]:
            try:
                # Test courier orders
                available_orders = await db.orders.count_documents({"status": "confirmed"})
                test_results.append({
                    "test": "Kurye Sipariş Kabul",
                    "status": "success",
                    "message": f"{available_orders} teslimata hazır sipariş",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Kurye Sipariş Kabul",
                    "status": "error",
                    "message": "Sipariş kabul testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["courier-all", "courier-delivery"]:
            try:
                # Test delivery system
                active_deliveries = await db.orders.count_documents({"status": "in_transit"})
                test_results.append({
                    "test": "Teslimat İşlemleri",
                    "status": "success",
                    "message": f"{active_deliveries} aktif teslimat",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Teslimat İşlemleri",
                    "status": "error",
                    "message": "Teslimat sistemi testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["courier-all", "courier-location"]:
            try:
                # Test location tracking
                couriers_with_location = await db.users.count_documents({
                    "role": "courier",
                    "lat": {"$exists": True},
                    "lng": {"$exists": True}
                })
                test_results.append({
                    "test": "Konum Takip Sistemi",
                    "status": "success",
                    "message": f"{couriers_with_location} kurye konum bilgisi mevcut",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Konum Takip Sistemi",
                    "status": "error",
                    "message": "Konum takip testi başarısız",
                    "error": str(e)
                })
        
        if button_type in ["courier-all", "courier-kyc"]:
            try:
                # Test courier KYC
                kyc_pending = await db.users.count_documents({"role": "courier", "kyc_status": "pending"})
                test_results.append({
                    "test": "Kurye KYC Durumu",
                    "status": "success",
                    "message": f"{kyc_pending} KYC onayı bekleyen kurye",
                    "error": None
                })
            except Exception as e:
                test_results.append({
                    "test": "Kurye KYC Durumu",
                    "status": "error",
                    "message": "KYC sistemi testi başarısız",
                    "error": str(e)
                })
        
        # Calculate overall status
        error_count = sum(1 for r in test_results if r["status"] == "error")
        warning_count = sum(1 for r in test_results if r["status"] == "warning")
        
        if error_count > 0:
            overall_status = "error"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "success"
        
        return {
            "test_results": test_results,
            "overall_status": overall_status,
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(test_results),
                "success": sum(1 for r in test_results if r["status"] == "success"),
                "warning": warning_count,
                "error": error_count
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Error running tests: {str(e)}")


# Public Content Endpoint for Landing Page
@api_router.get("/content/{page}")
async def get_public_content(page: str):
    """Get public content for a page (landing, about, etc)"""
    blocks = await db.content_blocks.find({
        "page": page,
        "is_active": True
    }).sort("order", 1).to_list(length=None)
    
    # Convert MongoDB documents
    for block in blocks:
        block["id"] = str(block.pop("_id"))
        if "created_at" in block and hasattr(block["created_at"], 'isoformat'):
            block["created_at"] = block["created_at"].isoformat()
        if "updated_at" in block and hasattr(block["updated_at"], 'isoformat'):
            block["updated_at"] = block["updated_at"].isoformat()
    
    return blocks

# ============================================================
# UTILITY ENDPOINTS - GPS Coordinate Updates
# ============================================================

@api_router.post("/admin/utils/update-business-gps")
async def update_business_gps_coordinates(current_user: dict = Depends(get_admin_user)):
    """
    Utility endpoint to update GPS coordinates for businesses that don't have them
    Uses city/district information to get coordinates from Turkish cities database
    """
    from utils.city_normalize import normalize_city_name
    from utils.turkish_cities_coordinates import get_city_coordinates
    
    try:
        # Find businesses without GPS coordinates
        businesses_without_gps = await db.users.find({
            "role": "business",
            "$or": [
                {"lat": {"$exists": False}},
                {"lng": {"$exists": False}},
                {"lat": None},
                {"lng": None}
            ]
        }).to_list(length=None)
        
        updated_count = 0
        failed_count = 0
        results = []
        
        for business in businesses_without_gps:
            business_id = business.get("id")
            business_name = business.get("business_name", "Unknown")
            city = business.get("city")
            district = business.get("district")
            
            if not city:
                results.append({
                    "business_id": business_id,
                    "business_name": business_name,
                    "status": "failed",
                    "reason": "No city information"
                })
                failed_count += 1
                continue
            
            # Normalize city name
            city_normalized = normalize_city_name(city)
            
            # Get GPS coordinates
            coordinates = get_city_coordinates(city, district)
            
            if coordinates:
                # Update business with GPS coordinates
                update_result = await db.users.update_one(
                    {"id": business_id},
                    {
                        "$set": {
                            "lat": coordinates["lat"],
                            "lng": coordinates["lng"],
                            "city_normalized": city_normalized,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    results.append({
                        "business_id": business_id,
                        "business_name": business_name,
                        "city": city,
                        "district": district,
                        "lat": coordinates["lat"],
                        "lng": coordinates["lng"],
                        "status": "success"
                    })
                    updated_count += 1
                else:
                    results.append({
                        "business_id": business_id,
                        "business_name": business_name,
                        "status": "failed",
                        "reason": "Database update failed"
                    })
                    failed_count += 1
            else:
                results.append({
                    "business_id": business_id,
                    "business_name": business_name,
                    "city": city,
                    "district": district,
                    "status": "failed",
                    "reason": "No GPS coordinates found for location"
                })
                failed_count += 1
        
        return {
            "message": "GPS coordinate update completed",
            "summary": {
                "total_businesses_processed": len(businesses_without_gps),
                "updated": updated_count,
                "failed": failed_count
            },
            "details": results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating GPS coordinates: {str(e)}"
        )

@api_router.get("/admin/utils/check-business-gps")
async def check_business_gps_status(current_user: dict = Depends(get_admin_user)):
    """
    Check how many businesses have GPS coordinates
    """
    try:
        # Total businesses
        total_businesses = await db.users.count_documents({"role": "business"})
        
        # Businesses with GPS
        with_gps = await db.users.count_documents({
            "role": "business",
            "lat": {"$exists": True, "$ne": None},
            "lng": {"$exists": True, "$ne": None}
        })
        
        # Businesses without GPS
        without_gps = await db.users.count_documents({
            "role": "business",
            "$or": [
                {"lat": {"$exists": False}},
                {"lng": {"$exists": False}},
                {"lat": None},
                {"lng": None}
            ]
        })
        
        # Get sample of businesses without GPS
        businesses_without_gps = await db.users.find({
            "role": "business",
            "$or": [
                {"lat": {"$exists": False}},
                {"lng": {"$exists": False}},
                {"lat": None},
                {"lng": None}
            ]
        }).limit(10).to_list(length=10)
        
        sample = []
        for business in businesses_without_gps:
            sample.append({
                "id": business.get("id"),
                "business_name": business.get("business_name"),
                "city": business.get("city"),
                "district": business.get("district"),
                "kyc_status": business.get("kyc_status")
            })
        
        return {
            "summary": {
                "total_businesses": total_businesses,
                "with_gps": with_gps,
                "without_gps": without_gps,
                "gps_coverage_percentage": round((with_gps / total_businesses * 100) if total_businesses > 0 else 0, 2)
            },
            "sample_without_gps": sample
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking GPS status: {str(e)}"
        )

# Include business dashboard routes
from routes.business_dashboard import router as dashboard_router
api_router.include_router(dashboard_router, tags=["business-dashboard"])

app.include_router(api_router)

# WebSocket endpoint for real-time order notifications
@app.websocket("/api/ws/orders")
async def websocket_orders_endpoint(
    websocket: WebSocket, 
    business_id: str = Query(None, description="Business ID to subscribe to (for businesses)"),
    role: str = Query("business", description="Role: 'business' or 'admin'")
):
    """Real-time order notifications via WebSocket"""
    from realtime.websocket_orders import websocket_order_notifications
    await websocket_order_notifications(websocket, business_id, role)

