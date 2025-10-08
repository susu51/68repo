#!/usr/bin/env python3
"""
MENÜ/ÜRÜN VİSİBİLİTY SORUNU - KAPSAMLI TEST
Comprehensive testing for business menu visibility issue in Aksaray

SORUN: "İşletme kısmında eklenen menüler gözükmüyor"

TEST ALANLARI:
1. İşletme Ürün Durumu - GET /api/businesses/{business_id}/products
2. Ürün Ekleme Sistemi Test - POST /api/products 
3. İşletme-Ürün İlişkisi - Business_id associations
4. Test Menüsü Oluşturma - Create test menus for Aksaray businesses
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://mockless-api.preview.emergentagent.com/api"

# Test credentials
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"
TEST_ADMIN_EMAIL = "admin@kuryecini.com"
TEST_ADMIN_PASSWORD = "KuryeciniAdmin2024!"

class MenuVisibilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.admin_token = None
        self.business_user_id = None
        self.created_products = []
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "aksaray_businesses": [],
            "product_analysis": {}
        }
    
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_data:
            test_result["response_data"] = response_data
        
        self.results["test_details"].append(test_result)
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {json.dumps(response_data, indent=2)}")
        print()
    
    def authenticate_business(self):
        """Authenticate as test business"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_BUSINESS_EMAIL,
                "password": TEST_BUSINESS_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.business_token = data.get("access_token")
                self.business_user_id = data.get("user", {}).get("id")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.business_token}"
                })
                self.log_test("Business Authentication", True, 
                            f"Business ID: {self.business_user_id}, Token length: {len(self.business_token) if self.business_token else 0}")
                return True
            else:
                self.log_test("Business Authentication", False, 
                            f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Business Authentication", False, f"Exception: {str(e)}")
            return False
    
    def authenticate_admin(self):
        """Authenticate as admin"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_test("Admin Authentication", True, 
                            f"Admin token length: {len(self.admin_token) if self.admin_token else 0}")
                return True
            else:
                self.log_test("Admin Authentication", False, 
                            f"Status: {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_all_businesses(self):
        """Get all businesses to analyze Aksaray businesses"""
        try:
            # Use admin token for this request
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                businesses = [user for user in users if user.get("role") == "business"]
                aksaray_businesses = [b for b in businesses if 
                                    b.get("city", "").lower() in ["aksaray", "Aksaray", "AKSARAY"]]
                
                self.results["aksaray_businesses"] = aksaray_businesses
                
                self.log_test("Get All Businesses", True, 
                            f"Total businesses: {len(businesses)}, Aksaray businesses: {len(aksaray_businesses)}")
                
                # Log Aksaray business details
                for business in aksaray_businesses:
                    print(f"    📍 Aksaray Business: {business.get('business_name', 'N/A')} (ID: {business.get('id', 'N/A')}, KYC: {business.get('kyc_status', 'N/A')})")
                
                return businesses
            else:
                self.log_test("Get All Businesses", False, 
                            f"Status: {response.status_code}", response.json())
                return []
        except Exception as e:
            self.log_test("Get All Businesses", False, f"Exception: {str(e)}")
            return []
    
    def check_business_products(self, business_id, business_name="Unknown"):
        """Check products for a specific business"""
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
            
            if response.status_code == 200:
                products = response.json()
                product_count = len(products) if isinstance(products, list) else 0
                
                self.results["product_analysis"][business_id] = {
                    "business_name": business_name,
                    "product_count": product_count,
                    "products": products
                }
                
                self.log_test(f"Products for {business_name}", True, 
                            f"Found {product_count} products")
                
                if product_count > 0:
                    for product in products[:3]:  # Show first 3 products
                        print(f"    🍽️ {product.get('name', 'N/A')} - ₺{product.get('price', 0)} ({product.get('category', 'N/A')})")
                
                return products
            else:
                self.log_test(f"Products for {business_name}", False, 
                            f"Status: {response.status_code}", response.json())
                return []
        except Exception as e:
            self.log_test(f"Products for {business_name}", False, f"Exception: {str(e)}")
            return []
    
    def create_test_product(self, business_name="Test Business", product_data=None):
        """Create a test product for the authenticated business"""
        if not product_data:
            product_data = {
                "name": f"Test Döner Kebap - {business_name}",
                "description": "Lezzetli döner kebap, taze sebzeler ile",
                "price": 35.50,
                "category": "Ana Yemek",
                "preparation_time_minutes": 20,
                "is_available": True
            }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/products", json=product_data)
            
            if response.status_code == 200:
                product = response.json()
                product_id = product.get("id")
                self.created_products.append(product_id)
                
                self.log_test(f"Create Product - {product_data['name']}", True, 
                            f"Product ID: {product_id}, Business ID: {product.get('business_id')}")
                return product
            else:
                self.log_test(f"Create Product - {product_data['name']}", False, 
                            f"Status: {response.status_code}", response.json())
                return None
        except Exception as e:
            self.log_test(f"Create Product - {product_data['name']}", False, f"Exception: {str(e)}")
            return None
    
    def create_test_menu_for_business(self, business_name="Test Restaurant"):
        """Create a complete test menu for a business"""
        test_menu = [
            {
                "name": "Döner Kebap",
                "description": "Geleneksel döner kebap, pilav ve salata ile",
                "price": 45.00,
                "category": "Ana Yemek",
                "preparation_time_minutes": 25,
                "is_available": True
            },
            {
                "name": "Pide - Kıymalı",
                "description": "Taze hamur üzerine kıyma ve kaşar peyniri",
                "price": 38.50,
                "category": "Pide",
                "preparation_time_minutes": 30,
                "is_available": True
            },
            {
                "name": "Coca Cola",
                "description": "Soğuk içecek - 330ml",
                "price": 8.00,
                "category": "İçecek",
                "preparation_time_minutes": 2,
                "is_available": True
            },
            {
                "name": "Künefe",
                "description": "Geleneksel künefe, fıstık ve şerbet ile",
                "price": 25.00,
                "category": "Tatlı",
                "preparation_time_minutes": 15,
                "is_available": True
            }
        ]
        
        created_products = []
        for product_data in test_menu:
            product = self.create_test_product(business_name, product_data)
            if product:
                created_products.append(product)
            time.sleep(0.5)  # Small delay between requests
        
        self.log_test(f"Create Complete Menu for {business_name}", 
                     len(created_products) == len(test_menu),
                     f"Created {len(created_products)}/{len(test_menu)} products")
        
        return created_products
    
    def test_product_visibility(self):
        """Test product visibility through public endpoints"""
        try:
            # Test public businesses endpoint
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                business_count = len(businesses) if isinstance(businesses, list) else 0
                
                self.log_test("Public Businesses Endpoint", True, 
                            f"Found {business_count} public businesses")
                
                # Check if our test business is visible
                test_business_visible = any(b.get("id") == self.business_user_id for b in businesses)
                self.log_test("Test Business Visibility", test_business_visible,
                            f"Test business {'visible' if test_business_visible else 'not visible'} in public list")
                
                return businesses
            else:
                self.log_test("Public Businesses Endpoint", False, 
                            f"Status: {response.status_code}", response.json())
                return []
        except Exception as e:
            self.log_test("Public Businesses Endpoint", False, f"Exception: {str(e)}")
            return []
    
    def run_comprehensive_test(self):
        """Run comprehensive menu visibility test"""
        print("🔍 MENÜ/ÜRÜN VİSİBİLİTY SORUNU - KAPSAMLI TEST")
        print("=" * 60)
        print()
        
        # Step 1: Authenticate
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - cannot continue")
            return
        
        if not self.authenticate_business():
            print("❌ Business authentication failed - cannot continue")
            return
        
        # Step 2: Analyze existing businesses
        print("📊 ANALYZING EXISTING BUSINESSES...")
        businesses = self.get_all_businesses()
        
        # Step 3: Check products for Aksaray businesses
        print("\n🏪 CHECKING AKSARAY BUSINESS PRODUCTS...")
        for business in self.results["aksaray_businesses"]:
            business_id = business.get("id")
            business_name = business.get("business_name", "Unknown")
            if business_id:
                self.check_business_products(business_id, business_name)
                time.sleep(0.5)
        
        # Step 4: Create test menu for authenticated business
        print("\n🍽️ CREATING TEST MENU...")
        self.create_test_menu_for_business("Test Restaurant")
        
        # Step 5: Test product visibility
        print("\n👁️ TESTING PRODUCT VISIBILITY...")
        self.test_product_visibility()
        
        # Step 6: Verify created products
        if self.business_user_id:
            print("\n✅ VERIFYING CREATED PRODUCTS...")
            self.check_business_products(self.business_user_id, "Test Restaurant")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📋 MENÜ VİSİBİLİTY TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.results["passed_tests"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        print(f"📊 Overall Results: {self.results['passed_tests']}/{self.results['total_tests']} tests passed ({success_rate:.1f}%)")
        print()
        
        # Aksaray Business Analysis
        print("🏪 AKSARAY BUSINESS ANALYSIS:")
        aksaray_count = len(self.results["aksaray_businesses"])
        print(f"   Total Aksaray businesses found: {aksaray_count}")
        
        if aksaray_count > 0:
            for business in self.results["aksaray_businesses"]:
                business_id = business.get("id")
                business_name = business.get("business_name", "Unknown")
                kyc_status = business.get("kyc_status", "unknown")
                product_info = self.results["product_analysis"].get(business_id, {})
                product_count = product_info.get("product_count", 0)
                
                print(f"   📍 {business_name}")
                print(f"      - ID: {business_id}")
                print(f"      - KYC Status: {kyc_status}")
                print(f"      - Products: {product_count}")
        else:
            print("   ⚠️ No Aksaray businesses found in database")
        
        print()
        
        # Product Creation Results
        created_count = len(self.created_products)
        print(f"🍽️ PRODUCT CREATION RESULTS:")
        print(f"   Products created: {created_count}")
        if created_count > 0:
            print(f"   Product IDs: {', '.join(self.created_products[:5])}{'...' if created_count > 5 else ''}")
        
        print()
        
        # Failed Tests
        failed_tests = [test for test in self.results["test_details"] if "❌" in test["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        else:
            print("✅ All tests passed!")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if aksaray_count == 0:
            print("   - No Aksaray businesses found - create test businesses in Aksaray")
        else:
            pending_kyc = [b for b in self.results["aksaray_businesses"] if b.get("kyc_status") != "approved"]
            if pending_kyc:
                print(f"   - {len(pending_kyc)} Aksaray businesses need KYC approval for visibility")
        
        if created_count > 0:
            print("   - Test products created successfully - check frontend visibility")
        
        if success_rate < 80:
            print("   - Multiple test failures detected - investigate backend issues")
        
        print("\n" + "=" * 60)

def main():
    tester = MenuVisibilityTester()
    
    try:
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
    finally:
        tester.print_summary()

if __name__ == "__main__":
    main()