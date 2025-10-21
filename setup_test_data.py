#!/usr/bin/env python3
"""
Setup test data for business-courier integration testing
Creates test products for the test business so orders can be properly assigned
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://ai-order-debug.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"

def setup_test_data():
    """Setup test products for the test business"""
    session = requests.Session()
    
    print("🔐 Authenticating test business...")
    
    # Login as test business
    login_data = {"email": BUSINESS_EMAIL, "password": BUSINESS_PASSWORD}
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Business login failed: {response.status_code}")
        return False
    
    data = response.json()
    token = data.get("access_token")
    business_user = data.get("user", {})
    business_id = business_user.get("id")
    
    print(f"✅ Business authenticated: {business_id}")
    
    # Set authorization header
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Create test products
    test_products = [
        {
            "name": "Test Burger",
            "description": "Delicious test burger for integration testing",
            "price": 45.0,
            "category": "Ana Yemek",
            "preparation_time_minutes": 15,
            "is_available": True
        },
        {
            "name": "Test Drink",
            "description": "Refreshing test drink for integration testing",
            "price": 15.0,
            "category": "İçecek",
            "preparation_time_minutes": 5,
            "is_available": True
        },
        {
            "name": "Test Pizza",
            "description": "Tasty test pizza for integration testing",
            "price": 65.0,
            "category": "Pizza",
            "preparation_time_minutes": 20,
            "is_available": True
        }
    ]
    
    created_products = []
    
    print("📦 Creating test products...")
    
    for product_data in test_products:
        response = session.post(f"{BACKEND_URL}/products", json=product_data)
        
        if response.status_code == 200:
            product = response.json()
            created_products.append(product)
            print(f"✅ Created product: {product['name']} (ID: {product['id']})")
        else:
            print(f"❌ Failed to create product {product_data['name']}: {response.status_code}")
            print(f"   Response: {response.text}")
    
    print(f"\n🎉 Setup complete! Created {len(created_products)} test products for business {business_id}")
    
    # Return product IDs for use in tests
    return [product['id'] for product in created_products]

if __name__ == "__main__":
    product_ids = setup_test_data()
    if product_ids:
        print(f"\n📋 Test Product IDs: {product_ids}")
    else:
        print("\n❌ Failed to setup test data")