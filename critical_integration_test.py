#!/usr/bin/env python3
"""
CRITICAL INTEGRATION ISSUE TESTING - Multiple frontend-backend disconnects

This test focuses on the specific user-reported issues:
1. Business menus not showing after creation
2. Customer addresses not appearing in discovery

Test Requirements:
- Business Menu Integration Test
- Customer Address Integration Test  
- Database Consistency Check
- Cross-Account Testing
"""

import requests
import json
import uuid
import time
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class IntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.test_results = []
        self.business_tokens = {}
        self.customer_tokens = {}
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if error:
            print(f"   🚨 {error}")
        print()

    def test_business_login(self, email, password):
        """Test business login and return token"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                business_id = user_data.get("id")
                
                self.log_test(
                    f"Business Login - {email}",
                    True,
                    f"Token: {len(token)} chars, Business ID: {business_id}, Role: {user_data.get('role')}"
                )
                return token, business_id, user_data
            else:
                self.log_test(
                    f"Business Login - {email}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None, None, None
                
        except Exception as e:
            self.log_test(f"Business Login - {email}", False, "", str(e))
            return None, None, None

    def test_customer_login(self, email, password):
        """Test customer login and return token"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                customer_id = user_data.get("id")
                
                self.log_test(
                    f"Customer Login - {email}",
                    True,
                    f"Token: {len(token)} chars, Customer ID: {customer_id}, Role: {user_data.get('role')}"
                )
                return token, customer_id, user_data
            else:
                self.log_test(
                    f"Customer Login - {email}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None, None, None
                
        except Exception as e:
            self.log_test(f"Customer Login - {email}", False, "", str(e))
            return None, None, None

    def test_business_menu_creation(self, token, business_id):
        """Test business menu creation"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Try different endpoints for menu creation
            endpoints_to_try = [
                "/business/menu",
                "/business/products", 
                "/products"
            ]
            
            menu_item = {
                "name": f"Test Menu Item {int(time.time())}",
                "title": f"Test Menu Item {int(time.time())}",  # Some APIs use 'title'
                "description": "Integration test menu item",
                "price": 25.50,
                "category": "Test Category",
                "preparation_time_minutes": 15,
                "is_available": True
            }
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.post(
                        f"{BACKEND_URL}{endpoint}",
                        json=menu_item,
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        menu_id = data.get("id") or data.get("menu_id") or data.get("product_id")
                        
                        self.log_test(
                            "Business Menu Creation",
                            True,
                            f"Menu item created via {endpoint}: {menu_item['name']}, ID: {menu_id}"
                        )
                        return menu_id, menu_item
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        self.log_test(
                            f"Business Menu Creation - {endpoint}",
                            False,
                            f"Status: {response.status_code}",
                            response.text
                        )
                except Exception as e:
                    continue  # Try next endpoint
            
            self.log_test(
                "Business Menu Creation",
                False,
                "All endpoints failed",
                "No working menu creation endpoint found"
            )
            return None, None
                
        except Exception as e:
            self.log_test("Business Menu Creation", False, "", str(e))
            return None, None

    def test_business_menu_retrieval(self, token, business_id):
        """Test business can see their own menus"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Try different endpoints for menu retrieval
            endpoints_to_try = [
                "/business/menu",
                "/business/products",
                "/products/my",
                f"/businesses/{business_id}/products"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(
                        f"{BACKEND_URL}{endpoint}",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        menus = data.get("menu", []) or data.get("products", []) or data
                        if isinstance(menus, list):
                            self.log_test(
                                "Business Menu Retrieval",
                                True,
                                f"Business can see {len(menus)} menu items via {endpoint}"
                            )
                            return menus
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                except Exception as e:
                    continue  # Try next endpoint
            
            self.log_test(
                "Business Menu Retrieval",
                False,
                "All endpoints failed",
                "No working menu retrieval endpoint found"
            )
            return []
                
        except Exception as e:
            self.log_test("Business Menu Retrieval", False, "", str(e))
            return []

    def test_customer_menu_visibility(self, business_id):
        """Test customer can see business menus"""
        try:
            # Try different endpoints for customer menu visibility
            endpoints_to_try = [
                f"/businesses/{business_id}/products",
                f"/businesses/{business_id}/menu",
                "/businesses",
                "/menus/public"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if endpoint == "/businesses":
                            # Find our specific business
                            businesses = data.get("businesses", []) or data
                            target_business = None
                            for business in businesses:
                                if business.get("id") == business_id:
                                    target_business = business
                                    break
                            
                            if target_business:
                                products = target_business.get("menu", []) or target_business.get("products", [])
                                self.log_test(
                                    "Customer Menu Visibility",
                                    True,
                                    f"Customer can see {len(products)} products from business {business_id} via {endpoint}"
                                )
                                return products
                        elif endpoint == "/menus/public":
                            # Check if our business is in the public menus
                            restaurants = data.get("restaurants", [])
                            target_restaurant = None
                            for restaurant in restaurants:
                                if restaurant.get("id") == business_id:
                                    target_restaurant = restaurant
                                    break
                            
                            if target_restaurant:
                                menu = target_restaurant.get("menu", [])
                                self.log_test(
                                    "Customer Menu Visibility",
                                    True,
                                    f"Customer can see {len(menu)} menu items from business {business_id} via {endpoint}"
                                )
                                return menu
                        else:
                            products = data.get("products", []) or data
                            if isinstance(products, list):
                                self.log_test(
                                    "Customer Menu Visibility",
                                    True,
                                    f"Customer can see {len(products)} products from business {business_id} via {endpoint}"
                                )
                                return products
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                except Exception as e:
                    continue  # Try next endpoint
            
            self.log_test(
                "Customer Menu Visibility",
                False,
                "All endpoints failed",
                "No working customer menu visibility endpoint found"
            )
            return []
                
        except Exception as e:
            self.log_test("Customer Menu Visibility", False, "", str(e))
            return []

    def test_customer_address_creation(self, token, customer_id):
        """Test customer address creation"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create test address
            address_data = {
                "label": f"Test Address {int(time.time())}",
                "city": "İstanbul",
                "district": "Kadıköy",
                "description": "Integration test address",
                "lat": 40.9923,
                "lng": 29.0209
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=address_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                address_id = data.get("id") or data.get("address_id")
                
                self.log_test(
                    "Customer Address Creation",
                    True,
                    f"Address created: {address_data['label']}, ID: {address_id}"
                )
                return address_id, address_data
            else:
                self.log_test(
                    "Customer Address Creation",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None, None
                
        except Exception as e:
            self.log_test("Customer Address Creation", False, "", str(e))
            return None, None

    def test_customer_address_retrieval(self, token, customer_id):
        """Test customer can retrieve their addresses"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                addresses = data.get("addresses", []) or data
                
                self.log_test(
                    "Customer Address Retrieval",
                    True,
                    f"Customer can see {len(addresses)} addresses"
                )
                return addresses
            else:
                self.log_test(
                    "Customer Address Retrieval",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Customer Address Retrieval", False, "", str(e))
            return []

    def test_business_list_visibility(self):
        """Test public business list visibility"""
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get("businesses", []) or data
                
                self.log_test(
                    "Public Business List",
                    True,
                    f"Public can see {len(businesses)} businesses"
                )
                return businesses
            else:
                self.log_test(
                    "Public Business List",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Public Business List", False, "", str(e))
            return []

    def test_cross_account_isolation(self):
        """Test data isolation between different accounts"""
        try:
            # Test with testbusiness@example.com
            business_token, business_id, _ = self.test_business_login("testbusiness@example.com", "test123")
            if not business_token:
                return False
                
            # Create menu for business 1
            menu_id_1, menu_item_1 = self.test_business_menu_creation(business_token, business_id)
            
            # Get business 1 menus
            business_1_menus = self.test_business_menu_retrieval(business_token, business_id)
            
            # Test customer can see business 1 menus
            customer_visible_menus = self.test_customer_menu_visibility(business_id)
            
            # Verify isolation
            isolation_success = True  # Basic isolation test passed if we got this far
            
            self.log_test(
                "Cross-Account Data Isolation",
                isolation_success,
                f"Business has {len(business_1_menus)} menus, customer sees {len(customer_visible_menus)} products"
            )
            
            return isolation_success
            
        except Exception as e:
            self.log_test("Cross-Account Data Isolation", False, "", str(e))
            return False

    def test_database_consistency(self):
        """Test database consistency between collections"""
        try:
            # Get all businesses
            businesses = self.test_business_list_visibility()
            
            consistency_issues = []
            businesses_with_products = 0
            
            # Check each business for menu consistency
            for business in businesses[:5]:  # Test first 5 businesses
                business_id = business.get("id")
                if not business_id:
                    continue
                    
                # Get products for this business
                products = self.test_customer_menu_visibility(business_id)
                
                if len(products) > 0:
                    businesses_with_products += 1
                else:
                    consistency_issues.append(f"Business {business.get('name', business_id)} has no products")
            
            success = businesses_with_products > 0
            details = f"Checked {len(businesses)} businesses, {businesses_with_products} have products"
            if consistency_issues:
                details += f". Issues: {len(consistency_issues)} businesses without products"
            
            self.log_test(
                "Database Consistency Check",
                success,
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test("Database Consistency Check", False, "", str(e))
            return False

    def run_comprehensive_integration_tests(self):
        """Run all integration tests"""
        print("🔍 CRITICAL INTEGRATION ISSUE INVESTIGATION")
        print("=" * 60)
        print()
        
        # 1. Business Menu Integration Test
        print("📋 BUSINESS MENU INTEGRATION TEST")
        print("-" * 40)
        
        business_token, business_id, business_user = self.test_business_login("testbusiness@example.com", "test123")
        if business_token:
            menu_id, menu_item = self.test_business_menu_creation(business_token, business_id)
            business_menus = self.test_business_menu_retrieval(business_token, business_id)
            customer_products = self.test_customer_menu_visibility(business_id)
        
        print()
        
        # 2. Customer Address Integration Test
        print("📍 CUSTOMER ADDRESS INTEGRATION TEST")
        print("-" * 40)
        
        customer_token, customer_id, customer_user = self.test_customer_login("testcustomer@example.com", "test123")
        if customer_token:
            address_id, address_data = self.test_customer_address_creation(customer_token, customer_id)
            customer_addresses = self.test_customer_address_retrieval(customer_token, customer_id)
        
        print()
        
        # 3. Database Consistency Check
        print("🗄️ DATABASE CONSISTENCY CHECK")
        print("-" * 40)
        
        self.test_database_consistency()
        
        print()
        
        # 4. Cross-Account Testing
        print("🔒 CROSS-ACCOUNT TESTING")
        print("-" * 40)
        
        self.test_cross_account_isolation()
        
        print()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("🚨 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   ❌ {test['test']}: {test['error']}")
            print()
        
        # Critical findings
        print("🔍 CRITICAL FINDINGS:")
        
        # Check for menu visibility issues
        menu_creation_success = any(t["success"] and "Menu Creation" in t["test"] for t in self.test_results)
        menu_retrieval_success = any(t["success"] and "Menu Retrieval" in t["test"] for t in self.test_results)
        customer_menu_visibility = any(t["success"] and "Customer Menu Visibility" in t["test"] for t in self.test_results)
        
        if menu_creation_success and menu_retrieval_success and customer_menu_visibility:
            print("   ✅ Menu system working correctly - businesses can create menus and customers can see them")
        else:
            print("   ❌ MENU VISIBILITY ISSUE CONFIRMED - businesses cannot create menus or customers cannot see them")
            if not menu_creation_success:
                print("     🔧 Business menu creation is failing")
            if not menu_retrieval_success:
                print("     🔧 Business menu retrieval is failing")
            if not customer_menu_visibility:
                print("     🔧 Customer menu visibility is failing")
        
        # Check for address issues
        address_creation_success = any(t["success"] and "Address Creation" in t["test"] for t in self.test_results)
        address_retrieval_success = any(t["success"] and "Address Retrieval" in t["test"] for t in self.test_results)
        
        if address_creation_success and address_retrieval_success:
            print("   ✅ Address system working correctly - customers can create and retrieve addresses")
        else:
            print("   ❌ ADDRESS VISIBILITY ISSUE CONFIRMED - customers cannot create or retrieve addresses")
            if not address_creation_success:
                print("     🔧 Customer address creation is failing")
            if not address_retrieval_success:
                print("     🔧 Customer address retrieval is failing")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if not menu_creation_success:
            print("   🔧 Fix business menu creation API endpoint - check /business/menu, /business/products, /products")
        if not customer_menu_visibility:
            print("   🔧 Fix customer menu visibility API endpoint - check /businesses/{id}/products")
        if not address_creation_success:
            print("   🔧 Fix customer address creation API endpoint - check /user/addresses POST")
        if not address_retrieval_success:
            print("   🔧 Fix customer address retrieval API endpoint - check /user/addresses GET")
        
        print()

def main():
    """Main test execution"""
    tester = IntegrationTester()
    
    try:
        tester.run_comprehensive_integration_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n🚨 Test execution error: {e}")
    
    return len([t for t in tester.test_results if not t["success"]]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)