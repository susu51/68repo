"""
Order Code Generator
Format: KC-YYYYMMDD-XXXXXX (6-digit base36 random)
"""
import random
import string
from datetime import datetime

def generate_order_code() -> str:
    """
    Generate unique order code in format: KC-YYYYMMDD-XXXXXX
    Example: KC-20251021-3F2A9B
    """
    date_part = datetime.now().strftime("%Y%m%d")
    
    # Generate 6-character random code (base36: 0-9, A-Z)
    chars = string.digits + string.ascii_uppercase
    random_part = ''.join(random.choices(chars, k=6))
    
    return f"KC-{date_part}-{random_part}"


async def generate_unique_order_code(db) -> str:
    """
    Generate unique order code with collision check
    Retries up to 5 times if collision occurs
    """
    max_attempts = 5
    
    for attempt in range(max_attempts):
        code = generate_order_code()
        
        # Check if code already exists
        existing = await db.orders.find_one({"order_code": code})
        
        if not existing:
            return code
    
    # Fallback: add timestamp microseconds if all attempts failed
    timestamp = datetime.now().strftime("%H%M%S%f")[:8]
    return f"KC-{datetime.now().strftime('%Y%m%d')}-{timestamp}"
