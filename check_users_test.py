#!/usr/bin/env python3
"""
Check what users exist in the database
"""

import requests
import json

# Configuration
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com/api"

def check_users():
    """Check what users exist by trying different login combinations"""
    
    test_credentials = [
        ("testbusiness@example.com", "test123"),
        ("testcustomer@example.com", "test123"),
        ("test@kuryecini.com", "test123"),
        ("admin@kuryecini.com", "KuryeciniAdmin2024!")
    ]
    
    print("🔍 Checking user credentials...")
    print("=" * 50)
    
    for email, password in test_credentials:
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    user = data.get("user", {})
                    print(f"✅ {email}: SUCCESS")
                    print(f"   ID: {user.get('id')}")
                    print(f"   Role: {user.get('role')}")
                    print(f"   Name: {user.get('first_name')} {user.get('last_name')}")
                else:
                    print(f"❌ {email}: Login failed - {data}")
            else:
                print(f"❌ {email}: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ {email}: Error - {str(e)}")
        
        print()

if __name__ == "__main__":
    check_users()