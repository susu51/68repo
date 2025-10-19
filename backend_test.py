#!/usr/bin/env python3
"""
Admin Panel Orders Real-Time WebSocket Integration Testing

CRITICAL: Test the newly implemented admin WebSocket system for real-time order notifications.

Test Scenarios:
1. Admin WebSocket Connection
2. Order Creation & Admin Notification  
3. WebSocket Role Validation
4. Multiple Admin Connections
5. Admin Endpoint Access
"""

import asyncio
import json
import requests
import websockets
import time
from datetime import datetime
import os
import sys

# Configuration
BACKEND_URL = "https://food-dash-87.preview.emergentagent.com"
WS_URL = "wss://food-dash-87.preview.emergentagent.com"

# Test credentials - try multiple admin credentials
ADMIN_CREDENTIALS_LIST = [
    {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    {"email": "admin@kuryecini.com", "password": "admin123"},
    {"email": "admin@demo.com", "password": "Admin!234"},
    {"email": "admin@kuryecini.com", "password": "6851"}
]

CUSTOMER_CREDENTIALS = {
    "email": "test@kuryecini.com", 
    "password": "test123"
}

class WebSocketTester:
    def __init__(self):
        self.admin_token = None
        self.customer_token = None
        self.test_results = []
        
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
    
    def authenticate_admin(self):
        """Authenticate admin user - try multiple credentials"""
        for i, credentials in enumerate(ADMIN_CREDENTIALS_LIST):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's cookie-based auth (success field) or JWT auth (access_token field)
                    if data.get("success"):
                        # Cookie-based auth
                        user_role = data.get("user", {}).get("role")
                        if user_role == "admin":
                            self.log_test(
                                "Admin Authentication",
                                True,
                                f"Admin login successful (cookie-based): {credentials['email']}, role: {user_role}"
                            )
                            return True
                    elif data.get("access_token"):
                        # JWT-based auth
                        self.admin_token = data.get("access_token")
                        user_role = data.get("user", {}).get("role")
                        if user_role == "admin":
                            self.log_test(
                                "Admin Authentication",
                                True,
                                f"Admin login successful (JWT): {credentials['email']}, role: {user_role}, token length: {len(self.admin_token)}"
                            )
                            return True
                    
                    print(f"   Tried {credentials['email']}: Wrong role ({data.get('user', {}).get('role')})")
                else:
                    print(f"   Tried {credentials['email']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   Tried {credentials['email']}: Error - {str(e)}")
        
        self.log_test("Admin Authentication", False, error="All admin credential attempts failed")
        return False
    
    def authenticate_customer(self):
        """Authenticate customer user"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                user_role = data.get("user", {}).get("role")
                
                if user_role == "customer":
                    self.log_test(
                        "Customer Authentication",
                        True,
                        f"Customer login successful, role: {user_role}"
                    )
                    return True
                else:
                    self.log_test("Customer Authentication", False, error=f"Expected customer role, got: {user_role}")
                    return False
            else:
                self.log_test("Customer Authentication", False, error=f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, error=f"Authentication error: {str(e)}")
            return False

    async def test_admin_websocket_connection(self):
        """Test 1: Admin WebSocket Connection"""
        try:
            # Test admin WebSocket connection with role=admin
            ws_url = f"{WS_URL}/api/ws/orders?role=admin"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for connection confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if (data.get("type") == "connected" and 
                    data.get("role") == "admin" and
                    data.get("client_id") == "admin"):
                    
                    self.log_test(
                        "Admin WebSocket Connection",
                        True,
                        f"Connection successful: role={data.get('role')}, client_id={data.get('client_id')}, message='{data.get('message')}'"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin WebSocket Connection",
                        False,
                        error=f"Unexpected connection response: {data}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Admin WebSocket Connection", False, error=f"WebSocket connection failed: {str(e)}")
            return False

    async def test_websocket_role_validation(self):
        """Test 2: Get Available Businesses by City (Aksaray)"""
        """Test 3: WebSocket Role Validation"""
        try:
            # Test 1: Business role WITHOUT business_id (should fail)
            try:
                ws_url = f"{WS_URL}/api/ws/orders?role=business"
                async with websockets.connect(ws_url) as websocket:
                    # Should close immediately
                    await asyncio.wait_for(websocket.recv(), timeout=5)
                    self.log_test(
                        "WebSocket Role Validation - Business without business_id",
                        False,
                        error="Connection should have been rejected but was accepted"
                    )
            except websockets.exceptions.ConnectionClosedError as e:
                if "business_id is required" in str(e):
                    self.log_test(
                        "WebSocket Role Validation - Business without business_id",
                        True,
                        "Connection properly rejected: business_id required for business role"
                    )
                else:
                    self.log_test(
                        "WebSocket Role Validation - Business without business_id",
                        False,
                        error=f"Unexpected close reason: {str(e)}"
                    )
            
            # Test 2: Admin role WITH business_id (should work, business_id ignored)
            ws_url = f"{WS_URL}/api/ws/orders?role=admin&business_id=test-business-id"
            async with websockets.connect(ws_url) as websocket:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("role") == "admin":
                    self.log_test(
                        "WebSocket Role Validation - Admin with business_id",
                        True,
                        "Admin connection works (business_id ignored for admin)"
                    )
                else:
                    self.log_test(
                        "WebSocket Role Validation - Admin with business_id",
                        False,
                        error=f"Expected admin role, got: {data.get('role')}"
                    )
            
            return True
            
        except Exception as e:
            self.log_test("WebSocket Role Validation", False, error=f"Role validation test failed: {str(e)}")
            return False

    def get_available_business(self):
        """Get available business for testing"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/businesses?city=Aksaray", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                if businesses and len(businesses) > 0:
                    business = businesses[0]
                    business_id = business.get("id")
                    business_name = business.get("name", "Unknown")
                    
                    self.log_test(
                        "Get Available Business",
                        True,
                        f"Found business: {business_name} (ID: {business_id})"
                    )
                    return business_id, business_name
                else:
                    self.log_test("Get Available Business", False, error="No businesses found in Aksaray")
                    return None, None
            else:
                self.log_test("Get Available Business", False, error=f"API error: {response.status_code}")
                return None, None
                
        except Exception as e:
            self.log_test("Get Available Business", False, error=f"Error getting business: {str(e)}")
            return None, None

    def get_business_menu(self, business_id):
        """Get business menu items"""
        # Try multiple menu endpoints
        endpoints_to_try = [
            f"{BACKEND_URL}/api/business/public/{business_id}/menu",
            f"{BACKEND_URL}/api/business/{business_id}/menu", 
            f"{BACKEND_URL}/api/business/public-menu/{business_id}/products",
            f"{BACKEND_URL}/api/businesses/{business_id}/products"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, timeout=10)
                
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

    def create_test_order(self, business_id, menu_item):
        """Create a test order"""
        try:
            order_data = {
                "delivery_address": "Test Address, Aksaray Merkez",
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
                "notes": "WebSocket test order"
            }
            
            headers = {"Authorization": f"Bearer {self.customer_token}"}
            response = requests.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                order_id = order.get("id")
                
                self.log_test(
                    "Create Test Order",
                    True,
                    f"Order created successfully: ID={order_id}, Total=₺{order.get('total_amount')}"
                )
                return order_id, order
            else:
                self.log_test("Create Test Order", False, error=f"Order creation failed: {response.status_code} - {response.text}")
                return None, None
                
        except Exception as e:
            self.log_test("Create Test Order", False, error=f"Error creating order: {str(e)}")
            return None, None

    async def test_order_creation_and_admin_notification(self):
        """Test 2: Order Creation & Admin Notification"""
        try:
            # Get available business and menu
            business_id, business_name = self.get_available_business()
            if not business_id:
                return False
                
            menu_item = self.get_business_menu(business_id)
            if not menu_item:
                return False
            
            # Start admin WebSocket connection
            ws_url = f"{WS_URL}/api/ws/orders?role=admin"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for connection confirmation
                await asyncio.wait_for(websocket.recv(), timeout=10)
                
                # Create order (this should trigger event_bus publication)
                order_id, order = self.create_test_order(business_id, menu_item)
                if not order_id:
                    return False
                
                # Wait for WebSocket notification
                try:
                    notification = await asyncio.wait_for(websocket.recv(), timeout=15)
                    data = json.loads(notification)
                    
                    if (data.get("type") == "order_notification" and
                        data.get("data", {}).get("event_type") == "order.created"):
                        
                        event_data = data.get("data", {})
                        self.log_test(
                            "Order Creation & Admin Notification",
                            True,
                            f"Admin received order notification: order_id={event_data.get('order_id')}, business_id={event_data.get('business_id')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Order Creation & Admin Notification",
                            False,
                            error=f"Unexpected notification format: {data}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Order Creation & Admin Notification",
                        False,
                        error="No WebSocket notification received within 15 seconds"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Order Creation & Admin Notification", False, error=f"Test failed: {str(e)}")
            return False

    async def test_multiple_admin_connections(self):
        """Test 4: Multiple Admin Connections"""
        try:
            ws_url = f"{WS_URL}/api/ws/orders?role=admin"
            
            # Create 2 concurrent admin connections
            async with websockets.connect(ws_url) as ws1, websockets.connect(ws_url) as ws2:
                # Wait for both connection confirmations
                await asyncio.wait_for(ws1.recv(), timeout=10)
                await asyncio.wait_for(ws2.recv(), timeout=10)
                
                # Get business and menu for order creation
                business_id, business_name = self.get_available_business()
                if not business_id:
                    return False
                    
                menu_item = self.get_business_menu(business_id)
                if not menu_item:
                    return False
                
                # Create an order
                order_id, order = self.create_test_order(business_id, menu_item)
                if not order_id:
                    return False
                
                # Check if both connections receive the notification
                notifications_received = 0
                
                try:
                    # Wait for notification on first connection
                    notification1 = await asyncio.wait_for(ws1.recv(), timeout=15)
                    data1 = json.loads(notification1)
                    if data1.get("type") == "order_notification":
                        notifications_received += 1
                except asyncio.TimeoutError:
                    pass
                
                try:
                    # Wait for notification on second connection
                    notification2 = await asyncio.wait_for(ws2.recv(), timeout=15)
                    data2 = json.loads(notification2)
                    if data2.get("type") == "order_notification":
                        notifications_received += 1
                except asyncio.TimeoutError:
                    pass
                
                if notifications_received == 2:
                    self.log_test(
                        "Multiple Admin Connections",
                        True,
                        f"Both admin connections received order notification (2/2)"
                    )
                    return True
                else:
                    self.log_test(
                        "Multiple Admin Connections",
                        False,
                        error=f"Only {notifications_received}/2 connections received notification"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Multiple Admin Connections", False, error=f"Test failed: {str(e)}")
            return False

    def test_admin_orders_endpoint(self):
        """Test 5: Admin Endpoint Access"""
        try:
            # Use cookie-based authentication (no headers needed if we're using the same session)
            # Create a new session and login as admin for this test
            admin_session = requests.Session()
            
            # Login as admin to get cookies
            login_response = admin_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"email": "admin@kuryecini.com", "password": "admin123"},
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.log_test("Admin Orders Endpoint Access", False, error="Admin login failed for orders test")
                return False
            
            # Now try to access admin orders with cookies
            response = admin_session.get(f"{BACKEND_URL}/api/admin/orders", timeout=10)
            
            if response.status_code == 200:
                orders = response.json()
                
                # Check if orders have required fields
                if orders and len(orders) > 0:
                    order = orders[0]
                    required_fields = ["id", "business_id", "business_name", "customer_name", "status", "total_amount", "items"]
                    missing_fields = [field for field in required_fields if field not in order]
                    
                    if not missing_fields:
                        self.log_test(
                            "Admin Orders Endpoint Access",
                            True,
                            f"Retrieved {len(orders)} orders with all required fields: {', '.join(required_fields)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin Orders Endpoint Access",
                            False,
                            error=f"Missing required fields: {missing_fields}"
                        )
                        return False
                else:
                    self.log_test(
                        "Admin Orders Endpoint Access",
                        True,
                        "Admin orders endpoint accessible (no orders found, which is valid)"
                    )
                    return True
            else:
                self.log_test("Admin Orders Endpoint Access", False, error=f"API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Orders Endpoint Access", False, error=f"Error accessing admin orders: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting Admin Panel Orders Real-Time WebSocket Integration Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - cannot proceed with tests")
            return
            
        if not self.authenticate_customer():
            print("❌ Customer authentication failed - cannot proceed with order creation tests")
            return
        
        print("\n🔗 Testing WebSocket Functionality...")
        print("-" * 50)
        
        # Test 1: Admin WebSocket Connection
        await self.test_admin_websocket_connection()
        
        # Test 2: Order Creation & Admin Notification
        await self.test_order_creation_and_admin_notification()
        
        # Test 3: WebSocket Role Validation
        await self.test_websocket_role_validation()
        
        # Test 4: Multiple Admin Connections
        await self.test_multiple_admin_connections()
        
        # Test 5: Admin Endpoint Access
        self.test_admin_orders_endpoint()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 ADMIN WEBSOCKET TESTING SUMMARY")
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
        admin_connection_working = any(r["test"] == "Admin WebSocket Connection" and r["success"] for r in self.test_results)
        order_notification_working = any(r["test"] == "Order Creation & Admin Notification" and r["success"] for r in self.test_results)
        role_validation_working = any(r["test"].startswith("WebSocket Role Validation") and r["success"] for r in self.test_results)
        
        if admin_connection_working:
            print("   ✅ Admin WebSocket connection with role=admin parameter working")
        else:
            print("   ❌ Admin WebSocket connection FAILED")
            
        if order_notification_working:
            print("   ✅ Admin receives ALL order notifications from event_bus")
        else:
            print("   ❌ Admin order notifications NOT WORKING")
            
        if role_validation_working:
            print("   ✅ WebSocket role validation working correctly")
        else:
            print("   ❌ WebSocket role validation FAILED")
        
        # Overall verdict
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: Admin WebSocket system is WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
        elif success_rate >= 60:
            print(f"\n⚠️ VERDICT: Admin WebSocket system has MINOR ISSUES ({success_rate:.1f}% success rate)")
        else:
            print(f"\n🚨 VERDICT: Admin WebSocket system has CRITICAL ISSUES ({success_rate:.1f}% success rate)")

async def main():
    """Main test runner"""
    tester = WebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
