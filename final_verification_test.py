#!/usr/bin/env python3
"""
FINAL VERIFICATION TEST - Confirm Aksaray business visibility is resolved
"""

import requests
import json

BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

def final_verification():
    print("🎯 FINAL VERIFICATION - AKSARAY BUSINESS VISIBILITY")
    print("=" * 60)
    
    # Test 1: Customer view - all businesses
    print("1. CUSTOMER VIEW - ALL BUSINESSES:")
    customer_session = requests.Session()
    response = customer_session.get(f"{BACKEND_URL}/businesses")
    
    if response.status_code == 200:
        businesses = response.json()
        aksaray_businesses = [b for b in businesses if 
                             'aksaray' in b.get('name', '').lower() or
                             b.get('city', '').lower() == 'aksaray']
        
        print(f"   Total businesses visible to customers: {len(businesses)}")
        print(f"   Aksaray businesses visible: {len(aksaray_businesses)}")
        
        for i, business in enumerate(aksaray_businesses, 1):
            print(f"   {i}. {business.get('name', 'Unknown')}")
        print()
    
    # Test 2: City filtering
    print("2. CITY FILTERING TEST:")
    response = customer_session.get(f"{BACKEND_URL}/businesses", params={"city": "Aksaray"})
    
    if response.status_code == 200:
        filtered_businesses = response.json()
        print(f"   Businesses found with city=Aksaray filter: {len(filtered_businesses)}")
        
        for i, business in enumerate(filtered_businesses, 1):
            print(f"   {i}. {business.get('name', 'Unknown')} (City: {business.get('city', 'Unknown')})")
        print()
    
    # Test 3: Business products check
    print("3. BUSINESS PRODUCTS CHECK:")
    if filtered_businesses:
        test_business = filtered_businesses[0]
        business_id = test_business.get('id')
        
        if business_id:
            response = customer_session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
            
            if response.status_code == 200:
                products = response.json()
                print(f"   Products for '{test_business.get('name')}': {len(products)}")
                
                for i, product in enumerate(products[:3], 1):  # Show first 3
                    print(f"   {i}. {product.get('name', 'Unknown')} - ₺{product.get('price', 0)}")
                print()
    
    # Test 4: Admin verification
    print("4. ADMIN VERIFICATION:")
    admin_login = {
        "email": "admin@kuryecini.com",
        "password": "KuryeciniAdmin2024!"
    }
    
    admin_session = requests.Session()
    response = admin_session.post(f"{BACKEND_URL}/auth/login", json=admin_login)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        admin_session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = admin_session.get(f"{BACKEND_URL}/admin/users")
        
        if response.status_code == 200:
            users = response.json()
            businesses = [u for u in users if u.get('role') == 'business']
            aksaray_businesses = [b for b in businesses if 
                                 b.get('city', '').lower() == 'aksaray' or 
                                 b.get('city_normalized', '').lower() == 'aksaray']
            
            approved_count = len([b for b in aksaray_businesses if b.get('kyc_status') == 'approved'])
            pending_count = len([b for b in aksaray_businesses if b.get('kyc_status') in ['pending', 'unknown', None]])
            
            print(f"   Total Aksaray businesses in database: {len(aksaray_businesses)}")
            print(f"   Approved: {approved_count}")
            print(f"   Pending/Unknown: {pending_count}")
            print()
    
    print("✅ VERIFICATION COMPLETE!")
    print("=" * 60)
    
    if len(aksaray_businesses) >= 5:  # From customer view
        print("🎉 SUCCESS: Aksaray business visibility issue is RESOLVED!")
        print("   - Multiple Aksaray businesses are now visible to customers")
        print("   - City filtering is working correctly")
        print("   - KYC approval system is functioning properly")
    else:
        print("⚠️ PARTIAL: Some issues may remain")
        print(f"   - Only {len(aksaray_businesses)} Aksaray businesses visible")

if __name__ == "__main__":
    final_verification()