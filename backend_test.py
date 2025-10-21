#!/usr/bin/env python3
"""
COMPLETE ORDER FLOW TESTING - Backend API Testing
Testing the entire order creation and management flow as requested in review.

Test Scenarios:
1. Create Order (Customer Side)
2. Business Gets Orders  
3. Order Status Updates
4. Order Details
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Test credentials
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

class OrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.customer_cookies = None
        self.business_cookies = None
        self.test_order_id = None
        self.business_id = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_customer_login(self):
        """Test 1: Customer Login"""
        self.log("🔐 Testing Customer Login...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": CUSTOMER_EMAIL,
                    "password": CUSTOMER_PASSWORD
                }
            )
            
            if response.status_code == 200:
                self.customer_cookies = response.cookies
                data = response.json()
                self.log(f"✅ Customer login successful: {data.get('message', 'Login OK')}")
                return True
            else:
                self.log(f"❌ Customer login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Customer login error: {str(e)}")
            return False
    
    def test_get_restaurants(self):
        """Test 2: Get Available Restaurants"""
        self.log("🏪 Testing Restaurant Discovery...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/restaurants",
                cookies=self.customer_cookies
            )
            
            if response.status_code == 200:
                restaurants = response.json()
                if restaurants:
                    self.business_id = restaurants[0].get('id')
                    business_name = restaurants[0].get('name', 'Unknown')
                    self.log(f"✅ Found {len(restaurants)} restaurants. Selected: {business_name} (ID: {self.business_id})")
                    return True
                else:
                    self.log("❌ No restaurants found")
                    return False
            else:
                self.log(f"❌ Restaurant discovery failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Restaurant discovery error: {str(e)}")
            return False
    
    def test_get_menu(self):
        """Test 3: Get Menu for Restaurant"""
        self.log("📋 Testing Menu Retrieval...")
        
        if not self.business_id:
            self.log("❌ No business_id available for menu test")
            return False
            
        try:
            response = self.session.get(
                f"{BACKEND_URL}/business/public/{self.business_id}/menu",
                cookies=self.customer_cookies
            )
            
            if response.status_code == 200:
                menu_items = response.json()
                if menu_items:
                    item = menu_items[0]
                    self.log(f"✅ Menu retrieved: {len(menu_items)} items. First item: {item.get('name', 'Unknown')} - ₺{item.get('price', 0)}")
                    return menu_items
                else:
                    self.log("⚠️ Menu is empty but endpoint works")
                    return []
            else:
                self.log(f"❌ Menu retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Menu retrieval error: {str(e)}")
            return False
    
    def test_create_order(self, menu_items):
        """Test 4: Create Order"""
        self.log("📦 Testing Order Creation...")
        
        if not menu_items:
            # Create a test order with mock data if no menu items
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "id": "test-item-1",
                        "name": "Test Item",
                        "quantity": 1,
                        "price": 29.99
                    }
                ],
                "delivery_address": "Test Address, Aksaray",
                "delivery_coords": {"lat": 38.3687, "lng": 34.0254},
                "payment_method": "cash",
                "notes": "Test order"
            }
        else:
            # Use actual menu item
            item = menu_items[0]
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "id": item.get('id'),
                        "name": item.get('name', 'Test Item'),
                        "quantity": 1,
                        "price": item.get('price', 29.99)
                    }
                ],
                "delivery_address": "Test Address, Aksaray",
                "delivery_coords": {"lat": 38.3687, "lng": 34.0254},
                "payment_method": "cash",
                "notes": "Test order from backend test"
            }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                cookies=self.customer_cookies
            )
            
            if response.status_code in [200, 201]:
                order_response = response.json()
                self.test_order_id = order_response.get('order_id') or order_response.get('id')
                order_code = order_response.get('order_code', 'N/A')
                status = order_response.get('status', 'N/A')
                created_at = order_response.get('created_at', 'N/A')
                
                self.log(f"✅ Order created successfully!")
                self.log(f"   Order ID: {self.test_order_id}")
                self.log(f"   Order Code: {order_code}")
                self.log(f"   Status: {status}")
                self.log(f"   Created: {created_at}")
                return True
            else:
                self.log(f"❌ Order creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Order creation error: {str(e)}")
            return False
    
    def test_business_login(self):
        """Test 5: Business Login"""
        self.log("🏢 Testing Business Login...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": BUSINESS_EMAIL,
                    "password": BUSINESS_PASSWORD
                }
            )
            
            if response.status_code == 200:
                self.business_cookies = response.cookies
                data = response.json()
                self.log(f"✅ Business login successful: {data.get('message', 'Login OK')}")
                return True
            else:
                self.log(f"❌ Business login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Business login error: {str(e)}")
            return False
    
    def test_business_get_orders(self):
        """Test 6: Business Gets Orders"""
        self.log("📋 Testing Business Order Retrieval...")
        
        try:
            # Test with business_id parameter
            response = self.session.get(
                f"{BACKEND_URL}/orders?business_id={self.business_id}",
                cookies=self.business_cookies
            )
            
            if response.status_code == 200:
                orders = response.json()
                self.log(f"✅ Business orders retrieved: {len(orders)} orders found")
                
                # Look for our test order
                test_order_found = False
                for order in orders:
                    if order.get('id') == self.test_order_id or order.get('order_id') == self.test_order_id:
                        test_order_found = True
                        self.log(f"✅ Test order found in business orders!")
                        self.log(f"   Order Code: {order.get('order_code', 'N/A')}")
                        self.log(f"   Customer: {order.get('customer_name', 'N/A')}")
                        self.log(f"   Status: {order.get('status', 'N/A')}")
                        self.log(f"   Total: ₺{order.get('total_amount', 0)}")
                        break
                
                if not test_order_found and self.test_order_id:
                    self.log(f"⚠️ Test order {self.test_order_id} not found in business orders")
                
                return True
            else:
                self.log(f"❌ Business order retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Business order retrieval error: {str(e)}")
            return False
    
    def test_order_status_updates(self):
        """Test 7: Order Status Updates"""
        self.log("🔄 Testing Order Status Updates...")
        
        if not self.test_order_id:
            self.log("❌ No test order ID available for status updates")
            return False
        
        # Test status progression: preparing -> ready -> confirmed
        statuses_to_test = ["preparing", "ready", "confirmed"]
        
        for status in statuses_to_test:
            try:
                response = self.session.patch(
                    f"{BACKEND_URL}/orders/{self.test_order_id}/status",
                    json={"status": status},
                    cookies=self.business_cookies
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Status updated to '{status}': {result.get('message', 'Success')}")
                else:
                    self.log(f"❌ Status update to '{status}' failed: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Status update to '{status}' error: {str(e)}")
                return False
        
        return True
    
    def test_order_details(self):
        """Test 8: Order Details Retrieval"""
        self.log("📄 Testing Order Details Retrieval...")
        
        if not self.test_order_id:
            self.log("❌ No test order ID available for details test")
            return False
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}",
                cookies=self.business_cookies
            )
            
            if response.status_code == 200:
                order = response.json()
                self.log(f"✅ Order details retrieved successfully!")
                
                # Verify required fields
                required_fields = ['customer_name', 'delivery_address', 'items', 'status', 'total_amount']
                missing_fields = []
                
                for field in required_fields:
                    if field not in order or order[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log(f"⚠️ Missing fields in order details: {missing_fields}")
                else:
                    self.log("✅ All required fields present in order details")
                
                # Log key details
                self.log(f"   Customer: {order.get('customer_name', 'N/A')}")
                self.log(f"   Phone: {order.get('customer_phone', 'N/A')}")
                self.log(f"   Address: {order.get('delivery_address', 'N/A')}")
                self.log(f"   Coords: {order.get('delivery_coords', 'N/A')}")
                self.log(f"   Items: {len(order.get('items', []))} items")
                self.log(f"   Status: {order.get('status', 'N/A')}")
                self.log(f"   Total: ₺{order.get('total_amount', 0)}")
                
                return True
            else:
                self.log(f"❌ Order details retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Order details retrieval error: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run the complete order flow test"""
        self.log("🚀 STARTING COMPLETE ORDER FLOW TESTING")
        self.log("=" * 60)
        
        test_results = []
        
        # Test 1: Customer Login
        result = self.test_customer_login()
        test_results.append(("Customer Login", result))
        if not result:
            self.log("❌ Cannot continue without customer login")
            return self.print_summary(test_results)
        
        # Test 2: Get Restaurants
        result = self.test_get_restaurants()
        test_results.append(("Restaurant Discovery", result))
        if not result:
            self.log("❌ Cannot continue without restaurants")
            return self.print_summary(test_results)
        
        # Test 3: Get Menu
        menu_items = self.test_get_menu()
        test_results.append(("Menu Retrieval", bool(menu_items is not False)))
        
        # Test 4: Create Order
        result = self.test_create_order(menu_items if menu_items else [])
        test_results.append(("Order Creation", result))
        if not result:
            self.log("❌ Cannot continue without order creation")
            return self.print_summary(test_results)
        
        # Test 5: Business Login
        result = self.test_business_login()
        test_results.append(("Business Login", result))
        if not result:
            self.log("❌ Cannot continue without business login")
            return self.print_summary(test_results)
        
        # Test 6: Business Get Orders
        result = self.test_business_get_orders()
        test_results.append(("Business Order Retrieval", result))
        
        # Test 7: Order Status Updates
        result = self.test_order_status_updates()
        test_results.append(("Order Status Updates", result))
        
        # Test 8: Order Details
        result = self.test_order_details()
        test_results.append(("Order Details Retrieval", result))
        
        return self.print_summary(test_results)
    
    def print_summary(self, test_results):
        """Print test summary"""
        self.log("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log("=" * 60)
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"📈 OVERALL RESULT: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        
        if success_rate >= 80:
            self.log("🎉 EXCELLENT - Order flow is working well!")
        elif success_rate >= 60:
            self.log("⚠️ GOOD - Order flow mostly working with some issues")
        else:
            self.log("🚨 CRITICAL - Major issues in order flow")
        
        return success_rate >= 60

if __name__ == "__main__":
    tester = OrderFlowTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 CONCLUSION: Order flow testing completed successfully")
    else:
        print("\n🚨 CONCLUSION: Order flow has critical issues that need attention")
