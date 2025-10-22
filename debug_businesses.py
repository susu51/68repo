#!/usr/bin/env python3
"""
Debug script to check businesses and their menu items
"""

import requests
import json

BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"

def check_businesses():
    """Check all businesses in Aksaray and their menu items"""
    
    # Get businesses in Aksaray
    response = requests.get(f"{BACKEND_URL}/businesses?city=Aksaray")
    
    if response.status_code == 200:
        businesses_data = response.json()
        businesses = businesses_data if isinstance(businesses_data, list) else businesses_data.get("businesses", [])
        
        print(f"Found {len(businesses)} businesses in Aksaray:")
        print("=" * 60)
        
        for i, business in enumerate(businesses):
            business_id = business.get("id")
            business_name = business.get("name", business.get("business_name", "Unknown"))
            
            print(f"\n{i+1}. {business_name}")
            print(f"   ID: {business_id}")
            print(f"   City: {business.get('city', 'N/A')}")
            print(f"   District: {business.get('district', 'N/A')}")
            
            # Check menu items for this business
            menu_response = requests.get(f"{BACKEND_URL}/business/public/{business_id}/menu")
            
            if menu_response.status_code == 200:
                menu_data = menu_response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                print(f"   Menu Items: {len(menu_items)}")
                
                if menu_items:
                    print("   Sample Items:")
                    for j, item in enumerate(menu_items[:3]):
                        print(f"     - {item.get('name', item.get('title', 'Unnamed'))}: {item.get('price', 0)} TL (ID: {item.get('id')})")
                else:
                    print("   No menu items available")
            else:
                print(f"   Menu check failed: HTTP {menu_response.status_code}")
        
        # Find businesses with menu items
        businesses_with_menu = []
        for business in businesses:
            business_id = business.get("id")
            menu_response = requests.get(f"{BACKEND_URL}/business/public/{business_id}/menu")
            
            if menu_response.status_code == 200:
                menu_data = menu_response.json()
                menu_items = menu_data if isinstance(menu_data, list) else menu_data.get("items", [])
                
                if menu_items:
                    businesses_with_menu.append({
                        "business": business,
                        "menu_count": len(menu_items),
                        "menu_items": menu_items
                    })
        
        print(f"\n" + "=" * 60)
        print(f"SUMMARY: {len(businesses_with_menu)}/{len(businesses)} businesses have menu items")
        
        if businesses_with_menu:
            print("\nBusinesses with menu items:")
            for bwm in businesses_with_menu:
                business = bwm["business"]
                print(f"- {business.get('name', business.get('business_name'))}: {bwm['menu_count']} items (ID: {business.get('id')})")
        
        return businesses_with_menu
    else:
        print(f"Failed to get businesses: HTTP {response.status_code}: {response.text}")
        return []

if __name__ == "__main__":
    businesses_with_menu = check_businesses()