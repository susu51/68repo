"""
Business Dashboard Summary Endpoint
Provides real-time metrics and activities for business panel
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone, timedelta
from typing import Optional
import os

router = APIRouter()

# Timezone configuration
DEFAULT_TZ = "Europe/Istanbul"

# Status definitions for revenue calculation
REVENUE_STATUSES = os.getenv("CONFIRM_STATUSES", "confirmed,delivered").split(",")


def get_day_range(date_str: Optional[str] = None, tz: str = DEFAULT_TZ):
    """
    Get start and end of day in UTC for given date
    """
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        import pytz
        tz_info = pytz.timezone(tz)
    else:
        tz_info = ZoneInfo(tz)
    
    if date_str:
        target_date = datetime.fromisoformat(date_str)
    else:
        target_date = datetime.now(tz_info)
    
    # Start of day
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # End of day
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Convert to UTC for MongoDB query
    start_utc = start_of_day.astimezone(timezone.utc)
    end_utc = end_of_day.astimezone(timezone.utc)
    
    return start_utc, end_utc


@router.get("/business/dashboard/summary")
async def get_dashboard_summary(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    tz: str = Query(DEFAULT_TZ, description="Timezone"),
    current_user: dict = Depends(None)  # Will be replaced with actual auth
):
    """
    Get dashboard summary for business
    
    Returns:
    - today_orders_count: Number of orders today
    - today_revenue: Revenue today (only from confirmed/delivered)
    - pending_orders_count: Pending orders
    - menu_items_count: Active menu items
    - total_customers: Unique customers
    - rating_avg: Average rating
    - rating_count: Number of ratings
    - activities: Recent activities
    """
    from config.db import db
    from auth_dependencies import get_approved_business_user_from_cookie
    
    # Get authenticated business user
    current_user = await get_approved_business_user_from_cookie(current_user)
    business_id = current_user.get("id")
    
    if not business_id:
        raise HTTPException(status_code=400, detail="Business ID not found")
    
    # Get date range
    start_utc, end_utc = get_day_range(date, tz)
    
    # 1. Today's orders count (all statuses except cancelled)
    today_orders_count = await db.orders.count_documents({
        "business_id": business_id,
        "created_at": {"$gte": start_utc, "$lte": end_utc},
        "status": {"$in": ["pending", "preparing", "ready", "confirmed", "delivered"]}
    })
    
    # 2. Today's revenue (only confirmed/delivered orders)
    revenue_pipeline = [
        {
            "$match": {
                "business_id": business_id,
                "created_at": {"$gte": start_utc, "$lte": end_utc},
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
    
    # 3. Pending orders count (pending + preparing)
    pending_orders_count = await db.orders.count_documents({
        "business_id": business_id,
        "status": {"$in": ["pending", "preparing"]}
    })
    
    # 4. Menu items count (active only)
    menu_items_count = await db.menus.count_documents({
        "business_id": business_id,
        "is_available": True
    })
    
    # 5. Total unique customers (all time)
    customers_pipeline = [
        {
            "$match": {"business_id": business_id}
        },
        {
            "$group": {
                "_id": "$customer_id"
            }
        },
        {
            "$count": "total"
        }
    ]
    
    customers_result = await db.orders.aggregate(customers_pipeline).to_list(length=1)
    total_customers = customers_result[0]["total"] if customers_result else 0
    
    # 6. Ratings (if ratings collection exists)
    try:
        ratings_pipeline = [
            {
                "$match": {"business_id": business_id}
            },
            {
                "$group": {
                    "_id": None,
                    "avg": {"$avg": "$rating"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        ratings_result = await db.ratings.aggregate(ratings_pipeline).to_list(length=1)
        if ratings_result:
            rating_avg = round(ratings_result[0]["avg"], 1)
            rating_count = ratings_result[0]["count"]
        else:
            rating_avg = 0.0
            rating_count = 0
    except Exception:
        # Ratings collection doesn't exist yet
        rating_avg = 0.0
        rating_count = 0
    
    # 7. Recent activities (last 20)
    activities = []
    
    # Get recent orders
    recent_orders = await db.orders.find({
        "business_id": business_id
    }).sort("created_at", -1).limit(20).to_list(length=20)
    
    for order in recent_orders:
        activities.append({
            "type": "order_created",
            "title": f"Yeni sipariş alındı",
            "meta": {
                "order_code": order.get("order_code", "N/A"),
                "amount": order.get("totals", {}).get("grand", 0),
                "customer_name": order.get("customer_name", "Müşteri")
            },
            "ts": order.get("created_at").isoformat() if order.get("created_at") else None
        })
    
    # Sort activities by timestamp
    activities.sort(key=lambda x: x["ts"] or "", reverse=True)
    activities = activities[:20]  # Limit to 20
    
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
