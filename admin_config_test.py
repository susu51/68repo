#!/usr/bin/env python3
"""
Admin Config System and Commission Endpoints Testing
Testing the FIXED admin config system and commission endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://address-manager-5.preview.emergentagent.com/api"
ADMIN_PASSWORD = "6851"

class AdminConfigTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def admin_login(self):
        """Test admin authentication with password 6851"""
        try:
            # Test admin login with any email + password "6851"
            test_email = "admin-config-test@kuryecini.com"
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": test_email,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"Admin login successful with email: {test_email}, role: {data.get('user', {}).get('role')}"
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, "", str(e))
            return False
    
    def test_get_admin_config(self):
        """Test GET /api/admin/config endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/config")
            
            if response.status_code == 200:
                data = response.json()
                configs = data.get("configurations", {})
                
                self.log_test(
                    "GET /api/admin/config", 
                    True, 
                    f"Retrieved {len(configs)} configurations. Keys: {list(configs.keys())}"
                )
                return True
            else:
                self.log_test(
                    "GET /api/admin/config", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/admin/config", False, "", str(e))
            return False
    
    def test_config_update(self):
        """Test POST /api/admin/config/update endpoint"""
        try:
            # Test updating a configuration
            test_key = "test_config_key"
            test_value = "test_config_value_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            test_description = "Test configuration for admin config system testing"
            
            response = self.session.post(f"{BACKEND_URL}/admin/config/update", params={
                "config_key": test_key,
                "config_value": test_value,
                "description": test_description
            })
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_test(
                    "POST /api/admin/config/update", 
                    True, 
                    f"Config updated successfully. Key: {test_key}, Value: {test_value}"
                )
                return True
            else:
                self.log_test(
                    "POST /api/admin/config/update", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("POST /api/admin/config/update", False, "", str(e))
            return False
    
    def test_get_commission_settings(self):
        """Test GET /api/admin/config/commission endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/config/commission")
            
            if response.status_code == 200:
                data = response.json()
                
                platform_rate = data.get("platform_commission_rate")
                courier_rate = data.get("courier_commission_rate")
                restaurant_rate = data.get("restaurant_fee_rate")
                
                self.log_test(
                    "GET /api/admin/config/commission", 
                    True, 
                    f"Platform: {platform_rate*100:.1f}%, Courier: {courier_rate*100:.1f}%, Restaurant: {restaurant_rate*100:.1f}%"
                )
                return True
            else:
                self.log_test(
                    "GET /api/admin/config/commission", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/admin/config/commission", False, "", str(e))
            return False
    
    def test_commission_update_valid(self):
        """Test POST /api/admin/config/commission with valid values"""
        try:
            # Test with valid commission rates (platform: 0.05, courier: 0.05)
            response = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                "platform_commission": 0.05,
                "courier_commission": 0.05
            })
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_test(
                    "POST /api/admin/config/commission (Valid)", 
                    True, 
                    f"Commission updated: {data.get('message')}. Platform: {data.get('platform_commission')}, Courier: {data.get('courier_commission')}, Restaurant: {data.get('restaurant_fee')}"
                )
                return True
            else:
                self.log_test(
                    "POST /api/admin/config/commission (Valid)", 
                    False, 
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("POST /api/admin/config/commission (Valid)", False, "", str(e))
            return False
    
    def test_commission_validation_high_rates(self):
        """Test commission validation with invalid rates > 0.2"""
        try:
            # Test with invalid high platform commission (> 20%)
            response = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                "platform_commission": 0.25,  # 25% - should be rejected
                "courier_commission": 0.05
            })
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                self.log_test(
                    "Commission Validation (High Platform Rate)", 
                    True, 
                    f"Correctly rejected high platform rate (25%). Error: {error_detail}"
                )
                
                # Test with invalid high courier commission (> 20%)
                response2 = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                    "platform_commission": 0.05,
                    "courier_commission": 0.25  # 25% - should be rejected
                })
                
                if response2.status_code == 400:
                    error_detail2 = response2.json().get("detail", "")
                    
                    self.log_test(
                        "Commission Validation (High Courier Rate)", 
                        True, 
                        f"Correctly rejected high courier rate (25%). Error: {error_detail2}"
                    )
                    return True
                else:
                    self.log_test(
                        "Commission Validation (High Courier Rate)", 
                        False, 
                        f"Should have rejected high courier rate but got status: {response2.status_code}",
                        response2.text
                    )
                    return False
            else:
                self.log_test(
                    "Commission Validation (High Platform Rate)", 
                    False, 
                    f"Should have rejected high platform rate but got status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Commission Validation (High Rates)", False, "", str(e))
            return False
    
    def test_commission_validation_low_restaurant_share(self):
        """Test commission validation ensuring restaurant gets at least 60%"""
        try:
            # Test with rates that would give restaurant < 60%
            response = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                "platform_commission": 0.25,  # 25%
                "courier_commission": 0.20   # 20% - total 45%, leaving only 55% for restaurant
            })
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                self.log_test(
                    "Commission Validation (Low Restaurant Share)", 
                    True, 
                    f"Correctly rejected rates leaving restaurant with <60%. Error: {error_detail}"
                )
                return True
            else:
                self.log_test(
                    "Commission Validation (Low Restaurant Share)", 
                    False, 
                    f"Should have rejected low restaurant share but got status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Commission Validation (Low Restaurant Share)", False, "", str(e))
            return False
    
    def test_turkish_error_messages(self):
        """Test that error messages are in Turkish"""
        try:
            # Test with invalid commission to get Turkish error message
            response = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                "platform_commission": 0.30,  # Invalid rate
                "courier_commission": 0.05
            })
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                # Check if error message contains Turkish characters/words
                turkish_indicators = ["komisyon", "olmalıdır", "arasında", "%"]
                has_turkish = any(indicator in error_detail.lower() for indicator in turkish_indicators)
                
                self.log_test(
                    "Turkish Error Messages", 
                    has_turkish, 
                    f"Error message: '{error_detail}'. Contains Turkish: {has_turkish}"
                )
                return has_turkish
            else:
                self.log_test(
                    "Turkish Error Messages", 
                    False, 
                    f"Expected 400 error but got status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Turkish Error Messages", False, "", str(e))
            return False
    
    def test_audit_logging(self):
        """Test that commission changes are logged in audit logs"""
        try:
            # First, make a commission change
            test_platform_rate = 0.06  # 6%
            test_courier_rate = 0.04   # 4%
            
            response = self.session.post(f"{BACKEND_URL}/admin/config/commission", params={
                "platform_commission": test_platform_rate,
                "courier_commission": test_courier_rate
            })
            
            if response.status_code != 200:
                self.log_test(
                    "Audit Logging Setup", 
                    False, 
                    f"Failed to update commission for audit test. Status: {response.status_code}",
                    response.text
                )
                return False
            
            # Now check audit logs for the commission update
            audit_response = self.session.get(f"{BACKEND_URL}/admin/audit-logs", params={
                "action_type": "commission_update",
                "limit": 10
            })
            
            if audit_response.status_code == 200:
                audit_data = audit_response.json()
                audit_logs = audit_data.get("audit_logs", [])
                
                # Look for recent commission update log
                recent_commission_log = None
                for log in audit_logs:
                    if log.get("action_type") == "commission_update" and "commission_rates" in log.get("target_id", ""):
                        recent_commission_log = log
                        break
                
                if recent_commission_log:
                    self.log_test(
                        "Audit Logging for Commission Changes", 
                        True, 
                        f"Found audit log: {recent_commission_log.get('description')}. User: {recent_commission_log.get('user_email')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Audit Logging for Commission Changes", 
                        False, 
                        f"No commission update audit log found. Found {len(audit_logs)} logs total"
                    )
                    return False
            else:
                self.log_test(
                    "Audit Logging for Commission Changes", 
                    False, 
                    f"Failed to retrieve audit logs. Status: {audit_response.status_code}",
                    audit_response.text
                )
                return False
                
        except Exception as e:
            self.log_test("Audit Logging for Commission Changes", False, "", str(e))
            return False
    
    def run_all_tests(self):
        """Run all admin config and commission tests"""
        print("🔧 ADMIN CONFIG SYSTEM AND COMMISSION ENDPOINTS TESTING")
        print("=" * 60)
        print()
        
        # Step 1: Admin Authentication
        if not self.admin_login():
            print("❌ Admin authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Test admin config endpoints
        self.test_get_admin_config()
        self.test_config_update()
        
        # Step 3: Test commission endpoints
        self.test_get_commission_settings()
        self.test_commission_update_valid()
        
        # Step 4: Test commission validation
        self.test_commission_validation_high_rates()
        self.test_commission_validation_low_restaurant_share()
        
        # Step 5: Test Turkish error messages
        self.test_turkish_error_messages()
        
        # Step 6: Test audit logging
        self.test_audit_logging()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['error']}")
            print()
        
        # Check for critical issues
        critical_failures = []
        for result in self.test_results:
            if not result["success"] and any(critical in result["test"] for critical in ["Authentication", "GET /api/admin/config", "POST /api/admin/config/commission"]):
                critical_failures.append(result["test"])
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"  - {failure}")
            print()
            return False
        
        print("🎉 ADMIN CONFIG SYSTEM TESTING COMPLETE")
        return passed_tests >= total_tests * 0.8  # 80% success rate required

if __name__ == "__main__":
    tester = AdminConfigTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)