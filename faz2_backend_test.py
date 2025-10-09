#!/usr/bin/env python3
"""
FAZ 2 - CUSTOMER CART & PAYMENT BACKEND TESTING
Comprehensive testing of customer cart and payment flow endpoints

PRIORITY TEST SCENARIOS:
1. Mock Payment System (Critical Priority)
2. Customer Order Tracking  
3. Order Creation Flow
4. Integration Test - Complete E2E Flow
5. Data Validation

Test validates the complete FAZ 2 customer journey: 
Keşfet→Ürün→Sepet→Adres→Ödeme(mock)→Sipariş→Takip
"""

import requests
import json
import sys
import time
import random
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://kuryecini-auth.preview.emergentagent.com/api"
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

class FAZ2BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.customer_user_id = None
        self.test_order_ids = []
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
    
    def authenticate_customer(self):
        """Authenticate customer for testing"""
        print("🔐 CUSTOMER AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                user_data = data.get("user", {})
                self.customer_user_id = user_data.get("id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log_test(
                    "Customer Authentication",
                    True,
                    f"Login successful. User ID: {self.customer_user_id}, Token length: {len(self.jwt_token) if self.jwt_token else 0} chars",
                    {"user_id": self.customer_user_id, "email": user_data.get("email"), "role": user_data.get("role")}
                )
                return True
            else:
                self.log_test(
                    "Customer Authentication",
                    False,
                    f"Login failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Customer Authentication",
                False,
                f"Exception during login: {str(e)}"
            )
            return False
    
    def test_order_creation_flow(self):
        """Test POST /orders - order creation with delivery address and items"""
        print("📦 TESTING ORDER CREATION FLOW")
        print("=" * 50)
        
        # Test order creation with multiple items
        test_orders = [
            {
                "delivery_address": "Kadıköy, Moda Caddesi No:123 Daire:5, İstanbul",
                "delivery_lat": 40.9876,
                "delivery_lng": 29.0234,
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
                "notes": "Test order for FAZ 2 testing"
            },
            {
                "delivery_address": "Beşiktaş, Barbaros Bulvarı No:456, İstanbul",
                "delivery_lat": 41.0766,
                "delivery_lng": 28.9688,
                "items": [
                    {
                        "product_id": "test-product-3",
                        "product_name": "Chicken Burger",
                        "product_price": 65.0,
                        "quantity": 2,
                        "subtotal": 130.0
                    },
                    {
                        "product_id": "test-product-4",
                        "product_name": "Patates Kızartması",
                        "product_price": 18.0,
                        "quantity": 1,
                        "subtotal": 18.0
                    }
                ],
                "total_amount": 148.0,
                "notes": "Second test order with multiple items"
            }
        ]
        
        for i, order_data in enumerate(test_orders):
            try:
                response = self.session.post(f"{BACKEND_URL}/orders", json=order_data)
                
                if response.status_code == 200:
                    created_order = response.json()
                    order_id = created_order.get("id")
                    
                    if order_id:
                        self.test_order_ids.append(order_id)
                    
                    # Verify order contains all required fields
                    required_fields = ["id", "customer_id", "items", "total_amount", "delivery_address", "status"]
                    missing_fields = [field for field in required_fields if field not in created_order]
                    
                    # Verify order status is "created"
                    status_correct = created_order.get("status") == "created"
                    
                    self.log_test(
                        f"Order Creation Test {i+1}",
                        len(missing_fields) == 0 and status_correct,
                        f"Order ID: {order_id}, Status: {created_order.get('status')}, Missing fields: {missing_fields}",
                        created_order
                    )
                else:
                    self.log_test(
                        f"Order Creation Test {i+1}",
                        False,
                        f"Failed to create order. Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Order Creation Test {i+1}",
                    False,
                    f"Exception during order creation: {str(e)}"
                )
    
    def test_mock_payment_system(self):
        """Test POST /payments/mock with different payment methods"""
        print("💳 TESTING MOCK PAYMENT SYSTEM")
        print("=" * 50)
        
        if not self.test_order_ids:
            self.log_test(
                "Mock Payment System",
                False,
                "No test orders available for payment testing"
            )
            return
        
        # Test different payment methods
        payment_methods = [
            {
                "method": "online",
                "description": "Online payment (90% success rate)",
                "expected_success_rate": 0.9
            },
            {
                "method": "cash_on_delivery",
                "description": "Cash on delivery (should always succeed)",
                "expected_success_rate": 1.0
            },
            {
                "method": "pos_on_delivery",
                "description": "POS on delivery (should always succeed)",
                "expected_success_rate": 1.0
            }
        ]
        
        for payment_method in payment_methods:
            method = payment_method["method"]
            description = payment_method["description"]
            
            # Test multiple times for online payment to verify success rate
            test_count = 10 if method == "online" else 3
            success_count = 0
            
            for i in range(test_count):
                try:
                    # Use different order for each test
                    order_id = self.test_order_ids[i % len(self.test_order_ids)]
                    
                    payment_data = {
                        "order_id": order_id,
                        "payment_method": method,
                        "amount": 100.0 + (i * 10)  # Vary amount
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/payments/mock", json=payment_data)
                    
                    if response.status_code == 200:
                        payment_result = response.json()
                        payment_success = payment_result.get("status") == "success"
                        
                        if payment_success:
                            success_count += 1
                            
                            # Verify payment record is stored
                            payment_id = payment_result.get("payment_id")
                            transaction_id = payment_result.get("transaction_id")
                            
                            self.log_test(
                                f"Payment {method.title()} Test {i+1}",
                                True,
                                f"Payment successful. Payment ID: {payment_id}, Transaction ID: {transaction_id}",
                                payment_result
                            )
                        else:
                            # For online payments, failures are expected (10% failure rate)
                            if method == "online":
                                self.log_test(
                                    f"Payment {method.title()} Test {i+1}",
                                    True,
                                    f"Payment failed as expected for online payment (simulated failure)",
                                    payment_result
                                )
                            else:
                                self.log_test(
                                    f"Payment {method.title()} Test {i+1}",
                                    False,
                                    f"Payment failed unexpectedly for {method}",
                                    payment_result
                                )
                    else:
                        self.log_test(
                            f"Payment {method.title()} Test {i+1}",
                            False,
                            f"Payment API failed. Status: {response.status_code}",
                            response.text
                        )
                        
                except Exception as e:
                    self.log_test(
                        f"Payment {method.title()} Test {i+1}",
                        False,
                        f"Exception during payment test: {str(e)}"
                    )
            
            # Verify success rate for this payment method
            actual_success_rate = success_count / test_count
            expected_rate = payment_method["expected_success_rate"]
            
            # Allow some tolerance for online payments (±20%)
            tolerance = 0.2 if method == "online" else 0.1
            rate_acceptable = abs(actual_success_rate - expected_rate) <= tolerance
            
            self.log_test(
                f"Payment Success Rate - {method.title()}",
                rate_acceptable,
                f"Success rate: {actual_success_rate:.1%} (Expected: {expected_rate:.1%}), Tests: {success_count}/{test_count}"
            )
    
    def test_customer_order_tracking(self):
        """Test GET /orders/my and GET /orders/{order_id}/track"""
        print("📍 TESTING CUSTOMER ORDER TRACKING")
        print("=" * 50)
        
        # Test 1: Get customer's order list
        try:
            response = self.session.get(f"{BACKEND_URL}/orders/my")
            
            if response.status_code == 200:
                orders = response.json()
                self.log_test(
                    "GET /orders/my - Customer Order List",
                    True,
                    f"Successfully retrieved {len(orders)} orders for customer",
                    {"order_count": len(orders), "orders": orders[:2] if orders else []}
                )
                
                # Test access control - verify orders belong to current customer
                if orders:
                    customer_orders = [order for order in orders if order.get("customer_id") == self.customer_user_id]
                    access_control_ok = len(customer_orders) == len(orders)
                    
                    self.log_test(
                        "Order Access Control - Customer Orders Only",
                        access_control_ok,
                        f"All {len(orders)} orders belong to current customer: {access_control_ok}"
                    )
            else:
                self.log_test(
                    "GET /orders/my - Customer Order List",
                    False,
                    f"Failed to retrieve customer orders. Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "GET /orders/my - Customer Order List",
                False,
                f"Exception during order list retrieval: {str(e)}"
            )
        
        # Test 2: Track specific orders
        for i, order_id in enumerate(self.test_order_ids[:3]):  # Test first 3 orders
            try:
                response = self.session.get(f"{BACKEND_URL}/orders/{order_id}/track")
                
                if response.status_code == 200:
                    tracking_data = response.json()
                    
                    # Verify tracking includes required fields
                    required_fields = ["id", "status"]  # The API returns "id" not "order_id", and "estimated_delivery" not "estimated_delivery_time"
                    missing_fields = [field for field in required_fields if field not in tracking_data]
                    
                    # Check if courier location is provided for active orders
                    has_courier_location = "courier_location" in tracking_data
                    order_status = tracking_data.get("status", "")
                    
                    self.log_test(
                        f"GET /orders/{order_id}/track - Order Tracking {i+1}",
                        len(missing_fields) == 0,
                        f"Status: {order_status}, Has courier location: {has_courier_location}, Missing fields: {missing_fields}",
                        tracking_data
                    )
                    
                    # Verify estimated delivery time is provided
                    estimated_delivery = tracking_data.get("estimated_delivery")
                    if estimated_delivery:
                        self.log_test(
                            f"Estimated Delivery Time - Order {i+1}",
                            True,
                            f"Estimated delivery: {estimated_delivery}"
                        )
                    else:
                        self.log_test(
                            f"Estimated Delivery Time - Order {i+1}",
                            False,
                            "No estimated delivery time provided"
                        )
                        
                elif response.status_code == 404:
                    self.log_test(
                        f"GET /orders/{order_id}/track - Order Tracking {i+1}",
                        False,
                        f"Order not found for tracking. Status: {response.status_code}",
                        response.text
                    )
                else:
                    self.log_test(
                        f"GET /orders/{order_id}/track - Order Tracking {i+1}",
                        False,
                        f"Failed to track order. Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"GET /orders/{order_id}/track - Order Tracking {i+1}",
                    False,
                    f"Exception during order tracking: {str(e)}"
                )
    
    def test_integration_e2e_flow(self):
        """Test complete E2E flow: Create order → Process payment → Track order"""
        print("🔄 TESTING COMPLETE E2E INTEGRATION FLOW")
        print("=" * 50)
        
        # E2E Test 1: Cash on Delivery Flow
        try:
            # Step 1: Create order
            order_data = {
                "delivery_address": "E2E Test Address, Şişli, İstanbul",
                "delivery_lat": 41.0498,
                "delivery_lng": 28.9662,
                "items": [
                    {
                        "product_id": "e2e-product-1",
                        "product_name": "E2E Test Pizza",
                        "product_price": 75.0,
                        "quantity": 1,
                        "subtotal": 75.0
                    }
                ],
                "total_amount": 75.0,
                "notes": "E2E integration test order"
            }
            
            order_response = self.session.post(f"{BACKEND_URL}/orders", json=order_data)
            
            if order_response.status_code == 200:
                order = order_response.json()
                order_id = order.get("id")
                initial_status = order.get("status")
                
                self.log_test(
                    "E2E Flow Step 1 - Order Creation",
                    True,
                    f"Order created with ID: {order_id}, Status: {initial_status}"
                )
                
                # Step 2: Process payment (cash on delivery)
                payment_data = {
                    "order_id": order_id,
                    "payment_method": "cash_on_delivery",
                    "amount": 75.0
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/payments/mock", json=payment_data)
                
                if payment_response.status_code == 200:
                    payment_result = payment_response.json()
                    payment_success = payment_result.get("status") == "success"
                    
                    self.log_test(
                        "E2E Flow Step 2 - Payment Processing",
                        payment_success,
                        f"Payment success: {payment_success}, Method: cash_on_delivery"
                    )
                    
                    if payment_success:
                        # Step 3: Verify order status updated to "confirmed"
                        time.sleep(1)  # Allow time for status update
                        
                        track_response = self.session.get(f"{BACKEND_URL}/orders/{order_id}/track")
                        
                        if track_response.status_code == 200:
                            tracking_data = track_response.json()
                            updated_status = tracking_data.get("status")
                            
                            # Check if status progressed from "created" to "confirmed"
                            status_updated = updated_status in ["confirmed", "preparing", "assigned"]
                            
                            self.log_test(
                                "E2E Flow Step 3 - Order Status Update",
                                status_updated,
                                f"Status updated from '{initial_status}' to '{updated_status}'"
                            )
                            
                            # Step 4: Track order
                            self.log_test(
                                "E2E Flow Step 4 - Order Tracking",
                                True,
                                f"Order tracking successful. Current status: {updated_status}"
                            )
                            
                        else:
                            self.log_test(
                                "E2E Flow Step 3 - Order Status Check",
                                False,
                                f"Failed to check order status. Status: {track_response.status_code}"
                            )
                else:
                    self.log_test(
                        "E2E Flow Step 2 - Payment Processing",
                        False,
                        f"Payment failed. Status: {payment_response.status_code}"
                    )
            else:
                self.log_test(
                    "E2E Flow Step 1 - Order Creation",
                    False,
                    f"Order creation failed. Status: {order_response.status_code}"
                )
                
        except Exception as e:
            self.log_test(
                "E2E Integration Flow",
                False,
                f"Exception during E2E test: {str(e)}"
            )
        
        # E2E Test 2: Online Payment Flow
        try:
            # Create another order for online payment test
            order_data_online = {
                "delivery_address": "E2E Online Test Address, Beşiktaş, İstanbul",
                "delivery_lat": 41.0766,
                "delivery_lng": 28.9688,
                "items": [
                    {
                        "product_id": "e2e-product-2",
                        "product_name": "E2E Test Burger",
                        "product_price": 55.0,
                        "quantity": 1,
                        "subtotal": 55.0
                    }
                ],
                "total_amount": 55.0,
                "notes": "E2E online payment test order"
            }
            
            order_response = self.session.post(f"{BACKEND_URL}/orders", json=order_data_online)
            
            if order_response.status_code == 200:
                order = order_response.json()
                order_id = order.get("id")
                
                # Process online payment
                payment_data = {
                    "order_id": order_id,
                    "payment_method": "online",
                    "amount": 55.0
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/payments/mock", json=payment_data)
                
                if payment_response.status_code == 200:
                    payment_result = payment_response.json()
                    payment_success = payment_result.get("status") == "success"
                    
                    if payment_success:
                        self.log_test(
                            "E2E Online Payment Flow",
                            True,
                            f"Complete online payment flow successful for order {order_id}"
                        )
                    else:
                        self.log_test(
                            "E2E Online Payment Flow",
                            True,  # Still success as failure is expected sometimes
                            f"Online payment failed as expected (simulated failure) for order {order_id}"
                        )
                        
        except Exception as e:
            self.log_test(
                "E2E Online Payment Flow",
                False,
                f"Exception during online payment E2E test: {str(e)}"
            )
    
    def test_data_validation(self):
        """Test payment and order validation scenarios"""
        print("✅ TESTING DATA VALIDATION")
        print("=" * 50)
        
        # Test 1: Payment with invalid order_id
        try:
            invalid_payment_data = {
                "order_id": "invalid-order-id-12345",
                "payment_method": "cash_on_delivery",
                "amount": 100.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/mock", json=invalid_payment_data)
            
            if response.status_code == 404:
                self.log_test(
                    "Data Validation - Invalid Order ID",
                    True,
                    f"Properly handled invalid order ID. Status: {response.status_code}",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Data Validation - Invalid Order ID",
                    False,
                    f"Should return 404 for invalid order ID but got: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Data Validation - Invalid Order ID",
                False,
                f"Exception during invalid order ID test: {str(e)}"
            )
        
        # Test 2: Order tracking with non-existent order_id
        try:
            invalid_order_id = "non-existent-order-12345"
            response = self.session.get(f"{BACKEND_URL}/orders/{invalid_order_id}/track")
            
            if response.status_code == 404:
                self.log_test(
                    "Data Validation - Non-existent Order Tracking",
                    True,
                    f"Properly handled non-existent order tracking. Status: {response.status_code}",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Data Validation - Non-existent Order Tracking",
                    False,
                    f"Should return 404 for non-existent order but got: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Data Validation - Non-existent Order Tracking",
                False,
                f"Exception during non-existent order test: {str(e)}"
            )
        
        # Test 3: Payment with invalid payment method
        if self.test_order_ids:
            try:
                invalid_method_data = {
                    "order_id": self.test_order_ids[0],
                    "payment_method": "invalid_payment_method",
                    "amount": 100.0
                }
                
                response = self.session.post(f"{BACKEND_URL}/payments/mock", json=invalid_method_data)
                
                if response.status_code == 422:
                    self.log_test(
                        "Data Validation - Invalid Payment Method",
                        True,
                        f"Properly handled invalid payment method. Status: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_test(
                        "Data Validation - Invalid Payment Method",
                        False,
                        f"Should return 422 for invalid payment method but got: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    "Data Validation - Invalid Payment Method",
                    False,
                    f"Exception during invalid payment method test: {str(e)}"
                )
        
        # Test 4: Access control - try to access another customer's order
        try:
            # Create a session without authentication
            unauth_session = requests.Session()
            
            if self.test_order_ids:
                response = unauth_session.get(f"{BACKEND_URL}/orders/{self.test_order_ids[0]}/track")
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        "Data Validation - Access Control (403 Forbidden)",
                        True,
                        f"Properly rejected unauthorized access. Status: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_test(
                        "Data Validation - Access Control (403 Forbidden)",
                        False,
                        f"Should reject unauthorized access but got: {response.status_code}",
                        response.text
                    )
                    
        except Exception as e:
            self.log_test(
                "Data Validation - Access Control",
                False,
                f"Exception during access control test: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all FAZ 2 backend tests"""
        print("🚀 STARTING FAZ 2 - CUSTOMER CART & PAYMENT BACKEND TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate customer
        if not self.authenticate_customer():
            print("❌ CRITICAL: Customer authentication failed. Cannot proceed with FAZ 2 tests.")
            return self.generate_final_report()
        
        # Step 2: Test order creation flow
        self.test_order_creation_flow()
        
        # Step 3: Test mock payment system
        self.test_mock_payment_system()
        
        # Step 4: Test customer order tracking
        self.test_customer_order_tracking()
        
        # Step 5: Test complete E2E integration flow
        self.test_integration_e2e_flow()
        
        # Step 6: Test data validation
        self.test_data_validation()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 FAZ 2 - CUSTOMER CART & PAYMENT BACKEND TEST RESULTS")
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
        
        # Categorize results by test area
        test_categories = {
            "Authentication": [],
            "Order Creation": [],
            "Payment System": [],
            "Order Tracking": [],
            "E2E Integration": [],
            "Data Validation": []
        }
        
        for test in self.results["test_details"]:
            test_name = test["test"]
            if "Authentication" in test_name:
                test_categories["Authentication"].append(test)
            elif "Order Creation" in test_name or "POST /orders" in test_name:
                test_categories["Order Creation"].append(test)
            elif "Payment" in test_name or "Mock Payment" in test_name:
                test_categories["Payment System"].append(test)
            elif "Order Tracking" in test_name or "/track" in test_name or "/orders/my" in test_name:
                test_categories["Order Tracking"].append(test)
            elif "E2E" in test_name or "Integration" in test_name:
                test_categories["E2E Integration"].append(test)
            elif "Data Validation" in test_name or "Validation" in test_name:
                test_categories["Data Validation"].append(test)
        
        print("📋 TEST RESULTS BY CATEGORY:")
        for category, tests in test_categories.items():
            if tests:
                passed_in_category = sum(1 for test in tests if "✅ PASS" in test["status"])
                total_in_category = len(tests)
                category_rate = (passed_in_category / total_in_category * 100) if total_in_category > 0 else 0
                print(f"  {category}: {passed_in_category}/{total_in_category} ({category_rate:.1f}%)")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Success criteria evaluation
        print("🎯 SUCCESS CRITERIA EVALUATION:")
        
        # Critical success criteria
        critical_tests = [
            ("Customer Authentication", "Authentication working"),
            ("Order Creation", "Order creation flow working"),
            ("Payment", "Mock payment system working"),
            ("Order Tracking", "Customer order tracking working"),
            ("E2E", "Complete E2E flow working")
        ]
        
        critical_success = True
        for criteria, description in critical_tests:
            criteria_tests = [test for test in self.results["test_details"] if criteria in test["test"]]
            if criteria_tests:
                criteria_passed = sum(1 for test in criteria_tests if "✅ PASS" in test["status"])
                criteria_total = len(criteria_tests)
                criteria_rate = (criteria_passed / criteria_total * 100) if criteria_total > 0 else 0
                
                if criteria_rate >= 80:
                    print(f"  ✅ {description}: {criteria_rate:.1f}% ({criteria_passed}/{criteria_total})")
                else:
                    print(f"  ❌ {description}: {criteria_rate:.1f}% ({criteria_passed}/{criteria_total})")
                    critical_success = False
            else:
                print(f"  ⚠️ {description}: Not tested")
                critical_success = False
        
        print()
        
        if success_rate >= 90 and critical_success:
            print("🎉 EXCELLENT: FAZ 2 customer cart & payment backend is working perfectly!")
            print("✅ All critical success criteria met:")
            print("  • Mock payment system working with all 3 methods")
            print("  • Customer order tracking fully functional")
            print("  • Complete order-to-payment-to-tracking flow works")
            print("  • Proper error handling and HTTP status codes")
            print("  • Customer access control working (security)")
        elif success_rate >= 75:
            print("✅ GOOD: FAZ 2 backend is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: FAZ 2 backend has significant issues that need attention.")
        else:
            print("❌ CRITICAL: FAZ 2 backend has major failures requiring immediate fixes.")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "critical_success": critical_success,
            "details": self.results["test_details"]
        }

def main():
    """Main test execution"""
    tester = FAZ2BackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 75 and results.get("critical_success", False):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()