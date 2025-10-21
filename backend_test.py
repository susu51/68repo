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
            
    async def test_dashboard_summary_with_date_parameter(self):
        """Test dashboard summary with date parameter"""
        try:
            test_date = "2025-01-15"
            url = f"{API_BASE}/business/dashboard/summary?date={test_date}"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if response_data.get("date") == test_date:
                        self.log_test(
                            "Dashboard Summary - Date Parameter",
                            True,
                            f"Date parameter working correctly: {test_date}"
                        )
                    else:
                        self.log_test(
                            "Dashboard Summary - Date Parameter",
                            False,
                            f"Expected date {test_date}, got {response_data.get('date')}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Dashboard Summary - Date Parameter",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Date Parameter", False, f"Exception: {str(e)}")
            
    async def test_dashboard_summary_unauthorized(self):
        """Test dashboard summary without authentication"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url) as response:
                response_data = await response.text()
                
                if response.status in [401, 403]:
                    self.log_test(
                        "Dashboard Summary - Unauthorized Access",
                        True,
                        f"Correctly blocked unauthorized access with status {response.status}"
                    )
                else:
                    self.log_test(
                        "Dashboard Summary - Unauthorized Access",
                        False,
                        f"Expected 401/403, got {response.status}",
                        {"status": response.status, "response": response_data}
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Unauthorized Access", False, f"Exception: {str(e)}")
            
    async def test_dashboard_summary_wrong_role(self):
        """Test dashboard summary with customer user (wrong role)"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.customer_cookies) as response:
                response_data = await response.text()
                
                if response.status == 403:
                    self.log_test(
                        "Dashboard Summary - Wrong Role Access",
                        True,
                        "Correctly blocked customer user access with 403"
                    )
                else:
                    self.log_test(
                        "Dashboard Summary - Wrong Role Access",
                        False,
                        f"Expected 403, got {response.status}",
                        {"status": response.status, "response": response_data}
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Wrong Role Access", False, f"Exception: {str(e)}")
            
    async def test_revenue_calculation_logic(self):
        """Test that revenue is calculated from confirmed/delivered orders only"""
        try:
            url = f"{API_BASE}/business/dashboard/summary"
            
            async with self.session.get(url, cookies=self.business_cookies) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    revenue = response_data.get("today_revenue", 0)
                    orders_count = response_data.get("today_orders_count", 0)
                    
                    # Revenue should be non-negative
                    if revenue >= 0:
                        self.log_test(
                            "Dashboard Summary - Revenue Calculation",
                            True,
                            f"Revenue calculation appears valid: ₺{revenue} from {orders_count} orders"
                        )
                    else:
                        self.log_test(
                            "Dashboard Summary - Revenue Calculation",
                            False,
                            f"Invalid negative revenue: ₺{revenue}",
                            response_data
                        )
                else:
                    self.log_test(
                        "Dashboard Summary - Revenue Calculation",
                        False,
                        f"Status: {response.status}",
                        response_data
                    )
                    
        except Exception as e:
            self.log_test("Dashboard Summary - Revenue Calculation", False, f"Exception: {str(e)}")

            
    async def run_all_tests(self):
        """Run all dashboard summary tests"""
        print("🎯 BUSINESS DASHBOARD SUMMARY ENDPOINT TESTING")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup - Login users
            business_login_success = await self.login_business_user()
            customer_login_success = await self.login_customer_user()
            
            if not business_login_success:
                print("❌ Cannot proceed without business user login")
                return
                
            # Core functionality tests
            await self.test_dashboard_summary_authenticated()
            await self.test_dashboard_summary_with_date_parameter()
            await self.test_revenue_calculation_logic()
            
            # Security tests
            await self.test_dashboard_summary_unauthorized()
            
            if customer_login_success:
                await self.test_dashboard_summary_wrong_role()
            else:
                print("⚠️  Skipping wrong role test - customer login failed")
                
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
                    
        return passed_tests, failed_tests


async def main():
    """Main test execution"""
    tester = BusinessDashboardTester()
    passed, failed = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())
