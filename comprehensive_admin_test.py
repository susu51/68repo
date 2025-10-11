#!/usr/bin/env python3
"""
COMPREHENSIVE ADMIN AND USER MANAGEMENT TESTING
Testing all authentication flows and user management as requested
"""

import requests
import json
import time
import jwt
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-stable.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveAdminTest:
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
        
    def test_all_authentication_flows(self):
        """Test all authentication flows comprehensively"""
        print("\n🔐 COMPREHENSIVE AUTHENTICATION TESTING")
        print("=" * 70)
        
        # Test users with exact credentials from review request
        test_users = [
            {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!",
                "expected_role": "admin",
                "description": "Admin (Fixed Credentials)"
            },
            {
                "email": "testcustomer@example.com", 
                "password": "test123",
                "expected_role": "customer",
                "description": "Customer"
            },
            {
                "email": "testbusiness@example.com",
                "password": "test123", 
                "expected_role": "business",
                "description": "Business"
            },
            {
                "email": "testkurye@example.com",
                "password": "test123",
                "expected_role": "courier", 
                "description": "Courier"
            }
        ]
        
        success_count = 0
        
        for user in test_users:
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json={"email": user["email"], "password": user["password"]},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    if "access_token" in data and "refresh_token" in data and "user" in data:
                        user_data = data["user"]
                        actual_role = user_data.get("role")
                        
                        if actual_role == user["expected_role"]:
                            # Store token for further testing
                            self.tokens[actual_role] = data["access_token"]
                            
                            # Decode JWT to verify contents
                            try:
                                token_payload = jwt.decode(data["access_token"], options={"verify_signature": False})
                                token_role = token_payload.get("role")
                                token_email = token_payload.get("sub")
                                
                                if token_role == user["expected_role"] and token_email == user["email"]:
                                    self.log_result(
                                        f"Auth - {user['description']}",
                                        True,
                                        f"✅ Login successful. Role: {actual_role}, JWT role: {token_role}, Email: {user_data.get('email')}",
                                        response_time
                                    )
                                    success_count += 1
                                else:
                                    self.log_result(
                                        f"Auth - {user['description']}",
                                        False,
                                        f"❌ JWT mismatch. Expected role: {user['expected_role']}, JWT role: {token_role}",
                                        response_time
                                    )
                            except Exception as jwt_error:
                                self.log_result(
                                    f"Auth - {user['description']}",
                                    False,
                                    f"❌ JWT decode failed: {str(jwt_error)}",
                                    response_time
                                )
                        else:
                            self.log_result(
                                f"Auth - {user['description']}",
                                False,
                                f"❌ Role mismatch. Expected: {user['expected_role']}, Got: {actual_role}",
                                response_time
                            )
                    else:
                        self.log_result(
                            f"Auth - {user['description']}",
                            False,
                            f"❌ Missing required fields in response: {list(data.keys())}",
                            response_time
                        )
                else:
                    self.log_result(
                        f"Auth - {user['description']}",
                        False,
                        f"❌ HTTP {response.status_code}: {response.text[:200]}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"Auth - {user['description']}",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == len(test_users)
    
    def test_admin_endpoints_comprehensive(self):
        """Test all admin endpoints comprehensively"""
        print("\n🔒 COMPREHENSIVE ADMIN ENDPOINTS TESTING")
        print("=" * 70)
        
        if "admin" not in self.tokens:
            self.log_result(
                "Admin Endpoints - No Token",
                False,
                "❌ No admin token available"
            )
            return False
        
        admin_token = self.tokens["admin"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Comprehensive admin endpoints test
        admin_endpoints = [
            {
                "endpoint": "/admin/users",
                "method": "GET",
                "description": "User Management - List All Users",
                "expected_data": "users list"
            },
            {
                "endpoint": "/admin/config",
                "method": "GET", 
                "description": "Config System - Get Configuration",
                "expected_data": "config data"
            },
            {
                "endpoint": "/admin/config/commission",
                "method": "GET",
                "description": "Config System - Commission Settings", 
                "expected_data": "commission rates"
            },
            {
                "endpoint": "/admin/couriers/kyc",
                "method": "GET",
                "description": "KYC Management - Courier Approvals",
                "expected_data": "kyc list"
            },
            {
                "endpoint": "/admin/orders",
                "method": "GET",
                "description": "Order Management - All Orders",
                "expected_data": "orders list"
            },
            {
                "endpoint": "/admin/products",
                "method": "GET", 
                "description": "Product Management - All Products",
                "expected_data": "products list"
            }
        ]
        
        success_count = 0
        
        for endpoint_config in admin_endpoints:
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{API_BASE}{endpoint_config['endpoint']}", 
                    headers=headers, 
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    data_size = len(str(data))
                    
                    self.log_result(
                        f"Admin - {endpoint_config['description']}",
                        True,
                        f"✅ {endpoint_config['endpoint']} accessible. Data size: {data_size} chars",
                        response_time
                    )
                    success_count += 1
                    
                elif response.status_code == 401:
                    self.log_result(
                        f"Admin - {endpoint_config['description']}",
                        False,
                        f"❌ 401 Unauthorized - Admin token rejected",
                        response_time
                    )
                elif response.status_code == 403:
                    self.log_result(
                        f"Admin - {endpoint_config['description']}",
                        False,
                        f"❌ 403 Forbidden - Admin role not recognized",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Admin - {endpoint_config['description']}",
                        False,
                        f"❌ HTTP {response.status_code}: {response.text[:200]}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"Admin - {endpoint_config['description']}",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == len(admin_endpoints)
    
    def test_role_based_access_control(self):
        """Test that non-admin users cannot access admin endpoints"""
        print("\n🛡️ ROLE-BASED ACCESS CONTROL TESTING")
        print("=" * 70)
        
        # Test that customer, business, courier cannot access admin endpoints
        non_admin_roles = ["customer", "business", "courier"]
        admin_endpoint = "/admin/users"
        
        success_count = 0
        
        for role in non_admin_roles:
            if role not in self.tokens:
                self.log_result(
                    f"RBAC - {role.title()} Access Denied",
                    False,
                    f"❌ No {role} token available for testing"
                )
                continue
            
            headers = {"Authorization": f"Bearer {self.tokens[role]}"}
            
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{API_BASE}{admin_endpoint}",
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 403:
                    self.log_result(
                        f"RBAC - {role.title()} Access Denied",
                        True,
                        f"✅ {role.title()} correctly denied admin access (403 Forbidden)",
                        response_time
                    )
                    success_count += 1
                elif response.status_code == 401:
                    self.log_result(
                        f"RBAC - {role.title()} Access Denied",
                        True,
                        f"✅ {role.title()} correctly denied admin access (401 Unauthorized)",
                        response_time
                    )
                    success_count += 1
                elif response.status_code == 200:
                    self.log_result(
                        f"RBAC - {role.title()} Access Denied",
                        False,
                        f"❌ SECURITY ISSUE: {role.title()} can access admin endpoints!",
                        response_time
                    )
                else:
                    self.log_result(
                        f"RBAC - {role.title()} Access Denied",
                        False,
                        f"❌ Unexpected response {response.status_code}: {response.text[:100]}",
                        response_time
                    )
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(
                    f"RBAC - {role.title()} Access Denied",
                    False,
                    f"❌ Request failed: {str(e)}",
                    response_time
                )
        
        return success_count == len(non_admin_roles)
    
    def test_token_refresh_flow(self):
        """Test JWT token refresh functionality"""
        print("\n🔄 TOKEN REFRESH TESTING")
        print("=" * 70)
        
        # Test with admin token refresh
        admin_credentials = {
            "email": "admin@kuryecini.com",
            "password": "KuryeciniAdmin2024!"
        }
        
        start_time = time.time()
        try:
            # Get fresh tokens
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=admin_credentials,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if "refresh_token" in data:
                    refresh_token = data["refresh_token"]
                    
                    # Test refresh token endpoint
                    start_time = time.time()
                    refresh_response = self.session.post(
                        f"{API_BASE}/auth/refresh",
                        json={"refresh_token": refresh_token},
                        timeout=10
                    )
                    refresh_time = time.time() - start_time
                    
                    if refresh_response.status_code == 200:
                        refresh_data = refresh_response.json()
                        
                        if "access_token" in refresh_data:
                            self.log_result(
                                "Token Refresh - Admin",
                                True,
                                f"✅ Token refresh successful. New token generated.",
                                refresh_time
                            )
                            return True
                        else:
                            self.log_result(
                                "Token Refresh - Admin",
                                False,
                                f"❌ No access_token in refresh response: {refresh_data}",
                                refresh_time
                            )
                    else:
                        self.log_result(
                            "Token Refresh - Admin",
                            False,
                            f"❌ Refresh failed HTTP {refresh_response.status_code}: {refresh_response.text}",
                            refresh_time
                        )
                else:
                    self.log_result(
                        "Token Refresh - Admin",
                        False,
                        f"❌ No refresh_token in login response",
                        response_time
                    )
            else:
                self.log_result(
                    "Token Refresh - Admin",
                    False,
                    f"❌ Login failed for refresh test: HTTP {response.status_code}",
                    response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(
                "Token Refresh - Admin",
                False,
                f"❌ Request failed: {str(e)}",
                response_time
            )
        
        return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🎯 COMPREHENSIVE ADMIN & USER MANAGEMENT TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Test 1: All authentication flows
        auth_success = self.test_all_authentication_flows()
        
        # Test 2: Admin endpoints comprehensive
        admin_endpoints_success = self.test_admin_endpoints_comprehensive()
        
        # Test 3: Role-based access control
        rbac_success = self.test_role_based_access_control()
        
        # Test 4: Token refresh flow
        refresh_success = self.test_token_refresh_flow()
        
        # Summary
        total_time = time.time() - self.start_time
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TESTING SUMMARY")
        print("=" * 80)
        print(f"✅ Successful Tests: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"🔐 Authentication: {'✅ WORKING' if auth_success else '❌ FAILED'}")
        print(f"🔒 Admin Endpoints: {'✅ WORKING' if admin_endpoints_success else '❌ FAILED'}")
        print(f"🛡️  Access Control: {'✅ WORKING' if rbac_success else '❌ FAILED'}")
        print(f"🔄 Token Refresh: {'✅ WORKING' if refresh_success else '❌ FAILED'}")
        
        # Critical findings
        critical_issues = []
        if not auth_success:
            critical_issues.append("Authentication flows failing")
        if not admin_endpoints_success:
            critical_issues.append("Admin endpoints not accessible")
        if not rbac_success:
            critical_issues.append("Role-based access control issues")
        if not refresh_success:
            critical_issues.append("Token refresh not working")
        
        if critical_issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"   • {issue}")
        else:
            print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        
        print("=" * 80)
        
        return {
            "success_rate": success_rate,
            "auth_working": auth_success,
            "admin_endpoints_working": admin_endpoints_success,
            "rbac_working": rbac_success,
            "refresh_working": refresh_success,
            "critical_issues": critical_issues,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "total_time": total_time
        }

if __name__ == "__main__":
    tester = ComprehensiveAdminTest()
    results = tester.run_all_tests()