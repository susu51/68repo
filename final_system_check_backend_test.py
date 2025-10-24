#!/usr/bin/env python3
"""
FINAL SYSTEM CHECK - Complete Flow Testing

Based on backend logs, the system is working. Let me verify each component properly.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com"
WORKING_BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"

# Test credentials
CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}
BUSINESS_CREDENTIALS = {"email": "testbusiness@example.com", "password": "test123"}
COURIER_CREDENTIALS = {"email": "testkurye@example.com", "password": "test123"}
ADMIN_CREDENTIALS = {"email": "admin@kuryecini.com", "password": "admin123"}

class FinalSystemChecker:
    def __init__(self):
        self.test_results = []
        self.customer_session = requests.Session()
        self.business_session = requests.Session()
        self.courier_session = requests.Session()
        self.admin_session = requests.Session()
        
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
        
    def authenticate_all_users(self):
        """Authenticate all users"""
        sessions_creds = [
            (self.customer_session, CUSTOMER_CREDENTIALS, "Customer"),
            (self.business_session, BUSINESS_CREDENTIALS, "Business"),
            (self.courier_session, COURIER_CREDENTIALS, "Courier"),
            (self.admin_session, ADMIN_CREDENTIALS, "Admin")
        ]
        
        all_success = True
        for session, credentials, role_name in sessions_creds:
            try:
                response = session.post(
                    f"{BACKEND_URL}/api/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        user_role = data.get("user", {}).get("role")
                        self.log_test(
                            f"{role_name} Authentication",
                            True,
                            f"Login successful: {credentials['email']}, role: {user_role}"
                        )
                    else:
                        self.log_test(f"{role_name} Authentication", False, error=f"Login failed: {data}")
                        all_success = False
                else:
                    self.log_test(f"{role_name} Authentication", False, error=f"HTTP {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"{role_name} Authentication", False, error=f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_1_customer_order_creation(self):
        """Test 1: Customer Order Creation"""
        try:
            # Get menu from working business
            menu_response = self.customer_session.get(
                f"{BACKEND_URL}/api/business/public/{WORKING_BUSINESS_ID}/menu",
                timeout=10
            )
            
            if menu_response.status_code != 200:
                self.log_test("1. Customer Order Creation - Get Menu", False, error=f"Menu API failed: {menu_response.status_code}")
                return None
                
            menu_items = menu_response.json()
            if not menu_items:
                self.log_test("1. Customer Order Creation - Get Menu", False, error="No menu items found")
                return None
                
            menu_item = menu_items[0]
            self.log_test(
                "1. Customer Order Creation - Get Menu",
                True,
                f"Found {len(menu_items)} menu items, using: {menu_item.get('name')} (₺{menu_item.get('price')})"
            )
            
            # Create order with proper format
            order_data = {
                "business_id": WORKING_BUSINESS_ID,
                "delivery_address": {
                    "label": "Test Address",
                    "address": "Test Street 123, Aksaray Merkez",
                    "lat": 38.3687,
                    "lng": 34.0254
                },
                "items": [{
                    "product_id": menu_item.get("id"),
                    "title": menu_item.get("name"),
                    "price": menu_item.get("price"),
                    "quantity": 1
                }],
                "payment_method": "cash_on_delivery",
                "notes": "Final system check test order"
            }
            
            order_response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            print(f"   Order Response Status: {order_response.status_code}")
            print(f"   Order Response: {order_response.text[:200]}...")
            
            if order_response.status_code in [200, 201]:
                order = order_response.json()
                
                # Check different possible order ID fields
                order_id = (order.get("order_id") or 
                           order.get("id") or 
                           order.get("data", {}).get("order_id") or
                           order.get("data", {}).get("id"))
                
                business_id = (order.get("business_id") or 
                              order.get("data", {}).get("business_id"))
                
                total_amount = (order.get("total_amount") or 
                               order.get("data", {}).get("total_amount"))
                
                self.log_test(
                    "1. Customer Order Creation - POST /api/orders",
                    True,
                    f"Order created: ID={order_id}, business_id={business_id}, total={total_amount}"
                )
                return order_id
            else:
                self.log_test(
                    "1. Customer Order Creation - POST /api/orders",
                    False,
                    error=f"Order creation failed: {order_response.status_code} - {order_response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("1. Customer Order Creation", False, error=f"Exception: {str(e)}")
            return None
    
    def test_2_business_order_reception(self, expected_order_id=None):
        """Test 2: Business Order Reception"""
        try:
            response = self.business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                timeout=10
            )
            
            if response.status_code == 200:
                orders = response.json()
                
                # Check if we have orders for this business
                business_orders = [o for o in orders if o.get("business_id") == WORKING_BUSINESS_ID]
                
                if business_orders:
                    order = business_orders[0]
                    order_id = order.get("id")
                    
                    self.log_test(
                        "2. Business Order Reception - GET /api/business/orders/incoming",
                        True,
                        f"Business can see {len(business_orders)} orders. Latest order: {order_id}, business_id: {order.get('business_id')}"
                    )
                    return order_id
                else:
                    self.log_test(
                        "2. Business Order Reception - GET /api/business/orders/incoming",
                        False,
                        error=f"No orders found for business {WORKING_BUSINESS_ID}. Total orders: {len(orders)}"
                    )
                    return None
            else:
                self.log_test(
                    "2. Business Order Reception - GET /api/business/orders/incoming",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("2. Business Order Reception", False, error=f"Exception: {str(e)}")
            return None
    
    def test_3_business_order_confirmation(self, order_id):
        """Test 3: Business Order Confirmation"""
        if not order_id:
            self.log_test("3. Business Order Confirmation", False, error="No order ID provided")
            return None
            
        try:
            confirm_data = {"unit_delivery_fee": 15.0}
            
            response = self.business_session.put(
                f"{BACKEND_URL}/api/business/orders/{order_id}/confirm",
                json=confirm_data,
                timeout=10
            )
            
            print(f"   Confirmation Response Status: {response.status_code}")
            print(f"   Confirmation Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                self.log_test(
                    "3. Business Order Confirmation - PUT /api/business/orders/{order_id}/confirm",
                    True,
                    f"Order confirmed successfully: task_id={task_id}, response={result}"
                )
                return task_id
            else:
                self.log_test(
                    "3. Business Order Confirmation - PUT /api/business/orders/{order_id}/confirm",
                    False,
                    error=f"Confirmation failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("3. Business Order Confirmation", False, error=f"Exception: {str(e)}")
            return None
    
    def test_4_courier_tasks(self):
        """Test 4: Courier Tasks"""
        try:
            response = self.courier_session.get(
                f"{BACKEND_URL}/api/courier/tasks?status=waiting",
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                
                if tasks and len(tasks) > 0:
                    task = tasks[0]
                    
                    # Check for required fields (business_id might be restaurant_id)
                    has_business_id = "business_id" in task or "restaurant_id" in task
                    required_fields = ["id", "order_id", "pickup_coords", "dropoff_coords", "unit_delivery_fee"]
                    missing_fields = [field for field in required_fields if field not in task]
                    
                    if not missing_fields and has_business_id:
                        self.log_test(
                            "4. Courier Tasks - GET /api/courier/tasks?status=waiting",
                            True,
                            f"Found {len(tasks)} waiting tasks. Task has all required fields. Business ID field: {'business_id' if 'business_id' in task else 'restaurant_id'}"
                        )
                        return True
                    else:
                        missing_info = []
                        if missing_fields:
                            missing_info.append(f"missing fields: {missing_fields}")
                        if not has_business_id:
                            missing_info.append("no business_id or restaurant_id")
                            
                        self.log_test(
                            "4. Courier Tasks - GET /api/courier/tasks?status=waiting",
                            False,
                            error=f"Task incomplete: {', '.join(missing_info)}. Available fields: {list(task.keys())}"
                        )
                        return False
                else:
                    self.log_test(
                        "4. Courier Tasks - GET /api/courier/tasks?status=waiting",
                        False,
                        error="No waiting tasks found"
                    )
                    return False
            else:
                self.log_test(
                    "4. Courier Tasks - GET /api/courier/tasks?status=waiting",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("4. Courier Tasks", False, error=f"Exception: {str(e)}")
            return False
    
    def test_5_coupon_system(self):
        """Test 5: Coupon System"""
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/api/admin/coupons",
                timeout=10
            )
            
            if response.status_code == 200:
                coupons = response.json()
                self.log_test(
                    "5. Coupon System - GET /api/admin/coupons",
                    True,
                    f"Admin coupons endpoint accessible. Found {len(coupons)} coupons"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "5. Coupon System - GET /api/admin/coupons",
                    False,
                    error="Coupon endpoint not implemented (404)"
                )
                return False
            elif response.status_code == 403:
                self.log_test(
                    "5. Coupon System - GET /api/admin/coupons",
                    False,
                    error="Admin access denied (403) - authentication issue"
                )
                return False
            else:
                self.log_test(
                    "5. Coupon System - GET /api/admin/coupons",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("5. Coupon System", False, error=f"Exception: {str(e)}")
            return False
    
    def run_final_check(self):
        """Run final comprehensive system check"""
        print("🔍 FINAL SYSTEM CHECK - Complete Flow Verification")
        print("=" * 80)
        
        # Authenticate all users
        if not self.authenticate_all_users():
            print("❌ Authentication failed - cannot proceed")
            return
        
        print("\n🎯 Testing All Critical Flows...")
        print("-" * 50)
        
        # Test 1: Customer Order Creation
        order_id = self.test_1_customer_order_creation()
        
        # Test 2: Business Order Reception
        business_order_id = self.test_2_business_order_reception(order_id)
        
        # Test 3: Business Order Confirmation (use the business order ID)
        if business_order_id:
            task_id = self.test_3_business_order_confirmation(business_order_id)
        else:
            self.log_test("3. Business Order Confirmation", False, error="No business order found to confirm")
        
        # Test 4: Courier Tasks
        self.test_4_courier_tasks()
        
        # Test 5: Coupon System
        self.test_5_coupon_system()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL SYSTEM CHECK RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🎯 CRITICAL FLOW STATUS:")
        
        # Check each critical flow
        auth_working = all("Authentication" in r["test"] and r["success"] for r in self.test_results if "Authentication" in r["test"])
        order_creation_working = any("1. Customer Order Creation" in r["test"] and r["success"] for r in self.test_results)
        business_reception_working = any("2. Business Order Reception" in r["test"] and r["success"] for r in self.test_results)
        order_confirmation_working = any("3. Business Order Confirmation" in r["test"] and r["success"] for r in self.test_results)
        courier_tasks_working = any("4. Courier Tasks" in r["test"] and r["success"] for r in self.test_results)
        admin_access_working = any("5. Coupon System" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"   1. Customer Order Creation: {'✅ WORKING' if order_creation_working else '❌ BROKEN'}")
        print(f"   2. Business Order Reception: {'✅ WORKING' if business_reception_working else '❌ BROKEN'}")
        print(f"   3. Business Order Confirmation: {'✅ WORKING' if order_confirmation_working else '❌ BROKEN'}")
        print(f"   4. Courier Tasks: {'✅ WORKING' if courier_tasks_working else '❌ BROKEN'}")
        print(f"   5. Admin Coupon System: {'✅ WORKING' if admin_access_working else '❌ BROKEN'}")
        
        print(f"\n🚨 WHAT'S NOT WORKING (User Issue: 'nothing is showing'):")
        
        broken_components = []
        if not order_creation_working:
            broken_components.append("❌ Customer cannot create orders")
        if not business_reception_working:
            broken_components.append("❌ Business cannot see incoming orders")
        if not order_confirmation_working:
            broken_components.append("❌ Business cannot confirm orders")
        if not courier_tasks_working:
            broken_components.append("❌ Courier cannot see tasks")
        if not admin_access_working:
            broken_components.append("❌ Admin panel features missing")
        
        if broken_components:
            for component in broken_components:
                print(f"   {component}")
        else:
            print("   ✅ All major components are working!")
            print("   💡 User issue might be frontend-related or specific business data")
        
        # Overall verdict
        if success_rate >= 90:
            print(f"\n🎉 VERDICT: System is WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
            print("   💡 If user reports 'nothing showing', check frontend or specific business data")
        elif success_rate >= 70:
            print(f"\n⚠️ VERDICT: System has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   🔧 Fix the failed components above")
        else:
            print(f"\n🚨 VERDICT: System is CRITICALLY BROKEN ({success_rate:.1f}% success rate)")
            print("   🔥 URGENT: Multiple critical systems are down")

def main():
    """Main test runner"""
    checker = FinalSystemChecker()
    checker.run_final_check()

if __name__ == "__main__":
    main()