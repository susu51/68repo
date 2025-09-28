#!/usr/bin/env python3
"""
Quick test to verify admin token validation issue
"""

import requests
import json

# Test with legacy admin endpoint token
def test_legacy_admin_token():
    print("Testing legacy admin token...")
    
    # Get legacy admin token
    response = requests.post(
        "https://delivertr-fix.preview.emergentagent.com/api/auth/admin",
        json={"password": "6851"}
    )
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"Legacy admin token: {token[:50]}...")
        
        # Test with admin endpoint
        headers = {'Authorization': f'Bearer {token}'}
        admin_response = requests.get(
            "https://delivertr-fix.preview.emergentagent.com/api/admin/users",
            headers=headers
        )
        
        print(f"Admin endpoint response: {admin_response.status_code}")
        if admin_response.status_code != 200:
            print(f"Error: {admin_response.text}")
        else:
            print("✅ Legacy admin token works!")
    else:
        print(f"Failed to get legacy admin token: {response.status_code}")

# Test with new admin login token
def test_new_admin_token():
    print("\nTesting new admin login token...")
    
    # Get new admin token
    response = requests.post(
        "https://delivertr-fix.preview.emergentagent.com/api/auth/login",
        json={"email": "any@email.com", "password": "6851"}
    )
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"New admin token: {token[:50]}...")
        
        # Test with admin endpoint
        headers = {'Authorization': f'Bearer {token}'}
        admin_response = requests.get(
            "https://delivertr-fix.preview.emergentagent.com/api/admin/users",
            headers=headers
        )
        
        print(f"Admin endpoint response: {admin_response.status_code}")
        if admin_response.status_code != 200:
            print(f"Error: {admin_response.text}")
        else:
            print("✅ New admin token works!")
    else:
        print(f"Failed to get new admin token: {response.status_code}")

if __name__ == "__main__":
    test_legacy_admin_token()
    test_new_admin_token()