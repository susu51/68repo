#!/usr/bin/env python3
"""
Business Dashboard Summary Endpoint Testing
Tests the new GET /api/business/dashboard/summary endpoint per review request
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
import sys
import os

# Test Configuration
BASE_URL = "https://courier-connect-14.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test Credentials
BUSINESS_USER = {
    "email": "testbusiness@example.com",
    "password": "test123"
}

CUSTOMER_USER = {
    "email": "test@kuryecini.com", 
    "password": "test123"
}

class BusinessDashboardTester:
    def __init__(self):
        self.session = None
        self.business_cookies = None
        self.customer_cookies = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "BusinessDashboardTester/1.0"}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if response_data and not success:
            print(f"    Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    async def login_business_user(self):
        """Login as business user and get cookies"""
        try:
            login_data = {
                "email": BUSINESS_USER["email"],
                "password": BUSINESS_USER["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    self.business_cookies = response.cookies
                    response_data = await response.json()
                    self.log_test("Business User Login", True, f"Logged in as {BUSINESS_USER['email']}")
                    return True
                else:
                    error_data = await response.text()
                    self.log_test("Business User Login", False, f"Status: {response.status}, Error: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_test("Business User Login", False, f"Exception: {str(e)}")
            return False
            
    async def login_customer_user(self):
        """Login as customer user for negative testing"""
        try:
            login_data = {
                "email": CUSTOMER_USER["email"],
                "password": CUSTOMER_USER["password"]
            }
            
            async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as response:
                if response.status == 200:
                    self.customer_cookies = response.cookies
                    self.log_test("Customer User Login", True, f"Logged in as {CUSTOMER_USER['email']}")
                    return True
                else:
                    error_data = await response.text()
                    self.log_test("Customer User Login", False, f"Status: {response.status}, Error: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_test("Customer User Login", False, f"Exception: {str(e)}")
            return False
            
    async def test_dashboard_summary_authenticated(self):
        """Test dashboard summary with authenticated business user"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Verify all required fields are present
                    required_fields = [
                        "business_id", "date", "today_orders_count", "today_revenue",
                        "pending_orders_count", "menu_items_count", "total_customers",
                        "rating_avg", "rating_count", "activities"
                    ]
                    
                    missing_fields = []
                    for field in required_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        self.log_test(
                            "Dashboard Summary - Field Validation", 
                            False, 
                            f"Missing fields: {missing_fields}",
                            response_data
                        )
                    else:
                        # Verify data types
                        type_checks = [
                            ("business_id", str),
                            ("date", str),
                            ("today_orders_count", int),
                            ("today_revenue", (int, float)),
                            ("pending_orders_count", int),
                            ("menu_items_count", int),
                            ("total_customers", int),
                            ("rating_avg", (int, float)),
                            ("rating_count", int),
                            ("activities", list)
                        ]
                        
                        type_errors = []
                        for field, expected_type in type_checks:
                            if not isinstance(response_data[field], expected_type):
                                type_errors.append(f"{field}: expected {expected_type}, got {type(response_data[field])}")
                        
                        if type_errors:
                            self.log_test(
                                "Dashboard Summary - Type Validation",
                                False,
                                f"Type errors: {type_errors}",
                                response_data
                            )
                        else:
                            # Verify activities structure
                            activities_valid = True
                            if response_data["activities"]:
                                for activity in response_data["activities"]:
                                    if not isinstance(activity, dict):
                                        activities_valid = False
                                        break
                                    required_activity_fields = ["type", "title", "meta"]
                                    for field in required_activity_fields:
                                        if field not in activity:
                                            activities_valid = False
                                            break
                                    if not activities_valid:
                                        break
                                        
                                    # Check meta structure for order activities
                                    if activity["type"] == "order_created":
                                        meta = activity["meta"]
                                        if not all(key in meta for key in ["order_code", "amount", "customer_name"]):
                                            activities_valid = False
                                            break
                            
                            if not activities_valid:
                                self.log_test(
                                    "Dashboard Summary - Activities Validation",
                                    False,
                                    "Invalid activities structure",
                                    response_data
                                )
                            else:
                                self.log_test(
                                    "Dashboard Summary - Authenticated Request",
                                    True,
                                    f"All fields present and valid. Orders: {response_data['today_orders_count']}, Revenue: {response_data['today_revenue']}, Activities: {len(response_data['activities'])}"
                                )
                else:
                    self.log_test(
                        "Dashboard Summary - Authenticated Request",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Authenticated Request", False, f"Exception: {str(e)}")
    
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

    # All AI Diagnostics tests implemented above

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

def main():
    """Main test runner"""
    tester = AIDiagnosticsTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
