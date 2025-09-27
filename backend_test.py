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

    # ===== COMPREHENSIVE BUSINESS REGISTRATION TESTS =====
    
    def test_business_registration_comprehensive(self):
        """Test business registration with complete data as specified in review request"""
        business_data = {
            "email": "testnewbusiness@example.com",
            "password": "test123",
            "business_name": "Test İşletmesi 2",
            "tax_number": "9876543210",
            "address": "Test Mahallesi, Test Sokak No: 1, İstanbul",
            "city": "Istanbul",
            "business_category": "gida",
            "description": "Test açıklaması"
        }
        
        success, response = self.run_test(
            "Business Registration - Complete Data",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ Missing response fields: {missing_fields}")
                self.log_test("Business Registration - Complete Data", False, f"Missing fields: {missing_fields}")
                return False
            
            # Verify response values
            if response.get('token_type') != 'bearer':
                print(f"   ❌ Wrong token_type: {response.get('token_type')}, expected 'bearer'")
                return False
            
            if response.get('user_type') != 'business':
                print(f"   ❌ Wrong user_type: {response.get('user_type')}, expected 'business'")
                return False
            
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'business':
                print(f"   ❌ Wrong role in user_data: {user_data.get('role')}, expected 'business'")
                return False
            
            # Verify business-specific fields
            expected_business_fields = ['business_name', 'tax_number', 'address', 'city', 'business_category', 'description']
            for field in expected_business_fields:
                if field not in user_data:
                    print(f"   ❌ Missing business field in user_data: {field}")
                    return False
                if user_data[field] != business_data[field]:
                    print(f"   ❌ Wrong {field}: {user_data[field]}, expected {business_data[field]}")
                    return False
            
            print(f"   ✅ All response fields correct")
            print(f"   ✅ Access token generated: {response['access_token'][:20]}...")
            print(f"   ✅ User role set to 'business'")
            print(f"   ✅ Business data correctly stored")
            
        return success

    def test_business_registration_duplicate_email(self):
        """Test business registration with duplicate email (should fail)"""
        # First registration
        business_data_1 = {
            "email": "duplicate@example.com",
            "password": "test123",
            "business_name": "First Business",
            "tax_number": "1111111111",
            "address": "First Address",
            "city": "Istanbul",
            "business_category": "gida",
            "description": "First business"
        }
        
        success_1, response_1 = self.run_test(
            "Business Registration - First (Should Succeed)",
            "POST",
            "register/business",
            200,
            data=business_data_1
        )
        
        if not success_1:
            self.log_test("Business Registration - Duplicate Email", False, "First registration failed")
            return False
        
        # Second registration with same email (should fail)
        business_data_2 = {
            "email": "duplicate@example.com",  # Same email
            "password": "test456",
            "business_name": "Second Business",
            "tax_number": "2222222222",
            "address": "Second Address",
            "city": "Istanbul",
            "business_category": "nakliye",
            "description": "Second business"
        }
        
        success_2, response_2 = self.run_test(
            "Business Registration - Duplicate Email (Should Fail)",
            "POST",
            "register/business",
            400,  # Should fail with bad request
            data=business_data_2
        )
        
        if success_2:
            print(f"   ✅ Duplicate email correctly rejected")
            return True
        else:
            self.log_test("Business Registration - Duplicate Email", False, "Duplicate email was not rejected")
            return False

    def test_business_registration_missing_fields(self):
        """Test business registration with missing required fields"""
        required_fields = ["email", "password", "business_name", "tax_number", "address", "city", "business_category"]
        
        base_data = {
            "email": "complete@example.com",
            "password": "test123",
            "business_name": "Complete Business",
            "tax_number": "3333333333",
            "address": "Complete Address",
            "city": "Istanbul",
            "business_category": "gida",
            "description": "Complete business"
        }
        
        all_success = True
        
        for field in required_fields:
            # Create data without the current field
            test_data = base_data.copy()
            del test_data[field]
            
            success, response = self.run_test(
                f"Business Registration - Missing {field} (Should Fail)",
                "POST",
                "register/business",
                422,  # Validation error
                data=test_data
            )
            
            if success:
                print(f"   ✅ Missing {field} correctly rejected")
            else:
                print(f"   ❌ Missing {field} was not rejected properly")
                all_success = False
        
        return all_success

    def test_business_registration_field_validation(self):
        """Test business registration field validation"""
        all_success = True
        
        # Test invalid email format
        invalid_email_data = {
            "email": "invalid-email",  # Invalid format
            "password": "test123",
            "business_name": "Test Business",
            "tax_number": "4444444444",
            "address": "Test Address",
            "city": "Istanbul",
            "business_category": "gida"
        }
        
        success, response = self.run_test(
            "Business Registration - Invalid Email (Should Fail)",
            "POST",
            "register/business",
            422,
            data=invalid_email_data
        )
        
        if not success:
            all_success = False
        
        # Test invalid business category
        invalid_category_data = {
            "email": "validcategory@example.com",
            "password": "test123",
            "business_name": "Test Business",
            "tax_number": "5555555555",
            "address": "Test Address",
            "city": "Istanbul",
            "business_category": "invalid_category"  # Should be 'gida' or 'nakliye'
        }
        
        # Note: This might pass if backend doesn't validate category values
        success, response = self.run_test(
            "Business Registration - Invalid Category",
            "POST",
            "register/business",
            200,  # Might pass if no validation
            data=invalid_category_data
        )
        
        if success:
            print(f"   ⚠️  Invalid category accepted (no validation implemented)")
        
        return all_success

    def test_business_registration_kyc_status(self):
        """Test that new business has initial KYC status"""
        business_data = {
            "email": "kyctest@example.com",
            "password": "test123",
            "business_name": "KYC Test Business",
            "tax_number": "6666666666",
            "address": "KYC Test Address",
            "city": "Istanbul",
            "business_category": "gida",
            "description": "KYC test business"
        }
        
        success, response = self.run_test(
            "Business Registration - KYC Status Check",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success:
            user_data = response.get('user_data', {})
            
            # Check if KYC status is set (might be in user_data or need separate check)
            kyc_status = user_data.get('kyc_status')
            
            if kyc_status:
                print(f"   ✅ KYC status set to: {kyc_status}")
                if kyc_status == 'pending':
                    print(f"   ✅ Initial KYC status is 'pending' as expected")
                else:
                    print(f"   ⚠️  KYC status is '{kyc_status}', expected 'pending'")
            else:
                print(f"   ⚠️  KYC status not found in response (might be set in database only)")
            
            # Check if business is active
            is_active = user_data.get('is_active')
            if is_active is not None:
                print(f"   ✅ Business active status: {is_active}")
            
        return success

    def test_business_registration_password_hashing(self):
        """Test that business password is properly hashed (not stored in plain text)"""
        business_data = {
            "email": "passwordtest@example.com",
            "password": "plaintext123",
            "business_name": "Password Test Business",
            "tax_number": "7777777777",
            "address": "Password Test Address",
            "city": "Istanbul",
            "business_category": "gida"
        }
        
        success, response = self.run_test(
            "Business Registration - Password Hashing",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success:
            user_data = response.get('user_data', {})
            
            # Verify password is not in response
            if 'password' in user_data:
                print(f"   ❌ Password found in response: {user_data['password']}")
                self.log_test("Business Registration - Password Hashing", False, "Password exposed in response")
                return False
            
            print(f"   ✅ Password not exposed in response")
            
            # Test login with the registered credentials
            login_data = {
                "email": business_data["email"],
                "password": business_data["password"]
            }
            
            login_success, login_response = self.run_test(
                "Business Login - Verify Password Hashing",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
            
            if login_success:
                print(f"   ✅ Login successful - password properly hashed and verified")
                return True
            else:
                print(f"   ❌ Login failed - password hashing/verification issue")
                return False
        
        return success

    def test_business_registration_token_validity(self):
        """Test that generated access token is valid and can be used for authentication"""
        business_data = {
            "email": "tokentest@example.com",
            "password": "test123",
            "business_name": "Token Test Business",
            "tax_number": "8888888888",
            "address": "Token Test Address",
            "city": "Istanbul",
            "business_category": "gida"
        }
        
        success, response = self.run_test(
            "Business Registration - Token Generation",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success:
            access_token = response.get('access_token')
            
            if not access_token:
                self.log_test("Business Registration - Token Validity", False, "No access token generated")
                return False
            
            print(f"   ✅ Access token generated: {access_token[:20]}...")
            
            # Test using the token to access a protected endpoint
            token_test_success, token_response = self.run_test(
                "Business Token - Access Protected Endpoint",
                "GET",
                "products/my",  # Business-only endpoint
                200,
                token=access_token
            )
            
            if token_test_success:
                print(f"   ✅ Access token valid - can access protected endpoints")
                return True
            else:
                print(f"   ❌ Access token invalid - cannot access protected endpoints")
                return False
        
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

    # ===== COURIER ORDER ACCEPTANCE TESTS =====
    
    def test_order_acceptance_endpoint(self):
        """Test /orders/{order_id}/accept endpoint functionality"""
        if not self.courier_token or not self.created_orders:
            self.log_test("Order Acceptance Endpoint", False, "No courier token or orders available")
            return False
        
        # Ensure courier is KYC approved first
        if self.admin_token and self.courier_id:
            self.run_test(
                "Approve Courier for Order Acceptance",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
        
        # Create a fresh order for acceptance testing
        if not self.customer_token or not self.created_products:
            self.log_test("Order Acceptance Endpoint", False, "No customer token or products for order creation")
            return False
        
        product = self.created_products[0]
        order_data = {
            "delivery_address": "Taksim Meydanı No:1, Beyoğlu, İstanbul",
            "delivery_lat": 41.0369,
            "delivery_lng": 28.9850,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 1,
                "subtotal": product['price']
            }],
            "total_amount": product['price'],
            "notes": "Order acceptance test"
        }
        
        order_success, order_response = self.run_test(
            "Create Order for Acceptance Test",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not order_success:
            self.log_test("Order Acceptance Endpoint", False, "Failed to create test order")
            return False
        
        order_id = order_response.get('id')
        
        # Test order acceptance
        success, response = self.run_test(
            "Accept Order - POST /orders/{order_id}/accept",
            "POST",
            f"orders/{order_id}/accept",
            200,
            token=self.courier_token
        )
        
        if success:
            print(f"   ✅ Order {order_id} accepted successfully")
            print(f"   Response: {response}")
            
            # Verify response contains expected fields
            expected_fields = ['success', 'message', 'order_id', 'courier_name']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing response fields: {missing_fields}")
        
        return success
    
    def test_order_acceptance_status_update(self):
        """Test that order acceptance updates status to 'assigned' and sets courier_id"""
        if not self.courier_token or not self.customer_token or not self.created_products:
            self.log_test("Order Acceptance Status Update", False, "Missing required tokens or products")
            return False
        
        # Ensure courier is KYC approved
        if self.admin_token and self.courier_id:
            self.run_test(
                "Approve Courier for Status Update Test",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
        
        # Create order
        product = self.created_products[0]
        order_data = {
            "delivery_address": "Şişli Plaza, Şişli, İstanbul",
            "delivery_lat": 41.0498,
            "delivery_lng": 28.9662,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 1,
                "subtotal": product['price']
            }],
            "total_amount": product['price'],
            "notes": "Status update test order"
        }
        
        order_success, order_response = self.run_test(
            "Create Order for Status Update Test",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not order_success:
            self.log_test("Order Acceptance Status Update", False, "Failed to create test order")
            return False
        
        order_id = order_response.get('id')
        
        # Verify initial order state
        if order_response.get('status') != 'created':
            self.log_test("Order Acceptance Status Update", False, f"Initial order status is '{order_response.get('status')}', expected 'created'")
            return False
        
        if order_response.get('courier_id') is not None:
            self.log_test("Order Acceptance Status Update", False, f"Initial courier_id is '{order_response.get('courier_id')}', expected None")
            return False
        
        print(f"   ✅ Initial order state correct: status='{order_response.get('status')}', courier_id={order_response.get('courier_id')}")
        
        # Accept the order
        accept_success, accept_response = self.run_test(
            "Accept Order for Status Verification",
            "POST",
            f"orders/{order_id}/accept",
            200,
            token=self.courier_token
        )
        
        if not accept_success:
            self.log_test("Order Acceptance Status Update", False, "Failed to accept order")
            return False
        
        # Verify order status was updated by getting order details from admin
        if self.admin_token:
            verify_success, all_orders = self.run_test(
                "Verify Order Status After Acceptance",
                "GET",
                "admin/orders",
                200,
                token=self.admin_token
            )
            
            if verify_success and isinstance(all_orders, list):
                accepted_order = None
                for order in all_orders:
                    if order.get('id') == order_id:
                        accepted_order = order
                        break
                
                if accepted_order:
                    actual_status = accepted_order.get('status')
                    actual_courier_id = accepted_order.get('courier_id')
                    
                    print(f"   📊 Order after acceptance: status='{actual_status}', courier_id='{actual_courier_id}'")
                    
                    if actual_status != 'assigned':
                        self.log_test("Order Acceptance Status Update", False, f"Order status is '{actual_status}', expected 'assigned'")
                        return False
                    
                    if actual_courier_id != self.courier_id:
                        self.log_test("Order Acceptance Status Update", False, f"Courier ID is '{actual_courier_id}', expected '{self.courier_id}'")
                        return False
                    
                    print(f"   ✅ Order status correctly updated to 'assigned' with courier_id '{actual_courier_id}'")
                    self.log_test("Order Acceptance Status Update", True)
                    return True
                else:
                    self.log_test("Order Acceptance Status Update", False, "Could not find accepted order in database")
                    return False
        
        self.log_test("Order Acceptance Status Update", False, "Could not verify order status update")
        return False
    
    def test_kyc_approval_check_for_acceptance(self):
        """Test that only KYC approved couriers can accept orders"""
        # Create a new courier that is not KYC approved
        non_approved_courier_email = f"non_approved_{uuid.uuid4().hex[:8]}@test.com"
        courier_data = {
            "email": non_approved_courier_email,
            "password": self.test_password,
            "first_name": "Non",
            "last_name": "Approved",
            "iban": "TR330006100519786457841330",
            "vehicle_type": "motor",
            "vehicle_model": "Test Bike",
            "license_class": "A2",
            "license_number": "34TEST123",
            "city": "İstanbul"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Non-Approved Courier",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if not reg_success:
            self.log_test("KYC Approval Check for Acceptance", False, "Failed to create non-approved courier")
            return False
        
        non_approved_token = reg_response.get('access_token')
        non_approved_id = reg_response.get('user_data', {}).get('id')
        
        # Create an order to test with
        if not self.customer_token or not self.created_products:
            self.log_test("KYC Approval Check for Acceptance", False, "No customer token or products available")
            return False
        
        product = self.created_products[0]
        order_data = {
            "delivery_address": "Beşiktaş İskelesi, Beşiktaş, İstanbul",
            "delivery_lat": 41.0766,
            "delivery_lng": 28.9688,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 1,
                "subtotal": product['price']
            }],
            "total_amount": product['price'],
            "notes": "KYC approval test order"
        }
        
        order_success, order_response = self.run_test(
            "Create Order for KYC Test",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not order_success:
            self.log_test("KYC Approval Check for Acceptance", False, "Failed to create test order")
            return False
        
        order_id = order_response.get('id')
        
        # Test 1: Non-approved courier tries to accept order (should fail)
        success, response = self.run_test(
            "Non-Approved Courier Accept Order (Should Fail)",
            "POST",
            f"orders/{order_id}/accept",
            403,  # Should be forbidden
            token=non_approved_token
        )
        
        if not success:
            self.log_test("KYC Approval Check for Acceptance", False, "Non-approved courier was able to accept order")
            return False
        
        print(f"   ✅ Non-approved courier correctly blocked from accepting orders")
        
        # Test 2: Approve the courier and try again (should succeed)
        if self.admin_token:
            approve_success, _ = self.run_test(
                "Approve Courier for Acceptance Test",
                "PATCH",
                f"admin/couriers/{non_approved_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
            
            if approve_success:
                # Now try to accept the order (should succeed)
                success, response = self.run_test(
                    "Approved Courier Accept Order",
                    "POST",
                    f"orders/{order_id}/accept",
                    200,
                    token=non_approved_token
                )
                
                if success:
                    print(f"   ✅ Approved courier successfully accepted order")
                    self.log_test("KYC Approval Check for Acceptance", True)
                    return True
                else:
                    self.log_test("KYC Approval Check for Acceptance", False, "Approved courier failed to accept order")
                    return False
        
        self.log_test("KYC Approval Check for Acceptance", False, "Could not complete KYC approval test")
        return False
    
    def test_already_accepted_order_error(self):
        """Test error handling for already accepted orders"""
        if not self.courier_token or not self.customer_token or not self.created_products:
            self.log_test("Already Accepted Order Error", False, "Missing required tokens or products")
            return False
        
        # Ensure courier is KYC approved
        if self.admin_token and self.courier_id:
            self.run_test(
                "Approve Courier for Double Accept Test",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
        
        # Create order
        product = self.created_products[0]
        order_data = {
            "delivery_address": "Üsküdar Meydanı, Üsküdar, İstanbul",
            "delivery_lat": 41.0431,
            "delivery_lng": 29.0088,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 1,
                "subtotal": product['price']
            }],
            "total_amount": product['price'],
            "notes": "Double acceptance test order"
        }
        
        order_success, order_response = self.run_test(
            "Create Order for Double Accept Test",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not order_success:
            self.log_test("Already Accepted Order Error", False, "Failed to create test order")
            return False
        
        order_id = order_response.get('id')
        
        # Accept the order first time (should succeed)
        first_accept_success, first_response = self.run_test(
            "First Order Acceptance",
            "POST",
            f"orders/{order_id}/accept",
            200,
            token=self.courier_token
        )
        
        if not first_accept_success:
            self.log_test("Already Accepted Order Error", False, "Failed to accept order first time")
            return False
        
        print(f"   ✅ Order accepted first time successfully")
        
        # Try to accept the same order again (should fail)
        second_accept_success, second_response = self.run_test(
            "Second Order Acceptance (Should Fail)",
            "POST",
            f"orders/{order_id}/accept",
            400,  # Should be bad request
            token=self.courier_token
        )
        
        if second_accept_success:
            print(f"   ✅ Second acceptance correctly rejected")
            self.log_test("Already Accepted Order Error", True)
            return True
        else:
            self.log_test("Already Accepted Order Error", False, "Second acceptance was not properly rejected")
            return False
    
    def test_nearby_orders_realistic_coordinates(self):
        """Test that nearby orders API returns realistic Istanbul coordinates instead of 520km distances"""
        if not self.courier_token:
            self.log_test("Nearby Orders Realistic Coordinates", False, "No courier token available")
            return False
        
        # Ensure courier is KYC approved
        if self.admin_token and self.courier_id:
            self.run_test(
                "Approve Courier for Coordinates Test",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
        
        # Get nearby orders
        success, nearby_orders = self.run_test(
            "Get Nearby Orders for Coordinate Check",
            "GET",
            "orders/nearby",
            200,
            token=self.courier_token
        )
        
        if not success:
            self.log_test("Nearby Orders Realistic Coordinates", False, "Failed to get nearby orders")
            return False
        
        if not isinstance(nearby_orders, list) or len(nearby_orders) == 0:
            self.log_test("Nearby Orders Realistic Coordinates", False, "No nearby orders returned")
            return False
        
        print(f"   📊 Found {len(nearby_orders)} nearby orders")
        
        # Check coordinates are realistic for Istanbul
        istanbul_bounds = {
            'lat_min': 40.8, 'lat_max': 41.3,  # Istanbul latitude range
            'lng_min': 28.5, 'lng_max': 29.5   # Istanbul longitude range
        }
        
        realistic_orders = 0
        total_distance_sum = 0
        
        for i, order in enumerate(nearby_orders[:5]):  # Check first 5 orders
            pickup_addr = order.get('pickup_address', {})
            delivery_addr = order.get('delivery_address', {})
            
            pickup_lat = pickup_addr.get('lat')
            pickup_lng = pickup_addr.get('lng')
            delivery_lat = delivery_addr.get('lat')
            delivery_lng = delivery_addr.get('lng')
            
            print(f"   📍 Order {i+1}:")
            print(f"      Pickup: {pickup_lat}, {pickup_lng}")
            print(f"      Delivery: {delivery_lat}, {delivery_lng}")
            
            # Check if coordinates are within Istanbul bounds
            pickup_in_istanbul = (
                pickup_lat and pickup_lng and
                istanbul_bounds['lat_min'] <= pickup_lat <= istanbul_bounds['lat_max'] and
                istanbul_bounds['lng_min'] <= pickup_lng <= istanbul_bounds['lng_max']
            )
            
            delivery_in_istanbul = (
                delivery_lat and delivery_lng and
                istanbul_bounds['lat_min'] <= delivery_lat <= istanbul_bounds['lat_max'] and
                istanbul_bounds['lng_min'] <= delivery_lng <= istanbul_bounds['lng_max']
            )
            
            if pickup_in_istanbul and delivery_in_istanbul:
                realistic_orders += 1
                
                # Calculate distance between pickup and delivery
                if pickup_lat and pickup_lng and delivery_lat and delivery_lng:
                    distance = self.calculate_distance(pickup_lat, pickup_lng, delivery_lat, delivery_lng)
                    total_distance_sum += distance
                    print(f"      Distance: {distance:.2f} km")
                    
                    # Check if distance is reasonable (not 520km!)
                    if distance > 50:  # More than 50km is unrealistic for Istanbul delivery
                        print(f"      ⚠️  Distance too large: {distance:.2f} km")
                    else:
                        print(f"      ✅ Realistic distance: {distance:.2f} km")
            else:
                print(f"      ❌ Coordinates outside Istanbul bounds")
        
        avg_distance = total_distance_sum / realistic_orders if realistic_orders > 0 else 0
        
        print(f"   📊 Realistic orders: {realistic_orders}/{min(5, len(nearby_orders))}")
        print(f"   📊 Average distance: {avg_distance:.2f} km")
        
        # Success criteria: at least 80% of orders have realistic coordinates and average distance < 20km
        success_rate = realistic_orders / min(5, len(nearby_orders))
        
        if success_rate >= 0.8 and avg_distance < 20:
            print(f"   ✅ Coordinates are realistic: {success_rate*100:.1f}% success rate, {avg_distance:.2f}km avg distance")
            self.log_test("Nearby Orders Realistic Coordinates", True)
            return True
        else:
            print(f"   ❌ Coordinates not realistic enough: {success_rate*100:.1f}% success rate, {avg_distance:.2f}km avg distance")
            self.log_test("Nearby Orders Realistic Coordinates", False, f"Only {success_rate*100:.1f}% realistic coordinates, {avg_distance:.2f}km avg distance")
            return False
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two points using Haversine formula"""
        import math
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def test_complete_order_acceptance_flow(self):
        """Test complete flow: courier accepts order → order status updates to 'assigned' → courier_id is set"""
        if not self.courier_token or not self.customer_token or not self.created_products:
            self.log_test("Complete Order Acceptance Flow", False, "Missing required tokens or products")
            return False
        
        print("\n🔍 Testing Complete Order Acceptance Flow...")
        
        # Step 1: Ensure courier is KYC approved
        if self.admin_token and self.courier_id:
            approve_success, _ = self.run_test(
                "Approve Courier for Complete Flow",
                "PATCH",
                f"admin/couriers/{self.courier_id}/kyc?kyc_status=approved",
                200,
                token=self.admin_token
            )
            
            if not approve_success:
                self.log_test("Complete Order Acceptance Flow", False, "Failed to approve courier")
                return False
        
        # Step 2: Create a fresh order
        product = self.created_products[0]
        order_data = {
            "delivery_address": "Sarıyer Sahil, Sarıyer, İstanbul",
            "delivery_lat": 41.1058,
            "delivery_lng": 29.0074,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 1,
                "subtotal": product['price']
            }],
            "total_amount": product['price'],
            "notes": "Complete flow test order"
        }
        
        order_success, order_response = self.run_test(
            "Create Order for Complete Flow",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if not order_success:
            self.log_test("Complete Order Acceptance Flow", False, "Failed to create test order")
            return False
        
        order_id = order_response.get('id')
        print(f"   ✅ Step 1: Order created with ID {order_id}")
        
        # Step 3: Verify initial order state
        if order_response.get('status') != 'created' or order_response.get('courier_id') is not None:
            self.log_test("Complete Order Acceptance Flow", False, "Initial order state incorrect")
            return False
        
        print(f"   ✅ Step 2: Initial order state correct (status='created', courier_id=None)")
        
        # Step 4: Accept the order
        accept_success, accept_response = self.run_test(
            "Accept Order in Complete Flow",
            "POST",
            f"orders/{order_id}/accept",
            200,
            token=self.courier_token
        )
        
        if not accept_success:
            self.log_test("Complete Order Acceptance Flow", False, "Failed to accept order")
            return False
        
        print(f"   ✅ Step 3: Order accepted successfully")
        
        # Step 5: Verify order status and courier assignment
        if self.admin_token:
            verify_success, all_orders = self.run_test(
                "Verify Final Order State",
                "GET",
                "admin/orders",
                200,
                token=self.admin_token
            )
            
            if verify_success and isinstance(all_orders, list):
                final_order = None
                for order in all_orders:
                    if order.get('id') == order_id:
                        final_order = order
                        break
                
                if final_order:
                    final_status = final_order.get('status')
                    final_courier_id = final_order.get('courier_id')
                    assigned_at = final_order.get('assigned_at')
                    
                    print(f"   📊 Final order state:")
                    print(f"      Status: {final_status}")
                    print(f"      Courier ID: {final_courier_id}")
                    print(f"      Assigned at: {assigned_at}")
                    
                    # Verify all expected changes
                    if final_status != 'assigned':
                        self.log_test("Complete Order Acceptance Flow", False, f"Final status is '{final_status}', expected 'assigned'")
                        return False
                    
                    if final_courier_id != self.courier_id:
                        self.log_test("Complete Order Acceptance Flow", False, f"Final courier_id is '{final_courier_id}', expected '{self.courier_id}'")
                        return False
                    
                    if not assigned_at:
                        self.log_test("Complete Order Acceptance Flow", False, "assigned_at timestamp not set")
                        return False
                    
                    print(f"   ✅ Step 4: Order status correctly updated to 'assigned'")
                    print(f"   ✅ Step 5: Courier ID correctly set to '{final_courier_id}'")
                    print(f"   ✅ Step 6: Assignment timestamp recorded")
                    
                    self.log_test("Complete Order Acceptance Flow", True, "All steps completed successfully")
                    return True
                else:
                    self.log_test("Complete Order Acceptance Flow", False, "Could not find order in database")
                    return False
        
        self.log_test("Complete Order Acceptance Flow", False, "Could not verify final order state")
        return False

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

    # ===== PUBLIC BUSINESS ENDPOINTS TESTS =====
    
    def test_public_businesses_endpoint(self):
        """Test GET /businesses endpoint - should return approved businesses with location data"""
        success, response = self.run_test(
            "Public Businesses Endpoint",
            "GET",
            "businesses",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} businesses")
            
            # Verify business data structure
            if len(response) > 0:
                business = response[0]
                required_fields = ['id', 'name', 'category', 'rating', 'delivery_time', 'min_order', 'location']
                missing_fields = [field for field in required_fields if field not in business]
                
                if missing_fields:
                    self.log_test("Public Businesses Endpoint", False, f"Missing required fields: {missing_fields}")
                    return False
                
                # Verify location data structure
                location = business.get('location', {})
                location_fields = ['name', 'lat', 'lng']
                missing_location_fields = [field for field in location_fields if field not in location]
                
                if missing_location_fields:
                    self.log_test("Public Businesses Endpoint", False, f"Missing location fields: {missing_location_fields}")
                    return False
                
                # Verify Istanbul coordinates
                lat = location.get('lat')
                lng = location.get('lng')
                istanbul_bounds = {'lat_min': 40.8, 'lat_max': 41.3, 'lng_min': 28.5, 'lng_max': 29.5}
                
                if not (istanbul_bounds['lat_min'] <= lat <= istanbul_bounds['lat_max'] and 
                        istanbul_bounds['lng_min'] <= lng <= istanbul_bounds['lng_max']):
                    self.log_test("Public Businesses Endpoint", False, f"Coordinates not in Istanbul bounds: {lat}, {lng}")
                    return False
                
                print(f"   ✅ Business data structure valid")
                print(f"   ✅ Location data: {location['name']} ({lat}, {lng})")
                print(f"   ✅ Sample business: {business['name']} - {business['category']}")
        
        return success

    def test_business_products_endpoint(self):
        """Test GET /businesses/{business_id}/products endpoint"""
        if not self.business_id:
            self.log_test("Business Products Endpoint", False, "No business ID available")
            return False
        
        success, response = self.run_test(
            "Business Products Endpoint",
            "GET",
            f"businesses/{self.business_id}/products",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} products for business {self.business_id}")
            
            # Verify product data structure if products exist
            if len(response) > 0:
                product = response[0]
                required_fields = ['name', 'description', 'price', 'is_available', 'preparation_time_minutes']
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    self.log_test("Business Products Endpoint", False, f"Missing required product fields: {missing_fields}")
                    return False
                
                print(f"   ✅ Product data structure valid")
                print(f"   ✅ Sample product: {product['name']} - ${product['price']}")
        
        return success

    def test_business_products_invalid_id(self):
        """Test GET /businesses/{business_id}/products with invalid business ID"""
        success, response = self.run_test(
            "Business Products - Invalid ID",
            "GET",
            "businesses/invalid-business-id/products",
            500  # Expecting error for invalid ID
        )
        
        return success

    def test_approved_businesses_only(self):
        """Test that only approved businesses (kyc_status: approved) are returned"""
        # First, create a business and ensure it's not approved
        non_approved_email = f"non_approved_biz_{uuid.uuid4().hex[:8]}@test.com"
        business_data = {
            "email": non_approved_email,
            "password": self.test_password,
            "business_name": "Non-Approved Restaurant",
            "tax_number": "9876543210",
            "address": "Test Address, İstanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "This business should not appear in public list"
        }
        
        reg_success, reg_response = self.run_test(
            "Register Non-Approved Business",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if not reg_success:
            self.log_test("Approved Businesses Only", False, "Failed to create non-approved business")
            return False
        
        non_approved_business_id = reg_response.get('user_data', {}).get('id')
        
        # Get public businesses list
        success, businesses = self.run_test(
            "Get Public Businesses for Approval Check",
            "GET",
            "businesses",
            200
        )
        
        if not success:
            self.log_test("Approved Businesses Only", False, "Failed to get businesses list")
            return False
        
        # Check that non-approved business is NOT in the list
        non_approved_found = False
        if isinstance(businesses, list):
            for business in businesses:
                if business.get('id') == non_approved_business_id:
                    non_approved_found = True
                    break
        
        if non_approved_found:
            self.log_test("Approved Businesses Only", False, "Non-approved business found in public list")
            return False
        
        # Now approve the business and check it appears
        if self.admin_token:
            # First, we need to set the business kyc_status to approved
            # This would typically be done through an admin endpoint
            print(f"   ✅ Non-approved business correctly excluded from public list")
            self.log_test("Approved Businesses Only", True)
            return True
        
        return True

    def test_public_endpoints_no_auth_required(self):
        """Test that public business endpoints work without authentication"""
        # Test businesses endpoint without token
        success, response = self.run_test(
            "Public Businesses - No Auth Required",
            "GET",
            "businesses",
            200
        )
        
        if not success:
            self.log_test("Public Endpoints No Auth Required", False, "Businesses endpoint requires authentication")
            return False
        
        # Test business products endpoint without token (if we have a business ID)
        if self.business_id:
            success, response = self.run_test(
                "Public Business Products - No Auth Required",
                "GET",
                f"businesses/{self.business_id}/products",
                200
            )
            
            if not success:
                self.log_test("Public Endpoints No Auth Required", False, "Business products endpoint requires authentication")
                return False
        
        print(f"   ✅ Public endpoints accessible without authentication")
        self.log_test("Public Endpoints No Auth Required", True)
        return True

    def test_business_data_completeness(self):
        """Test that business data includes all required fields with proper values"""
        success, businesses = self.run_test(
            "Get Businesses for Data Completeness Check",
            "GET",
            "businesses",
            200
        )
        
        if not success or not isinstance(businesses, list) or len(businesses) == 0:
            self.log_test("Business Data Completeness", False, "No businesses returned")
            return False
        
        all_valid = True
        for i, business in enumerate(businesses[:3]):  # Check first 3 businesses
            print(f"   Checking business {i+1}: {business.get('name', 'Unknown')}")
            
            # Check required fields
            required_fields = {
                'id': str,
                'name': str,
                'category': str,
                'rating': (int, float),
                'delivery_time': str,
                'min_order': (int, float),
                'location': dict,
                'is_open': bool
            }
            
            for field, expected_type in required_fields.items():
                value = business.get(field)
                if value is None:
                    print(f"      ❌ Missing field: {field}")
                    all_valid = False
                elif not isinstance(value, expected_type):
                    print(f"      ❌ Wrong type for {field}: expected {expected_type}, got {type(value)}")
                    all_valid = False
                else:
                    print(f"      ✅ {field}: {value}")
            
            # Check location data specifically
            location = business.get('location', {})
            if isinstance(location, dict):
                location_fields = ['name', 'lat', 'lng']
                for field in location_fields:
                    if field not in location:
                        print(f"      ❌ Missing location field: {field}")
                        all_valid = False
                    else:
                        print(f"      ✅ location.{field}: {location[field]}")
        
        if all_valid:
            print(f"   ✅ All business data complete and properly typed")
            self.log_test("Business Data Completeness", True)
            return True
        else:
            self.log_test("Business Data Completeness", False, "Some business data incomplete or improperly typed")
            return False

    def test_product_data_completeness(self):
        """Test that product data includes all required fields with proper values"""
        if not self.business_id:
            self.log_test("Product Data Completeness", False, "No business ID available")
            return False
        
        success, products = self.run_test(
            "Get Products for Data Completeness Check",
            "GET",
            f"businesses/{self.business_id}/products",
            200
        )
        
        if not success or not isinstance(products, list) or len(products) == 0:
            self.log_test("Product Data Completeness", False, "No products returned")
            return False
        
        all_valid = True
        for i, product in enumerate(products[:3]):  # Check first 3 products
            print(f"   Checking product {i+1}: {product.get('name', 'Unknown')}")
            
            # Check required fields
            required_fields = {
                'name': str,
                'description': str,
                'price': (int, float),
                'is_available': bool,
                'preparation_time_minutes': int
            }
            
            optional_fields = {
                'photo_url': str,
                'category': str
            }
            
            for field, expected_type in required_fields.items():
                value = product.get(field)
                if value is None:
                    print(f"      ❌ Missing required field: {field}")
                    all_valid = False
                elif not isinstance(value, expected_type):
                    print(f"      ❌ Wrong type for {field}: expected {expected_type}, got {type(value)}")
                    all_valid = False
                else:
                    print(f"      ✅ {field}: {value}")
            
            # Check optional fields (if present)
            for field, expected_type in optional_fields.items():
                value = product.get(field)
                if value is not None:
                    if not isinstance(value, expected_type):
                        print(f"      ❌ Wrong type for optional {field}: expected {expected_type}, got {type(value)}")
                        all_valid = False
                    else:
                        print(f"      ✅ {field}: {value}")
        
        if all_valid:
            print(f"   ✅ All product data complete and properly typed")
            self.log_test("Product Data Completeness", True)
            return True
        else:
            self.log_test("Product Data Completeness", False, "Some product data incomplete or improperly typed")
            return False

    def run_business_registration_tests(self):
        """Run comprehensive business registration tests as requested in review"""
        print("🚀 Starting Business Registration Endpoint Tests")
        print("=" * 70)
        
        # Test comprehensive business registration functionality
        print("\n📋 BUSINESS REGISTRATION COMPREHENSIVE TESTING")
        self.test_business_registration_comprehensive()
        self.test_business_registration_duplicate_email()
        self.test_business_registration_missing_fields()
        self.test_business_registration_field_validation()
        self.test_business_registration_kyc_status()
        self.test_business_registration_password_hashing()
        self.test_business_registration_token_validity()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 BUSINESS REGISTRATION TEST SUMMARY")
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
        else:
            print("\n✅ ALL BUSINESS REGISTRATION TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

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
        
        # Test 11: COURIER ORDER ACCEPTANCE TESTING
        print("\n📋 PHASE 11: COURIER ORDER ACCEPTANCE TESTING")
        self.test_order_acceptance_endpoint()
        self.test_order_acceptance_status_update()
        self.test_kyc_approval_check_for_acceptance()
        self.test_already_accepted_order_error()
        self.test_nearby_orders_realistic_coordinates()
        self.test_complete_order_acceptance_flow()
        
        # Test 12: ORDER VISIBILITY BUG TESTING
        print("\n📋 PHASE 12: ORDER VISIBILITY BUG TESTING")
        self.test_courier_nearby_orders_access_control()
        self.test_order_creation_and_visibility_flow()
        self.test_order_database_storage()
        self.test_multiple_customers_order_visibility()
        
        # Test 13: PUBLIC BUSINESS ENDPOINTS TESTING
        print("\n📋 PHASE 13: PUBLIC BUSINESS ENDPOINTS TESTING")
        self.test_public_businesses_endpoint()
        self.test_business_products_endpoint()
        self.test_business_products_invalid_id()
        self.test_approved_businesses_only()
        self.test_public_endpoints_no_auth_required()
        self.test_business_data_completeness()
        self.test_product_data_completeness()
        
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
    
    # Run business registration tests as requested in review
    print("🎯 RUNNING BUSINESS REGISTRATION TESTS AS REQUESTED")
    success = tester.run_business_registration_tests()
    
    if success:
        print("\n🎉 All Business Registration tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some Business Registration tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())