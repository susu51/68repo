#!/usr/bin/env python3
"""
PHASE 2 ACTUAL BACKEND TESTING
Testing the actual available endpoints based on the backend implementation.

ACTUAL AVAILABLE ENDPOINTS:

1. Business Product Management:
   - POST /api/products (create product with business authentication)
   - GET /api/products/my (get business's own products)
   - DELETE /api/products/{product_id} (delete product)

2. Business Discovery:
   - GET /api/businesses (get all businesses)
   - GET /api/businesses/{business_id}/products (get specific business products)

3. Customer Order System:
   - POST /api/orders (create order)
   - GET /api/orders/my (customer's orders)
   - GET /api/orders/{order_id}/track (order tracking)

Authentication:
- Business: testbusiness@example.com / test123
- Customer: testcustomer@example.com / test123
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://deliver-yemek.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"}
}

class Phase2ActualBackendTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.business_id = None
        self.customer_id = None
        self.test_products = []
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

    def test_business_product_management(self):
        """Test Business Product Management - Using actual endpoints"""
        print("🍽️ TESTING BUSINESS PRODUCT MANAGEMENT - ACTUAL ENDPOINTS...")
        
        if not self.business_id or "business" not in self.tokens:
            self.log_test(
                "Business Product Management - Setup",
                False,
                error="Business authentication required"
            )
            return

        # Test 1: POST /api/products (create product with business authentication)
        try:
            product_data = {
                "title": "Deluxe Burger Menu",  # Using 'title' instead of 'name' based on error
                "description": "Premium beef burger with fries and drink",
                "price": 45.50,
                "category": "Ana Yemek",
                "preparation_time_minutes": 25,
                "is_available": True
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/products",
                json=product_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                product_id = data.get("id") or data.get("product_id")
                self.test_products.append(product_id)
                
                self.log_test(
                    "Business Product Management - Create Product",
                    True,
                    f"Product created: {product_id}, Title: {data.get('title')}, Price: ₺{data.get('price')}"
                )
            else:
                self.log_test(
                    "Business Product Management - Create Product",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Product Management - Create Product",
                False,
                error=str(e)
            )

        # Test 2: GET /api/products/my (get business's own products)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/products/my",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data if isinstance(data, list) else data.get("products", [])
                
                self.log_test(
                    "Business Product Management - Get My Products",
                    True,
                    f"Retrieved {len(products)} products for business"
                )
            else:
                self.log_test(
                    "Business Product Management - Get My Products",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Product Management - Get My Products",
                False,
                error=str(e)
            )

        # Test 3: Create another product for delete test
        try:
            product_data = {
                "title": "Chicken Pizza",
                "description": "Delicious chicken pizza with vegetables",
                "price": 35.00,
                "category": "Pizza",
                "preparation_time_minutes": 20,
                "is_available": True
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/products",
                json=product_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                product_id = data.get("id") or data.get("product_id")
                self.test_products.append(product_id)
                
                # Test 4: DELETE /api/products/{product_id} (delete product)
                delete_response = requests.delete(
                    f"{BACKEND_URL}/products/{product_id}",
                    headers=headers,
                    timeout=10
                )
                
                if delete_response.status_code in [200, 204]:
                    self.log_test(
                        "Business Product Management - Delete Product",
                        True,
                        f"Successfully deleted product: {product_id}"
                    )
                    # Remove from test list since it's deleted
                    if product_id in self.test_products:
                        self.test_products.remove(product_id)
                else:
                    self.log_test(
                        "Business Product Management - Delete Product",
                        False,
                        f"Status: {delete_response.status_code}",
                        delete_response.text
                    )
                    
            else:
                self.log_test(
                    "Business Product Management - Create Second Product",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Product Management - Delete Test",
                False,
                error=str(e)
            )

        # Test 5: Validation tests - price validation, required fields
        try:
            # Test invalid price
            invalid_price_data = {
                "title": "Invalid Price Item",
                "description": "Test item with invalid price",
                "price": -10.00,  # Negative price should be invalid
                "category": "Test"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/products",
                json=invalid_price_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Product Management - Price Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for negative price)"
            )
        except Exception as e:
            self.log_test(
                "Business Product Management - Price Validation",
                False,
                error=str(e)
            )

        # Test 6: Required fields validation
        try:
            # Test missing required fields
            incomplete_data = {
                "description": "Missing title and price"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.post(
                f"{BACKEND_URL}/products",
                json=incomplete_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Product Management - Required Fields Validation",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing required fields)"
            )
        except Exception as e:
            self.log_test(
                "Business Product Management - Required Fields Validation",
                False,
                error=str(e)
            )

        # Test 7: Unauthorized access (customer trying to access business endpoints)
        try:
            product_data = {
                "title": "Unauthorized Item",
                "description": "This should fail",
                "price": 25.00,
                "category": "Test"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/products",
                json=product_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Product Management - Unauthorized Access",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for customer accessing business endpoint)"
            )
        except Exception as e:
            self.log_test(
                "Business Product Management - Unauthorized Access",
                False,
                error=str(e)
            )

        # Test 8: Invalid product ID for delete
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.delete(
                f"{BACKEND_URL}/products/invalid-product-id",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Business Product Management - Invalid Product ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid product ID)"
            )
        except Exception as e:
            self.log_test(
                "Business Product Management - Invalid Product ID",
                False,
                error=str(e)
            )

    def test_business_discovery(self):
        """Test Business Discovery - Using actual endpoints"""
        print("🗺️ TESTING BUSINESS DISCOVERY - ACTUAL ENDPOINTS...")

        # Test 1: GET /api/businesses (get all businesses)
        try:
            response = requests.get(
                f"{BACKEND_URL}/businesses",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                # Store businesses for later tests
                if businesses:
                    self.test_businesses = [b.get("id") for b in businesses[:3]]  # Store first 3
                
                self.log_test(
                    "Business Discovery - Get All Businesses",
                    True,
                    f"Found {len(businesses)} businesses"
                )
            else:
                self.log_test(
                    "Business Discovery - Get All Businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Discovery - Get All Businesses",
                False,
                error=str(e)
            )

        # Test 2: GET /api/businesses/{business_id}/products for specific businesses
        if self.test_businesses:
            for business_id in self.test_businesses[:2]:  # Test first 2 businesses
                try:
                    response = requests.get(
                        f"{BACKEND_URL}/businesses/{business_id}/products",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        products = data if isinstance(data, list) else data.get("products", [])
                        
                        self.log_test(
                            f"Business Discovery - Business Products {business_id[:8]}...",
                            True,
                            f"Retrieved {len(products)} products for business"
                        )
                    else:
                        self.log_test(
                            f"Business Discovery - Business Products {business_id[:8]}...",
                            False,
                            f"Status: {response.status_code}",
                            response.text
                        )
                except Exception as e:
                    self.log_test(
                        f"Business Discovery - Business Products {business_id[:8]}...",
                        False,
                        error=str(e)
                    )

        # Test 3: Invalid business ID
        try:
            response = requests.get(
                f"{BACKEND_URL}/businesses/invalid-business-id/products",
                timeout=10
            )
            
            self.log_test(
                "Business Discovery - Invalid Business ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid business ID)"
            )
        except Exception as e:
            self.log_test(
                "Business Discovery - Invalid Business ID",
                False,
                error=str(e)
            )

    def test_customer_order_system(self):
        """Test Customer Order System - Using actual endpoints"""
        print("📦 TESTING CUSTOMER ORDER SYSTEM - ACTUAL ENDPOINTS...")
        
        if not self.customer_id or "customer" not in self.tokens:
            self.log_test(
                "Customer Order System - Setup",
                False,
                error="Customer authentication required"
            )
            return

        # Test 1: POST /api/orders with cash_on_delivery payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "business-001",
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
                    "Customer Order System - Create Order (Cash on Delivery)",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}"
                )
            else:
                self.log_test(
                    "Customer Order System - Create Order (Cash on Delivery)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Create Order (Cash on Delivery)",
                False,
                error=str(e)
            )

        # Test 2: POST /api/orders with online payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "business-001",
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
                    "Customer Order System - Create Order (Online Payment)",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}"
                )
            else:
                self.log_test(
                    "Customer Order System - Create Order (Online Payment)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Create Order (Online Payment)",
                False,
                error=str(e)
            )

        # Test 3: POST /api/orders with pos_on_delivery payment method
        try:
            order_data = {
                "business_id": self.test_businesses[0] if self.test_businesses else "business-001",
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
                    }
                ],
                "total_amount": 55.00,
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
                    "Customer Order System - Create Order (POS on Delivery)",
                    True,
                    f"Order created: {order_id}, Total: ₺{data.get('total_amount')}"
                )
            else:
                self.log_test(
                    "Customer Order System - Create Order (POS on Delivery)",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer Order System - Create Order (POS on Delivery)",
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
                # Handle both list and object responses
                if isinstance(data, list):
                    orders = data
                else:
                    orders = data.get("orders", [])
                
                self.log_test(
                    "Customer Order System - Get My Orders",
                    True,
                    f"Retrieved {len(orders)} orders for customer"
                )
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
                        f"Customer Order System - Track Order {order_id[:8]}...",
                        True,
                        f"Status: {data.get('status')}, Total: ₺{data.get('total_amount')}"
                    )
                else:
                    self.log_test(
                        f"Customer Order System - Track Order {order_id[:8]}...",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Customer Order System - Track Order {order_id[:8]}...",
                    False,
                    error=str(e)
                )

        # Test 6: Order validation - missing required fields
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
                "Customer Order System - Validation (Missing Fields)",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for missing fields)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order System - Validation (Missing Fields)",
                False,
                error=str(e)
            )

        # Test 7: Unauthorized access (business trying to create customer order)
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
                "Customer Order System - Unauthorized Access",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for business accessing customer endpoint)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order System - Unauthorized Access",
                False,
                error=str(e)
            )

        # Test 8: Invalid order ID for tracking
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/invalid-order-id/track",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Customer Order System - Invalid Order ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for invalid order ID)"
            )
        except Exception as e:
            self.log_test(
                "Customer Order System - Invalid Order ID",
                False,
                error=str(e)
            )

    def run_comprehensive_test(self):
        """Run all Phase 2 actual backend tests"""
        print("🚀 STARTING PHASE 2 ACTUAL BACKEND TESTING")
        print("=" * 70)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not all(role in self.tokens for role in ["customer", "business"]):
            print("❌ CRITICAL: Authentication failed for required roles. Cannot proceed.")
            return
        
        # Step 2: Business Product Management
        self.test_business_product_management()
        
        # Step 3: Business Discovery
        self.test_business_discovery()
        
        # Step 4: Customer Order System
        self.test_customer_order_system()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 PHASE 2 ACTUAL BACKEND TEST SUMMARY")
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
        product_tests = [r for r in self.test_results if "Business Product Management" in r["test"]]
        product_success_rate = (sum(1 for r in product_tests if r["success"]) / len(product_tests) * 100) if product_tests else 0
        
        discovery_tests = [r for r in self.test_results if "Business Discovery" in r["test"]]
        discovery_success_rate = (sum(1 for r in discovery_tests if r["success"]) / len(discovery_tests) * 100) if discovery_tests else 0
        
        order_tests = [r for r in self.test_results if "Customer Order System" in r["test"]]
        order_success_rate = (sum(1 for r in order_tests if r["success"]) / len(order_tests) * 100) if order_tests else 0
        
        print(f"🍽️ Business Product Management: {product_success_rate:.1f}% ({len([r for r in product_tests if r['success']])}/{len(product_tests)})")
        print(f"🗺️ Business Discovery: {discovery_success_rate:.1f}% ({len([r for r in discovery_tests if r['success']])}/{len(discovery_tests)})")
        print(f"📦 Customer Order System: {order_success_rate:.1f}% ({len([r for r in order_tests if r['success']])}/{len(order_tests)})")
        
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
        if product_success_rate < 75:
            print("- Review Business Product Management implementation and validation logic")
        if discovery_success_rate < 75:
            print("- Check business discovery and product listing functionality")
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
    tester = Phase2ActualBackendTester()
    tester.run_comprehensive_test()