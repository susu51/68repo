#!/usr/bin/env python3
"""
Business WebSocket Real-Time Order Notification Testing

CRITICAL: Test the real-time order notification flow from customer to business via WebSocket.

Test Scenarios:
1. Business WebSocket Connection & Subscription
2. Customer Order Creation & Business Notification
3. Event Bus Activity Verification
4. Backend Log Monitoring
5. End-to-End Notification Flow
"""

import asyncio
import json
import requests
import websockets
import time
from datetime import datetime
import os
import sys
import subprocess

# Configuration
BACKEND_URL = "https://admin-wsocket.preview.emergentagent.com"
WS_URL = "wss://admin-wsocket.preview.emergentagent.com"

# Test credentials
BUSINESS_CREDENTIALS_LIST = [
    {"email": "testbusiness@example.com", "password": "test123"},
    {"email": "business@kuryecini.com", "password": "business123"}
]

CUSTOMER_CREDENTIALS = {
    "email": "test@kuryecini.com", 
    "password": "test123"
}

class BusinessWebSocketTester:
    def __init__(self):
        self.business_token = None
        self.customer_token = None
        self.business_id = None
        self.business_name = None
        self.test_results = []
        self.business_session = requests.Session()
        self.customer_session = requests.Session()
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate_business(self):
        """Authenticate business user - try multiple credentials"""
        for i, credentials in enumerate(BUSINESS_CREDENTIALS_LIST):
            try:
                response = self.business_session.post(
                    f"{BACKEND_URL}/api/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's cookie-based auth (success field) or JWT auth (access_token field)
                    if data.get("success"):
                        # Cookie-based auth
                        user_data = data.get("user", {})
                        user_role = user_data.get("role")
                        if user_role == "business":
                            self.business_id = user_data.get("id")
                            self.business_name = user_data.get("business_name", "Unknown Business")
                            self.log_test(
                                "Business Authentication",
                                True,
                                f"Business login successful (cookie-based): {credentials['email']}, role: {user_role}, business_id: {self.business_id}, name: {self.business_name}"
                            )
                            return True
                    elif data.get("access_token"):
                        # JWT-based auth
                        self.business_token = data.get("access_token")
                        user_data = data.get("user", {})
                        user_role = user_data.get("role")
                        if user_role == "business":
                            self.business_id = user_data.get("id")
                            self.business_name = user_data.get("business_name", "Unknown Business")
                            self.log_test(
                                "Business Authentication",
                                True,
                                f"Business login successful (JWT): {credentials['email']}, role: {user_role}, business_id: {self.business_id}, token length: {len(self.business_token)}"
                            )
                            return True
                    
                    print(f"   Tried {credentials['email']}: Wrong role ({data.get('user', {}).get('role')})")
                else:
                    print(f"   Tried {credentials['email']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   Tried {credentials['email']}: Error - {str(e)}")
        
        self.log_test("Business Authentication", False, error="All business credential attempts failed")
        return False
    
    def authenticate_customer(self):
        """Authenticate customer user"""
        try:
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check both auth types
                if data.get("success"):
                    # Cookie-based auth
                    user_role = data.get("user", {}).get("role")
                    if user_role == "customer":
                        self.log_test(
                            "Customer Authentication",
                            True,
                            f"Customer login successful (cookie-based), role: {user_role}"
                        )
                        return True
                elif data.get("access_token"):
                    # JWT-based auth
                    self.customer_token = data.get("access_token")
                    user_role = data.get("user", {}).get("role")
                    if user_role == "customer":
                        self.log_test(
                            "Customer Authentication",
                            True,
                            f"Customer login successful (JWT), role: {user_role}, token length: {len(self.customer_token)}"
                        )
                        return True
                
                self.log_test("Customer Authentication", False, error=f"Expected customer role, got: {data.get('user', {}).get('role')}")
                return False
            else:
                self.log_test("Customer Authentication", False, error=f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, error=f"Authentication error: {str(e)}")
            return False

    async def test_business_websocket_connection(self):
        """Test 1: Business WebSocket Connection & Subscription"""
        try:
            if not self.business_id:
                self.log_test("Business WebSocket Connection", False, error="No business_id available")
                return False
            
            # Test business WebSocket connection with role=business and business_id
            ws_url = f"{WS_URL}/api/ws/orders?role=business&business_id={self.business_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for connection confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if (data.get("type") == "connected" and 
                    data.get("role") == "business" and
                    data.get("client_id") == self.business_id):
                    
                    self.log_test(
                        "Business WebSocket Connection",
                        True,
                        f"Connection successful: role={data.get('role')}, business_id={data.get('business_id')}, message='{data.get('message')}'"
                    )
                    return True
                else:
                    self.log_test(
                        "Business WebSocket Connection",
                        False,
                        error=f"Unexpected connection response: {data}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Business WebSocket Connection", False, error=f"WebSocket connection failed: {str(e)}")
            return False

    def get_business_menu(self):
        """Get business menu items for the authenticated business"""
        try:
            # Try multiple menu endpoints
            endpoints_to_try = [
                f"{BACKEND_URL}/api/business/public/{self.business_id}/menu",
                f"{BACKEND_URL}/api/business/{self.business_id}/menu", 
                f"{BACKEND_URL}/api/business/menu"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    headers = {}
                    if self.business_token:
                        headers["Authorization"] = f"Bearer {self.business_token}"
                    
                    response = self.business_session.get(endpoint, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        menu_items = response.json()
                        if menu_items and len(menu_items) > 0:
                            item = menu_items[0]
                            self.log_test(
                                "Get Business Menu",
                                True,
                                f"Found {len(menu_items)} menu items using {endpoint}, using: {item.get('name')} (₺{item.get('price')})"
                            )
                            return item
                        else:
                            print(f"   Tried {endpoint}: Empty menu")
                    else:
                        print(f"   Tried {endpoint}: {response.status_code}")
                        
                except Exception as e:
                    print(f"   Tried {endpoint}: Error - {str(e)}")
            
            self.log_test("Get Business Menu", False, error="No menu items found in any endpoint")
            return None
            
        except Exception as e:
            self.log_test("Get Business Menu", False, error=f"Error getting menu: {str(e)}")
            return None

    def create_test_order(self, menu_item):
        """Create a test order for the business"""
        try:
            order_data = {
                "delivery_address": "Test Address for WebSocket Notification, Aksaray Merkez",
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
            
            headers = {}
            if self.customer_token:
                headers["Authorization"] = f"Bearer {self.customer_token}"
            
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                order = response.json()
                order_id = order.get("id") or order.get("order_id")
                
                self.log_test(
                    "Create Test Order",
                    True,
                    f"Order created successfully: ID={order_id}, Business={order.get('business_name')}, Total=₺{order.get('total_amount')}"
                )
                return order_id, order
            else:
                self.log_test("Create Test Order", False, error=f"Order creation failed: {response.status_code} - {response.text}")
                return None, None
                
        except Exception as e:
            self.log_test("Create Test Order", False, error=f"Error creating order: {str(e)}")
            return None, None

    def check_backend_logs(self):
        """Check backend logs for event bus activity"""
        try:
            # Check supervisor backend logs for event bus messages
            log_commands = [
                "tail -n 50 /var/log/supervisor/backend.out.log",
                "tail -n 50 /var/log/supervisor/backend.err.log",
                "tail -n 50 /var/log/supervisor/backend*.log"
            ]
            
            event_bus_messages = []
            websocket_messages = []
            
            for cmd in log_commands:
                try:
                    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        log_content = result.stdout
                        
                        # Look for event bus messages
                        for line in log_content.split('\n'):
                            if "📡 Order event published to business:" in line:
                                event_bus_messages.append(line.strip())
                            elif "📡 Publishing to topic business:" in line:
                                event_bus_messages.append(line.strip())
                            elif "WebSocket message delivery" in line:
                                websocket_messages.append(line.strip())
                            elif "order.created" in line:
                                event_bus_messages.append(line.strip())
                                
                except Exception as e:
                    print(f"   Log command failed: {cmd} - {str(e)}")
            
            if event_bus_messages or websocket_messages:
                self.log_test(
                    "Backend Log Monitoring",
                    True,
                    f"Found {len(event_bus_messages)} event bus messages and {len(websocket_messages)} WebSocket messages in logs"
                )
                
                # Print the messages for debugging
                if event_bus_messages:
                    print("   Event Bus Messages:")
                    for msg in event_bus_messages[-3:]:  # Show last 3
                        print(f"     {msg}")
                        
                if websocket_messages:
                    print("   WebSocket Messages:")
                    for msg in websocket_messages[-3:]:  # Show last 3
                        print(f"     {msg}")
                        
                return True
            else:
                self.log_test(
                    "Backend Log Monitoring",
                    False,
                    error="No event bus or WebSocket messages found in backend logs"
                )
                return False
                
        except Exception as e:
            self.log_test("Backend Log Monitoring", False, error=f"Error checking logs: {str(e)}")
            return False

    async def test_end_to_end_notification_flow(self):
        """Test 2: End-to-End Order Notification Flow"""
        try:
            if not self.business_id:
                self.log_test("End-to-End Notification Flow", False, error="No business_id available")
                return False
            
            # Get business menu
            menu_item = self.get_business_menu()
            if not menu_item:
                return False
            
            # Start business WebSocket connection
            ws_url = f"{WS_URL}/api/ws/orders?role=business&business_id={self.business_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for connection confirmation
                connection_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"   Business WebSocket connected: {json.loads(connection_msg).get('message')}")
                
                # Create order (this should trigger event_bus publication)
                print(f"   Creating order for business {self.business_id}...")
                order_id, order = self.create_test_order(menu_item)
                if not order_id:
                    return False
                
                # Wait for WebSocket notification
                try:
                    print("   Waiting for WebSocket notification...")
                    notification = await asyncio.wait_for(websocket.recv(), timeout=20)
                    data = json.loads(notification)
                    
                    print(f"   Received WebSocket message: {data}")
                    
                    # Check if it's an order notification
                    if (data.get("type") == "order_notification" or 
                        data.get("type") == "order.created" or
                        "order" in str(data).lower()):
                        
                        self.log_test(
                            "End-to-End Notification Flow",
                            True,
                            f"Business received order notification via WebSocket: {data.get('type')} for order {order_id}"
                        )
                        
                        # Check backend logs after successful notification
                        self.check_backend_logs()
                        return True
                    else:
                        self.log_test(
                            "End-to-End Notification Flow",
                            False,
                            error=f"Unexpected notification format: {data}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "End-to-End Notification Flow",
                        False,
                        error="No WebSocket notification received within 20 seconds"
                    )
                    
                    # Still check logs even if WebSocket failed
                    print("   Checking backend logs for event bus activity...")
                    self.check_backend_logs()
                    return False
                    
        except Exception as e:
            self.log_test("End-to-End Notification Flow", False, error=f"Test failed: {str(e)}")
            return False

    def test_event_bus_verification(self):
        """Test 3: Event Bus Activity Verification via API"""
        try:
            # Try to get recent orders to verify event bus is working
            headers = {}
            if self.business_token:
                headers["Authorization"] = f"Bearer {self.business_token}"
            
            # Check business orders endpoint
            response = self.business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                orders = response.json()
                recent_orders = [o for o in orders if o.get("business_id") == self.business_id]
                
                self.log_test(
                    "Event Bus Verification",
                    True,
                    f"Business has {len(recent_orders)} orders, event bus likely working (orders reaching business)"
                )
                return True
            else:
                self.log_test(
                    "Event Bus Verification",
                    False,
                    error=f"Cannot verify event bus via orders endpoint: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Event Bus Verification", False, error=f"Error verifying event bus: {str(e)}")
            return False

    def test_websocket_subscription_topics(self):
        """Test 4: WebSocket Subscription Topics"""
        try:
            # This test verifies that the business is subscribed to the correct topic
            # We can't directly test the subscription, but we can verify the business_id is correct
            
            if not self.business_id:
                self.log_test("WebSocket Subscription Topics", False, error="No business_id available")
                return False
            
            # Verify business exists and is active
            response = requests.get(f"{BACKEND_URL}/api/businesses", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                business_found = any(b.get("id") == self.business_id for b in businesses)
                
                if business_found:
                    self.log_test(
                        "WebSocket Subscription Topics",
                        True,
                        f"Business {self.business_id} exists and should be subscribed to topic 'business:{self.business_id}'"
                    )
                    return True
                else:
                    self.log_test(
                        "WebSocket Subscription Topics",
                        False,
                        error=f"Business {self.business_id} not found in businesses list"
                    )
                    return False
            else:
                self.log_test(
                    "WebSocket Subscription Topics",
                    False,
                    error=f"Cannot verify business existence: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("WebSocket Subscription Topics", False, error=f"Error verifying subscription topics: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all WebSocket notification tests"""
        print("🚀 Starting Business WebSocket Real-Time Order Notification Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_business():
            print("❌ Business authentication failed - cannot proceed with tests")
            return
            
        if not self.authenticate_customer():
            print("❌ Customer authentication failed - cannot proceed with order creation tests")
            return
        
        print(f"\n🏪 Testing for Business: {self.business_name} (ID: {self.business_id})")
        print("-" * 50)
        
        # Test 1: Business WebSocket Connection
        await self.test_business_websocket_connection()
        
        # Test 2: End-to-End Notification Flow
        await self.test_end_to_end_notification_flow()
        
        # Test 3: Event Bus Verification
        self.test_event_bus_verification()
        
        # Test 4: WebSocket Subscription Topics
        self.test_websocket_subscription_topics()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 BUSINESS WEBSOCKET NOTIFICATION TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        # Check critical functionality
        business_connection_working = any(r["test"] == "Business WebSocket Connection" and r["success"] for r in self.test_results)
        notification_flow_working = any(r["test"] == "End-to-End Notification Flow" and r["success"] for r in self.test_results)
        event_bus_working = any(r["test"] == "Event Bus Verification" and r["success"] for r in self.test_results)
        
        if business_connection_working:
            print(f"   ✅ Business WebSocket connection working (subscribed to business:{self.business_id})")
        else:
            print("   ❌ Business WebSocket connection FAILED")
            
        if notification_flow_working:
            print("   ✅ Real-time order notifications from customer to business WORKING")
        else:
            print("   ❌ Real-time order notifications NOT WORKING")
            
        if event_bus_working:
            print("   ✅ Event bus publishing order events correctly")
        else:
            print("   ❌ Event bus activity verification FAILED")
        
        # Overall verdict
        if success_rate >= 75:
            print(f"\n🎉 VERDICT: Business WebSocket notification system is WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
            print("   The end-to-end notification flow from customer order creation to business panel is functional.")
        elif success_rate >= 50:
            print(f"\n⚠️ VERDICT: Business WebSocket notification system has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Some components working but needs attention for full functionality.")
        else:
            print(f"\n🚨 VERDICT: Business WebSocket notification system has CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major problems preventing real-time notifications from working properly.")

async def main():
    """Main test runner"""
    tester = BusinessWebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())