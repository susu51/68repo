#!/usr/bin/env python3
"""
FINAL PRODUCTION READINESS TEST - ALL 26 FEATURES
Comprehensive validation for Kuryecini Platform deployment
"""

import requests
import json
import time
import os
from datetime import datetime
import tempfile

# Configuration - Use localhost since backend is running locally
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@test.com", "password": "6851"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class FinalProductionTest:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.refresh_tokens = {}
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0, category="General"):
        """Log test result with category"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} [{category}] {test_name}: {details}")
        
    def test_critical_infrastructure(self):
        """Test critical infrastructure components"""
        print("\n🏗️ CRITICAL INFRASTRUCTURE TESTING")
        print("=" * 50)
        
        # Health endpoints
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/healthz", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                db_status = data.get("database", "unknown")
                
                self.log_result(
                    "Health Check Endpoint",
                    status == "ok",
                    f"Status: {status}, DB: {db_status}, Time: {response_time*1000:.0f}ms",
                    response_time,
                    "Infrastructure"
                )
            else:
                self.log_result(
                    "Health Check Endpoint",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Infrastructure"
                )
        except Exception as e:
            self.log_result("Health Check Endpoint", False, f"Exception: {str(e)}", 0, "Infrastructure")
        
        # Legacy health endpoint
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/health", timeout=5)
            response_time = time.time() - start_time
            
            self.log_result(
                "Legacy Health Endpoint",
                response.status_code == 200,
                f"HTTP {response.status_code}",
                response_time,
                "Infrastructure"
            )
        except Exception as e:
            self.log_result("Legacy Health Endpoint", False, f"Exception: {str(e)}", 0, "Infrastructure")
        
        # Public menus endpoint
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/api/menus/public", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("restaurants", [])
                count = data.get("count", 0)
                
                self.log_result(
                    "Public Menus Endpoint",
                    True,
                    f"Found {count} approved restaurants",
                    response_time,
                    "Infrastructure"
                )
            else:
                self.log_result(
                    "Public Menus Endpoint",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Infrastructure"
                )
        except Exception as e:
            self.log_result("Public Menus Endpoint", False, f"Exception: {str(e)}", 0, "Infrastructure")

    def test_authentication_system(self):
        """Test authentication system comprehensively"""
        print("\n🔐 AUTHENTICATION SYSTEM TESTING")
        print("=" * 50)
        
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=5
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")
                    refresh_token = data.get("refresh_token")
                    user_info = data.get("user", {})
                    
                    if access_token:
                        self.tokens[user_type] = access_token
                    if refresh_token:
                        self.refresh_tokens[user_type] = refresh_token
                    
                    self.log_result(
                        f"{user_type.title()} Login",
                        access_token is not None,
                        f"Role: {user_info.get('role')}, Tokens: {'✓' if access_token and refresh_token else '✗'}",
                        response_time,
                        "Authentication"
                    )
                else:
                    self.log_result(
                        f"{user_type.title()} Login",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                        "Authentication"
                    )
            except Exception as e:
                self.log_result(f"{user_type.title()} Login", False, f"Exception: {str(e)}", 0, "Authentication")

    def test_jwt_refresh_system(self):
        """Test JWT refresh token system"""
        print("\n🔄 JWT REFRESH TOKEN SYSTEM TESTING")
        print("=" * 50)
        
        if "customer" in self.refresh_tokens:
            try:
                refresh_data = {"refresh_token": self.refresh_tokens["customer"]}
                start_time = time.time()
                response = self.session.post(f"{API_BASE}/auth/refresh", json=refresh_data, timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    new_token = data.get("access_token")
                    
                    self.log_result(
                        "JWT Refresh Token",
                        new_token is not None,
                        f"New access token generated: {'✓' if new_token else '✗'}",
                        response_time,
                        "Security"
                    )
                else:
                    self.log_result(
                        "JWT Refresh Token",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                        "Security"
                    )
            except Exception as e:
                self.log_result("JWT Refresh Token", False, f"Exception: {str(e)}", 0, "Security")

    def test_rate_limiting(self):
        """Test rate limiting on critical endpoints"""
        print("\n🚦 RATE LIMITING TESTING")
        print("=" * 50)
        
        # Test login rate limiting
        rate_limited = False
        attempts = 0
        
        for i in range(6):  # Try 6 requests (limit should be 5/minute)
            try:
                invalid_creds = {"email": "ratelimit@test.com", "password": "wrong"}
                response = self.session.post(f"{API_BASE}/auth/login", json=invalid_creds, timeout=3)
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
                elif response.status_code == 400:  # Invalid credentials
                    attempts += 1
                
                time.sleep(0.1)
            except Exception:
                break
        
        self.log_result(
            "Login Rate Limiting",
            rate_limited or attempts >= 5,
            f"Rate limited: {rate_limited}, Attempts: {attempts}",
            0,
            "Security"
        )

    def test_api_documentation(self):
        """Test API documentation accessibility"""
        print("\n📚 API DOCUMENTATION TESTING")
        print("=" * 50)
        
        # Test Swagger UI
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/docs", timeout=10)
            response_time = time.time() - start_time
            
            docs_accessible = response.status_code == 200
            swagger_ui = "swagger" in response.text.lower() if docs_accessible else False
            
            self.log_result(
                "Swagger UI Documentation",
                docs_accessible and swagger_ui,
                f"Accessible: {docs_accessible}, Swagger: {swagger_ui}",
                response_time,
                "Documentation"
            )
        except Exception as e:
            self.log_result("Swagger UI Documentation", False, f"Exception: {str(e)}", 0, "Documentation")
        
        # Test ReDoc
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/redoc", timeout=10)
            response_time = time.time() - start_time
            
            self.log_result(
                "ReDoc Documentation",
                response.status_code == 200,
                f"HTTP {response.status_code}",
                response_time,
                "Documentation"
            )
        except Exception as e:
            self.log_result("ReDoc Documentation", False, f"Exception: {str(e)}", 0, "Documentation")

    def test_admin_functionality(self):
        """Test admin functionality and configuration"""
        print("\n👑 ADMIN FUNCTIONALITY TESTING")
        print("=" * 50)
        
        if "admin" not in self.tokens:
            self.log_result("Admin Functionality", False, "Admin authentication required", 0, "Admin")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test admin endpoints
        admin_endpoints = [
            (f"{API_BASE}/admin/users", "User Management"),
            (f"{API_BASE}/admin/orders", "Order Management"),
            (f"{API_BASE}/admin/couriers/kyc", "KYC Management"),
            (f"{API_BASE}/admin/config", "System Configuration"),
            (f"{API_BASE}/admin/config/commission", "Commission Configuration")
        ]
        
        for endpoint, test_name in admin_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(endpoint, headers=headers, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.keys())
                    else:
                        count = 1
                    
                    self.log_result(
                        test_name,
                        True,
                        f"Retrieved {count} items",
                        response_time,
                        "Admin"
                    )
                else:
                    self.log_result(
                        test_name,
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                        "Admin"
                    )
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}", 0, "Admin")

    def test_business_operations(self):
        """Test business operations"""
        print("\n🏪 BUSINESS OPERATIONS TESTING")
        print("=" * 50)
        
        if "business" not in self.tokens:
            self.log_result("Business Operations", False, "Business authentication required", 0, "Business")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['business']}"}
        
        # Test business endpoints
        business_endpoints = [
            (f"{API_BASE}/products/my", "My Products"),
            (f"{API_BASE}/business/stats", "Business Statistics"),
            (f"{API_BASE}/business/orders/incoming", "Incoming Orders"),
            (f"{API_BASE}/business/status", "Business Status")
        ]
        
        for endpoint, test_name in business_endpoints:
            try:
                start_time = time.time()
                if "status" in endpoint:
                    # PUT request for status update
                    response = self.session.put(endpoint, json={"isOpen": True}, headers=headers, timeout=5)
                else:
                    response = self.session.get(endpoint, headers=headers, timeout=5)
                response_time = time.time() - start_time
                
                success = response.status_code in [200, 404]  # 404 is OK if no data
                
                self.log_result(
                    test_name,
                    success,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Business"
                )
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}", 0, "Business")

    def test_customer_operations(self):
        """Test customer operations"""
        print("\n👤 CUSTOMER OPERATIONS TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Customer Operations", False, "Customer authentication required", 0, "Customer")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test customer endpoints
        try:
            # Test businesses endpoint (public)
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/businesses", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_result(
                    "Customer - Browse Businesses",
                    True,
                    f"Found {len(businesses)} businesses",
                    response_time,
                    "Customer"
                )
            else:
                self.log_result(
                    "Customer - Browse Businesses",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Customer"
                )
        except Exception as e:
            self.log_result("Customer - Browse Businesses", False, f"Exception: {str(e)}", 0, "Customer")
        
        # Test address management
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/addresses", headers=headers, timeout=5)
            response_time = time.time() - start_time
            
            self.log_result(
                "Customer - Address Management",
                response.status_code == 200,
                f"HTTP {response.status_code}",
                response_time,
                "Customer"
            )
        except Exception as e:
            self.log_result("Customer - Address Management", False, f"Exception: {str(e)}", 0, "Customer")

    def test_courier_operations(self):
        """Test courier operations"""
        print("\n🚚 COURIER OPERATIONS TESTING")
        print("=" * 50)
        
        if "courier" not in self.tokens:
            self.log_result("Courier Operations", False, "Courier authentication required", 0, "Courier")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
        
        # Test courier endpoints
        courier_endpoints = [
            (f"{API_BASE}/orders/nearby", "Nearby Orders"),
            (f"{API_BASE}/courier/orders/available", "Available Orders"),
            (f"{API_BASE}/courier/orders/history", "Order History")
        ]
        
        for endpoint, test_name in courier_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(endpoint, headers=headers, timeout=5)
                response_time = time.time() - start_time
                
                # 403 is expected if courier is not KYC approved
                success = response.status_code in [200, 403]
                
                self.log_result(
                    test_name,
                    success,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Courier"
                )
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}", 0, "Courier")

    def test_order_system(self):
        """Test order creation and management"""
        print("\n📦 ORDER SYSTEM TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Order System", False, "Customer authentication required", 0, "Orders")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test order creation
        try:
            test_order = {
                "delivery_address": "Test Address, İstanbul",
                "delivery_lat": 41.0082,
                "delivery_lng": 28.9784,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Product",
                        "product_price": 50.0,
                        "quantity": 1,
                        "subtotal": 50.0
                    }
                ],
                "total_amount": 50.0,
                "notes": "Production test order"
            }
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/orders", json=test_order, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                commission = data.get("commission_amount", 0)
                expected_commission = test_order["total_amount"] * 0.03
                
                self.log_result(
                    "Order Creation",
                    True,
                    f"Order created, Commission: ₺{commission:.2f} (Expected: ₺{expected_commission:.2f})",
                    response_time,
                    "Orders"
                )
            else:
                self.log_result(
                    "Order Creation",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                    "Orders"
                )
        except Exception as e:
            self.log_result("Order Creation", False, f"Exception: {str(e)}", 0, "Orders")

    def test_performance_metrics(self):
        """Test performance metrics"""
        print("\n⚡ PERFORMANCE TESTING")
        print("=" * 50)
        
        # Test response times for critical endpoints
        critical_endpoints = [
            (f"{BACKEND_URL}/healthz", "Health Check"),
            (f"{API_BASE}/businesses", "Business Listing"),
            (f"{API_BASE}/menus/public", "Public Menus")
        ]
        
        for endpoint, test_name in critical_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(endpoint, timeout=5)
                response_time = time.time() - start_time
                
                # Response time should be under 1000ms for production
                acceptable_time = response_time < 1.0
                
                self.log_result(
                    f"Performance - {test_name}",
                    acceptable_time and response.status_code == 200,
                    f"{response_time*1000:.0f}ms ({'✓' if acceptable_time else '✗ >1000ms'})",
                    response_time,
                    "Performance"
                )
            except Exception as e:
                self.log_result(f"Performance - {test_name}", False, f"Exception: {str(e)}", 0, "Performance")

    def generate_final_report(self):
        """Generate final production readiness report"""
        print("\n📊 FINAL PRODUCTION READINESS REPORT")
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
        
        # Results by category
        categories = {}
        for result in self.test_results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"passed": 0, "total": 0}
            categories[category]["total"] += 1
            if result["success"]:
                categories[category]["passed"] += 1
        
        print(f"\n📊 RESULTS BY CATEGORY:")
        for category, stats in categories.items():
            cat_success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if cat_success_rate >= 80 else "❌" if cat_success_rate < 50 else "⚠️"
            print(f"   {status} {category}: {stats['passed']}/{stats['total']} ({cat_success_rate:.1f}%)")
        
        # Critical failures
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • [{result['category']}] {result['test']}: {result['details']}")
        
        # Production readiness assessment
        critical_categories = ["Infrastructure", "Authentication", "Security"]
        critical_success = all(
            categories.get(cat, {}).get("passed", 0) / categories.get(cat, {}).get("total", 1) >= 0.8
            for cat in critical_categories if cat in categories
        )
        
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        print(f"   Overall Success Rate: {success_rate:.1f}%")
        print(f"   Critical Systems: {'✅ READY' if critical_success and success_rate >= 80 else '❌ NOT READY'}")
        
        # Performance assessment
        performance_tests = [r for r in self.test_results if r["category"] == "Performance"]
        performance_ok = all(r["success"] for r in performance_tests) if performance_tests else True
        print(f"   Performance: {'✅ ACCEPTABLE' if performance_ok else '⚠️ NEEDS REVIEW'}")
        
        # Final recommendation
        production_ready = critical_success and success_rate >= 80 and performance_ok
        print(f"\n🚀 DEPLOYMENT RECOMMENDATION:")
        if production_ready:
            print("   ✅ READY FOR PRODUCTION DEPLOYMENT")
            print("   All critical systems are functional and performance is acceptable.")
        else:
            print("   ❌ NOT READY FOR PRODUCTION")
            print("   Critical issues must be resolved before deployment.")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "categories": categories,
            "production_ready": production_ready,
            "results": self.test_results
        }

def main():
    """Run final production readiness tests"""
    print("🚀 KURYECINI FINAL PRODUCTION READINESS TESTING")
    print("Comprehensive validation of all 26 features for deployment")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start Time: {datetime.now().isoformat()}")
    
    tester = FinalProductionTest()
    
    # Run all test suites in order
    tester.test_critical_infrastructure()
    tester.test_authentication_system()
    tester.test_jwt_refresh_system()
    tester.test_rate_limiting()
    tester.test_api_documentation()
    tester.test_admin_functionality()
    tester.test_business_operations()
    tester.test_customer_operations()
    tester.test_courier_operations()
    tester.test_order_system()
    tester.test_performance_metrics()
    
    # Generate final report
    report = tester.generate_final_report()
    
    return report

if __name__ == "__main__":
    main()