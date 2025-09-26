from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, WebSocket, WebSocketDisconnect
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
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'delivertr-secret-key-2024')
ALGORITHM = "HS256"
security = HTTPBearer()

# Enums
class OrderType(str, Enum):
    FOOD = "food"
    PACKAGE = "package"

class PackagePriority(str, Enum):
    NORMAL = "normal"
    EXPRESS = "express"

class DeliveryTimeSlot(str, Enum):
    ASAP = "asap"
    SCHEDULED = "scheduled"

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_to_couriers_in_area(self, message: dict, lat: float, lon: float, radius_km: float = 7):
        """Belirli bir alandaki kuryelerə mesaj gönder"""
        couriers = await db.couriers.find({
            "is_online": True,
            "kyc_status": "approved",
            "current_location": {"$exists": True}
        }).to_list(length=None)
        
        for courier in couriers:
            if courier.get('current_location'):
                courier_lat = courier['current_location'].get('lat', 0)
                courier_lon = courier['current_location'].get('lon', 0)
                
                distance = calculate_distance(lat, lon, courier_lat, courier_lon)
                if distance <= radius_km:
                    await self.send_personal_message(message, courier['user_id'])

manager = ConnectionManager()

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

# Pricing Calculator
def calculate_delivery_price(distance_km: float, order_type: str, package_priority: str = "normal", weight_kg: float = 0) -> Dict[str, float]:
    """Teslimat ücreti hesaplama"""
    # Base prices
    base_price = 12.0  # Base delivery fee
    
    # Per km pricing
    price_per_km = 2.5 if order_type == "food" else 3.0
    
    # Distance cost
    distance_cost = distance_km * price_per_km
    
    # Priority multiplier
    priority_multiplier = 1.5 if package_priority == "express" else 1.0
    
    # Weight multiplier (for packages)
    weight_multiplier = 1.0
    if order_type == "package" and weight_kg > 5:
        weight_multiplier = 1.0 + (weight_kg - 5) * 0.1  # 10% per kg over 5kg
    
    # Calculate total
    subtotal = (base_price + distance_cost) * priority_multiplier * weight_multiplier
    
    # Platform commission (3%)
    commission = subtotal * 0.03
    
    # Courier earning (85% of delivery fee after commission)
    courier_earning = (subtotal - commission) * 0.85
    
    return {
        "base_price": base_price,
        "distance_cost": distance_cost,
        "total_delivery_fee": round(subtotal, 2),
        "commission": round(commission, 2),
        "courier_earning": round(courier_earning, 2)
    }

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

# Location Models
class Location(BaseModel):
    lat: float
    lon: float
    address: str
    city: str
    
class UpdateLocationRequest(BaseModel):
    lat: float
    lon: float
    address: Optional[str] = None

# Product/Menu Models
class MenuCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_id: str
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_id: str
    category_id: str
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    preparation_time_minutes: int = 15  # Default prep time
    is_available: bool = True
    ingredients: Optional[List[str]] = []
    allergens: Optional[List[str]] = []
    tags: Optional[List[str]] = []  # vegetarian, spicy, etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CreateCategoryRequest(BaseModel):
    name: str
    description: Optional[str] = None

class CreateMenuItemRequest(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    preparation_time_minutes: int = 15
    ingredients: Optional[List[str]] = []
    allergens: Optional[List[str]] = []
    tags: Optional[List[str]] = []

# Package Models
class PackageDetails(BaseModel):
    weight_kg: float
    dimensions: Optional[str] = None  # "length x width x height cm"
    is_fragile: bool = False
    requires_cold_chain: bool = False
    priority: PackagePriority = PackagePriority.NORMAL
    floor_number: Optional[int] = None
    special_instructions: Optional[str] = None

# Enhanced Order Models
class OrderItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    menu_item_id: Optional[str] = None  # For food orders
    name: str
    quantity: int
    unit_price: float
    total_price: float
    special_instructions: Optional[str] = None

class CreateFoodOrderRequest(BaseModel):
    business_id: str
    delivery_address: Location
    items: List[OrderItem]
    delivery_time_preference: DeliveryTimeSlot = DeliveryTimeSlot.ASAP
    scheduled_time: Optional[datetime] = None
    order_notes: Optional[str] = None

class CreatePackageOrderRequest(BaseModel):
    pickup_address: Location
    delivery_address: Location
    package_details: PackageDetails
    recipient_name: str
    recipient_phone: str
    order_notes: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    business_id: Optional[str] = None  # None for package orders
    courier_id: Optional[str] = None
    
    # Order type and details
    order_type: OrderType
    items: Optional[List[OrderItem]] = []  # For food orders
    package_details: Optional[PackageDetails] = None  # For package orders
    
    # Recipient info (for packages)
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    
    # Locations
    pickup_location: Location
    delivery_location: Location
    
    # Timing
    delivery_time_preference: DeliveryTimeSlot = DeliveryTimeSlot.ASAP
    scheduled_time: Optional[datetime] = None
    
    # Pricing
    subtotal: float = 0  # Item total (food orders only)
    delivery_fee: float
    commission: float  # %3 platform commission
    courier_earning: float
    total: float
    
    # Status tracking
    status: str = "pending"  # pending, confirmed, preparing, ready, picked_up, delivering, delivered, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Estimated times
    estimated_prep_time: int = 30  # minutes
    estimated_delivery_time: int = 20  # minutes

class CourierOrderResponse(BaseModel):
    id: str
    business_name: Optional[str] = None
    business_address: str
    delivery_address: str
    distance_km: float
    estimated_earnings: float
    order_type: str
    estimated_delivery_time: int
    items_count: int
    created_at: datetime
    package_info: Optional[str] = None  # For package orders

# Courier Balance Models
class CourierEarning(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    courier_id: str
    order_id: str
    amount: float
    transaction_type: str = "delivery"  # delivery, bonus, penalty
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CourierBalance(BaseModel):
    courier_id: str
    total_earnings: float = 0
    available_balance: float = 0
    pending_balance: float = 0
    total_deliveries: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# User Models (existing + updates)
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

# Database Models (existing + updates)
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    user_type: str  # courier, business, customer
    is_verified: bool = True
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
    location: Optional[dict] = None  # {lat, lon}
    
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    city: str
    addresses: List[dict] = []
    current_location: Optional[dict] = None

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "location_update":
                await update_courier_location_in_db(
                    user_id, 
                    message_data.get("lat"), 
                    message_data.get("lon")
                )
    except WebSocketDisconnect:
        manager.disconnect(user_id)

async def update_courier_location_in_db(user_id: str, lat: float, lon: float):
    """Update courier location in database"""
    await db.couriers.update_one(
        {"user_id": user_id},
        {"$set": {"current_location": {"lat": lat, "lon": lon}}}
    )

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

# Auth Endpoints (existing)
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    """Kullanıcı girişi"""
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    user_data = {"email": user["email"], "user_type": user["user_type"]}
    
    if user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": user["id"]})
        if courier:
            # Get courier balance
            balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
            
            user_data.update({
                "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}",
                "kyc_status": courier.get("kyc_status", "pending"),
                "city": courier.get("city", ""),
                "is_online": courier.get("is_online", False),
                "balance": balance.get("available_balance", 0) if balance else 0
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": user["id"]})
        if business:
            user_data.update({
                "business_id": business["id"],
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

# Registration Endpoints (existing, keeping for completeness)
@api_router.post("/register/courier", response_model=LoginResponse)
async def register_courier(courier_data: CourierRegister):
    """Kurye kaydı"""
    existing_user = await db.users.find_one({"email": courier_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    if courier_data.city not in CITIES:
        raise HTTPException(status_code=400, detail="Geçersiz şehir seçimi")
    
    password_hash = hash_password(courier_data.password)
    user = User(
        email=courier_data.email, 
        password_hash=password_hash, 
        user_type="courier"
    )
    user_dict = user.dict()
    await db.users.insert_one(user_dict)
    
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
    
    # Create initial balance
    balance = CourierBalance(courier_id=courier.id)
    balance_dict = balance.dict()
    await db.courier_balances.insert_one(balance_dict)
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type="courier",
        user_data={
            "email": user.email,
            "name": f"{courier.first_name} {courier.last_name}",
            "city": courier.city,
            "kyc_status": "pending",
            "balance": 0
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
            "business_id": business.id,
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

# Menu Management Endpoints
@api_router.post("/menu/category")
async def create_menu_category(
    category_data: CreateCategoryRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Menü kategorisi oluştur"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "business":
        raise HTTPException(status_code=403, detail="Sadece işletmeler kategori oluşturabilir")
    
    business = await db.businesses.find_one({"user_id": current_user_id})
    if not business:
        raise HTTPException(status_code=404, detail="İşletme bulunamadı")
    
    # Get next display order
    categories_count = await db.menu_categories.count_documents({"business_id": business["id"]})
    
    category = MenuCategory(
        business_id=business["id"],
        name=category_data.name,
        description=category_data.description,
        display_order=categories_count + 1
    )
    
    category_dict = category.dict()
    category_dict["created_at"] = category.created_at.isoformat()
    
    await db.menu_categories.insert_one(category_dict)
    
    return {"success": True, "category_id": category.id, "message": "Kategori oluşturuldu"}

@api_router.post("/menu/item")
async def create_menu_item(
    item_data: CreateMenuItemRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Menü öğesi oluştur"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "business":
        raise HTTPException(status_code=403, detail="Sadece işletmeler ürün ekleyebilir")
    
    business = await db.businesses.find_one({"user_id": current_user_id})
    if not business:
        raise HTTPException(status_code=404, detail="İşletme bulunamadı")
    
    # Verify category belongs to business
    category = await db.menu_categories.find_one({
        "id": item_data.category_id,
        "business_id": business["id"]
    })
    if not category:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    
    item = MenuItem(
        business_id=business["id"],
        category_id=item_data.category_id,
        name=item_data.name,
        description=item_data.description,
        price=item_data.price,
        image_url=item_data.image_url,
        preparation_time_minutes=item_data.preparation_time_minutes,
        ingredients=item_data.ingredients or [],
        allergens=item_data.allergens or [],
        tags=item_data.tags or []
    )
    
    item_dict = item.dict()
    item_dict["created_at"] = item.created_at.isoformat()
    
    await db.menu_items.insert_one(item_dict)
    
    return {"success": True, "item_id": item.id, "message": "Ürün eklendi"}

@api_router.get("/menu/business/{business_id}")
async def get_business_menu(business_id: str):
    """İşletme menüsünü getir"""
    # Get categories
    categories = await db.menu_categories.find({
        "business_id": business_id,
        "is_active": True
    }).sort("display_order", 1).to_list(length=None)
    
    menu = []
    for category in categories:
        # Get items for this category
        items = await db.menu_items.find({
            "business_id": business_id,
            "category_id": category["id"],
            "is_available": True
        }).to_list(length=None)
        
        category_data = {
            "id": category["id"],
            "name": category["name"],
            "description": category.get("description"),
            "items": items
        }
        menu.append(category_data)
    
    return {"menu": menu}

@api_router.get("/menu/my-menu")
async def get_my_menu(current_user_id: str = Depends(get_current_user)):
    """Kendi menümü getir"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "business":
        raise HTTPException(status_code=403, detail="Sadece işletmeler menü görebilir")
    
    business = await db.businesses.find_one({"user_id": current_user_id})
    if not business:
        raise HTTPException(status_code=404, detail="İşletme bulunamadı")
    
    return await get_business_menu(business["id"])

# Enhanced Order Endpoints
@api_router.post("/orders/create-food")
async def create_food_order(
    order_data: CreateFoodOrderRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Yemek siparişi oluştur"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "customer":
        raise HTTPException(status_code=403, detail="Sadece müşteriler sipariş oluşturabilir")
    
    # İşletme bilgilerini al
    business = await db.businesses.find_one({"id": order_data.business_id})
    if not business:
        raise HTTPException(status_code=404, detail="İşletme bulunamadı")
    
    # Pickup location (business address)
    business_location = business.get("location", {})
    if not business_location:
        business_location = {"lat": 41.0082, "lon": 28.9784}
    
    pickup_location = Location(
        lat=business_location["lat"],
        lon=business_location["lon"],
        address=business["address"],
        city=business["city"]
    )
    
    # Calculate distance
    distance = calculate_distance(
        pickup_location.lat, pickup_location.lon,
        order_data.delivery_address.lat, order_data.delivery_address.lon
    )
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order_data.items)
    pricing = calculate_delivery_price(distance, "food")
    total = subtotal + pricing["total_delivery_fee"]
    
    # Create order
    order = Order(
        customer_id=current_user_id,
        business_id=order_data.business_id,
        order_type=OrderType.FOOD,
        items=order_data.items,
        pickup_location=pickup_location,
        delivery_location=order_data.delivery_address,
        delivery_time_preference=order_data.delivery_time_preference,
        scheduled_time=order_data.scheduled_time,
        subtotal=subtotal,
        delivery_fee=pricing["total_delivery_fee"],
        commission=pricing["commission"],
        courier_earning=pricing["courier_earning"],
        total=total
    )
    
    order_dict = order.dict()
    order_dict["created_at"] = order.created_at.isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Notify business
    await manager.send_personal_message({
        "type": "new_order",
        "order_id": order.id,
        "message": "Yeni yemek siparişi alındı!"
    }, business["user_id"])
    
    return {"success": True, "order_id": order.id, "message": "Yemek siparişi oluşturuldu"}

@api_router.post("/orders/create-package")
async def create_package_order(
    order_data: CreatePackageOrderRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Paket siparişi oluştur"""
    user = await db.users.find_one({"id": current_user_id})
    if not user:
        raise HTTPException(status_code=403, detail="Geçersiz kullanıcı")
    
    # Calculate distance
    distance = calculate_distance(
        order_data.pickup_address.lat, order_data.pickup_address.lon,
        order_data.delivery_address.lat, order_data.delivery_address.lon
    )
    
    # Calculate pricing
    pricing = calculate_delivery_price(
        distance, 
        "package", 
        order_data.package_details.priority,
        order_data.package_details.weight_kg
    )
    
    # Create order
    order = Order(
        customer_id=current_user_id,
        business_id=None,  # No business for package orders
        order_type=OrderType.PACKAGE,
        package_details=order_data.package_details,
        recipient_name=order_data.recipient_name,
        recipient_phone=order_data.recipient_phone,
        pickup_location=order_data.pickup_address,
        delivery_location=order_data.delivery_address,
        subtotal=0,  # No item subtotal for packages
        delivery_fee=pricing["total_delivery_fee"],
        commission=pricing["commission"],
        courier_earning=pricing["courier_earning"],
        total=pricing["total_delivery_fee"]
    )
    
    order_dict = order.dict()
    order_dict["created_at"] = order.created_at.isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Broadcast to nearby couriers
    await manager.broadcast_to_couriers_in_area({
        "type": "new_package_order",
        "order_id": order.id,
        "message": f"Yeni paket siparişi: {distance:.1f}km - ₺{pricing['courier_earning']}"
    }, order_data.pickup_address.lat, order_data.pickup_address.lon)
    
    return {"success": True, "order_id": order.id, "message": "Paket siparişi oluşturuldu"}

# Location Endpoints (existing)
@api_router.post("/courier/location/update")
async def update_courier_location(
    location_data: UpdateLocationRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Kurye konumu güncelle"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler konum güncelleyebilir")
    
    await db.couriers.update_one(
        {"user_id": current_user_id},
        {"$set": {"current_location": {
            "lat": location_data.lat,
            "lon": location_data.lon,
            "address": location_data.address,
            "updated_at": datetime.now(timezone.utc)
        }}}
    )
    
    return {"success": True, "message": "Konum güncellendi"}

@api_router.post("/courier/toggle-online")
async def toggle_courier_online_status(
    current_user_id: str = Depends(get_current_user)
):
    """Kurye çevrimiçi durumu değiştir"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler online durumu değiştirebilir")
    
    courier = await db.couriers.find_one({"user_id": current_user_id})
    if not courier:
        raise HTTPException(status_code=404, detail="Kurye bulunamadı")
    
    if courier["kyc_status"] != "approved":
        raise HTTPException(status_code=403, detail="KYC onayı olmadan çevrimiçi olamazsınız")
    
    new_status = not courier.get("is_online", False)
    
    await db.couriers.update_one(
        {"user_id": current_user_id},
        {"$set": {"is_online": new_status}}
    )
    
    return {"success": True, "is_online": new_status}

@api_router.post("/business/location/update")
async def update_business_location(
    location_data: UpdateLocationRequest,
    current_user_id: str = Depends(get_current_user)
):
    """İşletme konumu güncelle"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "business":
        raise HTTPException(status_code=403, detail="Sadece işletmeler konum güncelleyebilir")
    
    await db.businesses.update_one(
        {"user_id": current_user_id},
        {"$set": {"location": {
            "lat": location_data.lat,
            "lon": location_data.lon,
            "address": location_data.address
        }}}
    )
    
    return {"success": True, "message": "İşletme konumu güncellendi"}

# Order Management (existing + enhanced)
@api_router.get("/orders/nearby-couriers")
async def get_nearby_orders_for_courier(
    current_user_id: str = Depends(get_current_user)
):
    """Kuryeye yakın siparişleri listele"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler yakın siparişleri görebilir")
    
    courier = await db.couriers.find_one({"user_id": current_user_id})
    if not courier or courier["kyc_status"] != "approved":
        raise HTTPException(status_code=403, detail="Onaylanmış kuryeler sipariş alabilir")
    
    if not courier.get("is_online", False):
        return {"orders": [], "message": "Çevrimiçi olun"}
    
    courier_location = courier.get("current_location")
    if not courier_location:
        return {"orders": [], "message": "Konum bilginizi paylaşın"}
    
    # Get available orders
    available_orders = await db.orders.find({
        "status": {"$in": ["confirmed", "ready"]},
        "courier_id": None
    }).to_list(length=50)
    
    nearby_orders = []
    for order in available_orders:
        pickup_lat = order["pickup_location"]["lat"]
        pickup_lon = order["pickup_location"]["lon"]
        
        distance = calculate_distance(
            courier_location["lat"], courier_location["lon"],
            pickup_lat, pickup_lon
        )
        
        if distance <= 7:  # 7km radius
            # Get business info if food order
            business_name = "Paket Teslimat"
            if order.get("business_id"):
                business = await db.businesses.find_one({"id": order["business_id"]})
                business_name = business["business_name"] if business else "Bilinmeyen İşletme"
            
            # Package info for display
            package_info = None
            if order["order_type"] == "package":
                package_details = order.get("package_details", {})
                package_info = f"{package_details.get('weight_kg', 0)}kg"
                if package_details.get('priority') == 'express':
                    package_info += " (Express)"
            
            nearby_order = CourierOrderResponse(
                id=order["id"],
                business_name=business_name,
                business_address=order["pickup_location"]["address"],
                delivery_address=order["delivery_location"]["address"],
                distance_km=round(distance, 1),
                estimated_earnings=round(order["courier_earning"], 2),
                order_type=order["order_type"],
                estimated_delivery_time=order["estimated_delivery_time"],
                items_count=len(order.get("items", [])),
                created_at=datetime.fromisoformat(order["created_at"]),
                package_info=package_info
            )
            nearby_orders.append(nearby_order)
    
    # Sort by distance
    nearby_orders.sort(key=lambda x: x.distance_km)
    
    return {"orders": nearby_orders}

@api_router.post("/orders/{order_id}/accept")
async def accept_order(
    order_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Siparişi kabul et"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler sipariş kabul edebilir")
    
    courier = await db.couriers.find_one({"user_id": current_user_id})
    if not courier:
        raise HTTPException(status_code=404, detail="Kurye bulunamadı")
    
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    
    if order["status"] not in ["confirmed", "ready"] or order.get("courier_id"):
        raise HTTPException(status_code=400, detail="Bu sipariş artık müsait değil")
    
    # Assign courier to order
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "courier_id": courier["id"],
            "status": "picked_up",
            "picked_up_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Add earning record
    earning = CourierEarning(
        courier_id=courier["id"],
        order_id=order_id,
        amount=order["courier_earning"],
        description=f"Teslimat kazancı - #{order_id[:8]}"
    )
    earning_dict = earning.dict()
    earning_dict["created_at"] = earning.created_at.isoformat()
    await db.courier_earnings.insert_one(earning_dict)
    
    # Update courier balance
    await db.courier_balances.update_one(
        {"courier_id": courier["id"]},
        {
            "$inc": {
                "pending_balance": order["courier_earning"],
                "total_deliveries": 1
            },
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    # Notify customer and business
    await manager.send_personal_message({
        "type": "order_accepted",
        "order_id": order_id,
        "message": "Siparişiniz kurye tarafından kabul edildi!"
    }, order["customer_id"])
    
    if order.get("business_id"):
        business = await db.businesses.find_one({"id": order["business_id"]})
        if business:
            await manager.send_personal_message({
                "type": "courier_assigned",
                "order_id": order_id,
                "message": "Sipariş kurye tarafından alındı!"
            }, business["user_id"])
    
    return {"success": True, "message": "Sipariş kabul edildi"}

@api_router.post("/orders/{order_id}/update-status")
async def update_order_status(
    order_id: str,
    status: str,
    current_user_id: str = Depends(get_current_user)
):
    """Sipariş durumunu güncelle"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    
    user = await db.users.find_one({"id": current_user_id})
    
    # Status update permissions
    valid_statuses = {
        "business": ["confirmed", "preparing", "ready", "cancelled"],
        "courier": ["picked_up", "delivering", "delivered"],
        "customer": ["cancelled"]
    }
    
    if status not in valid_statuses.get(user["user_type"], []):
        raise HTTPException(status_code=403, detail="Bu durumu güncelleme yetkiniz yok")
    
    # Update fields based on status
    update_data = {"status": status}
    current_time = datetime.now(timezone.utc).isoformat()
    
    if status == "confirmed":
        update_data["confirmed_at"] = current_time
    elif status == "ready":
        update_data["ready_at"] = current_time
    elif status == "picked_up":
        update_data["picked_up_at"] = current_time
    elif status == "delivered":
        update_data["delivered_at"] = current_time
        
        # Move courier balance from pending to available
        if order.get("courier_id"):
            await db.courier_balances.update_one(
                {"courier_id": order["courier_id"]},
                {
                    "$inc": {
                        "available_balance": order["courier_earning"],
                        "pending_balance": -order["courier_earning"],
                        "total_earnings": order["courier_earning"]
                    },
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
                }
            )
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    # Send notifications
    status_messages = {
        "confirmed": "Sipariş onaylandı!",
        "preparing": "Sipariş hazırlanıyor",
        "ready": "Sipariş hazır, kurye bekleniyor",
        "picked_up": "Sipariş kurye tarafından alındı",
        "delivering": "Sipariş yolda",
        "delivered": "Sipariş teslim edildi!",
        "cancelled": "Sipariş iptal edildi"
    }
    
    message = {
        "type": "status_update",
        "order_id": order_id,
        "status": status,
        "message": status_messages.get(status, "Sipariş durumu güncellendi")
    }
    
    # Notify all relevant parties
    await manager.send_personal_message(message, order["customer_id"])
    if order.get("business_id"):
        business = await db.businesses.find_one({"id": order["business_id"]})
        if business:
            await manager.send_personal_message(message, business["user_id"])
    if order.get("courier_id"):
        courier = await db.couriers.find_one({"id": order["courier_id"]})
        if courier:
            await manager.send_personal_message(message, courier["user_id"])
    
    return {"success": True, "message": "Durum güncellendi"}

@api_router.get("/orders/my-orders")
async def get_my_orders(
    current_user_id: str = Depends(get_current_user)
):
    """Kullanıcının siparişlerini getir"""
    user = await db.users.find_one({"id": current_user_id})
    
    query = {}
    if user["user_type"] == "customer":
        query["customer_id"] = current_user_id
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": current_user_id})
        if business:
            query["business_id"] = business["id"]
    elif user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": current_user_id})
        if courier:
            query["courier_id"] = courier["id"]
    
    orders = await db.orders.find(query).sort("created_at", -1).to_list(length=50)
    
    # Enrich orders with additional info
    for order in orders:
        if user["user_type"] != "business" and order.get("business_id"):
            business = await db.businesses.find_one({"id": order["business_id"]})
            order["business_name"] = business["business_name"] if business else "Bilinmeyen İşletme"
        
        if user["user_type"] != "customer":
            customer = await db.customers.find_one({"user_id": order["customer_id"]})
            if customer:
                order["customer_name"] = f"{customer['first_name']} {customer['last_name']}"
    
    return {"orders": orders}

# Courier Balance & Earnings
@api_router.get("/courier/balance")
async def get_courier_balance(current_user_id: str = Depends(get_current_user)):
    """Kurye bakiye bilgileri"""
    user = await db.users.find_one({"id": current_user_id})
    if not user or user["user_type"] != "courier":
        raise HTTPException(status_code=403, detail="Sadece kuryeler bakiye görebilir")
    
    courier = await db.couriers.find_one({"user_id": current_user_id})
    if not courier:
        raise HTTPException(status_code=404, detail="Kurye bulunamadı")
    
    balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
    if not balance:
        # Create initial balance
        balance = CourierBalance(courier_id=courier["id"])
        balance_dict = balance.dict()
        await db.courier_balances.insert_one(balance_dict)
    
    # Get recent earnings
    recent_earnings = await db.courier_earnings.find(
        {"courier_id": courier["id"]}
    ).sort("created_at", -1).limit(10).to_list(length=None)
    
    return {
        "balance": balance,
        "recent_earnings": recent_earnings
    }

# Profile Endpoints (existing + updates)
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
            # Get balance
            balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
            
            profile_data.update({
                "first_name": courier["first_name"],
                "last_name": courier["last_name"],
                "vehicle_type": courier["vehicle_type"],
                "vehicle_model": courier["vehicle_model"],
                "city": courier["city"],
                "kyc_status": courier["kyc_status"],
                "license_photo_url": courier.get("license_photo_url"),
                "vehicle_photo_url": courier.get("vehicle_photo_url"),
                "is_online": courier.get("is_online", False),
                "current_location": courier.get("current_location"),
                "balance": balance.get("available_balance", 0) if balance else 0
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": current_user_id})
        if business:
            profile_data.update({
                "business_id": business["id"],
                "business_name": business["business_name"],
                "address": business["address"],
                "city": business["city"],
                "business_category": business["business_category"],
                "description": business.get("description"),
                "is_open": business.get("is_open", False),
                "location": business.get("location")
            })
    elif user["user_type"] == "customer":
        customer = await db.customers.find_one({"user_id": current_user_id})
        if customer:
            profile_data.update({
                "first_name": customer["first_name"],
                "last_name": customer["last_name"],
                "city": customer["city"],
                "addresses": customer.get("addresses", []),
                "current_location": customer.get("current_location")
            })
    
    return profile_data

# Update courier photos (existing)
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

# Şehirler listesi (existing)
@api_router.get("/cities")
async def get_cities():
    """Türkiye şehirleri listesi"""
    return {"cities": CITIES}

# Business Listings for Customers
@api_router.get("/businesses/nearby")
async def get_nearby_businesses(
    lat: float,
    lon: float,
    category: Optional[str] = None,
    current_user_id: str = Depends(get_current_user)
):
    """Yakındaki işletmeleri listele"""
    query = {"is_open": True}
    if category:
        query["business_category"] = category
    
    businesses = await db.businesses.find(query).to_list(length=50)
    
    nearby_businesses = []
    for business in businesses:
        business_location = business.get("location", {"lat": 41.0082, "lon": 28.9784})
        distance = calculate_distance(
            lat, lon,
            business_location["lat"], business_location["lon"]
        )
        
        if distance <= 10:  # 10km radius for businesses
            business_data = {
                "id": business["id"],
                "name": business["business_name"],
                "category": business["business_category"],
                "address": business["address"],
                "distance_km": round(distance, 1),
                "rating": 4.5,  # Mock rating
                "estimated_delivery_time": min(20 + int(distance * 2), 60)
            }
            nearby_businesses.append(business_data)
    
    # Sort by distance
    nearby_businesses.sort(key=lambda x: x["distance_km"])
    
    return {"businesses": nearby_businesses}

# Admin Endpoints (existing + updates)
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
    
    await db.couriers.update_one(
        {"id": courier_id},
        {"$set": {"kyc_status": "approved", "kyc_notes": notes}}
    )
    
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
    return {"message": "DeliverTR API v4.0 - Ürün/Menü & Gelişmiş Sipariş Sistemi"}

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