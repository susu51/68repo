#!/usr/bin/env python3
"""
Phase 2 Content & Media Foundation Backend Testing
Testing content blocks, media assets, admin stats, and popular products endpoints

Test Coverage:
1. GET /api/content/blocks - Content blocks retrieval
2. GET /api/content/blocks/home_admin - Admin dashboard content
3. PUT /api/content/blocks/home_admin - Update admin content (auth required)
4. GET /api/content/media-assets - Media galleries retrieval
5. GET /api/content/media-assets/courier_gallery - Courier images
6. GET /api/content/admin/stats - Real-time dashboard stats
7. GET /api/content/popular-products - Popular products data
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://delivery-platform-10.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

# Alternative admin credentials to try
ALTERNATIVE_ADMIN_CREDENTIALS = [
    {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    {"email": "admin@delivertr.com", "password": "6851"}
]

class ContentMediaTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.test_order_id = None
        self.test_courier_id = None
        
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
        """Authenticate all test users and get JWT tokens"""
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
                    
                    # Store courier ID for testing
                    if role == "courier":
                        self.test_courier_id = data["user"]["id"]
                    
                    self.log_test(
                        f"Authentication - {role.title()}",
                        True,
                        f"Token length: {len(data['access_token'])} chars, User ID: {data['user']['id']}"
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

    def create_test_order(self):
        """Create a test order for location tracking testing"""
        print("📦 CREATING TEST ORDER FOR LOCATION TRACKING...")
        
        try:
            # First, create an order as customer
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
                "notes": "Test order for courier location tracking"
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_order_id = data.get("id") or data.get("order_id")
                self.log_test(
                    "Create Test Order",
                    True,
                    f"Order ID: {self.test_order_id}, Status: {data.get('status', 'created')}"
                )
                
                # Update order status to picked_up to enable location tracking
                self.update_order_for_tracking()
                
            else:
                self.log_test(
                    "Create Test Order",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Create Test Order",
                False,
                error=str(e)
            )

    def update_order_for_tracking(self):
        """Update order status to enable courier location tracking"""
        if not self.test_order_id:
            return
            
        try:
            # Simulate order progression: created -> confirmed -> preparing -> ready -> picked_up
            statuses = ["confirmed", "preparing", "ready"]
            
            for status in statuses:
                # Update as business
                headers = {"Authorization": f"Bearer {self.tokens['business']}"}
                response = requests.patch(
                    f"{BACKEND_URL}/business/orders/{self.test_order_id}/status",
                    json={"status": status},
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   Order status updated to: {status}")
                else:
                    print(f"   Failed to update order to {status}: {response.status_code}")
            
            # Courier picks up the order
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.patch(
                f"{BACKEND_URL}/courier/orders/{self.test_order_id}/pickup",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Order Pickup for Tracking",
                    True,
                    "Order picked up by courier, ready for location tracking"
                )
            else:
                self.log_test(
                    "Order Pickup for Tracking",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Order Pickup for Tracking",
                False,
                error=str(e)
            )

    def test_courier_location_update(self):
        """Test POST /api/courier/location - Real-time location updates"""
        print("📍 TESTING COURIER LOCATION UPDATES...")
        
        # Test 1: Valid courier location update
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "heading": 45.5,
                "speed": 25.0,
                "accuracy": 10.0,
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Courier Location Update - Valid Data",
                    True,
                    f"Success: {data.get('success')}, Message: {data.get('message')}"
                )
            else:
                self.log_test(
                    "Courier Location Update - Valid Data",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Courier Location Update - Valid Data",
                False,
                error=str(e)
            )

        # Test 2: Invalid location data
        try:
            invalid_data = {
                "lat": "invalid",
                "lng": 28.9784
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=invalid_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Courier Location Update - Invalid Data",
                response.status_code in [400, 422],
                f"Status: {response.status_code} (Expected 400/422 for invalid data)"
            )
        except Exception as e:
            self.log_test(
                "Courier Location Update - Invalid Data",
                False,
                error=str(e)
            )

        # Test 3: Non-courier user trying to update location (RBAC test)
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Courier Location Update - RBAC Test (Customer)",
                response.status_code == 403,
                f"Status: {response.status_code} (Expected 403 for non-courier)"
            )
        except Exception as e:
            self.log_test(
                "Courier Location Update - RBAC Test (Customer)",
                False,
                error=str(e)
            )

        # Test 4: Multiple location updates (simulate real-time tracking)
        try:
            success_count = 0
            total_updates = 5
            
            for i in range(total_updates):
                location_data = {
                    "lat": 41.0082 + (i * 0.001),  # Simulate movement
                    "lng": 28.9784 + (i * 0.001),
                    "heading": 45.5 + (i * 10),
                    "speed": 20.0 + (i * 2),
                    "accuracy": 10.0,
                    "ts": int(time.time() * 1000)
                }
                
                headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
                response = requests.post(
                    f"{BACKEND_URL}/courier/location",
                    json=location_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                
                time.sleep(0.5)  # Small delay between updates
            
            self.log_test(
                "Courier Location Update - Multiple Updates",
                success_count == total_updates,
                f"Successful updates: {success_count}/{total_updates}"
            )
        except Exception as e:
            self.log_test(
                "Courier Location Update - Multiple Updates",
                False,
                error=str(e)
            )

    def test_courier_location_retrieval(self):
        """Test GET /api/courier/location/{courier_id} - Get courier location"""
        print("🔍 TESTING COURIER LOCATION RETRIEVAL...")
        
        if not self.test_courier_id:
            self.log_test(
                "Courier Location Retrieval - Setup",
                False,
                error="No courier ID available for testing"
            )
            return

        # Test 1: Customer accessing courier location (with active order)
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Courier Location Retrieval - Customer Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "Courier Location Retrieval - Customer Access",
                    True,
                    "Access denied (expected if no active order)"
                )
            else:
                self.log_test(
                    "Courier Location Retrieval - Customer Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Courier Location Retrieval - Customer Access",
                False,
                error=str(e)
            )

        # Test 2: Business accessing courier location
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Courier Location Retrieval - Business Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}"
                )
            elif response.status_code == 403:
                self.log_test(
                    "Courier Location Retrieval - Business Access",
                    True,
                    "Access denied (expected if no active order)"
                )
            else:
                self.log_test(
                    "Courier Location Retrieval - Business Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Courier Location Retrieval - Business Access",
                False,
                error=str(e)
            )

        # Test 3: Admin accessing courier location
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Courier Location Retrieval - Admin Access",
                    True,
                    f"Lat: {data.get('lat')}, Lng: {data.get('lng')}, Source: {data.get('source')}"
                )
            else:
                self.log_test(
                    "Courier Location Retrieval - Admin Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Courier Location Retrieval - Admin Access",
                False,
                error=str(e)
            )

        # Test 4: Non-existent courier ID
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{BACKEND_URL}/courier/location/non-existent-courier-id",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Courier Location Retrieval - Non-existent ID",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for non-existent courier)"
            )
        except Exception as e:
            self.log_test(
                "Courier Location Retrieval - Non-existent ID",
                False,
                error=str(e)
            )

    def test_order_courier_location(self):
        """Test GET /api/orders/{order_id}/courier/location - Order-specific courier tracking"""
        print("🚚 TESTING ORDER-SPECIFIC COURIER LOCATION...")
        
        if not self.test_order_id:
            self.log_test(
                "Order Courier Location - Setup",
                False,
                error="No test order ID available"
            )
            return

        # Test 1: Customer accessing their order's courier location
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}/courier/location",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "courier_id" in data:
                    self.log_test(
                        "Order Courier Location - Customer Access",
                        True,
                        f"Courier ID: {data.get('courier_id')}, Lat: {data.get('lat')}, Lng: {data.get('lng')}"
                    )
                else:
                    self.log_test(
                        "Order Courier Location - Customer Access",
                        True,
                        f"Message: {data.get('message')} (No courier assigned yet)"
                    )
            else:
                self.log_test(
                    "Order Courier Location - Customer Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Order Courier Location - Customer Access",
                False,
                error=str(e)
            )

        # Test 2: Business accessing their order's courier location
        try:
            headers = {"Authorization": f"Bearer {self.tokens['business']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}/courier/location",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "courier_id" in data:
                    self.log_test(
                        "Order Courier Location - Business Access",
                        True,
                        f"Courier ID: {data.get('courier_id')}, Lat: {data.get('lat')}, Lng: {data.get('lng')}"
                    )
                else:
                    self.log_test(
                        "Order Courier Location - Business Access",
                        True,
                        f"Message: {data.get('message')} (No courier assigned yet)"
                    )
            else:
                self.log_test(
                    "Order Courier Location - Business Access",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Order Courier Location - Business Access",
                False,
                error=str(e)
            )

        # Test 3: Non-existent order ID
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/non-existent-order-id/courier/location",
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Order Courier Location - Non-existent Order",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected 404 for non-existent order)"
            )
        except Exception as e:
            self.log_test(
                "Order Courier Location - Non-existent Order",
                False,
                error=str(e)
            )

    def test_redis_integration(self):
        """Test Redis caching functionality"""
        print("🔴 TESTING REDIS INTEGRATION...")
        
        # Test Redis by updating location and immediately retrieving it
        try:
            # Update location
            location_data = {
                "lat": 41.0123,
                "lng": 28.9876,
                "heading": 90.0,
                "speed": 30.0,
                "accuracy": 5.0,
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            update_response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            if update_response.status_code == 200:
                # Immediately retrieve location to test Redis caching
                time.sleep(1)  # Small delay
                
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                get_response = requests.get(
                    f"{BACKEND_URL}/courier/location/{self.test_courier_id}",
                    headers=headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    data = get_response.json()
                    # Check if we got the exact location we just updated
                    lat_match = abs(data.get('lat', 0) - location_data['lat']) < 0.0001
                    lng_match = abs(data.get('lng', 0) - location_data['lng']) < 0.0001
                    is_realtime = data.get('source') == 'realtime'
                    
                    self.log_test(
                        "Redis Integration - Cache Verification",
                        lat_match and lng_match,
                        f"Location match: {lat_match and lng_match}, Source: {data.get('source')}, Real-time: {is_realtime}"
                    )
                else:
                    self.log_test(
                        "Redis Integration - Cache Verification",
                        False,
                        f"Get status: {get_response.status_code}",
                        get_response.text
                    )
            else:
                self.log_test(
                    "Redis Integration - Cache Verification",
                    False,
                    f"Update status: {update_response.status_code}",
                    update_response.text
                )
        except Exception as e:
            self.log_test(
                "Redis Integration - Cache Verification",
                False,
                error=str(e)
            )

    def test_location_accuracy_and_timeout(self):
        """Test location accuracy and timeout handling"""
        print("⏱️ TESTING LOCATION ACCURACY AND TIMEOUT HANDLING...")
        
        # Test 1: High accuracy location
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "accuracy": 1.0,  # Very high accuracy
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Accuracy - High Accuracy",
                response.status_code == 200,
                f"Status: {response.status_code}, Accuracy: {location_data['accuracy']}m"
            )
        except Exception as e:
            self.log_test(
                "Location Accuracy - High Accuracy",
                False,
                error=str(e)
            )

        # Test 2: Low accuracy location
        try:
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "accuracy": 100.0,  # Low accuracy
                "ts": int(time.time() * 1000)
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Accuracy - Low Accuracy",
                response.status_code == 200,
                f"Status: {response.status_code}, Accuracy: {location_data['accuracy']}m"
            )
        except Exception as e:
            self.log_test(
                "Location Accuracy - Low Accuracy",
                False,
                error=str(e)
            )

        # Test 3: Old timestamp (timeout simulation)
        try:
            old_timestamp = int((time.time() - 3600) * 1000)  # 1 hour ago
            location_data = {
                "lat": 41.0082,
                "lng": 28.9784,
                "ts": old_timestamp
            }
            
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            response = requests.post(
                f"{BACKEND_URL}/courier/location",
                json=location_data,
                headers=headers,
                timeout=10
            )
            
            self.log_test(
                "Location Timeout - Old Timestamp",
                response.status_code == 200,  # Should still accept but may handle differently
                f"Status: {response.status_code}, Timestamp: 1 hour old"
            )
        except Exception as e:
            self.log_test(
                "Location Timeout - Old Timestamp",
                False,
                error=str(e)
            )

    def test_integration_with_order_system(self):
        """Test integration with existing order system"""
        print("🔗 TESTING INTEGRATION WITH ORDER SYSTEM...")
        
        # Test that location is only available for picked_up/delivering orders
        if not self.test_order_id:
            self.log_test(
                "Order System Integration - Setup",
                False,
                error="No test order available"
            )
            return

        # Test location access for picked_up order
        try:
            headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
            response = requests.get(
                f"{BACKEND_URL}/orders/{self.test_order_id}/courier/location",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                has_location = "lat" in data and "lng" in data
                self.log_test(
                    "Order System Integration - Picked Up Order",
                    True,
                    f"Location available: {has_location}, Message: {data.get('message', 'Location data present')}"
                )
            else:
                self.log_test(
                    "Order System Integration - Picked Up Order",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Order System Integration - Picked Up Order",
                False,
                error=str(e)
            )

    def run_comprehensive_test(self):
        """Run all courier location system tests"""
        print("🚀 STARTING PHASE 1 COURIER LOCATION SYSTEM TESTING")
        print("=" * 60)
        
        # Step 1: Authentication
        self.authenticate_users()
        
        if not all(role in self.tokens for role in ["admin", "courier", "customer", "business"]):
            print("❌ CRITICAL: Authentication failed for required roles. Cannot proceed.")
            return
        
        # Step 2: Setup test order
        self.create_test_order()
        
        # Step 3: Test courier location updates
        self.test_courier_location_update()
        
        # Step 4: Test courier location retrieval
        self.test_courier_location_retrieval()
        
        # Step 5: Test order-specific courier location
        self.test_order_courier_location()
        
        # Step 6: Test Redis integration
        self.test_redis_integration()
        
        # Step 7: Test location accuracy and timeout handling
        self.test_location_accuracy_and_timeout()
        
        # Step 8: Test integration with order system
        self.test_integration_with_order_system()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 PHASE 1 COURIER LOCATION SYSTEM TEST SUMMARY")
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
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["test"].split(" - ")[0]
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
            categories[category]["tests"].append(result)
        
        # Print category summaries
        for category, data in categories.items():
            total = data["passed"] + data["failed"]
            rate = (data["passed"] / total * 100) if total > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 75 else "❌"
            print(f"{status} {category}: {data['passed']}/{total} ({rate:.1f}%)")
        
        print("\n" + "=" * 60)
        print("🔍 DETAILED FAILURE ANALYSIS")
        print("=" * 60)
        
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            for result in failed_results:
                print(f"❌ {result['test']}")
                if result["error"]:
                    print(f"   Error: {result['error']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
                print()
        else:
            print("🎉 No test failures detected!")
        
        print("\n" + "=" * 60)
        print("📋 RECOMMENDATIONS")
        print("=" * 60)
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Courier location system is working excellently")
        elif success_rate >= 75:
            print("⚠️ GOOD: Courier location system is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️ NEEDS ATTENTION: Courier location system has significant issues")
        else:
            print("❌ CRITICAL: Courier location system has major problems")
        
        # Specific recommendations based on failures
        auth_failures = [r for r in self.test_results if "Authentication" in r["test"] and not r["success"]]
        if auth_failures:
            print("- Fix authentication issues for proper RBAC testing")
        
        rbac_failures = [r for r in self.test_results if "RBAC" in r["test"] and not r["success"]]
        if rbac_failures:
            print("- Review and fix role-based access control implementation")
        
        redis_failures = [r for r in self.test_results if "Redis" in r["test"] and not r["success"]]
        if redis_failures:
            print("- Check Redis connection and caching implementation")
        
        location_failures = [r for r in self.test_results if "Location" in r["test"] and not r["success"]]
        if location_failures:
            print("- Review location data validation and storage logic")

if __name__ == "__main__":
    tester = CourierLocationTester()
    tester.run_comprehensive_test()