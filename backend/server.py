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

# Order Models
class OrderItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: int
    unit_price: float
    total_price: float
    notes: Optional[str] = None

class CreateOrderRequest(BaseModel):
    business_id: str
    delivery_address: Location
    items: List[OrderItem]
    order_notes: Optional[str] = None
    delivery_fee: float = 15.0  # Default delivery fee

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    business_id: str
    courier_id: Optional[str] = None
    
    # Order details
    items: List[OrderItem]
    order_notes: Optional[str] = None
    
    # Locations
    pickup_location: Location
    delivery_location: Location
    
    # Pricing
    subtotal: float
    delivery_fee: float
    commission: float  # %3 platform commission
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
    business_name: str
    business_address: str
    delivery_address: str
    distance_km: float
    estimated_earnings: float
    order_type: str  # gida, nakliye
    estimated_delivery_time: int
    items_count: int
    created_at: datetime

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
            # Handle incoming messages if needed
            message_data = json.loads(data)
            
            if message_data.get("type") == "location_update":
                # Update courier location
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
            user_data.update({
                "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}",
                "kyc_status": courier.get("kyc_status", "pending"),
                "city": courier.get("city", ""),
                "is_online": courier.get("is_online", False)
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

# Location Endpoints
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

# Order Endpoints
@api_router.post("/orders/create")
async def create_order(
    order_data: CreateOrderRequest,
    current_user_id: str = Depends(get_current_user)
):
    """Yeni sipariş oluştur"""
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
        # Default coordinates if not set
        business_location = {"lat": 41.0082, "lon": 28.9784, "address": business["address"]}
    
    pickup_location = Location(
        lat=business_location["lat"],
        lon=business_location["lon"],
        address=business["address"],
        city=business["city"]
    )
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order_data.items)
    commission = subtotal * 0.03  # %3 platform commission
    total = subtotal + order_data.delivery_fee
    
    # Create order
    order = Order(
        customer_id=current_user_id,
        business_id=order_data.business_id,
        items=order_data.items,
        order_notes=order_data.order_notes,
        pickup_location=pickup_location,
        delivery_location=order_data.delivery_address,
        subtotal=subtotal,
        delivery_fee=order_data.delivery_fee,
        commission=commission,
        total=total
    )
    
    order_dict = order.dict()
    # Convert datetime to ISO string for MongoDB
    order_dict["created_at"] = order.created_at.isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Notify business
    await manager.send_personal_message({
        "type": "new_order",
        "order_id": order.id,
        "message": "Yeni sipariş alındı!"
    }, business["user_id"])
    
    return {"success": True, "order_id": order.id, "message": "Sipariş oluşturuldu"}

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
    
    # Get available orders (confirmed but not assigned)
    available_orders = await db.orders.find({
        "status": "confirmed",
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
            # Get business info
            business = await db.businesses.find_one({"id": order["business_id"]})
            
            # Calculate estimated earnings (delivery fee - platform cut)
            estimated_earnings = order["delivery_fee"] * 0.85  # Courier gets 85%
            
            nearby_order = CourierOrderResponse(
                id=order["id"],
                business_name=business["business_name"] if business else "Unknown",
                business_address=order["pickup_location"]["address"],
                delivery_address=order["delivery_location"]["address"],
                distance_km=round(distance, 1),
                estimated_earnings=round(estimated_earnings, 2),
                order_type=business["business_category"] if business else "gida",
                estimated_delivery_time=order["estimated_delivery_time"],
                items_count=len(order["items"]),
                created_at=datetime.fromisoformat(order["created_at"])
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
    
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    
    if order["status"] != "confirmed" or order.get("courier_id"):
        raise HTTPException(status_code=400, detail="Bu sipariş artık müsait değil")
    
    # Assign courier to order
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {
            "courier_id": current_user_id,
            "status": "picked_up",
            "picked_up_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify customer and business
    await manager.send_personal_message({
        "type": "order_accepted",
        "order_id": order_id,
        "message": "Siparişiniz kurye tarafından kabul edildi!"
    }, order["customer_id"])
    
    await manager.send_personal_message({
        "type": "courier_assigned",
        "order_id": order_id,
        "message": "Sipariş kurye tarafından alındı!"
    }, order["business_id"])
    
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
    await manager.send_personal_message(message, order["business_id"])
    if order.get("courier_id"):
        await manager.send_personal_message(message, order["courier_id"])
    
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
        query["business_id"] = current_user_id
    elif user["user_type"] == "courier":
        query["courier_id"] = current_user_id
    
    orders = await db.orders.find(query).sort("created_at", -1).to_list(length=50)
    
    # Enrich orders with additional info
    for order in orders:
        if user["user_type"] != "business":
            business = await db.businesses.find_one({"id": order["business_id"]})
            order["business_name"] = business["business_name"] if business else "Unknown"
        
        if user["user_type"] != "customer":
            customer = await db.customers.find_one({"user_id": order["customer_id"]})
            if customer:
                order["customer_name"] = f"{customer['first_name']} {customer['last_name']}"
    
    return {"orders": orders}

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
                "current_location": courier.get("current_location")
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
    return {"message": "DeliverTR API v3.0 - Harita & Sipariş Sistemi"}

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