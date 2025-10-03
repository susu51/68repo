#!/usr/bin/env python3
"""
Quick test for phone authentication endpoints
"""

import requests
import json

BASE_URL = "https://kuryecini-delivery-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_phone_auth():
    print("Testing phone authentication...")
    
    # Test OTP request
    phone_data = {"phone": "+905551234567"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/phone/request-otp", 
                               json=phone_data, 
                               headers=HEADERS, 
                               timeout=30)
        
        print(f"OTP Request Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"OTP Response: {json.dumps(data, indent=2)}")
            
            # Test OTP verification
            if data.get("mock_otp"):
                verify_data = {
                    "phone": phone_data["phone"],
                    "otp_code": data["mock_otp"]
                }
                
                verify_response = requests.post(f"{BASE_URL}/auth/phone/verify-otp",
                                              json=verify_data,
                                              headers=HEADERS,
                                              timeout=30)
                
                print(f"OTP Verify Status: {verify_response.status_code}")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"Verify Response: {json.dumps(verify_data, indent=2)}")
                else:
                    print(f"Verify Error: {verify_response.text}")
        else:
            print(f"OTP Request Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_profile_endpoint():
    print("\nTesting profile endpoint with customer auth...")
    
    # Login as customer first
    login_data = {
        "email": "testcustomer@example.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json=login_data, 
                               headers=HEADERS, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            auth_headers = HEADERS.copy()
            auth_headers["Authorization"] = f"Bearer {token}"
            
            # Test profile endpoint
            profile_response = requests.get(f"{BASE_URL}/profile/me",
                                          headers=auth_headers,
                                          timeout=30)
            
            print(f"Profile Status: {profile_response.status_code}")
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print(f"Profile Data: {json.dumps(profile_data, indent=2)}")
            else:
                print(f"Profile Error: {profile_response.text}")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_phone_auth()
    test_profile_endpoint()