"""
Business Dashboard Summary Endpoint
Provides real-time metrics and activities for business panel
"""
from fastapi import APIRouter, HTTPException, Query, Request
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os

router = APIRouter()

# Timezone configuration
DEFAULT_TZ = "Europe/Istanbul"
REVENUE_STATUSES = os.getenv("CONFIRM_STATUSES", "confirmed,delivered").split(",")


# Response Models
class ActivityItem(BaseModel):
    type: str
    title: str
    meta: Dict[str, Any]
    ts: Optional[str]


class DashboardSummaryResponse(BaseModel):
    business_id: str
    date: str
    today_orders_count: int
    today_revenue: float
    pending_orders_count: int
    menu_items_count: int
    total_customers: int
    rating_avg: float
    rating_count: int
    activities: List[ActivityItem]


@router.get("/business/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    request: Request,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    tz: str = Query(DEFAULT_TZ, description="Timezone")
):
    """
    Get dashboard summary for business
    """
    from config.db import db
    from auth_cookie import get_current_user_from_cookie_or_bearer
    
    # Get authenticated user
    current_user = await get_current_user_from_cookie_or_bearer(request)
    
    if current_user.get("role") != "business":
        raise HTTPException(status_code=403, detail="Business access required")
    
    if current_user.get("kyc_status") != "approved":
        raise HTTPException(status_code=403, detail="KYC approval required")
    
    business_id = current_user.get("id")
    
    # Get date range (simplified - just use UTC for now)
    if date:
        target_date = datetime.fromisoformat(date)
    else:
        target_date = datetime.now(timezone.utc)
    
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 1. Today's orders count
    today_orders_count = await db.orders.count_documents({
        "business_id": business_id,
        "created_at": {"$gte": start_of_day, "$lte": end_of_day},
        "status": {"$in": ["pending", "preparing", "ready", "confirmed", "delivered"]}
    })
    
    # 2. Today's revenue
    revenue_pipeline = [
        {
            "$match": {
                "business_id": business_id,
                "created_at": {"$gte": start_of_day, "$lte": end_of_day},
                "status": {"$in": REVENUE_STATUSES}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$totals.grand"}
            }
        }
    ]
    
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(length=1)
    today_revenue = revenue_result[0]["total"] if revenue_result else 0.0
    
    # 3. Pending orders count
    pending_orders_count = await db.orders.count_documents({
        "business_id": business_id,
        "status": {"$in": ["pending", "preparing"]}
    })
    
    # 4. Menu items count
    menu_items_count = await db.menus.count_documents({
        "business_id": business_id,
        "is_available": True
    })
    
    # 5. Total unique customers
    customers_pipeline = [
        {"$match": {"business_id": business_id}},
        {"$group": {"_id": "$customer_id"}},
        {"$count": "total"}
    ]
    
    customers_result = await db.orders.aggregate(customers_pipeline).to_list(length=1)
    total_customers = customers_result[0]["total"] if customers_result else 0
    
    # 6. Ratings
    rating_avg = 0.0
    rating_count = 0
    
    # 7. Recent activities
    activities = []
    recent_orders = await db.orders.find({
        "business_id": business_id
    }).sort("created_at", -1).limit(20).to_list(length=20)
    
    for order in recent_orders:
        created_at = order.get("created_at")
        activities.append({
            "type": "order_created",
            "title": "Yeni sipariş alındı",
            "meta": {
                "order_code": order.get("order_code", "N/A"),
                "amount": order.get("totals", {}).get("grand", 0),
                "customer_name": order.get("customer_name", "Müşteri")
            },
            "ts": created_at.isoformat() if created_at else None
        })
    
    activities.sort(key=lambda x: x["ts"] or "", reverse=True)
    activities = activities[:20]
    
    return {
        "business_id": business_id,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "today_orders_count": today_orders_count,
        "today_revenue": round(today_revenue, 2),
        "pending_orders_count": pending_orders_count,
        "menu_items_count": menu_items_count,
        "total_customers": total_customers,
        "rating_avg": rating_avg,
        "rating_count": rating_count,
        "activities": activities
    }
