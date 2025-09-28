#!/usr/bin/env python3
"""
Test normal user login functionality
"""

import requests
import json
import uuid

def test_normal_user_login():
    print("Testing normal user login...")
    
    # Create a unique customer
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    
    # Register customer
    customer_data = {
        "email": unique_email,
        "password": "test123",
        "first_name": "Test",
        "last_name": "User",
        "city": "İstanbul"
    }
    
    reg_response = requests.post(
        "https://delivertr-fix.preview.emergentagent.com/api/register/customer",
        json=customer_data
    )
    
    print(f"Registration response: {reg_response.status_code}")
    if reg_response.status_code == 200:
        print("✅ Customer registration successful")
        
        # Test login
        login_data = {
            "email": unique_email,
            "password": "test123"
        }
        
        login_response = requests.post(
            "https://delivertr-fix.preview.emergentagent.com/api/auth/login",
            json=login_data
        )
        
        print(f"Login response: {login_response.status_code}")
        if login_response.status_code == 200:
            user_data = login_response.json().get('user_data', {})
            print(f"✅ Normal user login successful")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   User Type: {login_response.json().get('user_type')}")
            
            if user_data.get('role') == 'customer':
                print("✅ Normal user login returns correct role")
                return True
            else:
                print(f"❌ Expected customer role, got {user_data.get('role')}")
                return False
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
    else:
        print(f"❌ Registration failed: {reg_response.text}")
        return False

if __name__ == "__main__":
    test_normal_user_login()