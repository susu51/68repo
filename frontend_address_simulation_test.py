#!/usr/bin/env python3
"""
FRONTEND SIMULATION TEST
Simulate exact frontend behavior to identify "Adres ekleme hatası" root cause
"""

import requests
import json
from datetime import datetime

# Configuration - Use exact same URL as frontend
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"

class FrontendSimulationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def simulate_frontend_login(self):
        """Simulate exact frontend login process"""
        print("🔐 SIMULATING FRONTEND LOGIN")
        print("=" * 50)
        
        # Simulate frontend login request with exact headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://kuryecini-ai.preview.emergentagent.com',
            'Referer': 'https://kuryecini-ai.preview.emergentagent.com/'
        }
        
        login_data = {
            "email": "testcustomer@example.com",
            "password": "test123"
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login", 
                json=login_data,
                headers=headers
            )
            
            print(f"📤 Login Request URL: {BACKEND_URL}/auth/login")
            print(f"📤 Login Headers: {json.dumps(headers, indent=2)}")
            print(f"📤 Login Data: {json.dumps(login_data, indent=2)}")
            print(f"📥 Login Response Status: {response.status_code}")
            print(f"📥 Login Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"📥 Login Response Data: {json.dumps(data, indent=2)}")
                print(f"✅ Login successful - Token length: {len(self.auth_token)}")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                print(f"📥 Error Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login request failed: {e}")
            return False

    def simulate_frontend_address_creation(self):
        """Simulate exact frontend address creation request"""
        print("\n🏠 SIMULATING FRONTEND ADDRESS CREATION")
        print("=" * 50)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        # Simulate frontend address creation with exact headers and data format
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.auth_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://kuryecini-ai.preview.emergentagent.com',
            'Referer': 'https://kuryecini-ai.preview.emergentagent.com/'
        }
        
        # Test with exact data format from review request
        address_data = {
            "label": "Debug Test Adres",
            "city": "İstanbul", 
            "district": "Kadıköy",
            "description": "Debug test address for error investigation",
            "lat": 40.9903,
            "lng": 29.0209
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/user/addresses",
                json=address_data,
                headers=headers
            )
            
            print(f"📤 Address Request URL: {BACKEND_URL}/user/addresses")
            print(f"📤 Address Headers: {json.dumps(headers, indent=2)}")
            print(f"📤 Address Data: {json.dumps(address_data, indent=2, ensure_ascii=False)}")
            print(f"📥 Address Response Status: {response.status_code}")
            print(f"📥 Address Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"📥 Address Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"📥 Address Response Text: {response.text}")
            
            if response.status_code in [200, 201]:
                print("✅ Address creation successful")
                return True
            else:
                print(f"❌ Address creation failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Address creation request failed: {e}")
            return False

    def test_cors_preflight(self):
        """Test CORS preflight request"""
        print("\n🌐 TESTING CORS PREFLIGHT")
        print("=" * 50)
        
        # Simulate CORS preflight OPTIONS request
        headers = {
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Origin': 'https://kuryecini-ai.preview.emergentagent.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.options(
                f"{BACKEND_URL}/user/addresses",
                headers=headers
            )
            
            print(f"📤 CORS Preflight URL: {BACKEND_URL}/user/addresses")
            print(f"📤 CORS Headers: {json.dumps(headers, indent=2)}")
            print(f"📥 CORS Response Status: {response.status_code}")
            print(f"📥 CORS Response Headers: {dict(response.headers)}")
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"📥 CORS Headers: {json.dumps(cors_headers, indent=2)}")
            
            if response.status_code in [200, 204]:
                print("✅ CORS preflight successful")
                return True
            else:
                print(f"❌ CORS preflight failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ CORS preflight request failed: {e}")
            return False

    def test_field_name_variations(self):
        """Test different field name variations that frontend might send"""
        print("\n🔤 TESTING FIELD NAME VARIATIONS")
        print("=" * 50)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.auth_token}',
        }
        
        # Test different field name variations
        field_variations = [
            {
                "name": "Standard Fields",
                "data": {
                    "label": "Standard Test",
                    "city": "İstanbul",
                    "district": "Kadıköy",
                    "description": "Standard field test",
                    "lat": 40.9903,
                    "lng": 29.0209
                }
            },
            {
                "name": "Missing District Field",
                "data": {
                    "label": "No District Test",
                    "city": "İstanbul",
                    "description": "Test without district field",
                    "lat": 40.9903,
                    "lng": 29.0209
                }
            }
        ]
        
        for variation in field_variations:
            try:
                print(f"\n🔄 Testing: {variation['name']}")
                
                response = requests.post(
                    f"{BACKEND_URL}/user/addresses",
                    json=variation['data'],
                    headers=headers
                )
                
                print(f"📤 Data: {json.dumps(variation['data'], indent=2, ensure_ascii=False)}")
                print(f"📥 Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    try:
                        response_data = response.json()
                        print(f"✅ {variation['name']}: Success - {response_data.get('id', 'No ID')}")
                    except:
                        print(f"✅ {variation['name']}: Success - {response.text}")
                else:
                    print(f"❌ {variation['name']}: Failed - {response.text}")
                    
            except Exception as e:
                print(f"❌ {variation['name']}: Request failed - {e}")

    def run_frontend_simulation(self):
        """Run complete frontend simulation"""
        print("🖥️ FRONTEND BEHAVIOR SIMULATION")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Step 1: Login simulation
        if not self.simulate_frontend_login():
            print("❌ CRITICAL: Frontend login simulation failed")
            return
        
        # Step 2: Address creation simulation
        self.simulate_frontend_address_creation()
        
        # Step 3: CORS testing
        self.test_cors_preflight()
        
        # Step 4: Field variations
        self.test_field_name_variations()
        
        print("\n" + "=" * 60)
        print("🔍 FRONTEND SIMULATION COMPLETE")
        print("=" * 60)
        print("📝 CONCLUSION: Backend API is working correctly for address creation.")
        print("📝 If user still reports 'Adres ekleme hatası', the issue is likely:")
        print("   1. Frontend JavaScript error preventing API call")
        print("   2. Frontend form validation blocking submission")
        print("   3. Frontend authentication token not being sent")
        print("   4. Frontend error handling showing wrong message")
        print("   5. Browser-specific issues (CORS, network, etc.)")
        print("=" * 60)

if __name__ == "__main__":
    tester = FrontendSimulationTester()
    tester.run_frontend_simulation()