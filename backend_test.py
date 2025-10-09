#!/usr/bin/env python3
"""
Address Management Backend Testing - Post-Fix Verification
Testing address creation after fixing endpoint inconsistencies and apiClient response handling.

Focus Areas:
1. Customer authentication verification
2. Address creation with correct endpoint /api/user/addresses
3. All CRUD operations verification
4. Response format validation
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import traceback

# Test Configuration
BASE_URL = "https://deliver-yemek.preview.emergentagent.com/api"
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

# Test data from review request
TEST_ADDRESS_DATA = {
    "label": "Test Adres Fix",
    "city": "Niğde", 
    "district": "Merkez",
    "description": "Test adres endpoint düzeltmesi sonrası",
    "lat": 37.9667,
    "lng": 34.6833
}

class AddressTestRunner:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_address_ids = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
        
    async def test_customer_authentication(self):
        """Test 1: Verify customer login with testcustomer@example.com/test123"""
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.auth_token = response_data.get("access_token")
                    user_data = response_data.get("user", {})
                    
                    if self.auth_token and user_data.get("role") == "customer":
                        self.log_test(
                            "Customer Authentication",
                            True,
                            f"Login successful. Token length: {len(self.auth_token)} chars, User ID: {user_data.get('id')}, Role: {user_data.get('role')}"
                        )
                        
                        # Update session headers with auth token
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                        return True
                    else:
                        self.log_test(
                            "Customer Authentication",
                            False,
                            "Missing token or incorrect role",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "Customer Authentication",
                        False,
                        f"Login failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Customer Authentication",
                False,
                f"Exception during login: {str(e)}"
            )
            return False
            
    async def test_jwt_token_validation(self):
        """Test 2: Verify JWT token is working via /me endpoint"""
        try:
            async with self.session.get(f"{BASE_URL}/me") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    user_data = response_data
                    if user_data.get("email") == TEST_CUSTOMER_EMAIL and user_data.get("role") == "customer":
                        self.log_test(
                            "JWT Token Validation",
                            True,
                            f"Token validation successful. User: {user_data.get('id')}, Email: {user_data.get('email')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "JWT Token Validation",
                            False,
                            "Token valid but user data mismatch",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "JWT Token Validation",
                        False,
                        f"Token validation failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "JWT Token Validation",
                False,
                f"Exception during token validation: {str(e)}"
            )
            return False
            
    async def test_get_user_addresses(self):
        """Test 3: GET /api/user/addresses - List existing addresses"""
        try:
            async with self.session.get(f"{BASE_URL}/user/addresses") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    addresses = response_data if isinstance(response_data, list) else response_data.get("addresses", [])
                    self.log_test(
                        "GET User Addresses",
                        True,
                        f"Retrieved {len(addresses)} addresses successfully"
                    )
                    return True
                else:
                    self.log_test(
                        "GET User Addresses",
                        False,
                        f"Failed to retrieve addresses with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "GET User Addresses",
                False,
                f"Exception during address retrieval: {str(e)}"
            )
            return False
            
    async def test_create_address(self):
        """Test 4: POST /api/user/addresses - Create new address with test data"""
        try:
            async with self.session.post(f"{BASE_URL}/user/addresses", json=TEST_ADDRESS_DATA) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    address_id = response_data.get("id")
                    if address_id:
                        self.created_address_ids.append(address_id)
                        
                        # Verify all fields are correctly saved
                        saved_data = response_data
                        field_matches = []
                        for key, expected_value in TEST_ADDRESS_DATA.items():
                            actual_value = saved_data.get(key)
                            if actual_value == expected_value:
                                field_matches.append(f"{key}: ✓")
                            else:
                                field_matches.append(f"{key}: ✗ (expected: {expected_value}, got: {actual_value})")
                        
                        self.log_test(
                            "POST Create Address",
                            True,
                            f"Address created successfully. ID: {address_id}. Field validation: {', '.join(field_matches)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "POST Create Address",
                            False,
                            "Address created but no ID returned",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "POST Create Address",
                        False,
                        f"Address creation failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "POST Create Address",
                False,
                f"Exception during address creation: {str(e)}"
            )
            return False
            
    async def test_update_address(self):
        """Test 5: PUT /api/user/addresses/{id} - Update address"""
        if not self.created_address_ids:
            self.log_test(
                "PUT Update Address",
                False,
                "No address ID available for update test"
            )
            return False
            
        try:
            address_id = self.created_address_ids[0]
            update_data = {
                "label": "Updated Test Address",
                "city": "Niğde",
                "district": "Merkez", 
                "description": "Updated description after endpoint fix",
                "lat": 37.9667,
                "lng": 34.6833
            }
            
            async with self.session.put(f"{BASE_URL}/user/addresses/{address_id}", json=update_data) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Verify the label was updated
                    updated_label = response_data.get("label")
                    if updated_label == "Updated Test Address":
                        self.log_test(
                            "PUT Update Address",
                            True,
                            f"Address {address_id} updated successfully. New label: {updated_label}"
                        )
                        return True
                    else:
                        self.log_test(
                            "PUT Update Address",
                            False,
                            f"Address updated but label not changed. Expected: 'Updated Test Address', Got: {updated_label}",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "PUT Update Address",
                        False,
                        f"Address update failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "PUT Update Address",
                False,
                f"Exception during address update: {str(e)}"
            )
            return False
            
    async def test_set_default_address(self):
        """Test 6: POST /api/user/addresses/{id}/set-default - Set default address"""
        if not self.created_address_ids:
            self.log_test(
                "POST Set Default Address",
                False,
                "No address ID available for set-default test"
            )
            return False
            
        try:
            address_id = self.created_address_ids[0]
            
            async with self.session.post(f"{BASE_URL}/user/addresses/{address_id}/set-default") as response:
                response_data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "POST Set Default Address",
                        True,
                        f"Address {address_id} set as default successfully"
                    )
                    return True
                else:
                    self.log_test(
                        "POST Set Default Address",
                        False,
                        f"Set default failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "POST Set Default Address",
                False,
                f"Exception during set default: {str(e)}"
            )
            return False
            
    async def test_delete_address(self):
        """Test 7: DELETE /api/user/addresses/{id} - Delete address"""
        if not self.created_address_ids:
            self.log_test(
                "DELETE Address",
                False,
                "No address ID available for delete test"
            )
            return False
            
        try:
            address_id = self.created_address_ids[0]
            
            async with self.session.delete(f"{BASE_URL}/user/addresses/{address_id}") as response:
                response_data = await response.json() if response.content_type == 'application/json' else {}
                
                if response.status == 200:
                    self.log_test(
                        "DELETE Address",
                        True,
                        f"Address {address_id} deleted successfully"
                    )
                    # Remove from our tracking list
                    self.created_address_ids.remove(address_id)
                    return True
                else:
                    self.log_test(
                        "DELETE Address",
                        False,
                        f"Address deletion failed with status {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "DELETE Address",
                False,
                f"Exception during address deletion: {str(e)}"
            )
            return False
            
    async def test_response_format_compatibility(self):
        """Test 8: Verify response format is compatible with frontend expectations"""
        try:
            # Create a test address to check response format
            test_data = {
                "label": "Format Test Address",
                "city": "İstanbul",
                "district": "Kadıköy",
                "description": "Testing response format",
                "lat": 40.9833,
                "lng": 29.0167
            }
            
            async with self.session.post(f"{BASE_URL}/user/addresses", json=test_data) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Check if response has expected fields for frontend
                    required_fields = ["id", "label", "city", "district", "description", "lat", "lng"]
                    missing_fields = []
                    present_fields = []
                    
                    for field in required_fields:
                        if field in response_data:
                            present_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log_test(
                            "Response Format Compatibility",
                            True,
                            f"All required fields present: {', '.join(present_fields)}"
                        )
                        
                        # Clean up test address
                        if response_data.get("id"):
                            self.created_address_ids.append(response_data["id"])
                        
                        return True
                    else:
                        self.log_test(
                            "Response Format Compatibility",
                            False,
                            f"Missing fields: {', '.join(missing_fields)}. Present: {', '.join(present_fields)}",
                            response_data
                        )
                        return False
                else:
                    self.log_test(
                        "Response Format Compatibility",
                        False,
                        f"Failed to create test address for format check. Status: {response.status}",
                        response_data
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Response Format Compatibility",
                False,
                f"Exception during format test: {str(e)}"
            )
            return False
            
    async def test_authentication_security(self):
        """Test 9: Verify endpoints require authentication"""
        try:
            # Create session without auth token
            test_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            # Test unauthenticated access
            async with test_session.get(f"{BASE_URL}/user/addresses") as response:
                if response.status in [401, 403]:
                    self.log_test(
                        "Authentication Security",
                        True,
                        f"Unauthenticated access properly blocked with status {response.status}"
                    )
                    await test_session.close()
                    return True
                else:
                    response_data = await response.json() if response.content_type == 'application/json' else {}
                    self.log_test(
                        "Authentication Security",
                        False,
                        f"Unauthenticated access allowed with status {response.status}",
                        response_data
                    )
                    await test_session.close()
                    return False
                    
        except Exception as e:
            self.log_test(
                "Authentication Security",
                False,
                f"Exception during security test: {str(e)}"
            )
            return False
            
    async def cleanup_test_addresses(self):
        """Clean up any remaining test addresses"""
        for address_id in self.created_address_ids[:]:
            try:
                async with self.session.delete(f"{BASE_URL}/user/addresses/{address_id}") as response:
                    if response.status == 200:
                        print(f"🧹 Cleaned up test address: {address_id}")
                        self.created_address_ids.remove(address_id)
            except Exception as e:
                print(f"⚠️  Failed to cleanup address {address_id}: {e}")
                
    async def run_all_tests(self):
        """Run all address management tests"""
        print("🚀 Starting Address Management Backend Testing - Post-Fix Verification")
        print("=" * 80)
        print()
        
        await self.setup_session()
        
        try:
            # Test sequence
            tests = [
                ("Customer Authentication", self.test_customer_authentication),
                ("JWT Token Validation", self.test_jwt_token_validation),
                ("GET User Addresses", self.test_get_user_addresses),
                ("POST Create Address", self.test_create_address),
                ("PUT Update Address", self.test_update_address),
                ("POST Set Default Address", self.test_set_default_address),
                ("DELETE Address", self.test_delete_address),
                ("Response Format Compatibility", self.test_response_format_compatibility),
                ("Authentication Security", self.test_authentication_security),
            ]
            
            # Run tests
            for test_name, test_func in tests:
                try:
                    await test_func()
                except Exception as e:
                    self.log_test(test_name, False, f"Unexpected error: {str(e)}")
                    print(f"Stack trace: {traceback.format_exc()}")
                    
            # Cleanup
            await self.cleanup_test_addresses()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("🎯 ADDRESS MANAGEMENT TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {success_rate:.1f}% success rate ({passed_tests}/{total_tests} tests passed)")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
            
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['details']}")
        print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        auth_working = any(r["success"] and "Authentication" in r["test"] for r in self.test_results)
        create_working = any(r["success"] and "Create Address" in r["test"] for r in self.test_results)
        crud_working = sum(1 for r in self.test_results if r["success"] and any(op in r["test"] for op in ["GET", "POST", "PUT", "DELETE"]))
        
        print(f"   • Customer Authentication: {'✅ Working' if auth_working else '❌ Failed'}")
        print(f"   • Address Creation (Main Issue): {'✅ Working' if create_working else '❌ Failed'}")
        print(f"   • CRUD Operations: {crud_working}/5 working")
        print(f"   • Response Format: {'✅ Compatible' if any(r['success'] and 'Format' in r['test'] for r in self.test_results) else '❌ Issues'}")
        print()
        
        # Conclusion
        if success_rate >= 80:
            print("🎉 CONCLUSION: Address management system is working well after the fixes!")
            if create_working:
                print("   The reported 'Adres eklerken hata oluştu' issue appears to be resolved.")
        else:
            print("⚠️  CONCLUSION: Address management system has issues that need attention.")
            if not create_working:
                print("   The 'Adres eklerken hata oluştu' issue is still present.")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    runner = AddressTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())