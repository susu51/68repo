#!/usr/bin/env python3
"""
COMPREHENSIVE BUSINESS ORDER AUTHORIZATION TEST

Test business authorization for order status updates with multiple transitions:
1. Login as business: testbusiness@example.com / test123
2. Get business_id from user response  
3. Create test orders and test multiple status transitions
4. Test with 2-3 orders to confirm consistency

Test Cases:
- Case 1: Business Updates Own Order (SHOULD WORK)
- Case 2: Multiple Status Transitions (confirmed → preparing → ready)
- Case 3: Verify Authorization Logic
- Critical Check: Business user ID should match order business_id directly
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

class ComprehensiveBusinessAuthTest:
    def __init__(self):
        self.session = None
        self.customer_cookies = None
        self.business_cookies = None
        self.business_id = None
        self.test_orders = []
        
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
    
    async def login_business(self):
        """Step 1: Login as business and get business_id"""
        print("\n🔐 Step 1: Business Login")
        
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
                self.business_cookies = response.cookies
                data = await response.json()
                user_data = data.get('user', {})
                self.business_id = user_data.get('id')
                business_name = user_data.get('business_name', 'Unknown Business')
                
                print(f"✅ Business login successful")
                print(f"   Business Name: {business_name}")
                print(f"   Business ID: {self.business_id}")
                print(f"   Email: {user_data.get('email')}")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Business login failed: {response.status} - {error_text}")
                return False
    
    async def login_customer(self):
        """Login as customer to create test orders"""
        print("\n🔐 Customer Login (for order creation)")
        
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
                self.customer_cookies = response.cookies
                data = await response.json()
                print(f"✅ Customer login successful: {data.get('user', {}).get('email')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Customer login failed: {response.status} - {error_text}")
                return False
    
    async def get_business_menu(self):
        """Get business menu items for order creation"""
        print(f"\n📋 Getting menu for business {self.business_id}...")
        
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
    
    async def create_test_orders(self, count=3):
        """Step 2: Create multiple test orders"""
        print(f"\n📦 Step 2: Creating {count} test orders for business {self.business_id}")
        
        if not self.customer_cookies or not self.business_id:
            print("❌ Customer not logged in or business_id not available")
            return []
        
        # Get menu items first
        menu_items = await self.get_business_menu()
        if not menu_items:
            print("❌ No menu items available for order creation")
            return []
        
        created_orders = []
        
        for i in range(count):
            # Use different menu items if available
            menu_item = menu_items[i % len(menu_items)]
            
            order_data = {
                "business_id": self.business_id,
                "items": [
                    {
                        "product_id": menu_item.get("id"),
                        "title": menu_item.get("name", f"Test Item {i+1}"),
                        "price": float(menu_item.get("price", 25.0 + i)),
                        "quantity": 1
                    }
                ],
                "delivery_address": f"Test Address {i+1}, Aksaray, Turkey",
                "delivery_lat": 38.3687 + (i * 0.001),
                "delivery_lng": 34.0254 + (i * 0.001),
                "payment_method": "cash_on_delivery",
                "notes": f"Business Authorization Test Order #{i+1}"
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
                    order_id = order.get('id')
                    order_business_id = order.get('business_id')
                    
                    print(f"✅ Test order #{i+1} created successfully!")
                    print(f"   Order ID: {order_id}")
                    print(f"   Order Business ID: {order_business_id}")
                    print(f"   Status: {order.get('status')}")
                    
                    # Verify business_id matches
                    if order_business_id == self.business_id:
                        print("✅ Business ID match confirmed")
                        created_orders.append(order_id)
                    else:
                        print(f"❌ Business ID mismatch! Order: {order_business_id}, Expected: {self.business_id}")
                else:
                    error_text = await response.text()
                    print(f"❌ Order #{i+1} creation failed: {response.status} - {error_text}")
        
        print(f"\n✅ Created {len(created_orders)} test orders successfully")
        return created_orders
    
    async def test_status_transition(self, order_id, new_status):
        """Test a single status transition"""
        print(f"\n🔄 Testing transition to '{new_status}' for order {order_id}")
        
        status_data = {"status": new_status}
        
        async with self.session.patch(
            f"{BACKEND_URL}/business/orders/{order_id}/status",
            json=status_data,
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            response_text = await response.text()
            
            print(f"   Request: PATCH /api/business/orders/{order_id}/status")
            print(f"   Payload: {json.dumps(status_data)}")
            print(f"   Response Status: {response.status}")
            
            if response.status == 200:
                try:
                    data = json.loads(response_text)
                    actual_status = data.get('new_status')
                    timestamp = data.get('timestamp')
                    print(f"✅ Status transition successful!")
                    print(f"   New Status: {actual_status}")
                    print(f"   Timestamp: {timestamp}")
                    return True, actual_status
                except json.JSONDecodeError:
                    print(f"✅ Status transition successful (non-JSON response)")
                    return True, new_status
            elif response.status == 403:
                print(f"❌ CRITICAL: 403 Forbidden - Authorization failed!")
                print(f"   This should NOT happen for business updating own order")
                return False, None
            elif response.status == 422:
                print(f"⚠️ Invalid status transition: {response.status}")
                print(f"   Response: {response_text}")
                return False, None
            else:
                print(f"⚠️ Status transition failed: {response.status}")
                print(f"   Response: {response_text}")
                return False, None
    
    async def test_complete_order_flow(self, order_id):
        """Test complete order status flow: confirmed → preparing → ready"""
        print(f"\n🎯 Testing Complete Order Flow for {order_id}")
        print("   Flow: pending → confirmed → preparing → ready")
        
        transitions = [
            ("confirmed", "Business confirms order"),
            ("preparing", "Business starts preparing"),
            ("ready", "Order ready for pickup")
        ]
        
        success_count = 0
        
        for status, description in transitions:
            print(f"\n   {description} ({status})...")
            success, actual_status = await self.test_status_transition(order_id, status)
            
            if success:
                success_count += 1
                print(f"   ✅ {description} - SUCCESS")
            else:
                print(f"   ❌ {description} - FAILED")
                break  # Stop on first failure
        
        print(f"\n🎯 Order Flow Result: {success_count}/{len(transitions)} transitions successful")
        return success_count == len(transitions)
    
    async def verify_authorization_consistency(self):
        """Verify authorization logic is consistent"""
        print(f"\n🔍 Verifying Authorization Consistency")
        
        # Get current user info to verify business_id
        async with self.session.get(
            f"{BACKEND_URL}/me",
            cookies=self.business_cookies,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                user_data = await response.json()
                current_user_id = user_data.get('id')
                
                print(f"✅ Current business user ID: {current_user_id}")
                print(f"✅ Expected business ID: {self.business_id}")
                
                if current_user_id == self.business_id:
                    print("✅ Business user ID matches expected business_id")
                    print("✅ Authorization should work for all orders with matching business_id")
                    return True
                else:
                    print(f"❌ Business user ID mismatch!")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get current user: {response.status} - {error_text}")
                return False
    
    async def run_comprehensive_test(self):
        """Run the comprehensive business authorization test"""
        print("🚀 COMPREHENSIVE BUSINESS ORDER AUTHORIZATION TEST")
        print("=" * 70)
        print("Testing business authorization with multiple orders and status transitions")
        print("=" * 70)
        
        try:
            await self.setup_session()
            
            # Step 1: Login as business and get business_id
            if not await self.login_business():
                return False
            
            # Login as customer for order creation
            if not await self.login_customer():
                return False
            
            # Step 2: Create multiple test orders
            test_orders = await self.create_test_orders(3)
            
            if not test_orders:
                print("❌ No test orders created")
                return False
            
            # Step 3: Verify authorization consistency
            if not await self.verify_authorization_consistency():
                return False
            
            # Step 4: Test complete order flows
            print(f"\n" + "="*70)
            print("TESTING COMPLETE ORDER FLOWS")
            print("="*70)
            
            successful_flows = 0
            
            for i, order_id in enumerate(test_orders, 1):
                print(f"\n📋 ORDER {i}/{len(test_orders)}: {order_id}")
                print("-" * 50)
                
                if await self.test_complete_order_flow(order_id):
                    successful_flows += 1
                    print(f"✅ Order {i} flow completed successfully")
                else:
                    print(f"❌ Order {i} flow failed")
            
            # Final Results
            print("\n" + "=" * 70)
            print("🎯 COMPREHENSIVE AUTHORIZATION TEST RESULTS")
            print("=" * 70)
            
            success_rate = (successful_flows / len(test_orders) * 100) if test_orders else 0
            
            print(f"✅ Business ID: {self.business_id}")
            print(f"✅ Test Orders Created: {len(test_orders)}")
            print(f"✅ Successful Order Flows: {successful_flows}/{len(test_orders)} ({success_rate:.1f}%)")
            
            if successful_flows == len(test_orders):
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ Business can update own orders")
                print("✅ Authorization logic working correctly")
                print("✅ No 403 errors for valid operations")
                print("✅ Complete status transitions working")
                print("✅ Business user ID matches order business_id directly")
                return True
            else:
                print(f"\n⚠️ {len(test_orders) - successful_flows} order flows failed")
                return False
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    test = ComprehensiveBusinessAuthTest()
    success = await test.run_comprehensive_test()
    
    if success:
        print("\n🎯 TEST RESULT: SUCCESS")
        sys.exit(0)
    else:
        print("\n💥 TEST RESULT: FAILURE")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())