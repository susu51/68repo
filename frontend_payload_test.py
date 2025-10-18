#!/usr/bin/env python3
"""
Frontend Payload Test - Test exact payload that frontend sends
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://order-flow-debug.preview.emergentagent.com/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

class FrontendPayloadTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate_customer(self):
        """Authenticate customer"""
        try:
            login_data = {
                "email": TEST_CUSTOMER_EMAIL,
                "password": TEST_CUSTOMER_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                print("✅ Customer authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    def test_exact_frontend_payload(self):
        """Test the exact payload that frontend sends"""
        print("\n🔍 TESTING EXACT FRONTEND PAYLOAD")
        print("=" * 50)
        
        # This is exactly what the frontend sends based on AddressesPage.js
        frontend_payload = {
            "label": "Test Address",
            "city": "İstanbul",
            "description": "Test address description", 
            "lat": 41.0082,
            "lng": 28.9784,
            # Frontend adds these additional fields
            "city_original": "İstanbul",
            "city_normalized": "istanbul"  # frontend does: city.toLowerCase().replace('ı', 'i')
        }
        
        print(f"Frontend payload: {json.dumps(frontend_payload, indent=2, ensure_ascii=False)}")
        print()
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=frontend_payload)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS - Address created with frontend payload")
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print("❌ FAILED - Address creation failed with frontend payload")
                print(f"Response Text: {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    print(f"Error JSON: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    pass
                
                return False
                
        except Exception as e:
            print(f"❌ Exception during request: {str(e)}")
            return False
    
    def test_minimal_payload(self):
        """Test minimal payload without extra fields"""
        print("\n🔍 TESTING MINIMAL PAYLOAD (without city_original/city_normalized)")
        print("=" * 70)
        
        minimal_payload = {
            "label": "Minimal Test Address",
            "city": "İstanbul",
            "description": "Minimal test description",
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        print(f"Minimal payload: {json.dumps(minimal_payload, indent=2, ensure_ascii=False)}")
        print()
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=minimal_payload)
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS - Address created with minimal payload")
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print("❌ FAILED - Address creation failed with minimal payload")
                print(f"Response Text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during request: {str(e)}")
            return False
    
    def test_network_and_headers(self):
        """Test network connectivity and headers"""
        print("\n🔍 TESTING NETWORK CONNECTIVITY AND HEADERS")
        print("=" * 50)
        
        # Test basic connectivity
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            print(f"Health check status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Backend is reachable")
            else:
                print("❌ Backend health check failed")
                
        except Exception as e:
            print(f"❌ Network connectivity issue: {str(e)}")
            return False
        
        # Test authentication endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/me")
            print(f"Auth validation status: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Authentication valid - User: {user_data.get('email')}")
            else:
                print("❌ Authentication validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Auth validation issue: {str(e)}")
            return False
        
        return True
    
    def run_frontend_payload_test(self):
        """Run comprehensive frontend payload testing"""
        print("🔍 FRONTEND PAYLOAD COMPATIBILITY TEST")
        print("=" * 60)
        print("Testing exact payloads that frontend sends to identify mismatch...")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_customer():
            print("❌ CRITICAL: Authentication failed")
            return False
        
        # Step 2: Test network connectivity
        if not self.test_network_and_headers():
            print("❌ CRITICAL: Network/Headers issue")
            return False
        
        # Step 3: Test exact frontend payload
        frontend_success = self.test_exact_frontend_payload()
        
        # Step 4: Test minimal payload for comparison
        minimal_success = self.test_minimal_payload()
        
        # Analysis
        print("\n" + "=" * 60)
        print("📊 FRONTEND PAYLOAD TEST ANALYSIS")
        print("=" * 60)
        
        if frontend_success and minimal_success:
            print("✅ CONCLUSION: Both frontend and minimal payloads work")
            print("   - Backend correctly handles frontend's extra fields")
            print("   - Issue is likely in frontend error handling or network")
            print("   - Check browser console for actual error details")
        elif not frontend_success and minimal_success:
            print("❌ CONCLUSION: Frontend payload has issues")
            print("   - Backend rejects frontend's extra fields")
            print("   - city_original/city_normalized fields causing problems")
            print("   - Frontend should send minimal payload")
        elif frontend_success and not minimal_success:
            print("⚠️  CONCLUSION: Minimal payload has issues (unexpected)")
            print("   - Backend requires extra fields from frontend")
            print("   - This is unusual - investigate backend validation")
        else:
            print("❌ CONCLUSION: Both payloads fail")
            print("   - Backend address creation endpoint has serious issues")
            print("   - Check backend logs and database connectivity")
        
        print()
        return frontend_success or minimal_success

def main():
    """Main execution"""
    tester = FrontendPayloadTester()
    success = tester.run_frontend_payload_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()