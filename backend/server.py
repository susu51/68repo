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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client.delivertr_database

# Create uploads directory
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create the main app without a prefix
app = FastAPI(title="DeliverTR API", description="Türkiye Teslimat Platformu - Email Authentication")

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'delivertr-secret-key-2024')
ALGORITHM = "HS256"
security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    return user

# Authentication Endpoints
@api_router.post("/auth/login")
async def login(login_data: LoginRequest):
    """Login with email and password"""
    user = await db.users.find_one({"email": login_data.email})
    
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    # Convert ObjectId to string for response
    user["id"] = str(user["_id"])
    del user["_id"]
    del user["password"]  # Don't send password in response
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user["role"],
        "user_data": user
    }
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        
        # Get user from database to check current status
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
        
        if user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Hesabınız askıya alınmış")
        
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin yetkisi kontrolü"""
    user_id = await get_current_user(credentials)
    user = await db.users.find_one({"id": user_id})
    
    if not user or user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    return user_id

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

class BusinessRegister(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    tax_number: str
    address: str
    city: str
    business_category: str
    description: Optional[str] = None

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

# EXISTING AUTH ENDPOINTS (keeping previous implementation)
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: UserLogin, request: Request):
    """Kullanıcı girişi"""
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="E-posta veya şifre yanlış")
    
    # Log login attempt
    await log_action(
        action_type="login",
        target_type="user",
        target_id=user["id"],
        user_id=user["id"],
        ip_address=request.client.host,
        description=f"User login: {user['email']}",
        user_agent=request.headers.get("user-agent", "")
    )
    
    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    user_data = {"email": user["email"], "user_type": user["user_type"]}
    
    if user["user_type"] == "courier":
        courier = await db.couriers.find_one({"user_id": user["id"]})
        if courier:
            balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
            user_data.update({
                "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}",
                "kyc_status": courier.get("kyc_status", "pending"),
                "city": courier.get("city", ""),
                "is_online": courier.get("is_online", False),
                "balance": balance.get("available_balance", 0) if balance else 0,
                "status": user.get("status", "active")
            })
    elif user["user_type"] == "business":
        business = await db.businesses.find_one({"user_id": user["id"]})
        if business:
            user_data.update({
                "business_id": business["id"],
                "business_name": business.get("business_name", ""),
                "city": business.get("city", ""),
                "category": business.get("business_category", ""),
                "is_approved": user.get("is_active", False),
                "status": user.get("status", "active")
            })
    elif user["user_type"] == "customer":
        customer = await db.customers.find_one({"user_id": user["id"]})
        if customer:
            user_data.update({
                "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}",
                "city": customer.get("city", ""),
                "status": user.get("status", "active")
            })
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_type=user["user_type"],
        user_data=user_data
    )

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

# ADMIN USER MANAGEMENT ENDPOINTS
@api_router.get("/admin/users")
async def get_all_users(
    user_type: Optional[str] = None,
    status: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user_id: str = Depends(get_admin_user)
):
    """Tüm kullanıcıları listele"""
    query = {}
    if user_type:
        query["user_type"] = user_type
    if status:
        query["status"] = status
    
    skip = (page - 1) * limit
    users = await db.users.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(length=None)
    total_count = await db.users.count_documents(query)
    
    # Enrich user data
    enriched_users = []
    for user in users:
        user_info = {
            "id": user["id"],
            "email": user["email"],
            "user_type": user["user_type"],
            "status": user.get("status", "active"),
            "created_at": user["created_at"],
            "last_login": user.get("last_login")
        }
        
        if user["user_type"] == "courier":
            courier = await db.couriers.find_one({"user_id": user["id"]})
            if courier:
                balance = await db.courier_balances.find_one({"courier_id": courier["id"]})
                user_info.update({
                    "name": f"{courier['first_name']} {courier['last_name']}",
                    "city": courier["city"],
                    "vehicle_type": courier["vehicle_type"],
                    "kyc_status": courier["kyc_status"],
                    "is_online": courier.get("is_online", False),
                    "total_deliveries": balance.get("total_deliveries", 0) if balance else 0,
                    "total_earnings": balance.get("total_earnings", 0) if balance else 0
                })
        elif user["user_type"] == "business":
            business = await db.businesses.find_one({"user_id": user["id"]})
            if business:
                user_info.update({
                    "business_name": business["business_name"],
                    "city": business["city"],
                    "category": business["business_category"],
                    "is_open": business.get("is_open", False)
                })
        elif user["user_type"] == "customer":
            customer = await db.customers.find_one({"user_id": user["id"]})
            if customer:
                user_info.update({
                    "name": f"{customer['first_name']} {customer['last_name']}",
                    "city": customer["city"]
                })
        
        enriched_users.append(user_info)
    
    return {
        "users": enriched_users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": math.ceil(total_count / limit)
        }
    }

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
async def get_system_configurations(current_user_id: str = Depends(get_admin_user)):
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
    current_user_id: str = Depends(get_admin_user)
):
    """Sistem konfigürasyonu güncelle"""
    old_config = await db.system_configs.find_one({"key": config_key})
    old_value = old_config.get("value") if old_config else None
    
    await set_system_config(config_key, config_value, current_user_id, description)
    
    # Log configuration change
    await log_action(
        action_type="config_update",
        target_type="system_config",
        target_id=config_key,
        user_id=current_user_id,
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

# Test endpoint
@api_router.get("/")
async def root():
    return {"message": "DeliverTR API v5.0 - Kapsamlı Admin & Yönetim Sistemi"}

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