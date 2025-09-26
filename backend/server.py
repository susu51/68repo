from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import shutil
import json

# Import our new services and models
from config import settings
from auth_service import AuthService
from otp_service import OTPService
from sms_service import sms_service
from models import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Global service instances
auth_service = None
otp_service = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# Cleanup task
async def cleanup_task():
    """Background task for cleaning up expired records"""
    while True:
        try:
            if otp_service:
                await otp_service.cleanup_expired_otps()
            if auth_service:
                await auth_service.cleanup_expired_tokens()
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        
        # Run cleanup every 5 minutes
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global auth_service, otp_service
    
    # Startup
    logger.info("Starting DeliverTR API...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client.get_database()
    
    # Initialize services
    auth_service = AuthService(db)
    otp_service = OTPService(db)
    
    # Create database indexes
    await auth_service.create_indexes()
    await otp_service.create_indexes()
    
    # Start cleanup task
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    logger.info("DeliverTR API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DeliverTR API...")
    cleanup_task_handle.cancel()
    client.close()

# Create FastAPI app
app = FastAPI(
    title="DeliverTR API",
    description="Turkish Delivery Platform with Phone/SMS OTP Authentication",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# API Router
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    try:
        # Verify access token
        payload = await auth_service.verify_access_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user data
        user_id = payload.get("sub")
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_courier_user(current_user: dict = Depends(get_current_user)):
    """Require courier role"""
    if current_user.get("role") != "courier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Courier access required"
        )
    return current_user

async def get_business_user(current_user: dict = Depends(get_current_user)):
    """Require business role"""
    if current_user.get("role") != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business access required"
        )
    return current_user

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers first (for reverse proxy setups)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection IP
    return request.client.host if request.client else "127.0.0.1"

# Authentication Endpoints
@api_router.post("/auth/otp/request", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequestModel,
    request: Request
):
    """
    Request OTP for phone number authentication
    Rate limited: 2 requests per minute per phone, 30 per minute per IP
    """
    try:
        client_ip = get_client_ip(request)
        
        result = await otp_service.generate_and_send_otp(
            phone=otp_request.phone,
            ip_address=client_ip,
            device_id=otp_request.device_id
        )
        
        return OTPResponse(**result)
        
    except Exception as e:
        logger.error(f"OTP request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS gönderimi başarısız oldu"
        )

@api_router.post("/auth/otp/verify", response_model=TokenResponse)
async def verify_otp(
    otp_verify: OTPVerifyModel,
    request: Request
):
    """
    Verify OTP and authenticate user
    Returns JWT access and refresh tokens
    """
    try:
        client_ip = get_client_ip(request)
        
        # Verify OTP
        verify_result = await otp_service.verify_otp(
            phone=otp_verify.phone,
            otp_code=otp_verify.otp,
            ip_address=client_ip
        )
        
        if not verify_result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verify_result['message']
            )
        
        # Authenticate user (create or login)
        auth_result = await auth_service.authenticate_user(
            phone=sms_service.format_turkish_phone(otp_verify.phone),
            otp_verified=verify_result['verified']
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Kullanıcı girişi başarısız oldu"
            )
        
        return TokenResponse(
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"],
            token_type=auth_result["token_type"],
            expires_in=auth_result["expires_in"],
            user_type=auth_result["user"]["role"],
            user_data=auth_result["user"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doğrulama başarısız oldu"
        )

@api_router.post("/auth/refresh")
async def refresh_token(token_request: RefreshTokenModel):
    """Refresh access token using refresh token"""
    try:
        result = await auth_service.refresh_access_token(token_request.refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token yenileme başarısız oldu"
        )

@api_router.post("/auth/logout")
async def logout(
    token_request: RefreshTokenModel,
    current_user: dict = Depends(get_current_user)
):
    """Logout user by revoking refresh token"""
    try:
        success = await auth_service.logout_user(token_request.refresh_token)
        
        return APIResponse(
            success=success,
            message="Çıkış yapıldı" if success else "Çıkış yaparken hata oluştu"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return APIResponse(
            success=False,
            message="Çıkış yaparken hata oluştu"
        )

# User Profile Endpoints
@api_router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

@api_router.patch("/me")
async def update_profile(
    user_update: UserUpdateModel,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        update_data = user_update.dict(exclude_unset=True)
        success = await auth_service.update_user(current_user["id"], update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profil güncellemesi başarısız oldu"
            )
        
        return APIResponse(
            success=True,
            message="Profil güncellendi"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil güncellemesi başarısız oldu"
        )

# Role Registration Endpoints (requires phone verification first)
@api_router.post("/register/courier")
async def register_courier(
    courier_data: CourierRegistrationModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Register as courier (requires verified phone number)
    """
    try:
        # Verify phone number matches current user
        formatted_phone = sms_service.format_turkish_phone(courier_data.phone)
        if formatted_phone != current_user.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon numarası doğrulanmamış"
            )
        
        # Check if user is already a courier
        if current_user.get("role") == "courier":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zaten kurye olarak kayıtlısınız"
            )
        
        # Update user data
        update_data = courier_data.dict()
        update_data["role"] = "courier"
        update_data["kyc_status"] = "pending"
        update_data["profile_completed"] = True
        update_data["balance"] = 0.0
        update_data["is_online"] = False
        
        success = await auth_service.update_user(current_user["id"], update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Kurye kaydı başarısız oldu"
            )
        
        return APIResponse(
            success=True,
            message="Kurye kaydınız tamamlandı. KYC onayı bekliyor."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Courier registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kurye kaydı başarısız oldu"
        )

@api_router.post("/register/business")
async def register_business(
    business_data: BusinessRegistrationModel,
    current_user: dict = Depends(get_current_user)
):
    """Register as business (requires verified phone number)"""
    try:
        # Verify phone number matches current user
        formatted_phone = sms_service.format_turkish_phone(business_data.phone)
        if formatted_phone != current_user.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon numarası doğrulanmamış"
            )
        
        # Check if user is already a business
        if current_user.get("role") == "business":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zaten işletme olarak kayıtlısınız"
            )
        
        # Update user data
        update_data = business_data.dict()
        update_data["role"] = "business"
        update_data["profile_completed"] = True
        update_data["is_active"] = True
        
        success = await auth_service.update_user(current_user["id"], update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="İşletme kaydı başarısız oldu"
            )
        
        return APIResponse(
            success=True,
            message="İşletme kaydınız tamamlandı"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Business registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İşletme kaydı başarısız oldu"
        )

@api_router.post("/register/customer")
async def register_customer(
    customer_data: CustomerRegistrationModel,
    current_user: dict = Depends(get_current_user)
):
    """Register as customer (requires verified phone number)"""
    try:
        # Verify phone number matches current user
        formatted_phone = sms_service.format_turkish_phone(customer_data.phone)
        if formatted_phone != current_user.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon numarası doğrulanmamış"
            )
        
        # Update user data (customer is default role, so just complete profile)
        update_data = customer_data.dict()
        update_data["role"] = "customer"
        update_data["profile_completed"] = True
        
        success = await auth_service.update_user(current_user["id"], update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Müşteri kaydı başarısız oldu"
            )
        
        return APIResponse(
            success=True,
            message="Müşteri kaydınız tamamlandı"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Müşteri kaydı başarısız oldu"
        )

# File Upload Endpoint
@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload file (images, documents)"""
    try:
        # Validate file type
        allowed_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'image/heic', 'image/heif'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Desteklenmeyen dosya türü"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya boyutu çok büyük (max 10MB)"
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dosya yükleme başarısız oldu"
        )

# Development/Debug Endpoints
@api_router.get("/debug/mock-otp/{phone}")
async def get_mock_otp(phone: str):
    """Get mock OTP for development (only works in mock mode)"""
    if not settings.sms_mock_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not available in production mode"
        )
    
    formatted_phone = sms_service.format_turkish_phone(phone)
    if not formatted_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    mock_otp = sms_service.get_mock_otp(formatted_phone)
    
    return {
        "phone": formatted_phone,
        "mock_otp": mock_otp,
        "available": mock_otp is not None
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "2.0.0",
        "features": {
            "phone_auth": settings.auth_phone_sms,
            "email_auth": settings.auth_email_login,
            "sms_mock_mode": settings.sms_mock_mode
        }
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo the message back (you can customize this)
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include API router
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "DeliverTR API v2.0 - Phone/SMS OTP Authentication",
        "documentation": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )