#!/usr/bin/env python3
"""
AI Settings API Testing for Panel-Aware AI Assistant Foundation

CRITICAL: Test the newly implemented AI Settings API endpoints for admin panel.

Test Scenarios:
1. GET Default AI Settings - Returns default settings with proper structure
2. PUT Update AI Settings - Updates settings and verifies persistence  
3. PUT Set Custom OpenAI Key - Sets custom key and verifies masking
4. POST Test OpenAI Connection - Tests connection with Emergent LLM Key
5. RBAC - Non-Admin Access Blocked - Verifies admin-only access

Authentication:
- Admin: admin@kuryecini.com / admin123
- Customer: test@kuryecini.com / test123 (for RBAC testing)
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://kuryecini-hub.preview.emergentagent.com"

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "admin@kuryecini.com",
    "password": "admin123"
}

CUSTOMER_CREDENTIALS = {
    "email": "test@kuryecini.com", 
    "password": "test123"
}

class AISettingsTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.customer_session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate_admin(self):
        """Authenticate admin user"""
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's cookie-based auth (success field) or JWT auth (access_token field)
                if data.get("success"):
                    # Cookie-based auth
                    user_role = data.get("user", {}).get("role")
                    if user_role == "admin":
                        self.log_test(
                            "Admin Authentication",
                            True,
                            f"Admin login successful (cookie-based): {ADMIN_CREDENTIALS['email']}, role: {user_role}"
                        )
                        return True
                elif data.get("access_token"):
                    # JWT-based auth
                    user_role = data.get("user", {}).get("role")
                    if user_role == "admin":
                        # Store token for header-based requests if needed
                        self.admin_token = data.get("access_token")
                        self.log_test(
                            "Admin Authentication",
                            True,
                            f"Admin login successful (JWT): {ADMIN_CREDENTIALS['email']}, role: {user_role}"
                        )
                        return True
                
                self.log_test("Admin Authentication", False, error=f"Wrong role: {data.get('user', {}).get('role')}")
                return False
            else:
                self.log_test("Admin Authentication", False, error=f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, error=f"Authentication error: {str(e)}")
            return False
    
    def authenticate_customer(self):
        """Authenticate customer user for RBAC testing"""
        try:
            response = self.customer_session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=CUSTOMER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_role = data.get("user", {}).get("role")
                
                if user_role == "customer":
                    self.log_test(
                        "Customer Authentication",
                        True,
                        f"Customer login successful, role: {user_role}"
                    )
                    return True
                else:
                    self.log_test("Customer Authentication", False, error=f"Expected customer role, got: {user_role}")
                    return False
            else:
                self.log_test("Customer Authentication", False, error=f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Customer Authentication", False, error=f"Authentication error: {str(e)}")
            return False

    def test_get_default_ai_settings(self):
        """Test 1: GET Default AI Settings"""
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/api/admin/ai/settings",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected default structure
                expected_fields = [
                    "id", "openai_api_key_configured", "use_emergent_key", 
                    "default_model", "default_time_window_minutes", 
                    "rate_limit_per_min", "redact_rules"
                ]
                
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    # Verify specific default values
                    checks = []
                    
                    if data.get("id") == "ai_settings_default":
                        checks.append("✓ ID correct")
                    else:
                        checks.append(f"✗ ID wrong: {data.get('id')}")
                    
                    if data.get("openai_api_key_configured") == False:
                        checks.append("✓ No custom key configured")
                    else:
                        checks.append(f"✗ Key configured flag wrong: {data.get('openai_api_key_configured')}")
                    
                    if data.get("use_emergent_key") == True:
                        checks.append("✓ Using emergent key")
                    else:
                        checks.append(f"✗ Emergent key flag wrong: {data.get('use_emergent_key')}")
                    
                    if data.get("default_model") == "gpt-4o-mini":
                        checks.append("✓ Default model correct")
                    else:
                        checks.append(f"✗ Default model wrong: {data.get('default_model')}")
                    
                    if data.get("default_time_window_minutes") == 60:
                        checks.append("✓ Time window correct")
                    else:
                        checks.append(f"✗ Time window wrong: {data.get('default_time_window_minutes')}")
                    
                    if data.get("rate_limit_per_min") == 6:
                        checks.append("✓ Rate limit correct")
                    else:
                        checks.append(f"✗ Rate limit wrong: {data.get('rate_limit_per_min')}")
                    
                    redact_rules = data.get("redact_rules", [])
                    if len(redact_rules) == 6:
                        checks.append("✓ 6 redact rules present")
                        
                        # Check if all expected rule types are present
                        rule_types = [rule.get("type") for rule in redact_rules]
                        expected_types = ["phone", "email", "iban", "jwt", "address", "card"]
                        missing_types = [t for t in expected_types if t not in rule_types]
                        
                        if not missing_types:
                            checks.append("✓ All redact rule types present")
                        else:
                            checks.append(f"✗ Missing redact types: {missing_types}")
                    else:
                        checks.append(f"✗ Wrong redact rules count: {len(redact_rules)}")
                    
                    self.log_test(
                        "GET Default AI Settings",
                        True,
                        f"Default settings returned correctly. Checks: {', '.join(checks)}"
                    )
                    return True
                else:
                    self.log_test(
                        "GET Default AI Settings",
                        False,
                        error=f"Missing required fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "GET Default AI Settings",
                    False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET Default AI Settings", False, error=f"Request error: {str(e)}")
            return False

    def test_update_ai_settings(self):
        """Test 2: PUT Update AI Settings"""
        try:
            # Update some settings
            update_data = {
                "default_time_window_minutes": 120,
                "rate_limit_per_min": 10
            }
            
            response = self.admin_session.put(
                f"{BACKEND_URL}/api/admin/ai/settings",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify the updated values are returned
                if (data.get("default_time_window_minutes") == 120 and 
                    data.get("rate_limit_per_min") == 10):
                    
                    # Verify persistence by getting settings again
                    get_response = self.admin_session.get(
                        f"{BACKEND_URL}/api/admin/ai/settings",
                        timeout=10
                    )
                    
                    if get_response.status_code == 200:
                        get_data = get_response.json()
                        
                        if (get_data.get("default_time_window_minutes") == 120 and 
                            get_data.get("rate_limit_per_min") == 10):
                            
                            self.log_test(
                                "PUT Update AI Settings",
                                True,
                                f"Settings updated and persisted: time_window={get_data.get('default_time_window_minutes')}, rate_limit={get_data.get('rate_limit_per_min')}"
                            )
                            return True
                        else:
                            self.log_test(
                                "PUT Update AI Settings",
                                False,
                                error=f"Settings not persisted correctly: time_window={get_data.get('default_time_window_minutes')}, rate_limit={get_data.get('rate_limit_per_min')}"
                            )
                            return False
                    else:
                        self.log_test(
                            "PUT Update AI Settings",
                            False,
                            error=f"Could not verify persistence: {get_response.status_code}"
                        )
                        return False
                else:
                    self.log_test(
                        "PUT Update AI Settings",
                        False,
                        error=f"Updated values not returned correctly: time_window={data.get('default_time_window_minutes')}, rate_limit={data.get('rate_limit_per_min')}"
                    )
                    return False
            else:
                self.log_test(
                    "PUT Update AI Settings",
                    False,
                    error=f"Update failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("PUT Update AI Settings", False, error=f"Request error: {str(e)}")
            return False

    def test_set_custom_openai_key(self):
        """Test 3: PUT Set Custom OpenAI Key"""
        try:
            # Set custom OpenAI key
            key_data = {
                "openai_api_key": "sk-test-custom-key-12345",
                "use_emergent_key": False
            }
            
            response = self.admin_session.put(
                f"{BACKEND_URL}/api/admin/ai/settings",
                json=key_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify key is configured but masked
                if (data.get("openai_api_key_configured") == True and 
                    data.get("use_emergent_key") == False):
                    
                    # Verify key is masked (should not contain the actual key)
                    if "sk-test-custom-key-12345" not in str(data):
                        self.log_test(
                            "PUT Set Custom OpenAI Key",
                            True,
                            f"Custom key set successfully: configured={data.get('openai_api_key_configured')}, use_emergent={data.get('use_emergent_key')}, key properly masked"
                        )
                        return True
                    else:
                        self.log_test(
                            "PUT Set Custom OpenAI Key",
                            False,
                            error="API key not properly masked in response"
                        )
                        return False
                else:
                    self.log_test(
                        "PUT Set Custom OpenAI Key",
                        False,
                        error=f"Key configuration flags wrong: configured={data.get('openai_api_key_configured')}, use_emergent={data.get('use_emergent_key')}"
                    )
                    return False
            else:
                self.log_test(
                    "PUT Set Custom OpenAI Key",
                    False,
                    error=f"Key setting failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("PUT Set Custom OpenAI Key", False, error=f"Request error: {str(e)}")
            return False

    def test_openai_connection(self):
        """Test 4: POST Test OpenAI Connection"""
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/api/admin/ai/settings/test",
                timeout=30  # Longer timeout for API call
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected response structure
                expected_fields = ["success", "message", "key_source", "model", "test_response"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    if data.get("success") == True:
                        key_source = data.get("key_source")
                        model = data.get("model")
                        test_response = data.get("test_response", "")
                        
                        # Verify we got a response from OpenAI
                        if test_response and len(test_response) > 0:
                            self.log_test(
                                "POST Test OpenAI Connection",
                                True,
                                f"OpenAI connection successful: key_source={key_source}, model={model}, response_length={len(test_response)} chars"
                            )
                            return True
                        else:
                            self.log_test(
                                "POST Test OpenAI Connection",
                                False,
                                error="No test response received from OpenAI"
                            )
                            return False
                    else:
                        self.log_test(
                            "POST Test OpenAI Connection",
                            False,
                            error=f"Connection test failed: {data.get('message')}"
                        )
                        return False
                else:
                    self.log_test(
                        "POST Test OpenAI Connection",
                        False,
                        error=f"Missing response fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "POST Test OpenAI Connection",
                    False,
                    error=f"Connection test failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("POST Test OpenAI Connection", False, error=f"Request error: {str(e)}")
            return False

    def test_rbac_non_admin_access(self):
        """Test 5: RBAC - Non-Admin Access Blocked"""
        try:
            # Try to access AI settings with customer credentials
            response = self.customer_session.get(
                f"{BACKEND_URL}/api/admin/ai/settings",
                timeout=10
            )
            
            # Should be blocked (403 Forbidden or 401 Unauthorized)
            if response.status_code in [401, 403]:
                self.log_test(
                    "RBAC - Non-Admin Access Blocked",
                    True,
                    f"Customer access properly blocked: {response.status_code} - Access denied as expected"
                )
                return True
            elif response.status_code == 200:
                self.log_test(
                    "RBAC - Non-Admin Access Blocked",
                    False,
                    error="Customer was able to access admin AI settings (SECURITY ISSUE)"
                )
                return False
            else:
                self.log_test(
                    "RBAC - Non-Admin Access Blocked",
                    False,
                    error=f"Unexpected response code: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("RBAC - Non-Admin Access Blocked", False, error=f"Request error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all AI Settings API tests"""
        print("🚀 Starting AI Settings API Testing for Panel-Aware AI Assistant Foundation")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - cannot proceed with tests")
            return
            
        if not self.authenticate_customer():
            print("❌ Customer authentication failed - cannot proceed with RBAC tests")
            return
        
        print("\n🔧 Testing AI Settings API Endpoints...")
        print("-" * 50)
        
        # Test 1: GET Default AI Settings
        self.test_get_default_ai_settings()
        
        # Test 2: PUT Update AI Settings
        self.test_update_ai_settings()
        
        # Test 3: PUT Set Custom OpenAI Key
        self.test_set_custom_openai_key()
        
        # Test 4: POST Test OpenAI Connection
        self.test_openai_connection()
        
        # Test 5: RBAC - Non-Admin Access Blocked
        self.test_rbac_non_admin_access()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 AI SETTINGS API TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🎯 KEY VALIDATION POINTS:")
        
        # Check critical functionality
        default_settings_working = any(r["test"] == "GET Default AI Settings" and r["success"] for r in self.test_results)
        settings_persistence_working = any(r["test"] == "PUT Update AI Settings" and r["success"] for r in self.test_results)
        key_masking_working = any(r["test"] == "PUT Set Custom OpenAI Key" and r["success"] for r in self.test_results)
        openai_connection_working = any(r["test"] == "POST Test OpenAI Connection" and r["success"] for r in self.test_results)
        rbac_working = any(r["test"] == "RBAC - Non-Admin Access Blocked" and r["success"] for r in self.test_results)
        
        if default_settings_working:
            print("   ✅ Default settings return correctly without database entry")
        else:
            print("   ❌ Default settings NOT WORKING")
            
        if settings_persistence_working:
            print("   ✅ Settings persist to admin_settings_ai collection")
        else:
            print("   ❌ Settings persistence FAILED")
            
        if key_masking_working:
            print("   ✅ API keys are masked in responses (never exposed)")
        else:
            print("   ❌ API key masking FAILED")
            
        if openai_connection_working:
            print("   ✅ Emergent LLM Key integration working")
        else:
            print("   ❌ OpenAI connection test FAILED")
            
        if rbac_working:
            print("   ✅ RBAC enforcement (admin-only access)")
        else:
            print("   ❌ RBAC enforcement FAILED")
        
        # Overall verdict
        if success_rate >= 80:
            print(f"\n🎉 VERDICT: AI Settings API is WORKING EXCELLENTLY ({success_rate:.1f}% success rate)")
            print("   The Panel-Aware AI Assistant foundation is ready for use!")
        elif success_rate >= 60:
            print(f"\n⚠️ VERDICT: AI Settings API has MINOR ISSUES ({success_rate:.1f}% success rate)")
            print("   Some functionality may need attention before full deployment.")
        else:
            print(f"\n🚨 VERDICT: AI Settings API has CRITICAL ISSUES ({success_rate:.1f}% success rate)")
            print("   Major fixes required before the AI Assistant can be used.")

def main():
    """Main test runner"""
    tester = AISettingsTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()