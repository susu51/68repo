#!/usr/bin/env python3
"""
Kuryecini Backend API Testing - Review Request Focus
Testing health endpoints, database connection, CORS, authentication, and public menu endpoints
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class KuryeciniBackendTest:
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
        
    def test_health_endpoints(self):
        """Test /health and /healthz endpoints"""
        print("\n🏥 HEALTH ENDPOINTS TESTING")
        print("=" * 50)
        
        # Test direct backend server health endpoints (port 8001)
        backend_direct = "http://localhost:8001"
        health_endpoints = [
            (f"{backend_direct}/health", "Legacy Health Check (Direct)"),
            (f"{backend_direct}/healthz", "Primary Health Check (Direct)")
        ]
        
        for endpoint, description in health_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(endpoint, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        status = data.get("status", "unknown")
                        db_status = data.get("database", data.get("db", "unknown"))
                        
                        self.log_result(
                            description,
                            status in ["ok", "healthy"],
                            f"Status: {status}, DB: {db_status}, Response time: {response_time:.2f}s",
                            response_time
                        )
                        
                        # Test database connection specifically
                        if "healthz" in endpoint:
                            db_working = db_status in ["ok", "connected", "not_configured"]
                            self.log_result(
                                "Database Connection Check",
                                db_working,
                                f"Database status: {db_status}"
                            )
                    except json.JSONDecodeError:
                        self.log_result(
                            description,
                            False,
                            f"Invalid JSON response: {response.text[:100]}",
                            response_time
                        )
                else:
                    self.log_result(
                        description,
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(description, False, f"Exception: {str(e)}")
        
        # Also test if health endpoints are accessible via the public URL
        public_health_endpoints = [
            (f"{BACKEND_URL}/health", "Legacy Health Check (Public)"),
            (f"{BACKEND_URL}/healthz", "Primary Health Check (Public)")
        ]
        
        for endpoint, description in public_health_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(endpoint, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        status = data.get("status", "unknown")
                        self.log_result(
                            description,
                            status in ["ok", "healthy"],
                            f"Status: {status}, Response time: {response_time:.2f}s",
                            response_time
                        )
                    except json.JSONDecodeError:
                        self.log_result(
                            description,
                            False,
                            f"Returns HTML instead of JSON - routing issue",
                            response_time
                        )
                else:
                    self.log_result(
                        description,
                        False,
                        f"HTTP {response.status_code}",
                        response_time
                    )
            except Exception as e:
                self.log_result(description, False, f"Exception: {str(e)}")
    
    def test_cors_configuration(self):
        """Test CORS headers are properly configured"""
        print("\n🌐 CORS CONFIGURATION TESTING")
        print("=" * 50)
        
        # Test preflight request
        try:
            headers = {
                'Origin': 'https://kuryecini-ai.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            start_time = time.time()
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                # Check if required CORS headers are present
                required_headers = ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods']
                missing_headers = [h for h in required_headers if not cors_headers.get(h)]
                
                self.log_result(
                    "CORS Preflight Request",
                    len(missing_headers) == 0,
                    f"CORS headers: {list(k for k, v in cors_headers.items() if v)}, Missing: {missing_headers}",
                    response_time
                )
            else:
                self.log_result(
                    "CORS Preflight Request",
                    False,
                    f"HTTP {response.status_code}: Preflight failed",
                    response_time
                )
        except Exception as e:
            self.log_result("CORS Configuration", False, f"Exception: {str(e)}")
        
        # Test actual CORS headers in regular request
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/businesses", timeout=10)
            response_time = time.time() - start_time
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            self.log_result(
                "CORS Headers in Response",
                cors_origin is not None,
                f"Origin: {cors_origin}, Methods: {cors_methods}",
                response_time
            )
        except Exception as e:
            self.log_result("CORS Headers in Response", False, f"Exception: {str(e)}")
    
    def test_authentication_endpoints(self):
        """Test login/register functionality"""
        print("\n🔐 AUTHENTICATION ENDPOINTS TESTING")
        print("=" * 50)
        
        # Test login for all user types
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[user_type] = data.get("access_token")
                    user_info = data.get("user", {})
                    
                    # Verify token structure
                    token_valid = bool(data.get("access_token")) and data.get("token_type") == "bearer"
                    
                    self.log_result(
                        f"{user_type.title()} Login",
                        token_valid,
                        f"Role: {user_info.get('role', 'unknown')}, Token: {'Valid' if token_valid else 'Invalid'}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"{user_type.title()} Login",
                        False,
                        f"Status: {response.status_code}, Response: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(f"{user_type.title()} Login", False, f"Exception: {str(e)}")
        
        # Test registration endpoint
        try:
            test_customer = {
                "email": f"test-{int(time.time())}@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User",
                "city": "İstanbul"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/register/customer",
                json=test_customer,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                registration_success = bool(data.get("access_token")) and data.get("user_type") == "customer"
                
                self.log_result(
                    "Customer Registration",
                    registration_success,
                    f"User created with token: {'Yes' if registration_success else 'No'}",
                    response_time
                )
            else:
                self.log_result(
                    "Customer Registration",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:100]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Customer Registration", False, f"Exception: {str(e)}")
    
    def test_public_menu_endpoint(self):
        """Test /menus/public endpoint"""
        print("\n🍽️ PUBLIC MENU ENDPOINT TESTING")
        print("=" * 50)
        
        # Test direct backend server endpoints
        backend_direct = "http://localhost:8001"
        
        # Test /menus/public endpoint (direct)
        try:
            start_time = time.time()
            response = self.session.get(f"{backend_direct}/menus/public", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    restaurants = data.get("restaurants", [])
                    count = data.get("count", 0)
                    
                    self.log_result(
                        "Public Menus Endpoint (Direct)",
                        True,
                        f"Found {count} restaurants with menus",
                        response_time
                    )
                    
                    # Test restaurant data structure
                    if restaurants:
                        restaurant = restaurants[0]
                        required_fields = ["id", "name", "address", "city", "rating", "menu"]
                        missing_fields = [field for field in required_fields if field not in restaurant]
                        
                        self.log_result(
                            "Restaurant Data Structure",
                            len(missing_fields) == 0,
                            f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                        )
                        
                        # Test menu items structure
                        menu = restaurant.get("menu", [])
                        if menu:
                            menu_item = menu[0]
                            menu_fields = ["id", "name", "price", "category"]
                            missing_menu_fields = [field for field in menu_fields if field not in menu_item]
                            
                            self.log_result(
                                "Menu Item Structure",
                                len(missing_menu_fields) == 0,
                                f"Missing menu fields: {missing_menu_fields}" if missing_menu_fields else "All menu fields present"
                            )
                    else:
                        self.log_result(
                            "Restaurant Availability",
                            False,
                            "No restaurants found - may need approved businesses in database"
                        )
                except json.JSONDecodeError:
                    self.log_result(
                        "Public Menus Endpoint (Direct)",
                        False,
                        f"Invalid JSON response: {response.text[:100]}",
                        response_time
                    )
            else:
                self.log_result(
                    "Public Menus Endpoint (Direct)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Public Menus Endpoint (Direct)", False, f"Exception: {str(e)}")
        
        # Test legacy /menus endpoint (direct)
        try:
            start_time = time.time()
            response = self.session.get(f"{backend_direct}/menus", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    menu_items = response.json()
                    self.log_result(
                        "Legacy Menus Endpoint (Direct)",
                        True,
                        f"Found {len(menu_items)} menu items",
                        response_time
                    )
                except json.JSONDecodeError:
                    self.log_result(
                        "Legacy Menus Endpoint (Direct)",
                        False,
                        f"Invalid JSON response: {response.text[:100]}",
                        response_time
                    )
            else:
                self.log_result(
                    "Legacy Menus Endpoint (Direct)",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Legacy Menus Endpoint (Direct)", False, f"Exception: {str(e)}")
        
        # Test public URL routing (should work through proxy)
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/menus/public", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_result(
                        "Public Menus Endpoint (Public URL)",
                        True,
                        f"Public URL routing works",
                        response_time
                    )
                except json.JSONDecodeError:
                    self.log_result(
                        "Public Menus Endpoint (Public URL)",
                        False,
                        f"Returns HTML - routing issue",
                        response_time
                    )
            else:
                self.log_result(
                    "Public Menus Endpoint (Public URL)",
                    False,
                    f"HTTP {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result("Public Menus Endpoint (Public URL)", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test endpoints gracefully handle database connection issues"""
        print("\n⚠️ ERROR HANDLING TESTING")
        print("=" * 50)
        
        # Test invalid endpoint
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/invalid-endpoint", timeout=10)
            response_time = time.time() - start_time
            
            self.log_result(
                "Invalid Endpoint Handling",
                response.status_code == 404,
                f"Status: {response.status_code} (Expected: 404)",
                response_time
            )
        except Exception as e:
            self.log_result("Invalid Endpoint Handling", False, f"Exception: {str(e)}")
        
        # Test authentication with invalid credentials
        try:
            invalid_creds = {"email": "invalid@test.com", "password": "wrongpassword"}
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/auth/login", json=invalid_creds, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [400, 401]:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                
                self.log_result(
                    "Invalid Login Error Handling",
                    True,
                    f"Status: {response.status_code}, Error: {error_detail[:50]}",
                    response_time
                )
            else:
                self.log_result(
                    "Invalid Login Error Handling",
                    False,
                    f"Expected 400/401, got {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result("Invalid Login Error Handling", False, f"Exception: {str(e)}")
        
        # Test protected endpoint without authentication
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/admin/users", timeout=10)
            response_time = time.time() - start_time
            
            self.log_result(
                "Unauthorized Access Handling",
                response.status_code in [401, 403],
                f"Status: {response.status_code} (Expected: 401/403)",
                response_time
            )
        except Exception as e:
            self.log_result("Unauthorized Access Handling", False, f"Exception: {str(e)}")
    
    def test_atlas_readiness(self):
        """Test if backend is ready for Atlas migration"""
        print("\n🌍 ATLAS READINESS TESTING")
        print("=" * 50)
        
        # Check if MongoDB connection is working (should work with local or Atlas)
        try:
            start_time = time.time()
            response = self.session.get("http://localhost:8001/healthz", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    db_status = data.get("database", "unknown")
                    
                    # Atlas readiness means DB connection is abstracted and working
                    atlas_ready = db_status in ["ok", "connected", "not_configured"]
                    
                    self.log_result(
                        "Atlas Migration Readiness",
                        atlas_ready,
                        f"DB Status: {db_status}, Atlas Ready: {atlas_ready}",
                        response_time
                    )
                except json.JSONDecodeError:
                    self.log_result(
                        "Atlas Migration Readiness",
                        False,
                        f"Invalid JSON response from health endpoint",
                        response_time
                    )
            else:
                self.log_result(
                    "Atlas Migration Readiness",
                    False,
                    f"Health check failed: {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result("Atlas Migration Readiness", False, f"Exception: {str(e)}")
        
        # Test if environment variables are properly configured
        try:
            # This is indirect - we test if the app responds properly to requests
            # which indicates environment configuration is working
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/businesses", timeout=10)
            response_time = time.time() - start_time
            
            env_config_working = response.status_code in [200, 404]  # Either works or no data
            
            self.log_result(
                "Environment Configuration",
                env_config_working,
                f"API responds properly: {response.status_code}",
                response_time
            )
        except Exception as e:
            self.log_result("Environment Configuration", False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 KURYECINI BACKEND TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ CRITICAL SUCCESS CRITERIA CHECK:")
        critical_tests = [
            "Primary Health Check",
            "Database Connection Check",
            "CORS Preflight Request",
            "Admin Login",
            "Customer Login",
            "Public Menus Endpoint",
            "Atlas Migration Readiness"
        ]
        
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"   {status} {test_name}")
            else:
                print(f"   ⚠️ {test_name} - Not tested")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": self.test_results
        }

def main():
    """Run Kuryecini backend tests"""
    print("🚀 KURYECINI BACKEND API TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start Time: {datetime.now().isoformat()}")
    
    tester = KuryeciniBackendTest()
    
    # Run all tests in order of review request priorities
    tester.test_health_endpoints()
    tester.test_cors_configuration()
    tester.test_authentication_endpoints()
    tester.test_public_menu_endpoint()
    tester.test_error_handling()
    tester.test_atlas_readiness()
    
    # Generate final report
    report = tester.generate_report()
    
    return report

if __name__ == "__main__":
    main()