#!/usr/bin/env python3
"""
KYC Response Format Testing - Verify backend response includes 'success: true' field
Testing the specific user-reported issue: "İşletme kyc başarısız oluyor onaylanmiyor"
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://db-driven-kuryecini.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

def test_kyc_response_format():
    """Test that KYC approval responses include 'success' field for frontend compatibility"""
    print("🎯 TESTING KYC RESPONSE FORMAT FOR FRONTEND COMPATIBILITY")
    print("=" * 70)
    
    # Step 1: Admin login
    print("1. Admin Authentication...")
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return False
    
    admin_token = login_response.json().get("access_token")
    print(f"✅ Admin authenticated successfully (Token: {len(admin_token)} chars)")
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get pending businesses
    print("\n2. Retrieving pending businesses...")
    businesses_response = requests.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", headers=headers)
    
    if businesses_response.status_code != 200:
        print(f"❌ Failed to get pending businesses: {businesses_response.status_code}")
        return False
    
    businesses_data = businesses_response.json()
    businesses = businesses_data.get("businesses", [])
    print(f"✅ Found {len(businesses)} pending businesses")
    
    if not businesses:
        print("⚠️  No pending businesses found. Creating test business...")
        # Create a test business for testing
        test_business_data = {
            "email": f"test-kyc-{int(datetime.now().timestamp())}@example.com",
            "password": "test123",
            "business_name": "KYC Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address, Istanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant for KYC testing"
        }
        
        create_response = requests.post(f"{BACKEND_URL}/register/business", json=test_business_data)
        if create_response.status_code == 200:
            print("✅ Test business created successfully")
            # Re-fetch pending businesses
            businesses_response = requests.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", headers=headers)
            businesses = businesses_response.json().get("businesses", [])
        else:
            print(f"❌ Failed to create test business: {create_response.status_code}")
            return False
    
    # Step 3: Test KYC approval response format
    if businesses:
        test_business = businesses[0]
        business_id = test_business.get("id")
        business_name = test_business.get("business_name", "Unknown")
        
        print(f"\n3. Testing KYC approval for: {business_name} (ID: {business_id})")
        
        # Test approval
        approval_data = {"kyc_status": "approved"}
        approval_response = requests.patch(
            f"{BACKEND_URL}/admin/businesses/{business_id}/status",
            headers=headers,
            json=approval_data
        )
        
        print(f"   Response Status: {approval_response.status_code}")
        
        if approval_response.status_code == 200:
            response_data = approval_response.json()
            print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            
            # Check for 'success' field
            has_success_field = "success" in response_data
            success_value = response_data.get("success")
            
            print(f"\n🔍 RESPONSE FORMAT ANALYSIS:")
            print(f"   Has 'success' field: {has_success_field}")
            print(f"   Success value: {success_value}")
            print(f"   Success type: {type(success_value)}")
            
            if has_success_field and success_value is True:
                print("✅ PERFECT: Response includes 'success: true' field as expected by frontend")
                
                # Test rejection format too
                print(f"\n4. Testing KYC rejection response format...")
                rejection_data = {
                    "kyc_status": "rejected",
                    "rejection_reason": "Test rejection for response format verification"
                }
                
                rejection_response = requests.patch(
                    f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                    headers=headers,
                    json=rejection_data
                )
                
                if rejection_response.status_code == 200:
                    rejection_response_data = rejection_response.json()
                    print(f"   Rejection Response: {json.dumps(rejection_response_data, indent=2)}")
                    
                    has_success_field_rejection = "success" in rejection_response_data
                    success_value_rejection = rejection_response_data.get("success")
                    
                    if has_success_field_rejection and success_value_rejection is True:
                        print("✅ PERFECT: Rejection response also includes 'success: true' field")
                    else:
                        print("⚠️  Rejection response format may need adjustment")
                
                return True
            else:
                print("❌ ISSUE: Response missing 'success: true' field expected by frontend")
                print("💡 Frontend expects: {'success': true, ...}")
                print(f"💡 Backend returns: {response_data}")
                return False
        else:
            print(f"❌ KYC approval failed with status: {approval_response.status_code}")
            print(f"   Response: {approval_response.text}")
            return False
    
    return False

def main():
    """Main test execution"""
    print("🚀 KYC RESPONSE FORMAT TESTING")
    print("Testing user-reported issue: 'İşletme kyc başarısız oluyor onaylanmiyor'")
    print("Focus: Verify backend response format matches frontend expectations")
    print()
    
    success = test_kyc_response_format()
    
    print("\n" + "=" * 70)
    print("📊 FINAL ANALYSIS")
    print("=" * 70)
    
    if success:
        print("✅ KYC APPROVAL BACKEND IS WORKING CORRECTLY")
        print("✅ Response format includes 'success: true' field as expected")
        print()
        print("🎯 USER ISSUE DIAGNOSIS:")
        print("   Since backend KYC approval is working correctly, the issue")
        print("   'İşletme kyc başarısız oluyor onaylanmiyor' is likely in:")
        print("   • Frontend implementation")
        print("   • User interface workflow")
        print("   • Network connectivity")
        print("   • Browser-specific issues")
        print()
        print("💡 RECOMMENDATION:")
        print("   Backend is functioning correctly. Focus troubleshooting on frontend.")
    else:
        print("❌ KYC APPROVAL BACKEND HAS ISSUES")
        print("❌ Response format or functionality needs fixes")
        print()
        print("🔧 REQUIRED ACTIONS:")
        print("   • Fix backend response format to include 'success: true'")
        print("   • Ensure proper error handling")
        print("   • Test frontend integration after backend fixes")

if __name__ == "__main__":
    main()