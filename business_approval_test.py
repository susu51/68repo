#!/usr/bin/env python3
"""
Business Approval Test
Check and approve business user if needed
"""

import requests
import json

# Backend URL from frontend .env
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"
BUSINESS_EMAIL = "testbusiness@example.com"

def login_admin():
    """Login as admin"""
    session = requests.Session()
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
            print(f"✅ Admin login successful")
            return session
    
    print(f"❌ Admin login failed: {response.status_code} - {response.text}")
    return None

def check_business_status(session):
    """Check business approval status"""
    try:
        response = session.get(f"{BACKEND_URL}/admin/businesses")
        
        if response.status_code == 200:
            data = response.json()
            businesses = data if isinstance(data, list) else data.get("businesses", [])
            
            # Find testbusiness@example.com
            test_business = None
            for business in businesses:
                if business.get("email") == BUSINESS_EMAIL:
                    test_business = business
                    break
            
            if test_business:
                print(f"✅ Found business: {BUSINESS_EMAIL}")
                print(f"   ID: {test_business.get('id')}")
                print(f"   KYC Status: {test_business.get('kyc_status')}")
                print(f"   Business Name: {test_business.get('business_name')}")
                return test_business
            else:
                print(f"❌ Business {BUSINESS_EMAIL} not found")
                return None
        else:
            print(f"❌ Failed to get businesses: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception checking business status: {str(e)}")
        return None

def approve_business(session, business_id):
    """Approve business KYC status"""
    try:
        update_data = {
            "kyc_status": "approved"
        }
        
        response = session.patch(f"{BACKEND_URL}/admin/businesses/{business_id}/status", json=update_data)
        
        if response.status_code == 200:
            print(f"✅ Business approved successfully")
            return True
        else:
            print(f"❌ Failed to approve business: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception approving business: {str(e)}")
        return False

def main():
    print("🔍 BUSINESS APPROVAL CHECK")
    print("=" * 50)
    
    # Login as admin
    admin_session = login_admin()
    if not admin_session:
        return
    
    # Check business status
    business = check_business_status(admin_session)
    if not business:
        return
    
    # Approve if needed
    if business.get("kyc_status") != "approved":
        print(f"⚠️  Business is not approved (status: {business.get('kyc_status')})")
        print("🔧 Approving business...")
        
        if approve_business(admin_session, business.get("id")):
            print("✅ Business approval complete!")
        else:
            print("❌ Business approval failed!")
    else:
        print("✅ Business is already approved!")

if __name__ == "__main__":
    main()