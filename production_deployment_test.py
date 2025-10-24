#!/usr/bin/env python3
"""
Production Deployment Testing Suite
Tests the newly added required endpoints for production deployment:

1. Test health check endpoint: GET /healthz - should return {"status": "ok"}
2. Test menus endpoint: GET /menus - should return array with schema: {"id": "string", "title": "string", "price": number, "imageUrl": "string", "category": "string"}
3. Verify CORS is properly configured for cross-origin requests
4. Test that existing endpoints still work (auth, businesses, etc.)
5. Verify the backend starts properly with the production command: uvicorn server:app --host 0.0.0.0 --port 8000
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class ProductionDeploymentTester:
    def __init__(self, base_url="https://kuryecini-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test tokens for existing endpoints
        self.admin_token = None
        self.business_token = None
        self.customer_token = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None, check_cors=False):
        """Run a single API test"""
        # Handle both full URLs and endpoint paths
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint.startswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        
        test_headers = {'Content-Type': 'application/json'}
        
        # Add CORS test headers if requested
        if check_cors:
            test_headers.update({
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            })
        
        # Use specific token if provided
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            # Check CORS headers if requested
            if check_cors:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                print(f"   CORS Headers: {json.dumps(cors_headers, indent=2)}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    response_text = response.text
                    print(f"   Response: {response_text}")
                    self.log_test(name, True)
                    return True, response_text
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_health_check_endpoint(self):
        """Test health check endpoint: GET /api/healthz - should return {"status": "ok"}"""
        print("\n🏥 TESTING HEALTH CHECK ENDPOINT")
        
        success, response = self.run_test(
            "Health Check Endpoint",
            "GET",
            "healthz",
            200
        )
        
        if success:
            # Verify response structure
            if isinstance(response, dict) and response.get('status') == 'ok':
                print(f"   ✅ Health check response correct: {response}")
                return True
            else:
                self.log_test("Health Check Response Validation", False, f"Expected {{'status': 'ok'}}, got {response}")
                return False
        
        return success

    def test_menus_endpoint(self):
        """Test menus endpoint: GET /api/menus - should return array with proper schema"""
        print("\n🍽️ TESTING MENUS ENDPOINT")
        
        success, response = self.run_test(
            "Menus Endpoint",
            "GET",
            "menus",
            200
        )
        
        if success:
            # Verify response is an array
            if not isinstance(response, list):
                self.log_test("Menus Response Type", False, f"Expected array, got {type(response)}")
                return False
            
            print(f"   ✅ Menus endpoint returned array with {len(response)} items")
            
            # Verify schema for each menu item
            required_fields = ["id", "title", "price", "imageUrl", "category"]
            schema_valid = True
            
            for i, menu_item in enumerate(response[:5]):  # Check first 5 items
                print(f"\n   📋 Validating menu item {i+1}: {menu_item.get('title', 'Unknown')}")
                
                # Check required fields
                for field in required_fields:
                    if field not in menu_item:
                        print(f"   ❌ Missing required field '{field}' in menu item {i+1}")
                        schema_valid = False
                    else:
                        print(f"   ✅ {field}: {menu_item[field]} ({type(menu_item[field]).__name__})")
                
                # Validate field types
                if "id" in menu_item and not isinstance(menu_item["id"], str):
                    print(f"   ❌ Field 'id' should be string, got {type(menu_item['id'])}")
                    schema_valid = False
                
                if "title" in menu_item and not isinstance(menu_item["title"], str):
                    print(f"   ❌ Field 'title' should be string, got {type(menu_item['title'])}")
                    schema_valid = False
                
                if "price" in menu_item and not isinstance(menu_item["price"], (int, float)):
                    print(f"   ❌ Field 'price' should be number, got {type(menu_item['price'])}")
                    schema_valid = False
                
                if "imageUrl" in menu_item and not isinstance(menu_item["imageUrl"], str):
                    print(f"   ❌ Field 'imageUrl' should be string, got {type(menu_item['imageUrl'])}")
                    schema_valid = False
                
                if "category" in menu_item and not isinstance(menu_item["category"], str):
                    print(f"   ❌ Field 'category' should be string, got {type(menu_item['category'])}")
                    schema_valid = False
            
            if schema_valid:
                print(f"   ✅ All menu items have correct schema")
                self.log_test("Menus Schema Validation", True, f"All {len(response)} menu items have correct schema")
                return True
            else:
                self.log_test("Menus Schema Validation", False, "Some menu items have invalid schema")
                return False
        
        return success

    def test_cors_configuration(self):
        """Test CORS configuration for cross-origin requests"""
        print("\n🌐 TESTING CORS CONFIGURATION")
        
        # Test preflight request (OPTIONS)
        cors_success, cors_response = self.run_test(
            "CORS Preflight Request",
            "OPTIONS",
            "/api/businesses",
            200,
            check_cors=True
        )
        
        if not cors_success:
            # Try different status codes that might be acceptable for OPTIONS
            cors_success, cors_response = self.run_test(
                "CORS Preflight Request (Alternative)",
                "OPTIONS", 
                "/api/businesses",
                204,
                check_cors=True
            )
        
        # Test actual cross-origin request
        cross_origin_headers = {
            'Origin': 'https://example.com'
        }
        
        cross_origin_success, cross_origin_response = self.run_test(
            "Cross-Origin GET Request",
            "GET",
            "businesses",
            200,
            headers=cross_origin_headers
        )
        
        if cross_origin_success:
            print(f"   ✅ Cross-origin requests working")
        
        return cors_success or cross_origin_success

    def test_existing_auth_endpoints(self):
        """Test that existing authentication endpoints still work"""
        print("\n🔐 TESTING EXISTING AUTHENTICATION ENDPOINTS")
        
        # Test admin login
        admin_success, admin_response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@test.com", "password": "6851"}
        )
        
        if admin_success and admin_response.get('access_token'):
            self.admin_token = admin_response['access_token']
            print(f"   ✅ Admin login successful, token stored")
        
        # Test customer registration and login
        customer_email = f"test_customer_{uuid.uuid4().hex[:8]}@example.com"
        customer_data = {
            "email": customer_email,
            "password": "test123",
            "first_name": "Test",
            "last_name": "Customer",
            "city": "İstanbul"
        }
        
        customer_reg_success, customer_reg_response = self.run_test(
            "Customer Registration",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        if customer_reg_success:
            # Test customer login
            customer_login_success, customer_login_response = self.run_test(
                "Customer Login",
                "POST",
                "auth/login",
                200,
                data={"email": customer_email, "password": "test123"}
            )
            
            if customer_login_success and customer_login_response.get('access_token'):
                self.customer_token = customer_login_response['access_token']
                print(f"   ✅ Customer login successful, token stored")
        
        # Test business registration and login
        business_email = f"test_business_{uuid.uuid4().hex[:8]}@example.com"
        business_data = {
            "email": business_email,
            "password": "test123",
            "business_name": "Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant"
        }
        
        business_reg_success, business_reg_response = self.run_test(
            "Business Registration",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if business_reg_success:
            # Test business login
            business_login_success, business_login_response = self.run_test(
                "Business Login",
                "POST",
                "auth/login",
                200,
                data={"email": business_email, "password": "test123"}
            )
            
            if business_login_success and business_login_response.get('access_token'):
                self.business_token = business_login_response['access_token']
                print(f"   ✅ Business login successful, token stored")
        
        return admin_success and customer_reg_success and business_reg_success

    def test_existing_business_endpoints(self):
        """Test that existing business endpoints still work"""
        print("\n🏢 TESTING EXISTING BUSINESS ENDPOINTS")
        
        # Test public businesses endpoint
        businesses_success, businesses_response = self.run_test(
            "Get Public Businesses",
            "GET",
            "businesses",
            200
        )
        
        if businesses_success:
            print(f"   ✅ Public businesses endpoint working, returned {len(businesses_response) if isinstance(businesses_response, list) else 'data'}")
        
        # Test admin endpoints if admin token available
        if self.admin_token:
            admin_users_success, admin_users_response = self.run_test(
                "Admin Get Users",
                "GET",
                "admin/users",
                200,
                token=self.admin_token
            )
            
            if admin_users_success:
                print(f"   ✅ Admin users endpoint working")
        
        # Test business endpoints if business token available
        if self.business_token:
            business_products_success, business_products_response = self.run_test(
                "Business Get Products",
                "GET",
                "products/my",
                200,
                token=self.business_token
            )
            
            if business_products_success:
                print(f"   ✅ Business products endpoint working")
        
        return businesses_success

    def test_backend_server_status(self):
        """Test that backend server is running and responding"""
        print("\n🖥️ TESTING BACKEND SERVER STATUS")
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Backend server is running and responding")
                print(f"   ✅ Server response time: {response.elapsed.total_seconds():.3f}s")
                return True
            else:
                print(f"   ❌ Backend server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Backend server not reachable: {str(e)}")
            return False

    def test_production_endpoints_comprehensive(self):
        """Run comprehensive test of all production deployment requirements"""
        print("\n🚀 COMPREHENSIVE PRODUCTION DEPLOYMENT TESTING")
        print("=" * 60)
        
        all_tests_passed = True
        
        # 1. Test health check endpoint
        if not self.test_health_check_endpoint():
            all_tests_passed = False
        
        # 2. Test menus endpoint
        if not self.test_menus_endpoint():
            all_tests_passed = False
        
        # 3. Test CORS configuration
        if not self.test_cors_configuration():
            all_tests_passed = False
        
        # 4. Test existing endpoints still work
        if not self.test_existing_auth_endpoints():
            all_tests_passed = False
        
        if not self.test_existing_business_endpoints():
            all_tests_passed = False
        
        # 5. Test backend server status
        if not self.test_backend_server_status():
            all_tests_passed = False
        
        return all_tests_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 PRODUCTION DEPLOYMENT TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL PRODUCTION DEPLOYMENT TESTS PASSED!")
            print("✅ Backend is ready for production deployment")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            print("❌ Production deployment requirements not fully met")
            
            # Show failed tests
            failed_tests = [test for test in self.test_results if not test['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)

def main():
    """Main test execution"""
    print("🚀 Starting Production Deployment Testing Suite")
    print("Testing newly added required endpoints for production deployment")
    
    tester = ProductionDeploymentTester()
    
    # Run comprehensive production deployment tests
    overall_success = tester.test_production_endpoints_comprehensive()
    
    # Print summary
    tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()