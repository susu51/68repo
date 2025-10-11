#!/usr/bin/env python3
"""
Kuryecini Backend Comprehensive Testing Suite
Comprehensive testing of all backend API endpoints, security, database, error handling, and performance
Based on the review request for complete system inspection.
"""

import requests
import sys
import json
import time
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class KuryeciniBackendTester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://courier-stable.preview.emergentagent.com')
        self.api_url = f"{self.base_url}/api"
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.critical_issues = []
        self.security_issues = []
        self.performance_issues = []
        
        # Authentication tokens
        self.admin_token = None
        self.business_token = None
        self.customer_token = None
        self.courier_token = None
        
        # Test data storage
        self.test_users = {}
        self.test_products = []
        self.test_orders = []
        
        print(f"🔧 Kuryecini Backend Tester initialized")
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")

    def log_test(self, name: str, success: bool, details: str = "", category: str = "general"):
        """Log test results with categorization"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - FAILED: {details}")
            
            # Categorize failures
            if category == "security":
                self.security_issues.append({"test": name, "details": details})
            elif category == "critical":
                self.critical_issues.append({"test": name, "details": details})
            elif category == "performance":
                self.performance_issues.append({"test": name, "details": details})
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    token: str = None, expected_status: int = 200, 
                    timeout: int = 10) -> tuple[bool, Any, int, float]:
        """Make HTTP request and return success, response, status_code, response_time"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return False, {}, 0, 0
            
            response_time = time.time() - start_time
            
            # Check if response time is acceptable (< 5 seconds for most endpoints)
            if response_time > 5.0:
                self.performance_issues.append({
                    "endpoint": endpoint,
                    "response_time": response_time,
                    "details": f"Slow response: {response_time:.2f}s"
                })
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return success, response_data, response.status_code, response_time
            
        except Exception as e:
            response_time = time.time() - start_time
            return False, {"error": str(e)}, 0, response_time

    # ===== 1. AUTHENTICATION ENDPOINTS TESTING =====
    
    def test_admin_authentication(self):
        """Test admin authentication with password '6851'"""
        print("\n🔐 TESTING ADMIN AUTHENTICATION")
        
        # Test 1: Admin login via regular endpoint
        success, response, status, time_taken = self.make_request(
            'POST', 'auth/login', 
            {"email": "admin@test.com", "password": "6851"}
        )
        
        if success and response.get('access_token'):
            self.admin_token = response['access_token']
            self.log_test("Admin Login via Regular Endpoint", True)
            
            # Verify admin user data
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'admin':
                self.log_test("Admin User Data Validation", False, 
                            f"Expected admin role, got {user_data.get('role')}", "critical")
            else:
                self.log_test("Admin User Data Validation", True)
        else:
            self.log_test("Admin Login via Regular Endpoint", False, 
                        f"Status: {status}, Response: {response}", "critical")
        
        # Test 2: Legacy admin endpoint
        success, response, status, time_taken = self.make_request(
            'POST', 'auth/admin', 
            {"password": "6851"}
        )
        
        self.log_test("Legacy Admin Endpoint", success, 
                     f"Status: {status}" if not success else "")
        
        # Test 3: Wrong admin password
        success, response, status, time_taken = self.make_request(
            'POST', 'auth/login', 
            {"email": "admin@test.com", "password": "wrong"}, 
            expected_status=401
        )
        
        self.log_test("Admin Wrong Password Rejection", success, 
                     f"Status: {status}" if not success else "", "security")

    def test_user_registration_endpoints(self):
        """Test all user registration endpoints"""
        print("\n👥 TESTING USER REGISTRATION ENDPOINTS")
        
        # Test Business Registration
        business_data = {
            "email": f"test_business_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "business_name": "Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address, Istanbul",
            "city": "Istanbul",
            "business_category": "gida",
            "description": "Test restaurant"
        }
        
        success, response, status, time_taken = self.make_request(
            'POST', 'register/business', business_data
        )
        
        if success and response.get('access_token'):
            self.business_token = response['access_token']
            self.test_users['business'] = {
                'email': business_data['email'],
                'password': business_data['password'],
                'token': self.business_token,
                'id': response.get('user_data', {}).get('id')
            }
            self.log_test("Business Registration", True)
        else:
            self.log_test("Business Registration", False, 
                        f"Status: {status}, Response: {response}", "critical")
        
        # Test Customer Registration
        customer_data = {
            "email": f"test_customer_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Customer",
            "city": "Istanbul"
        }
        
        success, response, status, time_taken = self.make_request(
            'POST', 'register/customer', customer_data
        )
        
        if success and response.get('access_token'):
            self.customer_token = response['access_token']
            self.test_users['customer'] = {
                'email': customer_data['email'],
                'password': customer_data['password'],
                'token': self.customer_token,
                'id': response.get('user_data', {}).get('id')
            }
            self.log_test("Customer Registration", True)
        else:
            self.log_test("Customer Registration", False, 
                        f"Status: {status}, Response: {response}", "critical")
        
        # Test Courier Registration
        courier_data = {
            "email": f"test_courier_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Courier",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "vehicle_model": "Honda PCX 150",
            "license_class": "A2",
            "license_number": "34ABC123",
            "city": "Istanbul"
        }
        
        success, response, status, time_taken = self.make_request(
            'POST', 'register/courier', courier_data
        )
        
        if success and response.get('access_token'):
            self.courier_token = response['access_token']
            self.test_users['courier'] = {
                'email': courier_data['email'],
                'password': courier_data['password'],
                'token': self.courier_token,
                'id': response.get('user_data', {}).get('id')
            }
            self.log_test("Courier Registration", True)
        else:
            self.log_test("Courier Registration", False, 
                        f"Status: {status}, Response: {response}", "critical")

    def test_login_endpoints(self):
        """Test login functionality for all user types"""
        print("\n🔑 TESTING LOGIN ENDPOINTS")
        
        for user_type, user_data in self.test_users.items():
            success, response, status, time_taken = self.make_request(
                'POST', 'auth/login',
                {"email": user_data['email'], "password": user_data['password']}
            )
            
            if success and response.get('access_token'):
                # Update token
                user_data['token'] = response['access_token']
                self.log_test(f"{user_type.title()} Login", True)
                
                # Verify user type in response
                expected_user_type = user_type if user_type != 'business' else 'business'
                actual_user_type = response.get('user_type')
                if actual_user_type != expected_user_type:
                    self.log_test(f"{user_type.title()} Login User Type", False,
                                f"Expected {expected_user_type}, got {actual_user_type}", "critical")
                else:
                    self.log_test(f"{user_type.title()} Login User Type", True)
            else:
                self.log_test(f"{user_type.title()} Login", False,
                            f"Status: {status}, Response: {response}", "critical")

    # ===== 2. BUSINESS ENDPOINTS TESTING =====
    
    def test_business_endpoints(self):
        """Test business-specific endpoints"""
        print("\n🏪 TESTING BUSINESS ENDPOINTS")
        
        if not self.business_token:
            self.log_test("Business Endpoints", False, "No business token available", "critical")
            return
        
        # Test Product Creation
        product_data = {
            "name": "Test Product",
            "description": "Test product description",
            "price": 25.50,
            "category": "main_course",
            "preparation_time_minutes": 20,
            "is_available": True
        }
        
        success, response, status, time_taken = self.make_request(
            'POST', 'products', product_data, token=self.business_token
        )
        
        if success and response.get('id'):
            self.test_products.append(response)
            self.log_test("Product Creation", True)
        else:
            self.log_test("Product Creation", False,
                        f"Status: {status}, Response: {response}", "critical")
        
        # Test Get Business Products
        success, response, status, time_taken = self.make_request(
            'GET', 'products/my', token=self.business_token
        )
        
        self.log_test("Get Business Products", success,
                     f"Status: {status}" if not success else "")
        
        # Test Get All Products (public)
        success, response, status, time_taken = self.make_request(
            'GET', 'products'
        )
        
        self.log_test("Get All Products (Public)", success,
                     f"Status: {status}" if not success else "")

    def test_business_authentication_security(self):
        """Test business endpoint security"""
        print("\n🔒 TESTING BUSINESS ENDPOINT SECURITY")
        
        # Test accessing business endpoints without token
        success, response, status, time_taken = self.make_request(
            'GET', 'products/my', expected_status=401
        )
        
        self.log_test("Business Endpoint Without Token", success,
                     f"Status: {status} - Should be 401" if not success else "", "security")
        
        # Test accessing business endpoints with customer token
        if self.customer_token:
            success, response, status, time_taken = self.make_request(
                'GET', 'products/my', token=self.customer_token, expected_status=403
            )
            
            self.log_test("Business Endpoint With Customer Token", success,
                         f"Status: {status} - Should be 403" if not success else "", "security")

    # ===== 3. ADMIN ENDPOINTS TESTING =====
    
    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        print("\n👑 TESTING ADMIN ENDPOINTS")
        
        if not self.admin_token:
            self.log_test("Admin Endpoints", False, "No admin token available", "critical")
            return
        
        # Test Get All Users
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/users', token=self.admin_token
        )
        
        if success and isinstance(response, list):
            self.log_test("Admin Get All Users", True)
            print(f"   Found {len(response)} users in system")
        else:
            self.log_test("Admin Get All Users", False,
                        f"Status: {status}, Response type: {type(response)}", "critical")
        
        # Test Get All Products
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/products', token=self.admin_token
        )
        
        self.log_test("Admin Get All Products", success,
                     f"Status: {status}" if not success else "")
        
        # Test Get All Orders
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/orders', token=self.admin_token
        )
        
        self.log_test("Admin Get All Orders", success,
                     f"Status: {status}" if not success else "")

    def test_kyc_management_system(self):
        """Test KYC management endpoints"""
        print("\n📋 TESTING KYC MANAGEMENT SYSTEM")
        
        if not self.admin_token:
            self.log_test("KYC Management", False, "No admin token available", "critical")
            return
        
        # Test Get Couriers for KYC
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/couriers/kyc', token=self.admin_token
        )
        
        if success and isinstance(response, list):
            self.log_test("Get Couriers for KYC", True)
            print(f"   Found {len(response)} couriers for KYC review")
            
            # Test KYC approval if we have a courier
            if len(response) > 0 and self.test_users.get('courier', {}).get('id'):
                courier_id = self.test_users['courier']['id']
                
                # Test KYC approval
                success, response, status, time_taken = self.make_request(
                    'PATCH', f'admin/couriers/{courier_id}/kyc?kyc_status=approved',
                    data={"notes": "Test approval"}, token=self.admin_token
                )
                
                self.log_test("KYC Courier Approval", success,
                             f"Status: {status}" if not success else "")
                
                # Test KYC rejection
                success, response, status, time_taken = self.make_request(
                    'PATCH', f'admin/couriers/{courier_id}/kyc?kyc_status=rejected',
                    data={"notes": "Test rejection reason"}, token=self.admin_token
                )
                
                self.log_test("KYC Courier Rejection with Notes", success,
                             f"Status: {status}" if not success else "")
        else:
            self.log_test("Get Couriers for KYC", False,
                        f"Status: {status}, Response type: {type(response)}", "critical")

    # ===== 4. ORDER MANAGEMENT TESTING =====
    
    def test_order_management_system(self):
        """Test order creation and management"""
        print("\n📦 TESTING ORDER MANAGEMENT SYSTEM")
        
        if not self.customer_token or not self.test_products:
            self.log_test("Order Management", False, 
                        "No customer token or products available", "critical")
            return
        
        # Create test order
        product = self.test_products[0]
        order_data = {
            "delivery_address": "Test Address, Istanbul",
            "delivery_lat": 41.0082,
            "delivery_lng": 28.9784,
            "items": [{
                "product_id": product['id'],
                "product_name": product['name'],
                "product_price": product['price'],
                "quantity": 2,
                "subtotal": product['price'] * 2
            }],
            "total_amount": product['price'] * 2,
            "notes": "Test order"
        }
        
        success, response, status, time_taken = self.make_request(
            'POST', 'orders', order_data, token=self.customer_token
        )
        
        if success and response.get('id'):
            self.test_orders.append(response)
            self.log_test("Order Creation", True)
            
            # Verify commission calculation (3%)
            expected_commission = order_data['total_amount'] * 0.03
            actual_commission = response.get('commission_amount', 0)
            if abs(expected_commission - actual_commission) < 0.01:
                self.log_test("Order Commission Calculation", True)
            else:
                self.log_test("Order Commission Calculation", False,
                            f"Expected {expected_commission}, got {actual_commission}", "critical")
        else:
            self.log_test("Order Creation", False,
                        f"Status: {status}, Response: {response}", "critical")
        
        # Test Get Customer Orders
        success, response, status, time_taken = self.make_request(
            'GET', 'orders', token=self.customer_token
        )
        
        self.log_test("Get Customer Orders", success,
                     f"Status: {status}" if not success else "")
        
        # Test Get Business Orders
        if self.business_token:
            success, response, status, time_taken = self.make_request(
                'GET', 'orders', token=self.business_token
            )
            
            self.log_test("Get Business Orders", success,
                         f"Status: {status}" if not success else "")

    def test_courier_order_acceptance(self):
        """Test courier order acceptance workflow"""
        print("\n🚴 TESTING COURIER ORDER ACCEPTANCE")
        
        if not self.courier_token or not self.test_orders:
            self.log_test("Courier Order Acceptance", False,
                        "No courier token or orders available", "critical")
            return
        
        # First approve courier KYC if admin token available
        if self.admin_token and self.test_users.get('courier', {}).get('id'):
            courier_id = self.test_users['courier']['id']
            self.make_request(
                'PATCH', f'admin/couriers/{courier_id}/kyc?kyc_status=approved',
                token=self.admin_token
            )
        
        # Test Get Nearby Orders
        success, response, status, time_taken = self.make_request(
            'GET', 'orders/nearby', token=self.courier_token
        )
        
        if success and isinstance(response, list):
            self.log_test("Get Nearby Orders", True)
            print(f"   Found {len(response)} nearby orders")
        else:
            self.log_test("Get Nearby Orders", False,
                        f"Status: {status}, Response type: {type(response)}", "critical")
        
        # Test Order Acceptance
        if self.test_orders:
            order_id = self.test_orders[0]['id']
            success, response, status, time_taken = self.make_request(
                'POST', f'orders/{order_id}/accept', token=self.courier_token
            )
            
            self.log_test("Order Acceptance", success,
                         f"Status: {status}" if not success else "")

    # ===== 5. FILE UPLOAD TESTING =====
    
    def test_file_upload_endpoints(self):
        """Test file upload functionality"""
        print("\n📁 TESTING FILE UPLOAD ENDPOINTS")
        
        # Test upload endpoint without file (should fail)
        success, response, status, time_taken = self.make_request(
            'POST', 'upload', expected_status=422
        )
        
        self.log_test("File Upload Without File", success,
                     f"Status: {status} - Should be 422" if not success else "")

    # ===== 6. SECURITY TESTING =====
    
    def test_jwt_token_validation(self):
        """Test JWT token validation and security"""
        print("\n🔐 TESTING JWT TOKEN VALIDATION")
        
        # Test with invalid token
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/users', token="invalid_token", expected_status=401
        )
        
        self.log_test("Invalid JWT Token Rejection", success,
                     f"Status: {status} - Should be 401" if not success else "", "security")
        
        # Test with expired token (simulate)
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/users', token="expired.token.here", expected_status=401
        )
        
        self.log_test("Expired JWT Token Rejection", success,
                     f"Status: {status} - Should be 401" if not success else "", "security")
        
        # Test admin endpoints with business token
        if self.business_token:
            success, response, status, time_taken = self.make_request(
                'GET', 'admin/users', token=self.business_token, expected_status=403
            )
            
            self.log_test("Admin Endpoint with Business Token", success,
                         f"Status: {status} - Should be 403" if not success else "", "security")

    def test_input_validation(self):
        """Test input validation and sanitization"""
        print("\n🛡️ TESTING INPUT VALIDATION")
        
        # Test business registration with invalid email
        success, response, status, time_taken = self.make_request(
            'POST', 'register/business',
            {
                "email": "invalid-email",
                "password": "test123",
                "business_name": "Test",
                "tax_number": "123",
                "address": "Test",
                "city": "Test",
                "business_category": "gida"
            },
            expected_status=422
        )
        
        self.log_test("Invalid Email Validation", success,
                     f"Status: {status} - Should be 422" if not success else "", "security")
        
        # Test SQL injection attempt
        success, response, status, time_taken = self.make_request(
            'POST', 'auth/login',
            {
                "email": "admin@test.com'; DROP TABLE users; --",
                "password": "6851"
            },
            expected_status=401
        )
        
        self.log_test("SQL Injection Protection", success,
                     f"Status: {status} - Should be 401" if not success else "", "security")

    # ===== 7. DATABASE CONNECTION TESTING =====
    
    def test_database_connectivity(self):
        """Test database connection and data consistency"""
        print("\n🗄️ TESTING DATABASE CONNECTIVITY")
        
        if not self.admin_token:
            self.log_test("Database Connectivity", False, "No admin token for testing", "critical")
            return
        
        # Test database read operations
        success, response, status, time_taken = self.make_request(
            'GET', 'admin/users', token=self.admin_token
        )
        
        if success and isinstance(response, list):
            self.log_test("Database Read Operations", True)
            
            # Check data consistency
            for user in response[:5]:  # Check first 5 users
                required_fields = ['id', 'email', 'created_at']
                missing_fields = [field for field in required_fields if field not in user]
                if missing_fields:
                    self.log_test("Database Data Consistency", False,
                                f"User missing fields: {missing_fields}", "critical")
                    break
            else:
                self.log_test("Database Data Consistency", True)
        else:
            self.log_test("Database Read Operations", False,
                        f"Status: {status}, Response type: {type(response)}", "critical")

    # ===== 8. PERFORMANCE TESTING =====
    
    def test_response_times(self):
        """Test API response times"""
        print("\n⚡ TESTING API RESPONSE TIMES")
        
        endpoints_to_test = [
            ('GET', 'businesses', None),
            ('POST', 'auth/login', {"email": "test@test.com", "password": "wrong"}, 401),
        ]
        
        if self.admin_token:
            endpoints_to_test.append(('GET', 'admin/users', None))
        
        for method, endpoint, data, *expected_status in endpoints_to_test:
            expected = expected_status[0] if expected_status else 200
            
            success, response, status, time_taken = self.make_request(
                method, endpoint, data, 
                token=self.admin_token if 'admin' in endpoint else None,
                expected_status=expected
            )
            
            if time_taken > 3.0:
                self.log_test(f"Response Time - {endpoint}", False,
                            f"Slow response: {time_taken:.2f}s", "performance")
            else:
                self.log_test(f"Response Time - {endpoint}", True)

    # ===== 9. ERROR HANDLING TESTING =====
    
    def test_error_handling(self):
        """Test error handling and status codes"""
        print("\n🚨 TESTING ERROR HANDLING")
        
        # Test 404 errors
        success, response, status, time_taken = self.make_request(
            'GET', 'nonexistent-endpoint', expected_status=404
        )
        
        self.log_test("404 Error Handling", success,
                     f"Status: {status} - Should be 404" if not success else "")
        
        # Test 405 Method Not Allowed
        success, response, status, time_taken = self.make_request(
            'DELETE', 'businesses', expected_status=405
        )
        
        self.log_test("405 Method Not Allowed", success,
                     f"Status: {status} - Should be 405" if not success else "")
        
        # Test malformed JSON
        try:
            url = f"{self.api_url}/auth/login"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data="invalid json", headers=headers, timeout=10)
            
            if response.status_code == 422 or response.status_code == 400:
                self.log_test("Malformed JSON Handling", True)
            else:
                self.log_test("Malformed JSON Handling", False,
                            f"Status: {response.status_code} - Should be 400/422")
        except Exception as e:
            self.log_test("Malformed JSON Handling", False, f"Exception: {str(e)}")

    # ===== 10. TURKISH CITIES INTEGRATION TESTING =====
    
    def test_turkish_cities_integration(self):
        """Test 81 Turkish cities integration"""
        print("\n🇹🇷 TESTING 81 TURKISH CITIES INTEGRATION")
        
        turkish_cities = [
            "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Gaziantep",
            "Konya", "Şanlıurfa", "Kayseri", "Eskişehir", "Diyarbakır", "Samsun"
        ]
        
        for i, city in enumerate(turkish_cities[:5]):  # Test first 5 cities
            business_data = {
                "email": f"city_test_{i}_{uuid.uuid4().hex[:6]}@test.com",
                "password": "test123",
                "business_name": f"Test Business {city}",
                "tax_number": f"{1000000000 + i}",
                "address": f"Test Address, {city}",
                "city": city,
                "business_category": "gida",
                "description": f"Test business in {city}"
            }
            
            success, response, status, time_taken = self.make_request(
                'POST', 'register/business', business_data
            )
            
            if success:
                user_data = response.get('user_data', {})
                stored_city = user_data.get('city')
                if stored_city == city:
                    self.log_test(f"Turkish City Registration - {city}", True)
                else:
                    self.log_test(f"Turkish City Registration - {city}", False,
                                f"City mismatch: expected {city}, got {stored_city}")
            else:
                self.log_test(f"Turkish City Registration - {city}", False,
                            f"Status: {status}")

    # ===== MAIN TEST EXECUTION =====
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 STARTING COMPREHENSIVE KURYECINI BACKEND TESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # 1. Authentication Tests
        self.test_admin_authentication()
        self.test_user_registration_endpoints()
        self.test_login_endpoints()
        
        # 2. Business Endpoints
        self.test_business_endpoints()
        self.test_business_authentication_security()
        
        # 3. Admin Endpoints
        self.test_admin_endpoints()
        self.test_kyc_management_system()
        
        # 4. Order Management
        self.test_order_management_system()
        self.test_courier_order_acceptance()
        
        # 5. File Upload
        self.test_file_upload_endpoints()
        
        # 6. Security Tests
        self.test_jwt_token_validation()
        self.test_input_validation()
        
        # 7. Database Tests
        self.test_database_connectivity()
        
        # 8. Performance Tests
        self.test_response_times()
        
        # 9. Error Handling
        self.test_error_handling()
        
        # 10. Turkish Cities Integration
        self.test_turkish_cities_integration()
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        return self.generate_comprehensive_report(total_time)

    def generate_comprehensive_report(self, total_time: float):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND TEST REPORT")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.2f} seconds")
        
        # Critical Issues
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   ❌ {issue['test']}: {issue['details']}")
        
        # Security Issues
        if self.security_issues:
            print(f"\n🔒 SECURITY ISSUES FOUND ({len(self.security_issues)}):")
            for issue in self.security_issues:
                print(f"   ⚠️  {issue['test']}: {issue['details']}")
        
        # Performance Issues
        if self.performance_issues:
            print(f"\n⚡ PERFORMANCE ISSUES FOUND ({len(self.performance_issues)}):")
            for issue in self.performance_issues:
                print(f"   🐌 {issue.get('endpoint', issue.get('test', 'Unknown'))}: {issue['details']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate < 80:
            print("   🔴 URGENT: Success rate below 80% - immediate attention required")
        elif success_rate < 95:
            print("   🟡 WARNING: Success rate below 95% - improvements needed")
        else:
            print("   🟢 GOOD: High success rate - system appears stable")
        
        if self.critical_issues:
            print("   🔧 Fix critical issues immediately - they may block core functionality")
        
        if self.security_issues:
            print("   🛡️  Address security vulnerabilities to prevent potential attacks")
        
        if self.performance_issues:
            print("   ⚡ Optimize slow endpoints to improve user experience")
        
        print("\n" + "=" * 80)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "critical_issues": len(self.critical_issues),
            "security_issues": len(self.security_issues),
            "performance_issues": len(self.performance_issues),
            "total_time": total_time
        }

def main():
    """Main execution function"""
    tester = KuryeciniBackendTester()
    tester.run_comprehensive_tests()
    
    # Return appropriate exit code based on test results
    if len(tester.critical_issues) > 0:
        return 1  # Critical issues found
    elif tester.tests_run > 0 and (tester.tests_passed / tester.tests_run * 100) < 80:
        return 1  # Low success rate
    else:
        return 0  # All good

if __name__ == "__main__":
    sys.exit(main())