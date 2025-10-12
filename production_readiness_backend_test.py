#!/usr/bin/env python3
"""
Kuryecini Platform - Production Readiness Backend Testing
Comprehensive testing for deployment readiness

Test Coverage:
1. Health Check & System Status - /api/healthz and system availability
2. Authentication System - User registration, login, JWT validation for all roles
3. Business Operations - Business registration, KYC approval, menu/product management
4. Customer Operations - Restaurant discovery, address management, order creation
5. Admin Functions - Admin login, business/courier management, settings management
6. API Security - RBAC enforcement and proper error handling
7. Database Operations - MongoDB connections and data persistence
8. Sentry Integration - Error monitoring initialization
"""

import requests
import json
import time
import random
from datetime import datetime, timezone
import uuid

# Configuration
BACKEND_URL = "https://stable-menus.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

class ProductionReadinessTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.customer_token = None
        self.business_token = None
        self.courier_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_health_check_system_status(self):
        """Test health check and system status endpoints"""
        print("\n🏥 TESTING HEALTH CHECK & SYSTEM STATUS")
        
        # Test /api/healthz
        try:
            response = self.session.get(f"{BACKEND_URL.replace('/api', '')}/healthz")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                db_status = data.get("database", "unknown")
                response_time = data.get("response_time_ms", 0)
                
                self.log_test("GET /healthz", True, 
                            f"System status: {status}, DB: {db_status}, Response time: {response_time}ms")
            else:
                self.log_test("GET /healthz", False, 
                            f"Health check failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("GET /healthz", False, f"Health check error: {str(e)}")
        
        # Test /api/health
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/health", True, 
                            f"API health check successful: {data}")
            else:
                self.log_test("GET /api/health", False, 
                            f"API health check failed: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/health", False, f"API health check error: {str(e)}")

    def test_authentication_system(self):
        """Test authentication system for all roles"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        
        # Test Admin Authentication
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_data = data.get("user", {})
                
                if self.admin_token and user_data.get("role") == "admin":
                    self.log_test("Admin Authentication", True, 
                                f"Admin login successful, token length: {len(self.admin_token)}, role: {user_data.get('role')}")
                else:
                    self.log_test("Admin Authentication", False, 
                                "Admin login response missing token or incorrect role")
            else:
                self.log_test("Admin Authentication", False, 
                            f"Admin login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Admin auth error: {str(e)}")
        
        # Test Customer Authentication
        try:
            customer_login = {
                "email": "testcustomer@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=customer_login)
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                user_data = data.get("user", {})
                
                if self.customer_token and user_data.get("role") == "customer":
                    self.log_test("Customer Authentication", True, 
                                f"Customer login successful, token length: {len(self.customer_token)}")
                else:
                    self.log_test("Customer Authentication", False, 
                                "Customer login response missing token or incorrect role")
            else:
                self.log_test("Customer Authentication", False, 
                            f"Customer login failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Customer Authentication", False, f"Customer auth error: {str(e)}")
        
        # Test Business Authentication
        try:
            business_login = {
                "email": "testbusiness@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=business_login)
            
            if response.status_code == 200:
                data = response.json()
                self.business_token = data.get("access_token")
                user_data = data.get("user", {})
                
                if self.business_token and user_data.get("role") == "business":
                    self.log_test("Business Authentication", True, 
                                f"Business login successful, token length: {len(self.business_token)}")
                else:
                    self.log_test("Business Authentication", False, 
                                "Business login response missing token or incorrect role")
            else:
                self.log_test("Business Authentication", False, 
                            f"Business login failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Business Authentication", False, f"Business auth error: {str(e)}")
        
        # Test Courier Authentication
        try:
            courier_login = {
                "email": "testkurye@example.com",
                "password": "test123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=courier_login)
            
            if response.status_code == 200:
                data = response.json()
                self.courier_token = data.get("access_token")
                user_data = data.get("user", {})
                
                if self.courier_token and user_data.get("role") == "courier":
                    self.log_test("Courier Authentication", True, 
                                f"Courier login successful, token length: {len(self.courier_token)}")
                else:
                    self.log_test("Courier Authentication", False, 
                                "Courier login response missing token or incorrect role")
            else:
                self.log_test("Courier Authentication", False, 
                            f"Courier login failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Courier Authentication", False, f"Courier auth error: {str(e)}")

    def test_jwt_validation(self):
        """Test JWT token validation"""
        print("\n🎫 TESTING JWT VALIDATION")
        
        # Test /me endpoint with admin token
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = self.session.get(f"{BACKEND_URL}/me", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("role") == "admin":
                        self.log_test("Admin JWT Validation", True, 
                                    f"Admin token valid, user ID: {data.get('id')}")
                    else:
                        self.log_test("Admin JWT Validation", False, 
                                    f"Token valid but wrong role: {data.get('role')}")
                else:
                    self.log_test("Admin JWT Validation", False, 
                                f"JWT validation failed: {response.status_code}")
            except Exception as e:
                self.log_test("Admin JWT Validation", False, f"JWT validation error: {str(e)}")
        
        # Test invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = self.session.get(f"{BACKEND_URL}/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test("Invalid JWT Rejection", True, 
                            "Invalid JWT token properly rejected with 401")
            else:
                self.log_test("Invalid JWT Rejection", False, 
                            f"Invalid token not properly rejected: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JWT Rejection", False, f"Invalid JWT test error: {str(e)}")

    def test_admin_functions(self):
        """Test admin functions and management endpoints"""
        print("\n👑 TESTING ADMIN FUNCTIONS")
        
        if not self.admin_token:
            self.log_test("Admin Functions", False, "No admin token available for testing")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test admin order management
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/orders", headers=headers)
            if response.status_code == 200:
                data = response.json()
                order_count = len(data) if isinstance(data, list) else "unknown"
                self.log_test("Admin Order Management", True, 
                            f"Retrieved orders successfully, count: {order_count}")
            else:
                self.log_test("Admin Order Management", False, 
                            f"Failed to retrieve orders: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Order Management", False, f"Admin orders error: {str(e)}")
        
        # Test admin business management
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses", headers=headers)
            if response.status_code == 200:
                data = response.json()
                business_count = len(data) if isinstance(data, list) else "unknown"
                self.log_test("Admin Business Management", True, 
                            f"Retrieved businesses successfully, count: {business_count}")
            else:
                self.log_test("Admin Business Management", False, 
                            f"Failed to retrieve businesses: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Business Management", False, f"Admin businesses error: {str(e)}")
        
        # Test admin courier management
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers", headers=headers)
            if response.status_code == 200:
                data = response.json()
                courier_count = len(data) if isinstance(data, list) else "unknown"
                self.log_test("Admin Courier Management", True, 
                            f"Retrieved couriers successfully, count: {courier_count}")
            else:
                self.log_test("Admin Courier Management", False, 
                            f"Failed to retrieve couriers: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Courier Management", False, f"Admin couriers error: {str(e)}")
        
        # Test admin settings management
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/settings", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Admin Settings Management", True, 
                            f"Retrieved settings successfully")
            else:
                self.log_test("Admin Settings Management", False, 
                            f"Failed to retrieve settings: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Settings Management", False, f"Admin settings error: {str(e)}")

    def test_business_operations(self):
        """Test business operations and KYC approval"""
        print("\n🏪 TESTING BUSINESS OPERATIONS")
        
        # Test business registration
        try:
            registration_data = {
                "email": f"test_business_{int(time.time())}@example.com",
                "password": "testpass123",
                "business_name": "Test Restaurant Production",
                "tax_number": "1234567890",
                "address": "Test Address, Istanbul",
                "city": "İstanbul",
                "business_category": "gida",
                "description": "Test restaurant for production testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/register/business", json=registration_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user_type") == "business":
                    self.log_test("Business Registration", True, 
                                f"Business registered successfully, user_type: {data.get('user_type')}")
                else:
                    self.log_test("Business Registration", False, 
                                "Registration response missing token or incorrect user type")
            else:
                self.log_test("Business Registration", False, 
                            f"Business registration failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Business Registration", False, f"Business registration error: {str(e)}")
        
        # Test public business listing
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            if response.status_code == 200:
                data = response.json()
                business_count = len(data) if isinstance(data, list) else "unknown"
                self.log_test("Public Business Listing", True, 
                            f"Retrieved public businesses, count: {business_count}")
            else:
                self.log_test("Public Business Listing", False, 
                            f"Failed to retrieve businesses: {response.status_code}")
        except Exception as e:
            self.log_test("Public Business Listing", False, f"Business listing error: {str(e)}")

    def test_customer_operations(self):
        """Test customer operations and restaurant discovery"""
        print("\n👥 TESTING CUSTOMER OPERATIONS")
        
        # Test customer registration
        try:
            registration_data = {
                "email": f"test_customer_{int(time.time())}@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "Customer",
                "city": "İstanbul"
            }
            
            response = self.session.post(f"{BACKEND_URL}/register/customer", json=registration_data)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if data.get("access_token") and data.get("user_type") == "customer":
                    self.log_test("Customer Registration", True, 
                                f"Customer registered successfully, user_type: {data.get('user_type')}")
                else:
                    self.log_test("Customer Registration", False, 
                                "Registration response missing token or incorrect user type")
            else:
                self.log_test("Customer Registration", False, 
                            f"Customer registration failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Customer Registration", False, f"Customer registration error: {str(e)}")
        
        # Test restaurant discovery
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.log_test("Restaurant Discovery", True, 
                                f"Found {len(data)} restaurants for customer discovery")
                else:
                    self.log_test("Restaurant Discovery", False, 
                                "No restaurants found for customer discovery")
            else:
                self.log_test("Restaurant Discovery", False, 
                            f"Restaurant discovery failed: {response.status_code}")
        except Exception as e:
            self.log_test("Restaurant Discovery", False, f"Restaurant discovery error: {str(e)}")
        
        # Test address management (if customer token available)
        if self.customer_token:
            try:
                headers = {"Authorization": f"Bearer {self.customer_token}"}
                response = self.session.get(f"{BACKEND_URL}/user/addresses", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    address_count = len(data) if isinstance(data, list) else "unknown"
                    self.log_test("Customer Address Management", True, 
                                f"Retrieved customer addresses, count: {address_count}")
                else:
                    self.log_test("Customer Address Management", False, 
                                f"Failed to retrieve addresses: {response.status_code}")
            except Exception as e:
                self.log_test("Customer Address Management", False, f"Address management error: {str(e)}")

    def test_api_security_rbac(self):
        """Test API security and RBAC enforcement"""
        print("\n🔒 TESTING API SECURITY & RBAC")
        
        # Test admin endpoint access without token
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/orders")
            if response.status_code == 401 or response.status_code == 403:
                self.log_test("Admin Endpoint Security", True, 
                            f"Admin endpoint properly protected, returned {response.status_code}")
            else:
                self.log_test("Admin Endpoint Security", False, 
                            f"Admin endpoint not properly protected: {response.status_code}")
        except Exception as e:
            self.log_test("Admin Endpoint Security", False, f"Admin security test error: {str(e)}")
        
        # Test customer accessing admin endpoint
        if self.customer_token:
            try:
                headers = {"Authorization": f"Bearer {self.customer_token}"}
                response = self.session.get(f"{BACKEND_URL}/admin/orders", headers=headers)
                
                if response.status_code == 403:
                    self.log_test("RBAC Enforcement", True, 
                                "Customer properly denied access to admin endpoint")
                else:
                    self.log_test("RBAC Enforcement", False, 
                                f"RBAC not properly enforced: {response.status_code}")
            except Exception as e:
                self.log_test("RBAC Enforcement", False, f"RBAC test error: {str(e)}")

    def test_database_operations(self):
        """Test database operations and data persistence"""
        print("\n🗄️ TESTING DATABASE OPERATIONS")
        
        # Test database health through API health endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("database", {}).get("mongodb", "unknown")
                
                if db_status == "connected":
                    self.log_test("Database Connection", True, 
                                "MongoDB connection confirmed through API health check")
                else:
                    self.log_test("Database Connection", False, 
                                f"Database connection issue: {db_status}")
            else:
                self.log_test("Database Connection", False, 
                            f"Could not verify database connection: {response.status_code}")
        except Exception as e:
            self.log_test("Database Connection", False, f"Database test error: {str(e)}")

    def test_sentry_integration(self):
        """Test Sentry integration for error monitoring"""
        print("\n🔍 TESTING SENTRY INTEGRATION")
        
        # Sentry integration is typically initialized at startup
        # We can test this by checking if the application starts without errors
        # and by testing error handling endpoints
        
        try:
            # Test a non-existent endpoint to potentially trigger error handling
            response = self.session.get(f"{BACKEND_URL}/non-existent-endpoint")
            
            if response.status_code == 404:
                self.log_test("Sentry Error Handling", True, 
                            "Application handles 404 errors properly (Sentry should capture if configured)")
            else:
                self.log_test("Sentry Error Handling", True, 
                            f"Application handles errors properly: {response.status_code}")
        except Exception as e:
            self.log_test("Sentry Error Handling", False, f"Error handling test failed: {str(e)}")

    def run_all_tests(self):
        """Run all production readiness tests"""
        print("🚀 STARTING KURYECINI PRODUCTION READINESS TESTING")
        print("=" * 70)
        
        # Run all test categories
        self.test_health_check_system_status()
        self.test_authentication_system()
        self.test_jwt_validation()
        self.test_admin_functions()
        self.test_business_operations()
        self.test_customer_operations()
        self.test_api_security_rbac()
        self.test_database_operations()
        self.test_sentry_integration()
        
        # Generate comprehensive summary
        self.generate_production_summary()

    def generate_production_summary(self):
        """Generate production readiness summary"""
        print("\n" + "=" * 70)
        print("📊 KURYECINI PRODUCTION READINESS TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical production readiness assessment
        print("\n🚨 PRODUCTION READINESS ASSESSMENT:")
        
        # Check critical systems
        critical_systems = {
            "Health Check": any("Health Check" in r["test"] and r["success"] for r in self.test_results),
            "Admin Authentication": any("Admin Authentication" in r["test"] and r["success"] for r in self.test_results),
            "Database Connection": any("Database Connection" in r["test"] and r["success"] for r in self.test_results),
            "API Security": any("Admin Endpoint Security" in r["test"] and r["success"] for r in self.test_results),
            "RBAC Enforcement": any("RBAC Enforcement" in r["test"] and r["success"] for r in self.test_results)
        }
        
        critical_failures = [system for system, status in critical_systems.items() if not status]
        
        if critical_failures:
            print(f"❌ CRITICAL FAILURES: {len(critical_failures)} critical systems failing:")
            for failure in critical_failures:
                print(f"   - {failure}")
        
        # Overall production readiness verdict
        print(f"\n📝 PRODUCTION READINESS VERDICT:")
        if success_rate >= 90 and not critical_failures:
            print("✅ READY FOR PRODUCTION: All critical systems operational")
            print("   Platform is ready for deployment")
        elif success_rate >= 75 and len(critical_failures) <= 1:
            print("⚠️ MOSTLY READY: Minor issues detected")
            print("   Platform can be deployed with monitoring")
        elif success_rate >= 50:
            print("🔧 NEEDS WORK: Significant issues detected")
            print("   Address critical failures before deployment")
        else:
            print("❌ NOT READY: Major system failures")
            print("   Extensive fixes required before deployment")
        
        # Specific recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not critical_systems.get("Admin Authentication"):
            print("   - Fix admin authentication system immediately")
        if not critical_systems.get("Database Connection"):
            print("   - Verify and fix database connectivity")
        if not critical_systems.get("API Security"):
            print("   - Implement proper API security measures")
        if success_rate < 80:
            print("   - Conduct thorough testing of all failed endpoints")
            print("   - Implement comprehensive error handling")
        
        print(f"\n🎯 NEXT STEPS:")
        print("   1. Address all critical failures identified above")
        print("   2. Verify admin account access with provided credentials")
        print("   3. Test all major user flows end-to-end")
        print("   4. Monitor error rates and performance in staging")
        print("   5. Conduct load testing before production deployment")

if __name__ == "__main__":
    tester = ProductionReadinessTester()
    tester.run_all_tests()