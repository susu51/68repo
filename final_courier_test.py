#!/usr/bin/env python3
"""
Final Courier Panel API Test - Focused on working scenarios
"""

import requests
import json
import os
from datetime import datetime

def test_courier_panel_apis():
    base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://quickship-49.preview.emergentagent.com')
    if not base_url.endswith('/api'):
        base_url = f"{base_url}/api"
    
    print("🚀 FINAL COURIER PANEL API TESTING")
    print("=" * 60)
    
    # Admin login
    response = requests.post(f'{base_url}/auth/login', json={'email': 'admin@test.com', 'password': '6851'})
    admin_token = response.json()['access_token']
    print("✅ Admin authentication successful")
    
    # Courier login
    response = requests.post(f'{base_url}/auth/login', json={'email': 'testcourier@courier.com', 'password': 'test123'})
    courier_token = response.json()['access_token']
    courier_id = response.json()['user_data']['id']
    print("✅ Courier authentication successful")
    
    # Customer login
    response = requests.post(f'{base_url}/auth/login', json={'email': 'testcustomer@test.com', 'password': 'test123'})
    customer_token = response.json()['access_token']
    print("✅ Customer authentication successful")
    
    # Business login
    response = requests.post(f'{base_url}/auth/login', json={'email': 'testbusiness@test.com', 'password': 'test123'})
    business_token = response.json()['access_token']
    print("✅ Business authentication successful")
    
    print("\n" + "=" * 60)
    print("🧪 TESTING COURIER PANEL ENDPOINTS")
    print("=" * 60)
    
    # 1. Test courier status toggle
    print("\n1. Testing courier status toggle...")
    response = requests.post(f'{base_url}/courier/status/toggle', headers={'Authorization': f'Bearer {courier_token}'})
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Status toggle: {status['message']}")
    else:
        print(f"❌ Status toggle failed: {response.text}")
    
    # 2. Test available orders
    print("\n2. Testing available orders...")
    response = requests.get(f'{base_url}/courier/orders/available', headers={'Authorization': f'Bearer {courier_token}'})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available orders: {data['message']}")
        available_orders = data.get('orders', [])
    else:
        print(f"❌ Available orders failed: {response.text}")
        available_orders = []
    
    # 3. Create a new order for testing if no orders available
    if not available_orders:
        print("\n3. Creating test order...")
        # Create product first
        response = requests.post(f'{base_url}/products', 
                               json={
                                   'name': 'Final Test Pizza',
                                   'description': 'Pizza for final testing',
                                   'price': 75.0,
                                   'category': 'pizza',
                                   'preparation_time_minutes': 25,
                                   'is_available': True
                               }, 
                               headers={'Authorization': f'Bearer {business_token}'})
        
        if response.status_code == 200:
            product_id = response.json()['id']
            print(f"✅ Test product created: {product_id}")
            
            # Create order
            response = requests.post(f'{base_url}/orders',
                                   json={
                                       'delivery_address': 'Final Test Address, İstanbul',
                                       'delivery_lat': 41.0082,
                                       'delivery_lng': 28.9784,
                                       'items': [{
                                           'product_id': product_id,
                                           'product_name': 'Final Test Pizza',
                                           'product_price': 75.0,
                                           'quantity': 1,
                                           'subtotal': 75.0
                                       }],
                                       'total_amount': 75.0,
                                       'notes': 'Final test order'
                                   },
                                   headers={'Authorization': f'Bearer {customer_token}'})
            
            if response.status_code == 200:
                test_order_id = response.json()['id']
                print(f"✅ Test order created: {test_order_id}")
                
                # Update order to pending status for courier acceptance
                import asyncio
                from motor.motor_asyncio import AsyncIOMotorClient
                from dotenv import load_dotenv
                
                async def update_order():
                    load_dotenv('/app/backend/.env')
                    mongo_url = os.environ['MONGO_URL']
                    client = AsyncIOMotorClient(mongo_url)
                    db = client.delivertr_database
                    
                    await db.orders.update_one(
                        {'id': test_order_id},
                        {'$set': {'status': 'pending'}, '$unset': {'courier_id': ''}}
                    )
                    client.close()
                
                asyncio.run(update_order())
                print("✅ Order status updated to pending")
                
                # Get available orders again
                response = requests.get(f'{base_url}/courier/orders/available', headers={'Authorization': f'Bearer {courier_token}'})
                if response.status_code == 200:
                    available_orders = response.json().get('orders', [])
                    print(f"✅ Updated available orders: {len(available_orders)} orders")
    
    # 4. Test order acceptance
    if available_orders:
        print("\n4. Testing order acceptance...")
        order_id = available_orders[0]['id']
        response = requests.post(f'{base_url}/courier/orders/{order_id}/accept', 
                               headers={'Authorization': f'Bearer {courier_token}'})
        if response.status_code == 200:
            print(f"✅ Order accepted: {response.json()['message']}")
            
            # 5. Test order status updates
            print("\n5. Testing order status updates...")
            
            # Update to picked_up
            response = requests.post(f'{base_url}/courier/orders/{order_id}/update-status',
                                   json={'status': 'picked_up', 'notes': 'Order picked up for final test'},
                                   headers={'Authorization': f'Bearer {courier_token}'})
            if response.status_code == 200:
                print(f"✅ Status updated to picked_up: {response.json()['message']}")
                
                # Update to delivered
                response = requests.post(f'{base_url}/courier/orders/{order_id}/update-status',
                                       json={'status': 'delivered', 'notes': 'Order delivered successfully'},
                                       headers={'Authorization': f'Bearer {courier_token}'})
                if response.status_code == 200:
                    print(f"✅ Status updated to delivered: {response.json()['message']}")
                else:
                    print(f"❌ Delivered status update failed: {response.text}")
            else:
                print(f"❌ Picked up status update failed: {response.text}")
        else:
            print(f"❌ Order acceptance failed: {response.text}")
    
    # 6. Test order history
    print("\n6. Testing order history...")
    response = requests.get(f'{base_url}/courier/orders/history', headers={'Authorization': f'Bearer {courier_token}'})
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Order history: {len(history['orders'])} orders, Total earnings: ₺{history['summary']['total_earnings']}")
    else:
        print(f"❌ Order history failed: {response.text}")
    
    # 7. Test notifications
    print("\n7. Testing notifications...")
    response = requests.get(f'{base_url}/courier/notifications', headers={'Authorization': f'Bearer {courier_token}'})
    if response.status_code == 200:
        notifications = response.json()
        print(f"✅ Notifications: {notifications['unread_count']} unread notifications")
        
        # Test marking notification as read if any exist
        if notifications['notifications']:
            notification_id = notifications['notifications'][0]['id']
            response = requests.post(f'{base_url}/courier/notifications/{notification_id}/read',
                                   headers={'Authorization': f'Bearer {courier_token}'})
            if response.status_code == 200:
                print(f"✅ Notification marked as read: {response.json()['message']}")
            else:
                print(f"❌ Mark notification read failed: {response.text}")
    else:
        print(f"❌ Notifications failed: {response.text}")
    
    # 8. Test messages
    print("\n8. Testing messages...")
    response = requests.get(f'{base_url}/courier/messages', headers={'Authorization': f'Bearer {courier_token}'})
    if response.status_code == 200:
        messages = response.json()
        print(f"✅ Messages: {len(messages['messages'])} messages retrieved")
    else:
        print(f"❌ Messages failed: {response.text}")
    
    # 9. Test admin messaging
    print("\n9. Testing admin messaging...")
    response = requests.post(f'{base_url}/admin/courier/message',
                           json={
                               'courier_ids': [courier_id],
                               'title': 'Final Test Message',
                               'message': 'This is a final test message from admin'
                           },
                           headers={'Authorization': f'Bearer {admin_token}'})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Admin message sent: {result['message']}")
    else:
        print(f"❌ Admin messaging failed: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 COURIER PANEL API TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_courier_panel_apis()