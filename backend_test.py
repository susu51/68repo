#!/usr/bin/env python3
"""
🚀 PHASE 1 COURIER BACKEND QUICK TEST
Testing 5 newly added courier endpoints with authentication
"""

import requests
import json
import sys
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://order-system-44.preview.emergentagent.com/api"
COURIER_EMAIL = "testkurye@example.com"
COURIER_PASSWORD = "test123"

class CourierBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.courier_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def test_courier_authentication(self):
        """Test courier login and JWT token retrieval"""
        print("🔐 Testing Courier Authentication...")
        
        try:
            # Test courier login
            login_data = {
                "email": COURIER_EMAIL,
                "password": COURIER_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.jwt_token = data["access_token"]
                    user_data = data.get("user", {})
                    self.courier_id = user_data.get("id")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.jwt_token}"
                    })
                    
                    self.log_test(
                        "Courier Authentication", 
                        True, 
                        f"JWT token obtained (length: {len(self.jwt_token)}), Courier ID: {self.courier_id}"
                    )
                    return True
                else:
                    self.log_test("Courier Authentication", False, "No access_token in response", data)
                    return False
            else:
                self.log_test("Courier Authentication", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Courier Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_earnings_pdf_report(self):
        """Test GET /api/courier/earnings/report/pdf?range=daily"""
        print("📊 Testing Earnings PDF Report...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/courier/earnings/report/pdf?range=daily",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'application/pdf' in content_type and content_length > 0:
                    self.log_test(
                        "Earnings PDF Report", 
                        True, 
                        f"PDF generated successfully (size: {content_length} bytes)"
                    )
                    return True
                else:
                    self.log_test(
                        "Earnings PDF Report", 
                        False, 
                        f"Invalid content type: {content_type}, size: {content_length}"
                    )
                    return False
            else:
                self.log_test(
                    "Earnings PDF Report", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Earnings PDF Report", False, f"Exception: {str(e)}")
            return False
    
    def test_profile_update(self):
        """Test PUT /api/courier/profile"""
        print("👤 Testing Profile Update...")
        
        try:
            # Test profile update
            profile_data = {
                "name": "Test",
                "surname": "Courier Updated",
                "phone": "+905551234567",
                "vehicleType": "motor",
                "plate": "34ABC123"
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/courier/profile",
                json=profile_data,
                headers={
                    "Authorization": f"Bearer {self.jwt_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "profile" in data:
                    updated_profile = data["profile"]
                    self.log_test(
                        "Profile Update", 
                        True, 
                        f"Profile updated: {updated_profile.get('name')} {updated_profile.get('surname')}"
                    )
                    return True
                else:
                    self.log_test("Profile Update", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Profile Update", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Profile Update", False, f"Exception: {str(e)}")
            return False
    
    def test_get_availability(self):
        """Test GET /api/courier/availability"""
        print("📅 Testing Get Availability...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/courier/availability",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data and "availability" in data:
                    availability = data["availability"]
                    self.log_test(
                        "Get Availability", 
                        True, 
                        f"Availability retrieved: {len(availability)} slots"
                    )
                    return True
                else:
                    self.log_test("Get Availability", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Get Availability", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Get Availability", False, f"Exception: {str(e)}")
            return False
    
    def test_set_availability(self):
        """Test POST /api/courier/availability"""
        print("📝 Testing Set Availability...")
        
        try:
            # Test availability setting
            availability_data = {
                "slots": [
                    {
                        "weekday": 1,  # Monday
                        "start": "09:00",
                        "end": "17:00"
                    },
                    {
                        "weekday": 2,  # Tuesday
                        "start": "10:00",
                        "end": "18:00"
                    }
                ]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/courier/availability",
                json=availability_data,
                headers={
                    "Authorization": f"Bearer {self.jwt_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "availability" in data:
                    saved_slots = data["availability"]
                    self.log_test(
                        "Set Availability", 
                        True, 
                        f"Availability saved: {len(saved_slots)} slots"
                    )
                    return True
                else:
                    self.log_test("Set Availability", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Set Availability", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Set Availability", False, f"Exception: {str(e)}")
            return False
    
    def test_order_history(self):
        """Test GET /api/courier/orders/history"""
        print("📋 Testing Order History...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/courier/orders/history?page=1&size=10",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data and "orders" in data and "pagination" in data:
                    orders = data["orders"]
                    pagination = data["pagination"]
                    self.log_test(
                        "Order History", 
                        True, 
                        f"History retrieved: {len(orders)} orders, total: {pagination.get('total', 0)}"
                    )
                    return True
                else:
                    self.log_test("Order History", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Order History", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Order History", False, f"Exception: {str(e)}")
            return False
    
    def test_ready_orders(self):
        """Test GET /api/courier/orders/ready"""
        print("🚚 Testing Ready Orders...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/courier/orders/ready",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                # Check if response is a list (expected format)
                data = response.json()
                if isinstance(data, list):
                    self.log_test(
                        "Ready Orders", 
                        True, 
                        f"Ready orders retrieved: {len(data)} orders available"
                    )
                    return True
                else:
                    self.log_test("Ready Orders", False, "Response is not a list", data)
                    return False
            else:
                self.log_test(
                    "Ready Orders", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Ready Orders", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all courier endpoint tests"""
        print("🚀 PHASE 1 COURIER BACKEND QUICK TEST")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Courier: {COURIER_EMAIL}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 50)
        print()
        
        # Test authentication first
        if not self.test_courier_authentication():
            print("❌ Authentication failed - cannot proceed with other tests")
            return False
        
        # Run all endpoint tests
        tests = [
            self.test_earnings_pdf_report,
            self.test_profile_update,
            self.test_get_availability,
            self.test_set_availability,
            self.test_order_history,
            self.test_ready_orders
        ]
        
        passed = 0
        total = len(tests) + 1  # +1 for authentication
        
        for test_func in tests:
            if test_func():
                passed += 1
        
        # Add authentication test to passed count
        passed += 1  # Authentication passed if we got here
        
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        
        if success_rate >= 85:
            print("🎉 EXCELLENT - Courier endpoints are working well!")
        elif success_rate >= 70:
            print("✅ GOOD - Most courier endpoints are functional")
        elif success_rate >= 50:
            print("⚠️  PARTIAL - Some courier endpoints need attention")
        else:
            print("❌ CRITICAL - Major issues with courier endpoints")
        
        return success_rate >= 70

def main():
    """Main test execution"""
    tester = CourierBackendTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()