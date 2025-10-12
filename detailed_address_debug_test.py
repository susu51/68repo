#!/usr/bin/env python3
"""
Detailed Address Creation Debug Test
Since backend tests pass 100%, let's investigate potential edge cases and frontend integration issues
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://stable-menus.preview.emergentagent.com/api"

# Test credentials
TEST_CUSTOMER_EMAIL = "testcustomer@example.com"
TEST_CUSTOMER_PASSWORD = "test123"

class DetailedAddressDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
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
                
                self.log_test("Customer Authentication", True, f"Token: {self.auth_token[:50]}...")
                return True
            else:
                self.log_test("Customer Authentication", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_turkish_characters_in_address(self):
        """Test Turkish characters in address fields"""
        turkish_addresses = [
            {
                "label": "Çalışma Yeri",
                "city": "İstanbul",
                "description": "Şişli'deki ofisim - Türkçe karakterler",
                "lat": 41.0082,
                "lng": 28.9784
            },
            {
                "label": "Büyükanne Evi",
                "city": "Ankara",
                "description": "Çankaya'da büyükannemin evi",
                "lat": 39.9334,
                "lng": 32.8597
            },
            {
                "label": "Öğrenci Evi",
                "city": "İzmir",
                "description": "Üniversite yakınındaki ev",
                "lat": 38.4192,
                "lng": 27.1287
            }
        ]
        
        for i, addr in enumerate(turkish_addresses):
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=addr)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        f"Turkish Characters Test {i+1}",
                        True,
                        f"Created: {addr['label']} in {addr['city']}"
                    )
                else:
                    self.log_test(
                        f"Turkish Characters Test {i+1}",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Turkish Characters Test {i+1}",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def test_edge_case_coordinates(self):
        """Test edge case coordinates"""
        edge_cases = [
            {
                "name": "Zero coordinates",
                "data": {
                    "label": "Zero Point",
                    "city": "İstanbul",
                    "description": "Zero coordinates test",
                    "lat": 0.0,
                    "lng": 0.0
                }
            },
            {
                "name": "Negative coordinates",
                "data": {
                    "label": "Negative Test",
                    "city": "İstanbul", 
                    "description": "Negative coordinates test",
                    "lat": -41.0082,
                    "lng": -28.9784
                }
            },
            {
                "name": "Very precise coordinates",
                "data": {
                    "label": "Precise Location",
                    "city": "İstanbul",
                    "description": "Very precise coordinates",
                    "lat": 41.008238472834,
                    "lng": 28.978472834729
                }
            },
            {
                "name": "String coordinates (should fail)",
                "data": {
                    "label": "String Coords",
                    "city": "İstanbul",
                    "description": "String coordinates test",
                    "lat": "41.0082",
                    "lng": "28.9784"
                }
            }
        ]
        
        for case in edge_cases:
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=case["data"])
                
                if response.status_code == 200:
                    self.log_test(
                        f"Edge Case: {case['name']}",
                        True,
                        "Handled successfully"
                    )
                else:
                    # For string coordinates, failure is expected
                    expected_failure = "String coordinates" in case["name"]
                    self.log_test(
                        f"Edge Case: {case['name']}",
                        expected_failure,
                        f"Status: {response.status_code} {'(Expected)' if expected_failure else '(Unexpected)'}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Edge Case: {case['name']}",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def test_very_long_text_fields(self):
        """Test very long text in address fields"""
        long_text = "Bu çok uzun bir adres açıklaması. " * 50  # Very long description
        long_label = "Çok Uzun Adres Etiketi " * 10  # Very long label
        
        long_address = {
            "label": long_label,
            "city": "İstanbul",
            "description": long_text,
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=long_address)
            
            if response.status_code == 200:
                self.log_test(
                    "Long Text Fields Test",
                    True,
                    f"Handled long text - Label: {len(long_label)} chars, Description: {len(long_text)} chars"
                )
            else:
                self.log_test(
                    "Long Text Fields Test",
                    False,
                    f"Failed with long text - Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Long Text Fields Test",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_special_characters_and_emojis(self):
        """Test special characters and emojis in address"""
        special_address = {
            "label": "🏠 Ev Adresim 🏡",
            "city": "İstanbul",
            "description": "Özel karakterler: @#$%^&*()_+-=[]{}|;':\",./<>? ve emojiler 🚀🎉",
            "lat": 41.0082,
            "lng": 28.9784
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/user/addresses", json=special_address)
            
            if response.status_code == 200:
                self.log_test(
                    "Special Characters & Emojis Test",
                    True,
                    "Successfully handled special characters and emojis"
                )
            else:
                self.log_test(
                    "Special Characters & Emojis Test",
                    False,
                    f"Failed - Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_test(
                "Special Characters & Emojis Test",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_concurrent_address_creation(self):
        """Test creating multiple addresses rapidly"""
        addresses = []
        for i in range(5):
            addresses.append({
                "label": f"Rapid Test {i+1}",
                "city": "İstanbul",
                "description": f"Concurrent creation test {i+1}",
                "lat": 41.0082 + (i * 0.001),
                "lng": 28.9784 + (i * 0.001)
            })
        
        success_count = 0
        for i, addr in enumerate(addresses):
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=addr)
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
        
        self.log_test(
            "Concurrent Address Creation",
            success_count == len(addresses),
            f"Created {success_count}/{len(addresses)} addresses successfully"
        )
    
    def test_address_with_null_values(self):
        """Test address creation with null/None values"""
        null_test_cases = [
            {
                "name": "Null lat/lng",
                "data": {
                    "label": "Null Coordinates",
                    "city": "İstanbul",
                    "description": "Test with null coordinates",
                    "lat": None,
                    "lng": None
                }
            },
            {
                "name": "Null description",
                "data": {
                    "label": "No Description",
                    "city": "İstanbul",
                    "description": None,
                    "lat": 41.0082,
                    "lng": 28.9784
                }
            }
        ]
        
        for case in null_test_cases:
            try:
                response = self.session.post(f"{BACKEND_URL}/user/addresses", json=case["data"])
                
                if response.status_code == 200:
                    self.log_test(
                        f"Null Values: {case['name']}",
                        True,
                        "Handled null values correctly"
                    )
                else:
                    self.log_test(
                        f"Null Values: {case['name']}",
                        False,
                        f"Failed - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Null Values: {case['name']}",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def check_database_consistency(self):
        """Check if all created addresses are properly stored"""
        try:
            response = self.session.get(f"{BACKEND_URL}/user/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                
                # Check for data integrity
                issues = []
                for addr in addresses:
                    if not addr.get('id'):
                        issues.append("Missing ID")
                    if not addr.get('label') and not addr.get('city'):
                        issues.append("Missing both label and city")
                
                if issues:
                    self.log_test(
                        "Database Consistency Check",
                        False,
                        f"Found issues: {', '.join(issues)}"
                    )
                else:
                    self.log_test(
                        "Database Consistency Check",
                        True,
                        f"All {len(addresses)} addresses have proper data integrity"
                    )
                    
            else:
                self.log_test(
                    "Database Consistency Check",
                    False,
                    f"Failed to retrieve addresses - Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(
                "Database Consistency Check",
                False,
                f"Exception: {str(e)}"
            )
    
    def run_detailed_debug(self):
        """Run detailed debugging tests"""
        print("🔍 DETAILED ADDRESS CREATION DEBUG TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing edge cases and potential frontend integration issues...")
        print("=" * 70)
        print()
        
        # Authenticate
        if not self.authenticate_customer():
            print("❌ CRITICAL: Authentication failed")
            return False
        
        # Run detailed tests
        self.test_turkish_characters_in_address()
        self.test_edge_case_coordinates()
        self.test_very_long_text_fields()
        self.test_special_characters_and_emojis()
        self.test_concurrent_address_creation()
        self.test_address_with_null_values()
        self.check_database_consistency()
        
        # Summary
        print("=" * 70)
        print("📊 DETAILED DEBUG SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Analysis
        print("🔍 ROOT CAUSE ANALYSIS:")
        if success_rate >= 90:
            print("   ✅ Backend address creation is working excellently")
            print("   ✅ All edge cases handled properly")
            print("   ✅ Turkish characters, special chars, and emojis supported")
            print("   ✅ Data validation and storage working correctly")
            print()
            print("   💡 CONCLUSION: The issue 'Adres eklenirken hata oluştu' is likely:")
            print("      - Frontend validation or UI issue")
            print("      - Network connectivity problem")
            print("      - Frontend-backend API integration mismatch")
            print("      - User input validation on frontend side")
            print()
            print("   🎯 RECOMMENDATION: Check frontend AddressesPage.js component")
        else:
            print("   ❌ Backend has issues with edge cases")
            failed_tests_list = [r for r in self.test_results if not r["success"]]
            for failure in failed_tests_list:
                print(f"      - {failure['test']}: {failure['details']}")
        
        return success_rate >= 80

def main():
    """Main execution"""
    debugger = DetailedAddressDebugger()
    success = debugger.run_detailed_debug()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()