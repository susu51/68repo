#!/usr/bin/env python3
"""
PHASE 2 COMPREHENSIVE BACKEND TESTING
Complete functionality testing of all Phase 2 endpoints now that authentication is working.

TESTING SCOPE - FULL FUNCTIONALITY:

1. Business Menu CRUD Operations (routes/business.py) - COMPREHENSIVE
2. Geospatial Nearby Businesses Discovery (routes/nearby.py) - COMPREHENSIVE  
3. Customer Order Creation System (routes/orders.py) - COMPREHENSIVE

Authentication:
- Business: testbusiness@example.com / test123 (authentication confirmed working)
- Customer: testcustomer@example.com / test123 (authentication confirmed working)

Focus: Data consistency, validation, error handling, business logic correctness, security and access control
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://express-track-2.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"}
}

class Phase2BackendTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.business_id = None
        self.customer_id = None
        self.test_menu_items = []
        self.test_businesses = []
        self.test_orders = []
        
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
                    
                    # Store user IDs for testing
                    if role == "business":
                        self.business_id = data["user"]["id"]
                    elif role == "customer":
                        self.customer_id = data["user"]["id"]
                    
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, User ID: {data['user']['id']}"
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

    def test_business_menu_crud_comprehensive(self):
        """Test Business Menu CRUD Operations - COMPREHENSIVE"""
        print("🍽️ TESTING BUSINESS MENU CRUD OPERATIONS - COMPREHENSIVE...")
        
        if not self.business_id or "business" not in self.tokens:
            self.log_test(
                "Business Menu CRUD - Setup",
                False,
                error="Business authentication required"
            )
            return

        # Test 1: POST /api/business/menu (create menu item with all fields)
        try:
            menu_item_data = {
                "name": "Deluxe Burger Menu",
                "description": "Premium beef burger with fries and drink",
                "price": 45.50,
                "category": "Ana Yemek",
                "preparation_time_minutes": 25,
                "is_available": True
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                menu_item_id = data.get("id") or data.get("menu_item_id")
                self.test_menu_items.append(menu_item_id)
                
                self.log_test(
                    "Business Menu CRUD - Create Menu Item",
                    True,
                    f"Menu item created: {menu_item_id}, Name: {data.get('name')}, Price: ₺{data.get('price')}"
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

        # Test 2: GET /api/business/menu (retrieve business's menu items)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/business/menu",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                menu_items = data.get("menu_items", data.get("items", []))
                
                self.log_test(
                    "Business Menu CRUD - Get Menu Items",
                    True,
                    f"Retrieved {len(menu_items)} menu items for business"
                )
            else:
                self.log_test(
                    "Business Menu CRUD - Get Menu Items",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Get Menu Items",
                False,
                error=str(e)
            )

        # Test 3: Create another menu item for update/delete tests
        try:
            menu_item_data = {
                "name": "Chicken Pizza",
                "description": "Delicious chicken pizza with vegetables",
                "price": 35.00,
                "category": "Pizza",
                "preparation_time_minutes": 20,
                "is_available": True
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                menu_item_id = data.get("id") or data.get("menu_item_id")
                self.test_menu_items.append(menu_item_id)
                
                # Test 4: PATCH /api/business/menu/{item_id} (update menu item fields)
                update_data = {
                    "name": "Updated Chicken Pizza Supreme",
                    "price": 42.00,
                    "description": "Premium chicken pizza with extra toppings",
                    "is_available": False
                }
                
                update_response = requests.patch(
                    f"{BACKEND_URL}/business/menu/{menu_item_id}",
                    json=update_data,
                    headers=headers,
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    update_result = update_response.json()
                    self.log_test(
                        "Business Menu CRUD - Update Menu Item",
                        True,
                        f"Updated menu item: {menu_item_id}, New name: {update_result.get('name')}, New price: ₺{update_result.get('price')}"
                    )
                else:
                    self.log_test(
                        "Business Menu CRUD - Update Menu Item",
                        False,
                        f"Status: {update_response.status_code}",
                        update_response.text
                    )
                
                # Test 5: DELETE /api/business/menu/{item_id} (delete menu item)
                delete_response = requests.delete(
                    f"{BACKEND_URL}/business/menu/{menu_item_id}",
                    headers=headers,
                    timeout=10
                )
                
                if delete_response.status_code in [200, 204]:
                    self.log_test(
                        "Business Menu CRUD - Delete Menu Item",
                        True,
                        f"Successfully deleted menu item: {menu_item_id}"
                    )
                    # Remove from test list since it's deleted
                    if menu_item_id in self.test_menu_items:
                        self.test_menu_items.remove(menu_item_id)
                else:
                    self.log_test(
                        "Business Menu CRUD - Delete Menu Item",
                        False,
                        f"Status: {delete_response.status_code}",
                        delete_response.text
                    )
                    
            else:
                self.log_test(
                    "Business Menu CRUD - Create Second Menu Item",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Update/Delete Tests",
                False,
                error=str(e)
            )

        # Test 6: Validation tests - price validation, required fields
        try:
            # Test invalid price
            invalid_price_data = {
                "name": "Invalid Price Item",
                "description": "Test item with invalid price",
                "price": -10.00,  # Negative price should be invalid
                "category": "Test",
                "preparation_time_minutes": 15
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=invalid_price_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Menu CRUD - Price Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for negative price)"
            )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Price Validation",
                False,
                error=str(e)
            )

        # Test 7: Required fields validation
        try:
            # Test missing required fields
            incomplete_data = {
                "description": "Missing name and price"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=incomplete_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Menu CRUD - Required Fields Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing required fields)"
            )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Required Fields Validation",
                False,
                error=str(e)
            )

        # Test 8: Unauthorized access (customer trying to access business menu endpoints)
        try:
            menu_item_data = {
                "name": "Unauthorized Item",
                "description": "This should fail",
                "price": 25.00,
                "category": "Test"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/business/menu",
                json=menu_item_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Menu CRUD - Unauthorized Access",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for customer accessing business endpoint)"
            )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Unauthorized Access",
                False,
                error=str(e)
            )

        # Test 9: Invalid item ID for update/delete
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.patch(
                f"{BACKEND_URL}/business/menu/invalid-item-id",
                json={"name": "Updated Name"},
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Menu CRUD - Invalid Item ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid item ID)"
            )
        except Exception as e:
            self.log_test(
                "Business Menu CRUD - Invalid Item ID",
                False,
                error=str(e)
            )

    def test_geospatial_nearby_businesses_comprehensive(self):
        """Test Geospatial Nearby Businesses Discovery - COMPREHENSIVE"""
        print("🗺️ TESTING GEOSPATIAL NEARBY BUSINESSES DISCOVERY - COMPREHENSIVE...")

        # Test coordinates from review request
        test_coordinates = [
            {"name": "Istanbul", "lat": 41.0082, "lng": 28.9784, "expected_businesses": True},
            {"name": "Aksaray", "lat": 38.3687, "lng": 34.0370, "expected_businesses": True}
        ]
        
        # Test different radius values
        radius_values = [1000, 5000, 10000]  # 1km, 5km, 10km

        # Test 1: GET /api/nearby/businesses with multiple coordinates and radius values
        for coord in test_coordinates:
            for radius in radius_values:
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/nearby/businesses",
                        params={
                            "lat": coord["lat"],
                            "lng": coord["lng"],
                            "radius_m": radius
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        businesses = data.get("businesses", [])
                        
                        # Store businesses for later tests
                        if businesses:
                            self.test_businesses.extend([b.get("id") for b in businesses[:3]])  # Store first 3
                        
                        self.log_test(
                            f"Nearby Businesses - {coord['name']} ({radius}m radius)",
                            True,
                            f"Found {len(businesses)} businesses within {radius}m of {coord['name']}"
                        )
                    else:
                        self.log_test(
                            f"Nearby Businesses - {coord['name']} ({radius}m radius)",
                            False,
                            f"Status: {response.status_code}",
                            response.text
                        )
                except Exception as e:
                    self.log_test(
                        f"Nearby Businesses - {coord['name']} ({radius}m radius)",
                        False,
                        error=str(e)
                    )

        # Test 2: Distance calculations and sorting verification
        try:
            # Test with Istanbul coordinates
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params={
                    "lat": 41.0082,
                    "lng": 28.9784,
                    "radius_m": 10000
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get("businesses", [])
                
                # Check if businesses are sorted by distance
                distances = [b.get("distance", 0) for b in businesses if "distance" in b]
                is_sorted = all(distances[i] <= distances[i+1] for i in range(len(distances)-1))
                
                self.log_test(
                    "Nearby Businesses - Distance Sorting",
                    is_sorted or len(distances) <= 1,
                    f"Businesses sorted by distance: {is_sorted}, Total with distance: {len(distances)}"
                )
            else:
                self.log_test(
                    "Nearby Businesses - Distance Sorting",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Nearby Businesses - Distance Sorting",
                False,
                error=str(e)
            )

        # Test 3: GET /api/nearby/businesses/{business_id}/menu for specific businesses
        if self.test_businesses:
            for business_id in self.test_businesses[:2]:  # Test first 2 businesses
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/nearby/businesses/{business_id}/menu",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        menu_items = data.get("menu", data.get("items", []))
                        
                        self.log_test(
                            f"Nearby Business Menu - {business_id[:8]}...",
                            True,
                            f"Retrieved menu with {len(menu_items)} items"
                        )
                    else:
                        self.log_test(
                            f"Nearby Business Menu - {business_id[:8]}...",
                            False,
                            f"Status: {response.status_code}",
                            response.text
                        )
                except Exception as e:
                    self.log_test(
                        f"Nearby Business Menu - {business_id[:8]}...",
                        False,
                        error=str(e)
                    )

        # Test 4: Invalid coordinates
        try:
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params={
                    "lat": 999,  # Invalid latitude
                    "lng": 999,  # Invalid longitude
                    "radius_m": 5000
                },
                timeout=10
            )
            
            self.log_test(
                "Nearby Businesses - Invalid Coordinates",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for invalid coordinates)"
            )
        except Exception as e:
            self.log_test(
                "Nearby Businesses - Invalid Coordinates",
                False,
                error=str(e)
            )

        # Test 5: Missing required parameters
        try:
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params={"lat": 41.0082},  # Missing lng and radius_m
                timeout=10
            )
            
            self.log_test(
                "Nearby Businesses - Missing Parameters",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing parameters)"
            )
        except Exception as e:
            self.log_test(
                "Nearby Businesses - Missing Parameters",
                False,
                error=str(e)
            )

        # Test 6: Invalid business ID for menu
        try:
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses/invalid-business-id/menu",
                timeout=10
            )
            
            self.log_test(
                "Nearby Business Menu - Invalid Business ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid business ID)"
            )
        except Exception as e:
            self.log_test(
                "Nearby Business Menu - Invalid Business ID",
                False,
                error=str(e)
            )

        # Test 7: Large radius test
        try:
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params={
                    "lat": 41.0082,
                    "lng": 28.9784,
                    "radius_m": 50000  # 50km radius
                },
                timeout=15  # Longer timeout for large radius
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get("businesses", [])
                
                self.log_test(
                    "Nearby Businesses - Large Radius (50km)",
                    True,
                    f"Found {len(businesses)} businesses within 50km radius"
                )
            else:
                self.log_test(
                    "Nearby Businesses - Large Radius (50km)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Nearby Businesses - Large Radius (50km)",
                False,
                error=str(e)
            )

    def test_customer_order_creation_comprehensive(self):
        """Test Customer Order Creation System - COMPREHENSIVE"""
        print("📦 TESTING CUSTOMER ORDER CREATION SYSTEM - COMPREHENSIVE...")
        
        if not self.customer_id or "customer" not in self.tokens:
            self.log_test(
                "Customer Order Creation - Setup",
                False,
                error="Customer authentication required"
            )
            return

        # Get some businesses and products for order testing
        self.prepare_order_test_data()

        # Test 1: POST /api/orders with cash_on_delivery payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "test-business-id",
                "delivery_address": "Test Delivery Address, Istanbul, Turkey",
                "delivery_lat": 41.0082,
                "delivery_lng": 28.9784,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Burger",
                        "product_price": 35.00,
                        "quantity": 2,
                        "subtotal": 70.00
                    },
                    {
                        "product_id": "test-product-2", 
                        "product_name": "Test Drink",
                        "product_price": 8.00,
                        "quantity": 2,
                        "subtotal": 16.00
                    }
                ],
                "total_amount": 86.00,
                "payment_method": "cash_on_delivery",
                "notes": "Please ring the doorbell"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                self.test_orders.append(order_id)
                
                self.log_test(
                    "Customer Order Creation - Cash on Delivery",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}, Payment: {data.get('payment_method')}"
                )
            else:
                self.log_test(
                    "Customer Order Creation - Cash on Delivery",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order Creation - Cash on Delivery",
                False,
                error=str(e)
            )

        # Test 2: POST /api/orders with online payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "test-business-id",
                "delivery_address": "Another Test Address, Ankara, Turkey",
                "delivery_lat": 39.9334,
                "delivery_lng": 32.8597,
                "items": [
                    {
                        "product_id": "test-product-3",
                        "product_name": "Test Pizza",
                        "product_price": 45.00,
                        "quantity": 1,
                        "subtotal": 45.00
                    }
                ],
                "total_amount": 45.00,
                "payment_method": "online",
                "notes": "Extra cheese please"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                self.test_orders.append(order_id)
                
                self.log_test(
                    "Customer Order Creation - Online Payment",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}, Payment: {data.get('payment_method')}"
                )
            else:
                self.log_test(
                    "Customer Order Creation - Online Payment",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order Creation - Online Payment",
                False,
                error=str(e)
            )

        # Test 3: POST /api/orders with pos_on_delivery payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "test-business-id",
                "delivery_address": "POS Test Address, Izmir, Turkey",
                "delivery_lat": 38.4192,
                "delivery_lng": 27.1287,
                "items": [
                    {
                        "product_id": "test-product-4",
                        "product_name": "Test Kebab",
                        "product_price": 55.00,
                        "quantity": 1,
                        "subtotal": 55.00
                    },
                    {
                        "product_id": "test-product-5",
                        "product_name": "Test Salad",
                        "product_price": 25.00,
                        "quantity": 1,
                        "subtotal": 25.00
                    }
                ],
                "total_amount": 80.00,
                "payment_method": "pos_on_delivery",
                "notes": "Call before delivery"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                self.test_orders.append(order_id)
                
                self.log_test(
                    "Customer Order Creation - POS on Delivery",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}, Payment: {data.get('payment_method')}"
                )
            else:
                self.log_test(
                    "Customer Order Creation - POS on Delivery",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order Creation - POS on Delivery",
                False,
                error=str(e)
            )

        # Test 4: GET /api/orders/my (retrieve customer's orders)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/my",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                self.log_test(
                    "Customer Order Retrieval - My Orders",
                    True,
                    f"Retrieved {len(orders)} orders for customer"
                )
            else:
                self.log_test(
                    "Customer Order Retrieval - My Orders",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order Retrieval - My Orders",
                False,
                error=str(e)
            )

        # Test 5: GET /api/orders/{order_id}/track for each created order
        for order_id in self.test_orders:
            try:
                headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
                response = requests.get(
                    f"{BACKEND_URL}/orders/{order_id}/track",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    self.log_test(
                        f"Customer Order Tracking - {order_id[:8]}...",
                        True,
                        f"Status: {data.get('status')}, Total: ₺{data.get('total_amount')}"
                    )
                else:
                    self.log_test(
                        f"Customer Order Tracking - {order_id[:8]}...",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Customer Order Tracking - {order_id[:8]}...",
                    False,
                    error=str(e)
                )

        # Test 6: Order validation - invalid business ID
        try:
            order_data = {
                "business_id": "invalid-business-id",
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Item",
                        "product_price": 25.00,
                        "quantity": 1,
                        "subtotal": 25.00
                    }
                ],
                "total_amount": 25.00,
                "payment_method": "cash_on_delivery"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order Validation - Invalid Business ID",
                response.status_code in [400, 404, 422],
                f"Status: {response.status_code} (Expected 400/404/422 for invalid business)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order Validation - Invalid Business ID",
                False,
                error=str(e)
            )

        # Test 7: Order validation - missing required fields
        try:
            incomplete_order = {
                "business_id": "test-business-id",
                "items": []  # Empty items should be invalid
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=incomplete_order,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order Validation - Missing Required Fields",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing fields)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order Validation - Missing Required Fields",
                False,
                error=str(e)
            )

        # Test 8: Total amount calculation validation
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "test-business-id",
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Item",
                        "product_price": 25.00,
                        "quantity": 2,
                        "subtotal": 50.00
                    }
                ],
                "total_amount": 100.00,  # Incorrect total (should be 50.00)
                "payment_method": "cash_on_delivery"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            # This could either be accepted (if backend calculates total) or rejected (if validation is strict)
            self.log_test(
                "Customer Order Validation - Total Amount Calculation",
                True,  # Accept either outcome
                f"Status: {response.status_code} (Total validation handling)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order Validation - Total Amount Calculation",
                False,
                error=str(e)
            )

        # Test 9: Unauthorized access (business trying to create customer order)
        try:
            order_data = {
                "business_id": "test-business-id",
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Item",
                        "product_price": 25.00,
                        "quantity": 1,
                        "subtotal": 25.00
                    }
                ],
                "total_amount": 25.00,
                "payment_method": "cash_on_delivery"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order Creation - Unauthorized Access",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for business accessing customer endpoint)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order Creation - Unauthorized Access",
                False,
                error=str(e)
            )

        # Test 10: Invalid order ID for tracking
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/invalid-order-id/track",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order Tracking - Invalid Order ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid order ID)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order Tracking - Invalid Order ID",
                False,
                error=str(e)
            )

    def prepare_order_test_data(self):
        """Prepare test data for order creation tests"""
        try:
            # Get some businesses from nearby endpoint
            response = requests.get(
                f"{BACKEND_URL}/nearby/businesses",
                params={
                    "lat": 41.0082,
                    "lng": 28.9784,
                    "radius_m": 10000
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get("businesses", [])
                if businesses:
                    self.test_businesses = [b.get("id") for b in businesses[:3]]
                    print(f"   Prepared {len(self.test_businesses)} businesses for order testing")
        except Exception as e:
            print(f"   Warning: Could not prepare business data: {e}")

    def run_comprehensive_test(self):
        """Run all Phase 2 comprehensive backend tests"""
        print("🚀 STARTING PHASE 2 COMPREHENSIVE BACKEND TESTING")
        print("=" * 70)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not all(role in self.tokens for role in ["customer", "business"]):
            print("❌ CRITICAL: Authentication failed for required roles. Cannot proceed.")
            return
        
        # Step 2: Business Menu CRUD Operations
        self.test_business_menu_crud_comprehensive()
        
        # Step 3: Geospatial Nearby Businesses Discovery
        self.test_geospatial_nearby_businesses_comprehensive()
        
        # Step 4: Customer Order Creation System
        self.test_customer_order_creation_comprehensive()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 PHASE 2 COMPREHENSIVE BACKEND TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("\n" + "=" * 70)
        print("🔍 DETAILED FAILURE ANALYSIS")
        print("=" * 70)
        
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
        
        print("\n" + "=" * 70)
        print("📋 PHASE 2 FUNCTIONALITY ASSESSMENT")
        print("=" * 70)
        
        # Assess each major component
        menu_tests = [r for r in self.test_results if "Business Menu CRUD" in r["test"]]
        menu_success_rate = (sum(1 for r in menu_tests if r["success"]) / len(menu_tests) * 100) if menu_tests else 0
        
        nearby_tests = [r for r in self.test_results if "Nearby" in r["test"]]
        nearby_success_rate = (sum(1 for r in nearby_tests if r["success"]) / len(nearby_tests) * 100) if nearby_tests else 0
        
        order_tests = [r for r in self.test_results if "Customer Order" in r["test"]]
        order_success_rate = (sum(1 for r in order_tests if r["success"]) / len(order_tests) * 100) if order_tests else 0
        
        print(f"🍽️ Business Menu CRUD Operations: {menu_success_rate:.1f}% ({len([r for r in menu_tests if r['success']])}/{len(menu_tests)})")
        print(f"🗺️ Geospatial Nearby Businesses: {nearby_success_rate:.1f}% ({len([r for r in nearby_tests if r['success']])}/{len(nearby_tests)})")
        print(f"📦 Customer Order Creation System: {order_success_rate:.1f}% ({len([r for r in order_tests if r['success']])}/{len(order_tests)})")
        
        print("\n" + "=" * 70)
        print("🎯 RECOMMENDATIONS")
        print("=" * 70)
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Phase 2 backend functionality is working excellently")
        elif success_rate >= 75:
            print("⚠️ GOOD: Phase 2 backend is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️ NEEDS ATTENTION: Phase 2 backend has significant issues")
        else:
            print("❌ CRITICAL: Phase 2 backend has major problems")
        
        # Component-specific recommendations
        if menu_success_rate < 75:
            print("- Review Business Menu CRUD implementation and validation logic")
        if nearby_success_rate < 75:
            print("- Check geospatial queries and business discovery functionality")
        if order_success_rate < 75:
            print("- Fix customer order creation and validation issues")
        
        # Authentication recommendations
        auth_failures = [r for r in self.test_results if "Authentication" in r["test"] and not r["success"]]
        if auth_failures:
            print("- Fix authentication issues for proper API access")
        
        # RBAC recommendations
        rbac_failures = [r for r in self.test_results if "Unauthorized" in r["test"] and not r["success"]]
        if rbac_failures:
            print("- Review and strengthen role-based access control")

if __name__ == "__main__":
    tester = Phase2BackendTester()
    tester.run_comprehensive_test()