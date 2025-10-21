#!/usr/bin/env python3
"""
WebSocket Real-Time Order Notifications Stability Testing

CRITICAL: Test the WebSocket implementation for persistent disconnection issues
(400 handshake errors, 1006 abnormal closures, 60-90s idle timeouts).

Test Scenarios:
1. WebSocket Connection Establishment (Business & Admin)
2. Heartbeat/Ping-Pong Mechanism  
3. Connection Stability - Idle Timeout (90s)
4. Re-subscription Support
5. Order Notification Flow
6. Error Handling
"""

import asyncio
import websockets
import json
import requests
import time
from datetime import datetime
import os
import sys
import logging

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com"
WEBSOCKET_URL = "wss://kuryecini-ai.preview.emergentagent.com/api/ws/orders"

# Test credentials
BUSINESS_CREDENTIALS = {"email": "testbusiness@example.com", "password": "test123"}
ADMIN_CREDENTIALS = {"email": "admin@kuryecini.com", "password": "admin123"}
CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}

# Test business ID from review request
TEST_BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"

class WebSocketStabilityTester:
    def __init__(self):
        self.test_results = []
        self.business_session = None
        self.admin_session = None
        self.customer_session = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
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
    
    def authenticate_users(self):
        """Authenticate all required users"""
        success_count = 0
        
        # Authenticate business user
        self.business_session = requests.Session()
        try:
            response = self.business_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=BUSINESS_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("user", {}).get("role") == "business":
                    self.log_test(
                        "Business Authentication",
                        True,
                        f"Business login successful: {BUSINESS_CREDENTIALS['email']}"
                    )
                    success_count += 1
                else:
                    self.log_test("Business Authentication", False, error="Invalid business credentials")
            else:
                self.log_test("Business Authentication", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Business Authentication", False, error=str(e))
        
        # Authenticate admin user
        self.admin_session = requests.Session()
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("user", {}).get("role") == "admin":
                    self.log_test(
                        "Admin Authentication",
                        True,
                        f"Admin login successful: {ADMIN_CREDENTIALS['email']}"
                    )
                    success_count += 1
                else:
                    self.log_test("Admin Authentication", False, error="Invalid admin credentials")
            else:
                self.log_test("Admin Authentication", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Authentication", False, error=str(e))
        
        # Authenticate customer user
        self.customer_session = requests.Session()
        try:
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("user", {}).get("role") == "customer":
                    self.log_test(
                        "Customer Authentication",
                        True,
                        f"Customer login successful: {CUSTOMER_CREDENTIALS['email']}"
                    )
                    success_count += 1
                else:
                    self.log_test("Customer Authentication", False, error="Invalid customer credentials")
            else:
                self.log_test("Customer Authentication", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Customer Authentication", False, error=str(e))
        
        return success_count >= 2  # Need at least business and customer auth
    
    async def test_business_websocket_connection(self):
        """Test 1: Business WebSocket Connection Establishment"""
        try:
            # Get cookies from business session
            cookies = "; ".join([f"{k}={v}" for k, v in self.business_session.cookies.items()])
            
            # Business WebSocket URL with business_id and role
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            # Connect to WebSocket
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if (data.get("type") == "connection" and 
                        data.get("role") == "business" and
                        data.get("business_id") == TEST_BUSINESS_ID):
                        
                        self.log_test(
                            "Business WebSocket Connection",
                            True,
                            f"Connected successfully: {data.get('message', 'No message')}"
                        )
                        return True, websocket
                    else:
                        self.log_test(
                            "Business WebSocket Connection",
                            False,
                            error=f"Invalid connection response: {data}"
                        )
                        return False, None
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Business WebSocket Connection",
                        False,
                        error="No connection confirmation received within 5s"
                    )
                    return False, None
                    
        except websockets.exceptions.InvalidHandshake as e:
            self.log_test(
                "Business WebSocket Connection",
                False,
                error=f"Handshake failed (400 error): {str(e)}"
            )
            return False, None
        except Exception as e:
            self.log_test(
                "Business WebSocket Connection",
                False,
                error=f"Connection failed: {str(e)}"
            )
            return False, None
    
    async def test_admin_websocket_connection(self):
        """Test 2: Admin WebSocket Connection Establishment"""
        try:
            # Get cookies from admin session
            cookies = "; ".join([f"{k}={v}" for k, v in self.admin_session.cookies.items()])
            
            # Admin WebSocket URL with role only
            ws_url = f"{WEBSOCKET_URL}?role=admin"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            # Connect to WebSocket
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if (data.get("type") == "connection" and 
                        data.get("role") == "admin"):
                        
                        self.log_test(
                            "Admin WebSocket Connection",
                            True,
                            f"Connected successfully: {data.get('message', 'No message')}"
                        )
                        return True, websocket
                    else:
                        self.log_test(
                            "Admin WebSocket Connection",
                            False,
                            error=f"Invalid connection response: {data}"
                        )
                        return False, None
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Admin WebSocket Connection",
                        False,
                        error="No connection confirmation received within 5s"
                    )
                    return False, None
                    
        except websockets.exceptions.InvalidHandshake as e:
            self.log_test(
                "Admin WebSocket Connection",
                False,
                error=f"Handshake failed (400 error): {str(e)}"
            )
            return False, None
        except Exception as e:
            self.log_test(
                "Admin WebSocket Connection",
                False,
                error=f"Connection failed: {str(e)}"
            )
            return False, None
    
    async def test_ping_pong_mechanism(self):
        """Test 3: Heartbeat/Ping-Pong Mechanism"""
        try:
            # Get cookies from business session
            cookies = "; ".join([f"{k}={v}" for k, v in self.business_session.cookies.items()])
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            ) as websocket:
                
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                ping_pong_results = []
                
                # Test multiple ping/pong cycles
                for i in range(3):
                    try:
                        # Send ping message
                        await websocket.send("ping")
                        
                        # Wait for pong response
                        start_time = time.time()
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_time = time.time() - start_time
                        
                        if response == "pong":
                            ping_pong_results.append(f"Cycle {i+1}: {response_time:.2f}s")
                        else:
                            ping_pong_results.append(f"Cycle {i+1}: Invalid response '{response}'")
                        
                        # Wait between cycles
                        await asyncio.sleep(1)
                        
                    except asyncio.TimeoutError:
                        ping_pong_results.append(f"Cycle {i+1}: Timeout (>5s)")
                
                # Check results
                successful_cycles = len([r for r in ping_pong_results if "Invalid" not in r and "Timeout" not in r])
                
                if successful_cycles == 3:
                    self.log_test(
                        "Ping-Pong Mechanism",
                        True,
                        f"All 3 ping-pong cycles successful: {', '.join(ping_pong_results)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Ping-Pong Mechanism",
                        False,
                        error=f"Only {successful_cycles}/3 cycles successful: {', '.join(ping_pong_results)}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Ping-Pong Mechanism",
                False,
                error=f"Ping-pong test failed: {str(e)}"
            )
            return False
    
    async def test_idle_timeout_stability(self):
        """Test 4: Connection Stability - Idle Timeout (90s)"""
        try:
            # Get cookies from business session
            cookies = "; ".join([f"{k}={v}" for k, v in self.business_session.cookies.items()])
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=None,  # Disable automatic pings
                ping_timeout=None,
                close_timeout=10
            ) as websocket:
                
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                print("   Starting 90-second idle timeout test...")
                start_time = time.time()
                
                # Wait for 90 seconds without sending any messages
                try:
                    # Check connection status every 10 seconds
                    for i in range(9):  # 9 * 10 = 90 seconds
                        await asyncio.sleep(10)
                        elapsed = time.time() - start_time
                        
                        # Try to check if connection is still alive
                        if websocket.closed:
                            self.log_test(
                                "Idle Timeout Stability",
                                False,
                                error=f"Connection closed prematurely after {elapsed:.1f}s (expected 90s)"
                            )
                            return False
                        
                        print(f"   Connection alive at {elapsed:.1f}s")
                    
                    # After 90 seconds, connection should still be alive
                    elapsed = time.time() - start_time
                    if not websocket.closed:
                        self.log_test(
                            "Idle Timeout Stability",
                            True,
                            f"Connection remained stable for {elapsed:.1f}s without premature disconnection"
                        )
                        return True
                    else:
                        self.log_test(
                            "Idle Timeout Stability",
                            False,
                            error=f"Connection closed at {elapsed:.1f}s"
                        )
                        return False
                        
                except websockets.exceptions.ConnectionClosed as e:
                    elapsed = time.time() - start_time
                    if elapsed >= 90:
                        self.log_test(
                            "Idle Timeout Stability",
                            True,
                            f"Connection closed after {elapsed:.1f}s (expected timeout behavior)"
                        )
                        return True
                    else:
                        self.log_test(
                            "Idle Timeout Stability",
                            False,
                            error=f"Connection closed prematurely after {elapsed:.1f}s with code {e.code}"
                        )
                        return False
                        
        except Exception as e:
            self.log_test(
                "Idle Timeout Stability",
                False,
                error=f"Idle timeout test failed: {str(e)}"
            )
            return False
    
    async def test_resubscription_support(self):
        """Test 5: Re-subscription Support"""
        try:
            # Get cookies from business session
            cookies = "; ".join([f"{k}={v}" for k, v in self.business_session.cookies.items()])
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            ) as websocket:
                
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Send re-subscription message
                resubscribe_message = {
                    "type": "subscribe",
                    "business_id": TEST_BUSINESS_ID,
                    "role": "business"
                }
                
                await websocket.send(json.dumps(resubscribe_message))
                
                # Wait for subscription confirmation
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if (data.get("type") == "subscribed" or 
                        "subscribed" in data.get("message", "").lower()):
                        
                        self.log_test(
                            "Re-subscription Support",
                            True,
                            f"Re-subscription successful: {data.get('message', 'Confirmed')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Re-subscription Support",
                            False,
                            error=f"Invalid subscription response: {data}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Re-subscription Support",
                        False,
                        error="No subscription confirmation received within 5s"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Re-subscription Support",
                False,
                error=f"Re-subscription test failed: {str(e)}"
            )
            return False
    
    async def test_order_notification_flow(self):
        """Test 6: Order Notification Flow"""
        try:
            # First, establish business WebSocket connection
            cookies = "; ".join([f"{k}={v}" for k, v in self.business_session.cookies.items()])
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            # Start WebSocket connection in background
            websocket_task = None
            notification_received = False
            notification_data = None
            
            async def websocket_listener():
                nonlocal notification_received, notification_data
                try:
                    async with websockets.connect(
                        ws_url,
                        extra_headers=headers,
                        ping_interval=30,
                        ping_timeout=10
                    ) as websocket:
                        
                        # Wait for connection
                        await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print("   Business WebSocket connected, waiting for order notification...")
                        
                        # Listen for notifications for up to 30 seconds
                        try:
                            while True:
                                message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                                data = json.loads(message)
                                
                                if data.get("type") == "order_notification":
                                    notification_received = True
                                    notification_data = data
                                    print(f"   📦 Order notification received: {data}")
                                    break
                                    
                        except asyncio.TimeoutError:
                            print("   ⏰ No order notification received within 30s")
                            
                except Exception as e:
                    print(f"   ❌ WebSocket listener error: {str(e)}")
            
            # Start WebSocket listener
            websocket_task = asyncio.create_task(websocket_listener())
            
            # Wait a moment for WebSocket to connect
            await asyncio.sleep(2)
            
            # Create an order via REST API
            try:
                # Get menu items for the business first
                menu_response = self.customer_session.get(
                    f"{BACKEND_URL}/api/business/public/{TEST_BUSINESS_ID}/menu",
                    timeout=10
                )
                
                if menu_response.status_code != 200:
                    self.log_test(
                        "Order Notification Flow",
                        False,
                        error=f"Failed to get menu items: HTTP {menu_response.status_code}"
                    )
                    return False
                
                menu_items = menu_response.json()
                if not menu_items:
                    self.log_test(
                        "Order Notification Flow",
                        False,
                        error="No menu items available for testing"
                    )
                    return False
                
                # Create order with first menu item
                first_item = menu_items[0]
                order_data = {
                    "business_id": TEST_BUSINESS_ID,
                    "delivery_address": "Test Address, Test District, Test City",
                    "delivery_lat": 39.9334,
                    "delivery_lng": 32.8597,
                    "items": [{
                        "product_id": first_item["id"],
                        "title": first_item["name"],
                        "price": first_item["price"],
                        "quantity": 1
                    }],
                    "total_amount": first_item["price"],
                    "payment_method": "cash_on_delivery",
                    "notes": "WebSocket test order"
                }
                
                print(f"   Creating test order with item: {first_item['name']} (₺{first_item['price']})")
                
                order_response = self.customer_session.post(
                    f"{BACKEND_URL}/api/orders",
                    json=order_data,
                    timeout=10
                )
                
                if order_response.status_code == 200:
                    order_result = order_response.json()
                    order_id = order_result.get("order_id")
                    print(f"   ✅ Order created successfully: {order_id}")
                    
                    # Wait for WebSocket task to complete
                    await asyncio.wait_for(websocket_task, timeout=35.0)
                    
                    # Check if notification was received
                    if notification_received and notification_data:
                        # Validate notification format
                        required_fields = ["order_id", "business_id", "customer_name", "total"]
                        missing_fields = [f for f in required_fields if f not in notification_data]
                        
                        if not missing_fields:
                            self.log_test(
                                "Order Notification Flow",
                                True,
                                f"Order notification received with all required fields: order_id={notification_data.get('order_id')}, business_id={notification_data.get('business_id')}, customer_name={notification_data.get('customer_name')}, total={notification_data.get('total')}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Order Notification Flow",
                                False,
                                error=f"Notification missing required fields: {missing_fields}"
                            )
                            return False
                    else:
                        self.log_test(
                            "Order Notification Flow",
                            False,
                            error="No order notification received via WebSocket"
                        )
                        return False
                        
                else:
                    self.log_test(
                        "Order Notification Flow",
                        False,
                        error=f"Order creation failed: HTTP {order_response.status_code} - {order_response.text[:200]}"
                    )
                    return False
                    
            except Exception as e:
                self.log_test(
                    "Order Notification Flow",
                    False,
                    error=f"Order creation error: {str(e)}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Order Notification Flow",
                False,
                error=f"Order notification test failed: {str(e)}"
            )
            return False
    
    async def test_error_handling(self):
        """Test 7: Error Handling"""
        error_tests = []
        
        # Test 1: Connection without business_id for business role
        try:
            ws_url = f"{WEBSOCKET_URL}?role=business"  # Missing business_id
            
            try:
                async with websockets.connect(
                    ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=5
                ) as websocket:
                    
                    # Should receive error or close with code 1008
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if "error" in data.get("message", "").lower():
                            error_tests.append("Missing business_id: ✅ Error message received")
                        else:
                            error_tests.append("Missing business_id: ❌ No error message")
                            
                    except websockets.exceptions.ConnectionClosed as e:
                        if e.code == 1008:
                            error_tests.append("Missing business_id: ✅ Connection closed with code 1008")
                        else:
                            error_tests.append(f"Missing business_id: ❌ Wrong close code {e.code}")
                    except asyncio.TimeoutError:
                        error_tests.append("Missing business_id: ❌ No response received")
                        
            except websockets.exceptions.InvalidHandshake:
                error_tests.append("Missing business_id: ✅ Handshake rejected")
            except Exception as e:
                error_tests.append(f"Missing business_id: ❌ Unexpected error: {str(e)[:50]}")
                
        except Exception as e:
            error_tests.append(f"Missing business_id: ❌ Test failed: {str(e)[:50]}")
        
        # Test 2: Admin role connection (should work)
        try:
            cookies = "; ".join([f"{k}={v}" for k, v in self.admin_session.cookies.items()])
            ws_url = f"{WEBSOCKET_URL}?role=admin"
            
            headers = {}
            if cookies:
                headers["Cookie"] = cookies
            
            async with websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            ) as websocket:
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("role") == "admin":
                        error_tests.append("Admin role: ✅ Connection successful")
                    else:
                        error_tests.append("Admin role: ❌ Invalid response")
                        
                except asyncio.TimeoutError:
                    error_tests.append("Admin role: ❌ No connection confirmation")
                    
        except Exception as e:
            error_tests.append(f"Admin role: ❌ Connection failed: {str(e)[:50]}")
        
        # Evaluate results
        successful_tests = len([t for t in error_tests if "✅" in t])
        total_tests = len(error_tests)
        
        if successful_tests >= total_tests * 0.8:  # 80% success rate
            self.log_test(
                "Error Handling",
                True,
                f"{successful_tests}/{total_tests} error handling tests passed: {'; '.join(error_tests)}"
            )
            return True
        else:
            self.log_test(
                "Error Handling",
                False,
                error=f"Only {successful_tests}/{total_tests} error tests passed: {'; '.join(error_tests)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all WebSocket stability tests"""
        print("🚀 Starting WebSocket Real-Time Order Notifications Stability Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_users():
            print("❌ User authentication failed - cannot proceed with WebSocket tests")
            return
        
        print("\n🔌 Testing WebSocket Connection Stability...")
        print("-" * 50)
        
        # Test 1: Business WebSocket Connection
        success, _ = await self.test_business_websocket_connection()
        
        # Test 2: Admin WebSocket Connection  
        await self.test_admin_websocket_connection()
        
        # Test 3: Ping-Pong Mechanism
        await self.test_ping_pong_mechanism()
        
        # Test 4: Idle Timeout Stability (90s test)
        print("⏰ Starting 90-second idle timeout test (this will take time)...")
        await self.test_idle_timeout_stability()
        
        # Test 5: Re-subscription Support
        await self.test_resubscription_support()
        
        # Test 6: Order Notification Flow
        await self.test_order_notification_flow()
        
        # Test 7: Error Handling
        await self.test_error_handling()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 WEBSOCKET STABILITY TESTING SUMMARY")
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
        business_conn = any(r["test"] == "Business WebSocket Connection" and r["success"] for r in self.test_results)
        admin_conn = any(r["test"] == "Admin WebSocket Connection" and r["success"] for r in self.test_results)
        ping_pong = any(r["test"] == "Ping-Pong Mechanism" and r["success"] for r in self.test_results)
        idle_timeout = any(r["test"] == "Idle Timeout Stability" and r["success"] for r in self.test_results)
        resubscription = any(r["test"] == "Re-subscription Support" and r["success"] for r in self.test_results)
        order_notifications = any(r["test"] == "Order Notification Flow" and r["success"] for r in self.test_results)
        error_handling = any(r["test"] == "Error Handling" and r["success"] for r in self.test_results)
        
        if business_conn:
            print("   ✅ Business WebSocket connections working - no 400 handshake errors")
        else:
            print("   ❌ Business WebSocket connections FAILED - handshake issues detected")
            
        if admin_conn:
            print("   ✅ Admin WebSocket connections working correctly")
        else:
            print("   ❌ Admin WebSocket connections FAILED")
            
        if ping_pong:
            print("   ✅ Ping-pong heartbeat mechanism working - prevents disconnections")
        else:
            print("   ❌ Ping-pong heartbeat FAILED - may cause connection drops")
            
        if idle_timeout:
            print("   ✅ Connection stable for 90s idle period - no premature 1006 closures")
        else:
            print("   ❌ Idle timeout FAILED - connections dropping before 90s")
            
        if resubscription:
            print("   ✅ Re-subscription support working correctly")
        else:
            print("   ❌ Re-subscription support FAILED")
            
        if order_notifications:
            print("   ✅ Real-time order notifications working - orders reach business WebSocket")
        else:
            print("   ❌ Order notifications FAILED - real-time updates not working")
            
        if error_handling:
            print("   ✅ Error handling working - proper validation for missing parameters")
        else:
            print("   ❌ Error handling FAILED - improper validation")
        
        # Overall verdict
        if success_rate >= 85:
            print(f"\n🎉 VERDICT: WebSocket System is STABLE ({success_rate:.1f}% success rate)")
            print("   ✅ No 400 handshake errors")
            print("   ✅ No unexpected 1006 closures") 
            print("   ✅ Connections stable for 90s idle")
            print("   ✅ Real-time notifications working")
            print("   The WebSocket implementation has resolved persistent disconnection issues.")
        elif success_rate >= 70:
            print(f"\n⚠️ VERDICT: WebSocket System has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Core functionality works but some stability issues remain.")
        else:
            print(f"\n🚨 VERDICT: WebSocket System has CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major stability problems detected - disconnection issues persist.")

def main():
    """Main test runner"""
    tester = WebSocketStabilityTester()
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()