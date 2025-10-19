#!/usr/bin/env python3
"""
Address Creation Issue Testing - URGENT
Testing customer address creation functionality based on user report:
"Adres eklenirken hata oluştu" (Error occurred while adding address)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://food-dash-87.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

# Sample address data from review request
SAMPLE_ADDRESS = {
    "label": "Test Address",
    "city": "İstanbul", 
    "description": "Test address description",
    "lat": 41.0082,
    "lng": 28.9784
}

class AddressCreationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def authenticate_customer(self):
        """Test customer authentication"""
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                user_data = data.get("user", {})
                
                self.log_test(
                    "Customer Authentication",
                    True,
                    f"Login successful - User ID: {user_data.get('id')}, Role: {user_data.get('role')}, Token length: {len(self.auth_token) if self.auth_token else 0}"
                )
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                return True
            else:
                self.log_test(
                    "Customer Authentication",
                    False,
                    f"Login failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Customer Authentication",
                False,
                f"Exception during login: {str(e)}"
            )
            return False
    
    def test_address_creation_original(self):
        """Test address creation with original sample data"""
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=SAMPLE_ADDRESS)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Address Creation (Original Sample)",
                    True,
                    f"Address created successfully - ID: {data.get('id')}, Label: {data.get('label')}"
                )
                return data.get('id')
            else:
                self.log_test(
                    "Address Creation (Original Sample)",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test(
                "Address Creation (Original Sample)",
                False,
                f"Exception: {str(e)}"
            )
            return None
    
    def test_address_creation_variations(self):
        """Test address creation with field name variations"""
        variations = [
            {
                "name": "city_original field",
                "data": {
                    "label": "Test Address 2",
                    "city_original": "İstanbul",
                    "description": "Test with city_original field",
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            },
            {
                "name": "full_address field",
                "data": {
                    "label": "Test Address 3",
                    "city": "İstanbul",
                    "full_address": "Test full address field",
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            },
            {
                "name": "district field",
                "data": {
                    "label": "Test Address 4",
                    "city": "İstanbul",
                    "district": "Kadıköy",
                    "description": "Test with district field",
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            }
        ]
        
        for variation in variations:
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=variation["data"])
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        f"Address Creation ({variation['name']})",
                        True,
                        f"Created with {variation['name']} - ID: {data.get('id')}"
                    )
                else:
                    self.log_test(
                        f"Address Creation ({variation['name']})",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Address Creation ({variation['name']})",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def test_missing_fields_validation(self):
        """Test validation with missing required fields"""
        test_cases = [
            {
                "name": "Missing label",
                "data": {
                    "city": "İstanbul",
                    "description": "Test without label",
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            },
            {
                "name": "Missing city",
                "data": {
                    "label": "Test Address",
                    "description": "Test without city",
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            },
            {
                "name": "Missing coordinates",
                "data": {
                    "label": "Test Address",
                    "city": "İstanbul",
                    "description": "Test without coordinates"
                }
            },
            {
                "name": "Empty data",
                "data": {}
            }
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=test_case["data"])
                
                # For validation tests, we expect either success (200) or validation error (422/400)
                if response.status_code in [200, 400, 422]:
                    self.log_test(
                        f"Validation Test ({test_case['name']})",
                        True,
                        f"Handled correctly - Status: {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"Validation Test ({test_case['name']})",
                        False,
                        f"Unexpected status - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Validation Test ({test_case['name']})",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def test_address_retrieval(self):
        """Test GET /api/user/addresses to verify addresses are saved"""
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                if isinstance(addresses, list):
                    self.log_test(
                        "Address Retrieval",
                        True,
                        f"Retrieved {len(addresses)} addresses successfully"
                    )
                    
                    # Log details of retrieved addresses
                    for i, addr in enumerate(addresses[:3]):  # Show first 3 addresses
                        print(f"   Address {i+1}: {addr.get('label', 'No Label')} - {addr.get('city', 'No City')} - ID: {addr.get('id', 'No ID')}")
                    
                    return addresses
                else:
                    self.log_test(
                        "Address Retrieval",
                        False,
                        f"Unexpected response format: {type(addresses)}"
                    )
                    return []
            else:
                self.log_test(
                    "Address Retrieval",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "Address Retrieval",
                False,
                f"Exception: {str(e)}"
            )
            return []
    
    def test_jwt_token_validation(self):
        """Test JWT token validation via /me endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/me")
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_test(
                    "JWT Token Validation",
                    True,
                    f"Token valid - User: {user_data.get('email')}, ID: {user_data.get('id')}, Role: {user_data.get('role')}"
                )
                return True
            else:
                self.log_test(
                    "JWT Token Validation",
                    False,
                    f"Token validation failed - Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "JWT Token Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def run_comprehensive_test(self):
        """Run all address creation tests"""
        print("🔍 URGENT ADDRESS CREATION ISSUE TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Customer: {TEST_CUSTOMER_EMAIL}")
        print("=" * 60)
        print()
        
        # Step 1: Authenticate customer
        if not self.authenticate_customer():
            print("❌ CRITICAL: Customer authentication failed - cannot proceed with address tests")
            return False
        
        # Step 2: Validate JWT token
        self.test_jwt_token_validation()
        
        # Step 3: Test address creation with original sample data
        address_id = self.test_address_creation_original()
        
        # Step 4: Test address creation with field variations
        self.test_address_creation_variations()
        
        # Step 5: Test validation with missing fields
        self.test_missing_fields_validation()
        
        # Step 6: Verify addresses are saved
        saved_addresses = self.test_address_retrieval()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical issues
        critical_failures = []
        for result in self.test_results:
            if not result["success"] and any(keyword in result["test"] for keyword in ["Authentication", "Address Creation (Original Sample)", "Address Retrieval"]):
                critical_failures.append(result)
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES IDENTIFIED:")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['details']}")
            print()
        
        # Recommendations
        print("💡 ANALYSIS & RECOMMENDATIONS:")
        
        if not self.auth_token:
            print("   - Customer authentication is failing - check credentials and login endpoint")
        elif failed_tests == 0:
            print("   - All address creation tests passed - issue may be frontend-related")
        elif any("Address Creation" in r["test"] and not r["success"] for r in self.test_results):
            print("   - Address creation endpoint has issues - check field validation and database operations")
        else:
            print("   - Mixed results - investigate specific failing scenarios")
        
        print()
        return success_rate > 80

def main():
    """Main test execution"""
    tester = AddressCreationTester()
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()