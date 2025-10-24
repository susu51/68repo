#!/usr/bin/env python3
"""
CRITICAL BUSINESS ORDER FLOW TESTING - Turkish Scenario
Müşteri siparişinden işletme onayına ve kurye havuzuna kadar tüm akışı test et

Test Senaryosu:
1. Müşteri olarak login yap (test@kuryecini.com / test123)
2. Yeni bir sipariş oluştur
3. İşletme olarak login yap (test_business@example.com / test123)
4. GET /api/business/orders/incoming - Yeni sipariş geldi mi kontrol et
5. PATCH /api/orders/{order_id}/status - Siparişi onayla {"to": "confirmed"}
6. PATCH /api/orders/{order_id}/status - Hazır duruma getir {"to": "ready"}
7. Kurye olarak login yap (testkurye@example.com / test123)
8. GET /api/courier/tasks/nearby-businesses - İşletme listesinde var mı?
9. GET /api/courier/tasks/businesses/{business_id}/available-orders - Hazır sipariş görünüyor mu?
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from frontend environment
BASE_URL = "https://kuryecini-hub.preview.emergentagent.com/api"

class KuryeciniOrderFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'KuryeciniTester/1.0'
        })
        self.customer_token = None
        self.business_token = None
        self.courier_token = None
        self.order_id = None
        self.business_id = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"  # Test business ID
        
        # Test results tracking
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        
        self.results.append(result)
        if success:
            self.passed += 1
        else:
            self.failed += 1
        
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and response_data:
            print(f"   🔍 Response: {response_data}")
        print()

    def test_customer_login(self):
        """Test 1: Müşteri olarak login yap (test@kuryecini.com / test123)"""
        try:
            login_data = {
                "email": "test@kuryecini.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "user" in data:
                    # Set cookie-based authentication
                    self.customer_token = "cookie_auth"
                    user_info = data["user"]
                    self.log_result(
                        "Customer Login", 
                        True, 
                        f"Login successful for {user_info.get('email', 'N/A')}, Role: {user_info.get('role', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result("Customer Login", False, "Login response missing success or user data", data)
                    return False
            else:
                self.log_result("Customer Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Customer Login", False, f"Exception: {str(e)}")
            return False
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Courier Login",
                        False, 
                        f"HTTP {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Courier Login", False, f"Exception: {str(e)}")
            return False
            
    async def test_nearby_businesses_endpoint(self):
        """Test 2: Nearby Businesses Endpoint"""
        try:
            # Test coordinates (Aksaray area)
            params = {
                "lng": 34.0254,
                "lat": 38.3687,
                "radius_m": 50000  # 50km radius to ensure we find businesses
            }
            
            async with self.session.get(
                f"{BACKEND_URL}/courier/tasks/nearby-businesses",
                params=params
            ) as response:
                
                if response.status == 200:
                    businesses = await response.json()
                    
                    if isinstance(businesses, list):
                        self.log_result(
                            "Nearby Businesses Endpoint",
                            True,
                            f"Returned {len(businesses)} businesses"
                        )
                        
                        # Print all returned businesses for verification
                        print("\n📍 RETURNED BUSINESSES:")
                        for i, business in enumerate(businesses, 1):
                            print(f"  {i}. Business ID: {business.get('business_id')}")
                            print(f"     Name: {business.get('name')}")
                            print(f"     Ready Orders: {business.get('pending_ready_count', 0)}")
                            print(f"     Distance: {business.get('distance', 0):.0f}m")
                            print(f"     Address: {business.get('address_short', 'N/A')}")
                            print()
                        
                        return businesses
                    else:
                        self.log_result(
                            "Nearby Businesses Endpoint",
                            False,
                            f"Invalid response format: {type(businesses)}"
                        )
                        return []
                else:
                    error_text = await response.text()
                    self.log_result(
                        "Nearby Businesses Endpoint",
                        False,
                        f"HTTP {response.status}: {error_text}"
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Nearby Businesses Endpoint", False, f"Exception: {str(e)}")
            return []
            
    async def test_business_filtering_logic(self, businesses):
        """Test 3: Business Filtering Logic"""
        try:
            # Check if the expected business exists but is correctly filtered out
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": "testbusiness@example.com", "password": "test123"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    user = data.get('user', {})
                    business_id = user.get('id')
                    has_coordinates = 'lat' in user and 'lng' in user
                    
                    # Check ready orders count
                    async with self.session.get(
                        f"{BACKEND_URL}/business/orders/incoming"
                    ) as orders_response:
                        
                        ready_orders_count = 0
                        if orders_response.status == 200:
                            orders = await orders_response.json()
                            ready_orders_count = len([o for o in orders if o.get('status') == 'ready'])
                        
                        # Determine if business should appear in nearby results
                        should_appear = has_coordinates and ready_orders_count > 0
                        business_found = any(b.get('business_id') == business_id for b in businesses)
                        
                        if should_appear == business_found:
                            self.log_result(
                                "Business Filtering Logic",
                                True,
                                f"Business {business_id} correctly {'included' if business_found else 'excluded'} "
                                f"(has_coords: {has_coordinates}, ready_orders: {ready_orders_count})"
                            )
                            return True
                        else:
                            self.log_result(
                                "Business Filtering Logic",
                                False,
                                f"Business {business_id} filtering error: should_appear={should_appear}, "
                                f"found={business_found} (has_coords: {has_coordinates}, ready_orders: {ready_orders_count})"
                            )
                            return False
                else:
                    self.log_result(
                        "Business Filtering Logic",
                        False,
                        f"Could not verify business data: HTTP {response.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Business Filtering Logic", False, f"Exception: {str(e)}")
            return False
            
    async def test_business_location_data(self, businesses):
        """Test 4: Business Location Data"""
        try:
            businesses_with_location = 0
            businesses_with_distance = 0
            
            for business in businesses:
                location = business.get('location')
                if location and location.get('coordinates'):
                    businesses_with_location += 1
                    
                if business.get('distance') is not None:
                    businesses_with_distance += 1
                    
            success = businesses_with_location > 0 and businesses_with_distance > 0
            
            self.log_result(
                "Business Location Data",
                success,
                f"{businesses_with_location}/{len(businesses)} have location, {businesses_with_distance}/{len(businesses)} have distance"
            )
            
            return success
            
        except Exception as e:
            self.log_result("Business Location Data", False, f"Exception: {str(e)}")
            return False
            
    async def test_pending_ready_count_field(self, businesses):
        """Test 5: Pending Ready Count Field"""
        try:
            businesses_with_count = 0
            total_ready_orders = 0
            
            for business in businesses:
                count = business.get('pending_ready_count')
                if count is not None:
                    businesses_with_count += 1
                    total_ready_orders += count
                    
            success = businesses_with_count == len(businesses)
            
            self.log_result(
                "Pending Ready Count Field",
                success,
                f"{businesses_with_count}/{len(businesses)} have pending_ready_count field, total ready orders: {total_ready_orders}"
            )
            
            return success
            
        except Exception as e:
            self.log_result("Pending Ready Count Field", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🎯 COURIER NEARBY-BUSINESSES ENDPOINT TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Expected Business ID: {EXPECTED_BUSINESS_ID}")
        print(f"Test Coordinates: lat=38.3687, lng=34.0254, radius=50km")
        print()
        
        await self.setup_session()
        
        try:
            # Test 1: Courier Login
            login_success = await self.test_courier_login()
            if not login_success:
                print("\n❌ Cannot proceed without authentication")
                return
                
            # Test 2: Nearby Businesses Endpoint
            businesses = await self.test_nearby_businesses_endpoint()
            if not businesses:
                print("\n❌ No businesses returned - cannot run remaining tests")
                return
                
            # Test 3: Business Filtering Logic
            await self.test_business_filtering_logic(businesses)
            
            # Test 4: Business Location Data
            await self.test_business_location_data(businesses)
            
            # Test 5: Pending Ready Count Field
            await self.test_pending_ready_count_field(businesses)
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
            print("🎉 ALL TESTS PASSED - Courier nearby-businesses endpoint is working correctly!")
            print("✅ Courier authentication working")
            print("✅ Nearby-businesses endpoint returns results (not empty)")
            print("✅ Business filtering logic working correctly")
            print("✅ pending_ready_count field present")
            print("✅ Distance calculation working")
        else:
            print("🚨 SOME TESTS FAILED - Issues identified:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
                    
        return passed == total

async def main():
    """Main test execution"""
    tester = CourierNearbyBusinessesTest()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())