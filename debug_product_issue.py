#!/usr/bin/env python3
"""
Debug Product Deletion Issue - Targeted Analysis
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://db-driven-kuryecini.preview.emergentagent.com/api"
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"

def debug_product_issue():
    session = requests.Session()
    
    print("🔍 DEBUGGING PRODUCT DELETION ISSUE")
    print("=" * 50)
    
    # Step 1: Login
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
    user_data = data.get("user", {})
    business_id = user_data.get("id")
    
    session.headers.update({"Authorization": f"Bearer {jwt_token}"})
    
    print(f"✅ Logged in as business: {business_id}")
    print(f"   Business name: {user_data.get('business_name', 'Unknown')}")
    print(f"   Role: {user_data.get('role')}")
    
    # Step 2: Check current products
    response = session.get(f"{BACKEND_URL}/products/my")
    if response.status_code == 200:
        current_products = response.json()
        print(f"📦 Current products: {len(current_products)}")
        for i, product in enumerate(current_products[:3]):
            print(f"   {i+1}. {product.get('name')} (ID: {product.get('id')[:8]}...)")
    else:
        print(f"❌ Failed to get current products: {response.status_code}")
        return
    
    # Step 3: Create a test product with detailed logging
    test_product = {
        "name": f"DEBUG Test Product {datetime.now().strftime('%H:%M:%S')}",
        "description": "Debug test product - should not be deleted",
        "price": 99.99,
        "category": "Debug",
        "preparation_time_minutes": 5,
        "is_available": True
    }
    
    print(f"\n➕ Creating test product...")
    print(f"   Product data: {json.dumps(test_product, indent=2)}")
    
    response = session.post(f"{BACKEND_URL}/products", json=test_product)
    print(f"   Response status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        created_product = response.json()
        product_id = created_product.get("id")
        print(f"✅ Product created successfully!")
        print(f"   Product ID: {product_id}")
        print(f"   Response: {json.dumps(created_product, indent=2)}")
        
        # Step 4: Immediately check if product exists
        print(f"\n🔍 Immediately checking if product exists...")
        response = session.get(f"{BACKEND_URL}/products/my")
        if response.status_code == 200:
            products_after_creation = response.json()
            product_exists = any(p.get("id") == product_id for p in products_after_creation)
            print(f"   Products after creation: {len(products_after_creation)}")
            print(f"   Test product exists: {product_exists}")
            
            if not product_exists:
                print("❌ CRITICAL: Product was deleted immediately after creation!")
                print("   This suggests an issue with the product creation or retrieval logic.")
            else:
                print("✅ Product exists immediately after creation")
                
                # Wait 5 seconds and check again
                print(f"\n⏱️ Waiting 5 seconds and checking again...")
                time.sleep(5)
                
                response = session.get(f"{BACKEND_URL}/products/my")
                if response.status_code == 200:
                    products_after_wait = response.json()
                    product_still_exists = any(p.get("id") == product_id for p in products_after_wait)
                    print(f"   Products after 5 seconds: {len(products_after_wait)}")
                    print(f"   Test product still exists: {product_still_exists}")
                    
                    if not product_still_exists:
                        print("❌ CRITICAL: Product was deleted within 5 seconds!")
                    else:
                        print("✅ Product survived 5 seconds")
        else:
            print(f"❌ Failed to check products after creation: {response.status_code}")
    else:
        print(f"❌ Product creation failed!")
        print(f"   Response: {response.text}")
    
    # Step 5: Check if there are any business ID mismatches
    print(f"\n🔍 Checking business ID consistency...")
    
    # Check /me endpoint
    response = session.get(f"{BACKEND_URL}/me")
    if response.status_code == 200:
        me_data = response.json()
        me_business_id = me_data.get("id")
        print(f"   /me endpoint business ID: {me_business_id}")
        print(f"   Login business ID: {business_id}")
        print(f"   IDs match: {me_business_id == business_id}")
        
        if me_business_id != business_id:
            print("❌ CRITICAL: Business ID mismatch detected!")
            print("   This could cause products to be created for wrong business or not found")
    else:
        print(f"❌ Failed to get /me data: {response.status_code}")

if __name__ == "__main__":
    debug_product_issue()