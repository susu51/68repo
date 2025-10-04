#!/usr/bin/env python3
"""
PHASE 1 ADDRESS MANAGEMENT BACKEND TESTING
Comprehensive testing of address-related endpoints for the new frontend implementation.

Focus Areas:
1. Customer Authentication - Verify customer login with testcustomer@example.com/test123
2. Address CRUD Operations - Test all address endpoints
3. Data Validation - Test form validation, required fields, city normalization
4. JWT Token Handling - Ensure all address endpoints require valid authentication
5. Error Scenarios - Test invalid address IDs, missing fields, unauthorized access
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://food-delivery-hub-19.preview.emergentagent.com/api"
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

class AddressBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.customer_user_id = None
        self.test_address_ids = []
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["test_details"].append(test_result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_customer_authentication(self):
        """Test customer login with testcustomer@example.com/test123"""
        print("🔐 TESTING CUSTOMER AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                user_data = data.get("user", {})
                self.customer_user_id = user_data.get("id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log_test(
                    "Customer Login Authentication",
                    True,
                    f"Login successful. User ID: {self.customer_user_id}, Token length: {len(self.jwt_token) if self.jwt_token else 0} chars",
                    {"user_id": self.customer_user_id, "email": user_data.get("email"), "role": user_data.get("role")}
                )
                
                # Test JWT token validation via /me endpoint
                me_response = self.session.get(f"{BACKEND_URL}/me")
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    self.log_test(
                        "JWT Token Validation (/me endpoint)",
                        True,
                        f"Token validation successful. User: {me_data.get('email')} (ID: {me_data.get('id')})",
                        me_data
                    )
                else:
                    self.log_test(
                        "JWT Token Validation (/me endpoint)",
                        False,
                        f"Token validation failed. Status: {me_response.status_code}",
                        me_response.text
                    )
                
                return True
            else:
                self.log_test(
                    "Customer Login Authentication",
                    False,
                    f"Login failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Customer Login Authentication",
                False,
                f"Exception during login: {str(e)}"
            )
            return False
    
    def test_get_user_addresses(self):
        """Test GET /api/user/addresses - retrieve user addresses"""
        print("📍 TESTING ADDRESS RETRIEVAL")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_test(
                    "GET /api/user/addresses",
                    True,
                    f"Successfully retrieved {len(addresses)} addresses for authenticated customer",
                    {"address_count": len(addresses), "addresses": addresses[:2] if addresses else []}  # Show first 2 for brevity
                )
                return addresses
            else:
                self.log_test(
                    "GET /api/user/addresses",
                    False,
                    f"Failed to retrieve addresses. Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "GET /api/user/addresses",
                False,
                f"Exception during address retrieval: {str(e)}"
            )
            return []
    
    def test_add_user_address(self):
        """Test POST /api/user/addresses - add new address"""
        print("➕ TESTING ADDRESS CREATION")
        print("=" * 50)
        
        # Test data for new address
        test_addresses = [
            {
                "label": "Test Ev Adresi",
                "city": "İstanbul",
                "description": "Kadıköy, Moda Caddesi No:123 Daire:5",
                "lat": 40.9876,
                "lng": 29.0234
            },
            {
                "label": "Test İş Adresi", 
                "city": "Ankara",
                "description": "Çankaya, Atatürk Bulvarı No:456",
                "lat": 39.9208,
                "lng": 32.8541
            }
        ]
        
        created_addresses = []
        
        for i, address_data in enumerate(test_addresses):
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=address_data)
                
                if response.status_code == 200:
                    created_address = response.json()
                    address_id = created_address.get("id")
                    
                    if address_id:
                        self.test_address_ids.append(address_id)
                        created_addresses.append(created_address)
                    
                    self.log_test(
                        f"POST /api/user/addresses (Test {i+1})",
                        True,
                        f"Successfully created address '{address_data['label']}' with ID: {address_id}",
                        created_address
                    )
                else:
                    self.log_test(
                        f"POST /api/user/addresses (Test {i+1})",
                        False,
                        f"Failed to create address '{address_data['label']}'. Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"POST /api/user/addresses (Test {i+1})",
                    False,
                    f"Exception during address creation: {str(e)}"
                )
        
        return created_addresses
    
    def test_update_user_address(self):
        """Test PUT /api/user/addresses/{address_id} - update existing address"""
        print("✏️ TESTING ADDRESS UPDATE")
        print("=" * 50)
        
        if not self.test_address_ids:
            self.log_test(
                "PUT /api/user/addresses/{address_id}",
                False,
                "No test addresses available for update testing"
            )
            return
        
        # Use first test address for update
        address_id = self.test_address_ids[0]
        
        update_data = {
            "label": "Updated Test Ev Adresi",
            "city": "İstanbul",
            "description": "Kadıköy, Moda Caddesi No:123 Daire:5 (Güncellenmiş)",
            "lat": 40.9900,
            "lng": 29.0250
        }
        
        try:
            response = self.session.put(f"{BACKEND_URL}/user/addresses/{address_id}", json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "PUT /api/user/addresses/{address_id}",
                    True,
                    f"Successfully updated address {address_id}",
                    result
                )
            else:
                self.log_test(
                    "PUT /api/user/addresses/{address_id}",
                    False,
                    f"Failed to update address {address_id}. Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/user/addresses/{address_id}",
                False,
                f"Exception during address update: {str(e)}"
            )
    
    def test_set_default_address(self):
        """Test POST /api/user/addresses/{address_id}/set-default - set default address"""
        print("⭐ TESTING SET DEFAULT ADDRESS")
        print("=" * 50)
        
        if not self.test_address_ids:
            self.log_test(
                "POST /api/user/addresses/{address_id}/set-default",
                False,
                "No test addresses available for default address testing"
            )
            return
        
        # Use first test address for default setting
        address_id = self.test_address_ids[0]
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses/{address_id}/set-default")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "POST /api/user/addresses/{address_id}/set-default",
                    True,
                    f"Successfully set address {address_id} as default",
                    result
                )
            else:
                self.log_test(
                    "POST /api/user/addresses/{address_id}/set-default",
                    False,
                    f"Failed to set default address {address_id}. Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "POST /api/user/addresses/{address_id}/set-default",
                False,
                f"Exception during set default address: {str(e)}"
            )
    
    def test_delete_user_address(self):
        """Test DELETE /api/user/addresses/{address_id} - delete address"""
        print("🗑️ TESTING ADDRESS DELETION")
        print("=" * 50)
        
        if len(self.test_address_ids) < 2:
            self.log_test(
                "DELETE /api/user/addresses/{address_id}",
                False,
                "Need at least 2 test addresses for deletion testing"
            )
            return
        
        # Delete the second test address (keep first one for other tests)
        address_id = self.test_address_ids[1]
        
        try:
            response = self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "DELETE /api/user/addresses/{address_id}",
                    True,
                    f"Successfully deleted address {address_id}",
                    result
                )
                # Remove from our tracking list
                self.test_address_ids.remove(address_id)
            else:
                self.log_test(
                    "DELETE /api/user/addresses/{address_id}",
                    False,
                    f"Failed to delete address {address_id}. Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "DELETE /api/user/addresses/{address_id}",
                False,
                f"Exception during address deletion: {str(e)}"
            )
    
    def test_data_validation(self):
        """Test form validation, required fields, city normalization"""
        print("✅ TESTING DATA VALIDATION")
        print("=" * 50)
        
        # Test 1: Missing required fields
        try:
            invalid_data = {"label": ""}  # Missing city, description
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=invalid_data)
            
            # Should either succeed with defaults or fail with validation error
            if response.status_code in [200, 400, 422]:
                self.log_test(
                    "Data Validation - Missing Fields",
                    True,
                    f"Proper handling of missing fields. Status: {response.status_code}",
                    response.json() if response.status_code == 200 else response.text
                )
            else:
                self.log_test(
                    "Data Validation - Missing Fields",
                    False,
                    f"Unexpected response for missing fields. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Data Validation - Missing Fields",
                False,
                f"Exception during validation test: {str(e)}"
            )
        
        # Test 2: City normalization
        try:
            city_test_data = {
                "label": "City Normalization Test",
                "city": "ISTANBUL",  # Should be normalized to lowercase
                "description": "Test city normalization",
                "lat": 41.0082,
                "lng": 28.9784
            }
            
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=city_test_data)
            
            if response.status_code == 200:
                created_address = response.json()
                address_id = created_address.get("id")
                if address_id:
                    self.test_address_ids.append(address_id)
                
                self.log_test(
                    "Data Validation - City Normalization",
                    True,
                    f"City normalization test successful. Created address with ID: {address_id}",
                    created_address
                )
            else:
                self.log_test(
                    "Data Validation - City Normalization",
                    False,
                    f"City normalization test failed. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Data Validation - City Normalization",
                False,
                f"Exception during city normalization test: {str(e)}"
            )
    
    def test_authentication_requirements(self):
        """Test that all address endpoints require valid authentication"""
        print("🔒 TESTING AUTHENTICATION REQUIREMENTS")
        print("=" * 50)
        
        # Create a session without authentication
        unauth_session = requests.Session()
        
        endpoints_to_test = [
            ("GET", "/user/addresses", "Get Addresses"),
            ("POST", "/user/addresses", "Create Address"),
            ("PUT", "/user/addresses/test-id", "Update Address"),
            ("DELETE", "/user/addresses/test-id", "Delete Address"),
            ("POST", "/user/addresses/test-id/set-default", "Set Default Address")
        ]
        
        for method, endpoint, test_name in endpoints_to_test:
            try:
                if method == "GET":
                    response = unauth_session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    test_data = {"label": "test", "city": "test", "description": "test"}
                    response = unauth_session.post(f"{BACKEND_URL}{endpoint}", json=test_data)
                elif method == "PUT":
                    test_data = {"label": "test", "city": "test", "description": "test"}
                    response = unauth_session.put(f"{BACKEND_URL}{endpoint}", json=test_data)
                elif method == "DELETE":
                    response = unauth_session.delete(f"{BACKEND_URL}{endpoint}")
                
                # Should return 401 Unauthorized or 403 Forbidden
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"Auth Required - {test_name}",
                        True,
                        f"Properly rejected unauthorized request. Status: {response.status_code}",
                        {"status_code": response.status_code}
                    )
                else:
                    self.log_test(
                        f"Auth Required - {test_name}",
                        False,
                        f"Should reject unauthorized request but got status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Auth Required - {test_name}",
                    False,
                    f"Exception during auth test: {str(e)}"
                )
    
    def test_error_scenarios(self):
        """Test invalid address IDs, missing fields, unauthorized access"""
        print("⚠️ TESTING ERROR SCENARIOS")
        print("=" * 50)
        
        # Test 1: Invalid address ID
        try:
            invalid_id = "invalid-address-id-12345"
            response = self.session.get(f"{BACKEND_URL}/user/addresses")  # This gets all addresses
            
            # Try to update non-existent address
            update_response = self.session.put(
                f"{BACKEND_URL}/user/addresses/{invalid_id}",
                json={"label": "test", "city": "test", "description": "test"}
            )
            
            if update_response.status_code == 404:
                self.log_test(
                    "Error Handling - Invalid Address ID",
                    True,
                    f"Properly handled invalid address ID. Status: {update_response.status_code}",
                    {"status_code": update_response.status_code}
                )
            else:
                self.log_test(
                    "Error Handling - Invalid Address ID",
                    False,
                    f"Should return 404 for invalid address ID but got: {update_response.status_code}",
                    update_response.text
                )
                
        except Exception as e:
            self.log_test(
                "Error Handling - Invalid Address ID",
                False,
                f"Exception during invalid ID test: {str(e)}"
            )
        
        # Test 2: Try to delete non-existent address
        try:
            invalid_id = "non-existent-address-id"
            response = self.session.delete(f"{BACKEND_URL}/user/addresses/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test(
                    "Error Handling - Delete Non-existent Address",
                    True,
                    f"Properly handled deletion of non-existent address. Status: {response.status_code}",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test(
                    "Error Handling - Delete Non-existent Address",
                    False,
                    f"Should return 404 for non-existent address but got: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Error Handling - Delete Non-existent Address",
                False,
                f"Exception during non-existent address deletion test: {str(e)}"
            )
    
    def cleanup_test_data(self):
        """Clean up test addresses created during testing"""
        print("🧹 CLEANING UP TEST DATA")
        print("=" * 50)
        
        for address_id in self.test_address_ids:
            try:
                response = self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up test address: {address_id}")
                else:
                    print(f"⚠️ Could not clean up test address {address_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error cleaning up test address {address_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run all address management backend tests"""
        print("🚀 STARTING PHASE 1 ADDRESS MANAGEMENT BACKEND TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate customer
        if not self.test_customer_authentication():
            print("❌ CRITICAL: Customer authentication failed. Cannot proceed with address tests.")
            return self.generate_final_report()
        
        # Step 2: Test address retrieval
        existing_addresses = self.test_get_user_addresses()
        
        # Step 3: Test address creation
        self.test_add_user_address()
        
        # Step 4: Test address update
        self.test_update_user_address()
        
        # Step 5: Test set default address
        self.test_set_default_address()
        
        # Step 6: Test address deletion
        self.test_delete_user_address()
        
        # Step 7: Test data validation
        self.test_data_validation()
        
        # Step 8: Test authentication requirements
        self.test_authentication_requirements()
        
        # Step 9: Test error scenarios
        self.test_error_scenarios()
        
        # Step 10: Clean up test data
        self.cleanup_test_data()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 PHASE 1 ADDRESS MANAGEMENT BACKEND TEST RESULTS")
        print("=" * 80)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Address management backend is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD: Address management backend is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Address management backend has significant issues that need attention.")
        else:
            print("❌ CRITICAL: Address management backend has major failures requiring immediate fixes.")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "details": self.results["test_details"]
        }

def main():
    """Main test execution"""
    tester = AddressBackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
"""
Production Readiness Testing for Kuryecini Platform
Testing newly implemented and updated endpoints (Madde 1-10)
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
import tempfile

# Configuration
BACKEND_URL = "https://food-delivery-hub-19.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@test.com", "password": "6851"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class ProductionReadinessTest:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def authenticate_users(self):
        """Authenticate all test users"""
        print("\n🔐 AUTHENTICATION TESTING")
        print("=" * 50)
        
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[user_type] = data.get("access_token")
                    user_info = data.get("user", {})
                    self.log_result(
                        f"{user_type.title()} Login",
                        True,
                        f"Token obtained, Role: {user_info.get('role', 'unknown')}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"{user_type.title()} Login",
                        False,
                        f"Status: {response.status_code}, Response: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(f"{user_type.title()} Login", False, f"Exception: {str(e)}")
    
    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n🏥 HEALTH ENDPOINTS TESTING")
        print("=" * 50)
        
        health_endpoints = [
            ("/api/healthz", "Primary Health Check")
        ]
        
        for endpoint, description in health_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    self.log_result(
                        description,
                        status == "ok",
                        f"Status: {status}, Response time: {response_time:.2f}s",
                        response_time
                    )
                else:
                    self.log_result(
                        description,
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(description, False, f"Exception: {str(e)}")
    
    def test_public_menu_system(self):
        """Test public menu system with approved restaurants"""
        print("\n🍽️ PUBLIC MENU SYSTEM TESTING")
        print("=" * 50)
        
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/businesses", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                businesses = response.json()
                
                self.log_result(
                    "Public Business Endpoint",
                    True,
                    f"Found {len(businesses)} approved businesses",
                    response_time
                )
                
                # Test business structure
                if businesses:
                    business = businesses[0]
                    required_fields = ["id", "name", "category", "rating", "location"]
                    missing_fields = [field for field in required_fields if field not in business]
                    
                    self.log_result(
                        "Business Data Structure",
                        len(missing_fields) == 0,
                        f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                    )
                else:
                    self.log_result(
                        "Business Availability",
                        False,
                        "No approved businesses found - may need to approve test businesses"
                    )
            else:
                self.log_result(
                    "Public Business Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Public Business System", False, f"Exception: {str(e)}")
    
    def test_kyc_file_upload(self):
        """Test KYC file upload functionality"""
        print("\n📄 KYC FILE UPLOAD TESTING")
        print("=" * 50)
        
        if "courier" not in self.tokens:
            self.log_result("KYC File Upload", False, "Courier authentication required")
            return
        
        # Create temporary test files
        try:
            # Create a small test image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                # Write minimal JPEG header
                temp_file.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00')
                temp_file.write(b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f')
                temp_file.write(b'\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa\xff\xd9')
                license_file_path = temp_file.name
            
            # Test KYC upload
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            
            with open(license_file_path, 'rb') as license_file:
                files = {
                    'license_photo': ('test_license.jpg', license_file, 'image/jpeg')
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/couriers/kyc",
                    files=files,
                    headers=headers,
                    timeout=15
                )
                response_time = time.time() - start_time
            
            # Clean up temp file
            os.unlink(license_file_path)
            
            if response.status_code == 200:
                data = response.json()
                uploaded_docs = data.get("uploaded_documents", {})
                self.log_result(
                    "KYC File Upload",
                    True,
                    f"Upload successful, Documents: {list(uploaded_docs.keys())}",
                    response_time
                )
            else:
                self.log_result(
                    "KYC File Upload",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                
        except Exception as e:
            self.log_result("KYC File Upload", False, f"Exception: {str(e)}")
    
    def test_address_management(self):
        """Test address management CRUD operations"""
        print("\n🏠 ADDRESS MANAGEMENT TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Address Management", False, "Customer authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        test_address_id = None
        
        # Test 1: Get addresses (initially empty)
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/addresses", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_result(
                    "Get Addresses",
                    True,
                    f"Retrieved {len(addresses)} addresses",
                    response_time
                )
            else:
                self.log_result(
                    "Get Addresses",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Get Addresses", False, f"Exception: {str(e)}")
        
        # Test 2: Create new address
        try:
            new_address = {
                "title": "Test Ev Adresi",
                "address_line": "Kadıköy Mah. Test Sok. No:123",
                "district": "Kadıköy",
                "city": "İstanbul",
                "postal_code": "34710",
                "is_default": True
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/addresses",
                json=new_address,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                test_address_id = data.get("address_id") or data.get("id")
                self.log_result(
                    "Create Address",
                    True,
                    f"Address created with ID: {test_address_id}",
                    response_time
                )
            else:
                self.log_result(
                    "Create Address",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Create Address", False, f"Exception: {str(e)}")
        
        # Test 3: Update address (if created successfully)
        if test_address_id:
            try:
                updated_address = {
                    "title": "Test Ev Adresi (Güncellenmiş)",
                    "address_line": "Kadıköy Mah. Test Sok. No:456",
                    "district": "Kadıköy",
                    "city": "İstanbul",
                    "postal_code": "34710",
                    "is_default": True
                }
                
                start_time = time.time()
                response = self.session.put(
                    f"{API_BASE}/addresses/{test_address_id}",
                    json=updated_address,
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Update Address",
                        True,
                        "Address updated successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Update Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Update Address", False, f"Exception: {str(e)}")
        
        # Test 4: Set default address
        if test_address_id:
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/addresses/{test_address_id}/set-default",
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Set Default Address",
                        True,
                        "Default address set successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Set Default Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Set Default Address", False, f"Exception: {str(e)}")
        
        # Test 5: Delete address
        if test_address_id:
            try:
                start_time = time.time()
                response = self.session.delete(
                    f"{API_BASE}/addresses/{test_address_id}",
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Delete Address",
                        True,
                        "Address deleted successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Delete Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Delete Address", False, f"Exception: {str(e)}")
    
    def test_commission_system(self):
        """Test commission system and PriceBreakdown in order creation"""
        print("\n💰 COMMISSION SYSTEM TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Commission System", False, "Customer authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test order creation with commission calculation
        try:
            test_order = {
                "delivery_address": "Test Delivery Address, İstanbul",
                "delivery_lat": 41.0082,
                "delivery_lng": 28.9784,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Burger",
                        "product_price": 45.0,
                        "quantity": 2,
                        "subtotal": 90.0
                    },
                    {
                        "product_id": "test-product-2", 
                        "product_name": "Test Drink",
                        "product_price": 15.0,
                        "quantity": 1,
                        "subtotal": 15.0
                    }
                ],
                "total_amount": 105.0,
                "notes": "Test order for commission testing"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/orders",
                json=test_order,
                headers=headers,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                commission_amount = data.get("commission_amount", 0)
                total_amount = data.get("total_amount", 0)
                price_breakdown = data.get("price_breakdown")
                
                # Verify commission calculation (3% as per code)
                expected_commission = total_amount * 0.03
                commission_correct = abs(commission_amount - expected_commission) < 0.01
                
                self.log_result(
                    "Order Creation with Commission",
                    True,
                    f"Order created, Commission: ₺{commission_amount:.2f} (Expected: ₺{expected_commission:.2f})",
                    response_time
                )
                
                self.log_result(
                    "Commission Calculation",
                    commission_correct,
                    f"Commission: ₺{commission_amount:.2f}, Expected: ₺{expected_commission:.2f}"
                )
                
                if price_breakdown:
                    self.log_result(
                        "PriceBreakdown Structure",
                        True,
                        f"PriceBreakdown present with fields: {list(price_breakdown.keys())}"
                    )
                else:
                    self.log_result(
                        "PriceBreakdown Structure",
                        False,
                        "PriceBreakdown not found in order response"
                    )
                    
            else:
                self.log_result(
                    "Commission System",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                
        except Exception as e:
            self.log_result("Commission System", False, f"Exception: {str(e)}")
    
    def test_admin_config_system(self):
        """Test admin configuration system for commission parameters"""
        print("\n⚙️ ADMIN CONFIG SYSTEM TESTING")
        print("=" * 50)
        
        if "admin" not in self.tokens:
            self.log_result("Admin Config System", False, "Admin authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test 1: Get current configuration
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/admin/config", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                config = response.json()
                self.log_result(
                    "Get Admin Config",
                    True,
                    f"Retrieved {len(config)} configuration items",
                    response_time
                )
                
                # Check for commission-related config
                commission_configs = [item for item in config if 'commission' in item.get('key', '').lower()]
                self.log_result(
                    "Commission Config Items",
                    len(commission_configs) > 0,
                    f"Found {len(commission_configs)} commission-related config items"
                )
                
            else:
                self.log_result(
                    "Get Admin Config",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Get Admin Config", False, f"Exception: {str(e)}")
        
        # Test 2: Update configuration
        try:
            params = {
                "config_key": "platform_commission_rate",
                "config_value": 0.05,
                "description": "Platform commission rate (5%)"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/admin/config/update",
                params=params,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result(
                    "Update Admin Config",
                    True,
                    "Configuration updated successfully",
                    response_time
                )
            else:
                self.log_result(
                    "Update Admin Config",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Update Admin Config", False, f"Exception: {str(e)}")
    
    def test_cors_functionality(self):
        """Test CORS configuration"""
        print("\n🌐 CORS FUNCTIONALITY TESTING")
        print("=" * 50)
        
        try:
            # Test preflight request
            headers = {
                'Origin': 'https://food-delivery-hub-19.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            start_time = time.time()
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                self.log_result(
                    "CORS Preflight Request",
                    True,
                    f"CORS headers present: {list(cors_headers.keys())}",
                    response_time
                )
            else:
                self.log_result(
                    "CORS Preflight Request",
                    False,
                    f"HTTP {response.status_code}: Preflight failed",
                    response_time
                )
        except Exception as e:
            self.log_result("CORS Functionality", False, f"Exception: {str(e)}")
    
    def test_turkish_error_messages(self):
        """Test Turkish error message formatting"""
        print("\n🇹🇷 TURKISH ERROR MESSAGES TESTING")
        print("=" * 50)
        
        # Test invalid login for Turkish error message
        try:
            invalid_creds = {"email": "invalid@test.com", "password": "wrongpassword"}
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/auth/login", json=invalid_creds, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                
                # Check if error message is in Turkish
                turkish_keywords = ["yanlış", "hata", "geçersiz", "bulunamadı"]
                is_turkish = any(keyword in error_detail.lower() for keyword in turkish_keywords)
                
                self.log_result(
                    "Turkish Error Messages",
                    is_turkish,
                    f"Error message: '{error_detail}', Turkish: {is_turkish}",
                    response_time
                )
            else:
                self.log_result(
                    "Turkish Error Messages",
                    False,
                    f"Expected 400 error, got {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result("Turkish Error Messages", False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 PRODUCTION READINESS TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ CRITICAL SUCCESS CRITERIA CHECK:")
        critical_tests = [
            "Primary Health Check",
            "Public Business Endpoint",
            "Admin Login",
            "Customer Login",
            "Business Login",
            "Courier Login"
        ]
        
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"   {status} {test_name}")
            else:
                print(f"   ⚠️ {test_name} - Not tested")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": self.test_results
        }

def main():
    """Run production readiness tests"""
    print("🚀 KURYECINI PRODUCTION READINESS TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start Time: {datetime.now().isoformat()}")
    
    tester = ProductionReadinessTest()
    
    # Run all tests
    tester.authenticate_users()
    tester.test_health_endpoints()
    tester.test_public_menu_system()
    tester.test_kyc_file_upload()
    tester.test_address_management()
    tester.test_commission_system()
    tester.test_admin_config_system()
    tester.test_cors_functionality()
    tester.test_turkish_error_messages()
    
    # Generate final report
    report = tester.generate_report()
    
    return report

if __name__ == "__main__":
    main()