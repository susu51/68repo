"""
API Endpoints for localStorage to MongoDB Migration
All CRUD operations for cart, addresses, preferences, and loyalty
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from .auth_cookies import (
    get_current_user, verify_csrf_token, set_auth_cookies, 
    clear_auth_cookies, create_auth_tokens, UserSession
)
from .models import (
    Address, Cart, CartItem, UserPreferences, NotificationPreferences,
    MarketingPreferences, LoyaltyTransaction, MigrationData, MigrationStatus,
    COLLECTION_NAMES
)
from .database import get_database
import logging

logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api", tags=["localStorage Migration"])

# Addresses API
@api_router.get("/addresses", response_model=List[Address])
async def get_user_addresses(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all addresses for current user"""
    try:
        addresses_cursor = db[COLLECTION_NAMES["addresses"]].find(
            {"user_id": current_user.user_id}
        ).sort("is_default", -1).sort("created_at", -1)
        
        addresses = []
        async for address_doc in addresses_cursor:
            address_doc["_id"] = address_doc.get("_id") or address_doc.get("id")
            addresses.append(Address(**address_doc))
        
        logger.info(f"Retrieved {len(addresses)} addresses for user {current_user.user_id}")
        return addresses
        
    except Exception as e:
        logger.error(f"Error fetching addresses for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch addresses")

@api_router.post("/addresses", response_model=Address)
async def create_address(
    address_data: Dict[str, Any],
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create new address for current user"""
    try:
        # Create address object
        new_address = Address(
            user_id=current_user.user_id,
            label=address_data.get("label", "Diğer"),
            full_address=address_data["full_address"],
            city=address_data["city"],
            district=address_data.get("district"),
            loc=address_data["loc"],
            is_default=address_data.get("is_default", False)
        )
        
        # If setting as default, unset other defaults
        if new_address.is_default:
            await db[COLLECTION_NAMES["addresses"]].update_many(
                {"user_id": current_user.user_id},
                {"$set": {"is_default": False}}
            )
        
        # Insert new address
        address_dict = new_address.dict(by_alias=True)
        result = await db[COLLECTION_NAMES["addresses"]].insert_one(address_dict)
        
        # Return created address
        new_address.id = str(result.inserted_id)
        
        logger.info(f"Created address {new_address.id} for user {current_user.user_id}")
        return new_address
        
    except Exception as e:
        logger.error(f"Error creating address for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create address")

@api_router.patch("/addresses/{address_id}", response_model=Address)
async def update_address(
    address_id: str,
    updates: Dict[str, Any],
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update existing address"""
    try:
        # Verify address belongs to user
        existing_address = await db[COLLECTION_NAMES["addresses"]].find_one({
            "_id": address_id,
            "user_id": current_user.user_id
        })
        
        if not existing_address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Handle default address logic
        if updates.get("is_default", False):
            await db[COLLECTION_NAMES["addresses"]].update_many(
                {"user_id": current_user.user_id},
                {"$set": {"is_default": False}}
            )
        
        # Update address
        updates["updated_at"] = datetime.now(timezone.utc)
        result = await db[COLLECTION_NAMES["addresses"]].update_one(
            {"_id": address_id, "user_id": current_user.user_id},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Address not updated")
        
        # Return updated address
        updated_address = await db[COLLECTION_NAMES["addresses"]].find_one({
            "_id": address_id
        })
        updated_address["_id"] = address_id
        
        logger.info(f"Updated address {address_id} for user {current_user.user_id}")
        return Address(**updated_address)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating address {address_id} for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update address")

@api_router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete address"""
    try:
        result = await db[COLLECTION_NAMES["addresses"]].delete_one({
            "_id": address_id,
            "user_id": current_user.user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        logger.info(f"Deleted address {address_id} for user {current_user.user_id}")
        return {"message": "Address deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting address {address_id} for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete address")

# Cart API
@api_router.get("/cart", response_model=Cart)
async def get_user_cart(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's cart with server-validated prices"""
    try:
        # Get cart from database
        cart_doc = await db[COLLECTION_NAMES["carts"]].find_one({
            "user_id": current_user.user_id
        })
        
        if not cart_doc:
            # Create empty cart
            empty_cart = Cart(user_id=current_user.user_id)
            cart_dict = empty_cart.dict(by_alias=True)
            await db[COLLECTION_NAMES["carts"]].insert_one(cart_dict)
            return empty_cart
        
        # Convert to Cart model
        cart_doc["_id"] = cart_doc.get("_id") or cart_doc.get("id")
        cart = Cart(**cart_doc)
        
        # Validate prices with database
        if cart.items:
            product_ids = [item.product_id for item in cart.items]
            products_cursor = db["products"].find({"id": {"$in": product_ids}})
            products = {p["id"]: p async for p in products_cursor}
            
            # Update cart items with current prices
            updated_items = []
            for item in cart.items:
                if item.product_id in products:
                    product = products[item.product_id]
                    item.price = product["price"]
                    item.product_name = product["name"]
                    updated_items.append(item)
                # Skip items for products that no longer exist
            
            cart.items = updated_items
            
            # Update cart in database with validated data
            await db[COLLECTION_NAMES["carts"]].update_one(
                {"user_id": current_user.user_id},
                {"$set": {
                    "items": [item.dict() for item in cart.items],
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
        
        logger.info(f"Retrieved cart with {len(cart.items)} items for user {current_user.user_id}")
        return cart
        
    except Exception as e:
        logger.error(f"Error fetching cart for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cart")

@api_router.put("/cart", response_model=Cart)
async def update_cart(
    cart_update: Dict[str, Any],
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update user's cart (add/remove/modify items)"""
    try:
        # Validate cart items against database
        if "items" in cart_update:
            items_data = cart_update["items"]
            validated_items = []
            
            # Get current prices from database
            if items_data:
                product_ids = [item["product_id"] for item in items_data]
                products_cursor = db["products"].find({"id": {"$in": product_ids}})
                products = {p["id"]: p async for p in products_cursor}
                
                for item_data in items_data:
                    product_id = item_data["product_id"]
                    if product_id in products:
                        product = products[product_id]
                        validated_item = CartItem(
                            product_id=product_id,
                            qty=item_data["qty"],
                            price=product["price"],
                            product_name=product["name"]
                        )
                        validated_items.append(validated_item)
            
            # Update or create cart
            cart_update_data = {
                "user_id": current_user.user_id,
                "items": [item.dict() for item in validated_items],
                "updated_at": datetime.now(timezone.utc)
            }
            
            if "business_id" in cart_update:
                cart_update_data["business_id"] = cart_update["business_id"]
            if "city" in cart_update:
                cart_update_data["city"] = cart_update["city"]
            
            result = await db[COLLECTION_NAMES["carts"]].update_one(
                {"user_id": current_user.user_id},
                {"$set": cart_update_data},
                upsert=True
            )
            
            # Return updated cart
            updated_cart_doc = await db[COLLECTION_NAMES["carts"]].find_one({
                "user_id": current_user.user_id
            })
            updated_cart_doc["_id"] = updated_cart_doc.get("_id") or updated_cart_doc.get("id")
            updated_cart = Cart(**updated_cart_doc)
            
            logger.info(f"Updated cart with {len(updated_cart.items)} items for user {current_user.user_id}")
            return updated_cart
        
        raise HTTPException(status_code=400, detail="Invalid cart update data")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update cart")

# Preferences API
@api_router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user preferences"""
    try:
        prefs_doc = await db[COLLECTION_NAMES["preferences"]].find_one({
            "user_id": current_user.user_id
        })
        
        if not prefs_doc:
            # Create default preferences
            default_prefs = UserPreferences(user_id=current_user.user_id)
            prefs_dict = default_prefs.dict(by_alias=True)
            await db[COLLECTION_NAMES["preferences"]].insert_one(prefs_dict)
            return default_prefs
        
        prefs_doc["_id"] = prefs_doc.get("_id") or prefs_doc.get("id")
        return UserPreferences(**prefs_doc)
        
    except Exception as e:
        logger.error(f"Error fetching preferences for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")

@api_router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: Dict[str, Any],
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update user preferences"""
    try:
        preferences["updated_at"] = datetime.now(timezone.utc)
        
        result = await db[COLLECTION_NAMES["preferences"]].update_one(
            {"user_id": current_user.user_id},
            {"$set": preferences},
            upsert=True
        )
        
        # Return updated preferences
        updated_prefs_doc = await db[COLLECTION_NAMES["preferences"]].find_one({
            "user_id": current_user.user_id
        })
        updated_prefs_doc["_id"] = updated_prefs_doc.get("_id") or updated_prefs_doc.get("id")
        
        logger.info(f"Updated preferences for user {current_user.user_id}")
        return UserPreferences(**updated_prefs_doc)
        
    except Exception as e:
        logger.error(f"Error updating preferences for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# Loyalty Points API
@api_router.get("/loyalty/points")
async def get_loyalty_points(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's current loyalty points balance"""
    try:
        # Get user's loyalty points
        user_doc = await db[COLLECTION_NAMES["users"]].find_one({
            "_id": current_user.user_id
        })
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        loyalty_points = user_doc.get("loyalty_points", 0)
        
        # Get recent transactions
        transactions_cursor = db[COLLECTION_NAMES["loyalty_transactions"]].find(
            {"user_id": current_user.user_id}
        ).sort("created_at", -1).limit(10)
        
        transactions = []
        async for txn_doc in transactions_cursor:
            txn_doc["_id"] = txn_doc.get("_id") or txn_doc.get("id")
            transactions.append(LoyaltyTransaction(**txn_doc))
        
        return {
            "balance": loyalty_points,
            "recent_transactions": transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching loyalty points for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch loyalty points")

@api_router.post("/loyalty/consume")
async def consume_loyalty_points(
    request_data: Dict[str, Any],
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Consume loyalty points for rewards"""
    try:
        points_to_spend = request_data.get("points", 0)
        description = request_data.get("description", "Points spent")
        
        if points_to_spend <= 0:
            raise HTTPException(status_code=400, detail="Invalid points amount")
        
        # Get current balance
        user_doc = await db[COLLECTION_NAMES["users"]].find_one({
            "_id": current_user.user_id
        })
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_points = user_doc.get("loyalty_points", 0)
        if current_points < points_to_spend:
            raise HTTPException(status_code=400, detail="Insufficient loyalty points")
        
        # Create transaction
        transaction = LoyaltyTransaction(
            user_id=current_user.user_id,
            points=-points_to_spend,
            transaction_type="spend",
            description=description
        )
        
        # Update user balance and record transaction
        new_balance = current_points - points_to_spend
        
        await db[COLLECTION_NAMES["users"]].update_one(
            {"_id": current_user.user_id},
            {"$set": {"loyalty_points": new_balance}}
        )
        
        await db[COLLECTION_NAMES["loyalty_transactions"]].insert_one(
            transaction.dict(by_alias=True)
        )
        
        logger.info(f"User {current_user.user_id} spent {points_to_spend} loyalty points")
        return {
            "success": True,
            "new_balance": new_balance,
            "points_spent": points_to_spend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consuming loyalty points for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to consume loyalty points")

# Migration API
@api_router.post("/migrate-localstorage")
async def migrate_localstorage_data(
    migration_data: MigrationData,
    current_user: UserSession = Depends(verify_csrf_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Migrate localStorage data to MongoDB (one-time migration)"""
    try:
        # Check if user already migrated
        existing_migration = await db[COLLECTION_NAMES["migration_status"]].find_one({
            "user_id": current_user.user_id
        })
        
        if existing_migration:
            return {"message": "Data already migrated", "skipped": True}
        
        migrated_types = []
        
        # Migrate cart
        if migration_data.cart:
            try:
                cart_items = [
                    CartItem(**item) for item in migration_data.cart
                    if "product_id" in item and "qty" in item
                ]
                
                if cart_items:
                    cart = Cart(user_id=current_user.user_id, items=cart_items)
                    await db[COLLECTION_NAMES["carts"]].insert_one(cart.dict(by_alias=True))
                    migrated_types.append("cart")
                    
            except Exception as e:
                logger.warning(f"Failed to migrate cart for user {current_user.user_id}: {e}")
        
        # Migrate addresses
        if migration_data.addresses:
            try:
                for addr_data in migration_data.addresses:
                    if "full_address" in addr_data and "city" in addr_data:
                        address = Address(
                            user_id=current_user.user_id,
                            **addr_data
                        )
                        await db[COLLECTION_NAMES["addresses"]].insert_one(address.dict(by_alias=True))
                
                if migration_data.addresses:
                    migrated_types.append("addresses")
                    
            except Exception as e:
                logger.warning(f"Failed to migrate addresses for user {current_user.user_id}: {e}")
        
        # Migrate preferences
        if migration_data.preferences:
            try:
                prefs = UserPreferences(
                    user_id=current_user.user_id,
                    **migration_data.preferences
                )
                await db[COLLECTION_NAMES["preferences"]].insert_one(prefs.dict(by_alias=True))
                migrated_types.append("preferences")
                
            except Exception as e:
                logger.warning(f"Failed to migrate preferences for user {current_user.user_id}: {e}")
        
        # Migrate loyalty points
        if migration_data.loyalty_points and migration_data.loyalty_points > 0:
            try:
                await db[COLLECTION_NAMES["users"]].update_one(
                    {"_id": current_user.user_id},
                    {"$set": {"loyalty_points": migration_data.loyalty_points}}
                )
                
                # Record migration transaction
                transaction = LoyaltyTransaction(
                    user_id=current_user.user_id,
                    points=migration_data.loyalty_points,
                    transaction_type="migration",
                    description="Migrated from localStorage"
                )
                await db[COLLECTION_NAMES["loyalty_transactions"]].insert_one(
                    transaction.dict(by_alias=True)
                )
                migrated_types.append("loyalty_points")
                
            except Exception as e:
                logger.warning(f"Failed to migrate loyalty points for user {current_user.user_id}: {e}")
        
        # Record migration status
        migration_status = MigrationStatus(
            user_id=current_user.user_id,
            data_types=migrated_types
        )
        await db[COLLECTION_NAMES["migration_status"]].insert_one(
            migration_status.dict(by_alias=True)
        )
        
        logger.info(f"Migrated localStorage data for user {current_user.user_id}: {migrated_types}")
        return {
            "message": "Data migrated successfully",
            "migrated_types": migrated_types
        }
        
    except Exception as e:
        logger.error(f"Error migrating localStorage data for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to migrate data")

# Banner analytics API
@api_router.post("/banners/{banner_id}/click")
async def track_banner_click(
    banner_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[UserSession] = Depends(get_current_user_optional)
):
    """Track banner click analytics"""
    try:
        # Update click count
        result = await db[COLLECTION_NAMES["banners"]].update_one(
            {"_id": banner_id},
            {"$inc": {"clicks": 1}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        # Log click event (could be expanded for detailed analytics)
        logger.info(f"Banner {banner_id} clicked by user {getattr(current_user, 'user_id', 'anonymous')}")
        
        return {"message": "Click tracked"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking banner click: {e}")
        raise HTTPException(status_code=500, detail="Failed to track click")

@api_router.post("/banners/{banner_id}/impression")
async def track_banner_impression(
    banner_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Track banner impression analytics"""
    try:
        result = await db[COLLECTION_NAMES["banners"]].update_one(
            {"_id": banner_id},
            {"$inc": {"impressions": 1}}
        )
        
        if result.modified_count == 0:
            # Banner might not exist, but impression tracking shouldn't fail
            logger.warning(f"Banner {banner_id} not found for impression tracking")
        
        return {"message": "Impression tracked"}
        
    except Exception as e:
        logger.error(f"Error tracking banner impression: {e}")
        # Don't fail on impression tracking errors
        return {"message": "Impression tracking failed"}

# Auth endpoints with cookie support
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/login")
async def login_with_cookies(
    request: Request,
    response: Response,
    login_data: Dict[str, str],
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Login with httpOnly cookies instead of localStorage tokens"""
    # This would integrate with your existing authentication logic
    # For now, this is a placeholder that shows the pattern
    
    # TODO: Implement actual login logic
    # 1. Validate credentials
    # 2. Create user session
    # 3. Generate JWT + CSRF tokens
    # 4. Set httpOnly cookies
    
    return {"message": "Login endpoint - to be implemented with existing auth"}

@auth_router.post("/logout")
async def logout_clear_cookies(
    response: Response,
    current_user: UserSession = Depends(get_current_user)
):
    """Logout and clear authentication cookies"""
    try:
        clear_auth_cookies(response)
        
        logger.info(f"User {current_user.user_id} logged out")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # Clear cookies anyway
        clear_auth_cookies(response)
        return {"message": "Logged out"}

# Add routers to main app
def setup_localstorage_api(app):
    """Add localStorage migration API routes to main app"""
    app.include_router(api_router)
    app.include_router(auth_router)
    logger.info("localStorage migration API routes added")