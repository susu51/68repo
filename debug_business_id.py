#!/usr/bin/env python3
"""
Debug Business ID Mismatch Issue
"""

import requests
import json

BACKEND_URL = "https://deliver-yemek.preview.emergentagent.com/api"

# Login as business
business_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"email": "testbusiness@example.com", "password": "test123"}
)

if business_response.status_code == 200:
    business_data = business_response.json()
    business_user = business_data["user"]
    business_token = business_data["access_token"]
    
    print(f"✅ Business login successful")
    print(f"Business ID: {business_user.get('id')}")
    print(f"Business Name: {business_user.get('business_name')}")
    print()
    
    # Login as customer
    customer_response = requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": "testcustomer@example.com", "password": "test123"}
    )
    
    if customer_response.status_code == 200:
        customer_token = customer_response.json()["access_token"]
        print(f"✅ Customer login successful")
        
        # Get nearby businesses
        headers = {"Authorization": f"Bearer {customer_token}"}
        params = {"lat": 40.9833, "lng": 29.0167, "radius": 5000}
        
        nearby_response = requests.get(
            f"{BACKEND_URL}/nearby/businesses",
            headers=headers,
            params=params
        )
        
        if nearby_response.status_code == 200:
            businesses = nearby_response.json()
            print(f"Found {len(businesses)} nearby businesses:")
            for business in businesses:
                print(f"  - ID: {business.get('id')}")
                print(f"    Name: {business.get('name')}")
                print(f"    Distance: {business.get('distance_m')}m")
                print()
        
        print(f"Business User ID: {business_user.get('id')}")
        print(f"Available Business IDs: {[b.get('id') for b in businesses]}")
        
        # Check if they match
        business_ids = [b.get('id') for b in businesses]
        if business_user.get('id') in business_ids:
            print("✅ Business ID matches - should work")
        else:
            print("❌ Business ID mismatch - this is the issue")
            
else:
    print(f"❌ Business login failed: {business_response.status_code}")
    print(f"Response: {business_response.text}")