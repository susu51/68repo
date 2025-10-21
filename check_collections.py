#!/usr/bin/env python3
"""
Check what collections exist in the database and their structure
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Admin credentials
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

def check_collections():
    """Check database collections and structure"""
    session = requests.Session()
    
    # Login as admin
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "access_token" in data:
            token = data["access_token"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            print("✅ Admin login successful")
        else:
            print("❌ Admin login failed")
            return
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        return
    
    # Check if there are any businesses with geospatial data
    print("\n🔍 Checking business data structure...")
    
    # Get businesses from admin endpoint
    response = session.get(f"{BACKEND_URL}/admin/businesses")
    
    if response.status_code == 200:
        businesses = response.json()
        if isinstance(businesses, dict):
            businesses = businesses.get("businesses", [])
        
        print(f"Found {len(businesses)} businesses in users collection")
        
        if businesses:
            # Check first business structure
            first_business = businesses[0]
            print(f"\nFirst business structure:")
            print(f"  ID: {first_business.get('id', 'N/A')}")
            print(f"  Name: {first_business.get('business_name', 'N/A')}")
            print(f"  City: {first_business.get('city', 'N/A')}")
            print(f"  District: {first_business.get('district', 'N/A')}")
            print(f"  Address: {first_business.get('address', 'N/A')}")
            print(f"  Lat/Lng: {first_business.get('lat', 'N/A')}, {first_business.get('lng', 'N/A')}")
            print(f"  Is Active: {first_business.get('is_active', 'N/A')}")
            print(f"  KYC Status: {first_business.get('kyc_status', 'N/A')}")
            
            # Check if any have address.city_slug structure
            has_address_structure = any(
                isinstance(b.get('address'), dict) and 'city_slug' in b.get('address', {})
                for b in businesses
            )
            
            print(f"\nBusinesses with address.city_slug structure: {has_address_structure}")
            
            # Check if any have geospatial coordinates
            has_coordinates = any(
                b.get('lat') is not None and b.get('lng') is not None
                for b in businesses
            )
            
            print(f"Businesses with lat/lng coordinates: {has_coordinates}")
            
            # Show all unique city values
            cities = set()
            for b in businesses:
                if b.get('city'):
                    cities.add(b.get('city'))
            
            print(f"Cities in database: {sorted(cities)}")
    
    else:
        print(f"❌ Failed to get businesses: {response.status_code}")

if __name__ == "__main__":
    check_collections()