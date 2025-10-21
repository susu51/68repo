#!/usr/bin/env python3
"""
Approve Aksaray businesses for testing - Version 2
"""

import requests
import json
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ai-order-debug.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def approve_aksaray_businesses():
    """Approve businesses with Aksaray in their city or address"""
    print("✅ APPROVING AKSARAY BUSINESSES V2")
    print("=" * 50)
    
    try:
        # Login as admin
        admin_login = {
            "email": "admin@kuryecini.com", 
            "password": "KuryeciniAdmin2024!"
        }
        login_response = requests.post(f"{API_BASE}/auth/login", json=admin_login, timeout=10)
        if login_response.status_code != 200:
            print(f"❌ Admin login failed: {login_response.status_code}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all users to find business users
        users_response = requests.get(f"{API_BASE}/admin/users", headers=headers, timeout=10)
        if users_response.status_code != 200:
            print(f"❌ Failed to get users: {users_response.status_code}")
            return
        
        users = users_response.json()
        
        # Find businesses with Aksaray in city or address
        aksaray_businesses = []
        for user in users:
            if user.get('role') == 'business':
                city = user.get('city', '').lower()
                address = user.get('address', '').lower()
                email = user.get('email', '').lower()
                
                if 'aksaray' in city or 'aksaray' in address or 'aksaray' in email:
                    aksaray_businesses.append(user)
        
        print(f"Found {len(aksaray_businesses)} Aksaray businesses:")
        for business in aksaray_businesses:
            kyc_status = business.get('kyc_status', 'N/A')
            print(f"  - {business.get('business_name', 'N/A')} ({business['email']}) - City: {business.get('city', 'N/A')} - KYC: {kyc_status}")
        print()
        
        approved_count = 0
        for business_user in aksaray_businesses:
            try:
                user_id = business_user['id']
                
                # Use the correct approve endpoint
                approve_response = requests.patch(
                    f"{API_BASE}/admin/users/{user_id}/approve",
                    headers=headers,
                    timeout=10
                )
                
                if approve_response.status_code == 200:
                    approved_count += 1
                    print(f"✅ Approved: {business_user.get('business_name', business_user['email'])}")
                else:
                    print(f"❌ Failed to approve {business_user['email']}: {approve_response.status_code} - {approve_response.text[:100]}")
            except Exception as e:
                print(f"❌ Error approving {business_user['email']}: {e}")
        
        print(f"\n📊 Approved {approved_count}/{len(aksaray_businesses)} Aksaray businesses")
        
    except Exception as e:
        print(f"❌ Error in approval process: {e}")
    
    print()

if __name__ == "__main__":
    approve_aksaray_businesses()