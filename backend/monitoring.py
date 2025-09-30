"""
Production Monitoring and Logging Configuration
Handles Sentry integration, structured logging, and health checks
"""

import os
import time
import uuid
import logging
import json
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from datetime import datetime, timezone

# Configure structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging():
    """Configure structured logging"""
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # Application logger
    app_logger = logging.getLogger("kuryecini")
    app_logger.setLevel(logging.INFO)
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").handlers = []  # Disable default access logs
    logging.getLogger("uvicorn.error").handlers = []
    
    return app_logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Extract user info if available
        user_id = None
        if hasattr(request.state, 'current_user'):
            user_id = getattr(request.state.current_user, 'id', None)
        
        # Log request
        logger = logging.getLogger("kuryecini.requests")
        logger.info(
            f"Request started",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'method': request.method,
                'endpoint': str(request.url.path),
                'ip_address': request.client.host,
                'user_agent': request.headers.get('user-agent'),
                'query_params': str(request.query_params)
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'endpoint': str(request.url.path),
                    'status_code': response.status_code,
                    'duration_ms': round(duration, 2),
                    'ip_address': request.client.host
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    'request_id': request_id,
                    'user_id': user_id,
                    'endpoint': str(request.url.path),
                    'duration_ms': round(duration, 2),
                    'ip_address': request.client.host,
                    'error_type': type(e).__name__
                }
            )
            
            raise e

def setup_sentry():
    """Setup Sentry error tracking"""
    sentry_dsn = os.environ.get('SENTRY_DSN_BACKEND')
    
    if not sentry_dsn:
        logging.getLogger("kuryecini").warning("Sentry DSN not configured")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
            release=os.environ.get('SENTRY_RELEASE', 'v1.0.0'),
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% profiling
            integrations=[
                FastApiIntegration(auto_session_tracking=True),
                StarletteIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            ],
            before_send=filter_sentry_events
        )
        
        logging.getLogger("kuryecini").info("Sentry monitoring initialized")
        
    except ImportError:
        logging.getLogger("kuryecini").warning("Sentry SDK not installed")
    except Exception as e:
        logging.getLogger("kuryecini").error(f"Sentry initialization failed: {e}")

def filter_sentry_events(event, hint):
    """Filter out non-critical events from Sentry"""
    # Don't send health check 404s
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, HTTPException):
            if exc_value.status_code == 404 and '/healthz' in str(exc_value.detail):
                return None
    
    # Don't send rate limit errors
    if event.get('exception'):
        for exception in event['exception']['values']:
            if 'Rate limit exceeded' in exception.get('value', ''):
                return None
    
    return event

class HealthCheckService:
    """Service for monitoring application health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        current_time = time.time()
        uptime_seconds = current_time - self.start_time
        
        # Check database connection
        db_status = await self._check_database()
        
        # Check external services
        external_services = await self._check_external_services()
        
        # Calculate error rate
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        
        status = {
            "status": "healthy" if db_status and error_rate < 5 else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(uptime_seconds, 2),
            "version": os.environ.get('SENTRY_RELEASE', 'v1.0.0'),
            "environment": os.environ.get('ENVIRONMENT', 'production'),
            "checks": {
                "database": "healthy" if db_status else "unhealthy",
                "external_services": external_services,
                "error_rate_percent": round(error_rate, 2),
                "request_count": self.request_count
            },
            "system": {
                "memory_usage": await self._get_memory_usage(),
                "disk_usage": await self._get_disk_usage()
            }
        }
        
        return status
    
    async def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # TODO: Implement actual database ping
            # from motor.motor_asyncio import AsyncIOMotorClient
            # client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
            # await client.admin.command('ping')
            return True
        except Exception as e:
            logging.getLogger("kuryecini.health").error(f"Database health check failed: {e}")
            return False
    
    async def _check_external_services(self) -> Dict[str, str]:
        """Check external service connectivity"""
        services = {}
        
        # Check OSM tiles
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('https://tile.openstreetmap.org/1/1/1.png') as response:
                    services['openstreetmap'] = 'healthy' if response.status == 200 else 'degraded'
        except Exception:
            services['openstreetmap'] = 'unhealthy'
        
        # TODO: Add more external service checks (payment gateway, SMS provider, etc.)
        
        return services
    
    async def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / 1024**3, 2),
                "available_gb": round(memory.available / 1024**3, 2),
                "used_percent": memory.percent
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    async def _get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage statistics"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                "total_gb": round(disk.total / 1024**3, 2),
                "free_gb": round(disk.free / 1024**3, 2),
                "used_percent": round((disk.used / disk.total) * 100, 2)
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    def increment_request_count(self):
        """Increment total request counter"""
        self.request_count += 1
    
    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1

# Global health service instance
health_service = HealthCheckService()

def setup_monitoring(app):
    """Setup comprehensive monitoring for the FastAPI app"""
    # Setup structured logging
    setup_logging()
    
    # Setup Sentry error tracking
    setup_sentry()
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add health check endpoints
    from fastapi import APIRouter
    
    monitoring_router = APIRouter()
    
    @monitoring_router.get("/healthz")
    async def health_check():
        """Basic health check endpoint"""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    @monitoring_router.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with system information"""
        return await health_service.get_health_status()
    
    @monitoring_router.get("/metrics")
    async def get_metrics():
        """Basic metrics endpoint"""
        return {
            "requests_total": health_service.request_count,
            "errors_total": health_service.error_count,
            "uptime_seconds": time.time() - health_service.start_time
        }
    
    app.include_router(monitoring_router)
    
    logging.getLogger("kuryecini").info("Monitoring setup completed")

# Uptime monitoring ping function
async def uptime_ping():
    """Send uptime ping to monitoring service"""
    ping_url = os.environ.get('UPTIME_PING_URL')
    
    if not ping_url:
        return
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(ping_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logging.getLogger("kuryecini.uptime").debug("Uptime ping successful")
                else:
                    logging.getLogger("kuryecini.uptime").warning(f"Uptime ping failed: {response.status}")
    except Exception as e:
        logging.getLogger("kuryecini.uptime").error(f"Uptime ping error: {e}")

# Background task for periodic uptime pings
async def start_uptime_monitoring():
    """Start background uptime monitoring"""
    if not os.environ.get('UPTIME_PING_URL'):
        return
    
    while True:
        try:
            await uptime_ping()
            await asyncio.sleep(300)  # Ping every 5 minutes
        except Exception as e:
            logging.getLogger("kuryecini.uptime").error(f"Uptime monitoring error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error