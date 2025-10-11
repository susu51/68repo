#!/usr/bin/env python3
"""
Debug Backend Test - Investigating specific E2E workflow issues
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://quickcourier.preview.emergentagent.com/api"

def test_businesses_endpoint():
    """Debug the businesses endpoint error"""
    print("🔍 DEBUGGING /api/businesses ENDPOINT")
    
    try:
        response = requests.get(f"{BACKEND_URL}/businesses")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("❌ Internal Server Error - likely database field issue")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_nearby_businesses_with_auth():
    """Test nearby businesses with customer authentication"""
    print("\n🔍 DEBUGGING /api/nearby/businesses WITH AUTHENTICATION")
    
    # First authenticate as customer
    try:
        login_data = {"email": "testcustomer@example.com", "password": "test123"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Customer authenticated, token length: {len(token)}")
            
            # Now test nearby businesses with auth
            headers = {"Authorization": f"Bearer {token}"}
            params = {"lat": 41.0082, "lng": 28.9784, "radius": 5000}
            
            response = requests.get(f"{BACKEND_URL}/nearby/businesses", params=params, headers=headers)
            print(f"Nearby businesses status: {response.status_code}")
            print(f"Nearby businesses response: {response.text}")
            
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_business_products_endpoint():
    """Debug the business products endpoint"""
    print("\n🔍 DEBUGGING /api/businesses/{id}/products ENDPOINT")
    
    business_id = "business-001"  # Test business ID
    
    try:
        response = requests.get(f"{BACKEND_URL}/businesses/{business_id}/products")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("❌ Internal Server Error - likely serialization issue")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_reviews_endpoint():
    """Debug the reviews endpoint"""
    print("\n🔍 DEBUGGING /api/reviews ENDPOINT")
    
    # First authenticate as customer
    try:
        login_data = {"email": "testcustomer@example.com", "password": "test123"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test creating a review
            review_data = {
                "order_id": "test-order-id",
                "target_type": "business",
                "target_id": "business-001",
                "rating": 5,
                "comment": "Test review"
            }
            
            response = requests.post(f"{BACKEND_URL}/reviews", json=review_data, headers=headers)
            print(f"Reviews status: {response.status_code}")
            print(f"Reviews response: {response.text}")
            
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_alternative_endpoints():
    """Test alternative endpoint patterns"""
    print("\n🔍 TESTING ALTERNATIVE ENDPOINT PATTERNS")
    
    # Test different business listing endpoints
    endpoints_to_try = [
        "/businesses",
        "/restaurants", 
        "/public/businesses",
        "/customer/businesses"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}")
            print(f"{endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"  Found {len(data)} items")
                elif isinstance(data, dict):
                    print(f"  Response keys: {list(data.keys())}")
        except Exception as e:
            print(f"{endpoint}: Error - {str(e)}")

def run_debug_tests():
    """Run all debug tests"""
    print("🚀 STARTING DEBUG BACKEND TESTING")
    print("=" * 50)
    
    test_businesses_endpoint()
    test_nearby_businesses_with_auth()
    test_business_products_endpoint()
    test_reviews_endpoint()
    test_alternative_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 DEBUG TESTING COMPLETE")

if __name__ == "__main__":
    run_debug_tests()