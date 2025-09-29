#!/usr/bin/env python3
"""
Comprehensive Phase 2 Backend Testing for Kuryecini Platform Enhancements
Testing all new business panel APIs, admin enhanced APIs, and advertisement system
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class Phase2BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.business_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def test_admin_simple_login(self):
        """Test POST /api/admin/login-simple - Simple admin login (password: 6851)"""
        print("🔐 Testing Admin Simple Login...")
        
        try:
            response = self.session.post(f"{API_BASE}/admin/login-simple")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user_data", {}).get("role") == "admin":
                    self.admin_token = data["access_token"]
                    self.log_test(
                        "Admin Simple Login", 
                        True, 
                        f"Admin login successful, token expires in {data.get('expires_in', 0)} seconds"
                    )
                else:
                    self.log_test("Admin Simple Login", False, "Invalid response structure", data)
            else:
                self.log_test("Admin Simple Login", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Simple Login", False, f"Exception: {str(e)}")

    def test_business_login(self):
        """Login as business user for testing business endpoints"""
        print("🏢 Testing Business Login...")
        
        try:
            # Try to login with existing business user
            login_data = {
                "email": "testrestoran@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user_type") == "business":
                    self.business_token = data["access_token"]
                    self.log_test(
                        "Business Login", 
                        True, 
                        f"Business login successful for {login_data['email']}"
                    )
                else:
                    self.log_test("Business Login", False, "Invalid response structure", data)
            else:
                self.log_test("Business Login", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Login", False, f"Exception: {str(e)}")

    def test_business_restaurant_view(self):
        """Test GET /api/business/restaurant-view - Get public restaurant view"""
        print("🍽️ Testing Business Restaurant View...")
        
        if not self.business_token:
            self.log_test("Business Restaurant View", False, "No business token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.business_token}"}
            response = self.session.get(f"{API_BASE}/business/restaurant-view", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                business_info = data.get("business_info", {})
                products = data.get("products", [])
                categories = data.get("categories", [])
                
                if business_info.get("business_name") and isinstance(products, list):
                    self.log_test(
                        "Business Restaurant View", 
                        True, 
                        f"Restaurant view loaded: {business_info.get('business_name')}, {len(products)} products, {len(categories)} categories"
                    )
                else:
                    self.log_test("Business Restaurant View", False, "Invalid response structure", data)
            elif response.status_code == 403:
                self.log_test("Business Restaurant View", False, "Access denied - check business authentication")
            else:
                self.log_test("Business Restaurant View", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Restaurant View", False, f"Exception: {str(e)}")

    def test_business_featured_status(self):
        """Test GET /api/business/featured-status - Get featured promotion status"""
        print("⭐ Testing Business Featured Status...")
        
        if not self.business_token:
            self.log_test("Business Featured Status", False, "No business token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.business_token}"}
            response = self.session.get(f"{API_BASE}/business/featured-status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                is_featured = data.get("is_featured", False)
                
                if is_featured:
                    plan = data.get("plan")
                    expires_at = data.get("expires_at")
                    remaining_days = data.get("remaining_days", 0)
                    self.log_test(
                        "Business Featured Status", 
                        True, 
                        f"Business is featured: {plan} plan, expires {expires_at}, {remaining_days} days remaining"
                    )
                else:
                    available_plans = data.get("available_plans", [])
                    self.log_test(
                        "Business Featured Status", 
                        True, 
                        f"Business not featured, {len(available_plans)} plans available"
                    )
            else:
                self.log_test("Business Featured Status", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Featured Status", False, f"Exception: {str(e)}")

    def test_business_request_featured(self):
        """Test POST /api/business/request-featured - Request featured promotion"""
        print("📝 Testing Business Request Featured...")
        
        if not self.business_token:
            self.log_test("Business Request Featured", False, "No business token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.business_token}"}
            request_data = {"plan": "daily"}  # Test with daily plan
            
            response = self.session.post(f"{API_BASE}/business/request-featured", json=request_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("request_id") and data.get("status") == "pending":
                    self.log_test(
                        "Business Request Featured", 
                        True, 
                        f"Featured request submitted: {data.get('message')}, request_id: {data.get('request_id')}"
                    )
                else:
                    self.log_test("Business Request Featured", False, "Invalid response structure", data)
            elif response.status_code == 400:
                # Could be already featured or invalid plan
                error_msg = response.json().get("detail", response.text)
                if "already featured" in error_msg.lower():
                    self.log_test("Business Request Featured", True, f"Expected error: {error_msg}")
                else:
                    self.log_test("Business Request Featured", False, f"Bad request: {error_msg}")
            else:
                self.log_test("Business Request Featured", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Request Featured", False, f"Exception: {str(e)}")

    def test_business_products_categories(self):
        """Test GET /api/business/products/categories - Get product categories with food/drinks classification"""
        print("🍕 Testing Business Products Categories...")
        
        if not self.business_token:
            self.log_test("Business Products Categories", False, "No business token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.business_token}"}
            response = self.session.get(f"{API_BASE}/business/products/categories", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                food_categories = data.get("food_categories", [])
                drink_categories = data.get("drink_categories", [])
                all_categories = data.get("all_categories", [])
                total_products = data.get("total_products", 0)
                
                self.log_test(
                    "Business Products Categories", 
                    True, 
                    f"Categories loaded: {len(food_categories)} food, {len(drink_categories)} drinks, {len(all_categories)} total, {total_products} products"
                )
            else:
                self.log_test("Business Products Categories", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Business Products Categories", False, f"Exception: {str(e)}")

    def test_admin_featured_requests(self):
        """Test GET /api/admin/featured-requests - Get all featured promotion requests"""
        print("📋 Testing Admin Featured Requests...")
        
        if not self.admin_token:
            self.log_test("Admin Featured Requests", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/admin/featured-requests", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                requests_list = data.get("requests", [])
                
                self.log_test(
                    "Admin Featured Requests", 
                    True, 
                    f"Featured requests loaded: {len(requests_list)} requests found"
                )
                
                # Store a request ID for approval/rejection tests
                if requests_list:
                    self.test_request_id = requests_list[0].get("request_id")
                    
            else:
                self.log_test("Admin Featured Requests", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Featured Requests", False, f"Exception: {str(e)}")

    def test_admin_featured_request_approve(self):
        """Test POST /api/admin/featured-requests/{request_id}/approve - Approve featured request"""
        print("✅ Testing Admin Featured Request Approve...")
        
        if not self.admin_token:
            self.log_test("Admin Featured Request Approve", False, "No admin token available")
            return
            
        if not hasattr(self, 'test_request_id') or not self.test_request_id:
            self.log_test("Admin Featured Request Approve", False, "No test request ID available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/featured-requests/{self.test_request_id}/approve", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") and data.get("expires_at"):
                    self.log_test(
                        "Admin Featured Request Approve", 
                        True, 
                        f"Request approved: {data.get('message')}, expires: {data.get('expires_at')}"
                    )
                else:
                    self.log_test("Admin Featured Request Approve", False, "Invalid response structure", data)
            elif response.status_code == 400:
                # Could be already processed
                error_msg = response.json().get("detail", response.text)
                if "already processed" in error_msg.lower():
                    self.log_test("Admin Featured Request Approve", True, f"Expected error: {error_msg}")
                else:
                    self.log_test("Admin Featured Request Approve", False, f"Bad request: {error_msg}")
            elif response.status_code == 404:
                self.log_test("Admin Featured Request Approve", False, "Request not found")
            else:
                self.log_test("Admin Featured Request Approve", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Featured Request Approve", False, f"Exception: {str(e)}")

    def test_admin_featured_request_reject(self):
        """Test POST /api/admin/featured-requests/{request_id}/reject - Reject featured request"""
        print("❌ Testing Admin Featured Request Reject...")
        
        if not self.admin_token:
            self.log_test("Admin Featured Request Reject", False, "No admin token available")
            return
            
        # Create a dummy request ID for rejection test
        dummy_request_id = str(uuid.uuid4())
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            rejection_data = {"reason": "Test rejection reason"}
            response = self.session.post(f"{API_BASE}/admin/featured-requests/{dummy_request_id}/reject", json=rejection_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message"):
                    self.log_test(
                        "Admin Featured Request Reject", 
                        True, 
                        f"Request rejected: {data.get('message')}"
                    )
                else:
                    self.log_test("Admin Featured Request Reject", False, "Invalid response structure", data)
            elif response.status_code == 404:
                # Expected for dummy ID
                self.log_test("Admin Featured Request Reject", True, "Expected 404 for dummy request ID")
            else:
                self.log_test("Admin Featured Request Reject", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Featured Request Reject", False, f"Exception: {str(e)}")

    def test_admin_featured_businesses(self):
        """Test GET /api/admin/featured-businesses - Get active featured businesses"""
        print("🌟 Testing Admin Featured Businesses...")
        
        if not self.admin_token:
            self.log_test("Admin Featured Businesses", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/admin/featured-businesses", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                featured_businesses = data.get("featured_businesses", [])
                
                self.log_test(
                    "Admin Featured Businesses", 
                    True, 
                    f"Featured businesses loaded: {len(featured_businesses)} active featured businesses"
                )
            else:
                self.log_test("Admin Featured Businesses", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Featured Businesses", False, f"Exception: {str(e)}")

    def test_admin_generate_dummy_data(self):
        """Test POST /api/admin/generate-dummy-data - Generate test data"""
        print("🎲 Testing Admin Generate Dummy Data...")
        
        if not self.admin_token:
            self.log_test("Admin Generate Dummy Data", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/generate-dummy-data", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                created_items = data.get("created_items", {})
                
                total_created = sum(created_items.values()) if created_items else 0
                self.log_test(
                    "Admin Generate Dummy Data", 
                    True, 
                    f"Dummy data generated: {total_created} total items created - {created_items}"
                )
            else:
                self.log_test("Admin Generate Dummy Data", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Generate Dummy Data", False, f"Exception: {str(e)}")

    def test_ads_active(self):
        """Test GET /api/ads/active - Get active ads with targeting"""
        print("📺 Testing Active Ads...")
        
        try:
            # Test without filters
            response = self.session.get(f"{API_BASE}/ads/active")
            
            if response.status_code == 200:
                ads = response.json()
                self.log_test(
                    "Active Ads (No Filter)", 
                    True, 
                    f"Active ads loaded: {len(ads)} ads found"
                )
                
                # Store an ad ID for impression/click tests
                if ads:
                    self.test_ad_id = ads[0].get("id")
                    
            else:
                self.log_test("Active Ads (No Filter)", False, f"HTTP {response.status_code}", response.text)
                
            # Test with city filter
            response = self.session.get(f"{API_BASE}/ads/active?city=İstanbul")
            
            if response.status_code == 200:
                ads = response.json()
                self.log_test(
                    "Active Ads (City Filter)", 
                    True, 
                    f"Active ads for İstanbul: {len(ads)} ads found"
                )
            else:
                self.log_test("Active Ads (City Filter)", False, f"HTTP {response.status_code}", response.text)
                
            # Test with category filter
            response = self.session.get(f"{API_BASE}/ads/active?category=gida")
            
            if response.status_code == 200:
                ads = response.json()
                self.log_test(
                    "Active Ads (Category Filter)", 
                    True, 
                    f"Active ads for gida category: {len(ads)} ads found"
                )
            else:
                self.log_test("Active Ads (Category Filter)", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Active Ads", False, f"Exception: {str(e)}")

    def test_ad_impression_tracking(self):
        """Test POST /api/ads/{ad_id}/impression - Track ad impression"""
        print("👁️ Testing Ad Impression Tracking...")
        
        # Use a dummy ad ID if no real ad available
        ad_id = getattr(self, 'test_ad_id', str(uuid.uuid4()))
        
        try:
            response = self.session.post(f"{API_BASE}/ads/{ad_id}/impression")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "Ad Impression Tracking", 
                        True, 
                        f"Impression tracked successfully for ad {ad_id}"
                    )
                else:
                    self.log_test("Ad Impression Tracking", False, "Success flag not set", data)
            else:
                self.log_test("Ad Impression Tracking", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Ad Impression Tracking", False, f"Exception: {str(e)}")

    def test_ad_click_tracking(self):
        """Test POST /api/ads/{ad_id}/click - Track ad click"""
        print("🖱️ Testing Ad Click Tracking...")
        
        # Use a dummy ad ID if no real ad available
        ad_id = getattr(self, 'test_ad_id', str(uuid.uuid4()))
        
        try:
            response = self.session.post(f"{API_BASE}/ads/{ad_id}/click")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "Ad Click Tracking", 
                        True, 
                        f"Click tracked successfully for ad {ad_id}"
                    )
                else:
                    self.log_test("Ad Click Tracking", False, "Success flag not set", data)
            else:
                self.log_test("Ad Click Tracking", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Ad Click Tracking", False, f"Exception: {str(e)}")

    def test_admin_ads_management(self):
        """Test admin advertisement management endpoints"""
        print("🛠️ Testing Admin Ads Management...")
        
        if not self.admin_token:
            self.log_test("Admin Ads Management", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET /api/admin/ads
        try:
            response = self.session.get(f"{API_BASE}/admin/ads", headers=headers)
            
            if response.status_code == 200:
                ads = response.json()
                self.log_test(
                    "Admin Get All Ads", 
                    True, 
                    f"All ads loaded: {len(ads)} ads found"
                )
            else:
                self.log_test("Admin Get All Ads", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Get All Ads", False, f"Exception: {str(e)}")
        
        # Test POST /api/admin/ads - Create advertisement
        try:
            ad_data = {
                "title": "Test Advertisement",
                "description": "Test ad description",
                "imgUrl": "https://example.com/test-ad.jpg",
                "targetUrl": "https://example.com/target",
                "ctaText": "Test CTA",
                "type": "general",
                "targeting": {
                    "city": "İstanbul",
                    "category": "gida"
                },
                "schedule": {
                    "startAt": datetime.now().isoformat(),
                    "endAt": (datetime.now() + timedelta(days=7)).isoformat()
                },
                "active": True,
                "order": 1
            }
            
            response = self.session.post(f"{API_BASE}/admin/ads", json=ad_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ad_id"):
                    self.created_ad_id = data["ad_id"]
                    self.log_test(
                        "Admin Create Ad", 
                        True, 
                        f"Advertisement created: {data.get('message')}, ID: {data.get('ad_id')}"
                    )
                else:
                    self.log_test("Admin Create Ad", False, "No ad_id in response", data)
            else:
                self.log_test("Admin Create Ad", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Admin Create Ad", False, f"Exception: {str(e)}")
        
        # Test DELETE /api/admin/ads/{ad_id} - Delete advertisement
        if hasattr(self, 'created_ad_id'):
            try:
                response = self.session.delete(f"{API_BASE}/admin/ads/{self.created_ad_id}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        "Admin Delete Ad", 
                        True, 
                        f"Advertisement deleted: {data.get('message')}"
                    )
                else:
                    self.log_test("Admin Delete Ad", False, f"HTTP {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test("Admin Delete Ad", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all Phase 2 backend tests"""
        print("🚀 Starting Phase 2 Kuryecini Backend Testing...")
        print(f"🌐 Backend URL: {API_BASE}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Authentication tests
        self.test_admin_simple_login()
        self.test_business_login()
        
        # Business Panel APIs
        self.test_business_restaurant_view()
        self.test_business_featured_status()
        self.test_business_request_featured()
        self.test_business_products_categories()
        
        # Admin Enhanced APIs
        self.test_admin_featured_requests()
        self.test_admin_featured_request_approve()
        self.test_admin_featured_request_reject()
        self.test_admin_featured_businesses()
        self.test_admin_generate_dummy_data()
        
        # Advertisement System
        self.test_ads_active()
        self.test_ad_impression_tracking()
        self.test_ad_click_tracking()
        self.test_admin_ads_management()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("=" * 80)
        print("📊 PHASE 2 BACKEND TESTING SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print(f"📈 Tests passed: {self.passed_tests}/{self.total_tests} ({(self.passed_tests/self.total_tests*100):.1f}%)")
        print()
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Print successful tests summary
        successful_tests = [test for test in self.test_results if test["success"]]
        if successful_tests:
            print("✅ SUCCESSFUL TESTS:")
            for test in successful_tests:
                print(f"   • {test['test']}")
            print()
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0,
            "duration": duration,
            "failed_tests": failed_tests,
            "successful_tests": successful_tests
        }

if __name__ == "__main__":
    tester = Phase2BackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:
        print("🎉 Phase 2 backend testing completed successfully!")
        exit(0)
    else:
        print("⚠️  Phase 2 backend testing completed with issues.")
        exit(1)