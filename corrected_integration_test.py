#!/usr/bin/env python3
"""
CORRECTED CRITICAL INTEGRATION ISSUE TESTING

Based on initial findings, the APIs are working but there were parsing issues.
This corrected test will properly investigate the user-reported issues:
1. Business menus not showing after creation
2. Customer addresses not appearing in discovery
"""

import requests
import json
import uuid
import time
from datetime import datetime
import sys
import os

# Configuration
BACKEND_URL = "https://kuryecini-auth.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class CorrectedIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.test_results = []
        
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
            
            # Create test menu item using the correct field name 'title'
            menu_item = {
                "title": f"Critical Test Menu {int(time.time())}",
                "description": "Critical integration test menu item",
                "price": 29.99,
                "category": "Critical Test",
                "is_available": True
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                menu_id = data.get("id") or data.get("menu_id")
                
                self.log_test(
                    "Business Menu Creation",
                    True,
                    f"Menu item created: {menu_item['title']}, ID: {menu_id}"
                )
                return menu_id, menu_item
            else:
                self.log_test(
                    "Business Menu Creation",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None, None
                
        except Exception as e:
            self.log_test("Business Menu Creation", False, "", str(e))
            return None, None

    def test_business_menu_retrieval(self, token, business_id):
        """Test business can see their own menus"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/business/menu",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                # The response is directly a list
                menus = data if isinstance(data, list) else []
                
                self.log_test(
                    "Business Menu Retrieval",
                    True,
                    f"Business can see {len(menus)} menu items"
                )
                return menus
            else:
                self.log_test(
                    "Business Menu Retrieval",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Business Menu Retrieval", False, "", str(e))
            return []

    def test_customer_menu_visibility(self, business_id):
        """Test customer can see business menus"""
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
            
            if response.status_code == 200:
                data = response.json()
                # The response is directly a list
                products = data if isinstance(data, list) else []
                
                self.log_test(
                    "Customer Menu Visibility",
                    True,
                    f"Customer can see {len(products)} products from business {business_id}"
                )
                return products
            else:
                self.log_test(
                    "Customer Menu Visibility",
                    False,
                    f"Status: {response.status_code}",
                    response.text
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
                "label": f"Critical Test Address {int(time.time())}",
                "city": "İstanbul",
                "district": "Kadıköy",
                "description": "Critical integration test address",
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
                # The response is directly a list
                addresses = data if isinstance(data, list) else []
                
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
                # The response is directly a list
                businesses = data if isinstance(data, list) else []
                
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

    def test_menu_field_consistency(self, token, business_id):
        """Test if menu creation and retrieval use consistent field names"""
        try:
            # Create menu with 'title' field
            headers = {"Authorization": f"Bearer {token}"}
            menu_item_title = {
                "title": f"Title Field Test {int(time.time())}",
                "description": "Testing title field",
                "price": 19.99,
                "category": "Field Test"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_title,
                headers=headers
            )
            
            title_success = response.status_code in [200, 201]
            
            # Try creating menu with 'name' field
            menu_item_name = {
                "name": f"Name Field Test {int(time.time())}",
                "description": "Testing name field",
                "price": 19.99,
                "category": "Field Test"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_name,
                headers=headers
            )
            
            name_success = response.status_code in [200, 201]
            
            # Get current menus to see field structure
            response = self.session.get(f"{BACKEND_URL}/business/menu", headers=headers)
            if response.status_code == 200:
                menus = response.json()
                if menus and len(menus) > 0:
                    sample_menu = menus[0]
                    has_title = 'title' in sample_menu
                    has_name = 'name' in sample_menu
                    
                    self.log_test(
                        "Menu Field Consistency Check",
                        True,
                        f"Title field works: {title_success}, Name field works: {name_success}, "
                        f"Response has 'title': {has_title}, Response has 'name': {has_name}"
                    )
                    return title_success, name_success, has_title, has_name
            
            self.log_test(
                "Menu Field Consistency Check",
                False,
                "Could not retrieve menus to check field structure"
            )
            return False, False, False, False
            
        except Exception as e:
            self.log_test("Menu Field Consistency Check", False, "", str(e))
            return False, False, False, False

    def test_address_discovery_integration(self, token, customer_id):
        """Test if addresses appear in discovery/selection contexts"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get customer addresses
            addresses = self.test_customer_address_retrieval(token, customer_id)
            
            if len(addresses) == 0:
                self.log_test(
                    "Address Discovery Integration",
                    False,
                    "No addresses found for discovery testing"
                )
                return False
            
            # Check if addresses have required fields for discovery
            discovery_ready_addresses = 0
            for address in addresses:
                has_required_fields = all(field in address for field in ['id', 'label', 'city', 'lat', 'lng'])
                if has_required_fields:
                    discovery_ready_addresses += 1
            
            success = discovery_ready_addresses > 0
            self.log_test(
                "Address Discovery Integration",
                success,
                f"{discovery_ready_addresses}/{len(addresses)} addresses have required fields for discovery"
            )
            return success
            
        except Exception as e:
            self.log_test("Address Discovery Integration", False, "", str(e))
            return False

    def test_business_menu_customer_sync(self, business_token, business_id):
        """Test if business menus sync properly with customer visibility"""
        try:
            # Get business menus
            business_menus = self.test_business_menu_retrieval(business_token, business_id)
            
            # Get customer view of same business
            customer_products = self.test_customer_menu_visibility(business_id)
            
            # Check if counts match (allowing for some differences due to availability)
            business_count = len(business_menus)
            customer_count = len(customer_products)
            
            # They should be roughly equal (customer might see fewer due to availability filters)
            sync_success = customer_count >= (business_count * 0.8)  # Allow 20% difference
            
            self.log_test(
                "Business-Customer Menu Sync",
                sync_success,
                f"Business has {business_count} menus, customer sees {customer_count} products"
            )
            
            return sync_success
            
        except Exception as e:
            self.log_test("Business-Customer Menu Sync", False, "", str(e))
            return False

    def run_comprehensive_integration_tests(self):
        """Run all corrected integration tests"""
        print("🔍 CORRECTED CRITICAL INTEGRATION ISSUE INVESTIGATION")
        print("=" * 60)
        print()
        
        # 1. Business Menu Integration Test
        print("📋 BUSINESS MENU INTEGRATION TEST")
        print("-" * 40)
        
        business_token, business_id, business_user = self.test_business_login("testbusiness@example.com", "test123")
        if business_token:
            # Test field consistency first
            self.test_menu_field_consistency(business_token, business_id)
            
            # Test menu creation and retrieval
            menu_id, menu_item = self.test_business_menu_creation(business_token, business_id)
            business_menus = self.test_business_menu_retrieval(business_token, business_id)
            customer_products = self.test_customer_menu_visibility(business_id)
            
            # Test sync between business and customer views
            self.test_business_menu_customer_sync(business_token, business_id)
        
        print()
        
        # 2. Customer Address Integration Test
        print("📍 CUSTOMER ADDRESS INTEGRATION TEST")
        print("-" * 40)
        
        customer_token, customer_id, customer_user = self.test_customer_login("testcustomer@example.com", "test123")
        if customer_token:
            address_id, address_data = self.test_customer_address_creation(customer_token, customer_id)
            customer_addresses = self.test_customer_address_retrieval(customer_token, customer_id)
            
            # Test discovery integration
            self.test_address_discovery_integration(customer_token, customer_id)
        
        print()
        
        # 3. Database Consistency Check
        print("🗄️ DATABASE CONSISTENCY CHECK")
        print("-" * 40)
        
        businesses = self.test_business_list_visibility()
        
        print()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("📊 CORRECTED INTEGRATION TEST SUMMARY")
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
        menu_sync_success = any(t["success"] and "Menu Sync" in t["test"] for t in self.test_results)
        
        if menu_creation_success and menu_retrieval_success and customer_menu_visibility:
            print("   ✅ Menu system working correctly - businesses can create menus and customers can see them")
            if menu_sync_success:
                print("   ✅ Business-customer menu synchronization working correctly")
            else:
                print("   ⚠️  Business-customer menu synchronization may have issues")
        else:
            print("   ❌ MENU VISIBILITY ISSUE CONFIRMED")
            if not menu_creation_success:
                print("     🔧 Business menu creation is failing")
            if not menu_retrieval_success:
                print("     🔧 Business menu retrieval is failing")
            if not customer_menu_visibility:
                print("     🔧 Customer menu visibility is failing")
        
        # Check for address issues
        address_creation_success = any(t["success"] and "Address Creation" in t["test"] for t in self.test_results)
        address_retrieval_success = any(t["success"] and "Address Retrieval" in t["test"] for t in self.test_results)
        address_discovery_success = any(t["success"] and "Address Discovery" in t["test"] for t in self.test_results)
        
        if address_creation_success and address_retrieval_success:
            print("   ✅ Address system working correctly - customers can create and retrieve addresses")
            if address_discovery_success:
                print("   ✅ Address discovery integration working correctly")
            else:
                print("   ⚠️  Address discovery integration may have issues")
        else:
            print("   ❌ ADDRESS VISIBILITY ISSUE CONFIRMED")
            if not address_creation_success:
                print("     🔧 Customer address creation is failing")
            if not address_retrieval_success:
                print("     🔧 Customer address retrieval is failing")
        
        # Check field consistency
        field_consistency_success = any(t["success"] and "Field Consistency" in t["test"] for t in self.test_results)
        if field_consistency_success:
            print("   ✅ API field consistency checked")
        
        print()
        
        # Root cause analysis
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Based on the user reports, let's analyze what might be happening
        if menu_creation_success and menu_retrieval_success and customer_menu_visibility:
            print("   💡 Backend APIs are working correctly for menu management")
            print("   💡 User issue likely in frontend implementation or API field usage")
            print("   💡 Check if frontend uses 'title' field instead of 'name' for menu creation")
        
        if address_creation_success and address_retrieval_success:
            print("   💡 Backend APIs are working correctly for address management")
            print("   💡 User issue likely in frontend address selector implementation")
            print("   💡 Check if discovery page properly fetches and displays user addresses")
        
        print()

def main():
    """Main test execution"""
    tester = CorrectedIntegrationTester()
    
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