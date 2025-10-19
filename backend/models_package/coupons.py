"""
Coupon Model - Phase 3
Represents discount coupons for items or cart
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CouponType(str, Enum):
    PERCENT = "percent"  # Percentage discount (e.g., 10%)
    FIXED = "fixed"      # Fixed amount discount (e.g., ₺10)

class CouponScope(str, Enum):
    ITEM = "item"   # Applied to individual items
    CART = "cart"   # Applied to cart total

class Coupon(BaseModel):
    id: str
    code: str
    title: str
    description: str
    type: CouponType
    scope: CouponScope
    value: float  # Percentage (10 = 10%) or fixed amount (10 = ₺10)
    min_basket: Optional[float] = None  # Minimum basket amount required
    valid_from: datetime
    valid_to: datetime
    per_user_limit: Optional[int] = None  # Max uses per user
    global_limit: Optional[int] = None    # Max total uses
    current_uses: int = 0
    applicable_restaurants: List[str] = []  # Empty = all restaurants
    applicable_categories: List[str] = []   # Empty = all categories
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class CouponCreate(BaseModel):
    code: str
    title: str
    description: str
    type: CouponType
    scope: CouponScope
    value: float
    min_basket: Optional[float] = None
    valid_from: datetime
    valid_to: datetime
    per_user_limit: Optional[int] = None
    global_limit: Optional[int] = None
    applicable_restaurants: List[str] = []
    applicable_categories: List[str] = []
    is_active: bool = True

class CouponUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    min_basket: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    per_user_limit: Optional[int] = None
    global_limit: Optional[int] = None
    applicable_restaurants: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ApplyCouponRequest(BaseModel):
    code: str
    
class ApplyCouponResponse(BaseModel):
    success: bool
    message: str
    coupon_id: Optional[str] = None
    discount_amount: float = 0
    items: List[dict] = []
    totals: dict = {}
