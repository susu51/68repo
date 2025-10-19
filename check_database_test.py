#!/usr/bin/env python3
"""
Database Check and Test Data Creation
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://kuryecini-ai-tools.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def check_database_collections():
    """Check what data exists in the database"""
    print("🔍 CHECKING DATABASE COLLECTIONS")
    print("=" * 50)
    
    # Check businesses
    try:
        response = requests.get(f"{API_BASE}/businesses", timeout=10)
        if response.status_code == 200:
            businesses = response.json()
            print(f"✅ Businesses collection: {len(businesses)} records")
            if businesses:
                print(f"   Sample business: {businesses[0]}")
        else:
            print(f"❌ Businesses endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Businesses check failed: {e}")
    
    # Check restaurants
    try:
        response = requests.get(f"{API_BASE}/restaurants", timeout=10)
        if response.status_code == 200:
            restaurants = response.json()
            print(f"✅ Restaurants endpoint: {len(restaurants)} records")
            if restaurants:
                print(f"   Sample restaurant: {restaurants[0]}")
        else:
            print(f"❌ Restaurants endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Restaurants check failed: {e}")
    
    # Check users (to see if businesses are stored there)
    try:
        # Try to login as admin to access admin endpoints
        admin_login = {
            "email": "admin@kuryecini.com",
            "password": "KuryeciniAdmin2024!"
        }
        login_response = requests.post(f"{API_BASE}/auth/login", json=admin_login, timeout=10)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get all users
            users_response = requests.get(f"{API_BASE}/admin/users", headers=headers, timeout=10)
            if users_response.status_code == 200:
                users = users_response.json()
                business_users = [u for u in users if u.get('role') == 'business']
                print(f"✅ Users collection: {len(users)} total users")
                print(f"   Business users: {len(business_users)}")
                if business_users:
                    print(f"   Sample business user: {business_users[0]}")
            else:
                print(f"❌ Users endpoint error: {users_response.status_code}")
        else:
            print(f"❌ Admin login failed: {login_response.status_code}")
    except Exception as e:
        print(f"❌ Users check failed: {e}")
    
    print()

def create_test_businesses():
    """Create test businesses with Aksaray city for testing"""
    print("🏗️ CREATING TEST BUSINESSES")
    print("=" * 50)
    
    # Test businesses to create
    test_businesses = [
        {
            "email": "aksaray-restaurant1@test.com",
            "password": "test123",
            "business_name": "Aksaray Kebap Evi",
            "tax_number": "1234567890",
            "address": "Merkez Mahallesi, Aksaray",
            "city": "Aksaray",
            "business_category": "gida",
            "description": "Geleneksel Aksaray lezzetleri"
        },
        {
            "email": "aksaray-restaurant2@test.com", 
            "password": "test123",
            "business_name": "Aksaray Pizza Palace",
            "tax_number": "1234567891",
            "address": "Cumhuriyet Caddesi, Aksaray Merkez",
            "city": "aksaray",  # lowercase to test normalization
            "business_category": "gida",
            "description": "En iyi pizza Aksaray'da"
        },
        {
            "email": "aksaray-restaurant3@test.com",
            "password": "test123", 
            "business_name": "AKSARAY Döner Salonu",
            "tax_number": "1234567892",
            "address": "Atatürk Bulvarı, AKSARAY",
            "city": "AKSARAY",  # uppercase to test normalization
            "business_category": "gida",
            "description": "Lezzetli döner ve pide"
        }
    ]
    
    created_count = 0
    for business in test_businesses:
        try:
            response = requests.post(f"{API_BASE}/register/business", json=business, timeout=10)
            if response.status_code == 200:
                created_count += 1
                print(f"✅ Created: {business['business_name']}")
            else:
                print(f"❌ Failed to create {business['business_name']}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ Error creating {business['business_name']}: {e}")
    
    print(f"\n📊 Created {created_count}/{len(test_businesses)} test businesses")
    print()

def approve_test_businesses():
    """Approve test businesses for KYC so they appear in public endpoints"""
    print("✅ APPROVING TEST BUSINESSES")
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
        business_users = [u for u in users if u.get('role') == 'business' and 'aksaray' in u.get('email', '').lower()]
        
        approved_count = 0
        for business_user in business_users:
            try:
                # Approve the business user
                approve_data = {"kyc_status": "approved"}
                approve_response = requests.patch(
                    f"{API_BASE}/admin/users/{business_user['id']}/approve",
                    json=approve_data,
                    headers=headers,
                    timeout=10
                )
                if approve_response.status_code == 200:
                    approved_count += 1
                    print(f"✅ Approved: {business_user.get('business_name', business_user['email'])}")
                else:
                    print(f"❌ Failed to approve {business_user['email']}: {approve_response.status_code}")
            except Exception as e:
                print(f"❌ Error approving {business_user['email']}: {e}")
        
        print(f"\n📊 Approved {approved_count}/{len(business_users)} test businesses")
        
    except Exception as e:
        print(f"❌ Error in approval process: {e}")
    
    print()

if __name__ == "__main__":
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print()
    
    # Check current database state
    check_database_collections()
    
    # Create test businesses
    create_test_businesses()
    
    # Approve test businesses
    approve_test_businesses()
    
    # Check database state again
    print("🔍 FINAL DATABASE STATE")
    print("=" * 50)
    check_database_collections()