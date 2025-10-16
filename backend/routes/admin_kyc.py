"""
Admin KYC Management Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()

class KYCApprovalRequest(BaseModel):
    user_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

@router.get("/kyc/pending")
async def get_pending_kyc_requests(current_user: dict = Depends(lambda: {"role": "admin"})):
    """Get all pending KYC requests"""
    from server import db
    
    # Only admin can access
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    # Get all users with pending KYC
    pending_users = await db.users.find({
        "kyc_status": "pending",
        "role": {"$in": ["courier", "business"]}
    }).to_list(length=100)
    
    # Format response
    result = []
    for user in pending_users:
        result.append({
            "id": user.get("id") or user.get("_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role"),
            "phone": user.get("phone"),
            "city": user.get("city"),
            "district": user.get("district"),
            "neighborhood": user.get("neighborhood"),
            "vehicle_type": user.get("vehicle_type"),
            "business_name": user.get("business_name"),
            "business_tax_id": user.get("business_tax_id"),
            "kyc_documents": user.get("kyc_documents", []),
            "created_at": user.get("created_at"),
            "kyc_status": user.get("kyc_status")
        })
    
    return {"success": True, "pending_requests": result, "count": len(result)}

@router.post("/kyc/action")
async def process_kyc_action(
    request: KYCApprovalRequest,
    current_user: dict = Depends(lambda: {"role": "admin"})
):
    """Approve or reject KYC request"""
    from server import db
    
    # Only admin can access
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    if request.action not in ["approve", "reject"]:
        raise HTTPException(400, "Invalid action. Must be 'approve' or 'reject'")
    
    # Update user KYC status
    update_data = {
        "kyc_status": "approved" if request.action == "approve" else "rejected",
        "kyc_updated_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    if request.action == "reject" and request.reason:
        update_data["kyc_rejection_reason"] = request.reason
    
    result = await db.users.update_one(
        {"$or": [{"id": request.user_id}, {"_id": request.user_id}]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    
    return {
        "success": True,
        "message": f"KYC {request.action}d successfully",
        "user_id": request.user_id,
        "new_status": update_data["kyc_status"]
    }

@router.get("/kyc/stats")
async def get_kyc_stats(current_user: dict = Depends(lambda: {"role": "admin"})):
    """Get KYC statistics"""
    from server import db
    
    # Only admin can access
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    pending_count = await db.users.count_documents({"kyc_status": "pending"})
    approved_count = await db.users.count_documents({"kyc_status": "approved"})
    rejected_count = await db.users.count_documents({"kyc_status": "rejected"})
    
    return {
        "success": True,
        "stats": {
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "total": pending_count + approved_count + rejected_count
        }
    }
