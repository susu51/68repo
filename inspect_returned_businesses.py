#!/usr/bin/env python3
"""
Inspect what businesses are actually being returned by the city catalog endpoint
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com/api"

def inspect_businesses():
    """Inspect businesses returned by city catalog endpoint"""
    
    # Test with Ankara
    params = {
        "city": "ankara",
        "lat": 39.9334,
        "lng": 32.8597,
        "radius_km": 50
    }
    
    session = requests.Session()
    response = session.get(f"{BACKEND_URL}/catalog/city-nearby", params=params)
    
    if response.status_code == 200:
        businesses = response.json()
        
        print(f"🔍 Found {len(businesses)} businesses for Ankara:")
        print("=" * 60)
        
        for i, business in enumerate(businesses, 1):
            print(f"{i}. Business Details:")
            print(f"   ID: {business.get('id', 'N/A')}")
            print(f"   Name: {business.get('name', 'N/A')}")
            print(f"   Address: {business.get('address', {})}")
            print(f"   Distance: {business.get('distance', 'N/A')}m")
            print(f"   Menu Items: {len(business.get('menu_snippet', []))}")
            
            # Check address structure
            address = business.get('address', {})
            if isinstance(address, dict):
                print(f"   Address Structure:")
                for key, value in address.items():
                    print(f"     {key}: {value}")
            else:
                print(f"   Address (string): {address}")
            
            print()
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    inspect_businesses()