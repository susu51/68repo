#!/usr/bin/env python3
"""
Approve test business for KYC to enable E2E testing
"""

import requests
import json

# Configuration
BACKEND_URL = "https://courier-stable.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}

def approve_test_business():
    session = requests.Session()
    
    # 1. Admin login
    print("🔐 Admin login...")
    response = session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return False
    
    admin_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin authenticated")
    
    # 2. Get test business user ID
    print("🔍 Finding test business...")
    response = session.get(f"{BACKEND_URL}/admin/businesses", headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get businesses: {response.text}")
        return False
    
    businesses = response.json()
    test_business = None
    
    for business in businesses:
        if business.get("email") == "testbusiness@example.com":
            test_business = business
            break
    
    if not test_business:
        print("❌ Test business not found")
        return False
    
    business_id = test_business.get("id") or test_business.get("_id")
    print(f"✅ Found test business: {business_id}")
    
    # 3. Approve the business
    print("✅ Approving test business...")
    approval_data = {"kyc_status": "approved"}
    response = session.patch(
        f"{BACKEND_URL}/admin/businesses/{business_id}/status",
        json=approval_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Test business approved successfully!")
        return True
    else:
        print(f"❌ Business approval failed: {response.text}")
        return False

if __name__ == "__main__":
    approve_test_business()