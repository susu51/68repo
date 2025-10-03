#!/usr/bin/env python3
"""
ADMIN LOGIN SPECIFIC TESTING
Testing admin authentication with fixed credentials as requested in review
"""

import requests
import json
import time
import jwt
from datetime import datetime

# Configuration
BACKEND_URL = "https://order-platform-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class AdminLoginTest:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def test_admin_login_with_fixed_credentials(self):
        """Test admin login with the exact credentials from review request"""
        print("\n🔐 CRITICAL ADMIN LOGIN TEST")
        print("=" * 60)
        
        # Test admin login with fixed credentials
        admin_credentials = {
            "email": "admin@kuryecini.com",
            "password": "KuryeciniAdmin2024!"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=admin_credentials,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "access_token" in data and "user" in data:
                    user_data = data["user"]
                    
                    # Verify admin role
                    if user_data.get("role") == "admin":
                        self.tokens["admin"] = data["access_token"]
                        
                        # Decode JWT to verify contents
                        try:
                            # Note: We can't verify signature without secret, but we can decode payload
                            token_payload = jwt.decode(data["access_token"], options={"verify_signature": False})
                            
                            self.log_result(
                                "Admin Login - Correct Credentials",
                                True,
                                f"✅ Login successful. Role: {user_data.get('role')}, Email: {user_data.get('email')}, Token contains role: {token_payload.get('role')}",
                                response_time
                            )
                            
                            return True
                        except Exception as jwt_error:
                            self.log_result(
                                "Admin Login - JWT Decode",
                                False,
                                f"❌ JWT decode failed: {str(jwt_error)}",
                                response_time
                            )
                            return False
                    else:
                        self.log_result(
                            "Admin Login - Role Verification",
                            False,
                            f"❌ Expected admin role, got: {user_data.get('role')}",
                            response_time
                        )
                        return False
                else:
                    self.log_result(
                        "Admin Login - Response Structure",
                        False,
                        f"❌ Missing access_token or user in response: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_result(
                    "Admin Login - HTTP Status",
                    False,
                    f"❌ HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "Admin Login - Network Error",
                False,
                f"❌ Request failed: {str(e)}",
                response_time
            )
            return False
    
    def test_admin_endpoints_access(self):
        """Test admin-only endpoint access with the token"""
        print("\n🔒 ADMIN ENDPOINTS ACCESS TEST")
        print("=" * 60)
        
        if "admin" not in self.tokens:
            self.log_result(
                "Admin Endpoints - No Token",
                False,
                "❌ No admin token available for testing"
            )
            return False
        
        admin_token = self.tokens["admin"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin endpoints
        admin_endpoints = [
            ("/admin/users", "GET", "Admin Users List"),
            ("/admin/config", "GET", "Admin Config System"),
            ("/admin/config/commission", "GET", "Admin Commission Settings"),
            ("/admin/couriers/kyc", "GET", "Admin KYC Management")
        ]
        
        success_count = 0
        total_tests = len(admin_endpoints)
        
        for endpoint, method, description in admin_endpoints:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}", headers=headers, timeout=10)
                else:
                    response = self.session.request(method, f"{API_BASE}{endpoint}", headers=headers, timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        f"Admin Access - {description}",
                        True,
                        f"✅ {method} {endpoint} successful. Data length: {len(str(data))} chars",
                        response_time
                    )
                    success_count += 1
                elif response.status_code == 401:
                    self.log_result(
                        f"Admin Access - {description}",
                        False,
                        f"❌ 401 Unauthorized - Token not accepted",
                        response_time
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"Admin Access - {description}",
                        False,
                        f"❌ 403 Forbidden - Admin role not recognized",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Admin Access - {description}",
                        False,
                        f"❌ HTTP {response.status_code}: {response.text[:200]}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"Admin Access - {description}",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == total_tests
    
    def test_other_user_roles(self):
        """Test other user roles as requested"""
        print("\n👥 OTHER USER ROLES TEST")
        print("=" * 60)
        
        test_users = [
            {"email": "testcustomer@example.com", "password": "test123", "expected_role": "customer"},
            {"email": "testbusiness@example.com", "password": "test123", "expected_role": "business"},
            {"email": "testkurye@example.com", "password": "test123", "expected_role": "courier"}
        ]
        
        success_count = 0
        total_tests = len(test_users)
        
        for user_creds in test_users:
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json={"email": user_creds["email"], "password": user_creds["password"]},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    user_data = data.get("user", {})
                    actual_role = user_data.get("role")
                    
                    if actual_role == user_creds["expected_role"]:
                        # Store token for potential further testing
                        self.tokens[actual_role] = data["access_token"]
                        
                        self.log_result(
                            f"User Login - {user_creds['expected_role'].title()}",
                            True,
                            f"✅ {user_creds['email']} login successful. Role: {actual_role}",
                            response_time
                        )
                        success_count += 1
                    else:
                        self.log_result(
                            f"User Login - {user_creds['expected_role'].title()}",
                            False,
                            f"❌ Expected role {user_creds['expected_role']}, got {actual_role}",
                            response_time
                        )
                else:
                    self.log_result(
                        f"User Login - {user_creds['expected_role'].title()}",
                        False,
                        f"❌ HTTP {response.status_code}: {response.text}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"User Login - {user_creds['expected_role'].title()}",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == total_tests
    
    def test_admin_config_endpoints_specifically(self):
        """Test /api/admin/config endpoints specifically as mentioned in review"""
        print("\n⚙️ ADMIN CONFIG ENDPOINTS SPECIFIC TEST")
        print("=" * 60)
        
        if "admin" not in self.tokens:
            self.log_result(
                "Admin Config - No Token",
                False,
                "❌ No admin token available for config testing"
            )
            return False
        
        admin_token = self.tokens["admin"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test specific config endpoints
        config_tests = [
            {
                "endpoint": "/admin/config",
                "method": "GET",
                "description": "Get Admin Configuration",
                "expected": "Configuration data"
            },
            {
                "endpoint": "/admin/config/commission",
                "method": "GET", 
                "description": "Get Commission Settings",
                "expected": "Commission rates"
            }
        ]
        
        success_count = 0
        total_tests = len(config_tests)
        
        for test_config in config_tests:
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{API_BASE}{test_config['endpoint']}", 
                    headers=headers, 
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        f"Config Access - {test_config['description']}",
                        True,
                        f"✅ {test_config['endpoint']} accessible. Response: {str(data)[:100]}...",
                        response_time
                    )
                    success_count += 1
                elif response.status_code == 401:
                    self.log_result(
                        f"Config Access - {test_config['description']}",
                        False,
                        f"❌ 401 Unauthorized - Admin token not accepted for config endpoint",
                        response_time
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"Config Access - {test_config['description']}",
                        False,
                        f"❌ 403 Forbidden - Admin role not sufficient for config access",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Config Access - {test_config['description']}",
                        False,
                        f"❌ HTTP {response.status_code}: {response.text[:200]}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"Config Access - {test_config['description']}",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == total_tests
    
    def run_all_tests(self):
        """Run all admin login tests"""
        print("🎯 ADMIN LOGIN SPECIFIC TESTING STARTED")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Test 1: Admin login with fixed credentials
        admin_login_success = self.test_admin_login_with_fixed_credentials()
        
        # Test 2: Admin endpoints access
        admin_access_success = self.test_admin_endpoints_access()
        
        # Test 3: Admin config endpoints specifically
        admin_config_success = self.test_admin_config_endpoints_specifically()
        
        # Test 4: Other user roles
        other_users_success = self.test_other_user_roles()
        
        # Summary
        total_time = time.time() - self.start_time
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 ADMIN LOGIN TESTING SUMMARY")
        print("=" * 80)
        print(f"✅ Successful Tests: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"🔐 Admin Login: {'✅ WORKING' if admin_login_success else '❌ FAILED'}")
        print(f"🔒 Admin Access: {'✅ WORKING' if admin_access_success else '❌ FAILED'}")
        print(f"⚙️  Admin Config: {'✅ WORKING' if admin_config_success else '❌ FAILED'}")
        print(f"👥 Other Users: {'✅ WORKING' if other_users_success else '❌ FAILED'}")
        
        # Critical issues
        critical_issues = []
        if not admin_login_success:
            critical_issues.append("Admin login with admin@kuryecini.com / KuryeciniAdmin2024! failing")
        if not admin_access_success:
            critical_issues.append("Admin JWT token not accepted by admin endpoints")
        if not admin_config_success:
            critical_issues.append("Admin config endpoints not accessible")
        if not other_users_success:
            critical_issues.append("Other user role authentication failing")
        
        if critical_issues:
            print("\n❌ CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   • {issue}")
        else:
            print("\n🎉 ALL ADMIN AUTHENTICATION TESTS PASSED!")
        
        print("=" * 80)
        
        return {
            "success_rate": success_rate,
            "admin_login_working": admin_login_success,
            "admin_access_working": admin_access_success,
            "admin_config_working": admin_config_success,
            "other_users_working": other_users_success,
            "critical_issues": critical_issues,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "total_time": total_time
        }

if __name__ == "__main__":
    tester = AdminLoginTest()
    results = tester.run_all_tests()