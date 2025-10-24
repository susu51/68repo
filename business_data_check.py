#!/usr/bin/env python3
"""
Check business data in database to understand city/district information
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com/api"

# Admin credentials
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

def check_business_data():
    """Check business data in database"""
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
    
    # Get all businesses
    response = session.get(f"{BACKEND_URL}/admin/businesses")
    
    if response.status_code == 200:
        businesses = response.json()
        if isinstance(businesses, dict):
            businesses = businesses.get("businesses", [])
        
        print(f"\n📊 Found {len(businesses)} businesses in database:")
        print("=" * 80)
        
        for i, business in enumerate(businesses, 1):
            print(f"{i}. Business: {business.get('business_name', 'N/A')}")
            print(f"   Email: {business.get('email', 'N/A')}")
            print(f"   City: {business.get('city', 'N/A')}")
            print(f"   District: {business.get('district', 'N/A')}")
            print(f"   KYC Status: {business.get('kyc_status', 'N/A')}")
            print(f"   Is Active: {business.get('is_active', 'N/A')}")
            print(f"   Address: {business.get('address', 'N/A')}")
            if business.get('lat') and business.get('lng'):
                print(f"   GPS: {business.get('lat')}, {business.get('lng')}")
            print()
        
        # Check specifically for testbusiness@example.com
        test_business = None
        for business in businesses:
            if business.get('email') == 'testbusiness@example.com':
                test_business = business
                break
        
        if test_business:
            print("🎯 TESTBUSINESS@EXAMPLE.COM DATA:")
            print("=" * 50)
            print(f"Business Name: {test_business.get('business_name', 'N/A')}")
            print(f"City: {test_business.get('city', 'N/A')}")
            print(f"District: {test_business.get('district', 'N/A')}")
            print(f"KYC Status: {test_business.get('kyc_status', 'N/A')}")
            print(f"Address: {test_business.get('address', 'N/A')}")
            if test_business.get('lat') and test_business.get('lng'):
                print(f"GPS Coordinates: {test_business.get('lat')}, {test_business.get('lng')}")
            else:
                print("GPS Coordinates: Not set")
        else:
            print("❌ testbusiness@example.com not found in database")
    
    else:
        print(f"❌ Failed to get businesses: {response.status_code}")

if __name__ == "__main__":
    check_business_data()