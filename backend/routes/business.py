"""
Business Menu CRUD Routes - Real Database Only
Phase 2: Business & Customer Implementation
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from models import MenuItem, UserRole
from auth_dependencies import get_business_user, get_approved_business_user
from auth_cookie import get_approved_business_user_from_cookie
from fastapi import Request

router = APIRouter(prefix="/business", tags=["business"])

# Request/Response Models
class MenuItemOption(BaseModel):
    name: str
    price: float

class MenuItemCreate(BaseModel):
    name: str  # Changed from 'title' to 'name' for consistency
    description: Optional[str] = ""
    price: float
    currency: str = "TRY"
    category: str  # Required field: Yemek | Kahvaltı | İçecek | Atıştırmalık
    tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    is_available: bool = True
    vat_rate: float = 0.10  # KDV oranı: 0, 0.08, 0.10, 0.18
    options: Optional[List[MenuItemOption]] = []
    preparation_time: Optional[int] = 15  # dakika cinsinden
    
    # Validation
    @classmethod
    def validate_category(cls, v):
        allowed = ["Yemek", "Kahvaltı", "İçecek", "Atıştırmalık"]
        if v not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(allowed)}")
        return v
    
    @classmethod
    def validate_vat_rate(cls, v):
        allowed_vat = [0, 0.08, 0.10, 0.18]
        if v not in allowed_vat:
            raise ValueError(f"VAT rate must be one of: {', '.join(map(str, allowed_vat))}")
        return v
    
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price must be >= 0")
        return v

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    vat_rate: Optional[float] = None
    options: Optional[List[MenuItemOption]] = None
    preparation_time: Optional[int] = None

class MenuItemResponse(BaseModel):
    id: str
    business_id: str
    name: str
    description: str
    price: float
    currency: str
    category: str
    tags: List[str]
    image_url: Optional[str]
    is_available: bool
    vat_rate: float
    options: List[dict]
    preparation_time: int
    created_at: datetime
    updated_at: Optional[datetime] = None

@router.post("/menu", response_model=MenuItemResponse)
async def create_menu_item(
    request: Request,
    item_data: MenuItemCreate,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Create new menu item - Business role only (KYC approved)"""
    try:
        from server import db
        
        # Validate category
        MenuItemCreate.validate_category(item_data.category)
        # Validate VAT rate
        MenuItemCreate.validate_vat_rate(item_data.vat_rate)
        # Validate price
        MenuItemCreate.validate_price(item_data.price)
        
        # Use current user ID as business ID (since business is registered as user)
        business_user_id = current_user["id"]
        
        # Create menu item document
        menu_item_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        menu_item_doc = {
            "_id": menu_item_id,
            "business_id": business_user_id,
            "name": item_data.name,
            "description": item_data.description,
            "price": float(item_data.price),
            "currency": item_data.currency,
            "category": item_data.category,
            "tags": item_data.tags or [],
            "image_url": item_data.image_url,
            "is_available": item_data.is_available,
            "vat_rate": item_data.vat_rate,
            "options": [opt.dict() for opt in (item_data.options or [])],
            "preparation_time": item_data.preparation_time or 15,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into both collections for compatibility
        # Insert into menu_items (business management)
        await db.menu_items.insert_one(menu_item_doc.copy())
        
        # Also insert into products (customer access) with compatible schema
        product_doc = {
            "_id": menu_item_doc["_id"],
            "business_id": menu_item_doc["business_id"],
            "name": item_data.name,
            "description": item_data.description,
            "price": item_data.price,
            "currency": item_data.currency,
            "image": item_data.image_url,
            "category": item_data.category,
            "tags": item_data.tags or [],
            "availability": item_data.is_available,
            "vat_rate": item_data.vat_rate,
            "options": [opt.dict() for opt in (item_data.options or [])],
            "preparation_time": item_data.preparation_time or 15,
            "created_at": now,
            "updated_at": now
        }
        
        await db.products.insert_one(product_doc)
        
        return MenuItemResponse(
            id=menu_item_doc["_id"],
            business_id=menu_item_doc["business_id"],
            name=menu_item_doc["name"],
            description=menu_item_doc["description"],
            price=menu_item_doc["price"],
            currency=menu_item_doc["currency"],
            category=menu_item_doc["category"],
            tags=menu_item_doc["tags"],
            image_url=menu_item_doc["image_url"],
            is_available=menu_item_doc["is_available"],
            vat_rate=menu_item_doc["vat_rate"],
            options=menu_item_doc["options"],
            preparation_time=menu_item_doc["preparation_time"],
            created_at=menu_item_doc["created_at"],
            updated_at=menu_item_doc.get("updated_at")
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating menu item: {str(e)}"
        )

@router.get("/menu", response_model=List[MenuItemResponse])
async def get_my_menu(
    request: Request,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Get business's own menu items only"""
    try:
        from server import db
        
        # Use current user ID as business ID (since business is registered as user)
        business_user_id = current_user["id"]
        
        # Get menu items for this business user
        menu_items = await db.menu_items.find({
            "business_id": business_user_id
        }).sort("created_at", -1).to_list(length=None)
        
        return [
            MenuItemResponse(
                id=str(item["_id"]),
                business_id=item["business_id"],
                name=item.get("name", item.get("title", "")),  # Backward compatibility
                description=item.get("description", ""),
                price=item.get("price", 0),
                currency=item.get("currency", "TRY"),
                category=item.get("category", "Yemek"),
                tags=item.get("tags", []),
                image_url=item.get("image_url", item.get("photo_url")),  # Backward compatibility
                is_available=item.get("is_available", True),
                vat_rate=item.get("vat_rate", 0.10),
                options=item.get("options", []),
                preparation_time=item.get("preparation_time", 15),
                created_at=item["created_at"],
                updated_at=item.get("updated_at")
            )
            for item in menu_items
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching menu: {str(e)}"
        )

@router.patch("/menu/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    request: Request,
    item_id: str,
    item_data: MenuItemUpdate,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """Update menu item - Business can only update their own items"""
    try:
        from server import db
        
        # Validate optional fields if provided
        if item_data.category is not None:
            MenuItemCreate.validate_category(item_data.category)
        if item_data.vat_rate is not None:
            MenuItemCreate.validate_vat_rate(item_data.vat_rate)
        if item_data.price is not None:
            MenuItemCreate.validate_price(item_data.price)
        
        # Use current user ID as business ID (since business is registered as user)
        business_user_id = current_user["id"]
        
        # Check if item belongs to this business
        existing_item = await db.menu_items.find_one({
            "_id": item_id,
            "business_id": business_user_id
        })
        
        if not existing_item:
            raise HTTPException(
                status_code=404,
                detail="Menu item not found or access denied"
            )
        
        # Prepare update data
        update_data = {}
        if item_data.name is not None:
            update_data["name"] = item_data.name
        if item_data.description is not None:
            update_data["description"] = item_data.description
        if item_data.price is not None:
            update_data["price"] = float(item_data.price)
        if item_data.currency is not None:
            update_data["currency"] = item_data.currency
        if item_data.category is not None:
            update_data["category"] = item_data.category
        if item_data.tags is not None:
            update_data["tags"] = item_data.tags
        if item_data.image_url is not None:
            update_data["image_url"] = item_data.image_url
        if item_data.is_available is not None:
            update_data["is_available"] = item_data.is_available
        if item_data.vat_rate is not None:
            update_data["vat_rate"] = item_data.vat_rate
        if item_data.options is not None:
            update_data["options"] = [opt.dict() for opt in item_data.options]
        if item_data.preparation_time is not None:
            update_data["preparation_time"] = item_data.preparation_time
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in both collections for consistency
        await db.menu_items.update_one(
            {"_id": item_id},
            {"$set": update_data}
        )
        
        # Prepare product update data with field mapping
        product_update_data = {}
        if item_data.name is not None:
            product_update_data["name"] = item_data.name
        if item_data.description is not None:
            product_update_data["description"] = item_data.description
        if item_data.price is not None:
            product_update_data["price"] = float(item_data.price)
        if item_data.currency is not None:
            product_update_data["currency"] = item_data.currency
        if item_data.category is not None:
            product_update_data["category"] = item_data.category
        if item_data.tags is not None:
            product_update_data["tags"] = item_data.tags
        if item_data.image_url is not None:
            product_update_data["image"] = item_data.image_url
        if item_data.is_available is not None:
            product_update_data["availability"] = item_data.is_available
        if item_data.vat_rate is not None:
            product_update_data["vat_rate"] = item_data.vat_rate
        if item_data.options is not None:
            product_update_data["options"] = [opt.dict() for opt in item_data.options]
        if item_data.preparation_time is not None:
            product_update_data["preparation_time"] = item_data.preparation_time
        
        product_update_data["updated_at"] = datetime.utcnow()
        
        # Update products collection
        await db.products.update_one(
            {"_id": item_id},
            {"$set": product_update_data}
        )
        
        # Get updated item
        updated_item = await db.menu_items.find_one({"_id": item_id})
        
        return MenuItemResponse(
            id=str(updated_item["_id"]),
            business_id=updated_item["business_id"],
            name=updated_item.get("name", updated_item.get("title", "")),
            description=updated_item.get("description", ""),
            price=updated_item.get("price", 0),
            currency=updated_item.get("currency", "TRY"),
            category=updated_item.get("category", "Yemek"),
            tags=updated_item.get("tags", []),
            image_url=updated_item.get("image_url", updated_item.get("photo_url")),
            is_available=updated_item.get("is_available", True),
            vat_rate=updated_item.get("vat_rate", 0.10),
            options=updated_item.get("options", []),
            preparation_time=updated_item.get("preparation_time", 15),
            created_at=updated_item["created_at"],
            updated_at=updated_item.get("updated_at")
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating menu item: {str(e)}"
        )

@router.delete("/menu/{item_id}")
async def delete_menu_item(
    request: Request,
    item_id: str,
    soft_delete: bool = True,
    current_user: dict = Depends(get_approved_business_user_from_cookie)
):
    """
    Delete menu item - Business can only delete their own items
    - soft_delete=True: Sets is_available=False (default)
    - soft_delete=False: Permanently deletes from database
    """
    try:
        from server import db
        
        # Use current user ID as business ID (since business is registered as user)
        business_user_id = current_user["id"]
        
        # Check ownership
        existing_item = await db.menu_items.find_one({
            "_id": item_id,
            "business_id": business_user_id
        })
        
        if not existing_item:
            raise HTTPException(
                status_code=404,
                detail="Menu item not found or access denied"
            )
        
        if soft_delete:
            # Soft delete: set is_available to False
            await db.menu_items.update_one(
                {"_id": item_id},
                {"$set": {"is_available": False, "updated_at": datetime.utcnow()}}
            )
            await db.products.update_one(
                {"_id": item_id},
                {"$set": {"availability": False, "updated_at": datetime.utcnow()}}
            )
            return {"success": True, "message": "Menu item disabled (soft delete)"}
        else:
            # Hard delete: permanently remove from database
            result = await db.menu_items.delete_one({
                "_id": item_id,
                "business_id": business_user_id
            })
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Menu item not found or access denied"
                )
            
            # Also delete from products collection
            await db.products.delete_one({"_id": item_id})
            
            return {"success": True, "message": "Menu item permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting menu item: {str(e)}"
        )

# Public endpoint for customers to view business menu
@router.get("/{business_id}/menu", response_model=List[MenuItemResponse])
async def get_business_menu(
    business_id: str,
    category: Optional[str] = None
):
    """
    Public endpoint - Get menu items for a specific business
    Optionally filter by category
    """
    try:
        from server import db
        
        # Build query - only show available items
        query = {
            "business_id": business_id,
            "is_available": True
        }
        
        if category:
            query["category"] = category
        
        # Get menu items
        menu_items = await db.menu_items.find(query).sort("category", 1).sort("name", 1).to_list(length=None)
        
        return [
            MenuItemResponse(
                id=str(item["_id"]),
                business_id=item["business_id"],
                name=item.get("name", item.get("title", "")),
                description=item.get("description", ""),
                price=item.get("price", 0),
                currency=item.get("currency", "TRY"),
                category=item.get("category", "Yemek"),
                tags=item.get("tags", []),
                image_url=item.get("image_url", item.get("photo_url")),
                is_available=item.get("is_available", True),
                vat_rate=item.get("vat_rate", 0.10),
                options=item.get("options", []),
                preparation_time=item.get("preparation_time", 15),
                created_at=item["created_at"],
                updated_at=item.get("updated_at")
            )
            for item in menu_items
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching business menu: {str(e)}"
        )

@router.get("/menu/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: str):
    """Public endpoint - Get single menu item details"""
    try:
        from server import db
        
        item = await db.menu_items.find_one({"_id": item_id})
        
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        return MenuItemResponse(
            id=str(item["_id"]),
            business_id=item["business_id"],
            name=item.get("name", item.get("title", "")),
            description=item.get("description", ""),
            price=item.get("price", 0),
            currency=item.get("currency", "TRY"),
            category=item.get("category", "Yemek"),
            tags=item.get("tags", []),
            image_url=item.get("image_url", item.get("photo_url")),
            is_available=item.get("is_available", True),
            vat_rate=item.get("vat_rate", 0.10),
            options=item.get("options", []),
            preparation_time=item.get("preparation_time", 15),
            created_at=item["created_at"],
            updated_at=item.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching menu item: {str(e)}"
        )

# ============================================
# PUBLIC ENDPOINTS FOR CUSTOMERS
# ============================================

@router.get("/businesses/{business_id}/products", response_model=List[MenuItemResponse])
async def get_public_business_menu(business_id: str):
    """
    Get public menu for a business - accessible by customers
    Returns only available items
    """
    try:
        from server import db
        
        # Get menu items for this business (only available ones)
        menu_items = await db.menu_items.find({
            "business_id": business_id,
            "is_available": True
        }).to_list(length=None)
        
        if not menu_items:
            return []
        
        return [
            MenuItemResponse(
                id=str(item["_id"]),
                business_id=item["business_id"],
                name=item.get("name", item.get("title", "")),
                description=item.get("description", ""),
                price=item.get("price", 0),
                currency=item.get("currency", "TRY"),
                category=item.get("category", "Yemek"),
                tags=item.get("tags", []),
                image_url=item.get("image_url", item.get("photo_url")),
                is_available=True,  # Only showing available items
                vat_rate=item.get("vat_rate", 0.10),
                options=item.get("options", []),
                preparation_time=item.get("preparation_time", 15),
                created_at=item["created_at"],
                updated_at=item.get("updated_at")
            )
            for item in menu_items
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching public menu: {str(e)}"
        )

# ============================================
# PUBLIC ENDPOINTS - For Customers
# ============================================

@router.get("/public/{business_id}/menu", response_model=List[MenuItem])
async def get_business_public_menu(business_id: str):
    """
    Get public menu of a business - NO AUTH REQUIRED
    Customers can view menus of approved businesses
    Only returns available items
    """
    try:
        from server import db
        
        # Verify business exists and is approved
        business = await db.users.find_one({
            "id": business_id,
            "role": "business",
            "kyc_status": "approved",
            "is_active": True
        })
        
        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business not found or not approved"
            )
        
        # Get all available menu items for this business
        menu_items = await db.menu_items.find({
            "business_id": business_id,
            "is_available": True
        }).sort("created_at", -1).to_list(length=None)
        
        return [
            MenuItem(
                id=item["_id"],
                business_id=item["business_id"],
                name=item["name"],
                description=item.get("description", ""),
                price=item["price"],
                currency=item.get("currency", "TRY"),
                category=item["category"],
                tags=item.get("tags", []),
                image_url=item.get("image_url"),
                is_available=item.get("is_available", True),
                vat_rate=item.get("vat_rate", 0.10),
                options=item.get("options", []),
                preparation_time=item.get("preparation_time", 15),
                created_at=item["created_at"],
                updated_at=item.get("updated_at")
            )
            for item in menu_items
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching public menu: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching public menu: {str(e)}"
        )