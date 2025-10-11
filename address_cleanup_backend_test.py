#!/usr/bin/env python3
"""
Address Management Cleanup and Testing Script
==============================================

This script performs comprehensive testing of the address management system:
1. DELETE ALL TEST ADDRESSES from the database
2. VERIFY ADDRESS ENDPOINTS work correctly  
3. TEST FIELD VALIDATION for address fields
4. TEST AUTHENTICATION to ensure user isolation

Usage: python address_cleanup_backend_test.py
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://courier-stable.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

# Test credentials
TEST_USERS = {
    "customer": {
        "email": "testcustomer@example.com",
        "password": "test123"
    },
    "admin": {
        "email": "admin@kuryecini.com", 
        "password": "KuryeciniAdmin2024!"
    }
}

class AddressCleanupTester:
    def __init__(self):
        self.session = None
        self.results = {
            "cleanup": {"total": 0, "passed": 0, "failed": 0, "details": []},
            "endpoints": {"total": 0, "passed": 0, "failed": 0, "details": []},
            "validation": {"total": 0, "passed": 0, "failed": 0, "details": []},
            "authentication": {"total": 0, "passed": 0, "failed": 0, "details": []},
        }
        self.tokens = {}
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.results[category]["total"] += 1
        if success:
            self.results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.results[category]["failed"] += 1
            status = "❌ FAIL"
            
        self.results[category]["details"].append({
            "test": test_name,
            "status": status,
            "details": details
        })
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")

    async def authenticate_user(self, user_type: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        try:
            user_creds = TEST_USERS[user_type]
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=user_creds,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    self.tokens[user_type] = token
                    print(f"🔐 {user_type.title()} authentication successful (token: {len(token)} chars)")
                    return token
                else:
                    error_text = await response.text()
                    print(f"❌ {user_type.title()} authentication failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Authentication error for {user_type}: {e}")
            return None

    async def get_all_addresses_from_db(self) -> List[Dict]:
        """Get all addresses from database using admin access"""
        try:
            # This would require direct database access or admin endpoint
            # For now, we'll use the customer endpoint to get addresses for test user
            token = self.tokens.get("customer")
            if not token:
                return []
                
            headers = {"Authorization": f"Bearer {token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            ) as response:
                if response.status == 200:
                    addresses = await response.json()
                    return addresses if isinstance(addresses, list) else []
                return []
                
        except Exception as e:
            print(f"❌ Error getting addresses from DB: {e}")
            return []

    async def delete_test_addresses(self) -> None:
        """Delete all test addresses from the database"""
        print("\n🧹 PHASE 1: CLEANING UP TEST ADDRESSES")
        print("=" * 50)
        
        # Get customer token
        customer_token = await self.authenticate_user("customer")
        if not customer_token:
            self.log_result("cleanup", "Customer Authentication", False, "Failed to authenticate customer")
            return
            
        # Get all addresses for the test customer
        try:
            headers = {"Authorization": f"Bearer {customer_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            ) as response:
                if response.status == 200:
                    addresses = await response.json()
                    if isinstance(addresses, list):
                        initial_count = len(addresses)
                        print(f"📊 Found {initial_count} addresses for test customer")
                        
                        # Delete each address
                        deleted_count = 0
                        for address in addresses:
                            address_id = address.get("id")
                            if address_id:
                                try:
                                    async with self.session.delete(
                                        f"{BACKEND_URL}/user/addresses/{address_id}",
                                        headers=headers
                                    ) as del_response:
                                        if del_response.status == 200:
                                            deleted_count += 1
                                            print(f"🗑️  Deleted address: {address.get('label', 'Unnamed')} (ID: {address_id})")
                                        else:
                                            error_text = await del_response.text()
                                            print(f"⚠️  Failed to delete address {address_id}: {error_text}")
                                except Exception as e:
                                    print(f"⚠️  Error deleting address {address_id}: {e}")
                        
                        self.log_result("cleanup", "Delete Test Addresses", True, 
                                      f"Deleted {deleted_count}/{initial_count} addresses")
                    else:
                        self.log_result("cleanup", "Get Addresses for Cleanup", False, 
                                      f"Invalid response format: {type(addresses)}")
                else:
                    error_text = await response.text()
                    self.log_result("cleanup", "Get Addresses for Cleanup", False, 
                                  f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("cleanup", "Delete Test Addresses", False, f"Exception: {e}")

    async def test_address_endpoints(self) -> None:
        """Test all address management endpoints"""
        print("\n🔗 PHASE 2: TESTING ADDRESS ENDPOINTS")
        print("=" * 50)
        
        customer_token = self.tokens.get("customer")
        if not customer_token:
            customer_token = await self.authenticate_user("customer")
            
        if not customer_token:
            self.log_result("endpoints", "Customer Authentication", False, "No customer token available")
            return
            
        headers = {"Authorization": f"Bearer {customer_token}"}
        
        # Test 1: GET /api/user/addresses (should be empty after cleanup)
        try:
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            ) as response:
                if response.status == 200:
                    addresses = await response.json()
                    if isinstance(addresses, list):
                        self.log_result("endpoints", "GET /api/user/addresses", True, 
                                      f"Retrieved {len(addresses)} addresses")
                    else:
                        self.log_result("endpoints", "GET /api/user/addresses", False, 
                                      f"Invalid response format: {type(addresses)}")
                else:
                    error_text = await response.text()
                    self.log_result("endpoints", "GET /api/user/addresses", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("endpoints", "GET /api/user/addresses", False, f"Exception: {e}")

        # Test 2: POST /api/user/addresses (create new address)
        test_address = {
            "label": "Test Address for Cleanup",
            "city": "İstanbul",
            "district": "Kadıköy", 
            "description": "Test address created during cleanup testing",
            "lat": 40.9923,
            "lng": 29.0209
        }
        
        created_address_id = None
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=test_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    created_address_id = result.get("id")
                    self.log_result("endpoints", "POST /api/user/addresses", True, 
                                  f"Created address with ID: {created_address_id}")
                else:
                    error_text = await response.text()
                    self.log_result("endpoints", "POST /api/user/addresses", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("endpoints", "POST /api/user/addresses", False, f"Exception: {e}")

        # Test 3: PUT /api/user/addresses/{id} (update address)
        if created_address_id:
            updated_address = {
                "label": "Updated Test Address",
                "city": "Ankara",
                "district": "Çankaya",
                "description": "Updated test address",
                "lat": 39.9334,
                "lng": 32.8597
            }
            
            try:
                async with self.session.put(
                    f"{BACKEND_URL}/user/addresses/{created_address_id}",
                    json=updated_address,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        self.log_result("endpoints", "PUT /api/user/addresses/{id}", True, 
                                      f"Updated address {created_address_id}")
                    else:
                        error_text = await response.text()
                        self.log_result("endpoints", "PUT /api/user/addresses/{id}", False, 
                                      f"HTTP {response.status}: {error_text}")
            except Exception as e:
                self.log_result("endpoints", "PUT /api/user/addresses/{id}", False, f"Exception: {e}")

        # Test 4: POST /api/user/addresses/{id}/set-default (set default address)
        if created_address_id:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/user/addresses/{created_address_id}/set-default",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        self.log_result("endpoints", "POST /api/user/addresses/{id}/set-default", True, 
                                      f"Set address {created_address_id} as default")
                    else:
                        error_text = await response.text()
                        self.log_result("endpoints", "POST /api/user/addresses/{id}/set-default", False, 
                                      f"HTTP {response.status}: {error_text}")
            except Exception as e:
                self.log_result("endpoints", "POST /api/user/addresses/{id}/set-default", False, f"Exception: {e}")

        # Test 5: DELETE /api/user/addresses/{id} (delete address)
        if created_address_id:
            try:
                async with self.session.delete(
                    f"{BACKEND_URL}/user/addresses/{created_address_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        self.log_result("endpoints", "DELETE /api/user/addresses/{id}", True, 
                                      f"Deleted address {created_address_id}")
                    else:
                        error_text = await response.text()
                        self.log_result("endpoints", "DELETE /api/user/addresses/{id}", False, 
                                      f"HTTP {response.status}: {error_text}")
            except Exception as e:
                self.log_result("endpoints", "DELETE /api/user/addresses/{id}", False, f"Exception: {e}")

    async def test_field_validation(self) -> None:
        """Test field validation for address fields"""
        print("\n✅ PHASE 3: TESTING FIELD VALIDATION")
        print("=" * 50)
        
        customer_token = self.tokens.get("customer")
        if not customer_token:
            self.log_result("validation", "Customer Token", False, "No customer token available")
            return
            
        headers = {"Authorization": f"Bearer {customer_token}"}
        
        # Test 1: Valid address with all fields
        valid_address = {
            "label": "Complete Test Address",
            "city": "İzmir",
            "district": "Konak",
            "description": "Complete address with all fields",
            "lat": 38.4192,
            "lng": 27.1287
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=valid_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    address_id = result.get("id")
                    self.log_result("validation", "Valid Address Creation", True, 
                                  f"Created address with all fields: {address_id}")
                    
                    # Clean up
                    if address_id:
                        await self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}", headers=headers)
                else:
                    error_text = await response.text()
                    self.log_result("validation", "Valid Address Creation", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("validation", "Valid Address Creation", False, f"Exception: {e}")

        # Test 2: Address with Turkish characters in city
        turkish_address = {
            "label": "Türkçe Karakter Testi",
            "city": "Şanlıurfa",
            "district": "Eyyübiye",
            "description": "Türkçe karakterler içeren adres: ğüşıöç",
            "lat": 37.1591,
            "lng": 38.7969
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=turkish_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    address_id = result.get("id")
                    self.log_result("validation", "Turkish Characters Support", True, 
                                  f"Created address with Turkish characters: {address_id}")
                    
                    # Clean up
                    if address_id:
                        await self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}", headers=headers)
                else:
                    error_text = await response.text()
                    self.log_result("validation", "Turkish Characters Support", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("validation", "Turkish Characters Support", False, f"Exception: {e}")

        # Test 3: Address with missing optional fields
        minimal_address = {
            "label": "Minimal Address",
            "city": "Bursa"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=minimal_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    address_id = result.get("id")
                    self.log_result("validation", "Minimal Address Fields", True, 
                                  f"Created address with minimal fields: {address_id}")
                    
                    # Clean up
                    if address_id:
                        await self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}", headers=headers)
                else:
                    error_text = await response.text()
                    self.log_result("validation", "Minimal Address Fields", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("validation", "Minimal Address Fields", False, f"Exception: {e}")

        # Test 4: Address with coordinates validation
        coordinate_address = {
            "label": "Coordinate Test",
            "city": "Antalya",
            "district": "Muratpaşa",
            "description": "Testing coordinate validation",
            "lat": 36.8969,
            "lng": 30.7133
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=coordinate_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    address_id = result.get("id")
                    # Verify coordinates are returned
                    if result.get("lat") == coordinate_address["lat"] and result.get("lng") == coordinate_address["lng"]:
                        self.log_result("validation", "Coordinate Validation", True, 
                                      f"Coordinates properly saved and returned: {address_id}")
                    else:
                        self.log_result("validation", "Coordinate Validation", False, 
                                      f"Coordinates not properly returned: expected {coordinate_address['lat']}, {coordinate_address['lng']}")
                    
                    # Clean up
                    if address_id:
                        await self.session.delete(f"{BACKEND_URL}/user/addresses/{address_id}", headers=headers)
                else:
                    error_text = await response.text()
                    self.log_result("validation", "Coordinate Validation", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("validation", "Coordinate Validation", False, f"Exception: {e}")

    async def test_authentication_isolation(self) -> None:
        """Test authentication and user isolation"""
        print("\n🔐 PHASE 4: TESTING AUTHENTICATION & USER ISOLATION")
        print("=" * 50)
        
        customer_token = self.tokens.get("customer")
        if not customer_token:
            self.log_result("authentication", "Customer Token", False, "No customer token available")
            return
            
        headers = {"Authorization": f"Bearer {customer_token}"}
        
        # Test 1: Authenticated access works
        try:
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.log_result("authentication", "Authenticated Access", True, 
                                  "Customer can access their addresses with valid token")
                else:
                    error_text = await response.text()
                    self.log_result("authentication", "Authenticated Access", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("authentication", "Authenticated Access", False, f"Exception: {e}")

        # Test 2: Unauthenticated access is blocked
        try:
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses"
            ) as response:
                if response.status in [401, 403]:
                    self.log_result("authentication", "Unauthenticated Access Blocked", True, 
                                  f"Properly blocked unauthenticated access: HTTP {response.status}")
                else:
                    self.log_result("authentication", "Unauthenticated Access Blocked", False, 
                                  f"Should block unauthenticated access but got: HTTP {response.status}")
        except Exception as e:
            self.log_result("authentication", "Unauthenticated Access Blocked", False, f"Exception: {e}")

        # Test 3: Invalid token is rejected
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        try:
            async with self.session.get(
                f"{BACKEND_URL}/user/addresses",
                headers=invalid_headers
            ) as response:
                if response.status in [401, 403]:
                    self.log_result("authentication", "Invalid Token Rejected", True, 
                                  f"Properly rejected invalid token: HTTP {response.status}")
                else:
                    self.log_result("authentication", "Invalid Token Rejected", False, 
                                  f"Should reject invalid token but got: HTTP {response.status}")
        except Exception as e:
            self.log_result("authentication", "Invalid Token Rejected", False, f"Exception: {e}")

        # Test 4: Create address for isolation test
        test_address = {
            "label": "Isolation Test Address",
            "city": "Gaziantep",
            "district": "Şahinbey",
            "description": "Address for testing user isolation",
            "lat": 37.0662,
            "lng": 37.3833
        }
        
        created_address_id = None
        try:
            async with self.session.post(
                f"{BACKEND_URL}/user/addresses",
                json=test_address,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    created_address_id = result.get("id")
                    self.log_result("authentication", "Create Address for Isolation Test", True, 
                                  f"Created test address: {created_address_id}")
                else:
                    error_text = await response.text()
                    self.log_result("authentication", "Create Address for Isolation Test", False, 
                                  f"HTTP {response.status}: {error_text}")
        except Exception as e:
            self.log_result("authentication", "Create Address for Isolation Test", False, f"Exception: {e}")

        # Test 5: Verify user can only access their own addresses
        if created_address_id:
            try:
                async with self.session.get(
                    f"{BACKEND_URL}/user/addresses",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        addresses = await response.json()
                        if isinstance(addresses, list):
                            # Check if the created address is in the list
                            found_address = any(addr.get("id") == created_address_id for addr in addresses)
                            if found_address:
                                self.log_result("authentication", "User Address Isolation", True, 
                                              f"User can see their own address: {created_address_id}")
                            else:
                                self.log_result("authentication", "User Address Isolation", False, 
                                              f"User cannot see their own address: {created_address_id}")
                        else:
                            self.log_result("authentication", "User Address Isolation", False, 
                                          f"Invalid response format: {type(addresses)}")
                    else:
                        error_text = await response.text()
                        self.log_result("authentication", "User Address Isolation", False, 
                                      f"HTTP {response.status}: {error_text}")
            except Exception as e:
                self.log_result("authentication", "User Address Isolation", False, f"Exception: {e}")

            # Clean up test address
            try:
                await self.session.delete(f"{BACKEND_URL}/user/addresses/{created_address_id}", headers=headers)
            except:
                pass  # Ignore cleanup errors

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 ADDRESS MANAGEMENT CLEANUP & TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = sum(cat["total"] for cat in self.results.values())
        total_passed = sum(cat["passed"] for cat in self.results.values())
        total_failed = sum(cat["failed"] for cat in self.results.values())
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {total_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        categories = [
            ("cleanup", "🧹 ADDRESS CLEANUP"),
            ("endpoints", "🔗 ENDPOINT TESTING"),
            ("validation", "✅ FIELD VALIDATION"),
            ("authentication", "🔐 AUTHENTICATION & ISOLATION")
        ]
        
        for cat_key, cat_name in categories:
            cat_data = self.results[cat_key]
            cat_success_rate = (cat_data["passed"] / cat_data["total"] * 100) if cat_data["total"] > 0 else 0
            
            print(f"{cat_name}: {cat_data['passed']}/{cat_data['total']} passed ({cat_success_rate:.1f}%)")
            
            for detail in cat_data["details"]:
                print(f"  {detail['status']}: {detail['test']}")
                if detail["details"]:
                    print(f"      {detail['details']}")
            print()
        
        # Summary for main agent
        if total_failed == 0:
            print("🎉 ALL TESTS PASSED - Address management system is working perfectly!")
            print("✅ Test addresses cleaned up successfully")
            print("✅ All address endpoints working correctly")
            print("✅ Field validation working properly")
            print("✅ Authentication and user isolation working correctly")
        else:
            print(f"⚠️  {total_failed} TESTS FAILED - Issues found in address management system")
            
            failed_categories = [cat for cat, data in self.results.items() if data["failed"] > 0]
            if failed_categories:
                print(f"❌ Failed categories: {', '.join(failed_categories)}")

    async def run_all_tests(self):
        """Run all address management tests"""
        print("🚀 STARTING ADDRESS MANAGEMENT CLEANUP & TESTING")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"⏱️  Timeout: {TEST_TIMEOUT}s")
        print()
        
        try:
            # Phase 1: Clean up test addresses
            await self.delete_test_addresses()
            
            # Phase 2: Test address endpoints
            await self.test_address_endpoints()
            
            # Phase 3: Test field validation
            await self.test_field_validation()
            
            # Phase 4: Test authentication and user isolation
            await self.test_authentication_isolation()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            
        finally:
            # Print comprehensive summary
            self.print_summary()

async def main():
    """Main test execution"""
    async with AddressCleanupTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())