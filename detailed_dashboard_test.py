#!/usr/bin/env python3
"""
Detailed Business Dashboard Summary Response Analysis
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "https://courier-connect-14.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

BUSINESS_USER = {
    "email": "testbusiness@example.com",
    "password": "test123"
}

async def detailed_test():
    """Run detailed analysis of dashboard response"""
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Login
        login_data = {
            "email": BUSINESS_USER["email"],
            "password": BUSINESS_USER["password"]
        }
        
        async with session.post(f"{API_BASE}/auth/login", json=login_data) as response:
            if response.status != 200:
                print("❌ Login failed")
                return
            
            cookies = response.cookies
            print("✅ Login successful")
        
        # Test dashboard endpoint
        async with session.get(f"{API_BASE}/business/dashboard/summary", cookies=cookies) as response:
            if response.status == 200:
                data = await response.json()
                print("\n📊 DASHBOARD SUMMARY RESPONSE:")
                print("=" * 50)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                print("\n🔍 FIELD ANALYSIS:")
                print("=" * 50)
                
                # Analyze each field
                fields_analysis = {
                    "business_id": {"type": str, "description": "Business identifier"},
                    "date": {"type": str, "description": "Date for the summary"},
                    "today_orders_count": {"type": int, "description": "Number of orders today"},
                    "today_revenue": {"type": (int, float), "description": "Revenue for today"},
                    "pending_orders_count": {"type": int, "description": "Number of pending orders"},
                    "menu_items_count": {"type": int, "description": "Number of menu items"},
                    "total_customers": {"type": int, "description": "Total unique customers"},
                    "rating_avg": {"type": (int, float), "description": "Average rating"},
                    "rating_count": {"type": int, "description": "Number of ratings"},
                    "activities": {"type": list, "description": "Recent activities"}
                }
                
                for field, info in fields_analysis.items():
                    if field in data:
                        value = data[field]
                        type_match = isinstance(value, info["type"])
                        print(f"✅ {field}: {value} ({type(value).__name__}) - {info['description']}")
                        if not type_match:
                            print(f"   ⚠️  Type mismatch: expected {info['type']}, got {type(value)}")
                    else:
                        print(f"❌ {field}: MISSING - {info['description']}")
                
                # Analyze activities structure
                if "activities" in data and data["activities"]:
                    print(f"\n🎯 ACTIVITIES ANALYSIS ({len(data['activities'])} items):")
                    print("=" * 50)
                    for i, activity in enumerate(data["activities"][:3]):  # Show first 3
                        print(f"Activity {i+1}:")
                        print(f"  Type: {activity.get('type', 'N/A')}")
                        print(f"  Title: {activity.get('title', 'N/A')}")
                        print(f"  Meta: {activity.get('meta', {})}")
                        print(f"  Timestamp: {activity.get('ts', 'N/A')}")
                        print()
                
                # Test with date parameter
                print("\n📅 TESTING DATE PARAMETER:")
                print("=" * 50)
                test_date = "2025-01-15"
                async with session.get(f"{API_BASE}/business/dashboard/summary?date={test_date}", cookies=cookies) as date_response:
                    if date_response.status == 200:
                        date_data = await date_response.json()
                        print(f"✅ Date parameter test successful")
                        print(f"   Requested date: {test_date}")
                        print(f"   Response date: {date_data.get('date', 'N/A')}")
                        print(f"   Orders for date: {date_data.get('today_orders_count', 0)}")
                        print(f"   Revenue for date: {date_data.get('today_revenue', 0)}")
                    else:
                        print(f"❌ Date parameter test failed: {date_response.status}")
                
            else:
                print(f"❌ Dashboard request failed: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text}")

if __name__ == "__main__":
    asyncio.run(detailed_test())