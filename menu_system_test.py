#!/usr/bin/env python3
"""
URGENT MENU DISPLAY ISSUE TESTING
User reports: "Eklediğim menüler gözükmüyor" (Added menus not showing)

Comprehensive Menu System Workflow Testing:
1. Menu Database Verification - Check if menus exist for approved businesses
2. Business Menu APIs Testing - Test menu creation and retrieval
3. Customer Menu Access Testing - Check customer menu visibility
4. Menu Collection Analysis - Verify data consistency
5. Authentication & Permissions - Test menu management security
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://address-manager-5.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = [
    {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    {"email": "admin@delivertr.com", "password": "6851"}
]

BUSINESS_CREDENTIALS = [
    {"email": "testbusiness@example.com", "password": "test123"},
    {"email": "testrestoran@example.com", "password": "test123"}
]

CUSTOMER_CREDENTIALS = [
    {"email": "testcustomer@example.com", "password": "test123"}
]

class MenuSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.business_token = None
        self.customer_token = None
        self.test_results = []
        self.business_ids = []
        self.menu_data = {}
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results with detailed information"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 Details: {details}")
        if error:
            print(f"   ❌ Error: {error}")
        print()

    def authenticate_admin(self):
        """Authenticate admin user"""
        print("🔐 ADMIN AUTHENTICATION")
        print("=" * 50)
        
        for creds in ADMIN_CREDENTIALS:
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("access_token")
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    
                    self.log_test(
                        "Admin Authentication",
                        True,
                        f"Admin login successful with {creds['email']} - Token: {len(self.admin_token)} chars"
                    )
                    return True
                    
            except Exception as e:
                continue
                
        self.log_test("Admin Authentication", False, "", "All admin credentials failed")
        return False

    def authenticate_business(self):
        """Authenticate business user"""
        print("🏪 BUSINESS AUTHENTICATION")
        print("=" * 50)
        
        for creds in BUSINESS_CREDENTIALS:
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                if response.status_code == 200:
                    data = response.json()
                    self.business_token = data.get("access_token")
                    business_headers = {"Authorization": f"Bearer {self.business_token}"}
                    
                    self.log_test(
                        "Business Authentication",
                        True,
                        f"Business login successful with {creds['email']} - Token: {len(self.business_token)} chars"
                    )
                    return business_headers
                    
            except Exception as e:
                continue
                
        self.log_test("Business Authentication", False, "", "All business credentials failed")
        return None

    def authenticate_customer(self):
        """Authenticate customer user"""
        print("👤 CUSTOMER AUTHENTICATION")
        print("=" * 50)
        
        for creds in CUSTOMER_CREDENTIALS:
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                if response.status_code == 200:
                    data = response.json()
                    self.customer_token = data.get("access_token")
                    customer_headers = {"Authorization": f"Bearer {self.customer_token}"}
                    
                    self.log_test(
                        "Customer Authentication",
                        True,
                        f"Customer login successful with {creds['email']} - Token: {len(self.customer_token)} chars"
                    )
                    return customer_headers
                    
            except Exception as e:
                continue
                
        self.log_test("Customer Authentication", False, "", "All customer credentials failed")
        return None

    def test_menu_database_verification(self):
        """1. Menu Database Verification - Check if menus exist for approved businesses"""
        print("📊 MENU DATABASE VERIFICATION")
        print("=" * 50)
        
        try:
            # Get all approved businesses
            response = self.session.get(f"{BACKEND_URL}/admin/businesses?kyc_status=approved")
            if response.status_code == 200:
                businesses = response.json()
                approved_count = len(businesses) if isinstance(businesses, list) else 0
                
                self.log_test(
                    "Get Approved Businesses",
                    True,
                    f"Found {approved_count} approved businesses"
                )
                
                # Check menus for each approved business
                businesses_with_menus = 0
                total_menu_items = 0
                
                for business in (businesses if isinstance(businesses, list) else []):
                    business_id = business.get("id")
                    if business_id:
                        self.business_ids.append(business_id)
                        
                        # Test GET /api/businesses/{business_id}/products
                        menu_response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
                        if menu_response.status_code == 200:
                            menu_data = menu_response.json()
                            menu_items = len(menu_data) if isinstance(menu_data, list) else 0
                            
                            if menu_items > 0:
                                businesses_with_menus += 1
                                total_menu_items += menu_items
                                self.menu_data[business_id] = menu_data
                                
                                self.log_test(
                                    f"Business Menu Check - {business.get('business_name', business_id)}",
                                    True,
                                    f"Found {menu_items} menu items"
                                )
                            else:
                                self.log_test(
                                    f"Business Menu Check - {business.get('business_name', business_id)}",
                                    False,
                                    f"No menu items found",
                                    "Business has no products/menu items"
                                )
                        else:
                            self.log_test(
                                f"Business Menu API - {business.get('business_name', business_id)}",
                                False,
                                f"API returned {menu_response.status_code}",
                                menu_response.text[:200]
                            )
                
                self.log_test(
                    "Menu Database Summary",
                    businesses_with_menus > 0,
                    f"{businesses_with_menus}/{approved_count} approved businesses have menus. Total menu items: {total_menu_items}"
                )
                
            else:
                self.log_test(
                    "Get Approved Businesses",
                    False,
                    f"API returned {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test("Menu Database Verification", False, "", str(e))

    def test_business_menu_apis(self):
        """2. Business Menu APIs Testing - Test menu creation and retrieval"""
        print("🏪 BUSINESS MENU APIs TESTING")
        print("=" * 50)
        
        business_headers = self.authenticate_business()
        if not business_headers:
            self.log_test("Business Menu APIs", False, "", "Business authentication failed")
            return
            
        try:
            # Test GET /api/business/menu (business menu retrieval)
            response = self.session.get(f"{BACKEND_URL}/business/menu", headers=business_headers)
            if response.status_code == 200:
                menu_data = response.json()
                menu_count = len(menu_data) if isinstance(menu_data, list) else 0
                
                self.log_test(
                    "GET /api/business/menu",
                    True,
                    f"Retrieved {menu_count} menu items for business"
                )
            else:
                self.log_test(
                    "GET /api/business/menu",
                    False,
                    f"API returned {response.status_code}",
                    response.text[:200]
                )
            
            # Test POST /api/business/menu (business menu creation)
            test_menu_item = {
                "name": f"Test Menu Item {int(time.time())}",
                "description": "Test menu item for urgent menu display issue testing",
                "price": 25.50,
                "category": "Test Category",
                "preparation_time_minutes": 15,
                "is_available": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/business/menu", json=test_menu_item, headers=business_headers)
            if response.status_code in [200, 201]:
                created_item = response.json()
                item_id = created_item.get("id")
                
                self.log_test(
                    "POST /api/business/menu",
                    True,
                    f"Successfully created menu item: {test_menu_item['name']} (ID: {item_id})"
                )
                
                # Verify the created item can be retrieved
                time.sleep(1)  # Brief delay for database consistency
                verify_response = self.session.get(f"{BACKEND_URL}/business/menu", headers=business_headers)
                if verify_response.status_code == 200:
                    updated_menu = verify_response.json()
                    found_item = any(item.get("name") == test_menu_item["name"] for item in (updated_menu if isinstance(updated_menu, list) else []))
                    
                    self.log_test(
                        "Menu Item Verification",
                        found_item,
                        f"Created menu item {'found' if found_item else 'NOT found'} in business menu list"
                    )
                
            else:
                self.log_test(
                    "POST /api/business/menu",
                    False,
                    f"API returned {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test("Business Menu APIs Testing", False, "", str(e))

    def test_customer_menu_access(self):
        """3. Customer Menu Access Testing - Check if customers can see business menus"""
        print("👤 CUSTOMER MENU ACCESS TESTING")
        print("=" * 50)
        
        customer_headers = self.authenticate_customer()
        if not customer_headers:
            self.log_test("Customer Menu Access", False, "", "Customer authentication failed")
            return
            
        try:
            # Test multiple business IDs for menu visibility
            for business_id in self.business_ids[:5]:  # Test first 5 businesses
                response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products", headers=customer_headers)
                
                if response.status_code == 200:
                    menu_data = response.json()
                    menu_count = len(menu_data) if isinstance(menu_data, list) else 0
                    
                    self.log_test(
                        f"Customer Menu Access - Business {business_id}",
                        menu_count > 0,
                        f"Customer can see {menu_count} menu items"
                    )
                    
                    # Show sample menu items
                    if menu_count > 0 and isinstance(menu_data, list):
                        sample_items = menu_data[:3]  # Show first 3 items
                        for item in sample_items:
                            print(f"   📋 {item.get('name', 'Unknown')} - ₺{item.get('price', 0)}")
                            
                else:
                    self.log_test(
                        f"Customer Menu Access - Business {business_id}",
                        False,
                        f"API returned {response.status_code}",
                        response.text[:200]
                    )
            
            # Test public menu endpoints
            response = self.session.get(f"{BACKEND_URL}/../menus/public")  # Remove /api prefix for public endpoint
            if response.status_code == 200:
                public_data = response.json()
                restaurant_count = len(public_data.get("restaurants", [])) if isinstance(public_data, dict) else 0
                
                self.log_test(
                    "Public Menu Endpoint",
                    restaurant_count > 0,
                    f"Public endpoint shows {restaurant_count} restaurants with menus"
                )
            else:
                self.log_test(
                    "Public Menu Endpoint",
                    False,
                    f"API returned {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test("Customer Menu Access Testing", False, "", str(e))

    def test_menu_collection_analysis(self):
        """4. Menu Collection Analysis - Check both menu_items and products collections"""
        print("🔍 MENU COLLECTION ANALYSIS")
        print("=" * 50)
        
        try:
            # Test different menu-related endpoints to understand data structure
            endpoints_to_test = [
                "/admin/products",
                "/admin/businesses",
                "/menus",
                "/menus/public"
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    # Use appropriate URL format
                    if endpoint.startswith("/menus"):
                        url = f"https://address-manager-5.preview.emergentagent.com{endpoint}"
                    else:
                        url = f"{BACKEND_URL}{endpoint}"
                        
                    response = self.session.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if endpoint == "/admin/products":
                            product_count = len(data) if isinstance(data, list) else 0
                            self.log_test(
                                f"Collection Analysis - {endpoint}",
                                True,
                                f"Found {product_count} products in admin collection"
                            )
                            
                        elif endpoint == "/admin/businesses":
                            business_count = len(data) if isinstance(data, list) else 0
                            approved_businesses = [b for b in (data if isinstance(data, list) else []) if b.get("kyc_status") == "approved"]
                            self.log_test(
                                f"Collection Analysis - {endpoint}",
                                True,
                                f"Found {business_count} total businesses, {len(approved_businesses)} approved"
                            )
                            
                        elif endpoint == "/menus":
                            menu_count = len(data) if isinstance(data, list) else 0
                            self.log_test(
                                f"Collection Analysis - {endpoint}",
                                True,
                                f"Legacy menu endpoint returns {menu_count} items"
                            )
                            
                        elif endpoint == "/menus/public":
                            if isinstance(data, dict):
                                restaurant_count = len(data.get("restaurants", []))
                                total_menu_items = sum(len(r.get("menu", [])) for r in data.get("restaurants", []))
                                self.log_test(
                                    f"Collection Analysis - {endpoint}",
                                    True,
                                    f"Public menu shows {restaurant_count} restaurants with {total_menu_items} total menu items"
                                )
                            else:
                                self.log_test(
                                    f"Collection Analysis - {endpoint}",
                                    False,
                                    "Unexpected data format",
                                    f"Expected dict, got {type(data)}"
                                )
                    else:
                        self.log_test(
                            f"Collection Analysis - {endpoint}",
                            False,
                            f"API returned {response.status_code}",
                            response.text[:200]
                        )
                        
                except Exception as e:
                    self.log_test(f"Collection Analysis - {endpoint}", False, "", str(e))
                    
        except Exception as e:
            self.log_test("Menu Collection Analysis", False, "", str(e))

    def test_authentication_permissions(self):
        """5. Authentication & Permissions - Test menu management security"""
        print("🔐 AUTHENTICATION & PERMISSIONS TESTING")
        print("=" * 50)
        
        try:
            # Test menu creation without authentication
            test_menu_item = {
                "name": "Unauthorized Test Item",
                "description": "This should fail",
                "price": 10.0,
                "category": "Test"
            }
            
            response = self.session.post(f"{BACKEND_URL}/business/menu", json=test_menu_item)
            
            self.log_test(
                "Menu Creation Without Auth",
                response.status_code in [401, 403],
                f"Correctly rejected with status {response.status_code}" if response.status_code in [401, 403] else f"Unexpectedly allowed with status {response.status_code}"
            )
            
            # Test menu retrieval without authentication
            response = self.session.get(f"{BACKEND_URL}/business/menu")
            
            self.log_test(
                "Menu Retrieval Without Auth",
                response.status_code in [401, 403],
                f"Correctly rejected with status {response.status_code}" if response.status_code in [401, 403] else f"Unexpectedly allowed with status {response.status_code}"
            )
            
            # Test RBAC - customer trying to access business menu management
            customer_headers = self.authenticate_customer()
            if customer_headers:
                response = self.session.post(f"{BACKEND_URL}/business/menu", json=test_menu_item, headers=customer_headers)
                
                self.log_test(
                    "Customer Access to Business Menu",
                    response.status_code in [401, 403],
                    f"Customer correctly blocked with status {response.status_code}" if response.status_code in [401, 403] else f"Customer unexpectedly allowed with status {response.status_code}"
                )
            
            # Test KYC approval requirement
            business_headers = self.authenticate_business()
            if business_headers:
                response = self.session.get(f"{BACKEND_URL}/business/menu", headers=business_headers)
                
                if response.status_code == 200:
                    self.log_test(
                        "KYC Approved Business Menu Access",
                        True,
                        "Business can access menu management (KYC approved)"
                    )
                elif response.status_code == 403:
                    self.log_test(
                        "KYC Pending Business Menu Access",
                        True,
                        "Business correctly blocked - KYC approval required"
                    )
                else:
                    self.log_test(
                        "Business Menu Access",
                        False,
                        f"Unexpected status {response.status_code}",
                        response.text[:200]
                    )
                    
        except Exception as e:
            self.log_test("Authentication & Permissions Testing", False, "", str(e))

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 URGENT MENU DISPLAY ISSUE - COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Group results by category
        categories = {
            "Authentication": [],
            "Menu Database": [],
            "Business Menu APIs": [],
            "Customer Menu Access": [],
            "Collection Analysis": [],
            "Security & Permissions": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Authentication" in test_name:
                categories["Authentication"].append(result)
            elif "Database" in test_name or "Approved Business" in test_name:
                categories["Menu Database"].append(result)
            elif "business/menu" in test_name or "Business Menu" in test_name:
                categories["Business Menu APIs"].append(result)
            elif "Customer" in test_name or "Public Menu" in test_name:
                categories["Customer Menu Access"].append(result)
            elif "Collection" in test_name:
                categories["Collection Analysis"].append(result)
            else:
                categories["Security & Permissions"].append(result)
        
        # Print category summaries
        for category, results in categories.items():
            if results:
                passed = len([r for r in results if r["success"]])
                total = len(results)
                print(f"🔍 {category}: {passed}/{total} passed")
                
                # Show failed tests
                failed = [r for r in results if not r["success"]]
                if failed:
                    print("   ❌ FAILED TESTS:")
                    for fail in failed:
                        print(f"      • {fail['test']}: {fail['error']}")
                print()
        
        # Critical findings
        print("🚨 CRITICAL FINDINGS:")
        critical_issues = []
        
        # Check for menu availability issues
        menu_db_tests = [r for r in self.test_results if "Menu Database" in r["test"] or "Business Menu Check" in r["test"]]
        businesses_without_menus = len([r for r in menu_db_tests if not r["success"] and "No menu items found" in r["error"]])
        
        if businesses_without_menus > 0:
            critical_issues.append(f"🔴 {businesses_without_menus} approved businesses have NO menu items")
        
        # Check for API failures
        api_failures = [r for r in self.test_results if not r["success"] and ("API returned" in r["error"] or "authentication failed" in r["error"])]
        if api_failures:
            critical_issues.append(f"🔴 {len(api_failures)} API endpoint failures detected")
        
        # Check for customer access issues
        customer_access_failures = [r for r in self.test_results if not r["success"] and "Customer Menu Access" in r["test"]]
        if customer_access_failures:
            critical_issues.append(f"🔴 Customer menu access issues: {len(customer_access_failures)} failures")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"   {issue}")
        else:
            print("   ✅ No critical issues detected in menu system")
        
        print()
        print("💡 RECOMMENDATIONS:")
        
        if businesses_without_menus > 0:
            print("   1. 🔧 URGENT: Investigate why approved businesses have empty menus")
            print("      - Check if menu creation API is working properly")
            print("      - Verify database consistency between users and products collections")
            print("      - Ensure business menu creation workflow is functional")
        
        if customer_access_failures:
            print("   2. 🔧 URGENT: Fix customer menu visibility issues")
            print("      - Verify GET /api/businesses/{business_id}/products endpoint")
            print("      - Check KYC approval filtering logic")
            print("      - Test public menu endpoints")
        
        if api_failures:
            print("   3. 🔧 HIGH: Resolve API endpoint failures")
            print("      - Check authentication middleware")
            print("      - Verify database connections")
            print("      - Review error handling")
        
        print("   4. 📋 Monitor menu creation workflow end-to-end")
        print("   5. 🔍 Implement menu visibility debugging tools")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "critical_issues": critical_issues,
            "detailed_results": self.test_results
        }

    def run_all_tests(self):
        """Run all menu system tests"""
        print("🚀 STARTING URGENT MENU DISPLAY ISSUE INVESTIGATION")
        print("User Report: 'Eklediğim menüler gözükmüyor' (Added menus not showing)")
        print("=" * 80)
        
        # Authenticate admin first
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Run all test categories
        self.test_menu_database_verification()
        self.test_business_menu_apis()
        self.test_customer_menu_access()
        self.test_menu_collection_analysis()
        self.test_authentication_permissions()
        
        # Generate comprehensive summary
        return self.generate_summary()

if __name__ == "__main__":
    tester = MenuSystemTester()
    summary = tester.run_all_tests()
    
    print(f"\n🎯 FINAL VERDICT: {summary['success_rate']:.1f}% success rate")
    if summary['critical_issues']:
        print("🚨 URGENT ACTION REQUIRED - Critical menu system issues detected!")
    else:
        print("✅ Menu system appears to be functioning correctly")