#!/usr/bin/env python3
"""
URGENT FULL SYSTEM CHECK - Backend Testing

Testing all critical flows as requested:
1. Customer Order Creation
2. Business Order Reception  
3. Business Order Confirmation
4. Courier Tasks
5. Coupon System

User reports: "nothing is showing" - need to find what's broken!
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com"

# Test credentials
CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}
BUSINESS_CREDENTIALS = {"email": "testbusiness@example.com", "password": "test123"}
COURIER_CREDENTIALS = {"email": "testkurye@example.com", "password": "test123"}
ADMIN_CREDENTIALS = {"email": "admin@kuryecini.com", "password": "admin123"}

class UrgentSystemChecker:
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
        
    def authenticate_user(self, session, credentials, role_name):
        """Authenticate user and return success status"""
        try:
            response = session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=credentials,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_role = data.get("user", {}).get("role")
                
                if data.get("success"):
                    self.log_test(
                        f"{role_name} Authentication",
                        True,
                        f"Login successful: {credentials['email']}, role: {user_role}"
                    )
                    return True, data.get("user", {})
                else:
                    self.log_test(f"{role_name} Authentication", False, error=f"Login failed: {data}")
                    return False, None
            else:
                self.log_test(f"{role_name} Authentication", False, error=f"HTTP {response.status_code}: {response.text}")
                return False, None
                
        except Exception as e:
            self.log_test(f"{role_name} Authentication", False, error=f"Exception: {str(e)}")
            return False, None
    
    def test_customer_order_creation(self, customer_user):
        """Test 1: Customer Order Creation"""
        try:
            # First, get available businesses
            response = self.customer_session.get(f"{BACKEND_URL}/api/businesses?city=Aksaray", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Customer Order Creation - Get Businesses", False, error=f"Cannot get businesses: {response.status_code}")
                return None, None
                
            businesses = response.json()
            if not businesses:
                self.log_test("Customer Order Creation - Get Businesses", False, error="No businesses found")
                return None, None
                
            business = businesses[0]
            business_id = business.get("id")
            business_name = business.get("name", "Unknown Business")
            
            self.log_test(
                "Customer Order Creation - Get Businesses", 
                True, 
                f"Found {len(businesses)} businesses, using: {business_name} (ID: {business_id})"
            )
            
            # Get menu items for this business
            menu_response = self.customer_session.get(
                f"{BACKEND_URL}/api/business/public/{business_id}/menu", 
                timeout=10
            )
            
            if menu_response.status_code != 200:
                self.log_test("Customer Order Creation - Get Menu", False, error=f"Cannot get menu: {menu_response.status_code}")
                return None, None
                
            menu_items = menu_response.json()
            if not menu_items:
                self.log_test("Customer Order Creation - Get Menu", False, error="No menu items found")
                return None, None
                
            menu_item = menu_items[0]
            self.log_test(
                "Customer Order Creation - Get Menu", 
                True, 
                f"Found {len(menu_items)} menu items, using: {menu_item.get('name')} (₺{menu_item.get('price')})"
            )
            
            # Create order
            order_data = {
                "business_id": business_id,
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
                "notes": "Urgent system check test order"
            }
            
            order_response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                timeout=10
            )
            
            if order_response.status_code in [200, 201]:
                order = order_response.json()
                order_id = order.get("order_id") or order.get("id")
                
                # Verify order has business_id
                if order.get("business_id") == business_id:
                    self.log_test(
                        "Customer Order Creation - POST /api/orders",
                        True,
                        f"Order created successfully: ID={order_id}, business_id={order.get('business_id')}, total={order.get('total_amount')}"
                    )
                    return order_id, business_id
                else:
                    self.log_test(
                        "Customer Order Creation - POST /api/orders",
                        False,
                        error=f"Order created but business_id mismatch: expected {business_id}, got {order.get('business_id')}"
                    )
                    return None, None
            else:
                self.log_test(
                    "Customer Order Creation - POST /api/orders",
                    False,
                    error=f"Order creation failed: {order_response.status_code} - {order_response.text}"
                )
                return None, None
                
        except Exception as e:
            self.log_test("Customer Order Creation", False, error=f"Exception: {str(e)}")
            return None, None
    
    def test_business_order_reception(self, business_user, expected_business_id):
        """Test 2: Business Order Reception"""
        try:
            response = self.business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                timeout=10
            )
            
            if response.status_code == 200:
                orders = response.json()
                
                # Check if orders appear and have correct business_id
                matching_orders = [o for o in orders if o.get("business_id") == expected_business_id]
                
                if matching_orders:
                    order = matching_orders[0]
                    self.log_test(
                        "Business Order Reception - GET /api/business/orders/incoming",
                        True,
                        f"Found {len(matching_orders)} orders for business {expected_business_id}. Order fields: {list(order.keys())}"
                    )
                    return matching_orders[0].get("id")
                else:
                    self.log_test(
                        "Business Order Reception - GET /api/business/orders/incoming",
                        False,
                        error=f"No orders found for business {expected_business_id}. Total orders: {len(orders)}"
                    )
                    return None
            else:
                self.log_test(
                    "Business Order Reception - GET /api/business/orders/incoming",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Business Order Reception", False, error=f"Exception: {str(e)}")
            return None
    
    def test_business_order_confirmation(self, order_id):
        """Test 3: Business Order Confirmation"""
        try:
            confirm_data = {"unit_delivery_fee": 15.0}
            
            response = self.business_session.put(
                f"{BACKEND_URL}/api/business/orders/{order_id}/confirm",
                json=confirm_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if courier_tasks created
                if result.get("success") and result.get("task_id"):
                    self.log_test(
                        "Business Order Confirmation - PUT /api/business/orders/{order_id}/confirm",
                        True,
                        f"Order confirmed successfully: task_id={result.get('task_id')}, success={result.get('success')}"
                    )
                    return result.get("task_id")
                else:
                    self.log_test(
                        "Business Order Confirmation - PUT /api/business/orders/{order_id}/confirm",
                        False,
                        error=f"Confirmation response missing task_id: {result}"
                    )
                    return None
            else:
                self.log_test(
                    "Business Order Confirmation - PUT /api/business/orders/{order_id}/confirm",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Business Order Confirmation", False, error=f"Exception: {str(e)}")
            return None
    
    def test_courier_tasks(self, courier_user):
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
                    required_fields = ["id", "order_id", "business_id", "pickup_coords", "dropoff_coords", "unit_delivery_fee"]
                    missing_fields = [field for field in required_fields if field not in task]
                    
                    if not missing_fields:
                        self.log_test(
                            "Courier Tasks - GET /api/courier/tasks?status=waiting",
                            True,
                            f"Found {len(tasks)} waiting tasks. Task has all required fields: {required_fields}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Courier Tasks - GET /api/courier/tasks?status=waiting",
                            False,
                            error=f"Task missing required fields: {missing_fields}. Available fields: {list(task.keys())}"
                        )
                        return False
                else:
                    self.log_test(
                        "Courier Tasks - GET /api/courier/tasks?status=waiting",
                        False,
                        error="No waiting tasks found"
                    )
                    return False
            else:
                self.log_test(
                    "Courier Tasks - GET /api/courier/tasks?status=waiting",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Courier Tasks", False, error=f"Exception: {str(e)}")
            return False
    
    def test_coupon_system(self, admin_user):
        """Test 5: Coupon System"""
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/api/admin/coupons",
                timeout=10
            )
            
            if response.status_code == 200:
                coupons = response.json()
                self.log_test(
                    "Coupon System - GET /api/admin/coupons",
                    True,
                    f"Admin coupons endpoint accessible. Found {len(coupons)} coupons"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Coupon System - GET /api/admin/coupons",
                    False,
                    error="Coupon endpoint not implemented (404)"
                )
                return False
            elif response.status_code == 403:
                self.log_test(
                    "Coupon System - GET /api/admin/coupons",
                    False,
                    error="Admin access denied (403) - authentication issue"
                )
                return False
            else:
                self.log_test(
                    "Coupon System - GET /api/admin/coupons",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Coupon System", False, error=f"Exception: {str(e)}")
            return False
    
    def check_service_status(self):
        """Check if services are running"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
            
            if response.status_code == 200:
                health = response.json()
                self.log_test(
                    "Service Status Check",
                    True,
                    f"Backend service is running. Status: {health.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    "Service Status Check",
                    False,
                    error=f"Backend service unhealthy: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Service Status Check", False, error=f"Backend service unreachable: {str(e)}")
            return False
    
    def run_urgent_system_check(self):
        """Run all critical system checks"""
        print("🚨 URGENT FULL SYSTEM CHECK - Finding What's Not Working")
        print("=" * 80)
        
        # Check service status first
        if not self.check_service_status():
            print("❌ Backend service is down - cannot proceed with tests")
            return
        
        # Authenticate all users
        customer_success, customer_user = self.authenticate_user(self.customer_session, CUSTOMER_CREDENTIALS, "Customer")
        business_success, business_user = self.authenticate_user(self.business_session, BUSINESS_CREDENTIALS, "Business")
        courier_success, courier_user = self.authenticate_user(self.courier_session, COURIER_CREDENTIALS, "Courier")
        admin_success, admin_user = self.authenticate_user(self.admin_session, ADMIN_CREDENTIALS, "Admin")
        
        if not customer_success:
            print("❌ Customer authentication failed - cannot test order creation")
            return
            
        print("\n🔍 Testing Critical Flows...")
        print("-" * 50)
        
        # Test 1: Customer Order Creation
        order_id, business_id = self.test_customer_order_creation(customer_user)
        
        # Test 2: Business Order Reception (only if business auth worked)
        business_order_id = None
        if business_success and business_id:
            business_order_id = self.test_business_order_reception(business_user, business_id)
        elif not business_success:
            self.log_test("Business Order Reception", False, error="Business authentication failed")
        
        # Test 3: Business Order Confirmation (only if we have an order)
        task_id = None
        if business_success and business_order_id:
            task_id = self.test_business_order_confirmation(business_order_id)
        elif not business_order_id:
            self.log_test("Business Order Confirmation", False, error="No business order found to confirm")
        
        # Test 4: Courier Tasks (only if courier auth worked)
        if courier_success:
            self.test_courier_tasks(courier_user)
        else:
            self.log_test("Courier Tasks", False, error="Courier authentication failed")
        
        # Test 5: Coupon System (only if admin auth worked)
        if admin_success:
            self.test_coupon_system(admin_user)
        else:
            self.log_test("Coupon System", False, error="Admin authentication failed")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print detailed summary of what's working and what's broken"""
        print("\n" + "=" * 80)
        print("📊 URGENT SYSTEM CHECK RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n🚨 CRITICAL ISSUES FOUND:")
        critical_failures = []
        
        for result in self.test_results:
            if not result["success"]:
                critical_failures.append(f"   • {result['test']}: {result['error']}")
        
        if critical_failures:
            for failure in critical_failures:
                print(failure)
        else:
            print("   ✅ No critical issues found!")
        
        print(f"\n🎯 SYSTEM COMPONENT STATUS:")
        
        # Check each major component
        auth_working = any("Authentication" in r["test"] and r["success"] for r in self.test_results)
        order_creation_working = any("Customer Order Creation" in r["test"] and r["success"] for r in self.test_results)
        business_orders_working = any("Business Order Reception" in r["test"] and r["success"] for r in self.test_results)
        order_confirmation_working = any("Business Order Confirmation" in r["test"] and r["success"] for r in self.test_results)
        courier_tasks_working = any("Courier Tasks" in r["test"] and r["success"] for r in self.test_results)
        admin_access_working = any("Coupon System" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"   Authentication System: {'✅ WORKING' if auth_working else '❌ BROKEN'}")
        print(f"   Customer Order Creation: {'✅ WORKING' if order_creation_working else '❌ BROKEN'}")
        print(f"   Business Order Reception: {'✅ WORKING' if business_orders_working else '❌ BROKEN'}")
        print(f"   Business Order Confirmation: {'✅ WORKING' if order_confirmation_working else '❌ BROKEN'}")
        print(f"   Courier Task System: {'✅ WORKING' if courier_tasks_working else '❌ BROKEN'}")
        print(f"   Admin Panel Access: {'✅ WORKING' if admin_access_working else '❌ BROKEN'}")
        
        # Overall verdict
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: System is mostly WORKING ({success_rate:.1f}% success rate)")
        elif success_rate >= 50:
            print(f"\n⚠️ VERDICT: System has SIGNIFICANT ISSUES ({success_rate:.1f}% success rate)")
        else:
            print(f"\n🚨 VERDICT: System is CRITICALLY BROKEN ({success_rate:.1f}% success rate)")
        
        print(f"\n💡 RECOMMENDATION:")
        if not auth_working:
            print("   🔥 URGENT: Fix authentication system first - nothing else will work")
        elif not order_creation_working:
            print("   🔥 URGENT: Fix customer order creation - core functionality is broken")
        elif not business_orders_working:
            print("   🔥 URGENT: Fix business order reception - businesses can't see orders")
        else:
            print("   ✅ Core systems working - investigate minor issues")

def main():
    """Main test runner"""
    checker = UrgentSystemChecker()
    checker.run_urgent_system_check()

if __name__ == "__main__":
    main()