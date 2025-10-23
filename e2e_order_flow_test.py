#!/usr/bin/env python3
"""
Complete End-to-End Order Flow Testing
Tests the complete order flow from customer order creation to courier acceptance
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

# Test credentials
CUSTOMER_CREDENTIALS = {
    "email": "test@kuryecini.com",
    "password": "test123"
}

BUSINESS_CREDENTIALS = {
    "email": "testbusiness@example.com", 
    "password": "test123"
}

COURIER_CREDENTIALS = {
    "email": "testkurye@example.com",
    "password": "test123"
}

# Test business ID
BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"

class E2EOrderFlowTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.order_id = None
        self.customer_session = None
        self.business_session = None
        self.courier_session = None
        
    async def setup_sessions(self):
        """Initialize HTTP sessions for different user types"""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        
        # Create separate sessions for each user type to maintain cookies
        self.customer_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "E2EOrderFlowTest/1.0"
            }
        )
        
        self.business_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "E2EOrderFlowTest/1.0"
            }
        )
        
        self.courier_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False),
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "E2EOrderFlowTest/1.0"
            }
        )
        
    async def cleanup_sessions(self):
        """Clean up HTTP sessions"""
        for session in [self.customer_session, self.business_session, self.courier_session]:
            if session:
                await session.close()
                
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} {test_name}: {details}")
        
    async def step_1_customer_login_and_order(self):
        """STEP 1: Customer Creates Order"""
        print("\n🔸 STEP 1: Customer Creates Order")
        print("-" * 40)
        
        try:
            # 1.1: Customer Login
            async with self.customer_session.post(
                f"{BACKEND_URL}/auth/login",
                json=CUSTOMER_CREDENTIALS
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.log_result(
                            "Customer Login",
                            True,
                            f"Authenticated as {CUSTOMER_CREDENTIALS['email']}"
                        )
                    else:
                        self.log_result("Customer Login", False, f"Login failed: {data.get('message')}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Customer Login", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 1.2: Get Business Menu
            async with self.customer_session.get(
                f"{BACKEND_URL}/business/public/{BUSINESS_ID}/menu"
            ) as response:
                
                if response.status == 200:
                    menu_items = await response.json()
                    if menu_items:
                        first_item = menu_items[0]
                        self.log_result(
                            "Get Business Menu",
                            True,
                            f"Retrieved {len(menu_items)} menu items, first item: {first_item.get('name', 'Unknown')}"
                        )
                    else:
                        self.log_result("Get Business Menu", False, "No menu items found")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Get Business Menu", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 1.3: Create Order
            order_data = {
                "business_id": BUSINESS_ID,
                "items": [
                    {
                        "product_id": first_item.get("id"),
                        "title": first_item.get("name", "Test Item"),
                        "price": float(first_item.get("price", 99.99)),
                        "quantity": 1
                    }
                ],
                "delivery_address": "Kızılay Mahallesi, Atatürk Bulvarı No:123, Ankara",
                "delivery_lat": 39.9334,
                "delivery_lng": 32.8597,
                "payment_method": "cash_on_delivery",
                "notes": "Örnek test siparişi - lütfen çabuk getirin"
            }
            
            async with self.customer_session.post(
                f"{BACKEND_URL}/orders",
                json=order_data
            ) as response:
                
                if response.status == 200:
                    order_response = await response.json()
                    # The response has nested structure: {"success": true, "order": {...}}
                    order_data_response = order_response.get("order", {})
                    self.order_id = order_data_response.get("id")
                    if self.order_id:
                        self.log_result(
                            "Create Order",
                            True,
                            f"Order created successfully with ID: {self.order_id}"
                        )
                        total = order_data_response.get("totals", {}).get("grand", 0)
                        print(f"📦 Order Details: Business ID: {BUSINESS_ID}, Total: ₺{total}")
                        return True
                    else:
                        self.log_result("Create Order", False, f"Order created but no order ID returned. Response: {order_response}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Create Order", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Customer Order Creation", False, f"Exception: {str(e)}")
            return False
            
    async def step_2_business_confirms_order(self):
        """STEP 2: Business Confirms Order"""
        print("\n🔸 STEP 2: Business Confirms and Marks Order Ready")
        print("-" * 50)
        
        try:
            # 2.1: Business Login
            async with self.business_session.post(
                f"{BACKEND_URL}/auth/login",
                json=BUSINESS_CREDENTIALS
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.log_result(
                            "Business Login",
                            True,
                            f"Authenticated as {BUSINESS_CREDENTIALS['email']}"
                        )
                    else:
                        self.log_result("Business Login", False, f"Login failed: {data.get('message')}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Business Login", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 2.2: Get Incoming Orders
            async with self.business_session.get(
                f"{BACKEND_URL}/business/orders/incoming"
            ) as response:
                
                if response.status == 200:
                    orders = await response.json()
                    order_found = any(order.get("id") == self.order_id for order in orders)
                    if order_found:
                        self.log_result(
                            "Verify Order in Business Panel",
                            True,
                            f"Order {self.order_id} found in incoming orders ({len(orders)} total orders)"
                        )
                    else:
                        self.log_result(
                            "Verify Order in Business Panel",
                            False,
                            f"Order {self.order_id} not found in {len(orders)} incoming orders"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Verify Order in Business Panel", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 2.3: Confirm Order
            async with self.business_session.patch(
                f"{BACKEND_URL}/business/orders/{self.order_id}/status",
                json={"status": "confirmed"}
            ) as response:
                
                if response.status == 200:
                    self.log_result(
                        "Confirm Order",
                        True,
                        f"Order {self.order_id} confirmed successfully"
                    )
                else:
                    error_text = await response.text()
                    self.log_result("Confirm Order", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 2.4: Mark Order as Ready
            async with self.business_session.patch(
                f"{BACKEND_URL}/business/orders/{self.order_id}/status",
                json={"status": "ready"}
            ) as response:
                
                if response.status == 200:
                    self.log_result(
                        "Mark Order Ready",
                        True,
                        f"Order {self.order_id} marked as ready"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Mark Order Ready", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Business Order Management", False, f"Exception: {str(e)}")
            return False
            
    async def step_3_verify_courier_map(self):
        """STEP 3: Verify Order in Courier Map"""
        print("\n🔸 STEP 3: Verify Order Appears in Courier Map")
        print("-" * 45)
        
        try:
            # 3.1: Courier Login
            async with self.courier_session.post(
                f"{BACKEND_URL}/auth/login",
                json=COURIER_CREDENTIALS
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        self.log_result(
                            "Courier Login",
                            True,
                            f"Authenticated as {COURIER_CREDENTIALS['email']}"
                        )
                    else:
                        self.log_result("Courier Login", False, f"Login failed: {data.get('message')}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Courier Login", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 3.2: Get Nearby Businesses
            params = {
                "lng": 34.0254,
                "lat": 38.3687,
                "radius_m": 50000
            }
            
            async with self.courier_session.get(
                f"{BACKEND_URL}/courier/tasks/nearby-businesses",
                params=params
            ) as response:
                
                if response.status == 200:
                    businesses = await response.json()
                    target_business = None
                    for business in businesses:
                        if business.get("business_id") == BUSINESS_ID:
                            target_business = business
                            break
                    
                    if target_business:
                        ready_count = target_business.get("pending_ready_count", 0)
                        if ready_count > 0:
                            self.log_result(
                                "Business in Courier Map",
                                True,
                                f"Business {BUSINESS_ID} found with {ready_count} ready orders"
                            )
                        else:
                            self.log_result(
                                "Business in Courier Map",
                                False,
                                f"Business {BUSINESS_ID} found but no ready orders ({ready_count})"
                            )
                            return False
                    else:
                        self.log_result(
                            "Business in Courier Map",
                            False,
                            f"Business {BUSINESS_ID} not found in {len(businesses)} nearby businesses"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Business in Courier Map", False, f"HTTP {response.status}: {error_text}")
                    return False
            
            # 3.3: Get Available Orders for Business
            async with self.courier_session.get(
                f"{BACKEND_URL}/courier/tasks/businesses/{BUSINESS_ID}/available-orders"
            ) as response:
                
                if response.status == 200:
                    orders = await response.json()
                    order_found = any(order.get("order_id") == self.order_id for order in orders)
                    if order_found:
                        self.log_result(
                            "Order in Available Orders",
                            True,
                            f"Order {self.order_id} found in available orders for business"
                        )
                        return True
                    else:
                        self.log_result(
                            "Order in Available Orders",
                            False,
                            f"Order {self.order_id} not found in {len(orders)} available orders"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Order in Available Orders", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Courier Map Verification", False, f"Exception: {str(e)}")
            return False
            
    async def step_4_courier_claims_order(self):
        """STEP 4: Courier Claims Order"""
        print("\n🔸 STEP 4: Courier Claims Order")
        print("-" * 30)
        
        try:
            # 4.1: Claim Order
            async with self.courier_session.post(
                f"{BACKEND_URL}/courier/tasks/orders/{self.order_id}/claim"
            ) as response:
                
                if response.status == 200:
                    claim_response = await response.json()
                    self.log_result(
                        "Claim Order",
                        True,
                        f"Order {self.order_id} claimed successfully"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("Claim Order", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Courier Order Claim", False, f"Exception: {str(e)}")
            return False
            
    async def step_5_verify_active_orders(self):
        """STEP 5: Verify Order in Courier Active Orders"""
        print("\n🔸 STEP 5: Verify Order in Courier Active Orders")
        print("-" * 45)
        
        try:
            # 5.1: Get Courier Active Orders
            async with self.courier_session.get(
                f"{BACKEND_URL}/courier/tasks/my-orders"
            ) as response:
                
                if response.status == 200:
                    orders = await response.json()
                    target_order = None
                    for order in orders:
                        if order.get("order_id") == self.order_id:
                            target_order = order
                            break
                    
                    if target_order:
                        # Verify order details
                        has_business_info = bool(target_order.get("business_name") and target_order.get("business_address"))
                        has_customer_info = bool(target_order.get("customer_name") and target_order.get("delivery_address"))
                        has_coordinates = bool(
                            target_order.get("business_location", {}).get("lat") and 
                            target_order.get("business_location", {}).get("lng") and
                            target_order.get("delivery_location", {}).get("lat") and 
                            target_order.get("delivery_location", {}).get("lng")
                        )
                        is_assigned = target_order.get("status") == "assigned"
                        
                        if has_business_info and has_customer_info and has_coordinates and is_assigned:
                            self.log_result(
                                "Order in Active Orders",
                                True,
                                f"Order {self.order_id} found in active orders with complete details"
                            )
                            
                            # Print order details
                            print(f"📋 Order Details:")
                            print(f"   Business: {target_order.get('business_name')}")
                            print(f"   Pickup: {target_order.get('business_address')}")
                            print(f"   Customer: {target_order.get('customer_name')}")
                            print(f"   Delivery: {target_order.get('delivery_address')}")
                            print(f"   Status: {target_order.get('status')}")
                            print(f"   Business GPS: {target_order.get('business_location')}")
                            print(f"   Delivery GPS: {target_order.get('delivery_location')}")
                            
                            return True
                        else:
                            missing_fields = []
                            if not has_business_info: missing_fields.append("business info")
                            if not has_customer_info: missing_fields.append("customer info")
                            if not has_coordinates: missing_fields.append("GPS coordinates")
                            if not is_assigned: missing_fields.append("assigned status")
                            
                            self.log_result(
                                "Order in Active Orders",
                                False,
                                f"Order {self.order_id} found but missing: {', '.join(missing_fields)}"
                            )
                            
                            # Debug: Print what we actually got
                            print(f"🔍 Debug - Order data received:")
                            print(f"   business_name: {target_order.get('business_name')}")
                            print(f"   business_address: {target_order.get('business_address')}")
                            print(f"   customer_name: {target_order.get('customer_name')}")
                            print(f"   delivery_address: {target_order.get('delivery_address')}")
                            print(f"   business_location: {target_order.get('business_location')}")
                            print(f"   delivery_location: {target_order.get('delivery_location')}")
                            print(f"   status: {target_order.get('status')}")
                            
                            return False
                    else:
                        self.log_result(
                            "Order in Active Orders",
                            False,
                            f"Order {self.order_id} not found in {len(orders)} active orders"
                        )
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Order in Active Orders", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Courier Active Orders Verification", False, f"Exception: {str(e)}")
            return False
            
    async def run_complete_flow(self):
        """Run complete end-to-end order flow"""
        print("🎯 COMPLETE END-TO-END ORDER FLOW TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Business ID: {BUSINESS_ID}")
        print(f"Customer: {CUSTOMER_CREDENTIALS['email']}")
        print(f"Business: {BUSINESS_CREDENTIALS['email']}")
        print(f"Courier: {COURIER_CREDENTIALS['email']}")
        print()
        
        await self.setup_sessions()
        
        try:
            # Execute all steps in sequence
            step1_success = await self.step_1_customer_login_and_order()
            if not step1_success:
                print("\n❌ STEP 1 FAILED - Cannot proceed")
                return False
                
            step2_success = await self.step_2_business_confirms_order()
            if not step2_success:
                print("\n❌ STEP 2 FAILED - Cannot proceed")
                return False
                
            step3_success = await self.step_3_verify_courier_map()
            if not step3_success:
                print("\n❌ STEP 3 FAILED - Cannot proceed")
                return False
                
            step4_success = await self.step_4_courier_claims_order()
            if not step4_success:
                print("\n❌ STEP 4 FAILED - Cannot proceed")
                return False
                
            step5_success = await self.step_5_verify_active_orders()
            if not step5_success:
                print("\n❌ STEP 5 FAILED")
                return False
                
            return True
            
        finally:
            await self.cleanup_sessions()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 COMPLETE FLOW TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
            
        print("\n" + "=" * 60)
        
        # Overall result
        if passed == total:
            print("🎉 COMPLETE ORDER FLOW SUCCESS!")
            print("✅ Customer can create orders")
            print("✅ Business can confirm and mark orders ready")
            print("✅ Orders appear in courier map")
            print("✅ Courier can claim orders")
            print("✅ Orders appear in courier active orders with complete details")
            print(f"📦 Test Order ID: {self.order_id}")
        else:
            print("🚨 ORDER FLOW ISSUES IDENTIFIED:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
                    
        return passed == total

async def main():
    """Main test execution"""
    tester = E2EOrderFlowTest()
    success = await tester.run_complete_flow()
    return success

if __name__ == "__main__":
    asyncio.run(main())