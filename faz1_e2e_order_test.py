#!/usr/bin/env python3
"""
FAZ 1 COMPLETE END-TO-END TEST - Order Creation to Business Confirmation

This test implements the exact flow requested in the review:
1. Customer creates order (login as test@kuryecini.com / test123)
2. Business receives order within 5 seconds (GET /api/business/orders/incoming)
3. Business confirms order (PUT /api/business/orders/{order_id}/confirm with unit_delivery_fee: 15.0)
4. Verify courier task created in courier_tasks collection

Expected Results:
✅ Order created successfully (POST /api/orders → 201)
✅ Order visible in business incoming orders within 5 seconds
✅ Business can confirm order (PUT confirm → 200)
✅ courier_tasks document created
✅ Task has status="waiting"
"""

import asyncio
import json
import requests
import time
from datetime import datetime
import os
import sys
from pymongo import MongoClient

# Configuration
BACKEND_URL = "https://admin-wsocket.preview.emergentagent.com"

# Test credentials
CUSTOMER_CREDENTIALS = {
    "email": "test@kuryecini.com", 
    "password": "test123"
}

BUSINESS_CREDENTIALS = {
    "email": "testbusiness@example.com",
    "password": "test123"
}

class FAZ1OrderFlowTester:
    def __init__(self):
        self.customer_session = requests.Session()
        self.business_session = requests.Session()
        self.test_results = []
        self.order_id = None
        self.business_id = None
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
    
    def authenticate_customer(self):
        """Step 1: Login as customer (test@kuryecini.com / test123)"""
        try:
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_role = data.get("user", {}).get("role")
                user_id = data.get("user", {}).get("id")
                
                if user_role == "customer":
                    self.log_test(
                        "Customer Login",
                        True,
                        f"Customer login successful: {CUSTOMER_CREDENTIALS['email']}, user_id: {user_id}"
                    )
                    return True
                else:
                    self.log_test("Customer Login", False, error=f"Expected customer role, got: {user_role}")
                    return False
            else:
                self.log_test("Customer Login", False, error=f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Customer Login", False, error=f"Authentication error: {str(e)}")
            return False

    def authenticate_business(self):
        """Authenticate business user for order confirmation"""
        try:
            response = self.business_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=BUSINESS_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_role = data.get("user", {}).get("role")
                user_id = data.get("user", {}).get("id")
                
                if user_role == "business":
                    self.business_id = user_id
                    self.log_test(
                        "Business Login",
                        True,
                        f"Business login successful: {BUSINESS_CREDENTIALS['email']}, business_id: {user_id}"
                    )
                    return True
                else:
                    self.log_test("Business Login", False, error=f"Expected business role, got: {user_role}")
                    return False
            else:
                self.log_test("Business Login", False, error=f"Business login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Business Login", False, error=f"Business authentication error: {str(e)}")
            return False

    def get_business_for_order(self):
        """Get available business with menu items"""
        try:
            # Get businesses in Aksaray (where test customer is located)
            response = requests.get(f"{BACKEND_URL}/api/businesses?city=Aksaray", timeout=10)
            
            if response.status_code == 200:
                businesses = response.json()
                if businesses and len(businesses) > 0:
                    # Find a business with menu items
                    for business in businesses:
                        business_id = business.get("id")
                        business_name = business.get("name", "Unknown")
                        
                        # Check if business has menu items
                        menu_response = requests.get(
                            f"{BACKEND_URL}/api/business/public/{business_id}/menu", 
                            timeout=10
                        )
                        
                        if menu_response.status_code == 200:
                            menu_items = menu_response.json()
                            if menu_items and len(menu_items) > 0:
                                self.log_test(
                                    "Get Business for Order",
                                    True,
                                    f"Found business with menu: {business_name} (ID: {business_id}), {len(menu_items)} menu items"
                                )
                                return business_id, business_name, menu_items[0]
                    
                    self.log_test("Get Business for Order", False, error="No businesses found with menu items")
                    return None, None, None
                else:
                    self.log_test("Get Business for Order", False, error="No businesses found in Aksaray")
                    return None, None, None
            else:
                self.log_test("Get Business for Order", False, error=f"API error: {response.status_code}")
                return None, None, None
                
        except Exception as e:
            self.log_test("Get Business for Order", False, error=f"Error getting business: {str(e)}")
            return None, None, None

    def create_order(self, business_id, menu_item):
        """Step 2: Customer creates order using POST /api/orders"""
        try:
            order_data = {
                "business_id": business_id,  # Add business_id to the order
                "delivery_address": "Test Address, Aksaray Merkez",
                "delivery_lat": 38.3687,
                "delivery_lng": 34.0254,
                "items": [{
                    "product_id": menu_item["id"],
                    "title": menu_item.get("name", menu_item.get("title", "Test Item")),
                    "price": menu_item["price"],
                    "quantity": 1
                }],
                "total_amount": menu_item["price"],
                "payment_method": "cash_on_delivery",
                "notes": "FAZ 1 E2E Test Order"
            }
            
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                self.order_id = order.get("order_id") or order.get("id")
                order_business_id = order.get("business_id")
                order_status = order.get("status")
                
                self.log_test(
                    "Create Order (POST /api/orders)",
                    True,
                    f"Order created successfully: ID={self.order_id}, business_id={order_business_id}, status={order_status}, total=₺{order.get('total_amount')}"
                )
                return True
            else:
                self.log_test("Create Order (POST /api/orders)", False, error=f"Order creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Order (POST /api/orders)", False, error=f"Error creating order: {str(e)}")
            return False

    def check_business_receives_order(self):
        """Step 3: Business receives order (5 second check) - GET /api/business/orders/incoming"""
        try:
            start_time = time.time()
            max_wait_time = 5  # 5 seconds as specified
            
            while time.time() - start_time < max_wait_time:
                response = self.business_session.get(
                    f"{BACKEND_URL}/api/business/orders/incoming",
                    timeout=10
                )
                
                if response.status_code == 200:
                    orders = response.json()
                    
                    # Look for our order
                    for order in orders:
                        if order.get("id") == self.order_id:
                            elapsed_time = time.time() - start_time
                            order_business_id = order.get("business_id")
                            
                            self.log_test(
                                "Business Receives Order (within 5 seconds)",
                                True,
                                f"Order found in business incoming orders in {elapsed_time:.2f} seconds. Order ID: {self.order_id}, business_id: {order_business_id}"
                            )
                            return True
                
                time.sleep(0.5)  # Check every 500ms
            
            # If we get here, order wasn't found within 5 seconds
            elapsed_time = time.time() - start_time
            self.log_test(
                "Business Receives Order (within 5 seconds)",
                False,
                error=f"Order not found in business incoming orders after {elapsed_time:.2f} seconds"
            )
            return False
                
        except Exception as e:
            self.log_test("Business Receives Order (within 5 seconds)", False, error=f"Error checking business orders: {str(e)}")
            return False

    def confirm_order(self):
        """Step 4: Business confirms order - PUT /api/business/orders/{order_id}/confirm"""
        try:
            confirm_data = {
                "unit_delivery_fee": 15.0
            }
            
            response = self.business_session.put(
                f"{BACKEND_URL}/api/business/orders/{self.order_id}/confirm",
                json=confirm_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success")
                self.task_id = result.get("task_id")
                
                if success and self.task_id:
                    self.log_test(
                        "Business Confirms Order (PUT confirm)",
                        True,
                        f"Order confirmed successfully: success={success}, task_id={self.task_id}"
                    )
                    return True
                else:
                    self.log_test(
                        "Business Confirms Order (PUT confirm)",
                        False,
                        error=f"Confirmation response missing success or task_id: {result}"
                    )
                    return False
            else:
                self.log_test("Business Confirms Order (PUT confirm)", False, error=f"Order confirmation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Business Confirms Order (PUT confirm)", False, error=f"Error confirming order: {str(e)}")
            return False

    def verify_courier_task_created(self):
        """Step 5: Verify courier task created in courier_tasks collection"""
        try:
            # Connect to MongoDB to check courier_tasks collection
            mongo_url = "mongodb://localhost:27017/kuryecini"
            client = MongoClient(mongo_url)
            db = client.kuryecini
            
            # Query courier_tasks collection for our task
            task = db.courier_tasks.find_one({"id": self.task_id})
            
            if task:
                task_order_id = task.get("order_id")
                task_business_id = task.get("business_id")
                task_status = task.get("status")
                unit_delivery_fee = task.get("unit_delivery_fee")
                pickup_coords = task.get("pickup_coords")
                dropoff_coords = task.get("dropoff_coords")
                
                # Verify all required fields
                verification_results = []
                verification_results.append(f"order_id matches: {task_order_id == self.order_id}")
                verification_results.append(f"business_id matches: {task_business_id == self.business_id}")
                verification_results.append(f"status='waiting': {task_status == 'waiting'}")
                verification_results.append(f"unit_delivery_fee=15.0: {unit_delivery_fee == 15.0}")
                verification_results.append(f"pickup_coords present: {pickup_coords is not None}")
                verification_results.append(f"dropoff_coords present: {dropoff_coords is not None}")
                
                all_checks_passed = all([
                    task_order_id == self.order_id,
                    task_business_id == self.business_id,
                    task_status == "waiting",
                    unit_delivery_fee == 15.0,
                    pickup_coords is not None,
                    dropoff_coords is not None
                ])
                
                if all_checks_passed:
                    self.log_test(
                        "Verify Courier Task Created",
                        True,
                        f"Courier task created successfully with all required fields: {', '.join(verification_results)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Courier Task Created",
                        False,
                        error=f"Courier task missing required fields or incorrect values: {', '.join(verification_results)}"
                    )
                    return False
            else:
                self.log_test("Verify Courier Task Created", False, error=f"Courier task not found with task_id: {self.task_id}")
                return False
                
        except Exception as e:
            self.log_test("Verify Courier Task Created", False, error=f"Error verifying courier task: {str(e)}")
            return False

    def check_backend_logs(self):
        """Check backend logs for expected messages"""
        try:
            # Try to get backend logs via supervisor
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for expected log messages
                task_created_found = f"✅ Created courier task: {self.task_id}" in logs
                event_published_found = "📡 Published task.created event" in logs
                
                if task_created_found and event_published_found:
                    self.log_test(
                        "Backend Logs Verification",
                        True,
                        f"Found expected log messages: task creation and event publication"
                    )
                    return True
                else:
                    self.log_test(
                        "Backend Logs Verification",
                        False,
                        error=f"Missing expected log messages. task_created: {task_created_found}, event_published: {event_published_found}"
                    )
                    return False
            else:
                self.log_test("Backend Logs Verification", False, error="Could not access backend logs")
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Verification", False, error=f"Error checking backend logs: {str(e)}")
            return False

    def verify_order_status_changed(self):
        """Verify order status changed to 'confirmed'"""
        try:
            response = self.customer_session.get(f"{BACKEND_URL}/api/orders", timeout=10)
            
            if response.status_code == 200:
                orders = response.json()
                
                # Find our order
                for order in orders:
                    if order.get("id") == self.order_id:
                        order_status = order.get("status")
                        
                        if order_status == "confirmed":
                            self.log_test(
                                "Verify Order Status Changed",
                                True,
                                f"Order status successfully changed to 'confirmed'"
                            )
                            return True
                        else:
                            self.log_test(
                                "Verify Order Status Changed",
                                False,
                                error=f"Order status is '{order_status}', expected 'confirmed'"
                            )
                            return False
                
                self.log_test("Verify Order Status Changed", False, error="Order not found in customer orders")
                return False
            else:
                self.log_test("Verify Order Status Changed", False, error=f"Error getting customer orders: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Verify Order Status Changed", False, error=f"Error verifying order status: {str(e)}")
            return False

    def run_faz1_test(self):
        """Run the complete FAZ 1 end-to-end test"""
        print("🚀 Starting FAZ 1 COMPLETE END-TO-END TEST - Order Creation to Business Confirmation")
        print("=" * 90)
        
        # Step 1: Customer Login
        if not self.authenticate_customer():
            print("❌ Customer authentication failed - cannot proceed")
            return
        
        # Step 2: Business Login
        if not self.authenticate_business():
            print("❌ Business authentication failed - cannot proceed")
            return
        
        # Step 3: Get business and menu for order
        business_id, business_name, menu_item = self.get_business_for_order()
        if not business_id:
            print("❌ No suitable business found - cannot proceed")
            return
        
        print(f"\n📋 Test Setup Complete:")
        print(f"   Customer: {CUSTOMER_CREDENTIALS['email']}")
        print(f"   Business: {business_name} (ID: {business_id})")
        print(f"   Menu Item: {menu_item.get('name')} (₺{menu_item.get('price')})")
        print()
        
        # Step 4: Create Order
        if not self.create_order(business_id, menu_item):
            print("❌ Order creation failed - cannot proceed")
            return
        
        # Step 5: Check Business Receives Order (within 5 seconds)
        if not self.check_business_receives_order():
            print("❌ Business did not receive order within 5 seconds - cannot proceed")
            return
        
        # Step 6: Business Confirms Order
        if not self.confirm_order():
            print("❌ Order confirmation failed - cannot proceed")
            return
        
        # Step 7: Verify Order Status Changed
        self.verify_order_status_changed()
        
        # Step 8: Verify Courier Task Created
        self.verify_courier_task_created()
        
        # Step 9: Check Backend Logs
        self.check_backend_logs()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 90)
        print("📊 FAZ 1 END-TO-END TEST SUMMARY")
        print("=" * 90)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show all test results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']} {result['test']}")
            if result['details']:
                print(f"      → {result['details']}")
            if result['error']:
                print(f"      → ERROR: {result['error']}")
        
        # Critical findings
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        # Check each expected result
        order_created = any(r["test"] == "Create Order (POST /api/orders)" and r["success"] for r in self.test_results)
        business_received = any(r["test"] == "Business Receives Order (within 5 seconds)" and r["success"] for r in self.test_results)
        order_confirmed = any(r["test"] == "Business Confirms Order (PUT confirm)" and r["success"] for r in self.test_results)
        courier_task_created = any(r["test"] == "Verify Courier Task Created" and r["success"] for r in self.test_results)
        order_status_confirmed = any(r["test"] == "Verify Order Status Changed" and r["success"] for r in self.test_results)
        
        print(f"   {'✅' if order_created else '❌'} Order created successfully (POST /api/orders → 201)")
        print(f"   {'✅' if business_received else '❌'} Order visible in business incoming orders within 5 seconds")
        print(f"   {'✅' if order_confirmed else '❌'} Business can confirm order (PUT confirm → 200)")
        print(f"   {'✅' if courier_task_created else '❌'} courier_tasks document created")
        print(f"   {'✅' if order_status_confirmed else '❌'} Order status changed to 'confirmed'")
        
        # Overall verdict
        critical_tests_passed = sum([order_created, business_received, order_confirmed, courier_task_created])
        
        if critical_tests_passed == 4:
            print(f"\n🎉 VERDICT: FAZ 1 COMPLETE END-TO-END FLOW IS WORKING PERFECTLY!")
            print("   All critical acceptance criteria met. The system is ready for FAZ 1 completion.")
        elif critical_tests_passed >= 3:
            print(f"\n⚠️ VERDICT: FAZ 1 FLOW HAS MINOR ISSUES ({critical_tests_passed}/4 critical tests passed)")
            print("   Most functionality working but some issues need attention.")
        else:
            print(f"\n🚨 VERDICT: FAZ 1 FLOW HAS CRITICAL ISSUES ({critical_tests_passed}/4 critical tests passed)")
            print("   Major functionality broken - requires immediate attention.")
        
        if self.order_id:
            print(f"\n📝 Test Order ID: {self.order_id}")
        if self.task_id:
            print(f"📝 Courier Task ID: {self.task_id}")

def main():
    """Main test runner"""
    tester = FAZ1OrderFlowTester()
    tester.run_faz1_test()

if __name__ == "__main__":
    main()