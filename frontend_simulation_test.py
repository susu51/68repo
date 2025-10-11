#!/usr/bin/env python3
"""
Frontend Simulation Test - Simulate exact frontend behavior including response handling
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://quickcourier.preview.emergentagent.com/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

class FrontendSimulator:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.addresses = []  # Simulate frontend state
        
    def authenticate_customer(self):
        """Simulate customer authentication"""
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
    
    def load_existing_addresses(self):
        """Simulate loading existing addresses (like useEffect in frontend)"""
        try:
            print("\n🔄 Loading existing addresses...")
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                self.addresses = response.json()
                print(f"✅ Loaded {len(self.addresses)} existing addresses")
                return True
            else:
                print(f"❌ Failed to load addresses: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception loading addresses: {str(e)}")
            return False
    
    def simulate_frontend_address_creation(self):
        """Simulate exact frontend address creation behavior"""
        print("\n🎯 SIMULATING FRONTEND ADDRESS CREATION")
        print("=" * 50)
        
        # Simulate user input (newAddress state)
        new_address = {
            "label": "Frontend Simulation Test",
            "city": "İstanbul",
            "description": "Testing frontend simulation",
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        print(f"User input (newAddress state): {json.dumps(new_address, indent=2, ensure_ascii=False)}")
        
        # Simulate frontend validation
        if not new_address.get("label") or not new_address.get("city") or not new_address.get("description"):
            missing_fields = []
            if not new_address.get("label"):
                missing_fields.append("Adres Adı")
            if not new_address.get("city"):
                missing_fields.append("Şehir")
            if not new_address.get("description"):
                missing_fields.append("Adres Açıklaması")
            
            print(f"❌ Validation failed. Missing fields: {missing_fields}")
            return False
        
        print("✅ Frontend validation passed")
        
        # Simulate frontend address data preparation (exact code from AddressesPage.js)
        address_data = {
            **new_address,
            # Normalize city name on the frontend as well
            "city_original": new_address["city"],
            "city_normalized": new_address["city"].lower().replace('ı', 'i')
        }
        
        print(f"Address data to send: {json.dumps(address_data, indent=2, ensure_ascii=False)}")
        
        try:
            # Simulate API call
            print("\n📡 Making API call...")
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=address_data)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ API call successful")
                print(f"Response data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                
                # Simulate frontend state update (THIS IS THE POTENTIAL BUG!)
                # Frontend code: setAddresses([...addresses, response]);
                # But it should be: setAddresses([...addresses, response.data]);
                
                print("\n🔍 TESTING FRONTEND STATE UPDATE BEHAVIOR")
                print("-" * 50)
                
                # Test 1: What frontend currently does (WRONG)
                print("Test 1: Frontend current behavior - setAddresses([...addresses, response])")
                try:
                    # In JavaScript, this would be the full axios response object
                    # In Python, we simulate this by using the full response
                    simulated_wrong_update = self.addresses + [response]  # This is wrong!
                    print(f"❌ This would add the full response object to addresses array")
                    print(f"   Response object type: {type(response)}")
                    print(f"   This is likely causing frontend issues!")
                except Exception as e:
                    print(f"❌ Error with wrong approach: {str(e)}")
                
                # Test 2: What frontend should do (CORRECT)
                print("\nTest 2: Correct behavior - setAddresses([...addresses, response.data])")
                try:
                    simulated_correct_update = self.addresses + [response_data]  # This is correct!
                    print(f"✅ This correctly adds the address data to addresses array")
                    print(f"   New addresses count: {len(simulated_correct_update)}")
                    print(f"   Last address: {simulated_correct_update[-1].get('label', 'No label')}")
                    
                    # Update our simulated state correctly
                    self.addresses = simulated_correct_update
                    
                except Exception as e:
                    print(f"❌ Error with correct approach: {str(e)}")
                
                return True
                
            else:
                print(f"❌ API call failed")
                print(f"Response text: {response.text}")
                
                # Simulate frontend error handling
                print("\n🚨 Frontend would show: 'Adres eklenirken hata oluştu'")
                return False
                
        except Exception as e:
            print(f"❌ Exception during API call: {str(e)}")
            print("\n🚨 Frontend would show: 'Adres eklenirken hata oluştu'")
            return False
    
    def verify_address_was_saved(self):
        """Verify the address was actually saved in backend"""
        print("\n🔍 VERIFYING ADDRESS WAS SAVED IN BACKEND")
        print("=" * 50)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                current_addresses = response.json()
                print(f"✅ Backend has {len(current_addresses)} addresses")
                
                # Check if our test address exists
                test_address = None
                for addr in current_addresses:
                    if addr.get("label") == "Frontend Simulation Test":
                        test_address = addr
                        break
                
                if test_address:
                    print(f"✅ Test address found in backend: {test_address.get('label')}")
                    print(f"   ID: {test_address.get('id')}")
                    print(f"   City: {test_address.get('city')}")
                    return True
                else:
                    print("❌ Test address not found in backend")
                    return False
                    
            else:
                print(f"❌ Failed to retrieve addresses: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception verifying address: {str(e)}")
            return False
    
    def run_frontend_simulation(self):
        """Run complete frontend simulation"""
        print("🎭 FRONTEND BEHAVIOR SIMULATION")
        print("=" * 60)
        print("Simulating exact frontend behavior to identify the issue...")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_customer():
            return False
        
        # Step 2: Load existing addresses
        if not self.load_existing_addresses():
            return False
        
        # Step 3: Simulate address creation
        creation_success = self.simulate_frontend_address_creation()
        
        # Step 4: Verify backend saved the address
        backend_verification = self.verify_address_was_saved()
        
        # Analysis
        print("\n" + "=" * 60)
        print("📊 FRONTEND SIMULATION ANALYSIS")
        print("=" * 60)
        
        if creation_success and backend_verification:
            print("✅ CONCLUSION: Backend works perfectly")
            print("❌ IDENTIFIED ISSUE: Frontend response handling bug")
            print()
            print("🐛 BUG DETAILS:")
            print("   File: /app/frontend/src/pages/customer/AddressesPage.js")
            print("   Line: 112")
            print("   Current: setAddresses([...addresses, response]);")
            print("   Should be: setAddresses([...addresses, response.data]);")
            print()
            print("🔧 FIX REQUIRED:")
            print("   The frontend is adding the full axios response object")
            print("   to the addresses array instead of just the response data.")
            print("   This causes the UI to break when trying to render addresses.")
            print()
            print("   While the backend successfully saves the address,")
            print("   the frontend shows an error because the state update fails.")
            
        elif not creation_success and backend_verification:
            print("⚠️  CONCLUSION: API call failed but address was saved")
            print("   This indicates a race condition or response handling issue")
            
        elif creation_success and not backend_verification:
            print("⚠️  CONCLUSION: API call succeeded but address not in backend")
            print("   This indicates a backend saving issue")
            
        else:
            print("❌ CONCLUSION: Both frontend and backend have issues")
        
        return creation_success

def main():
    """Main execution"""
    simulator = FrontendSimulator()
    success = simulator.run_frontend_simulation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()