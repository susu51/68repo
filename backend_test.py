#!/usr/bin/env python3
"""
DeliverTR Backend API Testing Suite - Core Business Flow
Tests all API endpoints for the Turkish delivery platform MVP core business flow:
- Product Management (Business creates products with photos)
- Order Creation (Customer creates orders with multiple items)
- Order Status Management (CREATED→ASSIGNED→ON_ROUTE→DELIVERED)
- Admin Authentication (password "6851")
- Admin Management (users, products, orders)
- Commission Calculation (3%)
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class DeliverTRAPITester:
    def __init__(self, base_url="https://quick-courier-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.access_token = None
        self.admin_token = None
        self.business_token = None
        self.customer_token = None
        self.courier_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.business_email = f"business_{uuid.uuid4().hex[:8]}@test.com"
        self.customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"
        self.courier_email = f"courier_{uuid.uuid4().hex[:8]}@test.com"
        self.test_password = "TestPass123!"
        
        # Store created entities for testing
        self.created_products = []
        self.created_orders = []
        self.business_id = None
        self.customer_id = None
        self.courier_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use default access_token
        auth_token = token or self.access_token
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    response_text = response.text
                    print(f"   Response: {response_text}")
                    self.log_test(name, True)
                    return True, response_text
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    # ===== CORE BUSINESS FLOW TESTS =====
    
    def test_admin_authentication(self):
        """Test admin authentication with password '6851'"""
        success, response = self.run_test(
            "Admin Authentication",
            "POST",
            "auth/admin",
            200,
            data={"password": "6851"}
        )
        
        if success and response.get('access_token'):
            self.admin_token = response['access_token']
            print(f"   Admin token stored: {self.admin_token[:20]}...")
        
        return success

    def test_admin_authentication_wrong_password(self):
        """Test admin authentication with wrong password"""
        return self.run_test(
            "Admin Authentication - Wrong Password",
            "POST",
            "auth/admin",
            401,
            data={"password": "wrong_password"}
        )

    def test_business_registration(self):
        """Test business registration"""
        business_data = {
            "email": self.business_email,
            "password": self.test_password,
            "business_name": "Test Restaurant Istanbul",
            "tax_number": "1234567890",
            "address": "Kadıköy, İstanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant for API testing"
        }
        
        success, response = self.run_test(
            "Business Registration",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success and response.get('access_token'):
            self.business_token = response['access_token']
            self.business_id = response.get('user_data', {}).get('id')
            print(f"   Business token stored: {self.business_token[:20]}...")
            print(f"   Business ID: {self.business_id}")
        
        return success

    def test_customer_registration(self):
        """Test customer registration"""
        customer_data = {
            "email": self.customer_email,
            "password": self.test_password,
            "first_name": "Ahmet",
            "last_name": "Yılmaz",
            "city": "İstanbul"
        }
        
        success, response = self.run_test(
            "Customer Registration",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        if success and response.get('access_token'):
            self.customer_token = response['access_token']
            self.customer_id = response.get('user_data', {}).get('id')
            print(f"   Customer token stored: {self.customer_token[:20]}...")
            print(f"   Customer ID: {self.customer_id}")
        
        return success

    def test_courier_registration(self):
        """Test courier registration"""
        courier_data = {
            "email": self.courier_email,
            "password": self.test_password,
            "first_name": "Mehmet",
            "last_name": "Kurye",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "vehicle_model": "Honda PCX 150",
            "license_class": "A2",
            "license_number": "34ABC123",
            "city": "İstanbul"
        }
        
        success, response = self.run_test(
            "Courier Registration",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if success and response.get('access_token'):
            self.courier_token = response['access_token']
            self.courier_id = response.get('user_data', {}).get('id')
            print(f"   Courier token stored: {self.courier_token[:20]}...")
            print(f"   Courier ID: {self.courier_id}")
        
        return success

    def test_business_login(self):
        """Test business login"""
        login_data = {
            "email": self.business_email,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Business Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response.get('access_token'):
            self.business_token = response['access_token']
            print(f"   Business login successful, token updated")
        
        return success

    def test_customer_login(self):
        """Test customer login"""
        login_data = {
            "email": self.customer_email,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Customer Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response.get('access_token'):
            self.customer_token = response['access_token']
            print(f"   Customer login successful, token updated")
        
        return success

    def test_product_creation(self):
        """Test product creation by business"""
        if not self.business_token:
            self.log_test("Product Creation", False, "No business token available")
            return False
        
        product_data = {
            "name": "İskender Kebap",
            "description": "Geleneksel İskender kebap, tereyağı ve yoğurt ile",
            "price": 45.50,
            "category": "ana_yemek",
            "preparation_time_minutes": 25,
            "photo_url": "/uploads/iskender-kebap.jpg",
            "is_available": True
        }
        
        success, response = self.run_test(
            "Product Creation",
            "POST",
            "products",
            200,
            data=product_data,
            token=self.business_token
        )
        
        if success and response.get('id'):
            self.created_products.append(response)
            print(f"   Product created with ID: {response['id']}")
        
        return success

    def test_product_creation_multiple(self):
        """Test creating multiple products"""
        if not self.business_token:
            self.log_test("Multiple Product Creation", False, "No business token available")
            return False
        
        products = [
            {
                "name": "Adana Kebap",
                "description": "Acılı Adana kebap, bulgur pilavı ile",
                "price": 42.00,
                "category": "ana_yemek",
                "preparation_time_minutes": 20,
                "is_available": True
            },
            {
                "name": "Baklava",
                "description": "Antep fıstıklı baklava, 4 dilim",
                "price": 18.50,
                "category": "tatli",
                "preparation_time_minutes": 5,
                "is_available": True
            },
            {
                "name": "Ayran",
                "description": "Ev yapımı ayran, 250ml",
                "price": 5.00,
                "category": "icecek",
                "preparation_time_minutes": 2,
                "is_available": True
            }
        ]
        
        all_success = True
        for i, product_data in enumerate(products):
            success, response = self.run_test(
                f"Product Creation {i+2}",
                "POST",
                "products",
                200,
                data=product_data,
                token=self.business_token
            )
            
            if success and response.get('id'):
                self.created_products.append(response)
                print(f"   Product {i+2} created with ID: {response['id']}")
            else:
                all_success = False
        
        return all_success

    def test_get_products(self):
        """Test getting all available products"""
        return self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )

    def test_get_business_products(self):
        """Test getting products for current business"""
        if not self.business_token:
            self.log_test("Get Business Products", False, "No business token available")
            return False
        
        return self.run_test(
            "Get Business Products",
            "GET",
            "products/my",
            200,
            token=self.business_token
        )

    def test_order_creation(self):
        """Test order creation by customer"""
        if not self.customer_token or not self.created_products:
            self.log_test("Order Creation", False, "No customer token or products available")
            return False
        
        # Use created products for order
        order_items = []
        total_amount = 0
        
        for product in self.created_products[:3]:  # Use first 3 products
            quantity = 2 if product['name'] == 'İskender Kebap' else 1
            subtotal = product['price'] * quantity
            
            order_items.append({
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": quantity,
                "subtotal": subtotal
            })
            total_amount += subtotal
        
        order_data = {
            "delivery_address": "Bağdat Caddesi No:123, Kadıköy, İstanbul",
            "delivery_lat": 40.9876,
            "delivery_lng": 29.0234,
            "items": order_items,
            "total_amount": total_amount,
            "notes": "Kapıda ödeme, 2. kat"
        }
        
        success, response = self.run_test(
            "Order Creation",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if success and response.get('id'):
            self.created_orders.append(response)
            print(f"   Order created with ID: {response['id']}")
            print(f"   Total amount: {response.get('total_amount')}")
            print(f"   Commission (3%): {response.get('commission_amount')}")
            
            # Verify commission calculation (3%)
            expected_commission = total_amount * 0.03
            actual_commission = response.get('commission_amount', 0)
            if abs(expected_commission - actual_commission) < 0.01:
                print(f"   ✅ Commission calculation correct: {actual_commission}")
            else:
                print(f"   ❌ Commission calculation incorrect: expected {expected_commission}, got {actual_commission}")
        
        return success

    def test_order_status_flow(self):
        """Test complete order status flow: CREATED → ASSIGNED → ON_ROUTE → DELIVERED"""
        if not self.created_orders or not self.courier_token:
            self.log_test("Order Status Flow", False, "No orders or courier token available")
            return False
        
        order_id = self.created_orders[0]['id']
        statuses = ["assigned", "on_route", "delivered"]
        
        all_success = True
        for status in statuses:
            success, response = self.run_test(
                f"Order Status Update - {status.upper()}",
                "PATCH",
                f"orders/{order_id}/status",
                200,
                data={"new_status": status},
                token=self.courier_token
            )
            
            if not success:
                all_success = False
            else:
                print(f"   Order status updated to: {status}")
        
        return all_success

    def test_get_orders_customer(self):
        """Test getting orders for customer"""
        if not self.customer_token:
            self.log_test("Get Customer Orders", False, "No customer token available")
            return False
        
        return self.run_test(
            "Get Customer Orders",
            "GET",
            "orders",
            200,
            token=self.customer_token
        )

    def test_get_orders_business(self):
        """Test getting orders for business"""
        if not self.business_token:
            self.log_test("Get Business Orders", False, "No business token available")
            return False
        
        return self.run_test(
            "Get Business Orders",
            "GET",
            "orders",
            200,
            token=self.business_token
        )

    def test_admin_get_all_users(self):
        """Test admin getting all users"""
        if not self.admin_token:
            self.log_test("Admin Get All Users", False, "No admin token available")
            return False
        
        return self.run_test(
            "Admin Get All Users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )

    def test_admin_get_all_products(self):
        """Test admin getting all products"""
        if not self.admin_token:
            self.log_test("Admin Get All Products", False, "No admin token available")
            return False
        
        return self.run_test(
            "Admin Get All Products",
            "GET",
            "admin/products",
            200,
            token=self.admin_token
        )

    def test_admin_get_all_orders(self):
        """Test admin getting all orders"""
        if not self.admin_token:
            self.log_test("Admin Get All Orders", False, "No admin token available")
            return False
        
        return self.run_test(
            "Admin Get All Orders",
            "GET",
            "admin/orders",
            200,
            token=self.admin_token
        )

    def test_role_based_access_control(self):
        """Test role-based access control"""
        all_success = True
        
        # Test customer trying to create product (should fail)
        if self.customer_token:
            success, _ = self.run_test(
                "RBAC - Customer Create Product (Should Fail)",
                "POST",
                "products",
                403,
                data={
                    "name": "Unauthorized Product",
                    "description": "This should fail",
                    "price": 10.0,
                    "category": "test"
                },
                token=self.customer_token
            )
            if not success:
                all_success = False
        
        # Test business trying to access admin endpoint (should fail)
        if self.business_token:
            success, _ = self.run_test(
                "RBAC - Business Access Admin (Should Fail)",
                "GET",
                "admin/users",
                403,
                token=self.business_token
            )
            if not success:
                all_success = False
        
        return all_success

    def test_file_upload(self):
        """Test file upload functionality"""
        # This is a basic test - in real scenario we'd upload actual files
        # For now, we'll test the endpoint exists and returns proper error for missing file
        success, _ = self.run_test(
            "File Upload Endpoint",
            "POST",
            "upload",
            422,  # Expecting validation error for missing file
            token=self.business_token
        )
        
        return success

    def run_all_tests(self):
        """Run all backend tests for DeliverTR MVP Core Business Flow"""
        print("🚀 Starting DeliverTR Backend API Tests - Core Business Flow")
        print("=" * 70)
        
        # Test 1: Admin Authentication
        print("\n📋 PHASE 1: ADMIN AUTHENTICATION")
        self.test_admin_authentication()
        self.test_admin_authentication_wrong_password()
        
        # Test 2: User Registration
        print("\n📋 PHASE 2: USER REGISTRATION")
        self.test_business_registration()
        self.test_customer_registration()
        self.test_courier_registration()
        
        # Test 3: User Login
        print("\n📋 PHASE 3: USER LOGIN")
        self.test_business_login()
        self.test_customer_login()
        
        # Test 4: Product Management Flow
        print("\n📋 PHASE 4: PRODUCT MANAGEMENT FLOW")
        self.test_product_creation()
        self.test_product_creation_multiple()
        self.test_get_products()
        self.test_get_business_products()
        
        # Test 5: Order Creation Flow
        print("\n📋 PHASE 5: ORDER CREATION FLOW")
        self.test_order_creation()
        self.test_get_orders_customer()
        self.test_get_orders_business()
        
        # Test 6: Order Status Management Flow
        print("\n📋 PHASE 6: ORDER STATUS MANAGEMENT FLOW")
        self.test_order_status_flow()
        
        # Test 7: Admin Management
        print("\n📋 PHASE 7: ADMIN MANAGEMENT")
        self.test_admin_get_all_users()
        self.test_admin_get_all_products()
        self.test_admin_get_all_orders()
        
        # Test 8: Role-Based Access Control
        print("\n📋 PHASE 8: ROLE-BASED ACCESS CONTROL")
        self.test_role_based_access_control()
        
        # Test 9: File Upload
        print("\n📋 PHASE 9: FILE HANDLING")
        self.test_file_upload()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY - DeliverTR MVP Core Business Flow")
        print("=" * 70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests details
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Print successful core flow tests
        core_flow_tests = [
            "Admin Authentication",
            "Business Registration", 
            "Customer Registration",
            "Product Creation",
            "Order Creation",
            "Order Status Update - ASSIGNED",
            "Order Status Update - ON_ROUTE", 
            "Order Status Update - DELIVERED",
            "Admin Get All Users",
            "Admin Get All Products",
            "Admin Get All Orders"
        ]
        
        successful_core_tests = [test for test in self.test_results 
                               if test['success'] and test['test'] in core_flow_tests]
        
        print(f"\n✅ CORE BUSINESS FLOW TESTS PASSED: {len(successful_core_tests)}/{len(core_flow_tests)}")
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100,
                    "timestamp": datetime.now().isoformat(),
                    "test_type": "delivertr_mvp_core_business_flow",
                    "core_flow_success": len(successful_core_tests) == len(core_flow_tests)
                },
                "test_results": self.test_results,
                "created_entities": {
                    "business_id": self.business_id,
                    "customer_id": self.customer_id,
                    "courier_id": self.courier_id,
                    "products": [p.get('id') for p in self.created_products],
                    "orders": [o.get('id') for o in self.created_orders]
                }
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = DeliverTRAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())