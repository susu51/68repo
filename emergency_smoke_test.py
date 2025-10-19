#!/usr/bin/env python3
"""
EMERGENCY SMOKE TESTS - System Stability Check

Critical backend API tests to verify system stability for basic operations:
1. Restaurant Discovery (GET /api/restaurants)
2. Restaurant Discovery with GPS Coordinates
3. Business Orders Listing (Authentication + Orders)
4. Customer Order Creation (Full Flow)
5. Admin System Status

Focus: Confirm system is stable for basic operations!
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com"

# Test credentials
BUSINESS_CREDENTIALS = [
    {"email": "testbusiness@example.com", "password": "test123"},
    {"email": "business@kuryecini.com", "password": "business123"}
]

CUSTOMER_CREDENTIALS = {"email": "test@kuryecini.com", "password": "test123"}

class EmergencySmokeTest:
    def __init__(self):
        self.test_results = []
        self.business_token = None
        self.customer_token = None
        self.business_session = requests.Session()
        self.customer_session = requests.Session()
        
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
    
    def test_1_restaurant_discovery(self):
        """Test 1: Restaurant Discovery - GET /api/restaurants (no params)"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/restaurants", timeout=10)
            
            if response.status_code == 200:
                restaurants = response.json()
                
                if isinstance(restaurants, list) and len(restaurants) >= 1:
                    # Check first restaurant for required fields
                    restaurant = restaurants[0]
                    
                    # Check required fields
                    has_name = "name" in restaurant or "business_name" in restaurant
                    has_coords = ("lat" in restaurant and "lng" in restaurant) or \
                                ("location" in restaurant and restaurant.get("location", {}).get("coordinates"))
                    has_delivery_fee = "delivery_fee" in restaurant or "min_order_amount" in restaurant or "min_order" in restaurant
                    is_open_field = "is_open" in restaurant or "is_active" in restaurant
                    
                    if has_name and has_coords and has_delivery_fee:
                        # Get coordinates for display
                        if "lat" in restaurant and "lng" in restaurant:
                            coords_display = f"({restaurant.get('lat')}, {restaurant.get('lng')})"
                        elif restaurant.get("location", {}).get("coordinates"):
                            coords = restaurant["location"]["coordinates"]
                            coords_display = f"({coords[1]}, {coords[0]})"  # GeoJSON is [lng, lat]
                        else:
                            coords_display = "N/A"
                        
                        self.log_test(
                            "Restaurant Discovery (No Params)",
                            True,
                            f"Found {len(restaurants)} restaurants. Sample: {restaurant.get('name', restaurant.get('business_name'))}, coords: {coords_display}, is_open: {restaurant.get('is_open', restaurant.get('is_active'))}"
                        )
                        return True
                    else:
                        missing_fields = []
                        if not has_name: missing_fields.append("name/business_name")
                        if not has_coords: missing_fields.append("lat/lng/location.coordinates")
                        if not has_delivery_fee: missing_fields.append("delivery_fee/min_order_amount/min_order")
                        
                        self.log_test(
                            "Restaurant Discovery (No Params)",
                            False,
                            error=f"Missing required fields: {', '.join(missing_fields)}"
                        )
                        return False
                else:
                    self.log_test(
                        "Restaurant Discovery (No Params)",
                        False,
                        error=f"Expected array with ≥1 restaurant, got: {type(restaurants)} with {len(restaurants) if isinstance(restaurants, list) else 'N/A'} items"
                    )
                    return False
            else:
                self.log_test(
                    "Restaurant Discovery (No Params)",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Restaurant Discovery (No Params)", False, error=f"Request failed: {str(e)}")
            return False
    
    def test_2_restaurant_discovery_with_coords(self):
        """Test 2: Restaurant Discovery with Coordinates"""
        try:
            # Test coordinates for Aksaray, Turkey
            lat, lng = 38.3687, 34.0254
            response = requests.get(
                f"{BACKEND_URL}/api/restaurants?lat={lat}&lng={lng}",
                timeout=10
            )
            
            if response.status_code == 200:
                restaurants = response.json()
                
                if isinstance(restaurants, list):
                    if len(restaurants) > 0:
                        # Check if restaurants have distance field (sorted by distance)
                        restaurant = restaurants[0]
                        has_distance = "distance_m" in restaurant or "distance" in restaurant
                        
                        if has_distance:
                            distance_value = restaurant.get("distance_m", restaurant.get("distance"))
                            self.log_test(
                                "Restaurant Discovery with Coords",
                                True,
                                f"Found {len(restaurants)} restaurants sorted by distance. Closest: {restaurant.get('name', restaurant.get('business_name'))} at {distance_value}m"
                            )
                            return True
                        else:
                            self.log_test(
                                "Restaurant Discovery with Coords",
                                True,
                                f"Found {len(restaurants)} restaurants (distance field not present but query successful)"
                            )
                            return True
                    else:
                        self.log_test(
                            "Restaurant Discovery with Coords",
                            True,
                            "No restaurants found in area (valid response for remote coordinates)"
                        )
                        return True
                else:
                    self.log_test(
                        "Restaurant Discovery with Coords",
                        False,
                        error=f"Expected array, got: {type(restaurants)}"
                    )
                    return False
            else:
                self.log_test(
                    "Restaurant Discovery with Coords",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Restaurant Discovery with Coords", False, error=f"Request failed: {str(e)}")
            return False
    
    def authenticate_business(self):
        """Authenticate business user"""
        for credentials in BUSINESS_CREDENTIALS:
            try:
                response = self.business_session.post(
                    f"{BACKEND_URL}/api/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for cookie-based auth (success field) or JWT auth (access_token field)
                    if data.get("success"):
                        user_role = data.get("user", {}).get("role")
                        if user_role == "business":
                            self.log_test(
                                "Business Authentication",
                                True,
                                f"Business login successful (cookie-based): {credentials['email']}"
                            )
                            return True, None  # Cookie-based, no token needed
                    elif data.get("access_token"):
                        self.business_token = data.get("access_token")
                        user_role = data.get("user", {}).get("role")
                        if user_role == "business":
                            self.log_test(
                                "Business Authentication",
                                True,
                                f"Business login successful (JWT): {credentials['email']}"
                            )
                            return True, self.business_token
                    
                    print(f"   Tried {credentials['email']}: Wrong role ({data.get('user', {}).get('role')})")
                else:
                    print(f"   Tried {credentials['email']}: {response.status_code}")
                    
            except Exception as e:
                print(f"   Tried {credentials['email']}: Error - {str(e)}")
        
        self.log_test("Business Authentication", False, error="All business credential attempts failed")
        return False, None
    
    def test_3_business_orders_listing(self):
        """Test 3: Business Orders Listing"""
        # First authenticate
        auth_success, token = self.authenticate_business()
        if not auth_success:
            return False
        
        try:
            # Prepare headers if we have a token
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Test business orders endpoint using the authenticated session
            response = self.business_session.get(
                f"{BACKEND_URL}/api/business/orders/incoming",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                orders = response.json()
                
                if isinstance(orders, list):
                    self.log_test(
                        "Business Orders Listing",
                        True,
                        f"Successfully retrieved {len(orders)} incoming orders (empty array is valid)"
                    )
                    return True
                else:
                    self.log_test(
                        "Business Orders Listing",
                        False,
                        error=f"Expected array, got: {type(orders)}"
                    )
                    return False
            elif response.status_code == 500:
                self.log_test(
                    "Business Orders Listing",
                    False,
                    error=f"CRITICAL: 500 Internal Server Error - {response.text[:200]}"
                )
                return False
            else:
                self.log_test(
                    "Business Orders Listing",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Business Orders Listing", False, error=f"Request failed: {str(e)}")
            return False
    
    def authenticate_customer(self):
        """Authenticate customer user"""
        try:
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for cookie-based auth or JWT auth
                if data.get("success"):
                    user_role = data.get("user", {}).get("role")
                    if user_role == "customer":
                        self.log_test(
                            "Customer Authentication",
                            True,
                            f"Customer login successful (cookie-based): {CUSTOMER_CREDENTIALS['email']}"
                        )
                        return True, None
                elif data.get("access_token"):
                    self.customer_token = data.get("access_token")
                    user_role = data.get("user", {}).get("role")
                    if user_role == "customer":
                        self.log_test(
                            "Customer Authentication",
                            True,
                            f"Customer login successful (JWT): {CUSTOMER_CREDENTIALS['email']}"
                        )
                        return True, self.customer_token
                
                self.log_test("Customer Authentication", False, error=f"Wrong role: {data.get('user', {}).get('role')}")
                return False, None
            else:
                self.log_test("Customer Authentication", False, error=f"Login failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Customer Authentication", False, error=f"Authentication error: {str(e)}")
            return False, None
    
    def get_available_business_and_menu(self):
        """Get available business with menu items"""
        try:
            # Get businesses
            response = requests.get(f"{BACKEND_URL}/api/businesses", timeout=10)
            
            if response.status_code != 200:
                return None, None
            
            businesses = response.json()
            if not businesses or len(businesses) == 0:
                return None, None
            
            # Try to find a business with menu items
            for business in businesses[:3]:  # Check first 3 businesses
                business_id = business.get("id")
                if not business_id:
                    continue
                
                # Try to get menu items
                menu_response = requests.get(
                    f"{BACKEND_URL}/api/business/public/{business_id}/menu",
                    timeout=10
                )
                
                if menu_response.status_code == 200:
                    menu_items = menu_response.json()
                    if menu_items and len(menu_items) > 0:
                        return business, menu_items[0]  # Return first menu item
            
            return businesses[0], None  # Return first business even without menu
            
        except Exception as e:
            print(f"Error getting business/menu: {str(e)}")
            return None, None
    
    def test_4_customer_order_creation(self):
        """Test 4: Customer Order Creation"""
        # First authenticate
        auth_success, token = self.authenticate_customer()
        if not auth_success:
            return False
        
        # Get available business and menu
        business, menu_item = self.get_available_business_and_menu()
        if not business:
            self.log_test("Customer Order Creation", False, error="No businesses available for order creation")
            return False
        
        try:
            # Prepare order data
            business_id = business.get("id")
            
            if menu_item:
                # Use real menu item
                order_data = {
                    "business_id": business_id,
                    "delivery_address": "Test Delivery Address, Aksaray Merkez",
                    "delivery_lat": 38.3687,
                    "delivery_lng": 34.0254,
                    "items": [{
                        "product_id": menu_item.get("id"),
                        "title": menu_item.get("name", menu_item.get("title", "Test Item")),
                        "price": menu_item.get("price", 50.0),
                        "quantity": 1
                    }],
                    "payment_method": "cash_on_delivery",
                    "notes": "Emergency smoke test order"
                }
                total_amount = menu_item.get("price", 50.0)
            else:
                # Use mock data if no menu available
                order_data = {
                    "business_id": business_id,
                    "delivery_address": "Test Delivery Address, Aksaray Merkez", 
                    "delivery_lat": 38.3687,
                    "delivery_lng": 34.0254,
                    "items": [{
                        "product_id": "test-product-id",
                        "title": "Test Menu Item",
                        "price": 50.0,
                        "quantity": 1
                    }],
                    "payment_method": "cash_on_delivery",
                    "notes": "Emergency smoke test order (mock item)"
                }
                total_amount = 50.0
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Create order using the authenticated session
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Handle both direct order response and wrapped response
                if data.get("success") and data.get("order"):
                    order = data.get("order")
                else:
                    order = data
                
                order_id = order.get("order_id", order.get("id"))
                
                # Check if business_id is populated
                order_business_id = order.get("business_id")
                
                if order_id and order_business_id:
                    self.log_test(
                        "Customer Order Creation",
                        True,
                        f"Order created successfully: ID={order_id}, business_id={order_business_id}, total=₺{total_amount}"
                    )
                    return True
                else:
                    self.log_test(
                        "Customer Order Creation",
                        False,
                        error=f"Order created but missing required fields: order_id={order_id}, business_id={order_business_id}"
                    )
                    return False
            else:
                self.log_test(
                    "Customer Order Creation",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:300]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Customer Order Creation", False, error=f"Request failed: {str(e)}")
            return False
    
    def test_5_admin_system_status(self):
        """Test 5: Admin System Status"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/admin/system/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                self.log_test(
                    "Admin System Status",
                    True,
                    f"Admin system status accessible: {json.dumps(status_data, indent=2)[:200]}..."
                )
                return True
            elif response.status_code == 404:
                # Try alternative health endpoints
                health_endpoints = [
                    f"{BACKEND_URL}/api/health",
                    f"{BACKEND_URL}/healthz",
                    f"{BACKEND_URL}/health"
                ]
                
                for endpoint in health_endpoints:
                    try:
                        health_response = requests.get(endpoint, timeout=10)
                        if health_response.status_code == 200:
                            self.log_test(
                                "Admin System Status",
                                True,
                                f"Alternative health endpoint working: {endpoint}"
                            )
                            return True
                    except:
                        continue
                
                self.log_test(
                    "Admin System Status",
                    False,
                    error="Admin system status endpoint not found (404) and no alternative health endpoints working"
                )
                return False
            else:
                self.log_test(
                    "Admin System Status",
                    False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin System Status", False, error=f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all emergency smoke tests"""
        print("🚨 EMERGENCY SMOKE TESTS - System Stability Check")
        print("=" * 60)
        print("GOAL: Confirm system is stable for basic operations!")
        print()
        
        # Run all tests
        test_1_result = self.test_1_restaurant_discovery()
        test_2_result = self.test_2_restaurant_discovery_with_coords()
        test_3_result = self.test_3_business_orders_listing()
        test_4_result = self.test_4_customer_order_creation()
        test_5_result = self.test_5_admin_system_status()
        
        # Print summary
        self.print_summary()
        
        return all([test_1_result, test_2_result, test_3_result, test_4_result, test_5_result])
    
    def print_summary(self):
        """Print emergency test summary"""
        print("\n" + "=" * 60)
        print("📊 EMERGENCY SMOKE TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        # Check which endpoints return 200
        endpoints_200 = []
        restaurants_visible = False
        business_orders_accessible = False
        critical_errors = []
        
        for result in self.test_results:
            if result["success"]:
                if "Restaurant Discovery" in result["test"]:
                    endpoints_200.append("/api/restaurants")
                    restaurants_visible = True
                elif "Business Orders" in result["test"]:
                    endpoints_200.append("/api/business/orders/incoming")
                    business_orders_accessible = True
                elif "Customer Order Creation" in result["test"]:
                    endpoints_200.append("/api/orders")
                elif "Admin System Status" in result["test"]:
                    endpoints_200.append("/api/admin/system/status")
            else:
                if "500" in result["error"] or "Internal Server Error" in result["error"]:
                    critical_errors.append(f"{result['test']}: {result['error']}")
        
        print(f"   • Endpoints returning 200: {', '.join(set(endpoints_200)) if endpoints_200 else 'None'}")
        print(f"   • Are restaurants visible? {'✅ YES' if restaurants_visible else '❌ NO'}")
        print(f"   • Are business orders accessible? {'✅ YES' if business_orders_accessible else '❌ NO'}")
        
        if critical_errors:
            print(f"   • Critical errors found:")
            for error in critical_errors:
                print(f"     - {error}")
        else:
            print(f"   • Critical errors: ✅ None found")
        
        # Overall system stability verdict
        if success_rate >= 80:
            print(f"\n🎉 SYSTEM STATUS: STABLE - Ready for basic operations ({success_rate:.1f}% success)")
        elif success_rate >= 60:
            print(f"\n⚠️ SYSTEM STATUS: DEGRADED - Some issues detected ({success_rate:.1f}% success)")
        else:
            print(f"\n🚨 SYSTEM STATUS: CRITICAL - Major stability issues ({success_rate:.1f}% success)")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")

def main():
    """Main test runner"""
    tester = EmergencySmokeTest()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()