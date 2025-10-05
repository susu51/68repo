"""
Business Menu CRUD Routes - Real Database Only
Phase 2: Business & Customer Implementation
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import jwt
import os
from models import MenuItem, UserRole

router = APIRouter(prefix="/business", tags=["business"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        secret_key = os.environ.get("JWT_SECRET", "kuryecini_secret_key_2024")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        from server import db
        user_id = payload.get("sub")
        user = await db.users.find_one({"_id": user_id})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "id": user["_id"],
            "email": user["email"],
            "role": user["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_business_user(current_user: dict = Depends(get_current_user)):
    """Require business role"""
    if current_user.get("role") != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business access required"
        )
    return current_user

# Request/Response Models
class MenuItemCreate(BaseModel):
    title: str
    description: str
    price: float
    photo_url: Optional[str] = None
    category: Optional[str] = "Ana Yemek"
    is_available: bool = True

class MenuItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    photo_url: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None

class MenuItemResponse(BaseModel):
    id: str
    business_id: str
    title: str
    description: str
    price: float
    photo_url: Optional[str]
    category: str
    is_available: bool
    created_at: datetime

@router.post("/menu", response_model=MenuItemResponse)
async def create_menu_item(
    item_data: MenuItemCreate,
    current_user: dict = Depends(get_business_user)
):
    """Create new menu item - Business role only"""
    try:
        from server import db
        
        # Get business ID from user
        business = await db.businesses.find_one({"owner_user_id": current_user["id"]})
        if not business:
            raise HTTPException(
                status_code=404, 
                detail="Business not found for this user"
            )
        
        # Create menu item document
        menu_item_doc = {
            "_id": str(uuid.uuid4()),
            "business_id": str(business["_id"]),
            "title": item_data.title,
            "description": item_data.description,
            "price": float(item_data.price),
            "photo_url": item_data.photo_url,
            "category": item_data.category or "Ana Yemek",
            "is_available": item_data.is_available,
            "created_at": datetime.utcnow()
        }
        
        # Insert to database
        await db.menu_items.insert_one(menu_item_doc)
        
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
    current_user: dict = Depends(get_business_user)
):
    """Get business's own menu items only"""
    try:
        from server import db
        
        # Get business ID
        business = await db.businesses.find_one({"owner_user_id": current_user["id"]})
        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business not found"
            )
        
        # Get menu items
        menu_items = await db.menu_items.find({
            "business_id": str(business["_id"])
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
        
        # Update in database
        await db.menu_items.update_one(
            {"_id": item_id},
            {"$set": update_data}
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
        
        # Check ownership and delete
        result = await db.menu_items.delete_one({
            "_id": item_id,
            "business_id": str(business["_id"])
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Menu item not found or access denied"
            )
        
        return {"success": True, "message": "Menu item deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting menu item: {str(e)}"
        )