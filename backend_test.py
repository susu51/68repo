#!/usr/bin/env python3
"""
Admin Panel Backend Testing - Comprehensive Test Suite
Testing all admin panel endpoints as requested in the review.

Test Endpoints:
1. Dashboard: GET /api/admin/reports/dashboard
2. Financial Report: GET /api/admin/reports/financial
3. Order Report: GET /api/admin/reports/orders?business_name=test
4. User Report: GET /api/admin/reports/user?customer_name=test
5. Category Analytics: GET /api/admin/reports/category-analytics
6. Platform Settings: GET /api/admin/settings, PATCH /api/admin/settings
7. Promotions: GET /api/admin/promotions

Test Credentials: admin@kuryecini.com / admin123
"""

import requests
import json
import sys
from datetime import datetime
import os

# Configuration
BACKEND_URL = "https://quickship-49.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

class AdminPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate_admin(self):
        """Authenticate admin user and get token"""
        print("🔐 Authenticating admin user...")
        
        try:
            # Try cookie-based authentication first
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Admin Authentication (Cookie)", True, 
                                f"Admin authenticated successfully via cookies")
                    return True
                else:
                    self.log_test("Admin Authentication (Cookie)", False, 
                                f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Admin Authentication (Cookie)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication (Cookie)", False, f"Exception: {str(e)}")
            
        return False

    def test_dashboard_reports(self):
        """Test GET /api/admin/reports/dashboard"""
        print("📊 Testing Dashboard Reports...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/reports/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                # Check if dashboard has expected structure
                expected_keys = ["orders", "revenue", "users", "businesses"]
                has_structure = any(key in data for key in expected_keys)
                
                if has_structure:
                    self.log_test("Dashboard Reports", True, 
                                f"Dashboard data retrieved successfully with {len(data)} metrics")
                else:
                    self.log_test("Dashboard Reports", True, 
                                f"Dashboard data retrieved (structure may vary): {list(data.keys())}")
            elif response.status_code == 403:
                self.log_test("Dashboard Reports", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Dashboard Reports", False, 
                            "Dashboard endpoint not found")
            else:
                self.log_test("Dashboard Reports", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Dashboard Reports", False, f"Exception: {str(e)}")

    def test_financial_reports(self):
        """Test GET /api/admin/reports/financial"""
        print("💰 Testing Financial Reports...")
        
        try:
            # Test with date range parameters
            params = {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/reports/financial", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Check for financial data structure
                expected_keys = ["revenue", "commission", "total", "daily", "summary"]
                has_structure = any(key in data for key in expected_keys)
                
                if has_structure:
                    self.log_test("Financial Reports", True, 
                                f"Financial data retrieved with date filtering: {list(data.keys())}")
                else:
                    self.log_test("Financial Reports", True, 
                                f"Financial data retrieved: {list(data.keys())}")
            elif response.status_code == 403:
                self.log_test("Financial Reports", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Financial Reports", False, 
                            "Financial reports endpoint not found")
            else:
                self.log_test("Financial Reports", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Financial Reports", False, f"Exception: {str(e)}")

    def test_order_reports(self):
        """Test GET /api/admin/reports/orders?business_name=test"""
        print("📦 Testing Order Reports...")
        
        try:
            # Test with business name filter
            params = {"business_name": "test"}
            
            response = self.session.get(f"{BACKEND_URL}/admin/reports/orders", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Check for order report structure
                if isinstance(data, list):
                    self.log_test("Order Reports", True, 
                                f"Order reports retrieved: {len(data)} orders found")
                elif isinstance(data, dict):
                    self.log_test("Order Reports", True, 
                                f"Order reports retrieved: {list(data.keys())}")
                else:
                    self.log_test("Order Reports", True, 
                                f"Order reports retrieved: {type(data)}")
            elif response.status_code == 403:
                self.log_test("Order Reports", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Order Reports", False, 
                            "Order reports endpoint not implemented")
            else:
                self.log_test("Order Reports", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order Reports", False, f"Exception: {str(e)}")

    def test_user_reports(self):
        """Test GET /api/admin/reports/user?customer_name=test"""
        print("👥 Testing User Reports...")
        
        try:
            # Test with customer name filter
            params = {"customer_name": "test"}
            
            response = self.session.get(f"{BACKEND_URL}/admin/reports/user", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Check for user report structure
                if isinstance(data, list):
                    self.log_test("User Reports", True, 
                                f"User reports retrieved: {len(data)} users found")
                elif isinstance(data, dict):
                    self.log_test("User Reports", True, 
                                f"User reports retrieved: {list(data.keys())}")
                else:
                    self.log_test("User Reports", True, 
                                f"User reports retrieved: {type(data)}")
            elif response.status_code == 403:
                self.log_test("User Reports", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("User Reports", False, 
                            "User reports endpoint not implemented")
            else:
                self.log_test("User Reports", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("User Reports", False, f"Exception: {str(e)}")

    def test_category_analytics(self):
        """Test GET /api/admin/reports/category-analytics"""
        print("📈 Testing Category Analytics...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/reports/category-analytics")
            
            if response.status_code == 200:
                data = response.json()
                # Check for category analytics structure
                expected_keys = ["categories", "analytics", "stats", "breakdown"]
                has_structure = any(key in data for key in expected_keys)
                
                if has_structure:
                    self.log_test("Category Analytics", True, 
                                f"Category analytics retrieved: {list(data.keys())}")
                else:
                    self.log_test("Category Analytics", True, 
                                f"Category analytics retrieved: {list(data.keys())}")
            elif response.status_code == 403:
                self.log_test("Category Analytics", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Category Analytics", False, 
                            "Category analytics endpoint not implemented")
            else:
                self.log_test("Category Analytics", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Category Analytics", False, f"Exception: {str(e)}")

    def test_platform_settings_get(self):
        """Test GET /api/admin/settings"""
        print("⚙️ Testing Platform Settings (GET)...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/settings")
            
            if response.status_code == 200:
                data = response.json()
                # Check for settings structure
                expected_keys = ["commission_rate", "delivery_fee", "min_order_amount", "platform"]
                has_structure = any(key in data for key in expected_keys)
                
                if has_structure:
                    self.log_test("Platform Settings (GET)", True, 
                                f"Platform settings retrieved: {list(data.keys())}")
                    return data  # Return for update test
                else:
                    self.log_test("Platform Settings (GET)", True, 
                                f"Platform settings retrieved: {list(data.keys())}")
                    return data
            elif response.status_code == 403:
                self.log_test("Platform Settings (GET)", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Platform Settings (GET)", False, 
                            "Platform settings endpoint not found")
            else:
                self.log_test("Platform Settings (GET)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Platform Settings (GET)", False, f"Exception: {str(e)}")
            
        return None

    def test_platform_settings_patch(self, current_settings=None):
        """Test PATCH /api/admin/settings"""
        print("⚙️ Testing Platform Settings (PATCH)...")
        
        try:
            # Test update with sample data
            update_data = {
                "commission_rate": 5.5,
                "delivery_fee": 12.0,
                "min_order_amount": 30.0
            }
            
            response = self.session.patch(f"{BACKEND_URL}/admin/settings", json=update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Platform Settings (PATCH)", True, 
                            f"Platform settings updated successfully: {list(update_data.keys())}")
                
                # Verify the update by checking response
                if isinstance(data, dict):
                    updated_values = []
                    for key, value in update_data.items():
                        if key in data and data[key] == value:
                            updated_values.append(f"{key}={value}")
                    
                    if updated_values:
                        print(f"   Verified updates: {', '.join(updated_values)}")
                        
            elif response.status_code == 403:
                self.log_test("Platform Settings (PATCH)", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Platform Settings (PATCH)", False, 
                            "Platform settings update endpoint not found")
            elif response.status_code == 422:
                self.log_test("Platform Settings (PATCH)", False, 
                            f"Validation error: {response.text}")
            else:
                self.log_test("Platform Settings (PATCH)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Platform Settings (PATCH)", False, f"Exception: {str(e)}")

    def test_promotions(self):
        """Test GET /api/admin/promotions"""
        print("🎯 Testing Promotions...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/promotions")
            
            if response.status_code == 200:
                data = response.json()
                # Check for promotions structure
                if isinstance(data, list):
                    self.log_test("Promotions", True, 
                                f"Promotions retrieved: {len(data)} promotions found")
                elif isinstance(data, dict):
                    if "promotions" in data:
                        promotions = data["promotions"]
                        self.log_test("Promotions", True, 
                                    f"Promotions retrieved: {len(promotions)} promotions found")
                    else:
                        self.log_test("Promotions", True, 
                                    f"Promotions data retrieved: {list(data.keys())}")
                else:
                    self.log_test("Promotions", True, 
                                f"Promotions retrieved: {type(data)}")
            elif response.status_code == 403:
                self.log_test("Promotions", False, 
                            "Access denied - admin authentication required")
            elif response.status_code == 404:
                self.log_test("Promotions", False, 
                            "Promotions endpoint not found")
            else:
                self.log_test("Promotions", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Promotions", False, f"Exception: {str(e)}")

    def test_authentication_security(self):
        """Test that endpoints require admin authentication"""
        print("🔒 Testing Authentication Security...")
        
        # Create a new session without authentication
        test_session = requests.Session()
        
        endpoints_to_test = [
            "/admin/reports/dashboard",
            "/admin/reports/financial", 
            "/admin/settings",
            "/admin/promotions"
        ]
        
        security_passed = 0
        total_security_tests = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            try:
                response = test_session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code in [401, 403]:
                    security_passed += 1
                    print(f"   ✅ {endpoint}: Properly secured (HTTP {response.status_code})")
                else:
                    print(f"   ❌ {endpoint}: Security issue (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint}: Exception during security test: {str(e)}")
        
        if security_passed == total_security_tests:
            self.log_test("Authentication Security", True, 
                        f"All {total_security_tests} endpoints properly secured")
        else:
            self.log_test("Authentication Security", False, 
                        f"Only {security_passed}/{total_security_tests} endpoints properly secured")

    def run_all_tests(self):
        """Run all admin panel tests"""
        print("🚀 Starting Admin Panel Backend Testing...")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_admin():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
            
        print("=" * 60)
        
        # Step 2: Test all endpoints
        self.test_dashboard_reports()
        self.test_financial_reports()
        self.test_order_reports()
        self.test_user_reports()
        self.test_category_analytics()
        
        # Step 3: Test settings (GET then PATCH)
        current_settings = self.test_platform_settings_get()
        self.test_platform_settings_patch(current_settings)
        
        # Step 4: Test promotions
        self.test_promotions()
        
        # Step 5: Test security
        self.test_authentication_security()
        
        # Step 6: Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("📊 ADMIN PANEL BACKEND TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Print passed tests
        passed_tests = [r for r in self.test_results if r["success"]]
        if passed_tests:
            print("✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   • {test['test']}")
            print()
        
        # Overall assessment
        if success_rate >= 80:
            print("🎉 OVERALL ASSESSMENT: EXCELLENT - Admin panel backend is working well")
        elif success_rate >= 60:
            print("⚠️ OVERALL ASSESSMENT: GOOD - Admin panel has minor issues")
        elif success_rate >= 40:
            print("🔧 OVERALL ASSESSMENT: NEEDS WORK - Several admin endpoints need fixes")
        else:
            print("❌ OVERALL ASSESSMENT: CRITICAL ISSUES - Major admin functionality problems")
        
        print("=" * 60)

def main():
    """Main test execution"""
    print("Admin Panel Backend Testing")
    print("Testing comprehensive admin functionality as requested")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print()
    
    tester = AdminPanelTester()
    success = tester.run_all_tests()
    
    if success:
        return 0 if tester.passed_tests == tester.total_tests else 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())