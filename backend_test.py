#!/usr/bin/env python3
"""
ORDER STATUS TRANSITIONS TEST
Test the complete order status transition flow with the new "confirmed" status

Expected Flow: created/pending → confirmed → preparing → ready

Phase 1: Create Order
Phase 2: Business Confirms Order (NEW)
Phase 3: Start Preparing (Creates Courier Task)
Phase 4: Mark as Ready
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

class OrderStatusTransitionTest:
    def __init__(self):
        self.session = None
        self.customer_cookies = None
        self.business_cookies = None
        self.order_id = None
        self.business_id = None
        
    async def setup_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        print("🔗 HTTP session initialized")
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            print("🔗 HTTP session closed")
    
    async def login_customer(self):
        """Phase 1.1: Login as customer"""
        print("\n🔐 Phase 1.1: Customer Login")
        
        login_data = {
            "email": "test@kuryecini.com",
            "password": "test123"
        }
        
        async with self.session.post(
            f"{BACKEND_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                # Extract cookies for future requests
                self.customer_cookies = response.cookies
                
                data = await response.json()
                print(f"✅ Customer login successful: {data.get('message', 'Login successful')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Customer login failed: {response.status} - {error_text}")
                return False
    
    async def login_business(self):
        """Phase 2.1: Login as business"""
        print("\n🔐 Phase 2.1: Business Login")
        
        login_data = {
            "email": "testbusiness@example.com",
            "password": "test123"
        }
        
        async with self.session.post(
            f"{BACKEND_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                # Extract cookies for future requests
                self.business_cookies = {}
                for cookie in response.cookies:
                    self.business_cookies[cookie.key] = cookie.value
                
                data = await response.json()
                user_data = data.get('user', {})
                self.business_id = user_data.get('id')
                print(f"✅ Business login successful: {user_data.get('business_name', 'Business')} (ID: {self.business_id})")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Business login failed: {response.status} - {error_text}")
                return False
    
    async def get_business_menu(self):
        """Get business menu items for order creation"""
        print("\n📋 Getting business menu items...")
        
        if not self.business_id:
            print("❌ Business ID not available")
            return []
        
        async with self.session.get(
            f"{BACKEND_URL}/business/public/{self.business_id}/menu",
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                menu_items = await response.json()
                print(f"✅ Found {len(menu_items)} menu items")
                return menu_items
            else:
                error_text = await response.text()
                print(f"⚠️ Menu retrieval failed: {response.status} - {error_text}")
                return []
    
    async def create_order(self):
        """Phase 1.2: Create a new order"""
        print("\n📦 Phase 1.2: Creating Order")
        
        if not self.customer_cookies:
            print("❌ Customer not logged in")
            return False
        
        # Get menu items first
        menu_items = await self.get_business_menu()
        if not menu_items:
            print("❌ No menu items available for order creation")
            return False
        
        # Use first available menu item
        menu_item = menu_items[0]
        
        order_data = {
            "business_id": self.business_id,
            "restaurant_id": self.business_id,
            "items": [
                {
                    "product_id": menu_item.get("id"),
                    "id": menu_item.get("id"),
                    "title": menu_item.get("name", "Test Item"),
                    "price": float(menu_item.get("price", 25.0)),
                    "quantity": 1
                }
            ],
            "delivery_address": "Test Address, Aksaray, Turkey",
            "delivery_lat": 38.3687,
            "delivery_lng": 34.0254,
            "payment_method": "cash_on_delivery",
            "notes": "Order Status Transition Test"
        }
        
        async with self.session.post(
            f"{BACKEND_URL}/orders",
            json=order_data,
            cookies=self.customer_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                order = data.get('order', {})
                self.order_id = order.get('id')
                status = order.get('status')
                total = order.get('totals', {}).get('grand', 0)
                
                print(f"✅ Order created successfully!")
                print(f"   Order ID: {self.order_id}")
                print(f"   Status: {status}")
                print(f"   Total: {total} TL")
                print(f"   Business ID: {order.get('business_id')}")
                
                # Verify initial status
                if status in ["created", "pending"]:
                    print(f"✅ Initial status verified: {status}")
                    return True
                else:
                    print(f"⚠️ Unexpected initial status: {status}")
                    return True  # Still continue with test
            else:
                error_text = await response.text()
                print(f"❌ Order creation failed: {response.status} - {error_text}")
                return False
    
    async def confirm_order(self):
        """Phase 2.2: Business confirms order (NEW)"""
        print("\n✅ Phase 2.2: Business Confirms Order")
        
        if not self.business_cookies or not self.order_id:
            print("❌ Business not logged in or order not created")
            return False
        
        status_data = {"status": "confirmed"}
        
        async with self.session.patch(
            f"{BACKEND_URL}/business/orders/{self.order_id}/status",
            json=status_data,
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                new_status = data.get('new_status')
                timestamp = data.get('timestamp')
                
                print(f"✅ Order confirmed successfully!")
                print(f"   New Status: {new_status}")
                print(f"   Timestamp: {timestamp}")
                
                # Verify status change
                if new_status == "confirmed":
                    print("✅ Status transition verified: → confirmed")
                    return True
                else:
                    print(f"❌ Unexpected status: {new_status}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Order confirmation failed: {response.status} - {error_text}")
                return False
    
    async def start_preparing(self):
        """Phase 3: Start preparing (Creates Courier Task)"""
        print("\n👨‍🍳 Phase 3: Start Preparing")
        
        if not self.business_cookies or not self.order_id:
            print("❌ Business not logged in or order not created")
            return False
        
        status_data = {"status": "preparing"}
        
        async with self.session.patch(
            f"{BACKEND_URL}/business/orders/{self.order_id}/status",
            json=status_data,
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                new_status = data.get('new_status')
                timestamp = data.get('timestamp')
                
                print(f"✅ Order preparation started!")
                print(f"   New Status: {new_status}")
                print(f"   Timestamp: {timestamp}")
                
                # Verify status change
                if new_status == "preparing":
                    print("✅ Status transition verified: confirmed → preparing")
                    return True
                else:
                    print(f"❌ Unexpected status: {new_status}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Preparation start failed: {response.status} - {error_text}")
                return False
    
    async def mark_ready(self):
        """Phase 4: Mark as ready"""
        print("\n🍽️ Phase 4: Mark as Ready")
        
        if not self.business_cookies or not self.order_id:
            print("❌ Business not logged in or order not created")
            return False
        
        status_data = {"status": "ready"}
        
        async with self.session.patch(
            f"{BACKEND_URL}/business/orders/{self.order_id}/status",
            json=status_data,
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                new_status = data.get('new_status')
                timestamp = data.get('timestamp')
                
                print(f"✅ Order marked as ready!")
                print(f"   New Status: {new_status}")
                print(f"   Timestamp: {timestamp}")
                
                # Verify status change
                if new_status == "ready":
                    print("✅ Status transition verified: preparing → ready")
                    return True
                else:
                    print(f"❌ Unexpected status: {new_status}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Ready marking failed: {response.status} - {error_text}")
                return False
    
    async def verify_order_in_confirmed_list(self):
        """Verify order appears in confirmed list"""
        print("\n📋 Verifying order in business active orders...")
        
        if not self.business_cookies:
            print("❌ Business not logged in")
            return False
        
        async with self.session.get(
            f"{BACKEND_URL}/business/orders/active",
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                orders = await response.json()
                
                # Find our order
                our_order = None
                for order in orders:
                    if order.get('id') == self.order_id:
                        our_order = order
                        break
                
                if our_order:
                    status = our_order.get('status')
                    print(f"✅ Order found in active orders list")
                    print(f"   Status: {status}")
                    print(f"   Customer: {our_order.get('customer_name')}")
                    print(f"   Total: {our_order.get('total_amount')} TL")
                    return True
                else:
                    print(f"⚠️ Order {self.order_id} not found in active orders list")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get active orders: {response.status} - {error_text}")
                return False
    
    async def verify_status_transitions(self):
        """Verify all status transitions are allowed"""
        print("\n🔄 Verifying Status Transition Rules...")
        
        expected_flow = ["created/pending", "confirmed", "preparing", "ready"]
        print(f"✅ Expected Flow: {' → '.join(expected_flow)}")
        
        # Test invalid transitions (should fail)
        print("\n🚫 Testing Invalid Transitions:")
        
        invalid_transitions = [
            {"from_status": "ready", "to_status": "confirmed", "should_fail": True},
            {"from_status": "ready", "to_status": "created", "should_fail": True}
        ]
        
        for transition in invalid_transitions:
            print(f"   Testing: {transition['from_status']} → {transition['to_status']}")
            # This would require creating additional orders in different states
            # For now, we'll just document the expected behavior
            print(f"   Expected: Should fail (not implemented in this test)")
        
        return True
    
    async def run_complete_test(self):
        """Run the complete order status transition test"""
        print("🚀 ORDER STATUS TRANSITIONS TEST")
        print("=" * 50)
        print("Testing: created/pending → confirmed → preparing → ready")
        print("=" * 50)
        
        try:
            await self.setup_session()
            
            # Phase 1: Create Order
            print("\n📦 PHASE 1: CREATE ORDER")
            if not await self.login_customer():
                return False
            
            if not await self.login_business():
                return False
            
            if not await self.create_order():
                return False
            
            # Phase 2: Business Confirms Order (NEW)
            print("\n✅ PHASE 2: BUSINESS CONFIRMS ORDER (NEW)")
            if not await self.confirm_order():
                return False
            
            # Verify order appears in confirmed list
            if not await self.verify_order_in_confirmed_list():
                return False
            
            # Phase 3: Start Preparing
            print("\n👨‍🍳 PHASE 3: START PREPARING")
            if not await self.start_preparing():
                return False
            
            # Phase 4: Mark as Ready
            print("\n🍽️ PHASE 4: MARK AS READY")
            if not await self.mark_ready():
                return False
            
            # Final verification
            if not await self.verify_order_in_confirmed_list():
                return False
            
            # Verify transition rules
            await self.verify_status_transitions()
            
            print("\n" + "=" * 50)
            print("🎉 ORDER STATUS TRANSITIONS TEST COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"✅ Order ID: {self.order_id}")
            print(f"✅ Business ID: {self.business_id}")
            print("✅ All transitions working correctly:")
            print("   • created/pending → confirmed ✅")
            print("   • confirmed → preparing ✅")
            print("   • preparing → ready ✅")
            print("✅ Order appears in business active orders list")
            print("✅ No 403 or 400 errors encountered")
            print("✅ Status progression is correct")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test = OrderStatusTransitionTest()
    success = await test.run_complete_test()
    
    if success:
        print("\n🎯 TEST RESULT: SUCCESS")
        sys.exit(0)
    else:
        print("\n💥 TEST RESULT: FAILURE")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())