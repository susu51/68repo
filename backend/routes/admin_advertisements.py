"""
Admin Advertisement Management Routes
Manage restaurant advertisements for customer discovery page
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from auth_dependencies import get_admin_user
import uuid
import os
import shutil

router = APIRouter()

# Upload directory
UPLOAD_DIR = "/app/backend/uploads/advertisements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Advertisement(BaseModel):
    id: Optional[str] = None
    business_id: str
    business_name: str
    title: Optional[str] = None  # Reklam başlığı/slogan
    image_url: str
    city: str  # Hangi şehirde gösterilecek
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/advertisements")
async def create_advertisement(
    business_id: str = Form(...),
    business_name: str = Form(...),
    city: str = Form(...),
    title: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_admin_user)
):
    """Create new advertisement with image upload"""
    from server import db
    
    try:
        # Validate business exists
        business = await db.users.find_one({"id": business_id, "role": "business"})
        if not business:
            raise HTTPException(404, "Business not found")
        
        # Save uploaded image
        ad_id = str(uuid.uuid4())
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"ad_{ad_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_url = f"/uploads/advertisements/{filename}"
        
        # Create advertisement
        advertisement = {
            "id": ad_id,
            "business_id": business_id,
            "business_name": business_name,
            "title": title,
            "image_url": image_url,
            "city": city.strip().title(),  # Normalize city name
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.advertisements.insert_one(advertisement)
        
        return {
            "success": True,
            "message": "Advertisement created successfully",
            "advertisement": advertisement
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error creating advertisement: {str(e)}")

@router.get("/advertisements")
async def get_all_advertisements(current_user: dict = Depends(get_admin_user)):
    """Get all advertisements for admin management"""
    from server import db
    
    try:
        advertisements = await db.advertisements.find().sort("created_at", -1).to_list(length=100)
        
        # Remove MongoDB _id
        for ad in advertisements:
            ad.pop("_id", None)
        
        return {
            "success": True,
            "advertisements": advertisements,
            "count": len(advertisements)
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error fetching advertisements: {str(e)}")

@router.get("/advertisements/{ad_id}")
async def get_advertisement(ad_id: str, current_user: dict = Depends(get_admin_user)):
    """Get specific advertisement details"""
    from server import db
    
    advertisement = await db.advertisements.find_one({"id": ad_id})
    if not advertisement:
        raise HTTPException(404, "Advertisement not found")
    
    advertisement.pop("_id", None)
    
    return {
        "success": True,
        "advertisement": advertisement
    }

@router.patch("/advertisements/{ad_id}")
async def update_advertisement(
    ad_id: str,
    update_data: AdvertisementUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update advertisement details"""
    from server import db
    
    # Check if advertisement exists
    advertisement = await db.advertisements.find_one({"id": ad_id})
    if not advertisement:
        raise HTTPException(404, "Advertisement not found")
    
    # Prepare update data
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    if update_data.city is not None:
        update_fields["city"] = update_data.city.strip().title()
    if update_data.is_active is not None:
        update_fields["is_active"] = update_data.is_active
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update advertisement
    await db.advertisements.update_one(
        {"id": ad_id},
        {"$set": update_fields}
    )
    
    # Fetch updated advertisement
    updated_ad = await db.advertisements.find_one({"id": ad_id})
    updated_ad.pop("_id", None)
    
    return {
        "success": True,
        "message": "Advertisement updated successfully",
        "advertisement": updated_ad
    }

@router.patch("/advertisements/{ad_id}/toggle")
async def toggle_advertisement_status(
    ad_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Toggle advertisement active/inactive status"""
    from server import db
    
    # Check if advertisement exists
    advertisement = await db.advertisements.find_one({"id": ad_id})
    if not advertisement:
        raise HTTPException(404, "Advertisement not found")
    
    new_status = not advertisement.get("is_active", False)
    
    # Update status
    await db.advertisements.update_one(
        {"id": ad_id},
        {"$set": {
            "is_active": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "message": f"Advertisement {'activated' if new_status else 'deactivated'}",
        "is_active": new_status
    }

@router.delete("/advertisements/{ad_id}")
async def delete_advertisement(
    ad_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Delete advertisement"""
    from server import db
    
    # Check if advertisement exists
    advertisement = await db.advertisements.find_one({"id": ad_id})
    if not advertisement:
        raise HTTPException(404, "Advertisement not found")
    
    # Delete image file
    image_url = advertisement.get("image_url", "")
    if image_url:
        file_path = f"/app/backend{image_url}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete image file: {e}")
    
    # Delete advertisement from database
    result = await db.advertisements.delete_one({"id": ad_id})
    
    if result.deleted_count == 0:
        raise HTTPException(500, "Failed to delete advertisement")
    
    return {
        "success": True,
        "message": "Advertisement deleted successfully"
    }
