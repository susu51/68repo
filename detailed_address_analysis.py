#!/usr/bin/env python3
"""
DETAILED ADDRESS DATA ANALYSIS
=============================

Analyzing the exact address data returned by the API to understand
the structure and content for the user's integration issue.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://deliver-yemek.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testcustomer@example.com"
TEST_USER_PASSWORD = "test123"

def get_detailed_address_data():
    """Get detailed address data for analysis"""
    session = requests.Session()
    
    # Login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    data = response.json()
    jwt_token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {jwt_token}"})
    
    # Get addresses
    response = session.get(f"{BASE_URL}/user/addresses")
    if response.status_code != 200:
        print("❌ Address retrieval failed")
        return
    
    addresses = response.json()
    
    print("🔍 DETAILED ADDRESS DATA ANALYSIS")
    print("=" * 50)
    print(f"Total addresses for testcustomer@example.com: {len(addresses)}")
    print(f"Analysis time: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Show first 5 addresses with full details
    print("\n📍 SAMPLE ADDRESS DATA (First 5 addresses):")
    for i, addr in enumerate(addresses[:5]):
        print(f"\nAddress {i+1}:")
        print(f"  ID: {addr.get('id', 'N/A')}")
        print(f"  Label: {addr.get('label', 'N/A')}")
        print(f"  City: {addr.get('city', 'N/A')}")
        print(f"  Description: {addr.get('description', 'N/A')}")
        print(f"  Coordinates: lat={addr.get('lat', 'N/A')}, lng={addr.get('lng', 'N/A')}")
        print(f"  Full Address: {addr.get('full_address', 'N/A')}")
        print(f"  District: {addr.get('district', 'N/A')}")
        print(f"  Is Default: {addr.get('is_default', 'N/A')}")
        
        # Show all fields
        print(f"  All fields: {list(addr.keys())}")
    
    # Check for our test address
    print("\n🎯 LOOKING FOR TEST INTEGRATION ADDRESS:")
    test_address_found = False
    for addr in addresses:
        if addr.get('label') == 'Test Integration Address':
            test_address_found = True
            print("✅ Test Integration Address found:")
            print(json.dumps(addr, indent=2))
            break
    
    if not test_address_found:
        print("❌ Test Integration Address not found")
    
    # Address structure analysis
    print("\n📊 ADDRESS STRUCTURE ANALYSIS:")
    if addresses:
        sample_addr = addresses[0]
        print("Required fields for frontend integration:")
        required_fields = ['id', 'label', 'city', 'description', 'lat', 'lng']
        for field in required_fields:
            status = "✅" if field in sample_addr else "❌"
            value = sample_addr.get(field, 'MISSING')
            print(f"  {status} {field}: {value}")
        
        print("\nOptional fields:")
        optional_fields = ['full_address', 'district', 'is_default', 'created_at']
        for field in optional_fields:
            if field in sample_addr:
                print(f"  ✅ {field}: {sample_addr.get(field)}")
    
    print("\n💡 INTEGRATION ANALYSIS:")
    print("For the discovery page to show addresses, the frontend needs:")
    print("1. ✅ Address data is available via GET /api/user/addresses")
    print("2. ✅ Address data includes coordinates (lat, lng)")
    print("3. ✅ Address data includes city and description")
    print("4. ❓ Frontend must call this API and populate address selector")
    print("5. ❓ Frontend must use selected address for restaurant filtering")
    
    return addresses

if __name__ == "__main__":
    get_detailed_address_data()