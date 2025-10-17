#!/usr/bin/env python3
"""
Fix business user KYC status and test menu creation
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://kuryecini-admin-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

BUSINESS_CREDENTIALS = {
    "email": "business@kuryecini.com",
    "password": "business123"
}

ADMIN_CREDENTIALS = {
    "email": "admin@kuryecini.com",
    "password": "KuryeciniAdmin2024!"
}

def main():
    session = requests.Session()
    
    print("🔧 FIXING BUSINESS USER KYC STATUS")
    print("=" * 50)
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    admin_response = session.post(f"{API_BASE}/auth/login", json=ADMIN_CREDENTIALS)
    
    if admin_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_response.status_code}")
        print(admin_response.text)
        return
    
    print("✅ Admin login successful")
    
    # Step 2: Get business user ID
    print("2. Getting business user info...")
    business_login = session.post(f"{API_BASE}/auth/login", json=BUSINESS_CREDENTIALS)
    
    if business_login.status_code != 200:
        print(f"❌ Business login failed: {business_login.status_code}")
        return
    
    business_data = business_login.json()
    business_id = business_data["user"]["id"]
    print(f"✅ Business ID: {business_id}")
    
    # Step 3: Re-login as admin (session might have changed)
    admin_response = session.post(f"{API_BASE}/auth/login", json=ADMIN_CREDENTIALS)
    
    # Step 4: Approve business
    print("3. Approving business...")
    approval_data = {
        "kyc_status": "approved"
    }
    
    approve_response = session.patch(
        f"{API_BASE}/admin/businesses/{business_id}/status",
        json=approval_data
    )
    
    print(f"Approval response status: {approve_response.status_code}")
    print(f"Approval response: {approve_response.text}")
    
    if approve_response.status_code == 200:
        print("✅ Business approved successfully")
    else:
        print(f"❌ Business approval failed: {approve_response.status_code}")
        
    # Step 5: Test business login again
    print("4. Testing business login after approval...")
    business_login2 = session.post(f"{API_BASE}/auth/login", json=BUSINESS_CREDENTIALS)
    
    if business_login2.status_code == 200:
        data = business_login2.json()
        print("✅ Business login successful after approval")
        print(f"User data: {data['user']}")
        
        # Step 6: Test menu creation
        print("5. Testing menu creation...")
        menu_item = {
            "title": "Test Pizza After Fix",
            "description": "Test pizza after KYC approval",
            "price": 50.00,
            "category": "food",
            "is_available": True
        }
        
        menu_response = session.post(f"{API_BASE}/business/menu", json=menu_item)
        print(f"Menu creation status: {menu_response.status_code}")
        print(f"Menu creation response: {menu_response.text}")
        
        if menu_response.status_code in [200, 201]:
            print("✅ Menu item created successfully!")
        else:
            print(f"❌ Menu creation failed: {menu_response.status_code}")
    else:
        print(f"❌ Business login failed after approval: {business_login2.status_code}")

if __name__ == "__main__":
    main()