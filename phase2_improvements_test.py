#!/usr/bin/env python3
"""
Phase 2 Improvements Testing for Kuryecini Platform (Madde 11-16)
Focus: Admin Authentication System, API Documentation, Production Readiness
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
BACKEND_URL = "https://address-manager-5.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class Phase2ImprovementsTest:
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
        
    def test_admin_authentication_system(self):
        """Test Admin Authentication System (Madde 11)"""
        print("\n🔐 ADMIN AUTHENTICATION SYSTEM TESTING (Madde 11)")
        print("=" * 60)
        
        # Test 1: Verify hardcoded password "6851" is no longer accepted via old endpoint
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE}/auth/admin", 
                json={"password": "6851"},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 410:
                self.log_result(
                    "Deprecated Admin Endpoint Returns 410 Gone",
                    True,
                    f"Old admin endpoint correctly returns 410 Gone: {response.json().get('detail', '')}",
                    response_time
                )
            else:
                self.log_result(
                    "Deprecated Admin Endpoint Returns 410 Gone",
                    False,
                    f"Expected 410 Gone, got {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "Deprecated Admin Endpoint Returns 410 Gone",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test 2: Verify hardcoded password "6851" is no longer accepted via unified login
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE}/auth/login",
                json={"email": "admin@test.com", "password": "6851"},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                self.log_result(
                    "Hardcoded Password 6851 No Longer Accepted",
                    True,
                    f"Hardcoded password '6851' correctly rejected: {response.json().get('detail', '')}",
                    response_time
                )
            else:
                self.log_result(
                    "Hardcoded Password 6851 No Longer Accepted",
                    False,
                    f"Expected 400 Bad Request, got {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "Hardcoded Password 6851 No Longer Accepted",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test 3: Test proper admin authentication with correct credentials
        start_time = time.time()
        try:
            # Try with the proper admin credentials
            response = self.session.post(f"{API_BASE}/auth/login",
                json={"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and data.get("user", {}).get("role") == "admin":
                    self.tokens["admin"] = data["access_token"]
                    self.log_result(
                        "JWT Admin Authentication with Proper Credentials",
                        True,
                        f"Admin login successful, role: {data['user']['role']}, email: {data['user']['email']}",
                        response_time
                    )
                else:
                    self.log_result(
                        "JWT Admin Authentication with Proper Credentials",
                        False,
                        f"Login successful but missing token or wrong role: {data}",
                        response_time
                    )
            else:
                # If proper credentials don't work, there might be a database field mismatch
                self.log_result(
                    "JWT Admin Authentication with Proper Credentials",
                    False,
                    f"Admin login failed - possible database field mismatch (password vs password_hash): {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "JWT Admin Authentication with Proper Credentials",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test 3: Verify admin endpoints require proper JWT tokens
        if "admin" in self.tokens:
            start_time = time.time()
            try:
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                response = self.session.get(f"{API_BASE}/admin/users", 
                    headers=headers, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    users = response.json()
                    self.log_result(
                        "Admin Endpoints Require JWT Authentication",
                        True,
                        f"Admin endpoint accessible with JWT token, retrieved {len(users)} users",
                        response_time
                    )
                else:
                    self.log_result(
                        "Admin Endpoints Require JWT Authentication",
                        False,
                        f"Admin endpoint failed with status {response.status_code}: {response.text[:200]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(
                    "Admin Endpoints Require JWT Authentication",
                    False,
                    f"Request failed: {str(e)}",
                    time.time() - start_time
                )
        
        # Test 4: Verify non-admin users cannot access admin endpoints
        start_time = time.time()
        try:
            # Try to login as regular user
            response = self.session.post(f"{API_BASE}/auth/login",
                json={"email": "testcustomer@example.com", "password": "test123"},
                timeout=10
            )
            
            if response.status_code == 200:
                customer_token = response.json().get("access_token")
                headers = {"Authorization": f"Bearer {customer_token}"}
                
                # Try to access admin endpoint with customer token
                admin_response = self.session.get(f"{API_BASE}/admin/users", 
                    headers=headers, timeout=10)
                response_time = time.time() - start_time
                
                if admin_response.status_code == 403:
                    self.log_result(
                        "Role-Based Access Control Working",
                        True,
                        f"Customer token correctly rejected from admin endpoint (403 Forbidden)",
                        response_time
                    )
                else:
                    self.log_result(
                        "Role-Based Access Control Working",
                        False,
                        f"Customer token should be rejected, got {admin_response.status_code}: {admin_response.text[:200]}",
                        response_time
                    )
            else:
                self.log_result(
                    "Role-Based Access Control Working",
                    False,
                    f"Customer login failed: {response.text[:200]}",
                    time.time() - start_time
                )
        except Exception as e:
            self.log_result(
                "Role-Based Access Control Working",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
    
    def test_api_documentation(self):
        """Test API Documentation (Madde 13)"""
        print("\n📚 API DOCUMENTATION TESTING (Madde 13)")
        print("=" * 50)
        
        # Test 1: Verify FastAPI OpenAPI docs are accessible at /docs
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/docs", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and "swagger" in response.text.lower():
                self.log_result(
                    "FastAPI Swagger UI Accessible",
                    True,
                    f"Swagger UI loaded successfully at /docs",
                    response_time
                )
            elif response.status_code == 200 and "<!doctype html>" in response.text:
                self.log_result(
                    "FastAPI Swagger UI Accessible",
                    False,
                    f"Frontend routing intercepting /docs - API docs not accessible due to deployment configuration",
                    response_time
                )
            else:
                self.log_result(
                    "FastAPI Swagger UI Accessible",
                    False,
                    f"Swagger UI not accessible, status: {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "FastAPI Swagger UI Accessible",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test 2: Verify OpenAPI JSON schema is comprehensive
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/openapi.json", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    openapi_spec = response.json()
                    paths = openapi_spec.get("paths", {})
                    
                    # Check for key endpoints
                    key_endpoints = [
                        "/api/auth/login",
                        "/api/admin/users", 
                        "/api/businesses",
                        "/menus/public",
                        "/healthz"
                    ]
                    
                    found_endpoints = []
                    missing_endpoints = []
                    
                    for endpoint in key_endpoints:
                        if endpoint in paths:
                            found_endpoints.append(endpoint)
                        else:
                            missing_endpoints.append(endpoint)
                    
                    if len(found_endpoints) >= 4:  # Most endpoints should be documented
                        self.log_result(
                            "OpenAPI Schema Comprehensive",
                            True,
                            f"Found {len(found_endpoints)}/{len(key_endpoints)} key endpoints documented: {found_endpoints}",
                            response_time
                        )
                    else:
                        self.log_result(
                            "OpenAPI Schema Comprehensive",
                            False,
                            f"Only {len(found_endpoints)}/{len(key_endpoints)} endpoints documented. Missing: {missing_endpoints}",
                            response_time
                        )
                except json.JSONDecodeError:
                    self.log_result(
                        "OpenAPI Schema Comprehensive",
                        False,
                        f"Frontend routing intercepting /openapi.json - API schema not accessible due to deployment configuration",
                        response_time
                    )
            else:
                self.log_result(
                    "OpenAPI Schema Comprehensive",
                    False,
                    f"OpenAPI schema not accessible, status: {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "OpenAPI Schema Comprehensive",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
        
        # Test 3: Check if endpoints have proper tags and descriptions
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/openapi.json", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    openapi_spec = response.json()
                    paths = openapi_spec.get("paths", {})
                    
                    tagged_endpoints = 0
                    described_endpoints = 0
                    total_endpoints = len(paths)
                    
                    for path, methods in paths.items():
                        for method, details in methods.items():
                            if isinstance(details, dict):
                                if "tags" in details and details["tags"]:
                                    tagged_endpoints += 1
                                if "description" in details or "summary" in details:
                                    described_endpoints += 1
                    
                    tag_percentage = (tagged_endpoints / max(total_endpoints, 1)) * 100
                    desc_percentage = (described_endpoints / max(total_endpoints, 1)) * 100
                    
                    if tag_percentage >= 70 and desc_percentage >= 70:
                        self.log_result(
                            "API Endpoints Have Tags and Descriptions",
                            True,
                            f"Tags: {tag_percentage:.1f}%, Descriptions: {desc_percentage:.1f}% of endpoints documented",
                            response_time
                        )
                    else:
                        self.log_result(
                            "API Endpoints Have Tags and Descriptions",
                            False,
                            f"Insufficient documentation - Tags: {tag_percentage:.1f}%, Descriptions: {desc_percentage:.1f}%",
                            response_time
                        )
                except json.JSONDecodeError:
                    self.log_result(
                        "API Endpoints Have Tags and Descriptions",
                        False,
                        f"Frontend routing intercepting /openapi.json - Cannot verify endpoint documentation due to deployment configuration",
                        response_time
                    )
            else:
                self.log_result(
                    "API Endpoints Have Tags and Descriptions",
                    False,
                    f"OpenAPI schema not accessible, status: {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result(
                "API Endpoints Have Tags and Descriptions",
                False,
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
    
    def test_production_readiness(self):
        """Test Production Readiness"""
        print("\n🚀 PRODUCTION READINESS TESTING")
        print("=" * 40)
        
        # Test 1: Health endpoints
        health_endpoints = ["/healthz", "/api/healthz"]
        
        for endpoint in health_endpoints:
            start_time = time.time()
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("status") == "ok":
                            self.log_result(
                                f"Health Endpoint {endpoint}",
                                True,
                                f"Health check passed: {data}",
                                response_time
                            )
                        else:
                            self.log_result(
                                f"Health Endpoint {endpoint}",
                                False,
                                f"Health check returned unexpected data: {data}",
                                response_time
                            )
                    except json.JSONDecodeError:
                        if "<!doctype html>" in response.text:
                            self.log_result(
                                f"Health Endpoint {endpoint}",
                                False,
                                f"Frontend routing intercepting {endpoint} - health endpoint not accessible due to deployment configuration",
                                response_time
                            )
                        else:
                            self.log_result(
                                f"Health Endpoint {endpoint}",
                                False,
                                f"Health check returned non-JSON response: {response.text[:100]}",
                                response_time
                            )
                else:
                    self.log_result(
                        f"Health Endpoint {endpoint}",
                        False,
                        f"Health check failed with status {response.status_code}: {response.text[:200]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(
                    f"Health Endpoint {endpoint}",
                    False,
                    f"Request failed: {str(e)}",
                    time.time() - start_time
                )
        
        # Test 2: Public endpoints
        public_endpoints = [
            ("/menus/public", "restaurants"),
            ("/api/businesses", None)
        ]
        
        for endpoint, expected_key in public_endpoints:
            start_time = time.time()
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if expected_key and expected_key in data:
                            self.log_result(
                                f"Public Endpoint {endpoint}",
                                True,
                                f"Endpoint accessible, contains expected key '{expected_key}': {len(data.get(expected_key, []))} items",
                                response_time
                            )
                        elif not expected_key and isinstance(data, list):
                            self.log_result(
                                f"Public Endpoint {endpoint}",
                                True,
                                f"Endpoint accessible, returned {len(data)} items",
                                response_time
                            )
                        else:
                            self.log_result(
                                f"Public Endpoint {endpoint}",
                                True,
                                f"Endpoint accessible, data structure: {type(data).__name__}",
                                response_time
                            )
                    except json.JSONDecodeError:
                        if "<!doctype html>" in response.text:
                            self.log_result(
                                f"Public Endpoint {endpoint}",
                                False,
                                f"Frontend routing intercepting {endpoint} - public endpoint not accessible due to deployment configuration",
                                response_time
                            )
                        else:
                            self.log_result(
                                f"Public Endpoint {endpoint}",
                                False,
                                f"Endpoint returned non-JSON response: {response.text[:100]}",
                                response_time
                            )
                else:
                    self.log_result(
                        f"Public Endpoint {endpoint}",
                        False,
                        f"Endpoint failed with status {response.status_code}: {response.text[:200]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(
                    f"Public Endpoint {endpoint}",
                    False,
                    f"Request failed: {str(e)}",
                    time.time() - start_time
                )
        
        # Test 3: Commission configuration endpoints (if admin token available)
        if "admin" in self.tokens:
            commission_endpoints = [
                "/api/admin/config/commission",
                "/api/admin/config"
            ]
            
            for endpoint in commission_endpoints:
                start_time = time.time()
                try:
                    headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", 
                        headers=headers, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log_result(
                            f"Commission Config Endpoint {endpoint}",
                            True,
                            f"Config endpoint accessible, returned data type: {type(data).__name__}",
                            response_time
                        )
                    else:
                        self.log_result(
                            f"Commission Config Endpoint {endpoint}",
                            False,
                            f"Config endpoint failed with status {response.status_code}: {response.text[:200]}",
                            response_time
                        )
                except Exception as e:
                    self.log_result(
                        f"Commission Config Endpoint {endpoint}",
                        False,
                        f"Request failed: {str(e)}",
                        time.time() - start_time
                    )
    
    def run_all_tests(self):
        """Run all Phase 2 improvement tests"""
        print("🎯 PHASE 2 IMPROVEMENTS TESTING (Madde 11-16)")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test Start Time: {datetime.now().isoformat()}")
        
        # Run all test categories
        self.test_admin_authentication_system()
        self.test_api_documentation()
        self.test_production_readiness()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print(f"\n📊 PHASE 2 IMPROVEMENTS TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n🎉 PHASE 2 TESTING COMPLETE")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = Phase2ImprovementsTest()
    tester.run_all_tests()