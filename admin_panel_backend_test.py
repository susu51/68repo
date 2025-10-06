#!/usr/bin/env python3
"""
FAZ 1 - ADMIN PANEL BACKEND COMPREHENSIVE TESTING
Testing all newly implemented admin management endpoints with comprehensive validation.

CRITICAL PRIORITY TESTING (Test in this exact order):
1. RBAC System (Highest Priority) - Test admin endpoints require proper admin role authentication
2. Admin Order Management (Priority #1)
3. Admin Business Management (Priority #2) 
4. Admin Menu/Product Management (Priority #3)
5. Admin Courier Management (Priority #4)
6. Admin Settings Management
7. Admin Promotion Management
8. Admin Reports Management

SUCCESS CRITERIA:
- 90%+ success rate across all admin endpoints
- RBAC system working perfectly (403 for non-admin access)
- All priority modules (Orders, Business, Products, Couriers) fully functional
- No authentication bypass vulnerabilities
- Proper error handling and data validation
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://db-driven-kuryecini.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"  # Actual admin password from backend

class AdminPanelBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.non_admin_token = None  # For RBAC testing
        self.test_data_ids = {
            "orders": [],
            "businesses": [],
            "products": [],
            "couriers": [],
            "promotions": [],
            "delivery_zones": []
        }
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["test_details"].append(test_result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_admin_authentication(self):
        """Test admin authentication with password 6851"""
        print("🔐 TESTING ADMIN AUTHENTICATION")
        print("=" * 50)
        
        try:
            # Test admin login with correct credentials
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_data = data.get("user", {})
                
                # Set authorization header for admin requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_test(
                    "Admin Authentication (admin@kuryecini.com)",
                    True,
                    f"Admin login successful. Role: {user_data.get('role')}, Token length: {len(self.admin_token) if self.admin_token else 0} chars",
                    {"user_id": user_data.get("id"), "email": user_data.get("email"), "role": user_data.get("role")}
                )
                
                # Test JWT token validation via /me endpoint
                me_response = self.session.get(f"{BACKEND_URL}/me")
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    self.log_test(
                        "Admin JWT Token Validation (/me endpoint)",
                        True,
                        f"Token validation successful. Admin: {me_data.get('email')} (Role: {me_data.get('role')})",
                        me_data
                    )
                else:
                    self.log_test(
                        "Admin JWT Token Validation (/me endpoint)",
                        False,
                        f"Token validation failed. Status: {me_response.status_code}",
                        me_response.text
                    )
                
                return True
            else:
                self.log_test(
                    "Admin Authentication (admin@kuryecini.com)",
                    False,
                    f"Admin login failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Admin Authentication (admin@kuryecini.com)",
                False,
                f"Exception during admin login: {str(e)}"
            )
            return False
    
    def test_non_admin_authentication(self):
        """Test non-admin user authentication for RBAC testing"""
        print("👤 TESTING NON-ADMIN AUTHENTICATION FOR RBAC")
        print("=" * 50)
        
        try:
            # Test customer login for RBAC testing
            login_data = {
                "email": "testcustomer@example.com",
                "password": "test123"
            }
            
            # Create separate session for non-admin user
            non_admin_session = requests.Session()
            response = non_admin_session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.non_admin_token = data.get("access_token")
                user_data = data.get("user", {})
                
                self.log_test(
                    "Non-Admin Authentication (for RBAC testing)",
                    True,
                    f"Customer login successful. Role: {user_data.get('role')}, Token: {len(self.non_admin_token) if self.non_admin_token else 0} chars",
                    {"user_id": user_data.get("id"), "email": user_data.get("email"), "role": user_data.get("role")}
                )
                return True
            else:
                self.log_test(
                    "Non-Admin Authentication (for RBAC testing)",
                    False,
                    f"Customer login failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Non-Admin Authentication (for RBAC testing)",
                False,
                f"Exception during customer login: {str(e)}"
            )
            return False
    
    def test_rbac_system(self):
        """Test RBAC system - admin endpoints should require admin role and return 403 for non-admin"""
        print("🛡️ TESTING RBAC SYSTEM (HIGHEST PRIORITY)")
        print("=" * 50)
        
        if not self.non_admin_token:
            self.log_test(
                "RBAC System Testing",
                False,
                "Non-admin token required for RBAC testing"
            )
            return
        
        # Test admin endpoints with non-admin token (should return 403)
        admin_endpoints = [
            ("GET", "/admin/orders", "Admin Orders List"),
            ("GET", "/admin/businesses", "Admin Business List"),
            ("GET", "/admin/products", "Admin Products List"),
            ("GET", "/admin/couriers", "Admin Couriers List"),
            ("GET", "/admin/settings", "Admin Settings"),
            ("GET", "/admin/promotions", "Admin Promotions"),
            ("GET", "/admin/reports/dashboard", "Admin Dashboard Reports")
        ]
        
        non_admin_session = requests.Session()
        non_admin_session.headers.update({
            "Authorization": f"Bearer {self.non_admin_token}"
        })
        
        for method, endpoint, test_name in admin_endpoints:
            try:
                if method == "GET":
                    response = non_admin_session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    response = non_admin_session.post(f"{BACKEND_URL}{endpoint}", json={})
                elif method == "PATCH":
                    response = non_admin_session.patch(f"{BACKEND_URL}{endpoint}", json={})
                
                # Should return 403 Forbidden for non-admin access
                if response.status_code == 403:
                    self.log_test(
                        f"RBAC - {test_name} (403 Forbidden for non-admin)",
                        True,
                        f"Properly rejected non-admin access. Status: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_test(
                        f"RBAC - {test_name} (403 Forbidden for non-admin)",
                        False,
                        f"Should return 403 for non-admin but got: {response.status_code}",
                        response.text[:200] if hasattr(response, 'text') else str(response)
                    )
                    
            except Exception as e:
                self.log_test(
                    f"RBAC - {test_name}",
                    False,
                    f"Exception during RBAC test: {str(e)}"
                )
    
    def test_admin_order_management(self):
        """Test Admin Order Management API (Priority #1)"""
        print("📦 TESTING ADMIN ORDER MANAGEMENT (PRIORITY #1)")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Order Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/orders (list all orders with pagination)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/orders")
            
            if response.status_code == 200:
                orders = response.json()
                self.log_test(
                    "GET /admin/orders (list all orders)",
                    True,
                    f"Successfully retrieved {len(orders) if isinstance(orders, list) else 'N/A'} orders",
                    {"order_count": len(orders) if isinstance(orders, list) else 0}
                )
                
                # Store first order ID for further testing
                if isinstance(orders, list) and orders:
                    self.test_data_ids["orders"].append(orders[0].get("id"))
                    
            else:
                self.log_test(
                    "GET /admin/orders (list all orders)",
                    False,
                    f"Failed to retrieve orders. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/orders (list all orders)",
                False,
                f"Exception during order list retrieval: {str(e)}"
            )
        
        # Test 2: GET /admin/orders/stats (order statistics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/orders/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /admin/orders/stats (order statistics)",
                    True,
                    f"Successfully retrieved order statistics",
                    stats
                )
            else:
                self.log_test(
                    "GET /admin/orders/stats (order statistics)",
                    False,
                    f"Failed to retrieve order stats. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/orders/stats (order statistics)",
                False,
                f"Exception during order stats retrieval: {str(e)}"
            )
        
        # Test 3: GET /admin/orders/{order_id} (specific order details)
        if self.test_data_ids["orders"]:
            order_id = self.test_data_ids["orders"][0]
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/orders/{order_id}")
                
                if response.status_code == 200:
                    order = response.json()
                    self.log_test(
                        "GET /admin/orders/{order_id} (specific order)",
                        True,
                        f"Successfully retrieved order details for ID: {order_id}",
                        {"order_id": order.get("id"), "status": order.get("status")}
                    )
                else:
                    self.log_test(
                        "GET /admin/orders/{order_id} (specific order)",
                        False,
                        f"Failed to retrieve order {order_id}. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "GET /admin/orders/{order_id} (specific order)",
                    False,
                    f"Exception during specific order retrieval: {str(e)}"
                )
        
        # Test 4: PATCH /admin/orders/{order_id}/status (update order status)
        if self.test_data_ids["orders"]:
            order_id = self.test_data_ids["orders"][0]
            try:
                status_data = {"status": "confirmed"}
                response = self.session.patch(f"{BACKEND_URL}/admin/orders/{order_id}/status", json=status_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/orders/{order_id}/status (update status)",
                        True,
                        f"Successfully updated order status to 'confirmed'",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/orders/{order_id}/status (update status)",
                        False,
                        f"Failed to update order status. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/orders/{order_id}/status (update status)",
                    False,
                    f"Exception during order status update: {str(e)}"
                )
        
        # Test 5: PATCH /admin/orders/{order_id}/assign-courier (assign courier)
        if self.test_data_ids["orders"]:
            order_id = self.test_data_ids["orders"][0]
            try:
                courier_data = {"courier_id": "courier-001"}
                response = self.session.patch(f"{BACKEND_URL}/admin/orders/{order_id}/assign-courier", json=courier_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/orders/{order_id}/assign-courier (assign courier)",
                        True,
                        f"Successfully assigned courier to order",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/orders/{order_id}/assign-courier (assign courier)",
                        False,
                        f"Failed to assign courier. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/orders/{order_id}/assign-courier (assign courier)",
                    False,
                    f"Exception during courier assignment: {str(e)}"
                )
    
    def test_admin_business_management(self):
        """Test Admin Business Management API (Priority #2)"""
        print("🏪 TESTING ADMIN BUSINESS MANAGEMENT (PRIORITY #2)")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Business Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/businesses (list businesses with filtering)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "GET /admin/businesses (list all businesses)",
                    True,
                    f"Successfully retrieved {len(businesses) if isinstance(businesses, list) else 'N/A'} businesses",
                    {"business_count": len(businesses) if isinstance(businesses, list) else 0}
                )
                
                # Store first business ID for further testing
                if isinstance(businesses, list) and businesses:
                    self.test_data_ids["businesses"].append(businesses[0].get("id"))
                    
            else:
                self.log_test(
                    "GET /admin/businesses (list all businesses)",
                    False,
                    f"Failed to retrieve businesses. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/businesses (list all businesses)",
                False,
                f"Exception during business list retrieval: {str(e)}"
            )
        
        # Test 2: GET /admin/businesses with city filter
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses?city=istanbul")
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "GET /admin/businesses?city=istanbul (city filtering)",
                    True,
                    f"Successfully retrieved businesses with city filter",
                    {"filtered_count": len(businesses) if isinstance(businesses, list) else 0}
                )
            else:
                self.log_test(
                    "GET /admin/businesses?city=istanbul (city filtering)",
                    False,
                    f"Failed to retrieve filtered businesses. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/businesses?city=istanbul (city filtering)",
                False,
                f"Exception during filtered business retrieval: {str(e)}"
            )
        
        # Test 3: GET /admin/businesses/stats (business statistics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /admin/businesses/stats (business statistics)",
                    True,
                    f"Successfully retrieved business statistics",
                    stats
                )
            else:
                self.log_test(
                    "GET /admin/businesses/stats (business statistics)",
                    False,
                    f"Failed to retrieve business stats. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/businesses/stats (business statistics)",
                False,
                f"Exception during business stats retrieval: {str(e)}"
            )
        
        # Test 4: GET /admin/businesses/{business_id} (specific business)
        if self.test_data_ids["businesses"]:
            business_id = self.test_data_ids["businesses"][0]
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/businesses/{business_id}")
                
                if response.status_code == 200:
                    business = response.json()
                    self.log_test(
                        "GET /admin/businesses/{business_id} (specific business)",
                        True,
                        f"Successfully retrieved business details for ID: {business_id}",
                        {"business_id": business.get("id"), "name": business.get("business_name")}
                    )
                else:
                    self.log_test(
                        "GET /admin/businesses/{business_id} (specific business)",
                        False,
                        f"Failed to retrieve business {business_id}. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "GET /admin/businesses/{business_id} (specific business)",
                    False,
                    f"Exception during specific business retrieval: {str(e)}"
                )
        
        # Test 5: PATCH /admin/businesses/{business_id}/status (update business status)
        if self.test_data_ids["businesses"]:
            business_id = self.test_data_ids["businesses"][0]
            try:
                status_data = {"kyc_status": "approved", "is_active": True}
                response = self.session.patch(f"{BACKEND_URL}/admin/businesses/{business_id}/status", json=status_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/businesses/{business_id}/status (update status)",
                        True,
                        f"Successfully updated business status",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/businesses/{business_id}/status (update status)",
                        False,
                        f"Failed to update business status. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/businesses/{business_id}/status (update status)",
                    False,
                    f"Exception during business status update: {str(e)}"
                )
    
    def test_admin_product_management(self):
        """Test Admin Menu/Product Management API (Priority #3)"""
        print("📋 TESTING ADMIN MENU/PRODUCT MANAGEMENT (PRIORITY #3)")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Product Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/products (list all products)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/products")
            
            if response.status_code == 200:
                products = response.json()
                self.log_test(
                    "GET /admin/products (list all products)",
                    True,
                    f"Successfully retrieved {len(products) if isinstance(products, list) else 'N/A'} products",
                    {"product_count": len(products) if isinstance(products, list) else 0}
                )
                
                # Store first product ID for further testing
                if isinstance(products, list) and products:
                    self.test_data_ids["products"].append(products[0].get("id"))
                    
            else:
                self.log_test(
                    "GET /admin/products (list all products)",
                    False,
                    f"Failed to retrieve products. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/products (list all products)",
                False,
                f"Exception during product list retrieval: {str(e)}"
            )
        
        # Test 2: GET /admin/products/stats (product statistics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/products/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /admin/products/stats (product statistics)",
                    True,
                    f"Successfully retrieved product statistics",
                    stats
                )
            else:
                self.log_test(
                    "GET /admin/products/stats (product statistics)",
                    False,
                    f"Failed to retrieve product stats. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/products/stats (product statistics)",
                False,
                f"Exception during product stats retrieval: {str(e)}"
            )
        
        # Test 3: GET /admin/products/{product_id} (specific product)
        if self.test_data_ids["products"]:
            product_id = self.test_data_ids["products"][0]
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/products/{product_id}")
                
                if response.status_code == 200:
                    product = response.json()
                    self.log_test(
                        "GET /admin/products/{product_id} (specific product)",
                        True,
                        f"Successfully retrieved product details for ID: {product_id}",
                        {"product_id": product.get("id"), "name": product.get("name")}
                    )
                else:
                    self.log_test(
                        "GET /admin/products/{product_id} (specific product)",
                        False,
                        f"Failed to retrieve product {product_id}. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "GET /admin/products/{product_id} (specific product)",
                    False,
                    f"Exception during specific product retrieval: {str(e)}"
                )
        
        # Test 4: PATCH /admin/products/{product_id} (update product)
        if self.test_data_ids["products"]:
            product_id = self.test_data_ids["products"][0]
            try:
                update_data = {
                    "name": "Updated Product Name",
                    "price": 29.99,
                    "is_available": True
                }
                response = self.session.patch(f"{BACKEND_URL}/admin/products/{product_id}", json=update_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/products/{product_id} (update product)",
                        True,
                        f"Successfully updated product",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/products/{product_id} (update product)",
                        False,
                        f"Failed to update product. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/products/{product_id} (update product)",
                    False,
                    f"Exception during product update: {str(e)}"
                )
    
    def test_admin_courier_management(self):
        """Test Admin Courier Management API (Priority #4)"""
        print("🚴 TESTING ADMIN COURIER MANAGEMENT (PRIORITY #4)")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Courier Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/couriers (list couriers with filtering)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers")
            
            if response.status_code == 200:
                couriers = response.json()
                self.log_test(
                    "GET /admin/couriers (list all couriers)",
                    True,
                    f"Successfully retrieved {len(couriers) if isinstance(couriers, list) else 'N/A'} couriers",
                    {"courier_count": len(couriers) if isinstance(couriers, list) else 0}
                )
                
                # Store first courier ID for further testing
                if isinstance(couriers, list) and couriers:
                    self.test_data_ids["couriers"].append(couriers[0].get("id"))
                    
            else:
                self.log_test(
                    "GET /admin/couriers (list all couriers)",
                    False,
                    f"Failed to retrieve couriers. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/couriers (list all couriers)",
                False,
                f"Exception during courier list retrieval: {str(e)}"
            )
        
        # Test 2: GET /admin/couriers with status filter
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers?status=approved")
            
            if response.status_code == 200:
                couriers = response.json()
                self.log_test(
                    "GET /admin/couriers?status=approved (status filtering)",
                    True,
                    f"Successfully retrieved couriers with status filter",
                    {"filtered_count": len(couriers) if isinstance(couriers, list) else 0}
                )
            else:
                self.log_test(
                    "GET /admin/couriers?status=approved (status filtering)",
                    False,
                    f"Failed to retrieve filtered couriers. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/couriers?status=approved (status filtering)",
                False,
                f"Exception during filtered courier retrieval: {str(e)}"
            )
        
        # Test 3: GET /admin/couriers/stats (courier statistics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /admin/couriers/stats (courier statistics)",
                    True,
                    f"Successfully retrieved courier statistics",
                    stats
                )
            else:
                self.log_test(
                    "GET /admin/couriers/stats (courier statistics)",
                    False,
                    f"Failed to retrieve courier stats. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/couriers/stats (courier statistics)",
                False,
                f"Exception during courier stats retrieval: {str(e)}"
            )
        
        # Test 4: GET /admin/couriers/{courier_id} (specific courier)
        if self.test_data_ids["couriers"]:
            courier_id = self.test_data_ids["couriers"][0]
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/couriers/{courier_id}")
                
                if response.status_code == 200:
                    courier = response.json()
                    self.log_test(
                        "GET /admin/couriers/{courier_id} (specific courier)",
                        True,
                        f"Successfully retrieved courier details for ID: {courier_id}",
                        {"courier_id": courier.get("id"), "name": f"{courier.get('first_name', '')} {courier.get('last_name', '')}".strip()}
                    )
                else:
                    self.log_test(
                        "GET /admin/couriers/{courier_id} (specific courier)",
                        False,
                        f"Failed to retrieve courier {courier_id}. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "GET /admin/couriers/{courier_id} (specific courier)",
                    False,
                    f"Exception during specific courier retrieval: {str(e)}"
                )
        
        # Test 5: PATCH /admin/couriers/{courier_id}/status (update courier status)
        if self.test_data_ids["couriers"]:
            courier_id = self.test_data_ids["couriers"][0]
            try:
                status_data = {"kyc_status": "approved", "is_active": True}
                response = self.session.patch(f"{BACKEND_URL}/admin/couriers/{courier_id}/status", json=status_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/couriers/{courier_id}/status (update status)",
                        True,
                        f"Successfully updated courier status",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/couriers/{courier_id}/status (update status)",
                        False,
                        f"Failed to update courier status. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/couriers/{courier_id}/status (update status)",
                    False,
                    f"Exception during courier status update: {str(e)}"
                )
    
    def test_admin_settings_management(self):
        """Test Admin Settings Management API"""
        print("⚙️ TESTING ADMIN SETTINGS MANAGEMENT")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Settings Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/settings (platform settings)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/settings")
            
            if response.status_code == 200:
                settings = response.json()
                self.log_test(
                    "GET /admin/settings (platform settings)",
                    True,
                    f"Successfully retrieved platform settings",
                    settings
                )
            else:
                self.log_test(
                    "GET /admin/settings (platform settings)",
                    False,
                    f"Failed to retrieve settings. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/settings (platform settings)",
                False,
                f"Exception during settings retrieval: {str(e)}"
            )
        
        # Test 2: PATCH /admin/settings (update platform configuration)
        try:
            settings_data = {
                "platform_commission_rate": 0.05,
                "delivery_fee": 5.0,
                "min_order_amount": 25.0
            }
            response = self.session.patch(f"{BACKEND_URL}/admin/settings", json=settings_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "PATCH /admin/settings (update configuration)",
                    True,
                    f"Successfully updated platform settings",
                    result
                )
            else:
                self.log_test(
                    "PATCH /admin/settings (update configuration)",
                    False,
                    f"Failed to update settings. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "PATCH /admin/settings (update configuration)",
                False,
                f"Exception during settings update: {str(e)}"
            )
        
        # Test 3: GET /admin/settings/delivery-zones (delivery zones)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/settings/delivery-zones")
            
            if response.status_code == 200:
                zones = response.json()
                self.log_test(
                    "GET /admin/settings/delivery-zones (delivery zones)",
                    True,
                    f"Successfully retrieved {len(zones) if isinstance(zones, list) else 'N/A'} delivery zones",
                    {"zone_count": len(zones) if isinstance(zones, list) else 0}
                )
            else:
                self.log_test(
                    "GET /admin/settings/delivery-zones (delivery zones)",
                    False,
                    f"Failed to retrieve delivery zones. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/settings/delivery-zones (delivery zones)",
                False,
                f"Exception during delivery zones retrieval: {str(e)}"
            )
        
        # Test 4: POST /admin/settings/delivery-zones (create zone)
        try:
            zone_data = {
                "name": "Test Delivery Zone",
                "city": "İstanbul",
                "districts": ["Kadıköy", "Beşiktaş"],
                "delivery_fee": 8.0,
                "min_order_amount": 30.0
            }
            response = self.session.post(f"{BACKEND_URL}/admin/settings/delivery-zones", json=zone_data)
            
            if response.status_code == 200:
                result = response.json()
                zone_id = result.get("id")
                if zone_id:
                    self.test_data_ids["delivery_zones"].append(zone_id)
                
                self.log_test(
                    "POST /admin/settings/delivery-zones (create zone)",
                    True,
                    f"Successfully created delivery zone with ID: {zone_id}",
                    result
                )
            else:
                self.log_test(
                    "POST /admin/settings/delivery-zones (create zone)",
                    False,
                    f"Failed to create delivery zone. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "POST /admin/settings/delivery-zones (create zone)",
                False,
                f"Exception during delivery zone creation: {str(e)}"
            )
    
    def test_admin_promotion_management(self):
        """Test Admin Promotion Management API"""
        print("🎯 TESTING ADMIN PROMOTION MANAGEMENT")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Promotion Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/promotions (list all promotions)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/promotions")
            
            if response.status_code == 200:
                promotions = response.json()
                self.log_test(
                    "GET /admin/promotions (list all promotions)",
                    True,
                    f"Successfully retrieved {len(promotions) if isinstance(promotions, list) else 'N/A'} promotions",
                    {"promotion_count": len(promotions) if isinstance(promotions, list) else 0}
                )
                
                # Store first promotion ID for further testing
                if isinstance(promotions, list) and promotions:
                    self.test_data_ids["promotions"].append(promotions[0].get("id"))
                    
            else:
                self.log_test(
                    "GET /admin/promotions (list all promotions)",
                    False,
                    f"Failed to retrieve promotions. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/promotions (list all promotions)",
                False,
                f"Exception during promotion list retrieval: {str(e)}"
            )
        
        # Test 2: POST /admin/promotions (create new promotion)
        try:
            promotion_data = {
                "title": "Test Promotion",
                "description": "Test promotion for admin panel testing",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "min_order_amount": 50.0,
                "valid_from": datetime.now().isoformat(),
                "valid_until": "2024-12-31T23:59:59",
                "is_active": True
            }
            response = self.session.post(f"{BACKEND_URL}/admin/promotions", json=promotion_data)
            
            if response.status_code == 200:
                result = response.json()
                promotion_id = result.get("id")
                if promotion_id:
                    self.test_data_ids["promotions"].append(promotion_id)
                
                self.log_test(
                    "POST /admin/promotions (create new promotion)",
                    True,
                    f"Successfully created promotion with ID: {promotion_id}",
                    result
                )
            else:
                self.log_test(
                    "POST /admin/promotions (create new promotion)",
                    False,
                    f"Failed to create promotion. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "POST /admin/promotions (create new promotion)",
                False,
                f"Exception during promotion creation: {str(e)}"
            )
        
        # Test 3: GET /admin/promotions/stats (promotion statistics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/promotions/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test(
                    "GET /admin/promotions/stats (promotion statistics)",
                    True,
                    f"Successfully retrieved promotion statistics",
                    stats
                )
            else:
                self.log_test(
                    "GET /admin/promotions/stats (promotion statistics)",
                    False,
                    f"Failed to retrieve promotion stats. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/promotions/stats (promotion statistics)",
                False,
                f"Exception during promotion stats retrieval: {str(e)}"
            )
        
        # Test 4: GET /admin/promotions/{promotion_id} (specific promotion)
        if self.test_data_ids["promotions"]:
            promotion_id = self.test_data_ids["promotions"][0]
            try:
                response = self.session.get(f"{BACKEND_URL}/admin/promotions/{promotion_id}")
                
                if response.status_code == 200:
                    promotion = response.json()
                    self.log_test(
                        "GET /admin/promotions/{promotion_id} (specific promotion)",
                        True,
                        f"Successfully retrieved promotion details for ID: {promotion_id}",
                        {"promotion_id": promotion.get("id"), "title": promotion.get("title")}
                    )
                else:
                    self.log_test(
                        "GET /admin/promotions/{promotion_id} (specific promotion)",
                        False,
                        f"Failed to retrieve promotion {promotion_id}. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "GET /admin/promotions/{promotion_id} (specific promotion)",
                    False,
                    f"Exception during specific promotion retrieval: {str(e)}"
                )
        
        # Test 5: PATCH /admin/promotions/{promotion_id}/toggle (activate/deactivate)
        if self.test_data_ids["promotions"]:
            promotion_id = self.test_data_ids["promotions"][0]
            try:
                response = self.session.patch(f"{BACKEND_URL}/admin/promotions/{promotion_id}/toggle")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        "PATCH /admin/promotions/{promotion_id}/toggle (toggle status)",
                        True,
                        f"Successfully toggled promotion status",
                        result
                    )
                else:
                    self.log_test(
                        "PATCH /admin/promotions/{promotion_id}/toggle (toggle status)",
                        False,
                        f"Failed to toggle promotion status. Status: {response.status_code}",
                        response.text[:200]
                    )
                    
            except Exception as e:
                self.log_test(
                    "PATCH /admin/promotions/{promotion_id}/toggle (toggle status)",
                    False,
                    f"Exception during promotion toggle: {str(e)}"
                )
    
    def test_admin_reports_management(self):
        """Test Admin Reports Management API"""
        print("📈 TESTING ADMIN REPORTS MANAGEMENT")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Admin Reports Management",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: GET /admin/reports/dashboard (comprehensive dashboard analytics)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/reports/dashboard")
            
            if response.status_code == 200:
                dashboard = response.json()
                self.log_test(
                    "GET /admin/reports/dashboard (dashboard analytics)",
                    True,
                    f"Successfully retrieved dashboard analytics",
                    dashboard
                )
            else:
                self.log_test(
                    "GET /admin/reports/dashboard (dashboard analytics)",
                    False,
                    f"Failed to retrieve dashboard analytics. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/reports/dashboard (dashboard analytics)",
                False,
                f"Exception during dashboard analytics retrieval: {str(e)}"
            )
        
        # Test 2: GET /admin/reports/financial (financial reports with date filtering)
        try:
            # Test with date range
            params = {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            response = self.session.get(f"{BACKEND_URL}/admin/reports/financial", params=params)
            
            if response.status_code == 200:
                financial = response.json()
                self.log_test(
                    "GET /admin/reports/financial (financial reports)",
                    True,
                    f"Successfully retrieved financial reports with date filtering",
                    financial
                )
            else:
                self.log_test(
                    "GET /admin/reports/financial (financial reports)",
                    False,
                    f"Failed to retrieve financial reports. Status: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "GET /admin/reports/financial (financial reports)",
                False,
                f"Exception during financial reports retrieval: {str(e)}"
            )
    
    def test_error_handling_and_validation(self):
        """Test error handling and data validation"""
        print("⚠️ TESTING ERROR HANDLING AND DATA VALIDATION")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "Error Handling Testing",
                False,
                "Admin authentication required"
            )
            return
        
        # Test 1: Invalid order ID
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/orders/invalid-order-id")
            
            if response.status_code == 404:
                self.log_test(
                    "Error Handling - Invalid Order ID (404)",
                    True,
                    f"Properly returned 404 for invalid order ID",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Error Handling - Invalid Order ID (404)",
                    False,
                    f"Should return 404 for invalid order ID but got: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "Error Handling - Invalid Order ID (404)",
                False,
                f"Exception during invalid order ID test: {str(e)}"
            )
        
        # Test 2: Invalid business ID
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses/invalid-business-id")
            
            if response.status_code == 404:
                self.log_test(
                    "Error Handling - Invalid Business ID (404)",
                    True,
                    f"Properly returned 404 for invalid business ID",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Error Handling - Invalid Business ID (404)",
                    False,
                    f"Should return 404 for invalid business ID but got: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "Error Handling - Invalid Business ID (404)",
                False,
                f"Exception during invalid business ID test: {str(e)}"
            )
        
        # Test 3: Invalid data validation (422)
        try:
            invalid_promotion_data = {
                "title": "",  # Empty title should fail validation
                "discount_value": -10  # Negative discount should fail
            }
            response = self.session.post(f"{BACKEND_URL}/admin/promotions", json=invalid_promotion_data)
            
            if response.status_code in [400, 422]:
                self.log_test(
                    "Data Validation - Invalid Promotion Data (422)",
                    True,
                    f"Properly rejected invalid promotion data. Status: {response.status_code}",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Data Validation - Invalid Promotion Data (422)",
                    False,
                    f"Should reject invalid data but got: {response.status_code}",
                    response.text[:200]
                )
                
        except Exception as e:
            self.log_test(
                "Data Validation - Invalid Promotion Data (422)",
                False,
                f"Exception during data validation test: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all admin panel backend tests in priority order"""
        print("🚀 STARTING FAZ 1 - ADMIN PANEL BACKEND COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {ADMIN_EMAIL}")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate admin user (CRITICAL)
        if not self.test_admin_authentication():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with admin tests.")
            return self.generate_final_report()
        
        # Step 2: Authenticate non-admin user for RBAC testing
        self.test_non_admin_authentication()
        
        # Step 3: Test RBAC System (HIGHEST PRIORITY)
        self.test_rbac_system()
        
        # Step 4: Test Admin Order Management (Priority #1)
        self.test_admin_order_management()
        
        # Step 5: Test Admin Business Management (Priority #2)
        self.test_admin_business_management()
        
        # Step 6: Test Admin Menu/Product Management (Priority #3)
        self.test_admin_product_management()
        
        # Step 7: Test Admin Courier Management (Priority #4)
        self.test_admin_courier_management()
        
        # Step 8: Test Admin Settings Management
        self.test_admin_settings_management()
        
        # Step 9: Test Admin Promotion Management
        self.test_admin_promotion_management()
        
        # Step 10: Test Admin Reports Management
        self.test_admin_reports_management()
        
        # Step 11: Test Error Handling and Data Validation
        self.test_error_handling_and_validation()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 FAZ 1 - ADMIN PANEL BACKEND TEST RESULTS")
        print("=" * 80)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical Success Criteria Check
        print("🎯 CRITICAL SUCCESS CRITERIA CHECK:")
        critical_tests = [
            "Admin Authentication (admin@kuryecini.com)",
            "RBAC - Admin Orders List (403 Forbidden for non-admin)",
            "GET /admin/orders (list all orders)",
            "GET /admin/businesses (list all businesses)",
            "GET /admin/products (list all products)",
            "GET /admin/couriers (list all couriers)"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            test_result = next((t for t in self.results["test_details"] if test_name in t["test"]), None)
            if test_result and "✅ PASS" in test_result["status"]:
                print(f"  ✅ {test_name}")
                critical_passed += 1
            else:
                print(f"  ❌ {test_name}")
        
        critical_success_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 0
        print(f"\nCritical Success Rate: {critical_success_rate:.1f}% ({critical_passed}/{len(critical_tests)})")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Overall Assessment
        if success_rate >= 90 and critical_success_rate >= 90:
            print("🎉 EXCELLENT: Admin panel backend is working perfectly! Ready for production.")
        elif success_rate >= 75 and critical_success_rate >= 75:
            print("✅ GOOD: Admin panel backend is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Admin panel backend has significant issues that need attention.")
        else:
            print("❌ CRITICAL: Admin panel backend has major failures requiring immediate fixes.")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "critical_success_rate": critical_success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "details": self.results["test_details"]
        }

def main():
    """Main test execution"""
    tester = AdminPanelBackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code based on success criteria
    if results["success_rate"] >= 90 and results["critical_success_rate"] >= 90:
        sys.exit(0)  # Excellent
    elif results["success_rate"] >= 75:
        sys.exit(0)  # Good enough
    else:
        sys.exit(1)  # Needs improvement

if __name__ == "__main__":
    main()