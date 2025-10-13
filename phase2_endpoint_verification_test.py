#!/usr/bin/env python3
"""
PHASE 2 ENDPOINT VERIFICATION TEST
Simple test to verify which Phase 2 endpoints are implemented and accessible.
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://quickship-49.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"}
}

class EndpointVerificationTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_users(self):
        """Authenticate test users"""
        print("🔐 AUTHENTICATING TEST USERS...")
        
        for role, credentials in TEST_CREDENTIALS.items():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json=credentials,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, Role: {data['user'].get('role', 'unknown')}"
                    )
                else:
                    self.log_test(
                        f"Authentication - {role.title()}",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Authentication - {role.title()}",
                    False,
                    error=str(e)
                )

    def test_endpoint_accessibility(self):
        """Test if Phase 2 endpoints are accessible"""
        print("🔍 TESTING PHASE 2 ENDPOINT ACCESSIBILITY...")
        
        # Define endpoints to test
        endpoints_to_test = [
            # Business Menu CRUD
            ("GET", "/business/menu", "business", "Business Menu - Get Items"),
            ("POST", "/business/menu", "business", "Business Menu - Create Item"),
            
            # Geospatial Discovery
            ("GET", "/nearby/businesses", "customer", "Nearby Businesses - Discovery"),
            
            # Customer Orders
            ("GET", "/orders/my", "customer", "Customer Orders - Get My Orders"),
            ("POST", "/orders", "customer", "Customer Orders - Create Order"),
        ]
        
        for method, endpoint, required_role, test_name in endpoints_to_test:
            if required_role not in self.tokens:
                self.log_test(
                    test_name,
                    False,
                    error=f"No {required_role} token available"
                )
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[required_role]}"}
            
            try:
                if method == "GET":
                    if endpoint == "/nearby/businesses":
                        # Add required parameters for nearby businesses
                        response = requests.get(
                            f"{BACKEND_URL}{endpoint}",
                            params={"lat": 41.0082, "lng": 28.9784},
                            headers=headers,
                            timeout=10
                        )
                    else:
                        response = requests.get(
                            f"{BACKEND_URL}{endpoint}",
                            headers=headers,
                            timeout=10
                        )
                elif method == "POST":
                    if endpoint == "/business/menu":
                        # Test data for menu item creation
                        test_data = {
                            "title": "Test Menu Item",
                            "description": "Test description",
                            "price": 25.0,
                            "category": "Test Category"
                        }
                    elif endpoint == "/orders":
                        # Test data for order creation
                        test_data = {
                            "business_id": "test-business-id",
                            "items": [
                                {
                                    "product_id": "test-product-id",
                                    "title": "Test Product",
                                    "price": 25.0,
                                    "quantity": 1
                                }
                            ],
                            "delivery_address": {
                                "label": "Test Address",
                                "address": "Test Street, Istanbul",
                                "lat": 41.0082,
                                "lng": 28.9784
                            }
                        }
                    else:
                        test_data = {}
                    
                    response = requests.post(
                        f"{BACKEND_URL}{endpoint}",
                        json=test_data,
                        headers=headers,
                        timeout=10
                    )
                
                # Analyze response
                if response.status_code == 401:
                    self.log_test(
                        test_name,
                        False,
                        f"Status: {response.status_code} - Authentication issue",
                        "Endpoint exists but authentication is failing"
                    )
                elif response.status_code == 404:
                    self.log_test(
                        test_name,
                        False,
                        f"Status: {response.status_code} - Endpoint not found",
                        "Endpoint not implemented"
                    )
                elif response.status_code == 403:
                    self.log_test(
                        test_name,
                        True,  # This means endpoint exists and RBAC is working
                        f"Status: {response.status_code} - Access denied (RBAC working)",
                        "Endpoint implemented with proper access control"
                    )
                elif response.status_code in [200, 201]:
                    self.log_test(
                        test_name,
                        True,
                        f"Status: {response.status_code} - Success",
                        "Endpoint working correctly"
                    )
                elif response.status_code in [400, 422]:
                    self.log_test(
                        test_name,
                        True,  # Validation errors mean endpoint exists
                        f"Status: {response.status_code} - Validation error",
                        "Endpoint exists but requires valid data"
                    )
                elif response.status_code == 500:
                    self.log_test(
                        test_name,
                        False,
                        f"Status: {response.status_code} - Server error",
                        response.text[:200] if response.text else "Internal server error"
                    )
                else:
                    self.log_test(
                        test_name,
                        False,
                        f"Status: {response.status_code} - Unexpected response",
                        response.text[:200] if response.text else "Unknown error"
                    )
                    
            except Exception as e:
                self.log_test(
                    test_name,
                    False,
                    error=str(e)
                )

    def test_existing_working_endpoints(self):
        """Test endpoints that are known to work from previous tests"""
        print("✅ TESTING KNOWN WORKING ENDPOINTS...")
        
        if "customer" not in self.tokens:
            print("No customer token available for testing")
            return
            
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test existing order endpoints that worked in previous test
        try:
            # Test order creation (this worked before)
            order_data = {
                "delivery_address": "Test Address, Istanbul",
                "delivery_lat": 41.0082,
                "delivery_lng": 28.9784,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Pizza",
                        "product_price": 45.0,
                        "quantity": 1,
                        "subtotal": 45.0
                    }
                ],
                "total_amount": 45.0,
                "notes": "Test order"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                order_id = data.get("id") or data.get("order_id")
                self.log_test(
                    "Existing Order Creation",
                    True,
                    f"Order created successfully: {order_id}"
                )
                
                # Test order tracking
                if order_id:
                    track_response = requests.get(
                        f"{BACKEND_URL}/orders/{order_id}/track",
                        headers=headers,
                        timeout=10
                    )
                    
                    self.log_test(
                        "Existing Order Tracking",
                        track_response.status_code == 200,
                        f"Tracking status: {track_response.status_code}"
                    )
            else:
                self.log_test(
                    "Existing Order Creation",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                
            # Test get my orders
            my_orders_response = requests.get(
                f"{BACKEND_URL}/orders/my",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Existing Get My Orders",
                my_orders_response.status_code == 200,
                f"Status: {my_orders_response.status_code}"
            )
            
        except Exception as e:
            self.log_test(
                "Existing Endpoints Test",
                False,
                error=str(e)
            )

    def run_verification_test(self):
        """Run endpoint verification tests"""
        print("🚀 STARTING PHASE 2 ENDPOINT VERIFICATION")
        print("=" * 60)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        # Step 2: Test endpoint accessibility
        self.test_endpoint_accessibility()
        
        # Step 3: Test known working endpoints
        self.test_existing_working_endpoints()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 ENDPOINT VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Categorize results
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"]]
        endpoint_tests = [r for r in self.test_results if "Authentication" not in r["test"]]
        
        auth_success = sum(1 for r in auth_tests if r["success"])
        endpoint_success = sum(1 for r in endpoint_tests if r["success"])
        
        print(f"🔐 Authentication: {auth_success}/{len(auth_tests)} ({auth_success/len(auth_tests)*100:.1f}%)")
        print(f"🔗 Endpoints: {endpoint_success}/{len(endpoint_tests)} ({endpoint_success/len(endpoint_tests)*100:.1f}%)")
        
        print("\n" + "=" * 60)
        print("🔍 IMPLEMENTATION STATUS")
        print("=" * 60)
        
        # Analyze endpoint implementation status
        business_menu_tests = [r for r in self.test_results if "Business Menu" in r["test"]]
        nearby_tests = [r for r in self.test_results if "Nearby" in r["test"]]
        order_tests = [r for r in self.test_results if "Order" in r["test"]]
        
        print(f"🍽️ Business Menu CRUD: {sum(1 for r in business_menu_tests if r['success'])}/{len(business_menu_tests)} working")
        print(f"📍 Nearby Businesses: {sum(1 for r in nearby_tests if r['success'])}/{len(nearby_tests)} working")
        print(f"📦 Customer Orders: {sum(1 for r in order_tests if r['success'])}/{len(order_tests)} working")
        
        print("\n" + "=" * 60)
        print("🎯 FINDINGS")
        print("=" * 60)
        
        # Detailed findings
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print("❌ ISSUES FOUND:")
            for result in failed_results:
                print(f"   • {result['test']}: {result.get('error', result.get('details', 'Unknown issue'))}")
        
        working_results = [r for r in self.test_results if r["success"] and "working correctly" in r.get("error", "")]
        if working_results:
            print("\n✅ WORKING ENDPOINTS:")
            for result in working_results:
                print(f"   • {result['test']}")

if __name__ == "__main__":
    tester = EndpointVerificationTester()
    tester.run_verification_test()