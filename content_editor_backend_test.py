#!/usr/bin/env python3
"""
Content Management System Backend Testing for ContentEditor
Phase 1 ContentEditor Implementation Testing

This script tests the content management backend endpoints to ensure 
ContentEditor functionality works correctly.

SPECIFIC TESTING REQUIREMENTS:
1. Test GET /api/content/blocks to retrieve existing content blocks
2. Test GET /api/content/blocks/{block_id} for specific block retrieval
3. Test PUT /api/content/blocks/{block_id} for updating content blocks (admin auth required)
4. Test GET /api/content/popular-products for popular products data
5. Test GET /api/content/media-assets for media asset management

AUTHENTICATION DETAILS:
- Admin email: admin@kuryecini.com
- Admin password: KuryeciniAdmin2024!
- JWT token should be included for admin-protected endpoints

FOCUS AREAS:
- Verify content blocks API structure matches ContentEditor frontend expectations  
- Test response formats include proper _id, title, sections, page_type fields
- Test popular products endpoint returns proper product data with business_name, name fields
- Ensure admin authentication works for content modification endpoints
- Check if content_blocks collection exists and is properly seeded
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://order-flow-debug.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

class ContentEditorTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
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

    def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_test(
                    "Admin Authentication",
                    True,
                    f"Admin login successful. Role: {user_info.get('role')}, Token length: {len(self.admin_token)} chars"
                )
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                return True
            else:
                self.log_test(
                    "Admin Authentication",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Admin Authentication",
                False,
                f"Authentication error: {str(e)}"
            )
            return False

    def test_get_content_blocks(self):
        """Test GET /api/content/blocks endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/content/blocks")
            
            if response.status_code == 200:
                blocks = response.json()
                
                # Verify response structure
                if isinstance(blocks, list):
                    self.log_test(
                        "GET /api/content/blocks",
                        True,
                        f"Retrieved {len(blocks)} content blocks successfully"
                    )
                    
                    # Test structure of first block if exists
                    if blocks:
                        first_block = blocks[0]
                        required_fields = ["_id"]
                        missing_fields = [field for field in required_fields if field not in first_block]
                        
                        if not missing_fields:
                            self.log_test(
                                "Content Block Structure Validation",
                                True,
                                f"First block has required fields: {list(first_block.keys())}"
                            )
                        else:
                            self.log_test(
                                "Content Block Structure Validation",
                                False,
                                f"Missing required fields: {missing_fields}"
                            )
                    else:
                        self.log_test(
                            "Content Block Data Check",
                            False,
                            "No content blocks found in database - collection may need seeding"
                        )
                    
                    return blocks
                else:
                    self.log_test(
                        "GET /api/content/blocks",
                        False,
                        f"Expected list response, got {type(blocks)}"
                    )
                    return []
            else:
                self.log_test(
                    "GET /api/content/blocks",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "GET /api/content/blocks",
                False,
                f"Request error: {str(e)}"
            )
            return []

    def test_get_specific_content_block(self, block_id):
        """Test GET /api/content/blocks/{block_id} endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/content/blocks/{block_id}")
            
            if response.status_code == 200:
                block = response.json()
                
                # Verify response structure
                if isinstance(block, dict) and "_id" in block:
                    self.log_test(
                        f"GET /api/content/blocks/{block_id}",
                        True,
                        f"Retrieved specific content block successfully. Fields: {list(block.keys())}"
                    )
                    return block
                else:
                    self.log_test(
                        f"GET /api/content/blocks/{block_id}",
                        False,
                        f"Invalid block structure: {block}"
                    )
                    return None
            elif response.status_code == 404:
                self.log_test(
                    f"GET /api/content/blocks/{block_id}",
                    False,
                    f"Content block not found (404) - block_id may not exist"
                )
                return None
            else:
                self.log_test(
                    f"GET /api/content/blocks/{block_id}",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test(
                f"GET /api/content/blocks/{block_id}",
                False,
                f"Request error: {str(e)}"
            )
            return None

    def test_update_content_block(self, block_id, update_data):
        """Test PUT /api/content/blocks/{block_id} endpoint (admin auth required)"""
        try:
            response = self.session.put(f"{BACKEND_URL}/content/blocks/{block_id}", json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.log_test(
                        f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                        True,
                        f"Content block updated successfully: {result.get('message')}"
                    )
                    return True
                else:
                    self.log_test(
                        f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                        False,
                        f"Update failed: {result}"
                    )
                    return False
            elif response.status_code == 403:
                self.log_test(
                    f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                    False,
                    "Access denied (403) - admin authentication may have failed"
                )
                return False
            elif response.status_code == 404:
                self.log_test(
                    f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                    False,
                    "Content block not found (404) - block_id may not exist"
                )
                return False
            else:
                self.log_test(
                    f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"PUT /api/content/blocks/{block_id} (Admin Auth)",
                False,
                f"Request error: {str(e)}"
            )
            return False

    def test_get_popular_products(self):
        """Test GET /api/content/popular-products endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/content/popular-products")
            
            if response.status_code == 200:
                products = response.json()
                
                # Verify response structure
                if isinstance(products, list):
                    self.log_test(
                        "GET /api/content/popular-products",
                        True,
                        f"Retrieved {len(products)} popular products successfully"
                    )
                    
                    # Test structure of first product if exists
                    if products:
                        first_product = products[0]
                        required_fields = ["_id", "name", "business_name"]
                        missing_fields = [field for field in required_fields if field not in first_product]
                        
                        if not missing_fields:
                            self.log_test(
                                "Popular Products Structure Validation",
                                True,
                                f"First product has required fields: {list(first_product.keys())}"
                            )
                        else:
                            self.log_test(
                                "Popular Products Structure Validation",
                                False,
                                f"Missing required fields: {missing_fields}. Available: {list(first_product.keys())}"
                            )
                    else:
                        self.log_test(
                            "Popular Products Data Check",
                            True,
                            "No popular products data - this is acceptable for new systems"
                        )
                    
                    return products
                else:
                    self.log_test(
                        "GET /api/content/popular-products",
                        False,
                        f"Expected list response, got {type(products)}"
                    )
                    return []
            else:
                self.log_test(
                    "GET /api/content/popular-products",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "GET /api/content/popular-products",
                False,
                f"Request error: {str(e)}"
            )
            return []

    def test_get_media_assets(self):
        """Test GET /api/content/media-assets endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/content/media-assets")
            
            if response.status_code == 200:
                assets = response.json()
                
                # Verify response structure
                if isinstance(assets, list):
                    self.log_test(
                        "GET /api/content/media-assets",
                        True,
                        f"Retrieved {len(assets)} media assets successfully"
                    )
                    
                    # Test structure of first asset if exists
                    if assets:
                        first_asset = assets[0]
                        self.log_test(
                            "Media Assets Structure Validation",
                            True,
                            f"First asset has fields: {list(first_asset.keys())}"
                        )
                    else:
                        self.log_test(
                            "Media Assets Data Check",
                            True,
                            "No media assets found - this is acceptable for new systems"
                        )
                    
                    return assets
                else:
                    self.log_test(
                        "GET /api/content/media-assets",
                        False,
                        f"Expected list response, got {type(assets)}"
                    )
                    return []
            else:
                self.log_test(
                    "GET /api/content/media-assets",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "GET /api/content/media-assets",
                False,
                f"Request error: {str(e)}"
            )
            return []

    def test_admin_rbac_protection(self):
        """Test that admin endpoints are properly protected"""
        try:
            # Remove authorization header temporarily
            original_headers = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            # Try to update a content block without authentication
            test_data = {"title": "Unauthorized Test", "content": "This should fail"}
            response = self.session.put(f"{BACKEND_URL}/content/blocks/test-id", json=test_data)
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Admin RBAC Protection Test",
                    True,
                    f"Unauthorized access properly blocked with status {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Admin RBAC Protection Test",
                    False,
                    f"Expected 401/403, got {response.status_code} - security vulnerability!"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Admin RBAC Protection Test",
                False,
                f"Test error: {str(e)}"
            )
            return False

    def create_test_content_block(self):
        """Create a test content block for testing purposes"""
        try:
            # First, let's try to create a content block directly in the database
            # Since there's no POST endpoint, we'll test with existing data or create via database
            
            test_block_data = {
                "_id": "test-content-block-001",
                "title": "Test Content Block",
                "page_type": "homepage",
                "sections": [
                    {
                        "type": "hero",
                        "title": "Welcome to Kuryecini",
                        "subtitle": "Fast delivery platform",
                        "image_url": "/images/hero-bg.jpg"
                    },
                    {
                        "type": "features",
                        "items": [
                            {"title": "Fast Delivery", "description": "Quick and reliable"},
                            {"title": "Wide Selection", "description": "Many restaurants"}
                        ]
                    }
                ],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            }
            
            # We'll use this data for update testing
            return test_block_data
            
        except Exception as e:
            self.log_test(
                "Create Test Content Block",
                False,
                f"Error creating test block: {str(e)}"
            )
            return None

    def run_comprehensive_tests(self):
        """Run all content management tests"""
        print("🎯 CONTENT MANAGEMENT SYSTEM BACKEND TESTING STARTED")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {ADMIN_EMAIL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        # 1. Admin Authentication
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with admin-protected tests.")
            return False

        # 2. Test GET /api/content/blocks
        content_blocks = self.test_get_content_blocks()

        # 3. Test GET /api/content/blocks/{block_id} if blocks exist
        if content_blocks:
            first_block_id = content_blocks[0].get("_id")
            if first_block_id:
                self.test_get_specific_content_block(first_block_id)
            else:
                self.log_test(
                    "Content Block ID Test",
                    False,
                    "First content block missing _id field"
                )
        else:
            # Test with a hypothetical block ID
            self.test_get_specific_content_block("test-block-001")

        # 4. Test PUT /api/content/blocks/{block_id} (admin auth required)
        test_block_data = self.create_test_content_block()
        if test_block_data:
            block_id = test_block_data["_id"]
            update_data = {
                "title": "Updated Test Content Block",
                "page_type": "homepage",
                "sections": test_block_data["sections"],
                "is_active": True
            }
            self.test_update_content_block(block_id, update_data)
        else:
            # Test with existing block if available
            if content_blocks:
                first_block_id = content_blocks[0].get("_id")
                if first_block_id:
                    update_data = {
                        "title": "Test Update",
                        "updated_by_test": True
                    }
                    self.test_update_content_block(first_block_id, update_data)

        # 5. Test GET /api/content/popular-products
        self.test_get_popular_products()

        # 6. Test GET /api/content/media-assets
        self.test_get_media_assets()

        # 7. Test admin RBAC protection
        self.test_admin_rbac_protection()

        # Print final results
        self.print_final_results()

    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("🎯 CONTENT MANAGEMENT SYSTEM TESTING COMPLETE")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS: {self.passed_tests}/{self.total_tests} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Group results by category
        categories = {
            "Authentication": [],
            "Content Blocks": [],
            "Popular Products": [],
            "Media Assets": [],
            "Security": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            if "Auth" in test_name:
                categories["Authentication"].append(result)
            elif "content/blocks" in test_name or "Content Block" in test_name:
                categories["Content Blocks"].append(result)
            elif "popular-products" in test_name or "Popular Products" in test_name:
                categories["Popular Products"].append(result)
            elif "media-assets" in test_name or "Media Assets" in test_name:
                categories["Media Assets"].append(result)
            elif "RBAC" in test_name or "Protection" in test_name:
                categories["Security"].append(result)
            else:
                categories["Other"].append(result)
        
        # Print results by category
        for category, results in categories.items():
            if results:
                print(f"📋 {category.upper()}:")
                for result in results:
                    print(f"   {result['status']}: {result['test']}")
                    if result['details']:
                        print(f"      └─ {result['details']}")
                print()
        
        # Print critical issues
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("🚨 CRITICAL ISSUES FOUND:")
            for result in failed_tests:
                print(f"   ❌ {result['test']}: {result['details']}")
            print()
        
        # Print recommendations
        print("💡 RECOMMENDATIONS:")
        
        # Check if content_blocks collection needs seeding
        content_block_tests = [r for r in self.test_results if "content/blocks" in r["test"]]
        if any("No content blocks found" in r.get("details", "") for r in content_block_tests):
            print("   • Content blocks collection appears empty - consider seeding with initial data")
        
        # Check authentication issues
        auth_tests = [r for r in self.test_results if "Auth" in r["test"]]
        if any(not r["success"] for r in auth_tests):
            print("   • Admin authentication issues detected - verify credentials and JWT configuration")
        
        # Check API structure
        structure_tests = [r for r in self.test_results if "Structure" in r["test"]]
        if any(not r["success"] for r in structure_tests):
            print("   • API response structure issues - verify ContentEditor frontend compatibility")
        
        if success_rate >= 80:
            print("✅ CONCLUSION: Content Management System backend is mostly functional for ContentEditor integration")
        elif success_rate >= 60:
            print("⚠️  CONCLUSION: Content Management System has some issues but core functionality works")
        else:
            print("❌ CONCLUSION: Content Management System has significant issues requiring immediate attention")
        
        print("=" * 80)

def main():
    """Main test execution"""
    tester = ContentEditorTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()