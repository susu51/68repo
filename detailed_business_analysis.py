#!/usr/bin/env python3
"""
DETAILED BUSINESS ANALYSIS - Check specific business statuses
"""

import requests
import json

BACKEND_URL = "https://kuryecini-auth.preview.emergentagent.com/api"

def analyze_businesses():
    # Admin login
    admin_login = {
        "email": "admin@kuryecini.com",
        "password": "KuryeciniAdmin2024!"
    }
    
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/auth/login", json=admin_login)
    
    if response.status_code != 200:
        print("Admin login failed")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Get all users
    response = session.get(f"{BACKEND_URL}/admin/users")
    if response.status_code != 200:
        print("Failed to get users")
        return
    
    users = response.json()
    businesses = [u for u in users if u.get('role') == 'business']
    aksaray_businesses = [b for b in businesses if 
                         b.get('city', '').lower() == 'aksaray' or 
                         b.get('city_normalized', '').lower() == 'aksaray']
    
    print(f"TOTAL BUSINESSES: {len(businesses)}")
    print(f"AKSARAY BUSINESSES: {len(aksaray_businesses)}")
    print()
    
    print("AKSARAY BUSINESS DETAILS:")
    print("=" * 80)
    
    for i, business in enumerate(aksaray_businesses, 1):
        print(f"{i}. {business.get('business_name', 'Unknown')}")
        print(f"   Email: {business.get('email', 'Unknown')}")
        print(f"   City: {business.get('city', 'Unknown')}")
        print(f"   KYC Status: {business.get('kyc_status', 'unknown')}")
        print(f"   ID: {business.get('id', 'Unknown')}")
        print()
    
    # Check customer view
    customer_session = requests.Session()
    response = customer_session.get(f"{BACKEND_URL}/businesses")
    
    if response.status_code == 200:
        customer_businesses = response.json()
        aksaray_customer = [b for b in customer_businesses if 
                           b.get('city', '').lower() == 'aksaray' or
                           'aksaray' in b.get('name', '').lower()]
        
        print("CUSTOMER VIEW - AKSARAY BUSINESSES:")
        print("=" * 50)
        for i, business in enumerate(aksaray_customer, 1):
            print(f"{i}. {business.get('name', 'Unknown')}")
            print(f"   ID: {business.get('id', 'Unknown')}")
            print()
    
    # Approve all pending Aksaray businesses
    pending_businesses = [b for b in aksaray_businesses if b.get('kyc_status') in ['unknown', 'pending', None]]
    
    if pending_businesses:
        print(f"APPROVING {len(pending_businesses)} PENDING AKSARAY BUSINESSES:")
        print("=" * 60)
        
        for business in pending_businesses:
            business_id = business.get('id')
            business_name = business.get('business_name', 'Unknown')
            
            if business_id:
                response = session.patch(f"{BACKEND_URL}/admin/users/{business_id}/approve")
                
                if response.status_code == 200:
                    print(f"✅ Approved: {business_name} (ID: {business_id})")
                else:
                    print(f"❌ Failed to approve: {business_name} (ID: {business_id})")
        
        print()
        print("CHECKING CUSTOMER VIEW AFTER APPROVALS:")
        print("=" * 50)
        
        # Check customer view again
        response = customer_session.get(f"{BACKEND_URL}/businesses")
        
        if response.status_code == 200:
            customer_businesses = response.json()
            aksaray_customer = [b for b in customer_businesses if 
                               b.get('city', '').lower() == 'aksaray' or
                               'aksaray' in b.get('name', '').lower()]
            
            print(f"NOW CUSTOMERS SEE {len(aksaray_customer)} AKSARAY BUSINESSES:")
            for i, business in enumerate(aksaray_customer, 1):
                print(f"{i}. {business.get('name', 'Unknown')}")
                print(f"   ID: {business.get('id', 'Unknown')}")
                print()

if __name__ == "__main__":
    analyze_businesses()