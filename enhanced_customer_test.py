#!/usr/bin/env python3
"""
Enhanced Customer App Backend Testing
====================================

Enhanced testing with better business ID extraction and more detailed analysis.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://meal-dash-163.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

def test_comprehensive_customer_endpoints():
    """Comprehensive test of customer endpoints"""
    print("🚀 ENHANCED CUSTOMER APP BACKEND TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    # Step 1: Customer Login
    print("🔐 TESTING CUSTOMER LOGIN")
    print("-" * 30)
    
    try:
        login_data = {"email": TEST_CUSTOMER_EMAIL, "password": TEST_CUSTOMER_PASSWORD}
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user = data.get("user", {})
            print(f"✅ Customer login successful")
            print(f"   User: {user.get('first_name')} {user.get('last_name')} ({user.get('email')})")
            print(f"   Token length: {len(auth_token)} chars")
            results["passed"] += 1
            results["details"].append("✅ Customer login working")
        else:
            print(f"❌ Login failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            auth_token = None
            results["failed"] += 1
            results["details"].append("❌ Customer login failed")
    except Exception as e:
        print(f"❌ Login exception: {str(e)}")
        auth_token = None
        results["failed"] += 1
        results["details"].append("❌ Customer login exception")
    
    print()
    
    # Step 2: Restaurant Discovery
    print("🍽️ TESTING RESTAURANT DISCOVERY")
    print("-" * 30)
    
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    business_id = None
    
    try:
        response = requests.get(f"{API_BASE}/restaurants/discover", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Restaurant discovery successful")
            print(f"   Found {len(data)} restaurants")
            
            if data:
                business_id = data[0].get("id")
                print(f"   First business ID: {business_id}")
                for i, restaurant in enumerate(data[:3]):  # Show first 3
                    name = restaurant.get("business_name", "Unknown")
                    category = restaurant.get("business_category", "Unknown")
                    print(f"   {i+1}. {name} ({category})")
            
            results["passed"] += 1
            results["details"].append(f"✅ Restaurant discovery: {len(data)} restaurants found")
        else:
            print(f"❌ Restaurant discovery failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            results["failed"] += 1
            results["details"].append("❌ Restaurant discovery failed")
    except Exception as e:
        print(f"❌ Restaurant discovery exception: {str(e)}")
        results["failed"] += 1
        results["details"].append("❌ Restaurant discovery exception")
    
    print()
    
    # Step 3: Nearby Restaurants
    print("📍 TESTING NEARBY RESTAURANTS (Kadıköy)")
    print("-" * 30)
    
    try:
        params = {"lat": 41.0058, "lng": 29.0281, "radius": 50000}
        response = requests.get(f"{API_BASE}/restaurants/near", params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Nearby restaurants query successful")
            print(f"   Found {len(data)} restaurants within 50km of Kadıköy")
            
            if data and not business_id:
                business_id = data[0].get("id")
                print(f"   Using business ID from nearby: {business_id}")
            
            results["passed"] += 1
            results["details"].append(f"✅ Nearby restaurants: {len(data)} found")
        else:
            print(f"❌ Nearby restaurants failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            results["failed"] += 1
            results["details"].append("❌ Nearby restaurants failed")
    except Exception as e:
        print(f"❌ Nearby restaurants exception: {str(e)}")
        results["failed"] += 1
        results["details"].append("❌ Nearby restaurants exception")
    
    print()
    
    # Step 4: Business Products
    print("🛍️ TESTING BUSINESS PRODUCTS")
    print("-" * 30)
    
    if business_id:
        try:
            response = requests.get(f"{API_BASE}/businesses/{business_id}/products", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Business products query successful")
                print(f"   Found {len(data)} products for business {business_id}")
                results["passed"] += 1
                results["details"].append(f"✅ Business products: {len(data)} products found")
            else:
                print(f"❌ Business products failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                results["failed"] += 1
                results["details"].append("❌ Business products failed")
        except Exception as e:
            print(f"❌ Business products exception: {str(e)}")
            results["failed"] += 1
            results["details"].append("❌ Business products exception")
    else:
        print("❌ No business ID available for testing")
        results["failed"] += 1
        results["details"].append("❌ Business products: No business ID available")
    
    print()
    
    # Step 5: Profile Endpoints (require authentication)
    if auth_token:
        print("👤 TESTING PROFILE ENDPOINTS")
        print("-" * 30)
        
        # Test coupons
        try:
            response = requests.get(f"{API_BASE}/profile/coupons", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile coupons: {len(data)} coupons")
                results["passed"] += 1
                results["details"].append(f"✅ Profile coupons: {len(data)} coupons (mock data)")
            else:
                print(f"❌ Profile coupons failed: HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append("❌ Profile coupons failed")
        except Exception as e:
            print(f"❌ Profile coupons exception: {str(e)}")
            results["failed"] += 1
            results["details"].append("❌ Profile coupons exception")
        
        # Test discounts
        try:
            response = requests.get(f"{API_BASE}/profile/discounts", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile discounts: {len(data)} discounts")
                results["passed"] += 1
                results["details"].append(f"✅ Profile discounts: {len(data)} discounts (mock data)")
            else:
                print(f"❌ Profile discounts failed: HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append("❌ Profile discounts failed")
        except Exception as e:
            print(f"❌ Profile discounts exception: {str(e)}")
            results["failed"] += 1
            results["details"].append("❌ Profile discounts exception")
        
        # Test campaigns (public endpoint)
        try:
            response = requests.get(f"{API_BASE}/campaigns", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Active campaigns: {len(data)} campaigns")
                results["passed"] += 1
                results["details"].append(f"✅ Active campaigns: {len(data)} campaigns (mock data)")
            else:
                print(f"❌ Active campaigns failed: HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append("❌ Active campaigns failed")
        except Exception as e:
            print(f"❌ Active campaigns exception: {str(e)}")
            results["failed"] += 1
            results["details"].append("❌ Active campaigns exception")
        
        # Test payment methods
        try:
            response = requests.get(f"{API_BASE}/payment-methods", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Payment methods: {len(data)} methods")
                results["passed"] += 1
                results["details"].append(f"✅ Payment methods: {len(data)} methods (empty for new user)")
            else:
                print(f"❌ Payment methods failed: HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append("❌ Payment methods failed")
        except Exception as e:
            print(f"❌ Payment methods exception: {str(e)}")
            results["failed"] += 1
            results["details"].append("❌ Payment methods exception")
    else:
        print("👤 SKIPPING PROFILE ENDPOINTS (No authentication token)")
        results["failed"] += 4  # Count as 4 failed tests
        results["details"].extend([
            "❌ Profile coupons: No auth token",
            "❌ Profile discounts: No auth token", 
            "❌ Active campaigns: No auth token",
            "❌ Payment methods: No auth token"
        ])
    
    print()
    
    # Summary
    total = results["passed"] + results["failed"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print("=" * 60)
    print("🎯 ENHANCED TESTING SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    for detail in results["details"]:
        print(f"  {detail}")
    
    print(f"\n🌐 Backend URL: {BACKEND_URL}")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 70  # 70% success rate threshold

if __name__ == "__main__":
    success = test_comprehensive_customer_endpoints()
    sys.exit(0 if success else 1)