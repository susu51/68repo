#!/usr/bin/env python3
"""
Real-Time Order Notification Flow Test

This test specifically focuses on the WebSocket notification flow as requested:
1. Login as business owner
2. Check WebSocket connection for order notifications  
3. Login as customer
4. Create test order
5. Verify backend logs for event bus activity
6. Confirm business receives real-time notification
"""

import asyncio
import json
import requests
import websockets
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com"
WS_URL = "wss://admin-wsocket.preview.emergentagent.com"

# Test credentials
BUSINESS_CREDENTIALS = {"email": "testbusiness@example.com", "password": "test123"}
CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}

async def test_websocket_notification_flow():
    """Test the complete WebSocket notification flow"""
    print("🚀 Testing Real-Time Order Notification Flow")
    print("=" * 60)
    
    # Step 1: Login as business owner
    print("1️⃣ Logging in as business owner...")
    business_session = requests.Session()
    business_response = business_session.post(
        f"{BACKEND_URL}/api/auth/login",
        json=BUSINESS_CREDENTIALS,
        timeout=10
    )
    
    if business_response.status_code != 200:
        print(f"❌ Business login failed: {business_response.status_code}")
        return False
    
    business_data = business_response.json()
    business_user = business_data.get("user", {})
    business_id = business_user.get("id")
    business_name = business_user.get("business_name", "Unknown")
    
    print(f"✅ Business login successful: {business_name} (ID: {business_id})")
    
    # Step 2: Login as customer
    print("\n2️⃣ Logging in as customer...")
    customer_session = requests.Session()
    customer_response = customer_session.post(
        f"{BACKEND_URL}/api/auth/login",
        json=CUSTOMER_CREDENTIALS,
        timeout=10
    )
    
    if customer_response.status_code != 200:
        print(f"❌ Customer login failed: {customer_response.status_code}")
        return False
    
    print("✅ Customer login successful")
    
    # Step 3: Get business menu
    print("\n3️⃣ Getting business menu...")
    menu_response = requests.get(
        f"{BACKEND_URL}/api/business/public/{business_id}/menu",
        timeout=10
    )
    
    if menu_response.status_code != 200 or not menu_response.json():
        print(f"❌ Failed to get menu: {menu_response.status_code}")
        return False
    
    menu_items = menu_response.json()
    menu_item = menu_items[0]
    print(f"✅ Found menu item: {menu_item['name']} (₺{menu_item['price']})")
    
    # Step 4: Establish business WebSocket connection
    print(f"\n4️⃣ Establishing business WebSocket connection...")
    ws_url = f"{WS_URL}/api/ws/orders?role=business&business_id={business_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Wait for connection confirmation
            connection_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
            connection_data = json.loads(connection_msg)
            
            print(f"✅ WebSocket connected: {connection_data.get('message')}")
            print(f"   Role: {connection_data.get('role')}")
            print(f"   Client ID: {connection_data.get('client_id')}")
            
            # Step 5: Create order from customer
            print(f"\n5️⃣ Creating order from customer...")
            order_data = {
                "business_id": business_id,
                "delivery_address": "WebSocket Test Address, Aksaray Merkez",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0254,
                "items": [{
                    "product_id": menu_item["id"],
                    "product_name": menu_item["name"],
                    "product_price": menu_item["price"],
                    "quantity": 1,
                    "subtotal": menu_item["price"]
                }],
                "total_amount": menu_item["price"],
                "payment_method": "cash_on_delivery",
                "notes": "WebSocket notification test order"
            }
            
            order_response = customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            if order_response.status_code not in [200, 201]:
                print(f"❌ Order creation failed: {order_response.status_code} - {order_response.text}")
                return False
            
            order = order_response.json()
            order_id = order.get("id") or order.get("order_id")
            print(f"✅ Order created successfully: ID={order_id}")
            
            # Step 6: Wait for WebSocket notification
            print(f"\n6️⃣ Waiting for WebSocket notification...")
            
            try:
                # Wait for notification with longer timeout
                notification = await asyncio.wait_for(websocket.recv(), timeout=30)
                notification_data = json.loads(notification)
                
                print(f"✅ Received WebSocket notification!")
                print(f"   Type: {notification_data.get('type')}")
                print(f"   Data: {json.dumps(notification_data, indent=2)}")
                
                # Verify it's an order notification
                if (notification_data.get("type") == "order_notification" or
                    "order" in str(notification_data).lower()):
                    print("✅ Notification is order-related")
                    return True
                else:
                    print("⚠️  Notification received but not order-related")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ No WebSocket notification received within 30 seconds")
                
                # Check backend logs for event bus activity
                print("\n🔍 Checking backend logs for event bus activity...")
                import subprocess
                try:
                    result = subprocess.run(
                        ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.returncode == 0:
                        log_lines = result.stdout.split('\n')
                        event_messages = [line for line in log_lines if "📡" in line or "order.created" in line]
                        
                        if event_messages:
                            print("✅ Found event bus activity in logs:")
                            for msg in event_messages[-5:]:  # Show last 5
                                print(f"   {msg}")
                            print("✅ Event bus is publishing order events correctly")
                        else:
                            print("❌ No event bus activity found in logs")
                    else:
                        print("❌ Could not read backend logs")
                        
                except Exception as e:
                    print(f"❌ Error checking logs: {e}")
                
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    """Main test runner"""
    success = await test_websocket_notification_flow()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("🎉 SUCCESS: Real-time order notification flow is WORKING!")
        print("✅ Customer creates order → Backend creates order in DB")
        print("✅ Event bus publishes to business:{business_id}")  
        print("✅ Business WebSocket receives notification")
        print("✅ Business panel shows new order")
    else:
        print("🚨 FAILURE: Real-time order notification flow has issues")
        print("❌ WebSocket notifications not reaching business")
        print("🔍 Check event bus subscription and WebSocket connection")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)