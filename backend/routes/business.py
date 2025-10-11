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
    item_data: MenuItemCreate,
    current_user: dict = Depends(get_approved_business_user)
):
    """Create new menu item - Business role only"""
    try:
        from server import db
        
        # Use current user ID as business ID (since business is registered as user)
        business_user_id = current_user["id"]
        
        # Create menu item document
        menu_item_id = str(uuid.uuid4())
        menu_item_doc = {
            "_id": menu_item_id,
            "business_id": business_user_id,
            "title": item_data.title,
            "description": item_data.description,
            "price": float(item_data.price),
            "photo_url": item_data.photo_url,
            "category": item_data.category or "Ana Yemek",
            "is_available": item_data.is_available,
            "created_at": datetime.utcnow()
        }
        
        # Insert into both collections for compatibility
        # Insert into menu_items (business management)
        await db.menu_items.insert_one(menu_item_doc.copy())
        
        # Also insert into products (customer access) with compatible schema
        product_doc = {
            "_id": menu_item_doc["_id"],
            "business_id": menu_item_doc["business_id"],
            "name": item_data.title,  # products uses 'name' field
            "description": item_data.description,
            "price": item_data.price,
            "image": item_data.photo_url,  # products uses 'image' field
            "category": item_data.category,
            "availability": item_data.is_available,  # products uses 'availability' field
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.products.insert_one(product_doc)
        
        return MenuItemResponse(
            id=menu_item_doc["_id"],
            business_id=menu_item_doc["business_id"],
            title=menu_item_doc["title"],
            description=menu_item_doc["description"],
            price=menu_item_doc["price"],
            photo_url=menu_item_doc["photo_url"],
            category=menu_item_doc["category"],
            is_available=menu_item_doc["is_available"],
            created_at=menu_item_doc["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating menu item: {str(e)}"
        )

@router.get("/menu", response_model=List[MenuItemResponse])
async def get_my_menu(
    current_user: dict = Depends(get_approved_business_user)
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
                title=item["title"],
                description=item["description"],
                price=item["price"],
                photo_url=item.get("photo_url"),
                category=item.get("category", "Ana Yemek"),
                is_available=item.get("is_available", True),
                created_at=item["created_at"]
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
    item_id: str,
    item_data: MenuItemUpdate,
    current_user: dict = Depends(get_business_user)
):
    """Update menu item - Business can only update their own items"""
    try:
        from server import db
        
        # Get business ID
        business = await db.businesses.find_one({"owner_user_id": current_user["id"]})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Check if item belongs to this business
        existing_item = await db.menu_items.find_one({
            "_id": item_id,
            "business_id": str(business["_id"])
        })
        
        if not existing_item:
            raise HTTPException(
                status_code=404,
                detail="Menu item not found or access denied"
            )
        
        # Prepare update data
        update_data = {}
        if item_data.title is not None:
            update_data["title"] = item_data.title
        if item_data.description is not None:
            update_data["description"] = item_data.description
        if item_data.price is not None:
            update_data["price"] = float(item_data.price)
        if item_data.photo_url is not None:
            update_data["photo_url"] = item_data.photo_url
        if item_data.category is not None:
            update_data["category"] = item_data.category
        if item_data.is_available is not None:
            update_data["is_available"] = item_data.is_available
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in both collections for consistency
        await db.menu_items.update_one(
            {"_id": item_id},
            {"$set": update_data}
        )
        
        # Prepare product update data with field mapping
        product_update_data = {}
        if item_data.title is not None:
            product_update_data["name"] = item_data.title  # products uses 'name'
        if item_data.description is not None:
            product_update_data["description"] = item_data.description
        if item_data.price is not None:
            product_update_data["price"] = float(item_data.price)
        if item_data.photo_url is not None:
            product_update_data["image"] = item_data.photo_url  # products uses 'image'
        if item_data.category is not None:
            product_update_data["category"] = item_data.category
        if item_data.is_available is not None:
            product_update_data["availability"] = item_data.is_available  # products uses 'availability'
        
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
            title=updated_item["title"],
            description=updated_item["description"],
            price=updated_item["price"],
            photo_url=updated_item.get("photo_url"),
            category=updated_item.get("category", "Ana Yemek"),
            is_available=updated_item.get("is_available", True),
            created_at=updated_item["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating menu item: {str(e)}"
        )

@router.delete("/menu/{item_id}")
async def delete_menu_item(
    item_id: str,
    current_user: dict = Depends(get_business_user)
):
    """Delete menu item - Business can only delete their own items"""
    try:
        from server import db
        
        # Get business ID  
        business = await db.businesses.find_one({"owner_user_id": current_user["id"]})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Check ownership and delete from both collections
        result = await db.menu_items.delete_one({
            "_id": item_id,
            "business_id": str(business["_id"])
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Menu item not found or access denied"
            )
        
        # Also delete from products collection
        await db.products.delete_one({"_id": item_id})
        
        return {"success": True, "message": "Menu item deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting menu item: {str(e)}"
        )