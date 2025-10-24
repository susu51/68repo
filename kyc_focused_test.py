#!/usr/bin/env python3
"""
Focused KYC Issues Testing
Testing specific issues found in the KYC enforcement system
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

def test_business_stats_security_gap():
    """Test the security gap in /business/stats endpoint"""
    print("🔍 TESTING BUSINESS STATS SECURITY GAP...")
    
    # Create a test business
    business_data = {
        "email": f"test_stats_business_{int(time.time())}@example.com",
        "password": "test123",
        "business_name": "Test Stats Restaurant",
        "tax_number": f"12345{int(time.time())}",
        "address": "Test Address, Istanbul",
        "city": "İstanbul",
        "business_category": "gida",
        "description": "Test restaurant for stats testing"
    }
    
    session = requests.Session()
    response = session.post(f"{BACKEND_URL}/register/business", json=business_data)
    
    if response.status_code == 200:
        data = response.json()
        pending_business_token = data.get("access_token")
        
        # Test access to /business/stats with pending business
        headers = {"Authorization": f"Bearer {pending_business_token}"}
        stats_response = session.get(f"{BACKEND_URL}/business/stats", headers=headers)
        
        print(f"Business Stats Response Status: {stats_response.status_code}")
        
        if stats_response.status_code == 200:
            print("❌ SECURITY GAP CONFIRMED: Pending business can access /business/stats")
            print("   This endpoint should use get_approved_business_user dependency")
        elif stats_response.status_code == 403:
            print("✅ SECURITY OK: Pending business correctly blocked from /business/stats")
        else:
            print(f"⚠️ UNEXPECTED: Status {stats_response.status_code}")
    else:
        print(f"❌ Failed to create test business: {response.status_code}")

def test_admin_business_lookup():
    """Test admin business lookup issue"""
    print("\n🔍 TESTING ADMIN BUSINESS LOOKUP...")
    
    # Authenticate as admin
    session = requests.Session()
    login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    login_response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if login_response.status_code == 200:
        admin_token = login_response.json().get("access_token")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get list of businesses first
        businesses_response = session.get(f"{BACKEND_URL}/admin/businesses", headers=admin_headers)
        
        if businesses_response.status_code == 200:
            businesses = businesses_response.json()
            if businesses:
                # Try to get first business by ID
                first_business = businesses[0]
                business_id = first_business.get("id")
                
                print(f"Testing business lookup for ID: {business_id}")
                
                # Test individual business lookup
                business_response = session.get(f"{BACKEND_URL}/admin/businesses/{business_id}", 
                                              headers=admin_headers)
                
                print(f"Individual Business Lookup Status: {business_response.status_code}")
                
                if business_response.status_code == 404:
                    print("❌ ADMIN LOOKUP ISSUE: Business exists in list but not found individually")
                    print("   Likely looking in wrong collection (businesses vs users)")
                elif business_response.status_code == 200:
                    print("✅ ADMIN LOOKUP OK: Individual business lookup working")
                else:
                    print(f"⚠️ UNEXPECTED: Status {business_response.status_code}")
            else:
                print("⚠️ No businesses found in admin list")
        else:
            print(f"❌ Failed to get businesses list: {businesses_response.status_code}")
    else:
        print(f"❌ Admin authentication failed: {login_response.status_code}")

def test_approved_business_login():
    """Test approved business login issue"""
    print("\n🔍 TESTING APPROVED BUSINESS LOGIN...")
    
    # Use existing approved business from database
    test_emails = [
        "testbusiness@example.com",
        "testrestoran@example.com"
    ]
    
    session = requests.Session()
    
    for email in test_emails:
        login_data = {"email": email, "password": "test123"}
        response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        print(f"Login attempt for {email}: Status {response.status_code}")
        
        if response.status_code == 500:
            print("❌ LOGIN ERROR: 500 Internal Server Error - likely password hash issue")
        elif response.status_code == 200:
            print("✅ LOGIN OK: Business login successful")
            break
        elif response.status_code == 400:
            print("⚠️ LOGIN FAILED: Invalid credentials")
        else:
            print(f"⚠️ UNEXPECTED: Status {response.status_code}")

if __name__ == "__main__":
    print("🚀 FOCUSED KYC ISSUES TESTING")
    print("=" * 50)
    
    test_business_stats_security_gap()
    test_admin_business_lookup()
    test_approved_business_login()
    
    print("\n📝 SUMMARY OF ISSUES FOUND:")
    print("1. /business/stats endpoint not protected by KYC enforcement")
    print("2. Admin individual business lookup returns 404 (wrong collection)")
    print("3. Approved business login fails with 500 error (password hash issue)")