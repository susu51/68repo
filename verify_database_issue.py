#!/usr/bin/env python3
"""
Verify Database Issue - Check if products exist with different IDs
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://food-delivery-hub-19.preview.emergentagent.com/api"
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"

def verify_database_issue():
    session = requests.Session()
    
    print("🔍 VERIFYING DATABASE ID ISSUE")
    print("=" * 50)
    
    # Login
    login_data = {
        "email": TEST_BUSINESS_EMAIL,
        "password": TEST_BUSINESS_PASSWORD
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    data = response.json()
    jwt_token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {jwt_token}"})
    
    # Create a product and track the exact ID
    test_product = {
        "name": f"ID Verification Test {datetime.now().strftime('%H:%M:%S')}",
        "description": "Testing ID consistency",
        "price": 1.00,
        "category": "Test",
        "preparation_time_minutes": 1,
        "is_available": True
    }
    
    print(f"➕ Creating test product...")
    response = session.post(f"{BACKEND_URL}/products", json=test_product)
    
    if response.status_code == 200:
        created_product = response.json()
        created_id = created_product.get("id")
        print(f"✅ Product created with ID: {created_id}")
        
        # Now get all products and see what IDs they have
        print(f"\n📦 Getting all products...")
        response = session.get(f"{BACKEND_URL}/products/my")
        
        if response.status_code == 200:
            all_products = response.json()
            print(f"   Found {len(all_products)} total products")
            
            # Look for our product by name
            matching_products = [p for p in all_products if test_product["name"] in p.get("name", "")]
            
            if matching_products:
                found_product = matching_products[0]
                found_id = found_product.get("id")
                print(f"✅ Found product by name with ID: {found_id}")
                print(f"   Created ID: {created_id}")
                print(f"   Found ID:   {found_id}")
                print(f"   IDs match:  {created_id == found_id}")
                
                if created_id != found_id:
                    print("❌ CONFIRMED: ID mismatch issue!")
                    print("   The product exists but with a different ID")
                    print("   This explains why products appear to be 'deleted'")
                else:
                    print("✅ IDs match - no issue found")
            else:
                print("❌ Product not found by name - checking all recent products...")
                # Show last 5 products
                recent_products = sorted(all_products, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
                for i, product in enumerate(recent_products):
                    print(f"   {i+1}. {product.get('name')} (ID: {product.get('id')}, Created: {product.get('created_at')})")
        else:
            print(f"❌ Failed to get products: {response.status_code}")
    else:
        print(f"❌ Product creation failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    verify_database_issue()