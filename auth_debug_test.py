#!/usr/bin/env python3
"""
Debug authentication issues
"""

import requests
import json

BACKEND_URL = "https://food-dash-87.preview.emergentagent.com/api"
CUSTOMER_EMAIL = "test@kuryecini.com"
CUSTOMER_PASSWORD = "test123"

def test_auth_debug():
    session = requests.Session()
    
    print("🔐 Testing Authentication Debug...")
    
    # Test login
    login_data = {
        "email": CUSTOMER_EMAIL,
        "password": CUSTOMER_PASSWORD
    }
    
    response = session.post(
        f"{BACKEND_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Login Response Status: {response.status_code}")
    print(f"Login Response Headers: {dict(response.headers)}")
    print(f"Login Response Cookies: {dict(response.cookies)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Login Response Data: {json.dumps(data, indent=2)}")
        
        # Test /me with cookies only (no Authorization header)
        print("\n🍪 Testing /me with cookies only...")
        me_response = session.get(f"{BACKEND_URL}/me")
        print(f"/me Response Status: {me_response.status_code}")
        print(f"/me Response: {me_response.text}")
        
        # Test /me with JWT token
        if "access_token" in data:
            print("\n🔑 Testing /me with JWT token...")
            jwt_token = data["access_token"]
            me_jwt_response = session.get(
                f"{BACKEND_URL}/me",
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
            print(f"/me JWT Response Status: {me_jwt_response.status_code}")
            print(f"/me JWT Response: {me_jwt_response.text}")
        
        # Test address endpoints (should work with cookies)
        print("\n🏠 Testing address endpoints with cookies...")
        addr_response = session.get(f"{BACKEND_URL}/me/addresses")
        print(f"Addresses Response Status: {addr_response.status_code}")
        print(f"Addresses Response: {addr_response.text[:200]}...")

if __name__ == "__main__":
    test_auth_debug()