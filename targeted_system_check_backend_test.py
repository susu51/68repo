#!/usr/bin/env python3
"""
TARGETED SYSTEM CHECK - Using Working Business

Testing with known working business: e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed
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

class TargetedSystemChecker:
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
    
    def test_complete_order_flow(self):
        """Test complete order flow with working business"""
        try:
            # Step 1: Get menu from working business
            menu_response = self.customer_session.get(
                f"{BACKEND_URL}/api/business/public/{WORKING_BUSINESS_ID}/menu",
                timeout=10
            )
            
            if menu_response.status_code != 200:
                self.log_test("Complete Order Flow - Get Menu", False, error=f"Menu API failed: {menu_response.status_code}")
                return None
                
            menu_items = menu_response.json()
            if not menu_items:
                self.log_test("Complete Order Flow - Get Menu", False, error="No menu items found")
                return None
                
            menu_item = menu_items[0]
            self.log_test(
                "Complete Order Flow - Get Menu",
                True,
                f"Found {len(menu_items)} menu items, using: {menu_item.get('name')} (₺{menu_item.get('price')})"
            )
            
            # Step 2: Create order
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
                "notes": "Targeted system check test order"
            }
            
            order_response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            if order_response.status_code not in [200, 201]:
                self.log_test("Complete Order Flow - Create Order", False, error=f"Order creation failed: {order_response.status_code} - {order_response.text}")
                return None
                
            order = order_response.json()
            order_id = order.get("order_id") or order.get("id")
            
            self.log_test(
                "Complete Order Flow - Create Order",
                True,
                f"Order created: ID={order_id}, business_id={order.get('business_id')}, total={order.get('total_amount')}"
            )
            
            # Step 3: Check business can see the order
            time.sleep(2)  # Wait for order to propagate
            
            business_orders_response = self.business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                timeout=10
            )
            
            if business_orders_response.status_code != 200:
                self.log_test("Complete Order Flow - Business Orders", False, error=f"Business orders API failed: {business_orders_response.status_code}")
                return None
                
            business_orders = business_orders_response.json()
            matching_orders = [o for o in business_orders if o.get("id") == order_id or str(o.get("id")) == str(order_id)]
            
            if matching_orders:
                self.log_test(
                    "Complete Order Flow - Business Orders",
                    True,
                    f"Business can see the order! Found order {order_id} in incoming orders"
                )
                return order_id
            else:
                self.log_test(
                    "Complete Order Flow - Business Orders",
                    False,
                    error=f"Order {order_id} not found in business incoming orders. Total orders: {len(business_orders)}"
                )
                return None
                
        except Exception as e:
            self.log_test("Complete Order Flow", False, error=f"Exception: {str(e)}")
            return None
    
    def test_business_order_confirmation(self, order_id):
        """Test business order confirmation"""
        try:
            confirm_data = {"unit_delivery_fee": 15.0}
            
            response = self.business_session.put(
                f"{BACKEND_URL}/api/business/orders/{order_id}/confirm",
                json=confirm_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "Business Order Confirmation",
                    True,
                    f"Order confirmed: {result}"
                )
                return result.get("task_id")
            else:
                self.log_test(
                    "Business Order Confirmation",
                    False,
                    error=f"Confirmation failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Business Order Confirmation", False, error=f"Exception: {str(e)}")
            return None
    
    def test_courier_tasks(self):
        """Test courier tasks endpoint"""
        try:
            response = self.courier_session.get(
                f"{BACKEND_URL}/api/courier/tasks?status=waiting",
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                
                if tasks and len(tasks) > 0:
                    task = tasks[0]
                    self.log_test(
                        "Courier Tasks",
                        True,
                        f"Found {len(tasks)} waiting tasks. Task fields: {list(task.keys())}"
                    )
                    return True
                else:
                    self.log_test(
                        "Courier Tasks",
                        False,
                        error="No waiting tasks found"
                    )
                    return False
            else:
                self.log_test(
                    "Courier Tasks",
                    False,
                    error=f"Courier tasks API failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Courier Tasks", False, error=f"Exception: {str(e)}")
            return False
    
    def test_admin_coupons(self):
        """Test admin coupons endpoint"""
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/api/admin/coupons",
                timeout=10
            )
            
            if response.status_code == 200:
                coupons = response.json()
                self.log_test(
                    "Admin Coupons",
                    True,
                    f"Admin coupons accessible. Found {len(coupons)} coupons"
                )
                return True
            else:
                self.log_test(
                    "Admin Coupons",
                    False,
                    error=f"Admin coupons failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Coupons", False, error=f"Exception: {str(e)}")
            return False
    
    def run_targeted_check(self):
        """Run targeted system check"""
        print("🎯 TARGETED SYSTEM CHECK - Using Working Business")
        print("=" * 80)
        
        # Authenticate all users
        if not self.authenticate_all_users():
            print("❌ Authentication failed - cannot proceed")
            return
        
        print("\n🔍 Testing Critical Flows with Working Business...")
        print("-" * 50)
        
        # Test complete order flow
        order_id = self.test_complete_order_flow()
        
        # Test business order confirmation if we have an order
        if order_id:
            task_id = self.test_business_order_confirmation(order_id)
        
        # Test courier tasks
        self.test_courier_tasks()
        
        # Test admin coupons
        self.test_admin_coupons()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "=" * 80)
        print("📊 TARGETED SYSTEM CHECK RESULTS")
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
        
        # Check what's working vs broken
        order_flow_working = any("Complete Order Flow" in r["test"] and r["success"] for r in self.test_results)
        confirmation_working = any("Business Order Confirmation" in r["test"] and r["success"] for r in self.test_results)
        courier_working = any("Courier Tasks" in r["test"] and r["success"] for r in self.test_results)
        admin_working = any("Admin Coupons" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"\n🎯 WHAT'S WORKING vs BROKEN:")
        print(f"   Order Creation → Business Reception: {'✅ WORKING' if order_flow_working else '❌ BROKEN'}")
        print(f"   Business Order Confirmation: {'✅ WORKING' if confirmation_working else '❌ BROKEN'}")
        print(f"   Courier Task System: {'✅ WORKING' if courier_working else '❌ BROKEN'}")
        print(f"   Admin Panel Access: {'✅ WORKING' if admin_working else '❌ BROKEN'}")
        
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: System is WORKING WELL ({success_rate:.1f}% success rate)")
        elif success_rate >= 50:
            print(f"\n⚠️ VERDICT: System has ISSUES ({success_rate:.1f}% success rate)")
        else:
            print(f"\n🚨 VERDICT: System is BROKEN ({success_rate:.1f}% success rate)")

def main():
    """Main test runner"""
    checker = TargetedSystemChecker()
    checker.run_targeted_check()

if __name__ == "__main__":
    main()