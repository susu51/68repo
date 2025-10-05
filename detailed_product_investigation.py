#!/usr/bin/env python3
"""
DETAILED PRODUCT INVESTIGATION
Deep dive into why products are not showing for businesses
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://meal-dash-163.preview.emergentagent.com/api"

# Test credentials
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"

class ProductInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.business_token = None
        self.business_user_id = None
    
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
                print(f"✅ Business authenticated - ID: {self.business_user_id}")
                return True
            else:
                print(f"❌ Business auth failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Business auth exception: {str(e)}")
            return False
    
    def test_product_endpoints(self):
        """Test different product endpoints"""
        print("\n🔍 TESTING PRODUCT ENDPOINTS...")
        
        # Test 1: Get my products (business endpoint)
        print("\n1. Testing GET /api/products/my (business products)")
        try:
            response = self.session.get(f"{BACKEND_URL}/products/my")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                products = response.json()
                print(f"   Products found: {len(products)}")
                for product in products[:3]:
                    print(f"   - {product.get('name')} (ID: {product.get('id')}, Business: {product.get('business_id')})")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test 2: Get all products
        print("\n2. Testing GET /api/products (all products)")
        try:
            response = self.session.get(f"{BACKEND_URL}/products")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                products = response.json()
                print(f"   Total products: {len(products)}")
                business_products = [p for p in products if p.get('business_id') == self.business_user_id]
                print(f"   My business products: {len(business_products)}")
                for product in business_products[:3]:
                    print(f"   - {product.get('name')} (Available: {product.get('is_available')})")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test 3: Get products by business ID
        print(f"\n3. Testing GET /api/products?business_id={self.business_user_id}")
        try:
            response = self.session.get(f"{BACKEND_URL}/products?business_id={self.business_user_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                products = response.json()
                print(f"   Products for business: {len(products)}")
                for product in products[:3]:
                    print(f"   - {product.get('name')} (Category: {product.get('category')})")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        # Test 4: Test the businesses/{id}/products endpoint
        print(f"\n4. Testing GET /api/businesses/{self.business_user_id}/products")
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses/{self.business_user_id}/products")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                products = response.json()
                print(f"   Products via businesses endpoint: {len(products)}")
                for product in products[:3]:
                    print(f"   - {product.get('name')} (Price: ₺{product.get('price')})")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
    
    def test_aksaray_business_products(self):
        """Test products for a specific Aksaray business"""
        print("\n🏪 TESTING AKSARAY BUSINESS PRODUCTS...")
        
        # Test with "başer" business
        baser_business_id = "68dfd5805b9cea03202ec133"
        
        print(f"\n📍 Testing 'başer' business (ID: {baser_business_id})")
        
        # Test different endpoints for this business
        endpoints_to_test = [
            f"/businesses/{baser_business_id}/products",
            f"/products?business_id={baser_business_id}"
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n   Testing GET {endpoint}")
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    products = response.json()
                    print(f"   Products found: {len(products)}")
                    if len(products) > 0:
                        for product in products[:3]:
                            print(f"   - {product.get('name')} (₺{product.get('price')})")
                    else:
                        print("   ⚠️ No products found for this business")
                else:
                    print(f"   Error: {response.text}")
            except Exception as e:
                print(f"   Exception: {str(e)}")
    
    def create_product_for_aksaray_business(self):
        """Try to create a product for an Aksaray business"""
        print("\n🍽️ CREATING PRODUCT FOR AKSARAY BUSINESS...")
        
        # First, let's try to authenticate as an Aksaray business
        # We'll use a test approach - create a product with our test business
        # but check if it shows up in the system
        
        product_data = {
            "name": "Aksaray Özel Döner",
            "description": "Aksaray'ın en lezzetli döneri",
            "price": 42.50,
            "category": "Ana Yemek",
            "preparation_time_minutes": 25,
            "is_available": True
        }
        
        print(f"Creating product: {product_data['name']}")
        try:
            response = self.session.post(f"{BACKEND_URL}/products", json=product_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                product = response.json()
                print(f"✅ Product created successfully!")
                print(f"   Product ID: {product.get('id')}")
                print(f"   Business ID: {product.get('business_id')}")
                print(f"   Name: {product.get('name')}")
                
                # Now verify it shows up
                print("\n🔍 Verifying product visibility...")
                time.sleep(1)
                
                # Check via business products endpoint
                response = self.session.get(f"{BACKEND_URL}/products/my")
                if response.status_code == 200:
                    products = response.json()
                    created_product = next((p for p in products if p.get('id') == product.get('id')), None)
                    if created_product:
                        print("✅ Product visible in business products list")
                    else:
                        print("❌ Product NOT visible in business products list")
                
                return product
            else:
                print(f"❌ Product creation failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Exception creating product: {str(e)}")
            return None
    
    def investigate_database_structure(self):
        """Investigate the database structure and relationships"""
        print("\n🔍 INVESTIGATING DATABASE STRUCTURE...")
        
        # Check if there are any products at all in the system
        print("\n1. Checking all products in system")
        try:
            response = self.session.get(f"{BACKEND_URL}/products")
            if response.status_code == 200:
                all_products = response.json()
                print(f"   Total products in system: {len(all_products)}")
                
                # Group by business_id
                business_groups = {}
                for product in all_products:
                    business_id = product.get('business_id', 'unknown')
                    if business_id not in business_groups:
                        business_groups[business_id] = []
                    business_groups[business_id].append(product)
                
                print(f"   Products grouped by business:")
                for business_id, products in business_groups.items():
                    print(f"   - Business {business_id}: {len(products)} products")
                    if len(products) > 0:
                        print(f"     Sample: {products[0].get('name', 'N/A')}")
            else:
                print(f"   Error getting products: {response.status_code}")
        except Exception as e:
            print(f"   Exception: {str(e)}")
    
    def run_investigation(self):
        """Run complete investigation"""
        print("🔍 DETAILED PRODUCT INVESTIGATION")
        print("=" * 50)
        
        if not self.authenticate_business():
            print("❌ Cannot continue without authentication")
            return
        
        self.test_product_endpoints()
        self.test_aksaray_business_products()
        self.investigate_database_structure()
        self.create_product_for_aksaray_business()
        
        print("\n" + "=" * 50)
        print("🎯 INVESTIGATION COMPLETE")
        print("=" * 50)

def main():
    investigator = ProductInvestigator()
    investigator.run_investigation()

if __name__ == "__main__":
    main()