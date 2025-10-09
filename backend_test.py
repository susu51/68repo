#!/usr/bin/env python3
"""
Phase 2 Content & Media Foundation Backend Testing
Testing content blocks, media assets, admin stats, and popular products endpoints

Test Coverage:
1. GET /api/content/blocks - Content blocks retrieval
2. GET /api/content/blocks/home_admin - Admin dashboard content
3. PUT /api/content/blocks/home_admin - Update admin content (auth required)
4. GET /api/content/media-assets - Media galleries retrieval
5. GET /api/content/media-assets/courier_gallery - Courier images
6. GET /api/content/admin/stats - Real-time dashboard stats
7. GET /api/content/popular-products - Popular products data
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://deliver-yemek.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

# Alternative admin credentials to try
ALTERNATIVE_ADMIN_CREDENTIALS = [
    {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    {"email": "admin@delivertr.com", "password": "6851"}
]

class ContentMediaTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("🔐 AUTHENTICATING ADMIN USER...")
        
        # Try primary admin credentials
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                if self.admin_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.admin_token}"
                    })
                    self.log_test("Admin Authentication", True, 
                                f"Successfully authenticated admin user, token length: {len(self.admin_token)}")
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No access token in response")
            else:
                self.log_test("Admin Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Authentication error: {str(e)}")
        
        # Try alternative credentials
        for creds in ALTERNATIVE_ADMIN_CREDENTIALS:
            try:
                response = self.session.post(f"{BACKEND_URL}/auth/login", json=creds)
                
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("access_token")
                    if self.admin_token:
                        self.session.headers.update({
                            "Authorization": f"Bearer {self.admin_token}"
                        })
                        self.log_test(f"Alternative Admin Auth ({creds['email']})", True, 
                                    f"Successfully authenticated, token length: {len(self.admin_token)}")
                        return True
                        
            except Exception as e:
                self.log_test(f"Alternative Admin Auth ({creds['email']})", False, 
                            f"Authentication error: {str(e)}")
        
        return False

    def test_content_blocks_endpoints(self):
        """Test content blocks API endpoints"""
        print("\n🔍 TESTING CONTENT BLOCKS ENDPOINTS")
        
        # Test GET /api/content/blocks
        try:
            response = self.session.get(f"{BACKEND_URL}/content/blocks")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/content/blocks", True, 
                            f"Retrieved content blocks successfully, count: {len(data) if isinstance(data, list) else 'N/A'}")
            elif response.status_code == 404:
                self.log_test("GET /api/content/blocks", False, 
                            "Endpoint not found - content blocks API not implemented")
            else:
                self.log_test("GET /api/content/blocks", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/blocks", False, f"Request error: {str(e)}")
        
        # Test GET /api/content/blocks/home_admin
        try:
            response = self.session.get(f"{BACKEND_URL}/content/blocks/home_admin")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/content/blocks/home_admin", True, 
                            f"Retrieved admin dashboard content successfully")
            elif response.status_code == 404:
                self.log_test("GET /api/content/blocks/home_admin", False, 
                            "Endpoint not found - admin dashboard content API not implemented")
            else:
                self.log_test("GET /api/content/blocks/home_admin", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/blocks/home_admin", False, f"Request error: {str(e)}")
        
        # Test PUT /api/content/blocks/home_admin (admin auth required)
        try:
            update_data = {
                "sections": [
                    {
                        "id": "welcome",
                        "title": "Welcome Admin",
                        "content": "Updated admin dashboard content"
                    }
                ]
            }
            response = self.session.put(f"{BACKEND_URL}/content/blocks/home_admin", json=update_data)
            if response.status_code == 200:
                self.log_test("PUT /api/content/blocks/home_admin", True, 
                            "Successfully updated admin dashboard content")
            elif response.status_code == 404:
                self.log_test("PUT /api/content/blocks/home_admin", False, 
                            "Endpoint not found - admin dashboard content update API not implemented")
            elif response.status_code == 403:
                self.log_test("PUT /api/content/blocks/home_admin", False, 
                            "Access denied - admin authentication may not be working properly")
            else:
                self.log_test("PUT /api/content/blocks/home_admin", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("PUT /api/content/blocks/home_admin", False, f"Request error: {str(e)}")

    def test_media_assets_endpoints(self):
        """Test media assets API endpoints"""
        print("\n🖼️ TESTING MEDIA ASSETS ENDPOINTS")
        
        # Test GET /api/content/media-assets
        try:
            response = self.session.get(f"{BACKEND_URL}/content/media-assets")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/content/media-assets", True, 
                            f"Retrieved media galleries successfully, count: {len(data) if isinstance(data, list) else 'N/A'}")
            elif response.status_code == 404:
                self.log_test("GET /api/content/media-assets", False, 
                            "Endpoint not found - media assets API not implemented")
            else:
                self.log_test("GET /api/content/media-assets", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/media-assets", False, f"Request error: {str(e)}")
        
        # Test GET /api/content/media-assets/courier_gallery
        try:
            response = self.session.get(f"{BACKEND_URL}/content/media-assets/courier_gallery")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/content/media-assets/courier_gallery", True, 
                            f"Retrieved courier gallery successfully, images count: {len(data.get('images', [])) if isinstance(data, dict) else 'N/A'}")
            elif response.status_code == 404:
                self.log_test("GET /api/content/media-assets/courier_gallery", False, 
                            "Endpoint not found - courier gallery API not implemented")
            else:
                self.log_test("GET /api/content/media-assets/courier_gallery", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/media-assets/courier_gallery", False, f"Request error: {str(e)}")

    def test_admin_stats_endpoint(self):
        """Test admin stats endpoint"""
        print("\n📊 TESTING ADMIN STATS ENDPOINT")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/content/admin/stats")
            if response.status_code == 200:
                data = response.json()
                # Check for expected stats structure
                expected_fields = ['orders', 'revenue', 'users', 'businesses']
                has_expected_structure = any(field in str(data).lower() for field in expected_fields)
                
                self.log_test("GET /api/content/admin/stats", True, 
                            f"Retrieved admin stats successfully, has expected structure: {has_expected_structure}")
            elif response.status_code == 404:
                self.log_test("GET /api/content/admin/stats", False, 
                            "Endpoint not found - admin stats API not implemented")
            elif response.status_code == 403:
                self.log_test("GET /api/content/admin/stats", False, 
                            "Access denied - admin authentication may not be working properly")
            else:
                self.log_test("GET /api/content/admin/stats", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/admin/stats", False, f"Request error: {str(e)}")

    def test_popular_products_endpoint(self):
        """Test popular products endpoint"""
        print("\n🔥 TESTING POPULAR PRODUCTS ENDPOINT")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/content/popular-products")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/content/popular-products", True, 
                            f"Retrieved popular products successfully, count: {len(data) if isinstance(data, list) else 'N/A'}")
            elif response.status_code == 404:
                self.log_test("GET /api/content/popular-products", False, 
                            "Endpoint not found - popular products API not implemented")
            else:
                self.log_test("GET /api/content/popular-products", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /api/content/popular-products", False, f"Request error: {str(e)}")

    def run_all_tests(self):
        """Run all content and media foundation tests"""
        print("🚀 STARTING PHASE 2 CONTENT & MEDIA FOUNDATION TESTING")
        print("=" * 60)
        
        # Try admin authentication
        auth_success = self.authenticate_admin()
        
        if not auth_success:
            print("\n⚠️ WARNING: Admin authentication failed, testing endpoints without auth...")
        
        # Run all endpoint tests
        self.test_content_blocks_endpoints()
        self.test_media_assets_endpoints()
        self.test_admin_stats_endpoint()
        self.test_popular_products_endpoint()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 CONTENT & MEDIA FOUNDATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical findings
        print("\n🚨 CRITICAL FINDINGS:")
        
        # Check for missing endpoints
        missing_endpoints = []
        for result in self.test_results:
            if not result["success"] and "not found" in result["details"].lower():
                missing_endpoints.append(result["test"])
        
        if missing_endpoints:
            print(f"❌ MISSING ENDPOINTS: {len(missing_endpoints)} critical endpoints not implemented:")
            for endpoint in missing_endpoints:
                print(f"   - {endpoint}")
        
        # Check authentication issues
        auth_issues = []
        for result in self.test_results:
            if not result["success"] and ("authentication" in result["details"].lower() or 
                                        "access denied" in result["details"].lower()):
                auth_issues.append(result["test"])
        
        if auth_issues:
            print(f"🔐 AUTHENTICATION ISSUES: {len(auth_issues)} endpoints have auth problems:")
            for issue in auth_issues:
                print(f"   - {issue}")
        
        print(f"\n📝 CONCLUSION:")
        if success_rate < 50:
            print("❌ CRITICAL: Phase 2 Content & Media Foundation is NOT READY")
            print("   Major implementation gaps detected - endpoints missing")
        elif success_rate < 80:
            print("⚠️ WARNING: Phase 2 Content & Media Foundation has significant issues")
            print("   Some functionality working but critical gaps remain")
        else:
            print("✅ SUCCESS: Phase 2 Content & Media Foundation is functional")
            print("   Most endpoints working correctly")

if __name__ == "__main__":
    tester = ContentMediaTester()
    tester.run_all_tests()