#!/usr/bin/env python3
"""
Complete E2E Food Delivery Workflow Backend Testing
Testing the full customer journey from business menu creation to order completion

REQUIRED WORKFLOW CHAIN:
1. Business Menu Creation - İşletme menü oluşturma (testbusiness@example.com / test123)
2. Customer Nearby Discovery - Müşteri yakın işletme keşfi (customer location-based)
3. Customer Menu Access - Müşteri işletme menülerini görebilme 
4. Customer Order Creation - Müşteri sipariş oluşturma
5. Business Order Management - İşletme sipariş onaylama/reddetme
6. Courier Order Assignment - Kurye sipariş alma ve teslim
7. Customer Rating - Müşteri değerlendirme sistemi

Authentication Details:
- Business: testbusiness@example.com / test123 (KYC approved)
- Customer: testcustomer@example.com / test123  
- Courier: testkurye@example.com / test123
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Test Users
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"
CUSTOMER_EMAIL = "testcustomer@example.com"
CUSTOMER_PASSWORD = "test123"
COURIER_EMAIL = "testkurye@example.com"
COURIER_PASSWORD = "test123"

class E2EFoodDeliveryTester:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.customer_token = None
        self.courier_token = None
        self.business_id = None
        self.customer_id = None
        self.courier_id = None
        self.test_results = []
        self.created_products = []
        self.created_order_id = None
        
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
        """Authenticate all test users"""
        print("🔐 AUTHENTICATING TEST USERS...")
        
        # Authenticate Business User
        try:
            login_data = {"email": BUSINESS_EMAIL, "password": BUSINESS_PASSWORD}
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.business_token = data.get("access_token")
                user_data = data.get("user", {})
                self.business_id = user_data.get("id")
                
                if self.business_token:
                    self.log_test("Business Authentication", True, 
                                f"Business authenticated successfully, ID: {self.business_id}, token length: {len(self.business_token)}")
                else:
                    self.log_test("Business Authentication", False, "No access token received")
            else:
                self.log_test("Business Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Business Authentication", False, f"Authentication error: {str(e)}")
        
        # Authenticate Customer User
        try:
            login_data = {"email": CUSTOMER_EMAIL, "password": CUSTOMER_PASSWORD}
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                user_data = data.get("user", {})
                self.customer_id = user_data.get("id")
                
                if self.customer_token:
                    self.log_test("Customer Authentication", True, 
                                f"Customer authenticated successfully, ID: {self.customer_id}, token length: {len(self.customer_token)}")
                else:
                    self.log_test("Customer Authentication", False, "No access token received")
            else:
                self.log_test("Customer Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Authentication error: {str(e)}")
        
        # Authenticate Courier User
        try:
            login_data = {"email": COURIER_EMAIL, "password": COURIER_PASSWORD}
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.courier_token = data.get("access_token")
                user_data = data.get("user", {})
                self.courier_id = user_data.get("id")
                
                if self.courier_token:
                    self.log_test("Courier Authentication", True, 
                                f"Courier authenticated successfully, ID: {self.courier_id}, token length: {len(self.courier_token)}")
                else:
                    self.log_test("Courier Authentication", False, "No access token received")
            else:
                self.log_test("Courier Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Courier Authentication", False, f"Authentication error: {str(e)}")

    def test_business_menu_creation(self):
        """Test Step 1: Business Menu Creation"""
        print("\n🍽️ TESTING BUSINESS MENU CREATION")
        
        if not self.business_token:
            self.log_test("Business Menu Creation", False, "Business authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.business_token}"}
        
        # Test creating multiple menu items
        menu_items = [
            {
                "name": "Margherita Pizza",
                "description": "Classic pizza with tomato sauce, mozzarella, and fresh basil",
                "price": 45.0,
                "category": "Pizza",
                "preparation_time_minutes": 25,
                "is_available": True
            },
            {
                "name": "Chicken Burger",
                "description": "Grilled chicken breast with lettuce, tomato, and special sauce",
                "price": 35.0,
                "category": "Burger",
                "preparation_time_minutes": 15,
                "is_available": True
            },
            {
                "name": "Caesar Salad",
                "description": "Fresh romaine lettuce with caesar dressing and croutons",
                "price": 25.0,
                "category": "Salad",
                "preparation_time_minutes": 10,
                "is_available": True
            }
        ]
        
        created_count = 0
        for item in menu_items:
            try:
                # Try different possible endpoints for product creation
                endpoints_to_try = [
                    "/products",
                    "/business/products", 
                    "/business/menu",
                    "/menu/items"
                ]
                
                product_created = False
                for endpoint in endpoints_to_try:
                    try:
                        response = requests.post(f"{BACKEND_URL}{endpoint}", json=item, headers=headers)
                        if response.status_code in [200, 201]:
                            data = response.json()
                            product_id = data.get("id") or data.get("product_id") or data.get("_id")
                            if product_id:
                                self.created_products.append(product_id)
                                created_count += 1
                                product_created = True
                                self.log_test(f"Create Menu Item: {item['name']}", True, 
                                            f"Created via {endpoint}, ID: {product_id}")
                                break
                    except Exception as e:
                        continue
                
                if not product_created:
                    self.log_test(f"Create Menu Item: {item['name']}", False, 
                                "Failed to create via any endpoint")
                        
            except Exception as e:
                self.log_test(f"Create Menu Item: {item['name']}", False, f"Error: {str(e)}")
        
        # Test retrieving business's own products
        try:
            endpoints_to_try = [
                "/products/my",
                "/business/products",
                "/business/menu"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        products = data if isinstance(data, list) else data.get("products", [])
                        self.log_test("Retrieve Business Menu", True, 
                                    f"Retrieved {len(products)} products via {endpoint}")
                        break
                except Exception:
                    continue
            else:
                self.log_test("Retrieve Business Menu", False, "Failed to retrieve via any endpoint")
                
        except Exception as e:
            self.log_test("Retrieve Business Menu", False, f"Error: {str(e)}")

    def test_customer_nearby_discovery(self):
        """Test Step 2: Customer Nearby Discovery"""
        print("\n🔍 TESTING CUSTOMER NEARBY DISCOVERY")
        
        # Test nearby businesses endpoint (no auth required for public discovery)
        try:
            # Test with location parameters (Istanbul coordinates)
            params = {
                "lat": 41.0082,
                "lng": 28.9784,
                "radius": 5000
            }
            
            response = requests.get(f"{BACKEND_URL}/nearby/businesses", params=params)
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test("GET /api/nearby/businesses", True, 
                            f"Found {len(businesses)} nearby businesses")
            else:
                self.log_test("GET /api/nearby/businesses", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/nearby/businesses", False, f"Error: {str(e)}")
        
        # Test general businesses endpoint
        try:
            response = requests.get(f"{BACKEND_URL}/businesses")
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                self.log_test("GET /api/businesses", True, 
                            f"Found {len(businesses)} total businesses")
                
                # Check if our test business is visible
                test_business_found = False
                for business in businesses:
                    if business.get("id") == self.business_id or business.get("email") == BUSINESS_EMAIL:
                        test_business_found = True
                        break
                
                if test_business_found:
                    self.log_test("Test Business Visibility", True, "Test business is visible to customers")
                else:
                    self.log_test("Test Business Visibility", False, "Test business not found in public listing")
                    
            else:
                self.log_test("GET /api/businesses", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/businesses", False, f"Error: {str(e)}")

    def test_customer_menu_access(self):
        """Test Step 3: Customer Menu Access"""
        print("\n📋 TESTING CUSTOMER MENU ACCESS")
        
        if not self.business_id:
            self.log_test("Customer Menu Access", False, "Business ID required")
            return
        
        # Test accessing business menu as customer
        try:
            response = requests.get(f"{BACKEND_URL}/businesses/{self.business_id}/products")
            if response.status_code == 200:
                data = response.json()
                products = data if isinstance(data, list) else data.get("products", [])
                self.log_test("GET /api/businesses/{id}/products", True, 
                            f"Retrieved {len(products)} products from business menu")
                
                # Verify our created products are accessible
                if len(products) > 0:
                    sample_product = products[0]
                    required_fields = ["name", "price", "description"]
                    has_required_fields = all(field in sample_product for field in required_fields)
                    self.log_test("Menu Product Structure", has_required_fields, 
                                f"Products have required fields: {required_fields}")
                else:
                    self.log_test("Menu Product Availability", False, "No products found in business menu")
                    
            else:
                self.log_test("GET /api/businesses/{id}/products", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/businesses/{id}/products", False, f"Error: {str(e)}")

    def test_customer_order_creation(self):
        """Test Step 4: Customer Order Creation"""
        print("\n🛒 TESTING CUSTOMER ORDER CREATION")
        
        if not self.customer_token or not self.business_id:
            self.log_test("Customer Order Creation", False, "Customer authentication and business ID required")
            return
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        # Create a test order
        order_data = {
            "business_id": self.business_id,
            "delivery_address": "Test Address, Istanbul, Turkey",
            "delivery_lat": 41.0082,
            "delivery_lng": 28.9784,
            "items": [
                {
                    "product_id": self.created_products[0] if self.created_products else "test-product-1",
                    "product_name": "Margherita Pizza",
                    "product_price": 45.0,
                    "quantity": 2,
                    "subtotal": 90.0
                },
                {
                    "product_id": self.created_products[1] if len(self.created_products) > 1 else "test-product-2",
                    "product_name": "Chicken Burger", 
                    "product_price": 35.0,
                    "quantity": 1,
                    "subtotal": 35.0
                }
            ],
            "total_amount": 125.0,
            "notes": "Please ring the doorbell"
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/orders", json=order_data, headers=headers)
            if response.status_code in [200, 201]:
                data = response.json()
                self.created_order_id = data.get("id") or data.get("order_id") or data.get("_id")
                self.log_test("POST /api/orders", True, 
                            f"Order created successfully, ID: {self.created_order_id}")
            else:
                self.log_test("POST /api/orders", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/orders", False, f"Error: {str(e)}")

    def test_business_order_management(self):
        """Test Step 5: Business Order Management"""
        print("\n🏪 TESTING BUSINESS ORDER MANAGEMENT")
        
        if not self.business_token:
            self.log_test("Business Order Management", False, "Business authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.business_token}"}
        
        # Test getting incoming orders
        try:
            response = requests.get(f"{BACKEND_URL}/business/orders/incoming", headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", []) if isinstance(data, dict) else data
                self.log_test("GET /api/business/orders/incoming", True, 
                            f"Retrieved {len(orders)} incoming orders")
                
                # If we have orders, test updating order status
                if orders and self.created_order_id:
                    try:
                        status_update = {"status": "confirmed"}
                        response = requests.patch(
                            f"{BACKEND_URL}/business/orders/{self.created_order_id}/status",
                            json=status_update,
                            headers=headers
                        )
                        if response.status_code == 200:
                            self.log_test("Business Order Approval", True, 
                                        "Successfully confirmed order")
                        else:
                            self.log_test("Business Order Approval", False, 
                                        f"Status: {response.status_code}, Response: {response.text}")
                    except Exception as e:
                        self.log_test("Business Order Approval", False, f"Error: {str(e)}")
                        
            else:
                self.log_test("GET /api/business/orders/incoming", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/business/orders/incoming", False, f"Error: {str(e)}")

    def test_courier_order_assignment(self):
        """Test Step 6: Courier Order Assignment"""
        print("\n🚚 TESTING COURIER ORDER ASSIGNMENT")
        
        if not self.courier_token:
            self.log_test("Courier Order Assignment", False, "Courier authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.courier_token}"}
        
        # Test getting available orders for courier
        try:
            response = requests.get(f"{BACKEND_URL}/courier/orders/available", headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", []) if isinstance(data, dict) else data
                self.log_test("GET /api/courier/orders/available", True, 
                            f"Retrieved {len(orders)} available orders")
                
                # If we have orders, test picking up an order
                if orders and self.created_order_id:
                    try:
                        response = requests.patch(
                            f"{BACKEND_URL}/courier/orders/{self.created_order_id}/pickup",
                            headers=headers
                        )
                        if response.status_code == 200:
                            self.log_test("Courier Order Pickup", True, 
                                        "Successfully picked up order")
                            
                            # Test updating order status to delivered
                            try:
                                status_update = {"status": "delivered"}
                                response = requests.patch(
                                    f"{BACKEND_URL}/courier/orders/{self.created_order_id}/status",
                                    json=status_update,
                                    headers=headers
                                )
                                if response.status_code == 200:
                                    self.log_test("Courier Order Delivery", True, 
                                                "Successfully marked order as delivered")
                                else:
                                    self.log_test("Courier Order Delivery", False, 
                                                f"Status: {response.status_code}, Response: {response.text}")
                            except Exception as e:
                                self.log_test("Courier Order Delivery", False, f"Error: {str(e)}")
                                
                        else:
                            self.log_test("Courier Order Pickup", False, 
                                        f"Status: {response.status_code}, Response: {response.text}")
                    except Exception as e:
                        self.log_test("Courier Order Pickup", False, f"Error: {str(e)}")
                        
            else:
                self.log_test("GET /api/courier/orders/available", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/courier/orders/available", False, f"Error: {str(e)}")

    def test_customer_rating_system(self):
        """Test Step 7: Customer Rating System"""
        print("\n⭐ TESTING CUSTOMER RATING SYSTEM")
        
        if not self.customer_token or not self.created_order_id:
            self.log_test("Customer Rating System", False, "Customer authentication and completed order required")
            return
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        # Test rating the business
        try:
            rating_data = {
                "order_id": self.created_order_id,
                "target_type": "business",
                "target_id": self.business_id,
                "rating": 5,
                "comment": "Excellent food and fast service!"
            }
            
            response = requests.post(f"{BACKEND_URL}/reviews", json=rating_data, headers=headers)
            if response.status_code in [200, 201]:
                self.log_test("Customer Business Rating", True, 
                            "Successfully rated business")
            else:
                self.log_test("Customer Business Rating", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Business Rating", False, f"Error: {str(e)}")
        
        # Test rating the courier
        try:
            rating_data = {
                "order_id": self.created_order_id,
                "target_type": "courier",
                "target_id": self.courier_id,
                "rating": 4,
                "comment": "Good delivery service"
            }
            
            response = requests.post(f"{BACKEND_URL}/reviews", json=rating_data, headers=headers)
            if response.status_code in [200, 201]:
                self.log_test("Customer Courier Rating", True, 
                            "Successfully rated courier")
            else:
                self.log_test("Customer Courier Rating", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Courier Rating", False, f"Error: {str(e)}")

    def test_order_tracking(self):
        """Test Customer Order Tracking"""
        print("\n📍 TESTING CUSTOMER ORDER TRACKING")
        
        if not self.customer_token:
            self.log_test("Customer Order Tracking", False, "Customer authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        
        # Test getting customer's orders
        try:
            response = requests.get(f"{BACKEND_URL}/orders/my", headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get("orders", [])
                self.log_test("GET /api/orders/my", True, 
                            f"Retrieved {len(orders)} customer orders")
            else:
                self.log_test("GET /api/orders/my", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/orders/my", False, f"Error: {str(e)}")
        
        # Test tracking specific order
        if self.created_order_id:
            try:
                response = requests.get(f"{BACKEND_URL}/orders/{self.created_order_id}/track", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("GET /api/orders/{id}/track", True, 
                                f"Successfully tracked order status")
                else:
                    self.log_test("GET /api/orders/{id}/track", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test("GET /api/orders/{id}/track", False, f"Error: {str(e)}")

    def run_complete_e2e_test(self):
        """Run the complete E2E food delivery workflow test"""
        print("🚀 STARTING COMPLETE E2E FOOD DELIVERY WORKFLOW TESTING")
        print("=" * 70)
        
        # Step 0: Authentication
        self.authenticate_users()
        
        # Step 1: Business Menu Creation
        self.test_business_menu_creation()
        
        # Step 2: Customer Nearby Discovery
        self.test_customer_nearby_discovery()
        
        # Step 3: Customer Menu Access
        self.test_customer_menu_access()
        
        # Step 4: Customer Order Creation
        self.test_customer_order_creation()
        
        # Step 5: Business Order Management
        self.test_business_order_management()
        
        # Step 6: Courier Order Assignment
        self.test_courier_order_assignment()
        
        # Step 7: Customer Rating System
        self.test_customer_rating_system()
        
        # Additional: Order Tracking
        self.test_order_tracking()
        
        # Generate comprehensive summary
        self.generate_e2e_summary()

    def generate_e2e_summary(self):
        """Generate comprehensive E2E test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPLETE E2E FOOD DELIVERY WORKFLOW TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Workflow step analysis
        workflow_steps = {
            "Authentication": ["Business Authentication", "Customer Authentication", "Courier Authentication"],
            "Business Menu Creation": ["Create Menu Item", "Retrieve Business Menu"],
            "Customer Discovery": ["GET /api/nearby/businesses", "GET /api/businesses", "Test Business Visibility"],
            "Menu Access": ["GET /api/businesses/{id}/products", "Menu Product Structure", "Menu Product Availability"],
            "Order Creation": ["POST /api/orders"],
            "Business Management": ["GET /api/business/orders/incoming", "Business Order Approval"],
            "Courier Assignment": ["GET /api/courier/orders/available", "Courier Order Pickup", "Courier Order Delivery"],
            "Rating System": ["Customer Business Rating", "Customer Courier Rating"],
            "Order Tracking": ["GET /api/orders/my", "GET /api/orders/{id}/track"]
        }
        
        print("\n🔍 WORKFLOW STEP ANALYSIS:")
        for step_name, test_names in workflow_steps.items():
            step_tests = [t for t in self.test_results if any(test_name in t["test"] for test_name in test_names)]
            step_passed = len([t for t in step_tests if t["success"]])
            step_total = len(step_tests)
            step_rate = (step_passed / step_total * 100) if step_total > 0 else 0
            
            status = "✅" if step_rate == 100 else "⚠️" if step_rate >= 50 else "❌"
            print(f"{status} {step_name}: {step_passed}/{step_total} ({step_rate:.1f}%)")
        
        print("\n🚨 CRITICAL FINDINGS:")
        
        # Authentication issues
        auth_failures = [t for t in self.test_results if "Authentication" in t["test"] and not t["success"]]
        if auth_failures:
            print(f"❌ AUTHENTICATION FAILURES: {len(auth_failures)} user types cannot authenticate")
            for failure in auth_failures:
                print(f"   - {failure['test']}: {failure['details']}")
        
        # Missing endpoints
        missing_endpoints = [t for t in self.test_results if not t["success"] and ("404" in t["error"] or "not found" in t["details"].lower())]
        if missing_endpoints:
            print(f"❌ MISSING ENDPOINTS: {len(missing_endpoints)} critical endpoints not implemented")
            for endpoint in missing_endpoints:
                print(f"   - {endpoint['test']}")
        
        # Workflow breaks
        critical_failures = [t for t in self.test_results if not t["success"] and any(critical in t["test"] for critical in ["Order Creation", "Order Management", "Menu Creation"])]
        if critical_failures:
            print(f"❌ WORKFLOW BREAKS: {len(critical_failures)} critical workflow steps failing")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['details']}")
        
        print(f"\n📝 E2E WORKFLOW CONCLUSION:")
        if success_rate >= 90:
            print("✅ EXCELLENT: Complete E2E food delivery workflow is fully functional")
            print("   All major components working correctly - ready for production")
        elif success_rate >= 75:
            print("✅ GOOD: E2E food delivery workflow is mostly functional")
            print("   Core functionality working with minor issues")
        elif success_rate >= 50:
            print("⚠️ WARNING: E2E food delivery workflow has significant issues")
            print("   Some components working but critical gaps exist")
        else:
            print("❌ CRITICAL: E2E food delivery workflow is NOT functional")
            print("   Major implementation gaps - workflow cannot complete")
        
        # Specific workflow readiness
        print(f"\n🎯 WORKFLOW READINESS:")
        print(f"   Business Menu Management: {'✅ Ready' if any('Menu' in t['test'] and t['success'] for t in self.test_results) else '❌ Not Ready'}")
        print(f"   Customer Discovery: {'✅ Ready' if any('businesses' in t['test'] and t['success'] for t in self.test_results) else '❌ Not Ready'}")
        print(f"   Order Processing: {'✅ Ready' if any('orders' in t['test'] and t['success'] for t in self.test_results) else '❌ Not Ready'}")
        print(f"   Courier System: {'✅ Ready' if any('Courier' in t['test'] and t['success'] for t in self.test_results) else '❌ Not Ready'}")
        print(f"   Rating System: {'✅ Ready' if any('Rating' in t['test'] and t['success'] for t in self.test_results) else '❌ Not Ready'}")

if __name__ == "__main__":
    tester = E2EFoodDeliveryTester()
    tester.run_complete_e2e_test()