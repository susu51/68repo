#!/usr/bin/env python3
"""
Business Dashboard API Testing Suite
Tests specific business dashboard API endpoints with authentication:
- Business login with testrestoran@example.com/test123
- GET /products/my endpoint - business products
- POST /products endpoint - create new products
- GET /orders endpoint - business orders
- PATCH /orders/{id}/status endpoint - update order status
- Authorization headers verification
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class BusinessDashboardTester:
    def __init__(self, base_url="https://kurye-platform.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.business_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Business credentials from review request
        self.business_email = "testrestoran@example.com"
        self.business_password = "test123"
        
        # Store created entities for testing
        self.created_products = []
        self.created_orders = []
        self.business_id = None

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
        
        # Use specific token if provided, otherwise use business_token
        auth_token = token or self.business_token
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if auth_token:
            print(f"   Auth: Bearer {auth_token[:20]}...")
        
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

    def test_business_login(self):
        """Test business login with testrestoran@example.com/test123"""
        login_data = {
            "email": self.business_email,
            "password": self.business_password
        }
        
        success, response = self.run_test(
            "Business Login - testrestoran@example.com",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response.get('access_token'):
            self.business_token = response['access_token']
            user_data = response.get('user_data', {})
            self.business_id = user_data.get('id')
            print(f"   ✅ Business token stored: {self.business_token[:20]}...")
            print(f"   ✅ Business ID: {self.business_id}")
            print(f"   ✅ User type: {response.get('user_type')}")
            print(f"   ✅ Business name: {user_data.get('business_name', 'N/A')}")
            
            # Verify it's a business account
            if response.get('user_type') != 'business':
                self.log_test("Business Login - testrestoran@example.com", False, f"Expected user_type 'business', got '{response.get('user_type')}'")
                return False
        
        return success

    def test_business_login_wrong_password(self):
        """Test business login with wrong password"""
        login_data = {
            "email": self.business_email,
            "password": "wrong_password"
        }
        
        return self.run_test(
            "Business Login - Wrong Password",
            "POST",
            "auth/login",
            401,
            data=login_data
        )[0]

    def test_get_my_products(self):
        """Test GET /products/my endpoint - should return business products"""
        if not self.business_token:
            self.log_test("GET /products/my", False, "No business token available")
            return False
        
        success, response = self.run_test(
            "GET /products/my - Business Products",
            "GET",
            "products/my",
            200,
            token=self.business_token
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Found {len(response)} products for business")
                for i, product in enumerate(response[:3]):  # Show first 3 products
                    print(f"   📦 Product {i+1}: {product.get('name', 'N/A')} - ₺{product.get('price', 0)}")
                    if product.get('business_id') != self.business_id:
                        print(f"   ⚠️  Product business_id mismatch: {product.get('business_id')} != {self.business_id}")
            else:
                print(f"   ⚠️  Expected list response, got: {type(response)}")
        
        return success

    def test_get_my_products_without_auth(self):
        """Test GET /products/my without authentication - should fail"""
        return self.run_test(
            "GET /products/my - No Auth (Should Fail)",
            "GET",
            "products/my",
            401
        )[0]

    def test_create_product(self):
        """Test POST /products endpoint - should create new products for business"""
        if not self.business_token:
            self.log_test("POST /products - Create Product", False, "No business token available")
            return False
        
        product_data = {
            "name": "Test Döner Kebap",
            "description": "Lezzetli döner kebap, pilav ve salata ile servis edilir",
            "price": 35.50,
            "category": "ana_yemek",
            "preparation_time_minutes": 15,
            "photo_url": "/uploads/doner-kebap.jpg",
            "is_available": True
        }
        
        success, response = self.run_test(
            "POST /products - Create Product",
            "POST",
            "products",
            200,
            data=product_data,
            token=self.business_token
        )
        
        if success and response.get('id'):
            self.created_products.append(response)
            print(f"   ✅ Product created with ID: {response['id']}")
            print(f"   ✅ Product name: {response.get('name')}")
            print(f"   ✅ Product price: ₺{response.get('price')}")
            print(f"   ✅ Business ID: {response.get('business_id')}")
            
            # Verify business_id matches
            if response.get('business_id') != self.business_id:
                print(f"   ⚠️  Business ID mismatch: {response.get('business_id')} != {self.business_id}")
        
        return success

    def test_create_multiple_products(self):
        """Test creating multiple products"""
        if not self.business_token:
            self.log_test("Create Multiple Products", False, "No business token available")
            return False
        
        products = [
            {
                "name": "Lahmacun",
                "description": "İnce hamur üzerine kıymalı lahmacun",
                "price": 12.00,
                "category": "ana_yemek",
                "preparation_time_minutes": 10,
                "is_available": True
            },
            {
                "name": "Künefe",
                "description": "Antep usulü künefe, kaymak ile",
                "price": 25.00,
                "category": "tatli",
                "preparation_time_minutes": 8,
                "is_available": True
            },
            {
                "name": "Şalgam Suyu",
                "description": "Geleneksel şalgam suyu, 250ml",
                "price": 8.00,
                "category": "icecek",
                "preparation_time_minutes": 1,
                "is_available": True
            }
        ]
        
        all_success = True
        for i, product_data in enumerate(products):
            success, response = self.run_test(
                f"Create Product {i+2} - {product_data['name']}",
                "POST",
                "products",
                200,
                data=product_data,
                token=self.business_token
            )
            
            if success and response.get('id'):
                self.created_products.append(response)
                print(f"   ✅ Product {i+2} created: {response.get('name')} - ₺{response.get('price')}")
            else:
                all_success = False
        
        return all_success

    def test_create_product_without_auth(self):
        """Test POST /products without authentication - should fail"""
        product_data = {
            "name": "Unauthorized Product",
            "description": "This should fail",
            "price": 10.0,
            "category": "test"
        }
        
        return self.run_test(
            "POST /products - No Auth (Should Fail)",
            "POST",
            "products",
            401,
            data=product_data
        )[0]

    def test_get_orders(self):
        """Test GET /orders endpoint - should return orders for business"""
        if not self.business_token:
            self.log_test("GET /orders - Business Orders", False, "No business token available")
            return False
        
        success, response = self.run_test(
            "GET /orders - Business Orders",
            "GET",
            "orders",
            200,
            token=self.business_token
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✅ Found {len(response)} orders for business")
                for i, order in enumerate(response[:3]):  # Show first 3 orders
                    print(f"   📋 Order {i+1}: ID={order.get('id', 'N/A')[:8]}... Status={order.get('status', 'N/A')} Amount=₺{order.get('total_amount', 0)}")
                    if order.get('business_id') != self.business_id:
                        print(f"   ⚠️  Order business_id mismatch: {order.get('business_id')} != {self.business_id}")
            else:
                print(f"   ⚠️  Expected list response, got: {type(response)}")
        
        return success

    def test_get_orders_without_auth(self):
        """Test GET /orders without authentication - should fail"""
        return self.run_test(
            "GET /orders - No Auth (Should Fail)",
            "GET",
            "orders",
            401
        )[0]

    def test_update_order_status(self):
        """Test PATCH /orders/{id}/status endpoint - should update order status"""
        if not self.business_token:
            self.log_test("PATCH /orders/{id}/status", False, "No business token available")
            return False
        
        # First, get orders to find one to update
        success, orders = self.run_test(
            "Get Orders for Status Update Test",
            "GET",
            "orders",
            200,
            token=self.business_token
        )
        
        if not success or not isinstance(orders, list) or len(orders) == 0:
            print("   ⚠️  No orders found to test status update")
            # Create a test order first (this would require customer token, so we'll simulate)
            self.log_test("PATCH /orders/{id}/status", False, "No orders available for status update test")
            return False
        
        # Find an order that can be updated
        test_order = None
        for order in orders:
            if order.get('status') in ['created', 'assigned']:
                test_order = order
                break
        
        if not test_order:
            print("   ⚠️  No orders with updatable status found")
            self.log_test("PATCH /orders/{id}/status", False, "No orders with updatable status")
            return False
        
        order_id = test_order.get('id')
        current_status = test_order.get('status')
        
        # Determine next status
        next_status = "assigned" if current_status == "created" else "on_route"
        
        print(f"   📋 Testing status update: {current_status} → {next_status}")
        
        success, response = self.run_test(
            f"PATCH /orders/{order_id[:8]}.../status - {current_status} → {next_status}",
            "PATCH",
            f"orders/{order_id}/status",
            200,
            data={"status": next_status},
            token=self.business_token
        )
        
        if success:
            print(f"   ✅ Order status updated successfully")
            print(f"   ✅ Response: {response}")
        
        return success

    def test_authorization_headers(self):
        """Test that authorization headers are working properly for business endpoints"""
        if not self.business_token:
            self.log_test("Authorization Headers Test", False, "No business token available")
            return False
        
        print("\n🔐 Testing Authorization Headers...")
        
        # Test 1: Valid token
        success1, _ = self.run_test(
            "Valid Authorization Header",
            "GET",
            "products/my",
            200,
            token=self.business_token
        )
        
        # Test 2: Invalid token
        success2, _ = self.run_test(
            "Invalid Authorization Header",
            "GET",
            "products/my",
            401,
            token="invalid_token_12345"
        )
        
        # Test 3: Missing Authorization header
        success3, _ = self.run_test(
            "Missing Authorization Header",
            "GET",
            "products/my",
            401
        )
        
        # Test 4: Malformed Authorization header
        success4 = self.run_test(
            "Malformed Authorization Header",
            "GET",
            "products/my",
            401,
            headers={"Authorization": "InvalidFormat token123"}
        )[0]
        
        all_success = success1 and success2 and success3 and success4
        
        if all_success:
            print("   ✅ All authorization header tests passed")
        else:
            print("   ❌ Some authorization header tests failed")
        
        return all_success

    def test_business_user_authentication_flow(self):
        """Test complete business user authentication flow"""
        print("\n🔄 Testing Complete Business Authentication Flow...")
        
        # Step 1: Login
        login_success = self.test_business_login()
        if not login_success:
            self.log_test("Business Authentication Flow", False, "Login failed")
            return False
        
        print("   ✅ Step 1: Business login successful")
        
        # Step 2: Access protected endpoint
        success, response = self.run_test(
            "Access Protected Endpoint After Login",
            "GET",
            "products/my",
            200,
            token=self.business_token
        )
        
        if not success:
            self.log_test("Business Authentication Flow", False, "Failed to access protected endpoint")
            return False
        
        print("   ✅ Step 2: Protected endpoint access successful")
        
        # Step 3: Verify business-specific data
        if isinstance(response, list):
            for product in response:
                if product.get('business_id') != self.business_id:
                    self.log_test("Business Authentication Flow", False, "Product business_id mismatch")
                    return False
        
        print("   ✅ Step 3: Business-specific data verification successful")
        
        self.log_test("Business Authentication Flow", True, "Complete authentication flow successful")
        return True

    def run_all_tests(self):
        """Run all business dashboard tests"""
        print("🚀 Starting Business Dashboard API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print(f"📧 Business Email: {self.business_email}")
        print("=" * 80)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_business_login()
        self.test_business_login_wrong_password()
        
        # Products Tests
        print("\n📋 PRODUCTS MANAGEMENT TESTS")
        print("-" * 40)
        self.test_get_my_products()
        self.test_get_my_products_without_auth()
        self.test_create_product()
        self.test_create_multiple_products()
        self.test_create_product_without_auth()
        
        # Orders Tests
        print("\n📋 ORDERS MANAGEMENT TESTS")
        print("-" * 40)
        self.test_get_orders()
        self.test_get_orders_without_auth()
        self.test_update_order_status()
        
        # Authorization Tests
        print("\n📋 AUTHORIZATION TESTS")
        print("-" * 40)
        self.test_authorization_headers()
        
        # Complete Flow Tests
        print("\n📋 COMPLETE FLOW TESTS")
        print("-" * 40)
        self.test_business_user_authentication_flow()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 BUSINESS DASHBOARD API TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            return False

if __name__ == "__main__":
    tester = BusinessDashboardTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)