"""
Content Management Routes for Kuryecini Platform
Phase 2: Content Blocks and Media Assets Management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from auth_dependencies import get_admin_user
import os

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
if MONGO_URL:
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(MONGO_URL)
    # Extract database name from MONGO_URL or environment
    db_name = os.environ.get("DB_NAME")
    if not db_name:
        if "/" in MONGO_URL:
            db_name = MONGO_URL.split("/")[-1].split("?")[0]
        else:
            db_name = "kuryecini"
    db = client[db_name]
else:
    raise RuntimeError("MONGO_URL environment variable required")

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/blocks")
async def get_content_blocks():
    """Get all content blocks (public endpoint)"""
    try:
        blocks = await db.content_blocks.find().to_list(length=None)
        return blocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching content blocks: {str(e)}")

@router.get("/blocks/{block_id}")
async def get_content_block(block_id: str):
    """Get specific content block by ID (public endpoint)"""
    try:
        block = await db.content_blocks.find_one({"_id": block_id})
        if not block:
            raise HTTPException(status_code=404, detail="Content block not found")
        return block
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching content block: {str(e)}")

@router.put("/blocks/{block_id}")
async def update_content_block(
    block_id: str, 
    block_data: Dict[str, Any],
    current_user: dict = Depends(get_admin_user)
):
    """Update content block (Admin only)"""
    try:
        # Add update timestamp
        block_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update the block
        result = await db.content_blocks.replace_one(
            {"_id": block_id}, 
            block_data
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Content block not found")
        
        return {"success": True, "message": "Content block updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating content block: {str(e)}")

@router.get("/media-assets")
async def get_media_assets():
    """Get all media assets (public endpoint)"""
    try:
        assets = await db.media_assets.find().to_list(length=None)
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching media assets: {str(e)}")

@router.get("/media-assets/{asset_id}")
async def get_media_asset(asset_id: str):
    """Get specific media asset by ID (public endpoint)"""
    try:
        asset = await db.media_assets.find_one({"_id": asset_id})
        if not asset:
            raise HTTPException(status_code=404, detail="Media asset not found")
        return asset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching media asset: {str(e)}")

@router.put("/media-assets/{asset_id}")
async def update_media_asset(
    asset_id: str,
    asset_data: Dict[str, Any],
    current_user: dict = Depends(get_admin_user)
):
    """Update media asset (Admin only)"""
    try:
        # Add update timestamp
        asset_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update the asset
        result = await db.media_assets.replace_one(
            {"_id": asset_id}, 
            asset_data
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Media asset not found")
        
        return {"success": True, "message": "Media asset updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating media asset: {str(e)}")

@router.get("/admin/stats")
async def get_admin_dashboard_stats(current_user: dict = Depends(get_admin_user)):
    """Get real-time stats for admin dashboard"""
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get statistics from database
        [
            active_couriers,
            active_businesses, 
            today_orders,
            total_revenue
        ] = await asyncio.gather(
            db.users.count_documents({"role": "courier", "is_active": True}),
            db.users.count_documents({"role": "business", "is_active": True}),
            db.orders.count_documents({"created_at": {"$gte": today.isoformat()}}),
            get_total_revenue()
        )
        
        return {
            "active_couriers": active_couriers,
            "active_businesses": active_businesses,
            "today_orders": today_orders,
            "total_revenue": total_revenue
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin stats: {str(e)}")

async def get_total_revenue():
    """Calculate total revenue from completed orders"""
    try:
        pipeline = [
            {"$match": {"status": "delivered"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        
        result = await db.orders.aggregate(pipeline).to_list(length=None)
        return result[0]["total"] if result else 0
    except:
        return 0

@router.get("/popular-products")
async def get_popular_products(
    limit: int = 8,
    sort_by: str = "order_count",
    time_range: str = "all_time"
):
    """Get popular products for admin dashboard with advanced filtering"""
    try:
        # Time filter
        time_filter = {}
        if time_range != "all_time":
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            
            if time_range == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "week":
                start_date = now - timedelta(days=7)
            elif time_range == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=365)
            
            time_filter = {"created_at": {"$gte": start_date.isoformat()}}
        
        # Aggregation pipeline
        match_stage = {"$match": time_filter} if time_filter else {"$match": {}}
        
        if sort_by == "order_count":
            pipeline = [
                match_stage,
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.product_id",
                    "name": {"$first": "$items.product_name"}, 
                    "order_count": {"$sum": "$items.quantity"},
                    "business_name": {"$first": "$business_name"},
                    "total_revenue": {"$sum": "$items.subtotal"}
                }},
                {"$sort": {"order_count": -1}},
                {"$limit": limit}
            ]
        elif sort_by == "revenue":
            pipeline = [
                match_stage,
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.product_id",
                    "name": {"$first": "$items.product_name"}, 
                    "order_count": {"$sum": "$items.quantity"},
                    "business_name": {"$first": "$business_name"},
                    "total_revenue": {"$sum": "$items.subtotal"}
                }},
                {"$sort": {"total_revenue": -1}},
                {"$limit": limit}
            ]
        elif sort_by == "recent":
            pipeline = [
                match_stage,
                {"$unwind": "$items"},
                {"$sort": {"created_at": -1}},
                {"$group": {
                    "_id": "$items.product_id",
                    "name": {"$first": "$items.product_name"}, 
                    "order_count": {"$sum": "$items.quantity"},
                    "business_name": {"$first": "$business_name"},
                    "last_ordered": {"$first": "$created_at"}
                }},
                {"$limit": limit}
            ]
        else:  # Default to order_count
            pipeline = [
                match_stage,
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.product_id",
                    "name": {"$first": "$items.product_name"}, 
                    "order_count": {"$sum": "$items.quantity"},
                    "business_name": {"$first": "$business_name"}
                }},
                {"$sort": {"order_count": -1}},
                {"$limit": limit}
            ]
        
        products = await db.orders.aggregate(pipeline).to_list(length=None)
        
        # If no real data, return demo products
        if not products:
            demo_products = [
                {"_id": "demo-1", "name": "Margherita Pizza", "order_count": 45, "business_name": "Pizza Palace", "total_revenue": 675},
                {"_id": "demo-2", "name": "Cheeseburger", "order_count": 38, "business_name": "Burger House", "total_revenue": 532},
                {"_id": "demo-3", "name": "Chicken Döner", "order_count": 32, "business_name": "Döner King", "total_revenue": 448},
                {"_id": "demo-4", "name": "Sushi Set", "order_count": 28, "business_name": "Tokyo Sushi", "total_revenue": 980},
                {"_id": "demo-5", "name": "Fish & Chips", "order_count": 25, "business_name": "Ocean Grill", "total_revenue": 400},
                {"_id": "demo-6", "name": "Chicken Wings", "order_count": 22, "business_name": "Wing Stop", "total_revenue": 330},
                {"_id": "demo-7", "name": "Pasta Carbonara", "order_count": 20, "business_name": "Italian Corner", "total_revenue": 380},
                {"_id": "demo-8", "name": "Beef Burger", "order_count": 18, "business_name": "Gourmet Burgers", "total_revenue": 396}
            ]
            
            # Apply sorting to demo data
            if sort_by == "revenue":
                demo_products.sort(key=lambda x: x["total_revenue"], reverse=True)
            elif sort_by == "order_count":
                demo_products.sort(key=lambda x: x["order_count"], reverse=True)
            
            products = demo_products[:limit]
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular products: {str(e)}")

# Import asyncio for concurrent operations
import asyncio