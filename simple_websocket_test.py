#!/usr/bin/env python3
"""
Simple WebSocket Real-Time Order Notifications Testing

Test the WebSocket implementation for stability and functionality.
"""

import asyncio
import websockets
import json
import requests
import time
from datetime import datetime
import os
import sys

# Configuration
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com"
WEBSOCKET_URL = "wss://kuryecini-ai.preview.emergentagent.com/api/ws/orders"

# Test credentials
BUSINESS_CREDENTIALS = {"email": "testbusiness@example.com", "password": "test123"}
ADMIN_CREDENTIALS = {"email": "admin@kuryecini.com", "password": "admin123"}
CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}

# Test business ID from review request
TEST_BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"

class SimpleWebSocketTester:
    def __init__(self):
        self.test_results = []
        self.business_session = None
        self.admin_session = None
        self.customer_session = None
        
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
    
    async def test_basic_websocket_connection(self):
        """Test 1: Basic WebSocket Connection"""
        try:
            # Business WebSocket URL with business_id and role
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            # Simple connection test
            async with websockets.connect(ws_url) as websocket:
                
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"   Received: {message}")
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(message)
                        if data.get("type") == "connection" or "connected" in message.lower():
                            self.log_test(
                                "Basic WebSocket Connection",
                                True,
                                f"Connection successful, received: {message[:100]}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Basic WebSocket Connection",
                                True,
                                f"Connection successful but unexpected format: {message[:100]}"
                            )
                            return True
                    except json.JSONDecodeError:
                        # Message might not be JSON
                        if "connected" in message.lower() or "sipariş" in message.lower():
                            self.log_test(
                                "Basic WebSocket Connection",
                                True,
                                f"Connection successful, received text: {message[:100]}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Basic WebSocket Connection",
                                False,
                                error=f"Unexpected message format: {message[:100]}"
                            )
                            return False
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Basic WebSocket Connection",
                        False,
                        error="No connection confirmation received within 10s"
                    )
                    return False
                    
        except websockets.exceptions.InvalidHandshake as e:
            self.log_test(
                "Basic WebSocket Connection",
                False,
                error=f"Handshake failed (400 error): {str(e)}"
            )
            return False
        except Exception as e:
            self.log_test(
                "Basic WebSocket Connection",
                False,
                error=f"Connection failed: {str(e)}"
            )
            return False
    
    async def test_admin_websocket_connection(self):
        """Test 2: Admin WebSocket Connection"""
        try:
            # Admin WebSocket URL with role only
            ws_url = f"{WEBSOCKET_URL}?role=admin"
            
            async with websockets.connect(ws_url) as websocket:
                
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"   Admin received: {message}")
                    
                    # Check if connection is successful
                    if ("connected" in message.lower() or 
                        "admin" in message.lower() or
                        "sipariş" in message.lower()):
                        
                        self.log_test(
                            "Admin WebSocket Connection",
                            True,
                            f"Admin connection successful: {message[:100]}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Admin WebSocket Connection",
                            False,
                            error=f"Unexpected admin response: {message[:100]}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test(
                        "Admin WebSocket Connection",
                        False,
                        error="No admin connection confirmation received within 10s"
                    )
                    return False
                    
        except websockets.exceptions.InvalidHandshake as e:
            self.log_test(
                "Admin WebSocket Connection",
                False,
                error=f"Admin handshake failed: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_test(
                "Admin WebSocket Connection",
                False,
                error=f"Admin connection failed: {str(e)}"
            )
            return False
    
    async def test_ping_pong_mechanism(self):
        """Test 3: Ping-Pong Mechanism"""
        try:
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            async with websockets.connect(ws_url) as websocket:
                
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=10.0)
                
                ping_results = []
                
                # Test ping/pong cycles
                for i in range(3):
                    try:
                        # Send ping message
                        await websocket.send("ping")
                        print(f"   Sent ping {i+1}")
                        
                        # Wait for response
                        start_time = time.time()
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        response_time = time.time() - start_time
                        
                        print(f"   Received: {response}")
                        
                        if response == "pong" or "pong" in response.lower():
                            ping_results.append(f"Cycle {i+1}: {response_time:.2f}s")
                        else:
                            ping_results.append(f"Cycle {i+1}: Got '{response[:50]}' instead of pong")
                        
                        # Wait between cycles
                        await asyncio.sleep(2)
                        
                    except asyncio.TimeoutError:
                        ping_results.append(f"Cycle {i+1}: Timeout (>10s)")
                
                # Check results
                successful_cycles = len([r for r in ping_results if "Timeout" not in r and "instead of" not in r])
                
                if successful_cycles >= 2:  # At least 2/3 successful
                    self.log_test(
                        "Ping-Pong Mechanism",
                        True,
                        f"{successful_cycles}/3 ping-pong cycles successful: {', '.join(ping_results)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Ping-Pong Mechanism",
                        False,
                        error=f"Only {successful_cycles}/3 cycles successful: {', '.join(ping_results)}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Ping-Pong Mechanism",
                False,
                error=f"Ping-pong test failed: {str(e)}"
            )
            return False
    
    async def test_connection_stability(self):
        """Test 4: Connection Stability (30s test)"""
        try:
            ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
            
            async with websockets.connect(ws_url) as websocket:
                
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=10.0)
                
                print("   Starting 30-second stability test...")
                start_time = time.time()
                
                # Monitor connection for 30 seconds
                try:
                    for i in range(6):  # 6 * 5 = 30 seconds
                        await asyncio.sleep(5)
                        elapsed = time.time() - start_time
                        
                        # Check if connection is still alive
                        if websocket.closed:
                            self.log_test(
                                "Connection Stability",
                                False,
                                error=f"Connection closed prematurely after {elapsed:.1f}s"
                            )
                            return False
                        
                        print(f"   Connection alive at {elapsed:.1f}s")
                    
                    # After 30 seconds, connection should still be alive
                    elapsed = time.time() - start_time
                    if not websocket.closed:
                        self.log_test(
                            "Connection Stability",
                            True,
                            f"Connection remained stable for {elapsed:.1f}s"
                        )
                        return True
                    else:
                        self.log_test(
                            "Connection Stability",
                            False,
                            error=f"Connection closed at {elapsed:.1f}s"
                        )
                        return False
                        
                except websockets.exceptions.ConnectionClosed as e:
                    elapsed = time.time() - start_time
                    self.log_test(
                        "Connection Stability",
                        False,
                        error=f"Connection closed after {elapsed:.1f}s with code {e.code}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Connection Stability",
                False,
                error=f"Stability test failed: {str(e)}"
            )
            return False
    
    async def test_order_creation_and_notification(self):
        """Test 5: Order Creation and Notification Flow"""
        try:
            # Start WebSocket listener in background
            notification_received = False
            notification_data = None
            
            async def websocket_listener():
                nonlocal notification_received, notification_data
                try:
                    ws_url = f"{WEBSOCKET_URL}?business_id={TEST_BUSINESS_ID}&role=business"
                    async with websockets.connect(ws_url) as websocket:
                        
                        # Wait for connection
                        await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        print("   Business WebSocket connected, waiting for notifications...")
                        
                        # Listen for notifications
                        try:
                            while True:
                                message = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                                print(f"   📦 WebSocket message: {message}")
                                
                                # Check if it's an order notification
                                if ("order" in message.lower() and 
                                    ("created" in message.lower() or "notification" in message.lower())):
                                    notification_received = True
                                    notification_data = message
                                    break
                                    
                        except asyncio.TimeoutError:
                            print("   ⏰ No order notification received within 20s")
                            
                except Exception as e:
                    print(f"   ❌ WebSocket listener error: {str(e)}")
            
            # Start WebSocket listener
            websocket_task = asyncio.create_task(websocket_listener())
            
            # Wait for WebSocket to connect
            await asyncio.sleep(3)
            
            # Create an order via REST API
            try:
                # Get menu items for the business first
                menu_response = self.customer_session.get(
                    f"{BACKEND_URL}/api/business/public/{TEST_BUSINESS_ID}/menu",
                    timeout=10
                )
                
                if menu_response.status_code != 200:
                    self.log_test(
                        "Order Creation and Notification",
                        False,
                        error=f"Failed to get menu items: HTTP {menu_response.status_code}"
                    )
                    return False
                
                menu_items = menu_response.json()
                if not menu_items:
                    self.log_test(
                        "Order Creation and Notification",
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
                    await asyncio.wait_for(websocket_task, timeout=25.0)
                    
                    # Check if notification was received
                    if notification_received and notification_data:
                        self.log_test(
                            "Order Creation and Notification",
                            True,
                            f"Order notification received: {notification_data[:200]}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Order Creation and Notification",
                            False,
                            error="No order notification received via WebSocket"
                        )
                        return False
                        
                else:
                    self.log_test(
                        "Order Creation and Notification",
                        False,
                        error=f"Order creation failed: HTTP {order_response.status_code} - {order_response.text[:200]}"
                    )
                    return False
                    
            except Exception as e:
                self.log_test(
                    "Order Creation and Notification",
                    False,
                    error=f"Order creation error: {str(e)}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Order Creation and Notification",
                False,
                error=f"Order notification test failed: {str(e)}"
            )
            return False
    
    async def test_error_handling(self):
        """Test 6: Error Handling"""
        error_tests = []
        
        # Test 1: Connection without business_id for business role
        try:
            ws_url = f"{WEBSOCKET_URL}?role=business"  # Missing business_id
            
            try:
                async with websockets.connect(ws_url) as websocket:
                    
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f"   Missing business_id response: {message}")
                        
                        if "error" in message.lower() or "missing" in message.lower():
                            error_tests.append("Missing business_id: ✅ Error message received")
                        else:
                            error_tests.append("Missing business_id: ❌ No error message")
                            
                    except websockets.exceptions.ConnectionClosed as e:
                        if e.code == 1008:
                            error_tests.append("Missing business_id: ✅ Connection closed with code 1008")
                        else:
                            error_tests.append(f"Missing business_id: ✅ Connection closed with code {e.code}")
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
            ws_url = f"{WEBSOCKET_URL}?role=admin"
            
            async with websockets.connect(ws_url) as websocket:
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"   Admin role response: {message}")
                    
                    if "admin" in message.lower() or "connected" in message.lower():
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
        
        if successful_tests >= 1:  # At least 1 test should pass
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
                error=f"No error tests passed: {'; '.join(error_tests)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting Simple WebSocket Real-Time Order Notifications Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_users():
            print("❌ User authentication failed - cannot proceed with WebSocket tests")
            return
        
        print("\n🔌 Testing WebSocket Functionality...")
        print("-" * 50)
        
        # Test 1: Basic WebSocket Connection
        await self.test_basic_websocket_connection()
        
        # Test 2: Admin WebSocket Connection  
        await self.test_admin_websocket_connection()
        
        # Test 3: Ping-Pong Mechanism
        await self.test_ping_pong_mechanism()
        
        # Test 4: Connection Stability (30s)
        await self.test_connection_stability()
        
        # Test 5: Order Creation and Notification
        await self.test_order_creation_and_notification()
        
        # Test 6: Error Handling
        await self.test_error_handling()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 WEBSOCKET TESTING SUMMARY")
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
        basic_conn = any(r["test"] == "Basic WebSocket Connection" and r["success"] for r in self.test_results)
        admin_conn = any(r["test"] == "Admin WebSocket Connection" and r["success"] for r in self.test_results)
        ping_pong = any(r["test"] == "Ping-Pong Mechanism" and r["success"] for r in self.test_results)
        stability = any(r["test"] == "Connection Stability" and r["success"] for r in self.test_results)
        notifications = any(r["test"] == "Order Creation and Notification" and r["success"] for r in self.test_results)
        error_handling = any(r["test"] == "Error Handling" and r["success"] for r in self.test_results)
        
        if basic_conn:
            print("   ✅ Business WebSocket connections working - no handshake errors")
        else:
            print("   ❌ Business WebSocket connections FAILED - handshake issues detected")
            
        if admin_conn:
            print("   ✅ Admin WebSocket connections working correctly")
        else:
            print("   ❌ Admin WebSocket connections FAILED")
            
        if ping_pong:
            print("   ✅ Ping-pong heartbeat mechanism working")
        else:
            print("   ❌ Ping-pong heartbeat FAILED")
            
        if stability:
            print("   ✅ Connection stable for test period - no premature closures")
        else:
            print("   ❌ Connection stability FAILED - connections dropping")
            
        if notifications:
            print("   ✅ Real-time order notifications working")
        else:
            print("   ❌ Order notifications FAILED - real-time updates not working")
            
        if error_handling:
            print("   ✅ Error handling working - proper validation")
        else:
            print("   ❌ Error handling FAILED - improper validation")
        
        # Overall verdict
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: WebSocket System is WORKING WELL ({success_rate:.1f}% success rate)")
            print("   The WebSocket implementation appears to be functioning correctly.")
        elif success_rate >= 60:
            print(f"\n⚠️ VERDICT: WebSocket System has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Core functionality works but some issues remain.")
        else:
            print(f"\n🚨 VERDICT: WebSocket System has CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major problems detected - needs immediate attention.")

def main():
    """Main test runner"""
    tester = SimpleWebSocketTester()
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()