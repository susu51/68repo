"""
Logging configuration for Kuryecini backend
Production-ready logging with structured JSON format
"""

import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request, Response
import time

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging():
    """Setup logging configuration"""
    
    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Set formatter based on environment
    if os.getenv("ENVIRONMENT") == "production":
        # JSON format for production
        json_formatter = JSONFormatter()
        console_handler.setFormatter(json_formatter)
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Kuryecini specific loggers
    logging.getLogger("kuryecini.auth").setLevel(logging.INFO)
    logging.getLogger("kuryecini.orders").setLevel(logging.INFO)
    logging.getLogger("kuryecini.business").setLevel(logging.INFO)
    logging.getLogger("kuryecini.courier").setLevel(logging.INFO)
    logging.getLogger("kuryecini.admin").setLevel(logging.INFO)

class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: Any, kwargs: Dict[str, Any]) -> tuple:
        kwargs['extra'] = {**self.extra, **kwargs.get('extra', {})}
        return msg, kwargs

# Request context logger
class RequestLogger:
    """Logger for request/response tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.requests")
    
    def log_request(
        self,
        request: Request,
        response: Response,
        process_time: float,
        user_id: Optional[str] = None,
        **extra_fields
    ):
        """Log request details"""
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id,
            **extra_fields
        }
        
        # Remove sensitive data from logs
        if "password" in str(request.url).lower():
            log_data["query_params"] = "***REDACTED***"
        
        level = logging.INFO
        if response.status_code >= 400:
            level = logging.WARNING
        if response.status_code >= 500:
            level = logging.ERROR
            
        self.logger.log(level, f"{request.method} {request.url.path}", extra={
            "extra_fields": log_data
        })

# Business logic loggers
class AuthLogger:
    """Logger for authentication events"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.auth")
    
    def log_login_attempt(self, email: str, success: bool, ip_address: str, **extra):
        """Log login attempt"""
        self.logger.info(
            f"Login attempt: {email} - {'SUCCESS' if success else 'FAILED'}",
            extra={
                "extra_fields": {
                    "event": "login_attempt",
                    "email": email,
                    "success": success,
                    "ip_address": ip_address,
                    **extra
                }
            }
        )
    
    def log_registration(self, email: str, role: str, ip_address: str):
        """Log user registration"""
        self.logger.info(
            f"User registration: {email} as {role}",
            extra={
                "extra_fields": {
                    "event": "user_registration",
                    "email": email,
                    "role": role,
                    "ip_address": ip_address
                }
            }
        )
    
    def log_token_refresh(self, user_id: str, ip_address: str):
        """Log token refresh"""
        self.logger.info(
            f"Token refresh for user: {user_id}",
            extra={
                "extra_fields": {
                    "event": "token_refresh",
                    "user_id": user_id,
                    "ip_address": ip_address
                }
            }
        )

class OrderLogger:
    """Logger for order events"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.orders")
    
    def log_order_created(self, order_id: str, customer_id: str, business_id: str, total_amount: float):
        """Log order creation"""
        self.logger.info(
            f"Order created: {order_id}",
            extra={
                "extra_fields": {
                    "event": "order_created",
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "business_id": business_id,
                    "total_amount": total_amount
                }
            }
        )
    
    def log_order_status_change(self, order_id: str, old_status: str, new_status: str, user_id: str):
        """Log order status change"""
        self.logger.info(
            f"Order {order_id} status: {old_status} -> {new_status}",
            extra={
                "extra_fields": {
                    "event": "order_status_change",
                    "order_id": order_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "changed_by": user_id
                }
            }
        )
    
    def log_payment_processed(self, order_id: str, amount: float, payment_method: str, success: bool):
        """Log payment processing"""
        self.logger.info(
            f"Payment for order {order_id}: {amount}₺ - {'SUCCESS' if success else 'FAILED'}",
            extra={
                "extra_fields": {
                    "event": "payment_processed",
                    "order_id": order_id,
                    "amount": amount,
                    "payment_method": payment_method,
                    "success": success
                }
            }
        )

class BusinessLogger:
    """Logger for business events"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.business")
    
    def log_kyc_status_change(self, business_id: str, old_status: str, new_status: str, admin_id: str):
        """Log business KYC status change"""
        self.logger.info(
            f"Business {business_id} KYC: {old_status} -> {new_status}",
            extra={
                "extra_fields": {
                    "event": "business_kyc_change",
                    "business_id": business_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "admin_id": admin_id
                }
            }
        )
    
    def log_menu_updated(self, business_id: str, product_count: int):
        """Log menu update"""
        self.logger.info(
            f"Menu updated for business {business_id}: {product_count} products",
            extra={
                "extra_fields": {
                    "event": "menu_updated",
                    "business_id": business_id,
                    "product_count": product_count
                }
            }
        )

class CourierLogger:
    """Logger for courier events"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.courier")
    
    def log_courier_online(self, courier_id: str, location: Dict[str, float]):
        """Log courier going online"""
        self.logger.info(
            f"Courier {courier_id} went online",
            extra={
                "extra_fields": {
                    "event": "courier_online",
                    "courier_id": courier_id,
                    "location": location
                }
            }
        )
    
    def log_delivery_completed(self, order_id: str, courier_id: str, delivery_time_minutes: int):
        """Log delivery completion"""
        self.logger.info(
            f"Delivery completed: Order {order_id} by courier {courier_id} in {delivery_time_minutes} minutes",
            extra={
                "extra_fields": {
                    "event": "delivery_completed",
                    "order_id": order_id,
                    "courier_id": courier_id,
                    "delivery_time_minutes": delivery_time_minutes
                }
            }
        )

class AdminLogger:
    """Logger for admin events"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.admin")
    
    def log_config_change(self, admin_id: str, config_key: str, old_value: Any, new_value: Any):
        """Log system configuration change"""
        self.logger.info(
            f"Config changed: {config_key} by admin {admin_id}",
            extra={
                "extra_fields": {
                    "event": "config_change",
                    "admin_id": admin_id,
                    "config_key": config_key,
                    "old_value": str(old_value),
                    "new_value": str(new_value)
                }
            }
        )
    
    def log_user_action(self, admin_id: str, action: str, target_user_id: str, details: Dict[str, Any]):
        """Log admin action on user"""
        self.logger.info(
            f"Admin action: {action} on user {target_user_id} by {admin_id}",
            extra={
                "extra_fields": {
                    "event": "admin_user_action",
                    "admin_id": admin_id,
                    "action": action,
                    "target_user_id": target_user_id,
                    "details": details
                }
            }
        )

# Performance monitoring logger
class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger("kuryecini.performance")
    
    def log_slow_query(self, query: str, execution_time_ms: float, threshold_ms: float = 1000):
        """Log slow database queries"""
        if execution_time_ms > threshold_ms:
            self.logger.warning(
                f"Slow query detected: {execution_time_ms:.2f}ms",
                extra={
                    "extra_fields": {
                        "event": "slow_query",
                        "query": query[:200],  # Truncate long queries
                        "execution_time_ms": execution_time_ms,
                        "threshold_ms": threshold_ms
                    }
                }
            )
    
    def log_memory_usage(self, memory_mb: float, threshold_mb: float = 1024):
        """Log high memory usage"""
        if memory_mb > threshold_mb:
            self.logger.warning(
                f"High memory usage: {memory_mb:.2f}MB",
                extra={
                    "extra_fields": {
                        "event": "high_memory_usage",
                        "memory_mb": memory_mb,
                        "threshold_mb": threshold_mb
                    }
                }
            )

# Initialize loggers
def get_loggers():
    """Get all configured loggers"""
    return {
        "request": RequestLogger(),
        "auth": AuthLogger(),
        "order": OrderLogger(),
        "business": BusinessLogger(),
        "courier": CourierLogger(),
        "admin": AdminLogger(),
        "performance": PerformanceLogger()
    }

# Health check logger
def log_health_check(endpoint: str, response_time_ms: float, status: str):
    """Log health check results"""
    logger = logging.getLogger("kuryecini.health")
    logger.info(
        f"Health check: {endpoint} - {status} ({response_time_ms:.2f}ms)",
        extra={
            "extra_fields": {
                "event": "health_check",
                "endpoint": endpoint,
                "response_time_ms": response_time_ms,
                "status": status
            }
        }
    )

# Setup logging on import
setup_logging()