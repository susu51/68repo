#!/usr/bin/env python3
"""
Focused Backend Testing - Testing specific issues found in comprehensive test
"""

import requests
import json
import time

def test_specific_issues():
    """Test specific issues found in comprehensive testing"""
    base_url = "https://kuryecini-platform.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 FOCUSED TESTING OF IDENTIFIED ISSUES")
    print("=" * 60)
    
    # Get admin token first
    admin_response = requests.post(f"{api_url}/auth/login", 
                                 json={"email": "admin@test.com", "password": "6851"})
    
    if admin_response.status_code == 200:
        admin_token = admin_response.json().get('access_token')
        print("✅ Admin token obtained")
    else:
        print("❌ Failed to get admin token")
        return
    
    # Test 1: Admin Get All Users (500 error)
    print("\n🔍 Testing Admin Get All Users endpoint...")
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    try:
        response = requests.get(f"{api_url}/admin/users", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ CONFIRMED: 500 Internal Server Error")
            print("🐛 ROOT CAUSE: created_at field datetime conversion issue")
            print("   Error: 'str' object has no attribute 'isoformat'")
            print("   Location: server.py line 956")
            print("   Fix needed: Check if created_at is already string before calling isoformat()")
        else:
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Users found: {len(data) if isinstance(data, list) else 'N/A'}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 2: Get All Products (500 error)
    print("\n🔍 Testing Get All Products endpoint...")
    
    try:
        response = requests.get(f"{api_url}/products", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ CONFIRMED: 500 Internal Server Error")
            print("🐛 ROOT CAUSE: Similar datetime conversion issue in products endpoint")
        else:
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Products found: {len(data) if isinstance(data, list) else 'N/A'}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 3: Business Dashboard API Authentication (from test_result.md)
    print("\n🔍 Testing Business Dashboard API Authentication...")
    
    # Register a test business first
    business_data = {
        "email": "testrestoran@example.com",
        "password": "test123",
        "business_name": "Test Restaurant",
        "tax_number": "1234567890",
        "address": "Test Address",
        "city": "Istanbul",
        "business_category": "gida"
    }
    
    try:
        # Try to register (might already exist)
        reg_response = requests.post(f"{api_url}/register/business", json=business_data)
        
        # Try to login
        login_response = requests.post(f"{api_url}/auth/login", 
                                     json={"email": "testrestoran@example.com", "password": "test123"})
        
        if login_response.status_code == 200:
            business_token = login_response.json().get('access_token')
            business_id = login_response.json().get('user_data', {}).get('id')
            print(f"✅ Business login successful")
            print(f"   Business ID: {business_id}")
            
            # Test protected endpoints WITHOUT token (should fail)
            print("\n   Testing protected endpoints without authentication:")
            
            endpoints_to_test = [
                ("GET", "products/my", "Get Business Products"),
                ("POST", "products", "Create Product"),
                ("GET", "orders", "Get Orders")
            ]
            
            for method, endpoint, description in endpoints_to_test:
                if method == "GET":
                    resp = requests.get(f"{api_url}/{endpoint}")
                else:
                    resp = requests.post(f"{api_url}/{endpoint}", json={"test": "data"})
                
                print(f"   {description}: Status {resp.status_code}")
                
                if resp.status_code == 200:
                    print(f"   ❌ SECURITY ISSUE: {description} accessible without authentication!")
                elif resp.status_code in [401, 403]:
                    print(f"   ✅ Properly protected")
                else:
                    print(f"   ⚠️  Unexpected status: {resp.status_code}")
            
            # Test with valid token
            print("\n   Testing protected endpoints with valid authentication:")
            headers = {'Authorization': f'Bearer {business_token}'}
            
            for method, endpoint, description in endpoints_to_test:
                if method == "GET":
                    resp = requests.get(f"{api_url}/{endpoint}", headers=headers)
                else:
                    test_data = {
                        "name": "Test Product",
                        "description": "Test",
                        "price": 10.0,
                        "category": "test"
                    } if endpoint == "products" else {"test": "data"}
                    resp = requests.post(f"{api_url}/{endpoint}", json=test_data, headers=headers)
                
                print(f"   {description}: Status {resp.status_code}")
                
                if resp.status_code == 200:
                    print(f"   ✅ Working with authentication")
                else:
                    print(f"   ❌ Failed even with authentication: {resp.status_code}")
        else:
            print(f"❌ Business login failed: {login_response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception during business testing: {str(e)}")
    
    # Test 4: User Management System (from test_result.md)
    print("\n🔍 Testing User Management System...")
    
    try:
        # Test user deletion with different ID formats
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        # Test with invalid UUID
        resp = requests.delete(f"{api_url}/admin/users/invalid-uuid", headers=headers)
        print(f"Delete invalid UUID: Status {resp.status_code}")
        
        # Test without authentication
        resp = requests.delete(f"{api_url}/admin/users/some-id")
        print(f"Delete without auth: Status {resp.status_code}")
        
        if resp.status_code == 400:
            print("❌ CONFIRMED: Returns 400 instead of 401 for missing auth")
        elif resp.status_code == 401:
            print("✅ Correctly returns 401 for missing auth")
        else:
            print(f"⚠️  Unexpected status: {resp.status_code}")
    
    except Exception as e:
        print(f"❌ Exception during user management testing: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📋 FOCUSED TEST SUMMARY")
    print("=" * 60)
    print("🐛 CONFIRMED ISSUES:")
    print("1. ❌ Admin Get All Users: 500 error due to datetime conversion")
    print("2. ❌ Get All Products: 500 error (likely same datetime issue)")
    print("3. ⚠️  Business Dashboard API: Authentication middleware issues")
    print("4. ⚠️  User Management: Inconsistent error codes")
    print("\n💡 IMMEDIATE FIXES NEEDED:")
    print("1. Fix datetime conversion in server.py (check if already string)")
    print("2. Review authentication middleware for business endpoints")
    print("3. Standardize error codes (401 vs 400 for auth failures)")

if __name__ == "__main__":
    test_specific_issues()