#!/usr/bin/env python3
"""
Debug Business Menu and Order Flow
"""

import requests
import json

BACKEND_URL = "https://admin-wsocket.preview.emergentagent.com/api"

# Login as customer
customer_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"email": "testcustomer@example.com", "password": "test123"}
)

if customer_response.status_code == 200:
    customer_token = customer_response.json()["access_token"]
    print(f"✅ Customer login successful")
    
    # Get nearby businesses
    headers = {"Authorization": f"Bearer {customer_token}"}
    params = {"lat": 40.9833, "lng": 29.0167, "radius": 5000}
    
    nearby_response = requests.get(
        f"{BACKEND_URL}/nearby/businesses",
        headers=headers,
        params=params
    )
    
    if nearby_response.status_code == 200:
        businesses = nearby_response.json()
        business = businesses[0]  # Use first business
        business_id = business.get('id')
        business_name = business.get('name')
        
        print(f"Using business: {business_name} (ID: {business_id})")
        
        # Get menu for this business
        menu_response = requests.get(
            f"{BACKEND_URL}/nearby/businesses/{business_id}/menu",
            headers=headers
        )
        
        if menu_response.status_code == 200:
            menu_items = menu_response.json()
            print(f"Menu items: {len(menu_items)}")
            
            if menu_items:
                item = menu_items[0]
                print(f"First item: {item.get('name')} - ₺{item.get('price')}")
                
                # Create order with correct business ID
                order_data = {
                    "business_id": business_id,  # Use the actual business ID
                    "business_name": business_name,
                    "delivery_address": "Kadıköy Test Address, İstanbul",
                    "delivery_lat": 40.9833,
                    "delivery_lng": 29.0167,
                    "items": [
                        {
                            "product_id": item.get("id", "test-product"),
                            "product_name": item.get("name", "Test Product"),
                            "product_price": float(item.get("price", 25.0)),
                            "quantity": 1,
                            "subtotal": float(item.get("price", 25.0))
                        }
                    ],
                    "total_amount": float(item.get("price", 25.0)),
                    "notes": "E2E Test Order"
                }
                
                order_response = requests.post(
                    f"{BACKEND_URL}/orders",
                    json=order_data,
                    headers=headers
                )
                
                print(f"Order creation status: {order_response.status_code}")
                if order_response.status_code == 200:
                    order = order_response.json()
                    order_id = order.get("id")
                    print(f"✅ Order created: {order_id}")
                    print(f"Order business_id: {order.get('business_id')}")
                    print(f"Expected business_id: {business_id}")
                else:
                    print(f"❌ Order creation failed: {order_response.text}")
            else:
                print("❌ No menu items found")
        else:
            print(f"❌ Menu retrieval failed: {menu_response.status_code}")
    else:
        print(f"❌ Nearby businesses failed: {nearby_response.status_code}")
else:
    print(f"❌ Customer login failed: {customer_response.status_code}")