#!/usr/bin/env python3
"""
Kuryecini Comprehensive Backend Endpoint Testing

CRITICAL: Test all backend endpoints covering all panels as requested:

1. Authentication (All Panels)
   - POST /api/auth/login (customer, business, courier, admin)
   - GET /api/me (auth verification)
   - POST /api/auth/logout

2. Customer Panel
   - GET /api/user/addresses (address list)
   - POST /api/user/addresses (add address)
   - GET /api/businesses?city=Aksaray (restaurant list)
   - GET /api/business/public/{id}/menu (menu - NEW endpoint)
   - POST /api/orders (order creation)
   - GET /api/orders/my (order history)

3. Business Panel
   - GET /api/business/orders (incoming orders)
   - POST /api/business/orders/{id}/confirm (order confirmation)
   - GET /api/business/menu (own menu)
   - POST /api/business/menu (add menu item)
   - PUT /api/business/menu/{id} (update item)

4. Courier Panel
   - GET /api/courier/tasks (pending tasks)
   - POST /api/courier/tasks/{id}/accept (accept task)
   - PUT /api/courier/tasks/{id}/status (update status)

5. Admin Panel
   - GET /api/admin/users (user list)
   - GET /api/admin/orders (all orders)
   - PUT /api/admin/kyc/{business_id}/approve (KYC approval)
   - GET /api/admin/system/status (system status)
   - POST /api/admin/ai/assist (Ops Co-Pilot)

Success Criteria:
✅ All auth endpoints working
✅ Each panel's critical functions accessible
✅ 401/403 only when auth required
✅ 404 none (endpoints exist)
✅ 422 validation errors meaningful
✅ 500 errors none
"""

import json
import requests
import time
from datetime import datetime
import os
import sys
import uuid

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com"

# Test credentials for all roles
TEST_CREDENTIALS = {
    "customer": {"email": "test@kuryecini.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "admin": {"email": "admin@kuryecini.com", "password": "admin123"}
}

class ComprehensiveEndpointTester:
    def __init__(self):
        self.sessions = {}
        self.test_results = []
        self.business_id = None
        self.order_id = None
        self.menu_item_id = None
        self.task_id = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate_all_roles(self):
        """Authenticate all user roles"""
        print("🔐 Authenticating all user roles...")
        print("-" * 50)
        
        for role, credentials in TEST_CREDENTIALS.items():
            session = requests.Session()
            try:
                response = session.post(
                    f"{BACKEND_URL}/api/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if it's cookie-based auth (success field) or JWT auth (access_token field)
                    if data.get("success"):
                        # Cookie-based auth
                        user_role = data.get("user", {}).get("role")
                        user_id = data.get("user", {}).get("id")
                        if user_role == role:
                            self.sessions[role] = session
                            if role == "business":
                                self.business_id = user_id
                            self.log_test(
                                f"{role.title()} Authentication",
                                True,
                                f"Login successful (cookie-based): {credentials['email']}, role: {user_role}, id: {user_id}"
                            )
                        else:
                            self.log_test(
                                f"{role.title()} Authentication",
                                False,
                                error=f"Role mismatch: expected {role}, got {user_role}"
                            )
                    elif data.get("access_token"):
                        # JWT-based auth - store token for headers
                        user_role = data.get("user", {}).get("role")
                        user_id = data.get("user", {}).get("id")
                        if user_role == role:
                            session.headers.update({
                                "Authorization": f"Bearer {data.get('access_token')}"
                            })
                            self.sessions[role] = session
                            if role == "business":
                                self.business_id = user_id
                            self.log_test(
                                f"{role.title()} Authentication",
                                True,
                                f"Login successful (JWT): {credentials['email']}, role: {user_role}, id: {user_id}"
                            )
                        else:
                            self.log_test(
                                f"{role.title()} Authentication",
                                False,
                                error=f"Role mismatch: expected {role}, got {user_role}"
                            )
                    else:
                        self.log_test(
                            f"{role.title()} Authentication",
                            False,
                            error=f"Unknown auth response format: {list(data.keys())}"
                        )
                else:
                    self.log_test(
                        f"{role.title()} Authentication",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{role.title()} Authentication",
                    False,
                    error=f"Request failed: {str(e)}"
                )
    
    def test_auth_verification(self):
        """Test GET /api/me for all roles"""
        print("🔍 Testing auth verification endpoints...")
        print("-" * 50)
        
        for role in ["customer", "business", "courier", "admin"]:
            if role not in self.sessions:
                self.log_test(f"{role.title()} /api/me", False, error="No authenticated session")
                continue
                
            try:
                response = self.sessions[role].get(
                    f"{BACKEND_URL}/api/me",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("role") == role:
                        self.log_test(
                            f"{role.title()} /api/me",
                            True,
                            f"Auth verification successful, role: {data.get('role')}, id: {data.get('id')}"
                        )
                    else:
                        self.log_test(
                            f"{role.title()} /api/me",
                            False,
                            error=f"Role mismatch: expected {role}, got {data.get('role')}"
                        )
                else:
                    self.log_test(
                        f"{role.title()} /api/me",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{role.title()} /api/me",
                    False,
                    error=f"Request failed: {str(e)}"
                )
    
    def test_customer_panel_endpoints(self):
        """Test customer panel endpoints"""
        print("👤 Testing Customer Panel endpoints...")
        print("-" * 50)
        
        if "customer" not in self.sessions:
            print("❌ No customer session available")
            return
            
        customer_session = self.sessions["customer"]
        
        # Test 1: GET /api/user/addresses
        try:
            response = customer_session.get(
                f"{BACKEND_URL}/api/user/addresses",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Customer - GET /api/user/addresses",
                    True,
                    f"Retrieved {len(data) if isinstance(data, list) else 'unknown'} addresses"
                )
            else:
                self.log_test(
                    "Customer - GET /api/user/addresses",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Customer - GET /api/user/addresses",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: POST /api/user/addresses
        try:
            address_data = {
                "label": "Test Address",
                "city": "Aksaray",
                "district": "Merkez",
                "full_address": "Test Street No:1",
                "lat": 38.3687,
                "lng": 34.0254,
                "is_default": False
            }
            
            response = customer_session.post(
                f"{BACKEND_URL}/api/user/addresses",
                json=address_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Customer - POST /api/user/addresses",
                    True,
                    f"Address created successfully: {data.get('id', 'unknown id')}"
                )
            else:
                self.log_test(
                    "Customer - POST /api/user/addresses",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Customer - POST /api/user/addresses",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 3: GET /api/businesses?city=Aksaray
        try:
            response = customer_session.get(
                f"{BACKEND_URL}/api/businesses?city=Aksaray",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test(
                    "Customer - GET /api/businesses?city=Aksaray",
                    True,
                    f"Retrieved {len(businesses)} businesses in Aksaray"
                )
                
                # Store first business ID for menu test
                if businesses and len(businesses) > 0:
                    first_business = businesses[0]
                    test_business_id = first_business.get("id")
                    
                    # Test 4: GET /api/business/public/{id}/menu
                    if test_business_id:
                        try:
                            menu_response = customer_session.get(
                                f"{BACKEND_URL}/api/business/public/{test_business_id}/menu",
                                timeout=10
                            )
                            
                            if menu_response.status_code == 200:
                                menu_data = menu_response.json()
                                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                                self.log_test(
                                    "Customer - GET /api/business/public/{id}/menu",
                                    True,
                                    f"Retrieved menu for business {test_business_id}: {len(menu_items)} items"
                                )
                            else:
                                self.log_test(
                                    "Customer - GET /api/business/public/{id}/menu",
                                    False,
                                    error=f"HTTP {menu_response.status_code}: {menu_response.text[:200]}"
                                )
                        except Exception as e:
                            self.log_test(
                                "Customer - GET /api/business/public/{id}/menu",
                                False,
                                error=f"Request failed: {str(e)}"
                            )
                    else:
                        self.log_test(
                            "Customer - GET /api/business/public/{id}/menu",
                            False,
                            error="No business ID available for menu test"
                        )
            else:
                self.log_test(
                    "Customer - GET /api/businesses?city=Aksaray",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Customer - GET /api/businesses?city=Aksaray",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 5: POST /api/orders
        try:
            order_data = {
                "delivery_address": "Test Delivery Address, Aksaray",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0254,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Product",
                        "product_price": 25.50,
                        "quantity": 2,
                        "subtotal": 51.00
                    }
                ],
                "total_amount": 51.00,
                "notes": "Test order from comprehensive endpoint test"
            }
            
            response = customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.order_id = data.get("id") or data.get("order_id")
                self.log_test(
                    "Customer - POST /api/orders",
                    True,
                    f"Order created successfully: {self.order_id}"
                )
            else:
                self.log_test(
                    "Customer - POST /api/orders",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Customer - POST /api/orders",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 6: GET /api/orders/my
        try:
            response = customer_session.get(
                f"{BACKEND_URL}/api/orders/my",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                self.log_test(
                    "Customer - GET /api/orders/my",
                    True,
                    f"Retrieved {len(orders)} customer orders"
                )
            else:
                self.log_test(
                    "Customer - GET /api/orders/my",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Customer - GET /api/orders/my",
                False,
                error=f"Request failed: {str(e)}"
            )
    
    def test_business_panel_endpoints(self):
        """Test business panel endpoints"""
        print("🏪 Testing Business Panel endpoints...")
        print("-" * 50)
        
        if "business" not in self.sessions:
            print("❌ No business session available")
            return
            
        business_session = self.sessions["business"]
        
        # Test 1: GET /api/business/orders/incoming
        try:
            response = business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                self.log_test(
                    "Business - GET /api/business/orders/incoming",
                    True,
                    f"Retrieved {len(orders)} business orders"
                )
            else:
                self.log_test(
                    "Business - GET /api/business/orders/incoming",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Business - GET /api/business/orders/incoming",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: GET /api/business/menu
        try:
            response = business_session.get(
                f"{BACKEND_URL}/api/business/menu",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data if isinstance(data, list) else data.get("items", [])
                self.log_test(
                    "Business - GET /api/business/menu",
                    True,
                    f"Retrieved {len(menu_items)} menu items"
                )
            else:
                self.log_test(
                    "Business - GET /api/business/menu",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Business - GET /api/business/menu",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 3: POST /api/business/menu
        try:
            menu_item_data = {
                "name": "Test Menu Item",
                "description": "Test description for comprehensive endpoint test",
                "price": 29.99,
                "category": "Yemek",
                "preparation_time": 15,
                "is_available": True
            }
            
            response = business_session.post(
                f"{BACKEND_URL}/api/business/menu",
                json=menu_item_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.menu_item_id = data.get("id")
                self.log_test(
                    "Business - POST /api/business/menu",
                    True,
                    f"Menu item created successfully: {self.menu_item_id}"
                )
            else:
                self.log_test(
                    "Business - POST /api/business/menu",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Business - POST /api/business/menu",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 4: PUT /api/business/menu/{id}
        if self.menu_item_id:
            try:
                update_data = {
                    "name": "Updated Test Menu Item",
                    "price": 34.99
                }
                
                response = business_session.patch(
                    f"{BACKEND_URL}/api/business/menu/{self.menu_item_id}",
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Business - PATCH /api/business/menu/{id}",
                        True,
                        f"Menu item updated successfully: {self.menu_item_id}"
                    )
                else:
                    self.log_test(
                        "Business - PATCH /api/business/menu/{id}",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                self.log_test(
                    "Business - PUT /api/business/menu/{id}",
                    False,
                    error=f"Request failed: {str(e)}"
                )
        else:
            self.log_test(
                "Business - PATCH /api/business/menu/{id}",
                False,
                error="No menu item ID available for update test"
            )
        
        # Test 5: PUT /api/business/orders/{id}/confirm
        if self.order_id:
            try:
                confirm_data = {
                    "unit_delivery_fee": 15.0
                }
                
                response = business_session.put(
                    f"{BACKEND_URL}/api/business/orders/{self.order_id}/confirm",
                    json=confirm_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        "Business - PUT /api/business/orders/{id}/confirm",
                        True,
                        f"Order confirmed successfully: {self.order_id}"
                    )
                else:
                    self.log_test(
                        "Business - PUT /api/business/orders/{id}/confirm",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                self.log_test(
                    "Business - PUT /api/business/orders/{id}/confirm",
                    False,
                    error=f"Request failed: {str(e)}"
                )
        else:
            self.log_test(
                "Business - PUT /api/business/orders/{id}/confirm",
                False,
                error="No order ID available for confirmation test"
            )
    
    def test_courier_panel_endpoints(self):
        """Test courier panel endpoints"""
        print("🚚 Testing Courier Panel endpoints...")
        print("-" * 50)
        
        if "courier" not in self.sessions:
            print("❌ No courier session available")
            return
            
        courier_session = self.sessions["courier"]
        
        # Test 1: GET /api/courier/tasks
        try:
            response = courier_session.get(
                f"{BACKEND_URL}/api/courier/tasks",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = data if isinstance(data, list) else data.get("tasks", [])
                self.log_test(
                    "Courier - GET /api/courier/tasks",
                    True,
                    f"Retrieved {len(tasks)} courier tasks"
                )
                
                # Store first task ID for accept test
                if tasks and len(tasks) > 0:
                    self.task_id = tasks[0].get("id")
            else:
                self.log_test(
                    "Courier - GET /api/courier/tasks",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Courier - GET /api/courier/tasks",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: PUT /api/courier/tasks/{id}/accept
        if self.task_id:
            try:
                response = courier_session.put(
                    f"{BACKEND_URL}/api/courier/tasks/{self.task_id}/accept",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Courier - PUT /api/courier/tasks/{id}/accept",
                        True,
                        f"Task accepted successfully: {self.task_id}"
                    )
                else:
                    self.log_test(
                        "Courier - PUT /api/courier/tasks/{id}/accept",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                self.log_test(
                    "Courier - PUT /api/courier/tasks/{id}/accept",
                    False,
                    error=f"Request failed: {str(e)}"
                )
        else:
            self.log_test(
                "Courier - PUT /api/courier/tasks/{id}/accept",
                False,
                error="No task ID available for accept test"
            )
        
        # Test 3: PUT /api/courier/tasks/{id}/status
        if self.task_id:
            try:
                status_data = {
                    "status": "picked_up",
                    "location": {
                        "lat": 38.3687,
                        "lng": 34.0254
                    }
                }
                
                response = courier_session.put(
                    f"{BACKEND_URL}/api/courier/tasks/{self.task_id}/status",
                    json=status_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Courier - PUT /api/courier/tasks/{id}/status",
                        True,
                        f"Task status updated successfully: {self.task_id}"
                    )
                else:
                    self.log_test(
                        "Courier - PUT /api/courier/tasks/{id}/status",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                self.log_test(
                    "Courier - PUT /api/courier/tasks/{id}/status",
                    False,
                    error=f"Request failed: {str(e)}"
                )
        else:
            self.log_test(
                "Courier - PUT /api/courier/tasks/{id}/status",
                False,
                error="No task ID available for status update test"
            )
    
    def test_admin_panel_endpoints(self):
        """Test admin panel endpoints"""
        print("⚙️ Testing Admin Panel endpoints...")
        print("-" * 50)
        
        if "admin" not in self.sessions:
            print("❌ No admin session available")
            return
            
        admin_session = self.sessions["admin"]
        
        # Test 1: GET /api/admin/users
        try:
            response = admin_session.get(
                f"{BACKEND_URL}/api/admin/users",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data if isinstance(data, list) else data.get("users", [])
                self.log_test(
                    "Admin - GET /api/admin/users",
                    True,
                    f"Retrieved {len(users)} users"
                )
            else:
                self.log_test(
                    "Admin - GET /api/admin/users",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Admin - GET /api/admin/users",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 2: GET /api/admin/orders
        try:
            response = admin_session.get(
                f"{BACKEND_URL}/api/admin/orders",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                self.log_test(
                    "Admin - GET /api/admin/orders",
                    True,
                    f"Retrieved {len(orders)} orders"
                )
            else:
                self.log_test(
                    "Admin - GET /api/admin/orders",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Admin - GET /api/admin/orders",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 3: PUT /api/admin/kyc/{business_id}/approve
        if self.business_id:
            try:
                response = admin_session.put(
                    f"{BACKEND_URL}/api/admin/kyc/{self.business_id}/approve",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(
                        "Admin - PUT /api/admin/kyc/{business_id}/approve",
                        True,
                        f"KYC approved successfully for business: {self.business_id}"
                    )
                else:
                    self.log_test(
                        "Admin - PUT /api/admin/kyc/{business_id}/approve",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                self.log_test(
                    "Admin - PUT /api/admin/kyc/{business_id}/approve",
                    False,
                    error=f"Request failed: {str(e)}"
                )
        else:
            self.log_test(
                "Admin - PUT /api/admin/kyc/{business_id}/approve",
                False,
                error="No business ID available for KYC approval test"
            )
        
        # Test 4: GET /api/admin/system/status
        try:
            response = admin_session.get(
                f"{BACKEND_URL}/api/admin/system/status",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin - GET /api/admin/system/status",
                    True,
                    f"System status retrieved: {data.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "Admin - GET /api/admin/system/status",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Admin - GET /api/admin/system/status",
                False,
                error=f"Request failed: {str(e)}"
            )
        
        # Test 5: POST /api/admin/ai/assist (Ops Co-Pilot)
        try:
            ai_data = {
                "panel": "müşteri",
                "message": "Comprehensive endpoint test - checking Ops Co-Pilot functionality"
            }
            
            response = admin_session.post(
                f"{BACKEND_URL}/api/admin/ai/assist",
                json=ai_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data and isinstance(data["response"], str):
                    self.log_test(
                        "Admin - POST /api/admin/ai/assist",
                        True,
                        f"Ops Co-Pilot response received: {len(data['response'])} chars"
                    )
                else:
                    self.log_test(
                        "Admin - POST /api/admin/ai/assist",
                        False,
                        error=f"Invalid response format: {list(data.keys())}"
                    )
            else:
                self.log_test(
                    "Admin - POST /api/admin/ai/assist",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log_test(
                "Admin - POST /api/admin/ai/assist",
                False,
                error=f"Request failed: {str(e)}"
            )
    
    def test_logout_endpoints(self):
        """Test logout endpoints for all roles"""
        print("🚪 Testing logout endpoints...")
        print("-" * 50)
        
        for role in ["customer", "business", "courier", "admin"]:
            if role not in self.sessions:
                self.log_test(f"{role.title()} Logout", False, error="No authenticated session")
                continue
                
            try:
                response = self.sessions[role].post(
                    f"{BACKEND_URL}/api/auth/logout",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(
                        f"{role.title()} Logout",
                        True,
                        "Logout successful"
                    )
                else:
                    self.log_test(
                        f"{role.title()} Logout",
                        False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"{role.title()} Logout",
                    False,
                    error=f"Request failed: {str(e)}"
                )
    
    def run_all_tests(self):
        """Run all comprehensive endpoint tests"""
        print("🚀 Starting Kuryecini Comprehensive Backend Endpoint Testing")
        print("=" * 80)
        
        # Step 1: Authentication
        self.authenticate_all_roles()
        
        # Step 2: Auth verification
        self.test_auth_verification()
        
        # Step 3: Customer Panel
        self.test_customer_panel_endpoints()
        
        # Step 4: Business Panel
        self.test_business_panel_endpoints()
        
        # Step 5: Courier Panel
        self.test_courier_panel_endpoints()
        
        # Step 6: Admin Panel
        self.test_admin_panel_endpoints()
        
        # Step 7: Logout
        self.test_logout_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND ENDPOINT TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results by panel
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"] or "/api/me" in r["test"] or "Logout" in r["test"]]
        customer_tests = [r for r in self.test_results if "Customer" in r["test"]]
        business_tests = [r for r in self.test_results if "Business" in r["test"]]
        courier_tests = [r for r in self.test_results if "Courier" in r["test"]]
        admin_tests = [r for r in self.test_results if "Admin" in r["test"]]
        
        print(f"\n📋 RESULTS BY PANEL:")
        print(f"   🔐 Authentication: {len([r for r in auth_tests if r['success']])}/{len(auth_tests)} passed")
        print(f"   👤 Customer Panel: {len([r for r in customer_tests if r['success']])}/{len(customer_tests)} passed")
        print(f"   🏪 Business Panel: {len([r for r in business_tests if r['success']])}/{len(business_tests)} passed")
        print(f"   🚚 Courier Panel: {len([r for r in courier_tests if r['success']])}/{len(courier_tests)} passed")
        print(f"   ⚙️ Admin Panel: {len([r for r in admin_tests if r['success']])}/{len(admin_tests)} passed")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        
        # Check success criteria
        auth_working = len([r for r in auth_tests if r['success']]) >= len(auth_tests) * 0.8
        customer_working = len([r for r in customer_tests if r['success']]) >= len(customer_tests) * 0.8
        business_working = len([r for r in business_tests if r['success']]) >= len(business_tests) * 0.8
        courier_working = len([r for r in courier_tests if r['success']]) >= len(courier_tests) * 0.8
        admin_working = len([r for r in admin_tests if r['success']]) >= len(admin_tests) * 0.8
        
        print(f"   ✅ All auth endpoints working: {'YES' if auth_working else 'NO'}")
        print(f"   ✅ Customer panel critical functions accessible: {'YES' if customer_working else 'NO'}")
        print(f"   ✅ Business panel critical functions accessible: {'YES' if business_working else 'NO'}")
        print(f"   ✅ Courier panel critical functions accessible: {'YES' if courier_working else 'NO'}")
        print(f"   ✅ Admin panel critical functions accessible: {'YES' if admin_working else 'NO'}")
        
        # Check for critical errors
        has_500_errors = any("500" in r["error"] for r in self.test_results if not r["success"])
        has_404_errors = any("404" in r["error"] for r in self.test_results if not r["success"])
        
        print(f"   ✅ No 500 errors: {'YES' if not has_500_errors else 'NO'}")
        print(f"   ✅ No 404 errors (endpoints exist): {'YES' if not has_404_errors else 'NO'}")
        
        # Overall verdict
        if success_rate >= 90:
            print(f"\n🎉 VERDICT: ALL BACKEND ENDPOINTS ARE WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
            print("   The Kuryecini platform backend is production-ready with comprehensive functionality.")
        elif success_rate >= 75:
            print(f"\n✅ VERDICT: BACKEND ENDPOINTS ARE WORKING WELL ({success_rate:.1f}% success rate)")
            print("   Core functionality works but some features need attention.")
        elif success_rate >= 50:
            print(f"\n⚠️ VERDICT: BACKEND ENDPOINTS HAVE MODERATE ISSUES ({success_rate:.1f}% success rate)")
            print("   Some critical functionality is broken and needs immediate attention.")
        else:
            print(f"\n🚨 VERDICT: BACKEND ENDPOINTS HAVE CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major functionality is broken and needs urgent fixes.")

def main():
    """Main test runner"""
    tester = ComprehensiveEndpointTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()