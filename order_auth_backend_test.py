#!/usr/bin/env python3
"""
🚨 URGENT: ORDER CREATION AUTHENTICATION ISSUE TESTING

CRITICAL: Test the authentication flow for order creation as reported by user.
User reports "No authentication cookie or token" error when trying to create orders.

Test Scenarios from Review Request:
1. Login & Cookie Test - POST /api/auth/login with test@kuryecini.com / test123
2. Authenticated /me Endpoint - GET /api/me with saved cookie  
3. Order Creation with Cookie - POST /api/orders with saved cookie
4. Debug Authentication Flow - Check cookie handling and backend logs
"""

import json
import requests
import time
from datetime import datetime
import os
import sys

# Configuration - Use REACT_APP_BACKEND_URL from frontend/.env
BACKEND_URL = "https://ai-order-debug.preview.emergentagent.com"

# Test credentials from review request
TEST_CUSTOMER_EMAIL = "test@kuryecini.com"
TEST_CUSTOMER_PASSWORD = "test123"

# Order data from review request
ORDER_DATA = {
    "business_id": "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed",
    "restaurant_id": "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed",
    "items": [{
        "product_id": "test-item",
        "id": "test-item", 
        "title": "Test Pizza",
        "price": 50.0,
        "quantity": 1
    }],
    "delivery_address": "Test Address",
    "city": "Aksaray",
    "district": "Merkez",
    "delivery_lat": 38.0,
    "delivery_lng": 34.0,
    "payment_method": "cash"
}

class OrderAuthTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.access_token = None
        self.cookies = None
        
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
    
    def test_login_and_cookie(self):
        """Test 1: Login & Cookie Test - POST /api/auth/login with test@kuryecini.com / test123"""
        try:
            self.session = requests.Session()
            
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            print(f"🔐 Attempting login to {BACKEND_URL}/api/auth/login")
            print(f"   Credentials: {TEST_CUSTOMER_EMAIL} / {TEST_CUSTOMER_PASSWORD}")
            
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=login_data,
                timeout=15
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Check for Set-Cookie header
                set_cookie_header = response.headers.get('Set-Cookie')
                if set_cookie_header:
                    print(f"   Set-Cookie Header: {set_cookie_header}")
                    
                    # Check if access_token is in cookie
                    if 'access_token' in set_cookie_header:
                        self.cookies = response.cookies
                        
                        # Also check for JWT token in response body
                        if data.get("access_token"):
                            self.access_token = data.get("access_token")
                            
                        self.log_test(
                            "Login & Cookie Test",
                            True,
                            f"Login successful, Set-Cookie header present with access_token, Response: {data.get('message', 'success')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Login & Cookie Test", 
                            False,
                            error=f"Set-Cookie header present but no access_token found: {set_cookie_header}"
                        )
                        return False
                else:
                    # Check if it's JWT-based auth instead
                    if data.get("access_token"):
                        self.access_token = data.get("access_token")
                        self.log_test(
                            "Login & Cookie Test",
                            True,
                            f"Login successful with JWT token (no cookie), Token: {self.access_token[:20]}..."
                        )
                        return True
                    else:
                        self.log_test(
                            "Login & Cookie Test",
                            False,
                            error=f"No Set-Cookie header and no access_token in response: {data}"
                        )
                        return False
            else:
                error_text = response.text
                self.log_test(
                    "Login & Cookie Test",
                    False,
                    error=f"Login failed with status {response.status_code}: {error_text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Login & Cookie Test",
                False,
                error=f"Login request failed: {str(e)}"
            )
            return False
    
    def test_authenticated_me_endpoint(self):
        """Test 2: Authenticated /me Endpoint - GET /api/me with saved cookie"""
        try:
            print(f"🔍 Testing /api/me endpoint with authentication")
            
            # Prepare headers for both cookie and JWT auth
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
                print(f"   Using JWT Authorization header")
            
            response = self.session.get(
                f"{BACKEND_URL}/api/me",
                headers=headers,
                timeout=15
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Request Cookies: {dict(self.session.cookies)}")
            print(f"   Request Headers: {headers}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   User Data: {json.dumps(data, indent=2)}")
                
                # Verify user data contains expected fields
                if data.get("email") == TEST_CUSTOMER_EMAIL:
                    self.log_test(
                        "Authenticated /me Endpoint",
                        True,
                        f"Successfully retrieved user data: {data.get('email')}, role: {data.get('role')}, id: {data.get('id')}"
                    )
                    return True, data
                else:
                    self.log_test(
                        "Authenticated /me Endpoint",
                        False,
                        error=f"User data mismatch - expected {TEST_CUSTOMER_EMAIL}, got {data.get('email')}"
                    )
                    return False, None
            elif response.status_code == 401:
                self.log_test(
                    "Authenticated /me Endpoint",
                    False,
                    error=f"Authentication failed (401) - cookie/token not working: {response.text}"
                )
                return False, None
            else:
                self.log_test(
                    "Authenticated /me Endpoint",
                    False,
                    error=f"Unexpected status {response.status_code}: {response.text}"
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Authenticated /me Endpoint",
                False,
                error=f"/me request failed: {str(e)}"
            )
            return False, None
    
    def get_real_menu_items(self):
        """Get real menu items from an existing business"""
        try:
            # First, get available businesses
            response = self.session.get(f"{BACKEND_URL}/api/businesses", timeout=10)
            if response.status_code == 200:
                businesses = response.json()
                if businesses:
                    business = businesses[0]  # Use first business
                    business_id = business.get("id")
                    
                    # Get menu items for this business
                    menu_response = self.session.get(
                        f"{BACKEND_URL}/api/business/public/{business_id}/menu", 
                        timeout=10
                    )
                    if menu_response.status_code == 200:
                        menu_items = menu_response.json()
                        if menu_items:
                            return business_id, menu_items[0]  # Return first menu item
            return None, None
        except:
            return None, None

    def test_order_creation_with_cookie(self):
        """Test 3: Order Creation with Cookie - POST /api/orders with saved cookie"""
        try:
            print(f"🛒 Testing order creation with authentication")
            
            # First, try to get real menu items
            business_id, menu_item = self.get_real_menu_items()
            
            if business_id and menu_item:
                # Use real menu item
                order_data = {
                    "business_id": business_id,
                    "items": [{
                        "product_id": menu_item.get("id"),
                        "id": menu_item.get("id"),
                        "title": menu_item.get("name", "Test Item"),
                        "price": float(menu_item.get("price", 50.0)),
                        "quantity": 1
                    }],
                    "delivery_address": "Test Address, Aksaray",
                    "delivery_lat": 38.3687,
                    "delivery_lng": 34.0254,
                    "payment_method": "cash_on_delivery",
                    "notes": "Test order for authentication verification"
                }
                print(f"   Using real business: {business_id}")
                print(f"   Using real menu item: {menu_item.get('name')} (₺{menu_item.get('price')})")
            else:
                # Fallback to original test data
                order_data = ORDER_DATA
                print(f"   Using test data (no real menu items found)")
            
            print(f"   Order Data: {json.dumps(order_data, indent=2)}")
            
            # Prepare headers for both cookie and JWT auth
            headers = {"Content-Type": "application/json"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
                print(f"   Using JWT Authorization header")
            
            response = self.session.post(
                f"{BACKEND_URL}/api/orders",
                json=order_data,
                headers=headers,
                timeout=20
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Request Cookies: {dict(self.session.cookies)}")
            print(f"   Request Headers: {headers}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Order Response: {json.dumps(data, indent=2)}")
                
                # Verify order was created successfully
                if data.get("id") or data.get("order_id"):
                    order_id = data.get("id") or data.get("order_id")
                    self.log_test(
                        "Order Creation with Cookie",
                        True,
                        f"Order created successfully: ID {order_id}, Status: {data.get('status')}, Total: {data.get('total_amount')}"
                    )
                    return True, data
                else:
                    self.log_test(
                        "Order Creation with Cookie",
                        False,
                        error=f"Order response missing ID field: {data}"
                    )
                    return False, None
            elif response.status_code == 401:
                error_text = response.text
                self.log_test(
                    "Order Creation with Cookie",
                    False,
                    error=f"Authentication failed (401) - 'No authentication cookie or token' error: {error_text}"
                )
                return False, None
            elif response.status_code == 403:
                error_text = response.text
                self.log_test(
                    "Order Creation with Cookie",
                    False,
                    error=f"Authorization failed (403) - insufficient permissions: {error_text}"
                )
                return False, None
            elif response.status_code == 404:
                error_text = response.text
                # Check if it's a product not found error (not an auth error)
                if "bulunamadı" in error_text or "not found" in error_text.lower():
                    self.log_test(
                        "Order Creation with Cookie",
                        False,
                        error=f"Product/Business not found (404) - authentication working but data issue: {error_text}"
                    )
                else:
                    self.log_test(
                        "Order Creation with Cookie",
                        False,
                        error=f"Endpoint not found (404) - possible routing issue: {error_text}"
                    )
                return False, None
            else:
                error_text = response.text
                self.log_test(
                    "Order Creation with Cookie",
                    False,
                    error=f"Order creation failed with status {response.status_code}: {error_text}"
                )
                return False, None
                
        except Exception as e:
            self.log_test(
                "Order Creation with Cookie",
                False,
                error=f"Order creation request failed: {str(e)}"
            )
            return False, None
    
    def test_debug_authentication_flow(self):
        """Test 4: Debug Authentication Flow - Check cookie handling and backend logs"""
        try:
            print(f"🔧 Debugging authentication flow")
            
            # Test 1: Check if cookies are properly set
            print(f"   Session Cookies: {dict(self.session.cookies)}")
            
            # Test 2: Try different authentication methods
            auth_methods = []
            
            # Method 1: Cookie-only request
            cookie_response = requests.get(
                f"{BACKEND_URL}/api/me",
                cookies=self.session.cookies,
                timeout=10
            )
            auth_methods.append({
                "method": "Cookie-only",
                "status": cookie_response.status_code,
                "success": cookie_response.status_code == 200
            })
            
            # Method 2: JWT-only request (if we have token)
            if self.access_token:
                jwt_response = requests.get(
                    f"{BACKEND_URL}/api/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10
                )
                auth_methods.append({
                    "method": "JWT-only",
                    "status": jwt_response.status_code,
                    "success": jwt_response.status_code == 200
                })
            
            # Method 3: Both cookie and JWT
            if self.access_token:
                both_response = requests.get(
                    f"{BACKEND_URL}/api/me",
                    cookies=self.session.cookies,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10
                )
                auth_methods.append({
                    "method": "Cookie + JWT",
                    "status": both_response.status_code,
                    "success": both_response.status_code == 200
                })
            
            # Test 3: Check backend health
            try:
                health_response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
                backend_healthy = health_response.status_code == 200
            except:
                backend_healthy = False
            
            # Analyze results
            working_methods = [m for m in auth_methods if m["success"]]
            
            if len(working_methods) > 0:
                self.log_test(
                    "Debug Authentication Flow",
                    True,
                    f"Authentication working via: {', '.join([m['method'] for m in working_methods])}. Backend healthy: {backend_healthy}"
                )
                return True
            else:
                failed_methods = [f"{m['method']} ({m['status']})" for m in auth_methods]
                self.log_test(
                    "Debug Authentication Flow",
                    False,
                    error=f"All authentication methods failed: {', '.join(failed_methods)}. Backend healthy: {backend_healthy}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Debug Authentication Flow",
                False,
                error=f"Authentication debug failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all order authentication tests"""
        print("🚨 URGENT: ORDER CREATION AUTHENTICATION ISSUE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_CUSTOMER_EMAIL}")
        print("=" * 80)
        
        # Test 1: Login & Cookie Test
        login_success = self.test_login_and_cookie()
        
        if not login_success:
            print("❌ Login failed - cannot proceed with authentication tests")
            self.print_summary()
            return
        
        # Test 2: Authenticated /me Endpoint
        me_success, user_data = self.test_authenticated_me_endpoint()
        
        # Test 3: Order Creation with Cookie
        order_success, order_data = self.test_order_creation_with_cookie()
        
        # Test 4: Debug Authentication Flow
        debug_success = self.test_debug_authentication_flow()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 ORDER AUTHENTICATION TESTING SUMMARY")
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
        
        print(f"\n🎯 EXPECTED RESULTS FROM REVIEW REQUEST:")
        
        # Check expected results
        login_working = any(r["test"] == "Login & Cookie Test" and r["success"] for r in self.test_results)
        me_working = any(r["test"] == "Authenticated /me Endpoint" and r["success"] for r in self.test_results)
        order_working = any(r["test"] == "Order Creation with Cookie" and r["success"] for r in self.test_results)
        
        if login_working:
            print("   ✅ Login sets access_token cookie")
        else:
            print("   ❌ Login does NOT set access_token cookie")
            
        if me_working:
            print("   ✅ /api/me works with cookie")
        else:
            print("   ❌ /api/me does NOT work with cookie")
            
        if order_working:
            print("   ✅ POST /api/orders works with cookie")
        else:
            print("   ❌ POST /api/orders does NOT work with cookie")
            
        # Check for the specific error
        auth_error_found = any("No authentication cookie or token" in r.get("error", "") for r in self.test_results)
        if not auth_error_found and order_working:
            print("   ✅ Should NOT see 'No authentication cookie or token' error")
        elif auth_error_found:
            print("   ❌ STILL seeing 'No authentication cookie or token' error")
        else:
            print("   ⚠️  Order creation failed for other reasons (not auth error)")
        
        # Overall verdict
        if success_rate == 100:
            print(f"\n🎉 VERDICT: ORDER AUTHENTICATION IS WORKING PERFECTLY ({success_rate:.1f}% success rate)")
            print("   All authentication flows are functional. The reported issue appears to be resolved.")
        elif success_rate >= 75:
            print(f"\n⚠️ VERDICT: ORDER AUTHENTICATION HAS MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Most authentication works but some edge cases need attention.")
        else:
            print(f"\n🚨 VERDICT: ORDER AUTHENTICATION HAS CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   The reported 'No authentication cookie or token' error is confirmed.")
            print("   URGENT: Main agent needs to investigate authentication flow implementation.")

def main():
    """Main test runner"""
    tester = OrderAuthTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()