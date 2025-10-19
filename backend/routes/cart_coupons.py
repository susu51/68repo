"""
Cart Coupon Application - Phase 3
Apply discount coupons to cart
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from auth_cookie import get_current_user_from_cookie_or_bearer
from models_package.coupons import ApplyCouponRequest, ApplyCouponResponse, CouponType, CouponScope

router = APIRouter(prefix="/cart", tags=["cart-coupons"])

@router.post("/apply-coupon", response_model=ApplyCouponResponse)
async def apply_coupon(
    request: ApplyCouponRequest,
    current_user: dict = Depends(get_current_user_from_cookie_or_bearer)
):
    """
    Apply coupon to cart
    
    Validates coupon and calculates discounts.
    For scope=item: applies to individual items (unit_discount).
    For scope=cart: applies to cart total.
    """
    from server import db
    
    try:
        user_id = current_user["id"]
        coupon_code = request.code.upper()
        
        # Find coupon
        coupon = await db.coupons.find_one({"code": coupon_code})
        
        if not coupon:
            raise HTTPException(
                status_code=404,
                detail="Kupon geçersiz veya kullanım koşulları sağlanmıyor."
            )
        
        # Validate coupon
        now = datetime.now(timezone.utc)
        
        # Check if active
        if not coupon.get("is_active", False):
            raise HTTPException(
                status_code=400,
                detail="Kupon geçersiz veya kullanım koşulları sağlanmıyor."
            )
        
        # Check date range
        valid_from = coupon.get("valid_from")
        valid_to = coupon.get("valid_to")
        
        if valid_from and now < valid_from:
            raise HTTPException(
                status_code=400,
                detail="Kupon henüz geçerli değil."
            )
        
        if valid_to and now > valid_to:
            raise HTTPException(
                status_code=400,
                detail="Kupon süresi dolmuş."
            )
        
        # Check global limit
        global_limit = coupon.get("global_limit")
        current_uses = coupon.get("current_uses", 0)
        
        if global_limit and current_uses >= global_limit:
            raise HTTPException(
                status_code=400,
                detail="Kupon kullanım limiti dolmuş."
            )
        
        # For actual implementation, we'd need cart data here
        # For now, return a mock response showing how it would work
        
        # MOCK CART DATA (in real implementation, this comes from request or session)
        mock_items = [
            {
                "product_id": "1",
                "name": "Pizza Margherita",
                "unit_price": 50.0,
                "quantity": 2,
                "category": "pizza"
            },
            {
                "product_id": "2",
                "name": "Cola",
                "unit_price": 10.0,
                "quantity": 1,
                "category": "beverage"
            }
        ]
        
        subtotal = sum(item["unit_price"] * item["quantity"] for item in mock_items)
        
        # Check min_basket
        min_basket = coupon.get("min_basket")
        if min_basket and subtotal < min_basket:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum sepet tutarı ₺{min_basket:.2f} olmalıdır."
            )
        
        # Calculate discount
        coupon_type = coupon.get("type")
        coupon_scope = coupon.get("scope")
        coupon_value = coupon.get("value", 0)
        
        discount_amount = 0
        discounted_items = []
        
        if coupon_scope == CouponScope.ITEM.value:
            # Item-level discount
            for item in mock_items:
                unit_price = item["unit_price"]
                quantity = item["quantity"]
                
                if coupon_type == CouponType.PERCENT.value:
                    unit_discount = unit_price * (coupon_value / 100)
                else:  # fixed
                    unit_discount = min(coupon_value, unit_price)
                
                final_unit_price = max(0, unit_price - unit_discount)
                line_total = final_unit_price * quantity
                
                discounted_items.append({
                    "name": item["name"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "unit_discount": unit_discount,
                    "final_unit_price": final_unit_price,
                    "line_total": line_total
                })
                
                discount_amount += unit_discount * quantity
        
        else:  # cart-level discount
            if coupon_type == CouponType.PERCENT.value:
                discount_amount = subtotal * (coupon_value / 100)
            else:  # fixed
                discount_amount = min(coupon_value, subtotal)
            
            # Items remain unchanged
            for item in mock_items:
                discounted_items.append({
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "unit_discount": 0,
                    "final_unit_price": item["unit_price"],
                    "line_total": item["unit_price"] * item["quantity"]
                })
        
        grand_total = max(0, subtotal - discount_amount)
        
        return ApplyCouponResponse(
            success=True,
            message=f"Kupon uygulandı: {coupon.get('title')}",
            coupon_id=coupon.get("_id"),
            discount_amount=discount_amount,
            items=discounted_items,
            totals={
                "subtotal": subtotal,
                "discount": discount_amount,
                "grand": grand_total
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error applying coupon: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Kupon uygulanırken hata oluştu: {str(e)}"
        )
