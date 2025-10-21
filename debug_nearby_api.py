#!/usr/bin/env python3
"""
Debug Nearby Businesses API Response
"""

import requests
import json

BACKEND_URL = "https://ai-order-debug.preview.emergentagent.com/api"

# Login as customer
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"email": "testcustomer@example.com", "password": "test123"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✅ Customer login successful")
    
    # Test nearby businesses API
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "lat": 40.9833,
        "lng": 29.0167,
        "radius": 5000
    }
    
    response = requests.get(
        f"{BACKEND_URL}/nearby/businesses",
        headers=headers,
        params=params
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")