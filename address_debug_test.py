#!/usr/bin/env python3
"""
Address Debug Test - Comprehensive testing of customer address functionality
Based on user report: "Adresi Kaydet" button not working
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://delivery-platform-10.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CUSTOMER = {
    "email": "testcustomer@example.com",
    "password": "test123"
}

class AddressDebugTest:
    def __init__(self):
        self.session = requests.Session()
        self.customer_token = None
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
        
    def test_customer_login(self):
        """Test customer authentication"""
        print("\n🔐 CUSTOMER AUTHENTICATION TEST")
        print("=" * 50)
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=TEST_CUSTOMER,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                
                if self.customer_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.customer_token}"
                    })
                    
                    user_data = data.get("user", {})
                    self.log_result(
                        "Customer Login",
                        True,
                        f"✅ Login successful. User: {user_data.get('first_name', '')} {user_data.get('last_name', '')} (ID: {user_data.get('id', 'unknown')})",
                        response_time
                    )
                    return True
                else:
                    self.log_result(
                        "Customer Login",
                        False,
                        "❌ Login response missing access_token",
                        response_time
                    )
                    return False
            else:
                self.log_result(
                    "Customer Login",
                    False,
                    f"❌ Login failed with status {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "Customer Login",
                False,
                f"❌ Login request failed: {str(e)}",
                response_time
            )
            return False
    
    def test_address_endpoints(self):
        """Test address endpoints comprehensively"""
        print("\n📍 ADDRESS ENDPOINTS COMPREHENSIVE TEST")
        print("=" * 50)
        
        if not self.customer_token:
            self.log_result(
                "Address Endpoints",
                False,
                "❌ No customer token available"
            )
            return False
        
        # Test 1: GET addresses
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/user/addresses", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_result(
                    "GET /api/user/addresses",
                    True,
                    f"✅ Retrieved {len(addresses)} addresses successfully",
                    response_time
                )
                
                # Show sample addresses
                for i, addr in enumerate(addresses[:3]):
                    print(f"   Address {i+1}: {addr.get('label', 'No label')} - {addr.get('city', 'No city')}")
                
            elif response.status_code == 401:
                self.log_result(
                    "GET /api/user/addresses",
                    False,
                    "❌ 401 Unauthorized - JWT token validation failed",
                    response_time
                )
                return False
            else:
                self.log_result(
                    "GET /api/user/addresses",
                    False,
                    f"❌ Failed with status {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "GET /api/user/addresses",
                False,
                f"❌ Request failed: {str(e)}",
                response_time
            )
            return False
        
        # Test 2: POST new address (the "Adresi Kaydet" functionality)
        test_address = {
            "label": "Debug Test Address",
            "city": "İstanbul",
            "description": "Test address for debugging Adresi Kaydet button",
            "lat": 41.0082,
            "lng": 28.9784,
            "city_original": "İstanbul",
            "city_normalized": "istanbul"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/user/addresses",
                json=test_address,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                saved_address = response.json()
                self.log_result(
                    "POST /api/user/addresses (Adresi Kaydet)",
                    True,
                    f"✅ Address saved successfully. ID: {saved_address.get('id', 'unknown')}, Label: {saved_address.get('label', 'unknown')}",
                    response_time
                )
                
                # Verify response format
                required_fields = ["id", "label", "city", "description", "lat", "lng"]
                missing_fields = [field for field in required_fields if field not in saved_address]
                
                if not missing_fields:
                    print(f"   ✅ Response format valid - all required fields present")
                    
                    # Verify data integrity
                    data_matches = (
                        saved_address.get("label") == test_address["label"] and
                        saved_address.get("city") == test_address["city"] and
                        saved_address.get("description") == test_address["description"]
                    )
                    
                    if data_matches:
                        print(f"   ✅ Data integrity verified - saved data matches input")
                    else:
                        print(f"   ⚠️  Data integrity issue - some fields don't match")
                else:
                    print(f"   ⚠️  Response missing fields: {missing_fields}")
                
                return True
                
            elif response.status_code == 401:
                self.log_result(
                    "POST /api/user/addresses (Adresi Kaydet)",
                    False,
                    "❌ 401 Unauthorized - JWT token validation failed",
                    response_time
                )
                return False
            elif response.status_code == 500:
                self.log_result(
                    "POST /api/user/addresses (Adresi Kaydet)",
                    False,
                    f"❌ 500 Internal Server Error: {response.text}",
                    response_time
                )
                return False
            else:
                self.log_result(
                    "POST /api/user/addresses (Adresi Kaydet)",
                    False,
                    f"❌ Failed with status {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "POST /api/user/addresses (Adresi Kaydet)",
                False,
                f"❌ Request failed: {str(e)}",
                response_time
            )
            return False
    
    def test_jwt_token_details(self):
        """Test JWT token validation in detail"""
        print("\n🔑 JWT TOKEN VALIDATION DETAILS")
        print("=" * 50)
        
        if not self.customer_token:
            self.log_result(
                "JWT Token Details",
                False,
                "❌ No customer token available"
            )
            return False
        
        print(f"Token length: {len(self.customer_token)} characters")
        print(f"Token starts with: {self.customer_token[:20]}...")
        print(f"Token ends with: ...{self.customer_token[-20:]}")
        
        # Test token with /me endpoint
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/me", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_result(
                    "JWT Token Validation (/me)",
                    True,
                    f"✅ Token valid. User ID: {user_data.get('id', 'unknown')}, Email: {user_data.get('email', 'unknown')}, Role: {user_data.get('role', 'unknown')}",
                    response_time
                )
                return True
            else:
                self.log_result(
                    "JWT Token Validation (/me)",
                    False,
                    f"❌ Token validation failed with status {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "JWT Token Validation (/me)",
                False,
                f"❌ Token validation request failed: {str(e)}",
                response_time
            )
            return False
    
    def run_debug_test(self):
        """Run comprehensive debug test for address functionality"""
        print("🐛 ADDRESS FUNCTIONALITY DEBUG TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER['email']}")
        print(f"Testing 'Adresi Kaydet' button functionality")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 3
        
        # Test sequence
        if self.test_customer_login():
            tests_passed += 1
        
        if self.test_jwt_token_details():
            tests_passed += 1
        
        if self.test_address_endpoints():
            tests_passed += 1
        
        # Summary
        total_time = time.time() - self.start_time
        success_rate = (tests_passed / total_tests) * 100
        
        print("\n" + "=" * 60)
        print("🎯 ADDRESS FUNCTIONALITY DEBUG SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        
        if success_rate == 100:
            print("🎉 PERFECT: All address functionality working correctly!")
            print("📝 CONCLUSION: The 'Adresi Kaydet' button backend functionality is working perfectly.")
            print("   If users are experiencing issues, the problem is likely in the frontend.")
        elif success_rate >= 70:
            print("✅ GOOD: Address functionality mostly working")
        else:
            print("❌ ISSUES: Address functionality has problems")
        
        # Detailed results
        print("\n📊 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']} ({result['response_time']})")
        
        return success_rate >= 70

if __name__ == "__main__":
    tester = AddressDebugTest()
    success = tester.run_debug_test()
    exit(0 if success else 1)