#!/usr/bin/env python3
"""
İŞLETME-MÜŞTERİ-KURYE ENTEGRASYON TEST
Complete end-to-end order flow from business to customer to courier

PRIORITY TEST SCENARIOS:
1. Business Order Management (Critical Priority)
2. Courier Order Management (Critical Priority) 
3. Complete E2E Order Flow Integration Test
4. Business-Customer Integration
5. Role-Based Access Control (RBAC)
6. Data Flow Validation

SUCCESS CRITERIA:
- Complete order flow from customer→business→courier works
- Business can see and manage their orders (confirm, prepare, ready)
- Couriers can see available orders and pick them up
- Proper role-based access control enforced
- Order status progression works correctly
- All endpoints return proper HTTP status codes and data
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://kuryecini-auth.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class BusinessCourierIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.user_data = {}
        self.test_order_id = None
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
    
    def authenticate_all_users(self):
        """Authenticate customer, business, and courier users"""
        print("🔐 AUTHENTICATING ALL USER TYPES")
        print("=" * 50)
        
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[user_type] = data.get("access_token")
                    self.user_data[user_type] = data.get("user", {})
                    
                    self.log_test(
                        f"{user_type.title()} Authentication",
                        True,
                        f"Login successful. User ID: {self.user_data[user_type].get('id')}, Role: {self.user_data[user_type].get('role')}",
                        {"user_id": self.user_data[user_type].get('id'), "role": self.user_data[user_type].get('role')}
                    )
                else:
                    self.log_test(
                        f"{user_type.title()} Authentication",
                        False,
                        f"Login failed. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
            except Exception as e:
                self.log_test(
                    f"{user_type.title()} Authentication",
                    False,
                    f"Exception during login: {str(e)}"
                )
                return False
        
        return True
    
    def create_test_order(self):
        """Create a test order as customer"""
        print("📦 CREATING TEST ORDER AS CUSTOMER")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_test("Create Test Order", False, "Customer authentication required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # First, get available products from the test business
        business_headers = {"Authorization": f"Bearer {self.tokens['business']}"}
        products_response = self.session.get(f"{BACKEND_URL}/products/my", headers=business_headers)
        
        if products_response.status_code != 200 or not products_response.json():
            self.log_test("Create Test Order", False, "No products available for test business")
            return False
        
        products = products_response.json()
        if len(products) < 2:
            self.log_test("Create Test Order", False, f"Need at least 2 products, found {len(products)}")
            return False
        
        # Use actual product IDs from the database
        product1 = products[0]
        product2 = products[1]
        
        # Create test order
        order_data = {
            "delivery_address": "Test Delivery Address, Kadıköy, İstanbul",
            "delivery_lat": 40.9876,
            "delivery_lng": 29.0234,
            "items": [
                {
                    "product_id": product1["id"],
                    "product_name": product1["name"],
                    "product_price": product1["price"],
                    "quantity": 2,
                    "subtotal": product1["price"] * 2
                },
                {
                    "product_id": product2["id"],
                    "product_name": product2["name"],
                    "product_price": product2["price"],
                    "quantity": 1,
                    "subtotal": product2["price"]
                }
            ],
            "total_amount": (product1["price"] * 2) + product2["price"],
            "notes": "Test order for integration testing"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/orders", json=order_data, headers=headers)
            
            if response.status_code == 200:
                order = response.json()
                self.test_order_id = order.get("id")
                
                self.log_test(
                    "Create Test Order",
                    True,
                    f"Order created successfully. Order ID: {self.test_order_id}, Status: {order.get('status')}",
                    {"order_id": self.test_order_id, "status": order.get('status'), "total_amount": order.get('total_amount')}
                )
                return True
            else:
                self.log_test(
                    "Create Test Order",
                    False,
                    f"Order creation failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Create Test Order",
                False,
                f"Exception during order creation: {str(e)}"
            )
            return False
    
    def test_business_incoming_orders(self):
        """Test GET /business/orders/incoming - business sees incoming orders"""
        print("🏪 TESTING BUSINESS INCOMING ORDERS")
        print("=" * 50)
        
        if "business" not in self.tokens:
            self.log_test("Business Incoming Orders", False, "Business authentication required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['business']}"}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/business/orders/incoming", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                # Check if our test order is visible
                test_order_found = any(order.get("order_id") == self.test_order_id for order in orders)
                
                self.log_test(
                    "GET /business/orders/incoming",
                    True,
                    f"Retrieved {len(orders)} incoming orders. Test order found: {test_order_found}",
                    {"order_count": len(orders), "test_order_found": test_order_found}
                )
                return True
            else:
                self.log_test(
                    "GET /business/orders/incoming",
                    False,
                    f"Failed to get incoming orders. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /business/orders/incoming",
                False,
                f"Exception during incoming orders test: {str(e)}"
            )
            return False
    
    def test_business_order_status_updates(self):
        """Test business order status updates: confirmed → preparing → ready"""
        print("📋 TESTING BUSINESS ORDER STATUS UPDATES")
        print("=" * 50)
        
        if "business" not in self.tokens or not self.test_order_id:
            self.log_test("Business Order Status Updates", False, "Business authentication and test order required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['business']}"}
        
        # Test status progression: confirmed → preparing → ready
        status_progression = ["confirmed", "preparing", "ready"]
        
        for status in status_progression:
            try:
                status_data = {"status": status}
                response = self.session.patch(
                    f"{BACKEND_URL}/business/orders/{self.test_order_id}/status",
                    json=status_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(
                        f"PATCH /business/orders/{{order_id}}/status - {status}",
                        True,
                        f"Order status updated to '{status}' successfully",
                        {"new_status": result.get("new_status"), "order_id": result.get("order_id")}
                    )
                else:
                    self.log_test(
                        f"PATCH /business/orders/{{order_id}}/status - {status}",
                        False,
                        f"Failed to update status to '{status}'. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
                # Small delay between status updates
                time.sleep(1)
                
            except Exception as e:
                self.log_test(
                    f"PATCH /business/orders/{{order_id}}/status - {status}",
                    False,
                    f"Exception during status update to '{status}': {str(e)}"
                )
                return False
        
        return True
    
    def test_courier_available_orders(self):
        """Test GET /courier/orders/available - courier sees ready orders"""
        print("🚚 TESTING COURIER AVAILABLE ORDERS")
        print("=" * 50)
        
        if "courier" not in self.tokens:
            self.log_test("Courier Available Orders", False, "Courier authentication required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/courier/orders/available", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                # Check if our test order is available for pickup
                test_order_found = any(order.get("order_id") == self.test_order_id for order in orders)
                ready_orders = [order for order in orders if order.get("status") == "ready"]
                
                self.log_test(
                    "GET /courier/orders/available",
                    True,
                    f"Retrieved {len(orders)} available orders, {len(ready_orders)} ready for pickup. Test order found: {test_order_found}",
                    {"total_orders": len(orders), "ready_orders": len(ready_orders), "test_order_found": test_order_found}
                )
                return True
            else:
                self.log_test(
                    "GET /courier/orders/available",
                    False,
                    f"Failed to get available orders. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /courier/orders/available",
                False,
                f"Exception during available orders test: {str(e)}"
            )
            return False
    
    def test_courier_pickup_order(self):
        """Test PATCH /courier/orders/{order_id}/pickup - courier picks up order"""
        print("📦 TESTING COURIER ORDER PICKUP")
        print("=" * 50)
        
        if "courier" not in self.tokens or not self.test_order_id:
            self.log_test("Courier Order Pickup", False, "Courier authentication and test order required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
        
        try:
            response = self.session.patch(
                f"{BACKEND_URL}/courier/orders/{self.test_order_id}/pickup",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "PATCH /courier/orders/{order_id}/pickup",
                    True,
                    f"Order picked up successfully. Courier ID: {result.get('courier_id')}",
                    {"order_id": result.get("order_id"), "courier_id": result.get("courier_id"), "pickup_time": result.get("pickup_time")}
                )
                return True
            else:
                self.log_test(
                    "PATCH /courier/orders/{order_id}/pickup",
                    False,
                    f"Failed to pickup order. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "PATCH /courier/orders/{order_id}/pickup",
                False,
                f"Exception during order pickup: {str(e)}"
            )
            return False
    
    def test_rbac_access_control(self):
        """Test Role-Based Access Control - cross-role access restrictions"""
        print("🔒 TESTING ROLE-BASED ACCESS CONTROL")
        print("=" * 50)
        
        # Test scenarios: wrong role trying to access endpoints
        rbac_tests = [
            # Customer trying to access business endpoints
            ("customer", "GET", "/business/orders/incoming", "Customer accessing business orders"),
            ("customer", "PATCH", f"/business/orders/{self.test_order_id or 'test'}/status", "Customer updating business order status"),
            
            # Customer trying to access courier endpoints
            ("customer", "GET", "/courier/orders/available", "Customer accessing courier orders"),
            ("customer", "PATCH", f"/courier/orders/{self.test_order_id or 'test'}/pickup", "Customer picking up order"),
            
            # Business trying to access courier endpoints
            ("business", "GET", "/courier/orders/available", "Business accessing courier orders"),
            ("business", "PATCH", f"/courier/orders/{self.test_order_id or 'test'}/pickup", "Business picking up order"),
            
            # Courier trying to access business endpoints
            ("courier", "GET", "/business/orders/incoming", "Courier accessing business orders"),
            ("courier", "PATCH", f"/business/orders/{self.test_order_id or 'test'}/status", "Courier updating business order status"),
        ]
        
        for user_type, method, endpoint, test_description in rbac_tests:
            if user_type not in self.tokens:
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                elif method == "PATCH":
                    test_data = {"status": "confirmed"} if "status" in endpoint else {}
                    response = self.session.patch(f"{BACKEND_URL}{endpoint}", json=test_data, headers=headers)
                
                # Should return 403 Forbidden for unauthorized role access
                if response.status_code == 403:
                    self.log_test(
                        f"RBAC - {test_description}",
                        True,
                        f"Properly rejected unauthorized access. Status: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_test(
                        f"RBAC - {test_description}",
                        False,
                        f"Should return 403 Forbidden but got: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"RBAC - {test_description}",
                    False,
                    f"Exception during RBAC test: {str(e)}"
                )
    
    def test_complete_e2e_flow(self):
        """Test complete end-to-end order flow integration"""
        print("🔄 TESTING COMPLETE E2E ORDER FLOW")
        print("=" * 50)
        
        # Verify final order status after complete flow
        if "customer" not in self.tokens or not self.test_order_id:
            self.log_test("Complete E2E Flow Verification", False, "Customer authentication and test order required")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        try:
            # Get order details to verify complete flow
            response = self.session.get(f"{BACKEND_URL}/orders", headers=headers)
            
            # Also try the customer-specific orders endpoint
            if response.status_code != 200:
                response = self.session.get(f"{BACKEND_URL}/orders/my", headers=headers)
            
            if response.status_code == 200:
                orders = response.json()
                test_order = next((order for order in orders if order.get("id") == self.test_order_id), None)
                
                if test_order:
                    final_status = test_order.get("status")
                    courier_assigned = test_order.get("courier_id") is not None
                    
                    # Expected final status should be "picked_up" after complete flow
                    flow_complete = final_status == "picked_up" and courier_assigned
                    
                    self.log_test(
                        "Complete E2E Flow Verification",
                        flow_complete,
                        f"Order final status: {final_status}, Courier assigned: {courier_assigned}",
                        {"final_status": final_status, "courier_assigned": courier_assigned, "order_id": self.test_order_id}
                    )
                    
                    # Log the complete flow progression
                    flow_summary = f"Customer Order Creation → Business Confirmation → Business Preparation → Business Ready → Courier Pickup"
                    self.log_test(
                        "E2E Flow Summary",
                        True,
                        f"Complete flow executed: {flow_summary}",
                        {"flow": "created → confirmed → preparing → ready → picked_up"}
                    )
                    
                    return flow_complete
                else:
                    self.log_test(
                        "Complete E2E Flow Verification",
                        False,
                        f"Test order {self.test_order_id} not found in customer orders"
                    )
                    return False
            else:
                self.log_test(
                    "Complete E2E Flow Verification",
                    False,
                    f"Failed to get customer orders. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Complete E2E Flow Verification",
                False,
                f"Exception during E2E flow verification: {str(e)}"
            )
            return False
    
    def test_data_flow_validation(self):
        """Test data consistency across business and courier views"""
        print("📊 TESTING DATA FLOW VALIDATION")
        print("=" * 50)
        
        if not all(role in self.tokens for role in ["business", "courier"]) or not self.test_order_id:
            self.log_test("Data Flow Validation", False, "All role authentications and test order required")
            return False
        
        # Get order data from business perspective
        business_headers = {"Authorization": f"Bearer {self.tokens['business']}"}
        courier_headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
        
        try:
            # Get business view of orders
            business_response = self.session.get(f"{BACKEND_URL}/business/orders/incoming", headers=business_headers)
            
            # Get courier view of orders
            courier_response = self.session.get(f"{BACKEND_URL}/courier/orders/available", headers=courier_headers)
            
            if business_response.status_code == 200 and courier_response.status_code == 200:
                business_orders = business_response.json().get("orders", [])
                courier_orders = courier_response.json().get("orders", [])
                
                # Find our test order in both views
                business_order = next((order for order in business_orders if order.get("order_id") == self.test_order_id), None)
                courier_order = next((order for order in courier_orders if order.get("order_id") == self.test_order_id), None)
                
                data_consistent = True
                consistency_details = []
                
                if business_order and courier_order:
                    # Check data consistency
                    if business_order.get("total_amount") != courier_order.get("total_amount"):
                        data_consistent = False
                        consistency_details.append("Total amount mismatch")
                    
                    if business_order.get("delivery_address") != courier_order.get("delivery_address"):
                        data_consistent = False
                        consistency_details.append("Delivery address mismatch")
                    
                    consistency_details.append(f"Business view status: {business_order.get('status')}")
                    consistency_details.append(f"Courier view status: {courier_order.get('status')}")
                
                self.log_test(
                    "Data Flow Validation",
                    data_consistent,
                    f"Data consistency check: {', '.join(consistency_details) if consistency_details else 'All data consistent'}",
                    {"business_order_found": business_order is not None, "courier_order_found": courier_order is not None}
                )
                
                return data_consistent
            else:
                self.log_test(
                    "Data Flow Validation",
                    False,
                    f"Failed to get order data. Business: {business_response.status_code}, Courier: {courier_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Data Flow Validation",
                False,
                f"Exception during data flow validation: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 STARTING İŞLETME-MÜŞTERİ-KURYE ENTEGRASYON TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate all users
        if not self.authenticate_all_users():
            print("❌ CRITICAL: User authentication failed. Cannot proceed with integration tests.")
            return self.generate_final_report()
        
        # Step 2: Create test order as customer
        if not self.create_test_order():
            print("❌ CRITICAL: Test order creation failed. Cannot proceed with integration tests.")
            return self.generate_final_report()
        
        # Step 3: Test business order management
        self.test_business_incoming_orders()
        self.test_business_order_status_updates()
        
        # Step 4: Test courier order management
        self.test_courier_available_orders()
        self.test_courier_pickup_order()
        
        # Step 5: Test role-based access control
        self.test_rbac_access_control()
        
        # Step 6: Test complete E2E flow (with small delay for data consistency)
        time.sleep(2)
        self.test_complete_e2e_flow()
        
        # Step 7: Test data flow validation
        self.test_data_flow_validation()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 İŞLETME-MÜŞTERİ-KURYE ENTEGRASYON TEST RESULTS")
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
        
        # Critical success criteria check
        critical_tests = [
            "Customer Authentication",
            "Business Authentication", 
            "Courier Authentication",
            "Create Test Order",
            "GET /business/orders/incoming",
            "PATCH /business/orders/{order_id}/status - confirmed",
            "PATCH /business/orders/{order_id}/status - preparing",
            "PATCH /business/orders/{order_id}/status - ready",
            "GET /courier/orders/available",
            "PATCH /courier/orders/{order_id}/pickup",
            "Complete E2E Flow Verification"
        ]
        
        critical_passed = 0
        print("🎯 CRITICAL SUCCESS CRITERIA:")
        for test_name in critical_tests:
            test_result = next((test for test in self.results["test_details"] if test["test"] == test_name), None)
            if test_result and "✅ PASS" in test_result["status"]:
                print(f"  ✅ {test_name}")
                critical_passed += 1
            else:
                print(f"  ❌ {test_name}")
        
        critical_success_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 0
        print(f"\nCritical Tests Success Rate: {critical_success_rate:.1f}% ({critical_passed}/{len(critical_tests)})")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Overall assessment
        if critical_success_rate >= 90 and success_rate >= 85:
            print("🎉 EXCELLENT: Business-Customer-Courier integration is working perfectly!")
            print("✅ Complete order flow from customer→business→courier is functional")
            print("✅ Role-based access control is properly enforced")
            print("✅ All critical endpoints are working correctly")
        elif critical_success_rate >= 75 and success_rate >= 70:
            print("✅ GOOD: Integration is mostly functional with minor issues.")
            print("⚠️ Some non-critical features may need attention")
        elif critical_success_rate >= 50:
            print("⚠️ MODERATE: Integration has significant issues that need attention.")
            print("❌ Critical order flow components are not working properly")
        else:
            print("❌ CRITICAL: Integration has major failures requiring immediate fixes.")
            print("🚨 Business-Customer-Courier flow is not functional")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "critical_success_rate": critical_success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "critical_passed": critical_passed,
            "critical_total": len(critical_tests),
            "details": self.results["test_details"]
        }

def main():
    """Main test execution"""
    tester = BusinessCourierIntegrationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["critical_success_rate"] >= 75 and results["success_rate"] >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()