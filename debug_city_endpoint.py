#!/usr/bin/env python3
"""
Debug the city catalog endpoint to understand why no businesses are returned
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"

def debug_endpoint():
    """Debug the city catalog endpoint"""
    
    # Test different city variations
    test_cases = [
        {"city": "aksaray", "lat": 39.9334, "lng": 32.8597},
        {"city": "Aksaray", "lat": 39.9334, "lng": 32.8597},
        {"city": "nigde", "lat": 39.9334, "lng": 32.8597},
        {"city": "Niğde", "lat": 39.9334, "lng": 32.8597},
        {"city": "istanbul", "lat": 41.0082, "lng": 28.9784},
        {"city": "İstanbul", "lat": 41.0082, "lng": 28.9784},
    ]
    
    session = requests.Session()
    
    for case in test_cases:
        print(f"\n🔍 Testing city: {case['city']}")
        print("=" * 50)
        
        params = {
            "city": case["city"],
            "lat": case["lat"],
            "lng": case["lng"],
            "radius_km": 100  # Large radius
        }
        
        try:
            response = session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else []
                print(f"Businesses found: {len(businesses)}")
                
                if businesses:
                    for i, business in enumerate(businesses, 1):
                        print(f"  {i}. {business.get('name', 'N/A')}")
                        print(f"     Address: {business.get('address', {})}")
                        print(f"     Distance: {business.get('distance', 'N/A')}m")
                else:
                    print("  No businesses found")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    # Also test the endpoint with missing parameters to see error handling
    print(f"\n🔍 Testing parameter validation")
    print("=" * 50)
    
    # Test missing city
    try:
        params = {"lat": 39.9334, "lng": 32.8597}
        response = session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
        print(f"Missing city - Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"Missing city test exception: {e}")
    
    # Test missing coordinates
    try:
        params = {"city": "aksaray"}
        response = session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
        print(f"Missing coords - Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"Missing coords test exception: {e}")

if __name__ == "__main__":
    debug_endpoint()