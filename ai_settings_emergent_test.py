#!/usr/bin/env python3
"""
AI Settings API - Test OpenAI Connection with Emergent Key

This test resets the AI settings to use the Emergent LLM key and tests the connection.
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-ai-tools.preview.emergentagent.com"

# Admin credentials
ADMIN_CREDENTIALS = {
    "email": "admin@kuryecini.com",
    "password": "admin123"
}

def test_emergent_key_connection():
    """Test OpenAI connection with Emergent LLM Key"""
    
    # Create admin session
    admin_session = requests.Session()
    
    # Login as admin
    print("🔐 Authenticating as admin...")
    response = admin_session.post(
        f"{BACKEND_URL}/api/auth/login",
        json=ADMIN_CREDENTIALS,
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        return False
    
    print("✅ Admin authenticated successfully")
    
    # Reset to use Emergent key
    print("\n🔄 Resetting to use Emergent LLM Key...")
    reset_data = {
        "use_emergent_key": True,
        "openai_api_key": ""  # Clear custom key
    }
    
    response = admin_session.put(
        f"{BACKEND_URL}/api/admin/ai/settings",
        json=reset_data,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Settings reset: use_emergent_key={data.get('use_emergent_key')}, configured={data.get('openai_api_key_configured')}")
    else:
        print(f"❌ Failed to reset settings: {response.status_code}")
        return False
    
    # Test OpenAI connection with Emergent key
    print("\n🧪 Testing OpenAI connection with Emergent LLM Key...")
    response = admin_session.post(
        f"{BACKEND_URL}/api/admin/ai/settings/test",
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get("success"):
            print("✅ OpenAI connection test SUCCESSFUL!")
            print(f"   Key source: {data.get('key_source')}")
            print(f"   Model: {data.get('model')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Test response length: {len(data.get('test_response', ''))} characters")
            
            # Show first 100 chars of response
            test_response = data.get('test_response', '')
            if test_response:
                preview = test_response[:100] + "..." if len(test_response) > 100 else test_response
                print(f"   Response preview: {preview}")
            
            return True
        else:
            print(f"❌ OpenAI connection test failed: {data.get('message')}")
            return False
    else:
        print(f"❌ Connection test request failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AI Settings API with Emergent LLM Key")
    print("=" * 60)
    
    success = test_emergent_key_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 EMERGENT LLM KEY CONNECTION TEST PASSED!")
        print("   The AI Settings API is working correctly with the configured Emergent key.")
    else:
        print("🚨 EMERGENT LLM KEY CONNECTION TEST FAILED!")
        print("   There may be an issue with the Emergent key configuration or API integration.")