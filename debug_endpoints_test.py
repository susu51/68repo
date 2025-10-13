#!/usr/bin/env python3
"""
Debug E2E Order Workflow Endpoints
Testing individual endpoints to identify issues
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://quickship-49.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class EndpointDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        
    def authenticate_user(self, role):
        """Authenticate user and get JWT token"""
        try:
            credentials = TEST_CREDENTIALS[role]
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=credentials,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                self.tokens[role] = token
                print(f"✅ {role.title()} authenticated: {len(token)} chars")
                return True
            else:
                print(f"❌ {role.title()} auth failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ {role.title()} auth error: {e}")
            return False
    
    def get_auth_headers(self, role):
        """Get authorization headers for role"""
        token = self.tokens.get(role)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}
    
    def test_endpoint(self, method, endpoint, role=None, params=None, json_data=None):
        """Test a specific endpoint"""
        print(f"\n🔍 Testing {method.upper()} {endpoint}")
        
        try:
            headers = self.get_auth_headers(role) if role else {}
            
            if method.upper() == "GET":
                response = self.session.get(
                    f"{BACKEND_URL}{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=10
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    f"{BACKEND_URL}{endpoint}",
                    headers=headers,
                    json=json_data,
                    timeout=10
                )
            elif method.upper() == "PATCH":
                response = self.session.patch(
                    f"{BACKEND_URL}{endpoint}",
                    headers=headers,
                    json=json_data,
                    timeout=10
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   Response: List with {len(data)} items")
                        if data:
                            print(f"   Sample item keys: {list(data[0].keys())}")
                    elif isinstance(data, dict):
                        print(f"   Response keys: {list(data.keys())}")
                        if "businesses" in data:
                            print(f"   Businesses count: {len(data['businesses'])}")
                        if "orders" in data:
                            print(f"   Orders count: {len(data['orders'])}")
                    else:
                        print(f"   Response: {data}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    def run_debug_tests(self):
        """Run debug tests for all endpoints"""
        print("🚀 Starting Endpoint Debug Tests")
        print("=" * 50)
        
        # Authenticate all users
        print("\n📋 AUTHENTICATION")
        self.authenticate_user("customer")
        self.authenticate_user("business") 
        self.authenticate_user("courier")
        
        # Test business discovery endpoints
        print("\n📋 BUSINESS DISCOVERY ENDPOINTS")
        
        # Test nearby businesses
        self.test_endpoint("GET", "/nearby/businesses", "customer", {"lat": 41.0082, "lng": 28.9784})
        
        # Test general businesses
        self.test_endpoint("GET", "/businesses", "customer")
        
        # Test without auth
        self.test_endpoint("GET", "/businesses")
        
        # Test alternative endpoints
        print("\n📋 ALTERNATIVE BUSINESS ENDPOINTS")
        self.test_endpoint("GET", "/menus/public")
        self.test_endpoint("GET", "/restaurants/near", params={"lat": 41.0082, "lng": 28.9784})
        
        # Test business-specific endpoints
        print("\n📋 BUSINESS MANAGEMENT ENDPOINTS")
        self.test_endpoint("GET", "/business/orders/incoming", "business")
        self.test_endpoint("GET", "/business/stats", "business")
        
        # Test courier endpoints
        print("\n📋 COURIER ENDPOINTS")
        self.test_endpoint("GET", "/courier/orders/available", "courier")
        
        # Test order creation (if we can get businesses)
        print("\n📋 ORDER CREATION TEST")
        # First try to get a business ID
        try:
            response = self.session.get(f"{BACKEND_URL}/menus/public", timeout=10)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("restaurants", [])
                if restaurants:
                    business_id = restaurants[0]["id"]
                    print(f"   Found business ID: {business_id}")
                    
                    # Try to get products for this business
                    self.test_endpoint("GET", f"/businesses/{business_id}/products")
                    
                    # Try to create an order
                    order_data = {
                        "business_id": business_id,
                        "items": [
                            {
                                "product_id": "test-product-id",
                                "product_name": "Test Product",
                                "product_price": 25.0,
                                "quantity": 1,
                                "subtotal": 25.0
                            }
                        ],
                        "total_amount": 25.0,
                        "delivery_address": "Test Address, Istanbul",
                        "delivery_lat": 41.0082,
                        "delivery_lng": 28.9784,
                        "notes": "Test order"
                    }
                    self.test_endpoint("POST", "/orders", "customer", json_data=order_data)
                else:
                    print("   No restaurants found in /menus/public")
            else:
                print(f"   Failed to get restaurants: {response.status_code}")
        except Exception as e:
            print(f"   Order creation test failed: {e}")

def main():
    debugger = EndpointDebugger()
    debugger.run_debug_tests()

if __name__ == "__main__":
    main()