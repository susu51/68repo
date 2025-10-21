#!/usr/bin/env python3
"""
Business Panel Backend Testing - New Endpoints
Test the newly implemented Business Panel backend endpoints with testbusiness@example.com/test123 credentials.

CRITICAL: Check testbusiness@example.com KYC status first. If kyc_status='pending', skip KYC-protected tests.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ai-order-debug.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔗 Testing Business Panel Backend at: {API_BASE}")
print(f"📅 Test started at: {datetime.now().isoformat()}")

class BusinessPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.business_user = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'error': error
        })
        print(f"{status} {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ❌ Error: {error}")
        print()

    def authenticate_business(self):
        """Authenticate business user and check KYC status"""
        print("🔐 STEP 1: Business Authentication & KYC Check")
        print("=" * 60)
        
        try:
            # Login with business credentials
            login_data = {
                "email": "testbusiness@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.business_user = data.get('user', {})
                
                # Extract JWT token from response (cookie-based login returns JWT token too)
                self.business_token = data.get('access_token')
                if self.business_token:
                    self.session.headers.update({'Authorization': f'Bearer {self.business_token}'})
                    self.log_test("Business Login (JWT Token)", True, 
                                f"Token length: {len(self.business_token)} chars, User ID: {self.business_user.get('id')}")
                else:
                    # Check if cookies are set (fallback)
                    if 'access_token' in [cookie.name for cookie in self.session.cookies]:
                        self.log_test("Business Login (Cookie Auth)", True, 
                                    f"User ID: {self.business_user.get('id')}, Role: {self.business_user.get('role')}")
                    else:
                        self.log_test("Business Login", False, error="No access token or cookies found")
                
                # Check KYC status
                kyc_status = self.business_user.get('kyc_status', 'unknown')
                print(f"🏢 Business User Details:")
                print(f"   📧 Email: {self.business_user.get('email')}")
                print(f"   🆔 ID: {self.business_user.get('id')}")
                print(f"   🏪 Business Name: {self.business_user.get('business_name', 'Not set')}")
                print(f"   ✅ KYC Status: {kyc_status}")
                print()
                
                if kyc_status == 'pending':
                    print("⚠️  WARNING: Business KYC status is 'pending'")
                    print("   KYC-protected endpoints will be skipped")
                    print("   Admin approval needed for full testing")
                    print()
                
                return True
                
            else:
                self.log_test("Business Login", False, 
                            f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Business Login", False, error=str(e))
            return False

    def test_business_profile_endpoints(self):
        """Test Business Profile Endpoints (NEW)"""
        print("🏢 STEP 2: Business Profile Endpoints (NEW)")
        print("=" * 60)
        
        # Check if KYC approved for protected endpoints
        kyc_status = self.business_user.get('kyc_status', 'unknown')
        if kyc_status == 'pending':
            print("⚠️  Skipping KYC-protected profile endpoints (KYC status: pending)")
            print("   Admin approval required to test these endpoints")
            print()
            return
        
        # Test GET /api/business/profile
        try:
            response = self.session.get(f"{API_BASE}/business/profile")
            
            if response.status_code == 200:
                profile_data = response.json()
                expected_fields = [
                    'business_name', 'phone', 'address', 'city', 'district', 
                    'description', 'opening_hours', 'delivery_radius_km', 
                    'min_order_amount', 'delivery_fee'
                ]
                
                present_fields = [field for field in expected_fields if field in profile_data]
                missing_fields = [field for field in expected_fields if field not in profile_data]
                
                details = f"Fields present: {len(present_fields)}/{len(expected_fields)}"
                if missing_fields:
                    details += f", Missing: {missing_fields}"
                
                self.log_test("GET /api/business/profile", True, details)
                
                # Store profile for update test
                self.original_profile = profile_data
                
            else:
                self.log_test("GET /api/business/profile", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/business/profile", False, error=str(e))
        
        # Test PATCH /api/business/profile
        try:
            # Test profile update with sample data
            update_data = {
                "business_name": "Updated Test Restaurant",
                "phone": "+905551234567",
                "opening_hours": "09:00-22:00",
                "delivery_radius_km": 15.5
            }
            
            response = self.session.patch(f"{API_BASE}/business/profile", json=update_data)
            
            if response.status_code == 200:
                updated_profile = response.json()
                
                # Verify updates were applied
                updates_applied = []
                for key, value in update_data.items():
                    if updated_profile.get(key) == value:
                        updates_applied.append(key)
                
                details = f"Updates applied: {len(updates_applied)}/{len(update_data)} fields"
                if len(updates_applied) == len(update_data):
                    self.log_test("PATCH /api/business/profile", True, details)
                else:
                    self.log_test("PATCH /api/business/profile", False, 
                                details, "Not all updates were applied")
                
            else:
                self.log_test("PATCH /api/business/profile", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("PATCH /api/business/profile", False, error=str(e))

    def test_business_orders_endpoints(self):
        """Test Business Orders Endpoints (EXISTING - Verify Still Working)"""
        print("📦 STEP 3: Business Orders Endpoints (EXISTING)")
        print("=" * 60)
        
        # Check if KYC approved for protected endpoints
        kyc_status = self.business_user.get('kyc_status', 'unknown')
        if kyc_status == 'pending':
            print("⚠️  Skipping KYC-protected order endpoints (KYC status: pending)")
            print("   Admin approval required to test these endpoints")
            print()
            return
        
        # Test GET /api/business/orders/incoming
        try:
            response = self.session.get(f"{API_BASE}/business/orders/incoming")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                details = f"Found {len(orders)} incoming orders"
                if orders:
                    # Check first order structure
                    first_order = orders[0]
                    required_fields = ['id', 'customer_name', 'total_amount', 'status', 'items']
                    present_fields = [field for field in required_fields if field in first_order]
                    details += f", Order fields: {len(present_fields)}/{len(required_fields)}"
                
                self.log_test("GET /api/business/orders/incoming", True, details)
                
                # Store order ID for status update test
                if orders:
                    self.test_order_id = orders[0].get('id') or orders[0].get('order_id')
                
            else:
                self.log_test("GET /api/business/orders/incoming", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/business/orders/incoming", False, error=str(e))
        
        # Test GET /api/business/orders/active
        try:
            response = self.session.get(f"{API_BASE}/business/orders/active")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                details = f"Found {len(orders)} active orders"
                self.log_test("GET /api/business/orders/active", True, details)
                
            else:
                self.log_test("GET /api/business/orders/active", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/business/orders/active", False, error=str(e))
        
        # Test PATCH /api/business/orders/{order_id}/status (if we have an order)
        if hasattr(self, 'test_order_id') and self.test_order_id:
            try:
                status_update = {"status": "confirmed"}
                response = self.session.patch(
                    f"{API_BASE}/business/orders/{self.test_order_id}/status", 
                    json=status_update
                )
                
                if response.status_code == 200:
                    result = response.json()
                    details = f"Order {self.test_order_id} status updated to 'confirmed'"
                    self.log_test("PATCH /api/business/orders/{order_id}/status", True, details)
                    
                else:
                    self.log_test("PATCH /api/business/orders/{order_id}/status", False, 
                                f"Status: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test("PATCH /api/business/orders/{order_id}/status", False, error=str(e))
        else:
            print("⚠️  No orders available for status update test")
            print()

    def test_business_menu_endpoints(self):
        """Test Business Menu Endpoints (EXISTING - Quick Smoke Test)"""
        print("🍽️  STEP 4: Business Menu Endpoints (EXISTING)")
        print("=" * 60)
        
        # Check if KYC approved for protected endpoints
        kyc_status = self.business_user.get('kyc_status', 'unknown')
        if kyc_status == 'pending':
            print("⚠️  Skipping KYC-protected menu endpoints (KYC status: pending)")
            print("   Admin approval required to test these endpoints")
            print()
            return
        
        # Test GET /api/business/menu
        try:
            response = self.session.get(f"{API_BASE}/business/menu")
            
            if response.status_code == 200:
                menu_data = response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get('items', [])
                
                details = f"Found {len(menu_items)} menu items"
                self.log_test("GET /api/business/menu", True, details)
                
            else:
                self.log_test("GET /api/business/menu", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/business/menu", False, error=str(e))
        
        # Test POST /api/business/menu (create test item)
        try:
            test_menu_item = {
                "name": "Test Menu Item",  # Note: API expects 'name' field
                "description": "Test description for backend testing",
                "price": 25.50,
                "category": "Yemek",
                "preparation_time": 20,
                "is_available": True
            }
            
            response = self.session.post(f"{API_BASE}/business/menu", json=test_menu_item)
            
            if response.status_code in [200, 201]:
                created_item = response.json()
                details = f"Created menu item: {created_item.get('name', 'Unknown')}"
                self.log_test("POST /api/business/menu", True, details)
                
                # Store item ID for cleanup
                self.test_menu_item_id = created_item.get('id')
                
            else:
                self.log_test("POST /api/business/menu", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("POST /api/business/menu", False, error=str(e))

    def test_business_stats_endpoints(self):
        """Test Business Stats Endpoints (EXISTING - Verify)"""
        print("📊 STEP 5: Business Stats Endpoints (EXISTING)")
        print("=" * 60)
        
        # Check if KYC approved for protected endpoints
        kyc_status = self.business_user.get('kyc_status', 'unknown')
        if kyc_status == 'pending':
            print("⚠️  Skipping KYC-protected stats endpoints (KYC status: pending)")
            print("   Admin approval required to test these endpoints")
            print()
            return
        
        # Test GET /api/business/stats
        try:
            response = self.session.get(f"{API_BASE}/business/stats")
            
            if response.status_code == 200:
                stats_data = response.json()
                
                # Check for expected stats structure
                expected_sections = ['today', 'week', 'month']
                present_sections = [section for section in expected_sections if section in stats_data]
                
                details = f"Stats sections: {len(present_sections)}/{len(expected_sections)}"
                if 'today' in stats_data:
                    today_stats = stats_data['today']
                    details += f", Today: {today_stats.get('orders', 0)} orders, ₺{today_stats.get('revenue', 0)} revenue"
                
                self.log_test("GET /api/business/stats", True, details)
                
            else:
                self.log_test("GET /api/business/stats", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("GET /api/business/stats", False, error=str(e))

    def test_error_handling(self):
        """Test Error Handling Scenarios"""
        print("🚨 STEP 6: Error Handling Tests")
        print("=" * 60)
        
        # Test unauthorized access (without authentication)
        try:
            # Create a new session without auth
            unauth_session = requests.Session()
            response = unauth_session.get(f"{API_BASE}/business/profile")
            
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Access Protection", True, 
                            f"Correctly blocked with {response.status_code}")
            else:
                self.log_test("Unauthorized Access Protection", False, 
                            f"Expected 401/403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Unauthorized Access Protection", False, error=str(e))
        
        # Test invalid field updates (if KYC approved)
        kyc_status = self.business_user.get('kyc_status', 'unknown')
        if kyc_status != 'pending':
            try:
                invalid_data = {
                    "delivery_radius_km": "invalid_number",  # Should be numeric
                    "min_order_amount": -10  # Should be positive
                }
                
                response = self.session.patch(f"{API_BASE}/business/profile", json=invalid_data)
                
                if response.status_code == 422:
                    self.log_test("Invalid Field Validation", True, 
                                "Correctly rejected invalid data with 422")
                else:
                    self.log_test("Invalid Field Validation", False, 
                                f"Expected 422, got {response.status_code}")
                    
            except Exception as e:
                self.log_test("Invalid Field Validation", False, error=str(e))

    def cleanup_test_data(self):
        """Clean up any test data created during testing"""
        print("🧹 STEP 7: Cleanup Test Data")
        print("=" * 60)
        
        # Delete test menu item if created
        if hasattr(self, 'test_menu_item_id') and self.test_menu_item_id:
            try:
                response = self.session.delete(f"{API_BASE}/business/menu/{self.test_menu_item_id}")
                
                if response.status_code in [200, 204]:
                    self.log_test("Cleanup Test Menu Item", True, 
                                f"Deleted item {self.test_menu_item_id}")
                else:
                    print(f"⚠️  Could not delete test menu item: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")

    def print_summary(self):
        """Print test summary"""
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"   • {test['test']}: {test['error']}")
            print()
        
        # KYC Status Summary
        kyc_status = self.business_user.get('kyc_status', 'unknown') if self.business_user else 'unknown'
        print(f"🏢 Business KYC Status: {kyc_status}")
        
        if kyc_status == 'pending':
            print("⚠️  NOTE: Many tests were skipped due to pending KYC status")
            print("   Admin approval needed for complete testing")
        elif kyc_status == 'approved':
            print("✅ KYC approved - All endpoints were testable")
        else:
            print("❓ Unknown KYC status - Some tests may have been limited")
        
        print()
        print(f"🏁 Testing completed at: {datetime.now().isoformat()}")

    def run_all_tests(self):
        """Run all business panel backend tests"""
        print("🚀 BUSINESS PANEL BACKEND TESTING")
        print("=" * 60)
        print("Testing newly implemented Business Panel endpoints")
        print("Credentials: testbusiness@example.com/test123")
        print()
        
        # Step 1: Authentication and KYC check
        if not self.authenticate_business():
            print("❌ Authentication failed - cannot proceed with testing")
            return
        
        # Step 2-6: Run all endpoint tests
        self.test_business_profile_endpoints()
        self.test_business_orders_endpoints()
        self.test_business_menu_endpoints()
        self.test_business_stats_endpoints()
        self.test_error_handling()
        
        # Step 7: Cleanup
        self.cleanup_test_data()
        
        # Final summary
        self.print_summary()

if __name__ == "__main__":
    tester = BusinessPanelTester()
    tester.run_all_tests()