#!/usr/bin/env python3
"""
Check the expected business from the review request
"""

import requests
import json

BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com/api"
BUSINESS_EMAIL = "testbusiness@example.com"
BUSINESS_PASSWORD = "test123"
EXPECTED_BUSINESS_ID = "e94a2e76-141a-4406-8ed6-d1c0ecc4d6ed"

def check_expected_business():
    """Check the expected business and its menu"""
    
    session = requests.Session()
    
    # Login as business
    login_data = {
        "email": BUSINESS_EMAIL,
        "password": BUSINESS_PASSWORD
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            user = data.get("user", {})
            business_id = user.get("id")
            
            print(f"✅ Business login successful:")
            print(f"   Email: {user.get('email')}")
            print(f"   ID: {business_id}")
            print(f"   Expected ID: {EXPECTED_BUSINESS_ID}")
            print(f"   ID Match: {business_id == EXPECTED_BUSINESS_ID}")
            print(f"   Role: {user.get('role')}")
            print(f"   Business Name: {user.get('business_name')}")
            
            # Check if this business has menu items
            menu_response = session.get(f"{BACKEND_URL}/business/menu")
            
            if menu_response.status_code == 200:
                menu_data = menu_response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                print(f"\n📋 Business Menu (Private):")
                print(f"   Total Items: {len(menu_items)}")
                
                if menu_items:
                    print("   Items:")
                    for i, item in enumerate(menu_items):
                        print(f"     {i+1}. {item.get('name', item.get('title', 'Unnamed'))}")
                        print(f"        ID: {item.get('id')}")
                        print(f"        Price: {item.get('price')} TL")
                        print(f"        Available: {item.get('is_available', True)}")
                        print(f"        Business ID: {item.get('business_id')}")
                else:
                    print("   No menu items found")
            else:
                print(f"\n❌ Failed to get business menu: HTTP {menu_response.status_code}: {menu_response.text}")
            
            # Check public menu
            public_menu_response = requests.get(f"{BACKEND_URL}/business/public/{business_id}/menu")
            
            if public_menu_response.status_code == 200:
                public_menu_data = public_menu_response.json()
                public_menu_items = public_menu_data if isinstance(public_menu_data, list) else public_menu_data.get("items", [])
                
                print(f"\n📋 Business Menu (Public):")
                print(f"   Total Items: {len(public_menu_items)}")
                
                if public_menu_items:
                    print("   Items:")
                    for i, item in enumerate(public_menu_items):
                        print(f"     {i+1}. {item.get('name', item.get('title', 'Unnamed'))}")
                        print(f"        ID: {item.get('id')}")
                        print(f"        Price: {item.get('price')} TL")
                        print(f"        Available: {item.get('is_available', True)}")
                        print(f"        Business ID: {item.get('business_id')}")
                else:
                    print("   No public menu items found")
            else:
                print(f"\n❌ Failed to get public menu: HTTP {public_menu_response.status_code}: {public_menu_response.text}")
            
            return business_id, menu_items
        else:
            print(f"❌ Login failed: {data}")
            return None, []
    else:
        print(f"❌ Login request failed: HTTP {response.status_code}: {response.text}")
        return None, []

if __name__ == "__main__":
    business_id, menu_items = check_expected_business()