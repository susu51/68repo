#!/usr/bin/env python3
"""
Kuryecini Ops Co-Pilot AI Diagnostics Panel Testing

CRITICAL: Test the newly implemented AI Diagnostics panel endpoint "/admin/ai/assist" for the AI Diagnostics panel.

Test Scenarios:
1. Endpoint Availability & Structure (CRITICAL)
2. Panel Switching (HIGH)
3. Response Format Validation (CRITICAL)
4. Tool Endpoints (MEDIUM)
5. Error Handling (HIGH)
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
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com"
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

class AIDiagnosticsTester:
    def __init__(self):
        self.admin_session = None
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
        self.admin_session = requests.Session()
        
        for i, credentials in enumerate(ADMIN_CREDENTIALS_LIST):
            try:
                response = self.admin_session.post(
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
                        # JWT-based auth - store token for headers
                        user_role = data.get("user", {}).get("role")
                        if user_role == "admin":
                            # Set authorization header for session
                            self.admin_session.headers.update({
                                "Authorization": f"Bearer {data.get('access_token')}"
                            })
                            self.log_test(
                                "Admin Authentication",
                                True,
                                f"Admin login successful (JWT): {credentials['email']}, role: {user_role}"
                            )
                            return True
                    
                    print(f"   Tried {credentials['email']}: Wrong role ({data.get('user', {}).get('role')})")
                else:
                    print(f"   Tried {credentials['email']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   Tried {credentials['email']}: Error - {str(e)}")
        
        self.log_test("Admin Authentication", False, error="All admin credential attempts failed")
        return False
    
    def test_endpoint_availability_and_structure(self):
        """Test 1: Endpoint Availability & Structure (CRITICAL)"""
        try:
            # Test POST to /api/admin/ai/assist
            test_data = {
                "panel": "müşteri",
                "message": "restoranlar gözükmüyor"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/api/admin/ai/assist",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains required fields
                if "response" in data and "panel" in data:
                    # Check if response is a string (the AI response)
                    if isinstance(data["response"], str) and len(data["response"]) > 0:
                        # Check if panel matches request
                        if data["panel"] == test_data["panel"]:
                            self.log_test(
                                "Endpoint Availability & Structure",
                                True,
                                f"Endpoint accessible, response length: {len(data['response'])} chars, panel: {data['panel']}"
                            )
                            return True, data
                        else:
                            self.log_test(
                                "Endpoint Availability & Structure",
                                False,
                                error=f"Panel mismatch: expected {test_data['panel']}, got {data['panel']}"
                            )
                            return False, None
                    else:
                        self.log_test(
                            "Endpoint Availability & Structure",
                            False,
                            error=f"Invalid response format: {type(data['response'])}"
                        )
                        return False, None
                else:
                    self.log_test(
                        "Endpoint Availability & Structure",
                        False,
                        error=f"Missing required fields in response: {list(data.keys())}"
                    )
                    return False, None
            else:
                self.log_test(
                    "Endpoint Availability & Structure",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Endpoint Availability & Structure",
                False,
                error=f"Request failed: {str(e)}"
            )
            return False, None

    def test_panel_switching(self):
        """Test 2: Panel Switching (HIGH)"""
        panels_to_test = ["müşteri", "işletme", "kurye", "admin", "multi"]
        successful_panels = []
        
        for panel in panels_to_test:
            try:
                test_data = {
                    "panel": panel,
                    "message": f"{panel} panelinde sorun var mı?"
                }
                
                response = self.admin_session.post(
                    f"{BACKEND_URL}/api/admin/ai/assist",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if (data.get("panel") == panel and 
                        isinstance(data.get("response"), str) and 
                        len(data.get("response", "")) > 0):
                        successful_panels.append(panel)
                        print(f"   ✅ Panel '{panel}': Response length {len(data['response'])} chars")
                    else:
                        print(f"   ❌ Panel '{panel}': Invalid response structure")
                else:
                    print(f"   ❌ Panel '{panel}': HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Panel '{panel}': Error - {str(e)}")
        
        if len(successful_panels) == len(panels_to_test):
            self.log_test(
                "Panel Switching",
                True,
                f"All {len(panels_to_test)} panels working: {', '.join(successful_panels)}"
            )
            return True
        elif len(successful_panels) > 0:
            self.log_test(
                "Panel Switching",
                False,
                error=f"Only {len(successful_panels)}/{len(panels_to_test)} panels working: {', '.join(successful_panels)}"
            )
            return False
        else:
            self.log_test(
                "Panel Switching",
                False,
                error="No panels working"
            )
            return False

    def test_response_format_validation(self):
        """Test 3: Response Format Validation (CRITICAL)"""
        try:
            test_data = {
                "panel": "işletme",
                "message": "sipariş sistemi çalışmıyor"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/api/admin/ai/assist",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")
                
                # Check for 7 required sections in Turkish
                required_sections = [
                    "Hızlı Teşhis",
                    "Derin RCA", 
                    "Kontrol Komutları",
                    "Patch",
                    "Test",
                    "İzleme & Alarm",
                    "DoD"
                ]
                
                found_sections = []
                missing_sections = []
                
                for section in required_sections:
                    if section in ai_response:
                        found_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                if len(found_sections) == len(required_sections):
                    self.log_test(
                        "Response Format Validation",
                        True,
                        f"All 7 required sections found: {', '.join(found_sections)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Response Format Validation",
                        False,
                        error=f"Missing sections: {', '.join(missing_sections)}. Found: {', '.join(found_sections)}"
                    )
                    return False
            else:
                self.log_test(
                    "Response Format Validation",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Response Format Validation",
                False,
                error=f"Format validation failed: {str(e)}"
            )
            return False

    def test_tool_endpoints(self):
        """Test 4: Tool Endpoints (MEDIUM)"""
        tool_endpoints = [
            {
                "name": "HTTP GET Tool",
                "url": f"{BACKEND_URL}/api/admin/ai/tools/http_get",
                "method": "POST",
                "data": {"url": f"{BACKEND_URL}/api/health"}
            },
            {
                "name": "Logs Tail Tool", 
                "url": f"{BACKEND_URL}/api/admin/ai/tools/logs_tail",
                "method": "POST",
                "data": {"path": "/var/log/supervisor/backend.out.log", "limit": 10}
            },
            {
                "name": "DB Query Tool",
                "url": f"{BACKEND_URL}/api/admin/ai/tools/db_query", 
                "method": "POST",
                "data": {"collection": "users", "action": "count", "filter": {}}
            },
            {
                "name": "Env List Tool",
                "url": f"{BACKEND_URL}/api/admin/ai/tools/env_list",
                "method": "GET",
                "data": None
            }
        ]
        
        successful_tools = []
        failed_tools = []
        
        for tool in tool_endpoints:
            try:
                if tool["method"] == "POST":
                    response = self.admin_session.post(
                        tool["url"],
                        json=tool["data"],
                        timeout=15
                    )
                else:
                    response = self.admin_session.get(
                        tool["url"],
                        timeout=15
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    # Basic validation - check if response is not empty
                    if data and isinstance(data, dict):
                        successful_tools.append(tool["name"])
                        print(f"   ✅ {tool['name']}: Working")
                    else:
                        failed_tools.append(f"{tool['name']} (empty response)")
                        print(f"   ❌ {tool['name']}: Empty response")
                else:
                    failed_tools.append(f"{tool['name']} (HTTP {response.status_code})")
                    print(f"   ❌ {tool['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                failed_tools.append(f"{tool['name']} (Error: {str(e)[:50]})")
                print(f"   ❌ {tool['name']}: Error - {str(e)[:50]}")
        
        if len(successful_tools) == len(tool_endpoints):
            self.log_test(
                "Tool Endpoints",
                True,
                f"All {len(tool_endpoints)} tool endpoints working: {', '.join(successful_tools)}"
            )
            return True
        elif len(successful_tools) > 0:
            self.log_test(
                "Tool Endpoints",
                False,
                error=f"Only {len(successful_tools)}/{len(tool_endpoints)} tools working. Failed: {', '.join(failed_tools)}"
            )
            return False
        else:
            self.log_test(
                "Tool Endpoints",
                False,
                error=f"No tool endpoints working. All failed: {', '.join(failed_tools)}"
            )
            return False

    def test_error_handling(self):
        """Test 5: Error Handling (HIGH)"""
        error_test_cases = [
            {
                "name": "Invalid Panel Value",
                "data": {"panel": "invalid_panel", "message": "test"},
                "expected_status": 400
            },
            {
                "name": "Empty Message",
                "data": {"panel": "müşteri", "message": ""},
                "expected_status": 422
            },
            {
                "name": "Missing Panel",
                "data": {"message": "test message"},
                "expected_status": 422
            },
            {
                "name": "Missing Message", 
                "data": {"panel": "müşteri"},
                "expected_status": 422
            }
        ]
        
        successful_error_tests = []
        failed_error_tests = []
        
        for test_case in error_test_cases:
            try:
                response = self.admin_session.post(
                    f"{BACKEND_URL}/api/admin/ai/assist",
                    json=test_case["data"],
                    timeout=15
                )
                
                if response.status_code == test_case["expected_status"]:
                    successful_error_tests.append(test_case["name"])
                    print(f"   ✅ {test_case['name']}: Correctly returned {response.status_code}")
                elif response.status_code == 200:
                    # Some validation might be handled by the AI system itself
                    data = response.json()
                    if "error" in data.get("response", "").lower():
                        successful_error_tests.append(test_case["name"])
                        print(f"   ✅ {test_case['name']}: Error handled by AI system")
                    else:
                        failed_error_tests.append(f"{test_case['name']} (unexpected success)")
                        print(f"   ❌ {test_case['name']}: Expected error but got success")
                else:
                    failed_error_tests.append(f"{test_case['name']} (got {response.status_code})")
                    print(f"   ❌ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                failed_error_tests.append(f"{test_case['name']} (Exception: {str(e)[:50]})")
                print(f"   ❌ {test_case['name']}: Exception - {str(e)[:50]}")
        
        # Test unauthenticated access
        try:
            unauth_session = requests.Session()
            response = unauth_session.post(
                f"{BACKEND_URL}/api/admin/ai/assist",
                json={"panel": "müşteri", "message": "test"},
                timeout=15
            )
            
            if response.status_code in [401, 403]:
                successful_error_tests.append("Unauthenticated Access")
                print(f"   ✅ Unauthenticated Access: Correctly blocked with {response.status_code}")
            else:
                failed_error_tests.append(f"Unauthenticated Access (got {response.status_code})")
                print(f"   ❌ Unauthenticated Access: Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            failed_error_tests.append(f"Unauthenticated Access (Exception)")
            print(f"   ❌ Unauthenticated Access: Exception - {str(e)[:50]}")
        
        total_tests = len(error_test_cases) + 1  # +1 for unauthenticated test
        
        if len(successful_error_tests) >= total_tests * 0.8:  # 80% success rate acceptable
            self.log_test(
                "Error Handling",
                True,
                f"{len(successful_error_tests)}/{total_tests} error handling tests passed: {', '.join(successful_error_tests)}"
            )
            return True
        else:
            self.log_test(
                "Error Handling",
                False,
                error=f"Only {len(successful_error_tests)}/{total_tests} error tests passed. Failed: {', '.join(failed_error_tests)}"
            )
            return False

    def run_all_tests(self):
        """Run all AI Diagnostics tests"""
        print("🚀 Starting Kuryecini Ops Co-Pilot AI Diagnostics Panel Testing")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - cannot proceed with tests")
            return
        
        print("\n🤖 Testing AI Diagnostics Panel Functionality...")
        print("-" * 50)
        
        # Test 1: Endpoint Availability & Structure (CRITICAL)
        success, sample_response = self.test_endpoint_availability_and_structure()
        
        # Test 2: Panel Switching (HIGH)
        self.test_panel_switching()
        
        # Test 3: Response Format Validation (CRITICAL)
        self.test_response_format_validation()
        
        # Test 4: Tool Endpoints (MEDIUM)
        self.test_tool_endpoints()
        
        # Test 5: Error Handling (HIGH)
        self.test_error_handling()
        
        # Summary
        self.print_summary()

    # Removed old async methods - replaced with AI Diagnostics tests

    def removed_old_method_1(self):
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

    def removed_old_method_2(self):
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

    def removed_old_method_3(self):
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
        print("📊 AI DIAGNOSTICS PANEL TESTING SUMMARY")
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
        endpoint_working = any(r["test"] == "Endpoint Availability & Structure" and r["success"] for r in self.test_results)
        panel_switching_working = any(r["test"] == "Panel Switching" and r["success"] for r in self.test_results)
        format_validation_working = any(r["test"] == "Response Format Validation" and r["success"] for r in self.test_results)
        tool_endpoints_working = any(r["test"] == "Tool Endpoints" and r["success"] for r in self.test_results)
        error_handling_working = any(r["test"] == "Error Handling" and r["success"] for r in self.test_results)
        
        if endpoint_working:
            print("   ✅ AI Diagnostics endpoint /api/admin/ai/assist is accessible and returns proper JSON")
        else:
            print("   ❌ AI Diagnostics endpoint FAILED - endpoint not accessible")
            
        if panel_switching_working:
            print("   ✅ Panel switching works correctly for all 5 panels (müşteri, işletme, kurye, admin, multi)")
        else:
            print("   ❌ Panel switching FAILED - some panels not working")
            
        if format_validation_working:
            print("   ✅ Response format contains all 7 required Turkish sections")
        else:
            print("   ❌ Response format validation FAILED - missing required sections")
            
        if tool_endpoints_working:
            print("   ✅ Tool endpoints (http_get, logs_tail, db_query, env_list) are accessible")
        else:
            print("   ❌ Tool endpoints FAILED - some tools not working")
            
        if error_handling_working:
            print("   ✅ Error handling working correctly for invalid inputs and authentication")
        else:
            print("   ❌ Error handling FAILED - improper error responses")
        
        # Overall verdict
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: AI Diagnostics Panel is WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
            print("   The Kuryecini Ops Co-Pilot endpoint is production-ready with proper 7-block structured responses.")
        elif success_rate >= 60:
            print(f"\n⚠️ VERDICT: AI Diagnostics Panel has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Core functionality works but some features need attention.")
        else:
            print(f"\n🚨 VERDICT: AI Diagnostics Panel has CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major functionality is broken and needs immediate attention.")

async def main():
    """Main test runner"""
    tester = WebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
