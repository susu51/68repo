"""
Customer Order Creation & Management Routes
Phase 2: Customer Order Implementation
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from models import UserRole, OrderStatus
from auth_dependencies import get_customer_user

router = APIRouter(prefix="/orders", tags=["orders"])

# Request/Response Models
class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    notes: Optional[str] = None

class DeliveryAddress(BaseModel):
    label: str
    address: str
    lat: float
    lng: float
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    business_id: str
    items: List[OrderItem]
    delivery_address: DeliveryAddress
    payment_method: str = "cash_on_delivery"  # online, cash_on_delivery, pos_on_delivery
    coupon_code: Optional[str] = None
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    business_id: str
    business_name: str
    items: List[OrderItem]
    total_amount: float
    delivery_fee: float = 10.0
    delivery_address: DeliveryAddress
    payment_method: str
    payment_status: str = "pending"  # pending, paid_mock, paid, failed
    status: OrderStatus
    estimated_delivery: Optional[str] = None
    created_at: datetime

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: dict = Depends(get_customer_user)
):
    """Create new customer order"""
    try:
        from server import db
        
        # Verify business exists and is active
        business = await db.businesses.find_one({
            "_id": order_data.business_id,
            "is_active": True
        })
        
        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business not found or inactive"
            )
        
        # Verify all products exist and are available
        product_ids = [item.product_id for item in order_data.items]
        products = await db.menu_items.find({
            "_id": {"$in": product_ids},
            "business_id": order_data.business_id,
            "is_available": True
        }).to_list(length=None)
        
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=400,
                detail="Some products are not available or don't belong to this business"
            )
        
        # Calculate total amount
        total_amount = 0
        for item in order_data.items:
            product = next((p for p in products if p["_id"] == item.product_id), None)
            if product:
                total_amount += product["price"] * item.quantity
        
        # Delivery fee
        delivery_fee = 10.0
        
        # Determine payment status based on payment method
        payment_status = "pending"
        if order_data.payment_method == "online":
            payment_status = "paid_mock"  # Mock payment for online orders
        elif order_data.payment_method in ["cash_on_delivery", "pos_on_delivery"]:
            payment_status = "pending"  # Will be paid on delivery
        
        # Create order document
        order_doc = {
            "_id": str(uuid.uuid4()),
            "customer_id": current_user["id"],
            "business_id": order_data.business_id,
            "business_name": business["name"],
            "items": [item.dict() for item in order_data.items],
            "total_amount": round(total_amount, 2),
            "delivery_fee": delivery_fee,
            "delivery_address": order_data.delivery_address.dict(),
            "payment_method": order_data.payment_method,
            "payment_status": payment_status,
            "coupon_code": order_data.coupon_code,
            "status": OrderStatus.CREATED.value,
            "notes": order_data.notes,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert to database
        # Insert order into database
        try:
            print(f"📦 [ROUTES/ORDERS] Inserting order: {order_doc.get('id')}")
            print(f"   Business ID: {order_doc.get('business_id')}")
            print(f"   Customer ID: {order_doc.get('customer_id')}")
            print(f"   Status: {order_doc.get('status')}")
            
            result = await db.orders.insert_one(order_doc)
            
            print(f"✅ Order inserted successfully!")
            print(f"   Inserted ID: {result.inserted_id}")
            print(f"   Acknowledged: {result.acknowledged}")
            
        except Exception as insert_error:
            print(f"❌ DB INSERT ERROR: {insert_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Database insert failed: {str(insert_error)}")
        
        # Calculate estimated delivery time (45 minutes from creation)
        estimated_delivery = datetime.now(timezone.utc)
        estimated_delivery = estimated_delivery.replace(minute=estimated_delivery.minute + 45)
        
        return OrderResponse(
            id=order_doc["_id"],
            customer_id=order_doc["customer_id"],
            business_id=order_doc["business_id"],
            business_name=order_doc["business_name"],
            items=[OrderItem(**item) for item in order_doc["items"]],
            total_amount=order_doc["total_amount"],
            delivery_fee=order_doc["delivery_fee"],
            delivery_address=DeliveryAddress(**order_doc["delivery_address"]),
            payment_method=order_doc["payment_method"],
            payment_status=order_doc["payment_status"],
            status=OrderStatus(order_doc["status"]),
            estimated_delivery=estimated_delivery.strftime("%H:%M"),
            created_at=order_doc["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating order: {str(e)}"
        )

@router.get("/my", response_model=List[OrderResponse])
async def get_my_orders(
    current_user: dict = Depends(get_customer_user)
):
    """Get customer's own orders"""
    try:
        from server import db
        
        orders = await db.orders.find({
            "customer_id": current_user["id"]
        }).sort("created_at", -1).to_list(length=None)
        
        order_responses = []
        for order in orders:
            # Calculate estimated delivery based on status
            if order["status"] in ["created", "preparing"]:
                estimated_time = "45 dk"
            elif order["status"] in ["picked_up", "delivering"]:
                estimated_time = "15 dk"
            elif order["status"] == "delivered":
                estimated_time = "Teslim edildi"
            else:
                estimated_time = "Hazırlanıyor"
                
            order_responses.append(OrderResponse(
                id=str(order["_id"]),
                customer_id=order["customer_id"],
                business_id=order["business_id"],
                business_name=order.get("business_name", "Unknown Business"),
                items=[OrderItem(**item) for item in order["items"]],
                total_amount=order["total_amount"],
                delivery_fee=order.get("delivery_fee", 10.0),
                delivery_address=DeliveryAddress(**order["delivery_address"]),
                payment_method=order["payment_method"],
                payment_status=order.get("payment_status", "pending"),
                status=OrderStatus(order["status"]),
                estimated_delivery=estimated_time,
                created_at=order["created_at"]
            ))
        
        return order_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching orders: {str(e)}"
        )

@router.get("/{order_id}/track")
async def track_order(
    order_id: str,
    current_user: dict = Depends(get_customer_user)
):
    """Track specific order - customer can only track their own orders"""
    try:
        from server import db
        
        order = await db.orders.find_one({
            "_id": order_id,
            "customer_id": current_user["id"]
        })
        
        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found or access denied"
            )
        
        # Get courier location if order is being delivered
        courier_location = None
        if order["status"] in ["picked_up", "delivering"] and order.get("courier_id"):
            try:
                # Check Redis first for real-time location
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                location_key = f"courier_location:{order['courier_id']}"
                location_data = r.get(location_key)
                
                if location_data:
                    import json
                    courier_location = json.loads(location_data)
                else:
                    # Fallback to MongoDB
                    courier_loc = await db.courier_locations.find_one(
                        {"courier_id": order["courier_id"]},
                        sort=[("timestamp", -1)]
                    )
                    if courier_loc:
                        courier_location = {
                            "lat": courier_loc["location"]["coordinates"][1],
                            "lng": courier_loc["location"]["coordinates"][0],
                            "timestamp": courier_loc["timestamp"].isoformat()
                        }
            except Exception as e:
                print(f"Error fetching courier location: {e}")
        
        # Calculate estimated delivery
        if order["status"] in ["created", "preparing"]:
            estimated_delivery = "45 dakika"
        elif order["status"] in ["picked_up", "delivering"]:
            estimated_delivery = "15 dakika"
        elif order["status"] == "delivered":
            estimated_delivery = "Teslim edildi"
        else:
            estimated_delivery = "Hazırlanıyor"
        
        return {
            "order_id": order_id,
            "status": order["status"],
            "business_name": order.get("business_name", "Unknown"),
            "total_amount": order["total_amount"],
            "estimated_delivery": estimated_delivery,
            "courier_location": courier_location,
            "delivery_address": order["delivery_address"],
            "created_at": order["created_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking order: {str(e)}"
        )