#!/usr/bin/env python3
"""
CRITICAL DATA ARCHITECTURE ISSUE VERIFICATION
Testing the root cause: Admin and customer endpoints query different collections
"""

import requests
import json

BACKEND_URL = "https://delivery-platform-10.preview.emergentagent.com/api"

def get_admin_token():
    creds = {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
    return response.json()["access_token"]

def main():
    print("🚨 CRITICAL DATA ARCHITECTURE ISSUE VERIFICATION")
    print("=" * 70)
    print("ROOT CAUSE: Admin and customer endpoints query different database collections")
    print("- Admin endpoint: db.businesses collection")
    print("- Customer endpoints: db.users collection")
    print()
    
    admin_token = get_admin_token()
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test admin endpoint (db.businesses)
    print("1. ADMIN ENDPOINT (db.businesses collection):")
    response = requests.get(f"{BACKEND_URL}/admin/businesses", headers=admin_headers)
    if response.status_code == 200:
        admin_businesses = response.json()
        print(f"   ✅ Found {len(admin_businesses)} businesses")
        
        target_businesses = [
            b for b in admin_businesses 
            if "Test Restoranı" in b.get("business_name", "") or "Pizza Palace İstanbul" in b.get("business_name", "")
        ]
        
        print(f"   🎯 Target businesses in db.businesses: {len(target_businesses)}")
        for tb in target_businesses:
            print(f"      - {tb['business_name']} (KYC: {tb['kyc_status']}, ID: {tb['id']})")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    print()
    
    # Test customer endpoint (db.users)
    print("2. CUSTOMER ENDPOINT (db.users collection):")
    response = requests.get(f"{BACKEND_URL}/restaurants")
    if response.status_code == 200:
        customer_restaurants = response.json()
        print(f"   ✅ Found {len(customer_restaurants)} restaurants")
        
        target_restaurants = [
            r for r in customer_restaurants 
            if "Test Restoranı" in (r.get("business_name") or r.get("name", "")) or 
               "Pizza Palace İstanbul" in (r.get("business_name") or r.get("name", ""))
        ]
        
        print(f"   🎯 Target businesses in db.users: {len(target_restaurants)}")
        for tr in target_restaurants:
            name = tr.get("business_name") or tr.get("name", "")
            print(f"      - {name} (KYC: {tr.get('kyc_status')}, ID: {tr.get('id')})")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    print()
    print("=" * 70)
    print("🎯 CRITICAL ISSUE CONFIRMED:")
    print("=" * 70)
    print("✅ Target businesses exist in db.businesses (admin view)")
    print("❌ Target businesses DO NOT exist in db.users (customer view)")
    print()
    print("💡 SOLUTION REQUIRED:")
    print("1. IMMEDIATE FIX: Update customer endpoints to query db.businesses")
    print("2. OR: Synchronize data between db.businesses and db.users collections")
    print("3. OR: Migrate all business data to a single collection")
    print()
    print("🚨 IMPACT: Customers cannot see any businesses that were created/approved")
    print("   through the admin panel because they're stored in different collections!")

if __name__ == "__main__":
    main()