"""
Customer Cart Management - localStorage yerine DB entegrasyonu
Phase 3.5: Cart persistence system
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from auth_dependencies import get_customer_user

router = APIRouter(prefix="/customer", tags=["customer-cart"])

class CartItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    business_id: str
    notes: Optional[str] = None

class CartRestaurant(BaseModel):
    id: str
    name: str
    address: Optional[str] = None

class CartData(BaseModel):
    items: List[CartItem] = []
    restaurant: Optional[CartRestaurant] = None
    updated_at: Optional[datetime] = None

class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1
    product_info: Dict[str, Any]

@router.get("/cart", response_model=CartData)
async def get_customer_cart(
    current_user: dict = Depends(get_customer_user)
):
    """Get customer's cart from database"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Find customer's cart
        cart = await db.customer_carts.find_one({"customer_id": customer_id})
        
        if not cart:
            # Return empty cart
            return CartData(items=[], restaurant=None)
        
        # Convert to response format
        cart_items = []
        for item in cart.get("items", []):
            cart_items.append(CartItem(
                product_id=item["product_id"],
                title=item["title"],
                price=item["price"],
                quantity=item["quantity"],
                business_id=item["business_id"],
                notes=item.get("notes")
            ))
        
        restaurant = None
        if cart.get("restaurant"):
            restaurant = CartRestaurant(**cart["restaurant"])
        
        return CartData(
            items=cart_items,
            restaurant=restaurant,
            updated_at=cart.get("updated_at")
        )
        
    except Exception as e:
        print(f"❌ Error getting cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cart: {str(e)}"
        )

@router.post("/cart")
async def save_customer_cart(
    cart_data: CartData,
    current_user: dict = Depends(get_customer_user)
):
    """Save customer's cart to database"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Prepare cart document
        cart_doc = {
            "customer_id": customer_id,
            "items": [item.dict() for item in cart_data.items],
            "restaurant": cart_data.restaurant.dict() if cart_data.restaurant else None,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Upsert cart
        await db.customer_carts.find_one_and_update(
            {"customer_id": customer_id},
            {"$set": cart_doc},
            upsert=True
        )
        
        print(f"✅ Cart saved for customer {customer_id}")
        
        return {"message": "Cart saved successfully"}
        
    except Exception as e:
        print(f"❌ Error saving cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error saving cart: {str(e)}"
        )

@router.post("/cart/add")
async def add_to_cart(
    add_request: AddToCartRequest,
    current_user: dict = Depends(get_customer_user)
):
    """Add item to customer's cart"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Get current cart
        cart = await db.customer_carts.find_one({"customer_id": customer_id})
        
        if not cart:
            # Create new cart
            cart = {
                "customer_id": customer_id,
                "items": [],
                "restaurant": None
            }
        
        # Check if item already exists
        item_exists = False
        for i, item in enumerate(cart["items"]):
            if item["product_id"] == add_request.product_id:
                # Update quantity
                cart["items"][i]["quantity"] += add_request.quantity
                item_exists = True
                break
        
        if not item_exists:
            # Add new item
            new_item = {
                "product_id": add_request.product_id,
                "title": add_request.product_info.get("title", "Unknown Product"),
                "price": add_request.product_info.get("price", 0),
                "quantity": add_request.quantity,
                "business_id": add_request.product_info.get("business_id", ""),
                "notes": None
            }
            cart["items"].append(new_item)
        
        # Update timestamp
        cart["updated_at"] = datetime.now(timezone.utc)
        
        # Save to database
        await db.customer_carts.find_one_and_update(
            {"customer_id": customer_id},
            {"$set": cart},
            upsert=True
        )
        
        print(f"✅ Item added to cart for customer {customer_id}")
        
        return {"message": "Item added to cart"}
        
    except Exception as e:
        print(f"❌ Error adding to cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding to cart: {str(e)}"
        )

@router.delete("/cart")
async def clear_customer_cart(
    current_user: dict = Depends(get_customer_user)
):
    """Clear customer's cart"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        # Delete cart
        await db.customer_carts.delete_one({"customer_id": customer_id})
        
        print(f"✅ Cart cleared for customer {customer_id}")
        
        return {"message": "Cart cleared successfully"}
        
    except Exception as e:
        print(f"❌ Error clearing cart: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cart: {str(e)}"
        )

@router.patch("/cart/item/{product_id}")
async def update_cart_item_quantity(
    product_id: str,
    quantity: int,
    current_user: dict = Depends(get_customer_user)
):
    """Update item quantity in cart"""
    try:
        from server import db
        
        customer_id = current_user["id"]
        
        if quantity <= 0:
            # Remove item
            await db.customer_carts.update_one(
                {"customer_id": customer_id},
                {"$pull": {"items": {"product_id": product_id}}}
            )
        else:
            # Update quantity
            await db.customer_carts.update_one(
                {"customer_id": customer_id, "items.product_id": product_id},
                {"$set": {"items.$.quantity": quantity, "updated_at": datetime.now(timezone.utc)}}
            )
        
        print(f"✅ Cart item quantity updated for customer {customer_id}")
        
        return {"message": "Item quantity updated"}
        
    except Exception as e:
        print(f"❌ Error updating cart item: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating cart item: {str(e)}"
        )