"""
AI Diagnostics Models & PII Redaction - Phase 1
Log ingestion, clustering, and privacy protection
"""
import re
import hashlib
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

class AppType(str, Enum):
    CUSTOMER = "customer"
    BUSINESS = "business"
    COURIER = "courier"
    ADMIN = "admin"

class AILog(BaseModel):
    id: str
    app: AppType
    level: LogLevel
    ts: datetime
    route: Optional[str] = None
    code_location: Optional[str] = None
    message: str
    stack: Optional[str] = None
    meta: dict = {}
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    redacted: bool = False
    fingerprint: str
    deployment: str = "prod"
    tags: List[str] = []

class AICluster(BaseModel):
    id: str
    fingerprint: str
    title: str
    sample_message: str
    top_stack: Optional[str] = None
    apps: List[str] = []
    first_seen: datetime
    last_seen: datetime
    severity: str  # "low", "med", "high", "critical"
    count_24h: int = 0
    affected_users: int = 0
    rca_summary: Optional[str] = None
    suggested_fix: Optional[str] = None

class LogIngestRequest(BaseModel):
    level: str
    message: str
    route: Optional[str] = None
    code_location: Optional[str] = None
    stack: Optional[str] = None
    meta: dict = {}
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = []
    deployment: str = "prod"

# PII Redaction Patterns
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b(\+90|0)?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b'),
    'iban': re.compile(r'\bTR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b', re.IGNORECASE),
    'jwt': re.compile(r'\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b'),
    'auth_header': re.compile(r'\bAuthorization:\s*Bearer\s+[A-Za-z0-9-_.]+', re.IGNORECASE),
    'coordinates': re.compile(r'\b\d{1,3}\.\d{6,}\b'),  # Precise GPS coords
    'card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'address_number': re.compile(r'\b(No:|Numara:|Apt:|Daire:)\s*\d+\b', re.IGNORECASE)
}

def redact_pii(text: str) -> str:
    """
    Redact PII from text
    Returns redacted text with ***REDACTED*** placeholders
    """
    if not text:
        return text
    
    redacted = text
    
    # Apply all redaction patterns
    for pattern_name, pattern in PII_PATTERNS.items():
        redacted = pattern.sub('***REDACTED***', redacted)
    
    return redacted

def compute_fingerprint(message: str, stack: Optional[str], route: Optional[str]) -> str:
    """
    Compute fingerprint for clustering similar errors
    Uses: message template + top 3 stack frames + route
    """
    components = []
    
    # Message template (remove specific values)
    msg_template = re.sub(r'\d+', 'N', message)
    msg_template = re.sub(r'[a-f0-9-]{32,}', 'ID', msg_template)
    components.append(msg_template[:100])
    
    # Top 3 stack frames if available
    if stack:
        lines = stack.split('\n')[:3]
        stack_summary = ' '.join(lines)
        # Remove line numbers
        stack_summary = re.sub(r':\d+', ':N', stack_summary)
        components.append(stack_summary)
    
    # Route
    if route:
        components.append(route)
    
    # Generate hash
    fingerprint_str = '|'.join(components)
    return hashlib.md5(fingerprint_str.encode()).hexdigest()[:16]

def classify_severity(level: str, message: str, stack: Optional[str]) -> str:
    """
    Classify error severity
    Returns: "low", "med", "high", "critical"
    """
    level_upper = level.upper()
    message_lower = message.lower()
    
    # Critical patterns
    if any(word in message_lower for word in ['database', 'mongo', 'connection pool', 'out of memory', 'oom']):
        return "critical"
    
    if level_upper == "ERROR" and stack and len(stack) > 500:
        return "high"
    
    if level_upper == "ERROR":
        return "med"
    
    if level_upper == "WARN":
        return "low"
    
    return "low"

def extract_tags(message: str, route: Optional[str], meta: dict) -> List[str]:
    """
    Extract relevant tags from log entry
    """
    tags = []
    
    # Route-based tags
    if route:
        if '/orders' in route:
            tags.append('orders')
        if '/auth' in route or '/login' in route:
            tags.append('auth')
        if '/payment' in route:
            tags.append('payments')
        if '/map' in route or '/coords' in route:
            tags.append('map')
        if '/business' in route:
            tags.append('business')
        if '/courier' in route:
            tags.append('courier')
    
    # Message-based tags
    message_lower = message.lower()
    if 'websocket' in message_lower or 'ws' in message_lower:
        tags.append('websocket')
    if 'redis' in message_lower or 'cache' in message_lower:
        tags.append('cache')
    if 'mongo' in message_lower or 'database' in message_lower:
        tags.append('database')
    
    return list(set(tags))
