#!/usr/bin/env python3
"""
PHASE 2 BACKEND TESTING - Business Menu CRUD, Geospatial Discovery, Customer Orders
Comprehensive testing of Phase 2 endpoints as requested in the review.

TESTING SCOPE:
1. Business Menu CRUD Operations (routes/business.py):
   - POST /api/business/menu (create menu item with business authentication)
   - GET /api/business/menu (get business's own menu items)
   - PATCH /api/business/menu/{item_id} (update menu item)
   - DELETE /api/business/menu/{item_id} (delete menu item)

2. Geospatial Nearby Businesses Discovery (routes/nearby.py):
   - GET /api/nearby/businesses?lat={latitude}&lng={longitude}&radius_m={optional_radius}
   - GET /api/nearby/businesses/{business_id}/menu (full menu for specific business)

3. Customer Order Creation System (routes/orders.py):
   - POST /api/orders (create order with delivery address and items)
   - GET /api/orders/my (customer's order list)
   - GET /api/orders/{order_id}/track (order tracking)

AUTHENTICATION DETAILS:
- Business login: testrestoran@example.com / test123
- Customer login: testcustomer@example.com / test123
- Admin login: admin@kuryecini.com / KuryeciniAdmin2024!
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://meal-dash-163.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testrestoran@example.com", "password": "test123"}
}

# Test coordinates from review request
ISTANBUL_COORDS = {"lat": 41.0082, "lng": 28.9784}
AKSARAY_COORDS = {"lat": 38.3687, "lng": 34.0370}

class Phase2BackendTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.test_business_id = None
        self.test_menu_item_id = None
        self.test_order_id = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
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
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_users(self):
        """Authenticate all test users and get JWT tokens"""
        print("🔐 AUTHENTICATING TEST USERS...")
        
        for role, credentials in TEST_CREDENTIALS.items():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    
                    # Store business ID for testing
                    if role == "business":
                        self.test_business_id = data["user"]["id"]
                    
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, User ID: {data['user']['id']}, Role: {data['user'].get('role', 'unknown')}"
                    )
                else:
                    self.log_test(
                        f"Authentication - {role.title()}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Authentication - {role.title()}",
                    False,
                    error=str(e)
                )

    def test_business_menu_crud(self):
        """Test Business Menu CRUD Operations"""
        print("🍽️ TESTING BUSINESS MENU CRUD OPERATIONS...")
        
        if "business" not in self.tokens:
            self.log_test(
                "Business Menu CRUD - Setup",
                False,
                error="Business authentication required"
            )
            return

        headers = {"Authorization": f"Bearer {self.tokens['business']}"}

        # Test 1: POST /api/business/menu - Create menu item
        try:
            menu_item_data = {
                "name": "Test Döner Kebap",
                "description": "Özel baharatlarla hazırlanmış döner kebap",
                "price": 45.50,
                "category": "Ana Yemek",
                "preparation_time_minutes": 20,
                "is_available": True
            }
            
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_menu_item_id = data.get("id") or data.get("menu_item_id")
                self.log_test(
                    "Business Menu CRUD - Create Menu Item",
                    True,
                    f"Menu item created: {data.get('name', 'Unknown')}, ID: {self.test_menu_item_id}, Price: ₺{data.get('price', 0)}"
                )
            else:
                self.log_test(
                    "Business Menu CRUD - Create Menu Item",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Create Menu Item",
                False,
                error=str(e)
            )

        # Test 2: GET /api/business/menu - Get business's own menu items
        try:
            response = requests.get(
                f"{BACKEND_URL}/business/menu",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data if isinstance(data, list) else data.get("menu_items", [])
                self.log_test(
                    "Business Menu CRUD - Get Own Menu Items",
                    True,
                    f"Retrieved {len(menu_items)} menu items for business"
                )
            else:
                self.log_test(
                    "Business Menu CRUD - Get Own Menu Items",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Get Own Menu Items",
                False,
                error=str(e)
            )

        # Test 3: PATCH /api/business/menu/{item_id} - Update menu item
        if self.test_menu_item_id:
            try:
                update_data = {
                    "name": "Updated Test Döner Kebap",
                    "price": 50.00,
                    "is_available": False
                }
                
                response = requests.patch(
                    f"{BACKEND_URL}/business/menu/{self.test_menu_item_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        "Business Menu CRUD - Update Menu Item",
                        True,
                        f"Menu item updated: {data.get('name', 'Unknown')}, New price: ₺{data.get('price', 0)}, Available: {data.get('is_available', False)}"
                    )
                else:
                    self.log_test(
                        "Business Menu CRUD - Update Menu Item",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    "Business Menu CRUD - Update Menu Item",
                    False,
                    error=str(e)
                )

        # Test 4: DELETE /api/business/menu/{item_id} - Delete menu item
        if self.test_menu_item_id:
            try:
                response = requests.delete(
                    f"{BACKEND_URL}/business/menu/{self.test_menu_item_id}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 204]:
                    self.log_test(
                        "Business Menu CRUD - Delete Menu Item",
                        True,
                        f"Menu item deleted successfully: {self.test_menu_item_id}"
                    )
                else:
                    self.log_test(
                        "Business Menu CRUD - Delete Menu Item",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    "Business Menu CRUD - Delete Menu Item",
                    False,
                    error=str(e)
                )

        # Test 5: RBAC - Customer trying to access business menu endpoints
        if "customer" in self.tokens:
            try:
                customer_headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
                response = requests.get(
                    f"{BACKEND_URL}/business/menu",
                    headers=customer_headers,
                    timeout=10
                )
                
                self.log_test(
                    "Business Menu CRUD - RBAC Test (Customer Access)",
                    response.status_code == 403,
                    f"Status: {response.status_code} (Expected 403 for customer accessing business endpoints)"
                )
            except Exception as e:
                self.log_test(
                    "Business Menu CRUD - RBAC Test (Customer Access)",
                    False,
                    error=str(e)
                )

    def test_geospatial_nearby_businesses(self):
        """Test Geospatial Nearby Businesses Discovery"""
        print("📍 TESTING GEOSPATIAL NEARBY BUSINESSES DISCOVERY...")
        
        if "customer" not in self.tokens:
            self.log_test(
                "Geospatial Discovery - Setup",
                False,
                error="Customer authentication required"
            )
            return

        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}

        # Test 1: GET /api/nearby/businesses with Istanbul coordinates
        try:
            params = {
                "lat": ISTANBUL_COORDS["lat"],
                "lng": ISTANBUL_COORDS["lng"],
                "radius_m": 5000
            }
            
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test(
                    "Geospatial Discovery - Istanbul Businesses",
                    True,
                    f"Found {len(businesses)} businesses near Istanbul (lat: {ISTANBUL_COORDS['lat']}, lng: {ISTANBUL_COORDS['lng']}, radius: 5km)"
                )
                
                # Store first business ID for menu testing
                if businesses and len(businesses) > 0:
                    self.test_business_id = businesses[0].get("id")
                    
            else:
                self.log_test(
                    "Geospatial Discovery - Istanbul Businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Geospatial Discovery - Istanbul Businesses",
                False,
                error=str(e)
            )

        # Test 2: GET /api/nearby/businesses with Aksaray coordinates
        try:
            params = {
                "lat": AKSARAY_COORDS["lat"],
                "lng": AKSARAY_COORDS["lng"],
                "radius_m": 10000
            }
            
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test(
                    "Geospatial Discovery - Aksaray Businesses",
                    True,
                    f"Found {len(businesses)} businesses near Aksaray (lat: {AKSARAY_COORDS['lat']}, lng: {AKSARAY_COORDS['lng']}, radius: 10km)"
                )
            else:
                self.log_test(
                    "Geospatial Discovery - Aksaray Businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Geospatial Discovery - Aksaray Businesses",
                False,
                error=str(e)
            )

        # Test 3: GET /api/nearby/businesses without radius (default radius)
        try:
            params = {
                "lat": ISTANBUL_COORDS["lat"],
                "lng": ISTANBUL_COORDS["lng"]
            }
            
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test(
                    "Geospatial Discovery - Default Radius",
                    True,
                    f"Found {len(businesses)} businesses with default radius near Istanbul"
                )
            else:
                self.log_test(
                    "Geospatial Discovery - Default Radius",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Geospatial Discovery - Default Radius",
                False,
                error=str(e)
            )

        # Test 4: GET /api/nearby/businesses/{business_id}/menu - Full menu for specific business
        if self.test_business_id:
            try:
                response = requests.get(
                    f"{BACKEND_URL}/nearby/businesses/{self.test_business_id}/menu",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    menu_items = data if isinstance(data, list) else data.get("menu_items", [])
                    self.log_test(
                        "Geospatial Discovery - Business Menu",
                        True,
                        f"Retrieved menu for business {self.test_business_id}: {len(menu_items)} items"
                    )
                else:
                    self.log_test(
                        "Geospatial Discovery - Business Menu",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    "Geospatial Discovery - Business Menu",
                    False,
                    error=str(e)
                )

        # Test 5: Invalid coordinates
        try:
            params = {
                "lat": "invalid",
                "lng": 28.9784
            }
            
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params=params,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Geospatial Discovery - Invalid Coordinates",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for invalid coordinates)"
            )
        except Exception as e:
            self.log_test(
                "Geospatial Discovery - Invalid Coordinates",
                False,
                error=str(e)
            )

        # Test 6: RBAC - Unauthenticated access
        try:
            params = {
                "lat": ISTANBUL_COORDS["lat"],
                "lng": ISTANBUL_COORDS["lng"]
            }
            
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params=params,
                timeout=10
            )
            
            self.log_test(
                "Geospatial Discovery - RBAC Test (Unauthenticated)",
                response.status_code in [401, 403],
                f"Status: {response.status_code} (Expected 401/403 for unauthenticated access)"
            )
        except Exception as e:
            self.log_test(
                "Geospatial Discovery - RBAC Test (Unauthenticated)",
                False,
                error=str(e)
            )

    def test_customer_order_system(self):
        """Test Customer Order Creation System"""
        print("📦 TESTING CUSTOMER ORDER CREATION SYSTEM...")
        
        if "customer" not in self.tokens:
            self.log_test(
                "Customer Order System - Setup",
                False,
                error="Customer authentication required"
            )
            return

        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}

        # Test 1: POST /api/orders - Create order with delivery address and items
        try:
            order_data = {
                "delivery_address": "Test Delivery Address, Istanbul, Turkey",
                "delivery_lat": ISTANBUL_COORDS["lat"],
                "delivery_lng": ISTANBUL_COORDS["lng"],
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Margherita Pizza",
                        "product_price": 85.0,
                        "quantity": 1,
                        "subtotal": 85.0
                    },
                    {
                        "product_id": "test-product-2",
                        "product_name": "Coca Cola",
                        "product_price": 15.0,
                        "quantity": 2,
                        "subtotal": 30.0
                    }
                ],
                "total_amount": 115.0,
                "notes": "Phase 2 test order - please handle with care",
                "payment_method": "cash_on_delivery"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_order_id = data.get("id") or data.get("order_id")
                self.log_test(
                    "Customer Order System - Create Order",
                    True,
                    f"Order created: ID {self.test_order_id}, Total: ₺{data.get('total_amount', 0)}, Items: {len(data.get('items', []))}, Status: {data.get('status', 'unknown')}"
                )
            else:
                self.log_test(
                    "Customer Order System - Create Order",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Create Order",
                False,
                error=str(e)
            )

        # Test 2: GET /api/orders/my - Customer's order list
        try:
            response = requests.get(
                f"{BACKEND_URL}/orders/my",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                self.log_test(
                    "Customer Order System - Get My Orders",
                    True,
                    f"Retrieved {len(orders)} orders for customer"
                )
                
                # Verify our test order is in the list
                if self.test_order_id:
                    test_order_found = any(order.get("id") == self.test_order_id for order in orders)
                    if test_order_found:
                        print(f"   ✅ Test order {self.test_order_id} found in customer's order list")
                    else:
                        print(f"   ⚠️ Test order {self.test_order_id} not found in customer's order list")
                        
            else:
                self.log_test(
                    "Customer Order System - Get My Orders",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Get My Orders",
                False,
                error=str(e)
            )

        # Test 3: GET /api/orders/{order_id}/track - Order tracking
        if self.test_order_id:
            try:
                response = requests.get(
                    f"{BACKEND_URL}/orders/{self.test_order_id}/track",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        "Customer Order System - Track Order",
                        True,
                        f"Order tracking: ID {data.get('id')}, Status: {data.get('status')}, Estimated delivery: {data.get('estimated_delivery', 'N/A')}"
                    )
                    
                    # Check if courier location is available
                    if data.get("courier_location"):
                        courier_loc = data["courier_location"]
                        print(f"   📍 Courier location: lat {courier_loc.get('lat')}, lng {courier_loc.get('lng')}")
                    else:
                        print(f"   📍 Courier location: Not available (status: {data.get('status')})")
                        
                else:
                    self.log_test(
                        "Customer Order System - Track Order",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    "Customer Order System - Track Order",
                    False,
                    error=str(e)
                )

        # Test 4: Order validation - Missing required fields
        try:
            invalid_order_data = {
                "delivery_address": "Test Address",
                # Missing items and total_amount
            }
            
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=invalid_order_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order System - Order Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for invalid order data)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order System - Order Validation",
                False,
                error=str(e)
            )

        # Test 5: Payment method validation - Online payment
        try:
            order_data = {
                "delivery_address": "Test Address",
                "delivery_lat": ISTANBUL_COORDS["lat"],
                "delivery_lng": ISTANBUL_COORDS["lng"],
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Item",
                        "product_price": 25.0,
                        "quantity": 1,
                        "subtotal": 25.0
                    }
                ],
                "total_amount": 25.0,
                "payment_method": "online"  # Test online payment
            }
            
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Customer Order System - Online Payment Method",
                    True,
                    f"Online payment order created: ID {data.get('id')}, Payment method: {data.get('payment_method', 'unknown')}"
                )
            else:
                self.log_test(
                    "Customer Order System - Online Payment Method",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Online Payment Method",
                False,
                error=str(e)
            )

        # Test 6: Payment method validation - POS on delivery
        try:
            order_data = {
                "delivery_address": "Test Address",
                "delivery_lat": ISTANBUL_COORDS["lat"],
                "delivery_lng": ISTANBUL_COORDS["lng"],
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Item",
                        "product_price": 35.0,
                        "quantity": 1,
                        "subtotal": 35.0
                    }
                ],
                "total_amount": 35.0,
                "payment_method": "pos_on_delivery"  # Test POS on delivery
            }
            
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "Customer Order System - POS on Delivery Payment",
                    True,
                    f"POS on delivery order created: ID {data.get('id')}, Payment method: {data.get('payment_method', 'unknown')}"
                )
            else:
                self.log_test(
                    "Customer Order System - POS on Delivery Payment",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - POS on Delivery Payment",
                False,
                error=str(e)
            )

        # Test 7: RBAC - Business user trying to access customer orders
        if "business" in self.tokens:
            try:
                business_headers = {"Authorization": f"Bearer {self.tokens['business']}"}
                response = requests.get(
                    f"{BACKEND_URL}/orders/my",
                    headers=business_headers,
                    timeout=10
                )
                
                self.log_test(
                    "Customer Order System - RBAC Test (Business Access)",
                    response.status_code == 403,
                    f"Status: {response.status_code} (Expected 403 for business accessing customer orders)"
                )
            except Exception as e:
                self.log_test(
                    "Customer Order System - RBAC Test (Business Access)",
                    False,
                    error=str(e)
                )

    def run_comprehensive_test(self):
        """Run all Phase 2 backend tests"""
        print("🚀 STARTING PHASE 2 BACKEND TESTING")
        print("=" * 80)
        print("Testing Business Menu CRUD, Geospatial Discovery, and Customer Orders")
        print("=" * 80)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not self.tokens:
            print("❌ CRITICAL: Authentication failed for all roles. Cannot proceed.")
            return
        
        # Step 2: Test Business Menu CRUD Operations
        self.test_business_menu_crud()
        
        # Step 3: Test Geospatial Nearby Businesses Discovery
        self.test_geospatial_nearby_businesses()
        
        # Step 4: Test Customer Order Creation System
        self.test_customer_order_system()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 PHASE 2 BACKEND TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["test"].split(" - ")[0]
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
            categories[category]["tests"].append(result)
        
        # Print category summaries
        for category, data in categories.items():
            total = data["passed"] + data["failed"]
            rate = (data["passed"] / total * 100) if total > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 75 else "❌"
            print(f"{status} {category}: {data['passed']}/{total} ({rate:.1f}%)")
        
        print("\n" + "=" * 80)
        print("🔍 DETAILED FAILURE ANALYSIS")
        print("=" * 80)
        
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            for result in failed_results:
                print(f"❌ {result['test']}")
                if result["error"]:
                    print(f"   Error: {result['error']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
                print()
        else:
            print("🎉 No test failures detected!")
        
        print("\n" + "=" * 80)
        print("📋 PHASE 2 IMPLEMENTATION STATUS")
        print("=" * 80)
        
        # Analyze which endpoints are implemented vs missing
        business_menu_tests = [r for r in self.test_results if "Business Menu CRUD" in r["test"]]
        geospatial_tests = [r for r in self.test_results if "Geospatial Discovery" in r["test"]]
        order_system_tests = [r for r in self.test_results if "Customer Order System" in r["test"]]
        
        business_menu_success = sum(1 for r in business_menu_tests if r["success"])
        geospatial_success = sum(1 for r in geospatial_tests if r["success"])
        order_system_success = sum(1 for r in order_system_tests if r["success"])
        
        print(f"🍽️ Business Menu CRUD: {business_menu_success}/{len(business_menu_tests)} tests passed")
        print(f"📍 Geospatial Discovery: {geospatial_success}/{len(geospatial_tests)} tests passed")
        print(f"📦 Customer Order System: {order_system_success}/{len(order_system_tests)} tests passed")
        
        print("\n" + "=" * 80)
        print("🎯 RECOMMENDATIONS")
        print("=" * 80)
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Phase 2 backend implementation is working excellently")
        elif success_rate >= 75:
            print("⚠️ GOOD: Phase 2 backend is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️ NEEDS ATTENTION: Phase 2 backend has significant issues")
        else:
            print("❌ CRITICAL: Phase 2 backend has major implementation gaps")
        
        # Specific recommendations based on failures
        if business_menu_success == 0:
            print("- ❌ Business Menu CRUD endpoints (/api/business/menu/*) appear to be NOT IMPLEMENTED")
        elif business_menu_success < len(business_menu_tests):
            print("- ⚠️ Business Menu CRUD endpoints have partial implementation issues")
            
        if geospatial_success == 0:
            print("- ❌ Geospatial Discovery endpoints (/api/nearby/businesses*) appear to be NOT IMPLEMENTED")
        elif geospatial_success < len(geospatial_tests):
            print("- ⚠️ Geospatial Discovery endpoints have partial implementation issues")
            
        if order_system_success < len(order_system_tests):
            print("- ⚠️ Customer Order System endpoints need attention")
        
        auth_failures = [r for r in self.test_results if "Authentication" in r["test"] and not r["success"]]
        if auth_failures:
            print("- ⚠️ Fix authentication issues for proper testing")
        
        rbac_failures = [r for r in self.test_results if "RBAC" in r["test"] and not r["success"]]
        if rbac_failures:
            print("- ⚠️ Review and fix role-based access control implementation")

if __name__ == "__main__":
    tester = Phase2BackendTester()
    tester.run_comprehensive_test()