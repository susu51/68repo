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
    def __init__(self, base_url="https://rapid-delivery-13.preview.emergentagent.com"):
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
            # Send status as query parameter
            success, response = self.run_test(
                f"Order Status Update - {status.upper()}",
                "PATCH",
                f"orders/{order_id}/status?new_status={status}",
                200,
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

    # ===== KYC MANAGEMENT SYSTEM TESTS =====
    
    def test_kyc_get_couriers(self):
        """Test GET /admin/couriers/kyc - Get all couriers with KYC data"""
        if not self.admin_token:
            self.log_test("KYC Get Couriers", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "KYC Get Couriers",
            "GET",
            "admin/couriers/kyc",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} couriers for KYC review")
            # Check if our test courier is in the list
            test_courier_found = False
            for courier in response:
                if courier.get('email') == self.courier_email:
                    test_courier_found = True
                    print(f"   Test courier found with KYC status: {courier.get('kyc_status', 'unknown')}")
                    break
            
            if not test_courier_found:
                print(f"   Warning: Test courier {self.courier_email} not found in KYC list")
        
        return success

    def test_kyc_approve_courier(self):
        """Test PATCH /admin/couriers/{courier_id}/kyc - Approve courier KYC"""
        if not self.admin_token or not self.courier_id:
            self.log_test("KYC Approve Courier", False, "No admin token or courier ID available")
            return False
        
        # Test approval without notes
        success, response = self.run_test(
            "KYC Approve Courier",
            "PATCH",
            f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
            200,
            token=self.admin_token
        )
        
        if success:
            print(f"   Courier {self.courier_id} KYC approved successfully")
        
        return success

    def test_kyc_reject_courier_with_notes(self):
        """Test PATCH /admin/couriers/{courier_id}/kyc - Reject courier KYC with notes"""
        if not self.admin_token or not self.courier_id:
            self.log_test("KYC Reject Courier with Notes", False, "No admin token or courier ID available")
            return False
        
        # First, let's create another courier for rejection test
        rejection_courier_email = f"reject_courier_{uuid.uuid4().hex[:8]}@test.com"
        courier_data = {
            "email": rejection_courier_email,
            "password": self.test_password,
            "first_name": "Rejected",
            "last_name": "Courier",
            "iban": "TR330006100519786457841327",
            "vehicle_type": "bisiklet",
            "vehicle_model": "Mountain Bike",
            "license_class": "B",
            "license_number": "34XYZ789",
            "city": "Ankara"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Courier for Rejection Test",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if not reg_success:
            self.log_test("KYC Reject Courier with Notes", False, "Failed to create test courier for rejection")
            return False
        
        reject_courier_id = reg_response.get('user_data', {}).get('id')
        if not reject_courier_id:
            self.log_test("KYC Reject Courier with Notes", False, "No courier ID from registration")
            return False
        
        # Test rejection with notes in request body
        rejection_notes = "Belge kalitesi yetersiz, ehliyet fotoğrafı bulanık. Lütfen yeniden yükleyin."
        success, response = self.run_test(
            "KYC Reject Courier with Notes",
            "PATCH",
            f"admin/couriers/{reject_courier_id}/kyc?kyc_status=rejected",
            200,
            data={"notes": rejection_notes},
            token=self.admin_token
        )
        
        if success:
            print(f"   Courier {reject_courier_id} KYC rejected with notes")
        
        return success

    def test_kyc_status_update_flow(self):
        """Test complete KYC status update flow: pending → approved → rejected"""
        if not self.admin_token:
            self.log_test("KYC Status Update Flow", False, "No admin token available")
            return False
        
        # Create a new courier for this test
        flow_courier_email = f"flow_courier_{uuid.uuid4().hex[:8]}@test.com"
        courier_data = {
            "email": flow_courier_email,
            "password": self.test_password,
            "first_name": "Flow",
            "last_name": "Test",
            "iban": "TR330006100519786457841328",
            "vehicle_type": "araba",
            "vehicle_model": "Toyota Corolla",
            "license_class": "B",
            "license_number": "06ABC456",
            "city": "Ankara"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Courier for Flow Test",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if not reg_success:
            self.log_test("KYC Status Update Flow", False, "Failed to create test courier")
            return False
        
        flow_courier_id = reg_response.get('user_data', {}).get('id')
        if not flow_courier_id:
            self.log_test("KYC Status Update Flow", False, "No courier ID from registration")
            return False
        
        # Test flow: pending → approved → rejected
        statuses = [
            ("approved", "Belgeler onaylandı"),
            ("rejected", "Yeniden değerlendirme sonucu red"),
            ("pending", "Tekrar inceleme için beklemede")
        ]
        
        all_success = True
        for kyc_status, notes in statuses:
            success, response = self.run_test(
                f"KYC Status Update - {kyc_status.upper()}",
                "PATCH",
                f"admin/couriers/{flow_courier_id}/kyc?kyc_status={kyc_status}",
                200,
                data={"notes": notes},
                token=self.admin_token
            )
            
            if not success:
                all_success = False
            else:
                print(f"   KYC status updated to: {kyc_status}")
        
        return all_success

    def test_kyc_admin_authentication_required(self):
        """Test that KYC endpoints require admin authentication"""
        all_success = True
        
        # Test without token
        success, _ = self.run_test(
            "KYC Get Couriers - No Auth (Should Fail)",
            "GET",
            "admin/couriers/kyc",
            401
        )
        if not success:
            all_success = False
        
        # Test with business token (should fail)
        if self.business_token:
            success, _ = self.run_test(
                "KYC Get Couriers - Business Token (Should Fail)",
                "GET",
                "admin/couriers/kyc",
                403,
                token=self.business_token
            )
            if not success:
                all_success = False
        
        # Test with customer token (should fail)
        if self.customer_token:
            success, _ = self.run_test(
                "KYC Get Couriers - Customer Token (Should Fail)",
                "GET",
                "admin/couriers/kyc",
                403,
                token=self.customer_token
            )
            if not success:
                all_success = False
        
        return all_success

    def test_kyc_error_scenarios(self):
        """Test KYC error scenarios"""
        if not self.admin_token:
            self.log_test("KYC Error Scenarios", False, "No admin token available")
            return False
        
        all_success = True
        
        # Test with invalid courier ID
        success, _ = self.run_test(
            "KYC Update - Invalid Courier ID",
            "PATCH",
            "admin/couriers/invalid-courier-id/kyc?kyc_status=approved",
            404,
            token=self.admin_token
        )
        if not success:
            all_success = False
        
        # Test with invalid KYC status
        if self.courier_id:
            success, _ = self.run_test(
                "KYC Update - Invalid Status",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=invalid_status",
                400,
                token=self.admin_token
            )
            if not success:
                all_success = False
        
        # Test with malformed request body
        if self.courier_id:
            success, _ = self.run_test(
                "KYC Update - Malformed Body",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,  # Should still work, notes are optional
                data={"invalid_field": "test"},
                token=self.admin_token
            )
            if not success:
                all_success = False
        
        return all_success

    def test_kyc_notes_handling(self):
        """Test KYC notes field handling"""
        if not self.admin_token:
            self.log_test("KYC Notes Handling", False, "No admin token available")
            return False
        
        # Create a courier for notes testing
        notes_courier_email = f"notes_courier_{uuid.uuid4().hex[:8]}@test.com"
        courier_data = {
            "email": notes_courier_email,
            "password": self.test_password,
            "first_name": "Notes",
            "last_name": "Test",
            "iban": "TR330006100519786457841329",
            "vehicle_type": "elektrikli_motor",
            "vehicle_model": "Electric Scooter",
            "license_class": "A1",
            "license_number": "34ELE123",
            "city": "İzmir"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Courier for Notes Test",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if not reg_success:
            self.log_test("KYC Notes Handling", False, "Failed to create test courier")
            return False
        
        notes_courier_id = reg_response.get('user_data', {}).get('id')
        if not notes_courier_id:
            self.log_test("KYC Notes Handling", False, "No courier ID from registration")
            return False
        
        all_success = True
        
        # Test with notes
        success, _ = self.run_test(
            "KYC Update - With Notes",
            "PATCH",
            f"admin/couriers/{notes_courier_id}/kyc?kyc_status=rejected",
            200,
            data={"notes": "Ehliyet süresi geçmiş, güncel ehliyet gerekli"},
            token=self.admin_token
        )
        if not success:
            all_success = False
        
        # Test without notes (approval)
        success, _ = self.run_test(
            "KYC Update - Without Notes",
            "PATCH",
            f"admin/couriers/{notes_courier_id}/kyc?kyc_status=approved",
            200,
            token=self.admin_token
        )
        if not success:
            all_success = False
        
        # Test with empty notes
        success, _ = self.run_test(
            "KYC Update - Empty Notes",
            "PATCH",
            f"admin/couriers/{notes_courier_id}/kyc?kyc_status=pending",
            200,
            data={"notes": ""},
            token=self.admin_token
        )
        if not success:
            all_success = False
        
        return all_success

    # ===== ORDER VISIBILITY BUG TESTS =====
    
    def test_courier_nearby_orders_access_control(self):
        """Test that only KYC-approved couriers can access nearby orders"""
        if not self.courier_token:
            self.log_test("Courier Nearby Orders Access Control", False, "No courier token available")
            return False
        
        # First test with non-approved courier (should fail)
        success, response = self.run_test(
            "Nearby Orders - Non-Approved Courier (Should Fail)",
            "GET",
            "orders/nearby",
            403,  # Should be forbidden for non-approved couriers
            token=self.courier_token
        )
        
        if not success:
            print("   Warning: Non-approved courier was able to access nearby orders")
        
        # Now approve the courier and test again
        if self.admin_token and self.courier_id:
            approve_success, _ = self.run_test(
                "Approve Test Courier for Nearby Orders",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
            
            if approve_success:
                # Test with approved courier (should succeed)
                success, response = self.run_test(
                    "Nearby Orders - Approved Courier",
                    "GET",
                    "orders/nearby",
                    200,
                    token=self.courier_token
                )
                
                if success:
                    print(f"   Approved courier can access nearby orders: {len(response) if isinstance(response, list) else 'N/A'} orders found")
                    return True
        
        return False

    def test_order_creation_and_visibility_flow(self):
        """Test complete flow: customer creates order → order appears in courier nearby orders"""
        if not self.customer_token or not self.created_products:
            self.log_test("Order Creation and Visibility Flow", False, "No customer token or products available")
            return False
        
        print("\n🔍 Testing Order Creation and Visibility Flow...")
        
        # Step 1: Create a new order as customer
        order_items = []
        total_amount = 0
        
        for product in self.created_products[:2]:  # Use first 2 products
            quantity = 1
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
            "delivery_address": "Beşiktaş Meydanı No:15, Beşiktaş, İstanbul",
            "delivery_lat": 41.0422,
            "delivery_lng": 29.0033,
            "items": order_items,
            "total_amount": total_amount,
            "notes": "Test order for visibility bug"
        }
        
        success, order_response = self.run_test(
            "Create Order for Visibility Test",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not success:
            self.log_test("Order Creation and Visibility Flow", False, "Failed to create test order")
            return False
        
        created_order_id = order_response.get('id')
        order_status = order_response.get('status')
        
        print(f"   ✅ Order created: ID={created_order_id}, Status={order_status}")
        
        # Step 2: Verify order has status "created" and no courier_id
        if order_status != "created":
            self.log_test("Order Creation and Visibility Flow", False, f"Order status is '{order_status}', expected 'created'")
            return False
        
        if order_response.get('courier_id') is not None:
            self.log_test("Order Creation and Visibility Flow", False, f"Order has courier_id '{order_response.get('courier_id')}', expected None")
            return False
        
        print(f"   ✅ Order status correct: {order_status}, courier_id: {order_response.get('courier_id')}")
        
        # Step 3: Ensure courier is KYC approved
        if self.admin_token and self.courier_id:
            approve_success, _ = self.run_test(
                "Ensure Courier KYC Approved",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
            
            if not approve_success:
                self.log_test("Order Creation and Visibility Flow", False, "Failed to approve courier KYC")
                return False
        
        # Step 4: Check if order appears in courier nearby orders
        success, nearby_orders = self.run_test(
            "Check Order in Nearby Orders",
            "GET",
            "orders/nearby",
            200,
            token=self.courier_token
        )
        
        if not success:
            self.log_test("Order Creation and Visibility Flow", False, "Failed to get nearby orders")
            return False
        
        # Step 5: Verify the created order is in the nearby orders list
        order_found = False
        if isinstance(nearby_orders, list):
            for nearby_order in nearby_orders:
                if nearby_order.get('id') == created_order_id:
                    order_found = True
                    print(f"   ✅ Order found in nearby orders: {nearby_order.get('customer_name')} - {nearby_order.get('business_name')}")
                    break
        
        if not order_found:
            print(f"   ❌ Order {created_order_id} NOT FOUND in nearby orders list")
            print(f"   📋 Nearby orders found: {len(nearby_orders) if isinstance(nearby_orders, list) else 0}")
            if isinstance(nearby_orders, list) and len(nearby_orders) > 0:
                print("   📋 Available orders:")
                for i, order in enumerate(nearby_orders[:3]):  # Show first 3
                    print(f"      {i+1}. ID: {order.get('id')}, Customer: {order.get('customer_name')}")
            
            self.log_test("Order Creation and Visibility Flow", False, f"Created order {created_order_id} not visible in courier nearby orders")
            return False
        
        self.log_test("Order Creation and Visibility Flow", True, f"Order {created_order_id} successfully visible in courier nearby orders")
        return True

    def test_order_database_storage(self):
        """Test that orders are properly stored in database with correct status"""
        if not self.admin_token:
            self.log_test("Order Database Storage", False, "No admin token available")
            return False
        
        # Get all orders from admin endpoint to verify database storage
        success, all_orders = self.run_test(
            "Get All Orders from Database",
            "GET",
            "admin/orders",
            200,
            token=self.admin_token
        )
        
        if not success:
            self.log_test("Order Database Storage", False, "Failed to get orders from database")
            return False
        
        if not isinstance(all_orders, list):
            self.log_test("Order Database Storage", False, "Orders response is not a list")
            return False
        
        # Check for orders with status "created"
        created_orders = [order for order in all_orders if order.get('status') == 'created']
        
        print(f"   📊 Total orders in database: {len(all_orders)}")
        print(f"   📊 Orders with status 'created': {len(created_orders)}")
        
        if len(created_orders) == 0:
            self.log_test("Order Database Storage", False, "No orders with status 'created' found in database")
            return False
        
        # Verify structure of created orders
        for order in created_orders[:3]:  # Check first 3 created orders
            required_fields = ['id', 'customer_id', 'status', 'total_amount', 'created_at']
            missing_fields = [field for field in required_fields if field not in order]
            
            if missing_fields:
                self.log_test("Order Database Storage", False, f"Order {order.get('id')} missing fields: {missing_fields}")
                return False
            
            # Check that courier_id is None for created orders
            if order.get('courier_id') is not None:
                print(f"   ⚠️  Order {order.get('id')} has courier_id {order.get('courier_id')} but status is 'created'")
        
        self.log_test("Order Database Storage", True, f"Orders properly stored in database: {len(created_orders)} created orders found")
        return True

    def test_multiple_customers_order_visibility(self):
        """Test that orders from multiple customers are visible to approved couriers"""
        if not self.admin_token:
            self.log_test("Multiple Customers Order Visibility", False, "No admin token available")
            return False
        
        # Create additional customers and orders
        additional_customers = []
        additional_orders = []
        
        for i in range(2):  # Create 2 additional customers
            customer_email = f"customer_multi_{i}_{uuid.uuid4().hex[:8]}@test.com"
            customer_data = {
                "email": customer_email,
                "password": self.test_password,
                "first_name": f"Müşteri{i+1}",
                "last_name": "Test",
                "city": "İstanbul"
            }
            
            success, response = self.run_test(
                f"Register Additional Customer {i+1}",
                "POST",
                "register/customer",
                200,
                data=customer_data
            )
            
            if success and response.get('access_token'):
                customer_token = response['access_token']
                additional_customers.append({
                    'email': customer_email,
                    'token': customer_token,
                    'id': response.get('user_data', {}).get('id')
                })
                
                # Create an order for this customer
                if self.created_products:
                    product = self.created_products[0]
                    order_data = {
                        "delivery_address": f"Test Address {i+1}, İstanbul",
                        "delivery_lat": 41.0082 + (i * 0.01),
                        "delivery_lng": 28.9784 + (i * 0.01),
                        "items": [{
                            "product_id": product['id'],
                            "product_name": product['name'],
                            "product_price": product['price'],
                            "quantity": 1,
                            "subtotal": product['price']
                        }],
                        "total_amount": product['price'],
                        "notes": f"Multi-customer test order {i+1}"
                    }
                    
                    order_success, order_response = self.run_test(
                        f"Create Order for Customer {i+1}",
                        "POST",
                        "orders",
                        200,
                        data=order_data,
                        token=customer_token
                    )
                    
                    if order_success:
                        additional_orders.append(order_response)
        
        if len(additional_orders) == 0:
            self.log_test("Multiple Customers Order Visibility", False, "Failed to create additional orders")
            return False
        
        # Ensure courier is approved
        if self.courier_id:
            self.run_test(
                "Approve Courier for Multi-Customer Test",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
        
        # Check if all orders are visible to courier
        success, nearby_orders = self.run_test(
            "Get Nearby Orders - Multi Customer",
            "GET",
            "orders/nearby",
            200,
            token=self.courier_token
        )
        
        if not success:
            self.log_test("Multiple Customers Order Visibility", False, "Failed to get nearby orders")
            return False
        
        # Verify orders from different customers are visible
        found_orders = 0
        if isinstance(nearby_orders, list):
            for additional_order in additional_orders:
                order_id = additional_order.get('id')
                if any(nearby_order.get('id') == order_id for nearby_order in nearby_orders):
                    found_orders += 1
        
        print(f"   📊 Additional orders created: {len(additional_orders)}")
        print(f"   📊 Orders found in nearby list: {found_orders}")
        
        if found_orders < len(additional_orders):
            self.log_test("Multiple Customers Order Visibility", False, f"Only {found_orders}/{len(additional_orders)} orders visible to courier")
            return False
        
        self.log_test("Multiple Customers Order Visibility", True, f"All {found_orders} orders from multiple customers visible to courier")
        return True

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
        
        # Test 10: KYC Management System
        print("\n📋 PHASE 10: KYC MANAGEMENT SYSTEM")
        self.test_kyc_get_couriers()
        self.test_kyc_approve_courier()
        self.test_kyc_reject_courier_with_notes()
        self.test_kyc_status_update_flow()
        self.test_kyc_admin_authentication_required()
        self.test_kyc_error_scenarios()
        self.test_kyc_notes_handling()
        
        # Test 11: ORDER VISIBILITY BUG TESTING
        print("\n📋 PHASE 11: ORDER VISIBILITY BUG TESTING")
        self.test_courier_nearby_orders_access_control()
        self.test_order_creation_and_visibility_flow()
        self.test_order_database_storage()
        self.test_multiple_customers_order_visibility()
        
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
            "Courier Registration",
            "Product Creation",
            "Order Creation",
            "Order Status Update - ASSIGNED",
            "Order Status Update - ON_ROUTE", 
            "Order Status Update - DELIVERED",
            "Admin Get All Users",
            "Admin Get All Products",
            "Admin Get All Orders",
            "KYC Get Couriers",
            "KYC Approve Courier",
            "KYC Reject Courier with Notes",
            "KYC Status Update - APPROVED",
            "KYC Status Update - REJECTED",
            "KYC Status Update - PENDING"
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
        print("\n🎉 All DeliverTR MVP Core Business Flow tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())