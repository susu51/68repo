#!/usr/bin/env python3
"""
COMPREHENSIVE BUSINESS VISIBILITY INVESTIGATION
Deep dive into the business visibility pipeline to identify the exact issue
"""

import requests
import json

BACKEND_URL = "https://address-manager-5.preview.emergentagent.com/api"

def get_token(role):
    """Get authentication token for role"""
    creds = {
        "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
        "customer": {"email": "testcustomer@example.com", "password": "test123"}
    }
    response = requests.post(f"{BACKEND_URL}/auth/login", json=creds[role])
    return response.json()["access_token"]

def test_endpoint(endpoint, headers=None, description=""):
    """Test an endpoint and return results"""
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "status": response.status_code,
                "count": len(data) if isinstance(data, list) else "N/A",
                "data": data
            }
        else:
            return {
                "success": False,
                "status": response.status_code,
                "error": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("🔍 COMPREHENSIVE BUSINESS VISIBILITY INVESTIGATION")
    print("=" * 70)
    
    # Get tokens
    admin_token = get_token("admin")
    customer_token = get_token("customer")
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    
    # Test all possible endpoints
    endpoints_to_test = [
        ("/admin/businesses", admin_headers, "Admin - All Businesses"),
        ("/businesses", None, "Public - Businesses (No Auth)"),
        ("/businesses", customer_headers, "Customer - Businesses (With Auth)"),
        ("/restaurants", None, "Public - Restaurants (No Auth)"),
        ("/restaurants", customer_headers, "Customer - Restaurants (With Auth)"),
        ("/restaurants/discover", None, "Public - Restaurant Discovery"),
        ("/restaurants/discover", customer_headers, "Customer - Restaurant Discovery"),
    ]
    
    results = {}
    
    for endpoint, headers, description in endpoints_to_test:
        print(f"\n📍 Testing: {description}")
        print(f"   Endpoint: {endpoint}")
        
        result = test_endpoint(endpoint, headers)
        results[description] = result
        
        if result["success"]:
            print(f"   ✅ Status: {result['status']}, Count: {result['count']}")
            
            # Look for target businesses
            data = result["data"]
            if isinstance(data, list):
                target_businesses = []
                for item in data:
                    name = item.get("business_name") or item.get("name", "")
                    if "Test Restoranı" in name or "Pizza Palace İstanbul" in name:
                        target_businesses.append({
                            "name": name,
                            "kyc_status": item.get("kyc_status"),
                            "id": item.get("id")
                        })
                
                if target_businesses:
                    print(f"   🎯 Target businesses found: {len(target_businesses)}")
                    for tb in target_businesses:
                        print(f"      - {tb['name']} (KYC: {tb['kyc_status']}, ID: {tb['id']})")
                else:
                    print(f"   ❌ No target businesses found")
                    
                # Show first few businesses for context
                if len(data) > 0:
                    print(f"   📋 First 3 businesses:")
                    for i, item in enumerate(data[:3]):
                        name = item.get("business_name") or item.get("name", "Unknown")
                        kyc = item.get("kyc_status", "No KYC")
                        print(f"      {i+1}. {name} (KYC: {kyc})")
        else:
            print(f"   ❌ Failed: {result.get('status', 'Unknown')} - {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS SUMMARY")
    print("=" * 70)
    
    # Check if target businesses exist in admin view
    admin_result = results.get("Admin - All Businesses")
    if admin_result and admin_result["success"]:
        admin_data = admin_result["data"]
        admin_targets = [
            item for item in admin_data 
            if "Test Restoranı" in item.get("business_name", "") or "Pizza Palace İstanbul" in item.get("business_name", "")
        ]
        
        print(f"✅ Admin view has {len(admin_targets)} target businesses:")
        for target in admin_targets:
            print(f"   - {target.get('business_name')} (KYC: {target.get('kyc_status')}, ID: {target.get('id')})")
    
    # Check customer endpoints
    customer_endpoints = [
        "Public - Businesses (No Auth)",
        "Customer - Businesses (With Auth)", 
        "Public - Restaurants (No Auth)",
        "Customer - Restaurants (With Auth)"
    ]
    
    print(f"\n📊 Customer Endpoint Results:")
    for endpoint_name in customer_endpoints:
        result = results.get(endpoint_name)
        if result and result["success"]:
            data = result["data"]
            target_count = len([
                item for item in data 
                if "Test Restoranı" in (item.get("business_name") or item.get("name", "")) or 
                   "Pizza Palace İstanbul" in (item.get("business_name") or item.get("name", ""))
            ])
            print(f"   {endpoint_name}: {result['count']} total, {target_count} targets")
        else:
            print(f"   {endpoint_name}: FAILED")
    
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    # Check if admin has targets but customer doesn't
    admin_has_targets = admin_result and admin_result["success"] and len(admin_targets) > 0
    
    customer_has_targets = False
    for endpoint_name in customer_endpoints:
        result = results.get(endpoint_name)
        if result and result["success"]:
            data = result["data"]
            if any("Test Restoranı" in (item.get("business_name") or item.get("name", "")) or 
                   "Pizza Palace İstanbul" in (item.get("business_name") or item.get("name", ""))
                   for item in data):
                customer_has_targets = True
                break
    
    if admin_has_targets and not customer_has_targets:
        print("❌ ISSUE CONFIRMED: Target businesses exist in admin view but NOT in customer endpoints")
        print("   This indicates a filtering or data consistency issue in customer-facing endpoints")
    elif admin_has_targets and customer_has_targets:
        print("✅ ISSUE RESOLVED: Target businesses are visible in both admin and customer views")
    elif not admin_has_targets:
        print("❌ CRITICAL: Target businesses don't exist in admin view - they need to be created first")
    
    print("\n💡 RECOMMENDATIONS:")
    if not customer_has_targets:
        print("1. Verify the customer endpoints are querying the correct database collection")
        print("2. Check if there's a data synchronization issue between admin and customer views")
        print("3. Ensure the KYC approval process is updating the correct records")
        print("4. Test the exact API endpoints the frontend is using")

if __name__ == "__main__":
    main()