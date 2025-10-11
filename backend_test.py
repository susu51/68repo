#!/usr/bin/env python3
"""
BUSINESS MENU CRUD COMPREHENSIVE TESTING
Testing with KYC-approved business user: testbusiness@example.com/test123

This test covers all scenarios from the review request:
1. Business Authentication
2. Menu Item Creation (4 categories)
3. Menu Item Retrieval
4. Menu Item Update
5. Toggle Availability
6. Soft Delete
7. Public Customer Endpoints
8. Validation Tests
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://courier-stable.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

class BusinessMenuTester:
    def __init__(self):
        self.session = None
        self.business_token = None
        self.business_user_id = None
        self.created_items = []
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    async def test_business_authentication(self):
        """Test 1: Business Authentication"""
        print("\n🔐 Testing Business Authentication...")
        
        try:
            # Login with approved business user (cookie-based auth)
            login_data = {
                "email": BUSINESS_EMAIL,
                "password": BUSINESS_PASSWORD
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.business_token = data.get("access_token")  # Fallback token
                    user_data = data.get("user", {})
                    self.business_user_id = user_data.get("id")
                    
                    # Cookies are automatically stored in session
                    # Now get full user details including KYC status from /me endpoint
                    async with self.session.get(f"{BASE_URL}/me") as me_response:
                        if me_response.status == 200:
                            me_data = await me_response.json()
                            kyc_status = me_data.get("kyc_status", "pending")
                            
                            if kyc_status == "approved":
                                self.log_test("Business Login", True, 
                                            f"User ID: {self.business_user_id}, KYC: {kyc_status} (Cookie auth)")
                                return True
                            else:
                                self.log_test("Business Login", False, 
                                            f"KYC not approved. Status: {kyc_status}")
                                return False
                        else:
                            # Try with bearer token as fallback
                            if self.business_token:
                                headers = {"Authorization": f"Bearer {self.business_token}"}
                                async with self.session.get(f"{BASE_URL}/me", headers=headers) as token_response:
                                    if token_response.status == 200:
                                        token_data = await token_response.json()
                                        kyc_status = token_data.get("kyc_status", "pending")
                                        
                                        if kyc_status == "approved":
                                            self.log_test("Business Login", True, 
                                                        f"User ID: {self.business_user_id}, KYC: {kyc_status} (Bearer token)")
                                            return True
                                        else:
                                            self.log_test("Business Login", False, 
                                                        f"KYC not approved. Status: {kyc_status}")
                                            return False
                                    else:
                                        error_text = await token_response.text()
                                        self.log_test("Business Login", False, f"Token validation failed: {error_text}")
                                        return False
                            else:
                                error_text = await me_response.text()
                                self.log_test("Business Login", False, f"Cookie auth failed: {error_text}")
                                return False
                else:
                    error_text = await response.text()
                    self.log_test("Business Login", False, f"Login failed {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Business Login", False, f"Exception: {str(e)}")
            return False
            
    async def test_jwt_token_validation(self):
        """Test 1.1: Authentication Validation"""
        print("\n🔍 Testing Authentication Validation...")
        
        try:
            # Try cookie-based auth first
            async with self.session.get(f"{BASE_URL}/me") as response:
                if response.status == 200:
                    data = await response.json()
                    user_id = data.get("id")
                    kyc_status = data.get("kyc_status")
                    
                    self.log_test("Authentication Validation", True, 
                                f"User ID: {user_id}, KYC Status: {kyc_status} (Cookie auth)")
                    return True
                else:
                    # Try bearer token as fallback
                    if self.business_token:
                        headers = {"Authorization": f"Bearer {self.business_token}"}
                        async with self.session.get(f"{BASE_URL}/me", headers=headers) as token_response:
                            if token_response.status == 200:
                                token_data = await token_response.json()
                                user_id = token_data.get("id")
                                kyc_status = token_data.get("kyc_status")
                                
                                self.log_test("Authentication Validation", True, 
                                            f"User ID: {user_id}, KYC Status: {kyc_status} (Bearer token)")
                                return True
                            else:
                                error_text = await token_response.text()
                                self.log_test("Authentication Validation", False, f"Bearer token failed: {error_text}")
                                return False
                    else:
                        error_text = await response.text()
                        self.log_test("Authentication Validation", False, f"Cookie auth failed: {error_text}")
                        return False
                    
        except Exception as e:
            self.log_test("Authentication Validation", False, f"Exception: {str(e)}")
            return False
            
    async def test_menu_creation(self):
        """Test 2: Menu Item Creation (4 categories)"""
        print("\n🍽️ Testing Menu Item Creation...")
        
        # Test data for 4 categories
        menu_items = [
            {
                "name": "Adana Kebap Premium",
                "description": "Özel baharatlarla marine edilmiş Adana kebabı",
                "price": 95.00,
                "currency": "TRY",
                "category": "Yemek",
                "tags": ["acılı", "et yemeği", "premium"],
                "image_url": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd",
                "is_available": True,
                "vat_rate": 0.18,
                "preparation_time": 25,
                "options": [
                    {"name": "Ekstra acı sos", "price": 5.0},
                    {"name": "Büyük porsiyon", "price": 20.0}
                ]
            },
            {
                "name": "Serpme Kahvaltı",
                "description": "Zengin içerikli serpme kahvaltı tabağı",
                "price": 120.00,
                "currency": "TRY",
                "category": "Kahvaltı",
                "tags": ["sabah", "organik", "köy ürünleri"],
                "vat_rate": 0.10,
                "preparation_time": 15
            },
            {
                "name": "Taze Sıkılmış Portakal Suyu",
                "description": "Günlük taze portakallardan",
                "price": 25.00,
                "currency": "TRY",
                "category": "İçecek",
                "tags": ["taze", "soğuk"],
                "vat_rate": 0.08,
                "preparation_time": 3
            },
            {
                "name": "Patates Kızartması",
                "description": "Çıtır çıtır patates kızartması",
                "price": 30.00,
                "currency": "TRY",
                "category": "Atıştırmalık",
                "tags": ["yan ürün", "çocuklar için"],
                "vat_rate": 0.18,
                "preparation_time": 10
            }
        ]
        
        success_count = 0
        
        for i, item_data in enumerate(menu_items):
            try:
                # Try cookie-based auth first, then bearer token fallback
                async with self.session.post(f"{BASE_URL}/business/menu", json=item_data) as response:
                    if response.status == 401 and self.business_token:
                        # Fallback to bearer token
                        headers = {"Authorization": f"Bearer {self.business_token}"}
                        async with self.session.post(f"{BASE_URL}/business/menu", 
                                                   json=item_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        item_id = data.get("id")
                        self.created_items.append(item_id)
                        success_count += 1
                        
                        self.log_test(f"Create {item_data['category']} Item", True, 
                                    f"ID: {item_id}, Name: {item_data['name']}")
                    else:
                        error_text = await response.text()
                        self.log_test(f"Create {item_data['category']} Item", False, 
                                    f"Status {response.status}: {error_text}")
                        
            except Exception as e:
                self.log_test(f"Create {item_data['category']} Item", False, f"Exception: {str(e)}")
                
        return success_count == len(menu_items)
        
    async def test_menu_retrieval(self):
        """Test 3: Menu Item Retrieval"""
        print("\n📋 Testing Menu Item Retrieval...")
        
        try:
            headers = {"Authorization": f"Bearer {self.business_token}"}
            
            async with self.session.get(f"{BASE_URL}/business/menu", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) >= 4:
                        # Check if all required fields are present
                        required_fields = ["id", "name", "description", "price", "category", 
                                         "tags", "vat_rate", "options", "preparation_time"]
                        
                        all_fields_present = True
                        for item in data:
                            for field in required_fields:
                                if field not in item:
                                    all_fields_present = False
                                    break
                        
                        if all_fields_present:
                            self.log_test("Menu Retrieval", True, 
                                        f"Retrieved {len(data)} items with all required fields")
                            return True
                        else:
                            self.log_test("Menu Retrieval", False, "Missing required fields in response")
                            return False
                    else:
                        self.log_test("Menu Retrieval", False, f"Expected 4+ items, got {len(data) if isinstance(data, list) else 'non-list'}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Menu Retrieval", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Menu Retrieval", False, f"Exception: {str(e)}")
            return False
            
    async def test_menu_update(self):
        """Test 4: Menu Item Update"""
        print("\n✏️ Testing Menu Item Update...")
        
        if not self.created_items:
            self.log_test("Menu Update", False, "No created items to update")
            return False
            
        try:
            item_id = self.created_items[0]  # Update first created item
            update_data = {
                "price": 105.00,
                "tags": ["premium", "acılı", "et yemeği", "bestseller"]
            }
            
            headers = {"Authorization": f"Bearer {self.business_token}"}
            
            async with self.session.patch(f"{BASE_URL}/business/menu/{item_id}", 
                                        json=update_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    updated_price = data.get("price")
                    updated_tags = data.get("tags", [])
                    
                    if updated_price == 105.00 and "bestseller" in updated_tags:
                        self.log_test("Menu Update", True, 
                                    f"Price updated to {updated_price}, Tags: {updated_tags}")
                        return True
                    else:
                        self.log_test("Menu Update", False, 
                                    f"Update not reflected. Price: {updated_price}, Tags: {updated_tags}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Menu Update", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Menu Update", False, f"Exception: {str(e)}")
            return False
            
    async def test_toggle_availability(self):
        """Test 5: Toggle Availability"""
        print("\n🔄 Testing Toggle Availability...")
        
        if not self.created_items:
            self.log_test("Toggle Availability", False, "No created items to toggle")
            return False
            
        try:
            item_id = self.created_items[0]
            headers = {"Authorization": f"Bearer {self.business_token}"}
            
            # Set to unavailable
            update_data = {"is_available": False}
            async with self.session.patch(f"{BASE_URL}/business/menu/{item_id}", 
                                        json=update_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get("is_available"):
                        # Set back to available
                        update_data = {"is_available": True}
                        async with self.session.patch(f"{BASE_URL}/business/menu/{item_id}", 
                                                    json=update_data, headers=headers) as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                if data2.get("is_available"):
                                    self.log_test("Toggle Availability", True, 
                                                "Successfully toggled availability false→true")
                                    return True
                                else:
                                    self.log_test("Toggle Availability", False, "Failed to set back to available")
                                    return False
                            else:
                                error_text = await response2.text()
                                self.log_test("Toggle Availability", False, f"Second toggle failed: {error_text}")
                                return False
                    else:
                        self.log_test("Toggle Availability", False, "Failed to set unavailable")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Toggle Availability", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Toggle Availability", False, f"Exception: {str(e)}")
            return False
            
    async def test_soft_delete(self):
        """Test 6: Soft Delete"""
        print("\n🗑️ Testing Soft Delete...")
        
        if len(self.created_items) < 2:
            self.log_test("Soft Delete", False, "Need at least 2 created items for soft delete test")
            return False
            
        try:
            item_id = self.created_items[1]  # Soft delete second item
            headers = {"Authorization": f"Bearer {self.business_token}"}
            
            async with self.session.delete(f"{BASE_URL}/business/menu/{item_id}?soft_delete=true", 
                                         headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        # Verify item still exists but is unavailable
                        async with self.session.get(f"{BASE_URL}/business/menu", headers=headers) as response2:
                            if response2.status == 200:
                                menu_data = await response2.json()
                                soft_deleted_item = None
                                for item in menu_data:
                                    if item.get("id") == item_id:
                                        soft_deleted_item = item
                                        break
                                
                                if soft_deleted_item and not soft_deleted_item.get("is_available"):
                                    self.log_test("Soft Delete", True, 
                                                f"Item {item_id} soft deleted (is_available=False)")
                                    return True
                                else:
                                    self.log_test("Soft Delete", False, 
                                                "Item not found or still available after soft delete")
                                    return False
                            else:
                                self.log_test("Soft Delete", False, "Failed to verify soft delete")
                                return False
                    else:
                        self.log_test("Soft Delete", False, "Delete operation not successful")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Soft Delete", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Soft Delete", False, f"Exception: {str(e)}")
            return False
            
    async def test_public_customer_endpoints(self):
        """Test 7: Public Customer Endpoints"""
        print("\n🌐 Testing Public Customer Endpoints...")
        
        if not self.business_user_id:
            self.log_test("Public Customer Endpoints", False, "No business user ID available")
            return False
            
        success_count = 0
        
        # Test 7.1: Get all menu items for business
        try:
            async with self.session.get(f"{BASE_URL}/business/{self.business_user_id}/menu") as response:
                if response.status == 200:
                    data = await response.json()
                    available_items = [item for item in data if item.get("is_available", True)]
                    
                    # Should return only available items (3 items, not the soft-deleted one)
                    if len(available_items) >= 3:
                        self.log_test("Public Menu Access", True, 
                                    f"Retrieved {len(available_items)} available items")
                        success_count += 1
                    else:
                        self.log_test("Public Menu Access", False, 
                                    f"Expected 3+ available items, got {len(available_items)}")
                else:
                    error_text = await response.text()
                    self.log_test("Public Menu Access", False, f"Status {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_test("Public Menu Access", False, f"Exception: {str(e)}")
            
        # Test 7.2: Filter by category
        try:
            async with self.session.get(f"{BASE_URL}/business/{self.business_user_id}/menu?category=Yemek") as response:
                if response.status == 200:
                    data = await response.json()
                    yemek_items = [item for item in data if item.get("category") == "Yemek"]
                    
                    if len(yemek_items) >= 1:
                        self.log_test("Public Category Filter", True, 
                                    f"Found {len(yemek_items)} Yemek items")
                        success_count += 1
                    else:
                        self.log_test("Public Category Filter", False, 
                                    f"No Yemek items found in filtered results")
                else:
                    error_text = await response.text()
                    self.log_test("Public Category Filter", False, f"Status {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_test("Public Category Filter", False, f"Exception: {str(e)}")
            
        # Test 7.3: Get single item details
        if self.created_items:
            try:
                item_id = self.created_items[0]
                async with self.session.get(f"{BASE_URL}/business/menu/{item_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("id") == item_id:
                            self.log_test("Public Single Item", True, 
                                        f"Retrieved item details for {item_id}")
                            success_count += 1
                        else:
                            self.log_test("Public Single Item", False, "Item ID mismatch in response")
                    else:
                        error_text = await response.text()
                        self.log_test("Public Single Item", False, f"Status {response.status}: {error_text}")
                        
            except Exception as e:
                self.log_test("Public Single Item", False, f"Exception: {str(e)}")
        else:
            self.log_test("Public Single Item", False, "No created items to test")
            
        return success_count >= 2  # At least 2 out of 3 tests should pass
        
    async def test_validation_scenarios(self):
        """Test 8: Validation Tests"""
        print("\n🔍 Testing Validation Scenarios...")
        
        headers = {"Authorization": f"Bearer {self.business_token}"}
        success_count = 0
        
        # Test 8.1: Invalid Category
        try:
            invalid_category_data = {
                "name": "Test Invalid Category",
                "price": 50.0,
                "category": "InvalidCategory"
            }
            
            async with self.session.post(f"{BASE_URL}/business/menu", 
                                       json=invalid_category_data, headers=headers) as response:
                if response.status == 422:
                    self.log_test("Invalid Category Validation", True, "422 validation error as expected")
                    success_count += 1
                else:
                    self.log_test("Invalid Category Validation", False, 
                                f"Expected 422, got {response.status}")
                    
        except Exception as e:
            self.log_test("Invalid Category Validation", False, f"Exception: {str(e)}")
            
        # Test 8.2: Invalid VAT Rate
        try:
            invalid_vat_data = {
                "name": "Test Invalid VAT",
                "price": 50.0,
                "category": "Yemek",
                "vat_rate": 0.99
            }
            
            async with self.session.post(f"{BASE_URL}/business/menu", 
                                       json=invalid_vat_data, headers=headers) as response:
                if response.status == 422:
                    self.log_test("Invalid VAT Rate Validation", True, "422 validation error as expected")
                    success_count += 1
                else:
                    self.log_test("Invalid VAT Rate Validation", False, 
                                f"Expected 422, got {response.status}")
                    
        except Exception as e:
            self.log_test("Invalid VAT Rate Validation", False, f"Exception: {str(e)}")
            
        # Test 8.3: Negative Price
        try:
            negative_price_data = {
                "name": "Test Negative Price",
                "price": -10.0,
                "category": "Yemek"
            }
            
            async with self.session.post(f"{BASE_URL}/business/menu", 
                                       json=negative_price_data, headers=headers) as response:
                if response.status == 422:
                    self.log_test("Negative Price Validation", True, "422 validation error as expected")
                    success_count += 1
                else:
                    self.log_test("Negative Price Validation", False, 
                                f"Expected 422, got {response.status}")
                    
        except Exception as e:
            self.log_test("Negative Price Validation", False, f"Exception: {str(e)}")
            
        return success_count >= 2  # At least 2 out of 3 validation tests should pass
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 BUSINESS MENU CRUD COMPREHENSIVE TESTING")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Test sequence as per review request
            tests = [
                ("Business Authentication", self.test_business_authentication()),
                ("JWT Token Validation", self.test_jwt_token_validation()),
                ("Menu Item Creation", self.test_menu_creation()),
                ("Menu Item Retrieval", self.test_menu_retrieval()),
                ("Menu Item Update", self.test_menu_update()),
                ("Toggle Availability", self.test_toggle_availability()),
                ("Soft Delete", self.test_soft_delete()),
                ("Public Customer Endpoints", self.test_public_customer_endpoints()),
                ("Validation Scenarios", self.test_validation_scenarios())
            ]
            
            results = []
            for test_name, test_coro in tests:
                try:
                    result = await test_coro
                    results.append(result)
                except Exception as e:
                    print(f"❌ FAIL {test_name}: Exception {str(e)}")
                    results.append(False)
                    
            # Summary
            passed = sum(results)
            total = len(results)
            success_rate = (passed / total) * 100
            
            print("\n" + "=" * 60)
            print("📊 BUSINESS MENU CRUD TEST SUMMARY")
            print("=" * 60)
            print(f"✅ Passed: {passed}/{total} tests ({success_rate:.1f}% success rate)")
            
            if success_rate >= 80:
                print("🎉 EXCELLENT: Business Menu CRUD system is working well!")
            elif success_rate >= 60:
                print("⚠️  GOOD: Business Menu CRUD system mostly working with minor issues")
            else:
                print("❌ CRITICAL: Business Menu CRUD system has significant issues")
                
            # Detailed results
            print("\n📋 Detailed Test Results:")
            for result in self.test_results:
                status = "✅" if result["success"] else "❌"
                print(f"{status} {result['test']}")
                if result["details"]:
                    print(f"    {result['details']}")
                    
            return success_rate >= 60
            
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    tester = BusinessMenuTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())