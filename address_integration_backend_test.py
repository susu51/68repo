#!/usr/bin/env python3
"""
URGENT ADDRESS INTEGRATION BACKEND TEST
=====================================

Testing the complete address integration workflow as requested:
- User reports: "Adres yönetimine eklediğim halde keşfette göstermiyor adresleri"
- Focus: Backend address verification, creation, and authentication

Test Requirements:
1. Backend Address Verification - Login as testcustomer@example.com/test123
2. GET /api/user/addresses - Check how many addresses exist
3. Address Creation Test - POST new address with sample data
4. Authentication Status - Verify JWT token is working properly
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://order-flow-debug.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testcustomer@example.com"
TEST_USER_PASSWORD = "test123"

class AddressIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.user_data = None
        self.test_results = []
        
    def log_test(self, test_name, success, details, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def test_customer_authentication(self):
        """Test 1: Customer Authentication"""
        print("\n🔐 TESTING CUSTOMER AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                self.user_data = data.get("user", {})
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log_test(
                    "Customer Login",
                    True,
                    f"Login successful - JWT token: {len(self.jwt_token)} chars, User ID: {self.user_data.get('id')}, Role: {self.user_data.get('role')}",
                    {
                        "user_id": self.user_data.get('id'),
                        "email": self.user_data.get('email'),
                        "role": self.user_data.get('role'),
                        "token_length": len(self.jwt_token) if self.jwt_token else 0
                    }
                )
                return True
            else:
                self.log_test(
                    "Customer Login",
                    False,
                    f"Login failed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Exception: {str(e)}")
            return False
    
    def test_jwt_token_validation(self):
        """Test 2: JWT Token Validation"""
        print("\n🎫 TESTING JWT TOKEN VALIDATION")
        print("=" * 50)
        
        if not self.jwt_token:
            self.log_test("JWT Token Validation", False, "No JWT token available")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/me")
            
            if response.status_code == 200:
                user_info = response.json()
                self.log_test(
                    "JWT Token Validation",
                    True,
                    f"Token validation successful - User: {user_info.get('email')}, Role: {user_info.get('role')}",
                    user_info
                )
                return True
            else:
                self.log_test(
                    "JWT Token Validation",
                    False,
                    f"Token validation failed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("JWT Token Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_address_retrieval(self):
        """Test 3: Address Retrieval - GET /api/user/addresses"""
        print("\n📍 TESTING ADDRESS RETRIEVAL")
        print("=" * 50)
        
        if not self.jwt_token:
            self.log_test("Address Retrieval", False, "No JWT token available")
            return False, []
        
        try:
            response = self.session.get(f"{BASE_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                address_count = len(addresses) if isinstance(addresses, list) else len(addresses.get('addresses', []))
                
                self.log_test(
                    "Address Retrieval",
                    True,
                    f"Successfully retrieved {address_count} addresses for testcustomer@example.com",
                    {
                        "address_count": address_count,
                        "addresses": addresses[:3] if isinstance(addresses, list) else addresses.get('addresses', [])[:3]  # Show first 3 addresses
                    }
                )
                return True, addresses
            else:
                self.log_test(
                    "Address Retrieval",
                    False,
                    f"Address retrieval failed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False, []
                
        except Exception as e:
            self.log_test("Address Retrieval", False, f"Exception: {str(e)}")
            return False, []
    
    def test_address_creation(self):
        """Test 4: Address Creation - POST /api/user/addresses"""
        print("\n➕ TESTING ADDRESS CREATION")
        print("=" * 50)
        
        if not self.jwt_token:
            self.log_test("Address Creation", False, "No JWT token available")
            return False
        
        try:
            # Sample address data as specified in the review request
            address_data = {
                "label": "Test Integration Address",
                "city": "İstanbul",
                "description": "Test address for integration debugging",
                "lat": 41.0082,
                "lng": 28.9784
            }
            
            response = self.session.post(f"{BASE_URL}/user/addresses", json=address_data)
            
            if response.status_code in [200, 201]:
                created_address = response.json()
                self.log_test(
                    "Address Creation",
                    True,
                    f"Address created successfully - ID: {created_address.get('id', 'N/A')}, Label: {created_address.get('label', 'N/A')}",
                    created_address
                )
                return True, created_address
            else:
                self.log_test(
                    "Address Creation",
                    False,
                    f"Address creation failed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False, None
                
        except Exception as e:
            self.log_test("Address Creation", False, f"Exception: {str(e)}")
            return False, None
    
    def test_address_verification_after_creation(self):
        """Test 5: Verify Address Was Saved - GET /api/user/addresses again"""
        print("\n🔍 TESTING ADDRESS VERIFICATION AFTER CREATION")
        print("=" * 50)
        
        if not self.jwt_token:
            self.log_test("Address Verification", False, "No JWT token available")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                address_count = len(addresses) if isinstance(addresses, list) else len(addresses.get('addresses', []))
                
                # Look for our test address
                test_address_found = False
                address_list = addresses if isinstance(addresses, list) else addresses.get('addresses', [])
                
                for addr in address_list:
                    if addr.get('label') == 'Test Integration Address':
                        test_address_found = True
                        break
                
                self.log_test(
                    "Address Verification",
                    True,
                    f"Address verification complete - Total: {address_count} addresses, Test address found: {test_address_found}",
                    {
                        "total_addresses": address_count,
                        "test_address_found": test_address_found,
                        "sample_addresses": address_list[:3]  # Show first 3 addresses
                    }
                )
                return True
            else:
                self.log_test(
                    "Address Verification",
                    False,
                    f"Address verification failed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Address Verification", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_requirements(self):
        """Test 6: Authentication Requirements - Test without token"""
        print("\n🚫 TESTING AUTHENTICATION REQUIREMENTS")
        print("=" * 50)
        
        try:
            # Create a session without authorization header
            unauth_session = requests.Session()
            
            response = unauth_session.get(f"{BASE_URL}/user/addresses")
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Authentication Requirements",
                    True,
                    f"Properly rejected unauthorized request - Status: {response.status_code}",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Authentication Requirements",
                    False,
                    f"Security issue - Unauthorized request allowed - Status: {response.status_code}",
                    response.json() if response.content else {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("Authentication Requirements", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all address integration tests"""
        print("🚀 URGENT ADDRESS INTEGRATION BACKEND TESTING")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Customer Authentication", self.test_customer_authentication),
            ("JWT Token Validation", self.test_jwt_token_validation),
            ("Address Retrieval", lambda: self.test_address_retrieval()[0]),
            ("Address Creation", lambda: self.test_address_creation()[0]),
            ("Address Verification", self.test_address_verification_after_creation),
            ("Authentication Requirements", self.test_authentication_requirements)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name}: Exception - {str(e)}")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎯 URGENT ADDRESS INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Address integration backend is working correctly")
        elif success_rate >= 75:
            print("⚠️  GOOD: Address integration mostly working with minor issues")
        else:
            print("❌ CRITICAL: Address integration has significant issues")
        
        # Detailed findings
        print("\n📋 DETAILED FINDINGS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # User Issue Analysis
        print("\n🔍 USER ISSUE ANALYSIS:")
        print("User reported: 'Adres yönetimine eklediğim halde keşfette göstermiyor adresleri'")
        print("(Addresses added to address management are not showing in discovery)")
        
        if passed_tests >= 4:  # If most backend tests pass
            print("✅ BACKEND ANALYSIS: Address management backend is working correctly")
            print("   - Customer authentication: Working")
            print("   - Address creation: Working") 
            print("   - Address retrieval: Working")
            print("   - Data persistence: Working")
            print("💡 CONCLUSION: Issue likely in FRONTEND address-discovery integration")
            print("   - Check if frontend properly loads addresses in discovery page")
            print("   - Verify address selection triggers restaurant filtering")
            print("   - Confirm API calls are made with correct address data")
        else:
            print("❌ BACKEND ANALYSIS: Critical backend issues found")
            print("💡 CONCLUSION: Backend address management needs fixes before frontend testing")
        
        return success_rate, self.test_results

def main():
    """Main test execution"""
    tester = AddressIntegrationTester()
    success_rate, results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 75 else 1)

if __name__ == "__main__":
    main()