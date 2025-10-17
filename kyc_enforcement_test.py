#!/usr/bin/env python3
"""
KYC Enforcement System Testing
Testing the KYC approval system and business access control

Test Coverage:
1. KYC Dependency: get_approved_business_user functionality
2. Critical Endpoint Security:
   - GET /api/business/menu → KYC approval required
   - GET /api/business/orders/incoming → KYC approval required  
   - PATCH /api/business/orders/{id}/status → KYC approval required
3. Pending Business Block: KYC pending businesses can't access system resources
4. Admin KYC Management: Admin can see and approve pending businesses
5. Approved Business Authentication: Test login and system access
"""

import requests
import json
import time
import random
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://delivery-nexus-5.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

class KYCEnforcementTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.pending_business_token = None
        self.approved_business_token = None
        self.test_results = []
        self.test_business_id = None
        self.test_order_id = None
        
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

    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("🔐 AUTHENTICATING ADMIN USER...")
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                if self.admin_token:
                    self.log_test("Admin Authentication", True, 
                                f"Successfully authenticated admin user, token length: {len(self.admin_token)}")
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No access token in response")
            else:
                self.log_test("Admin Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Authentication error: {str(e)}")
        
        return False

    def create_test_business(self):
        """Create a test business for KYC testing"""
        print("\n🏪 CREATING TEST BUSINESS FOR KYC TESTING...")
        
        try:
            # Create a test business with pending KYC status
            business_data = {
                "email": f"test_kyc_business_{int(time.time())}@example.com",
                "password": "test123",
                "business_name": "Test KYC Restaurant",
                "tax_number": f"12345{random.randint(10000, 99999)}",
                "address": "Test Address, Istanbul",
                "city": "İstanbul",
                "business_category": "gida",
                "description": "Test restaurant for KYC testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/register/business", json=business_data)
            
            if response.status_code == 200:
                data = response.json()
                self.pending_business_token = data.get("access_token")
                user_data = data.get("user_data", {})
                self.test_business_id = user_data.get("id")
                
                self.log_test("Test Business Creation", True, 
                            f"Created test business with ID: {self.test_business_id}, KYC status: pending")
                return True
            else:
                self.log_test("Test Business Creation", False, 
                            f"Business creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Test Business Creation", False, f"Business creation error: {str(e)}")
        
        return False

    def test_pending_business_access_blocked(self):
        """Test that pending businesses are blocked from accessing critical endpoints"""
        print("\n🚫 TESTING PENDING BUSINESS ACCESS BLOCKING...")
        
        if not self.pending_business_token:
            self.log_test("Pending Business Access Test", False, "No pending business token available")
            return
        
        # Set authorization header for pending business
        headers = {"Authorization": f"Bearer {self.pending_business_token}"}
        
        # Test critical endpoints that should be blocked
        critical_endpoints = [
            ("GET", "/business/menu", "Business Menu Access"),
            ("GET", "/business/orders/incoming", "Incoming Orders Access"),
            ("GET", "/business/stats", "Business Stats Access")
        ]
        
        blocked_count = 0
        total_endpoints = len(critical_endpoints)
        
        for method, endpoint, test_name in critical_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                
                if response.status_code == 403:
                    self.log_test(f"Pending Business Blocked - {test_name}", True, 
                                f"Correctly blocked with 403 Forbidden: {endpoint}")
                    blocked_count += 1
                elif response.status_code == 401:
                    self.log_test(f"Pending Business Blocked - {test_name}", True, 
                                f"Correctly blocked with 401 Unauthorized: {endpoint}")
                    blocked_count += 1
                else:
                    self.log_test(f"Pending Business Blocked - {test_name}", False, 
                                f"SECURITY ISSUE: Pending business accessed {endpoint} with status {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Pending Business Blocked - {test_name}", False, 
                            f"Error testing {endpoint}: {str(e)}")
        
        # Summary of blocking effectiveness
        block_rate = (blocked_count / total_endpoints * 100) if total_endpoints > 0 else 0
        self.log_test("KYC Enforcement Effectiveness", block_rate == 100, 
                    f"Blocked {blocked_count}/{total_endpoints} critical endpoints ({block_rate:.1f}%)")

    def test_admin_kyc_management(self):
        """Test admin KYC management capabilities"""
        print("\n👨‍💼 TESTING ADMIN KYC MANAGEMENT...")
        
        if not self.admin_token or not self.test_business_id:
            self.log_test("Admin KYC Management Test", False, "Missing admin token or test business ID")
            return
        
        # Set admin authorization header
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Admin can view pending businesses
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", 
                                      headers=admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                businesses = data if isinstance(data, list) else data.get("businesses", [])
                
                # Check if our test business is in the pending list
                test_business_found = any(b.get("id") == self.test_business_id for b in businesses)
                
                self.log_test("Admin View Pending Businesses", True, 
                            f"Retrieved {len(businesses)} pending businesses, test business found: {test_business_found}")
            else:
                self.log_test("Admin View Pending Businesses", False, 
                            f"Failed to retrieve pending businesses: {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin View Pending Businesses", False, f"Error: {str(e)}")
        
        # Test 2: Admin can approve businesses
        try:
            approval_data = {
                "kyc_status": "approved",
                "approval_notes": "Test approval for KYC testing"
            }
            
            response = self.session.patch(f"{BACKEND_URL}/admin/businesses/{self.test_business_id}/status", 
                                        json=approval_data, headers=admin_headers)
            
            if response.status_code == 200:
                self.log_test("Admin Business Approval", True, 
                            f"Successfully approved business {self.test_business_id}")
                
                # Verify approval by checking business status
                verify_response = self.session.get(f"{BACKEND_URL}/admin/businesses/{self.test_business_id}", 
                                                 headers=admin_headers)
                
                if verify_response.status_code == 200:
                    business_data = verify_response.json()
                    kyc_status = business_data.get("kyc_status")
                    
                    if kyc_status == "approved":
                        self.log_test("Business Approval Verification", True, 
                                    f"Business KYC status confirmed as: {kyc_status}")
                    else:
                        self.log_test("Business Approval Verification", False, 
                                    f"Business KYC status is: {kyc_status}, expected: approved")
                        
            else:
                self.log_test("Admin Business Approval", False, 
                            f"Failed to approve business: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Admin Business Approval", False, f"Error: {str(e)}")

    def test_approved_business_authentication(self):
        """Test approved business login and authentication"""
        print("\n🔓 TESTING APPROVED BUSINESS AUTHENTICATION...")
        
        if not self.test_business_id:
            self.log_test("Approved Business Authentication", False, "No test business ID available")
            return
        
        # First, get the business email for login
        try:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/businesses/{self.test_business_id}", 
                                      headers=admin_headers)
            
            if response.status_code == 200:
                business_data = response.json()
                business_email = business_data.get("email")
                
                if business_email:
                    # Try to login with the approved business
                    login_data = {
                        "email": business_email,
                        "password": "test123"
                    }
                    
                    login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
                    
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        self.approved_business_token = login_result.get("access_token")
                        user_data = login_result.get("user", {})
                        
                        self.log_test("Approved Business Login", True, 
                                    f"Successfully logged in approved business, role: {user_data.get('role')}, token length: {len(self.approved_business_token) if self.approved_business_token else 0}")
                    else:
                        self.log_test("Approved Business Login", False, 
                                    f"Login failed: {login_response.status_code} - {login_response.text}")
                else:
                    self.log_test("Approved Business Authentication", False, "No email found for test business")
            else:
                self.log_test("Approved Business Authentication", False, 
                            f"Failed to get business details: {response.status_code}")
                
        except Exception as e:
            self.log_test("Approved Business Authentication", False, f"Error: {str(e)}")

    def test_approved_business_access(self):
        """Test that approved businesses can access critical endpoints"""
        print("\n✅ TESTING APPROVED BUSINESS ACCESS...")
        
        if not self.approved_business_token:
            self.log_test("Approved Business Access Test", False, "No approved business token available")
            return
        
        # Set authorization header for approved business
        headers = {"Authorization": f"Bearer {self.approved_business_token}"}
        
        # Test critical endpoints that should now be accessible
        critical_endpoints = [
            ("GET", "/business/orders/incoming", "Incoming Orders Access"),
            ("GET", "/business/stats", "Business Stats Access")
        ]
        
        accessible_count = 0
        total_endpoints = len(critical_endpoints)
        
        for method, endpoint, test_name in critical_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    self.log_test(f"Approved Business Access - {test_name}", True, 
                                f"Successfully accessed {endpoint}")
                    accessible_count += 1
                elif response.status_code == 403:
                    self.log_test(f"Approved Business Access - {test_name}", False, 
                                f"ISSUE: Approved business still blocked from {endpoint}")
                elif response.status_code == 404:
                    self.log_test(f"Approved Business Access - {test_name}", False, 
                                f"Endpoint not found: {endpoint}")
                else:
                    self.log_test(f"Approved Business Access - {test_name}", False, 
                                f"Unexpected response {response.status_code} for {endpoint}")
                    
            except Exception as e:
                self.log_test(f"Approved Business Access - {test_name}", False, 
                            f"Error testing {endpoint}: {str(e)}")
        
        # Summary of access effectiveness
        access_rate = (accessible_count / total_endpoints * 100) if total_endpoints > 0 else 0
        self.log_test("Approved Business Access Rate", access_rate > 0, 
                    f"Accessed {accessible_count}/{total_endpoints} critical endpoints ({access_rate:.1f}%)")

    def test_order_status_update_kyc_enforcement(self):
        """Test KYC enforcement on order status updates"""
        print("\n📦 TESTING ORDER STATUS UPDATE KYC ENFORCEMENT...")
        
        # First create a test order to update
        if self.approved_business_token:
            headers = {"Authorization": f"Bearer {self.approved_business_token}"}
            
            # Try to update a non-existent order to test the endpoint
            test_order_id = "test-order-123"
            status_data = {"status": "confirmed"}
            
            try:
                response = self.session.patch(f"{BACKEND_URL}/business/orders/{test_order_id}/status", 
                                            json=status_data, headers=headers)
                
                if response.status_code == 404:
                    self.log_test("Order Status Update KYC - Approved Business", True, 
                                f"Endpoint accessible for approved business (404 expected for non-existent order)")
                elif response.status_code == 403:
                    self.log_test("Order Status Update KYC - Approved Business", False, 
                                f"ISSUE: Approved business blocked from order status updates")
                else:
                    self.log_test("Order Status Update KYC - Approved Business", True, 
                                f"Endpoint accessible, response: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Order Status Update KYC - Approved Business", False, f"Error: {str(e)}")
        
        # Test with pending business token
        if self.pending_business_token:
            headers = {"Authorization": f"Bearer {self.pending_business_token}"}
            
            test_order_id = "test-order-123"
            status_data = {"status": "confirmed"}
            
            try:
                response = self.session.patch(f"{BACKEND_URL}/business/orders/{test_order_id}/status", 
                                            json=status_data, headers=headers)
                
                if response.status_code == 403:
                    self.log_test("Order Status Update KYC - Pending Business", True, 
                                f"Correctly blocked pending business from order status updates")
                else:
                    self.log_test("Order Status Update KYC - Pending Business", False, 
                                f"SECURITY ISSUE: Pending business accessed order status update with {response.status_code}")
                    
            except Exception as e:
                self.log_test("Order Status Update KYC - Pending Business", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all KYC enforcement tests"""
        print("🚀 STARTING KYC ENFORCEMENT SYSTEM TESTING")
        print("=" * 60)
        
        # Step 1: Admin authentication
        admin_auth_success = self.authenticate_admin()
        if not admin_auth_success:
            print("❌ CRITICAL: Admin authentication failed - cannot proceed with full testing")
            return
        
        # Step 2: Create test business
        business_created = self.create_test_business()
        if not business_created:
            print("❌ CRITICAL: Test business creation failed - cannot proceed with KYC testing")
            return
        
        # Step 3: Test pending business access blocking
        self.test_pending_business_access_blocked()
        
        # Step 4: Test admin KYC management
        self.test_admin_kyc_management()
        
        # Step 5: Test approved business authentication
        self.test_approved_business_authentication()
        
        # Step 6: Test approved business access
        self.test_approved_business_access()
        
        # Step 7: Test order status update KYC enforcement
        self.test_order_status_update_kyc_enforcement()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 KYC ENFORCEMENT SYSTEM TEST SUMMARY")
        print("=" * 60)
        
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
        
        # Critical security findings
        print("\n🚨 SECURITY ANALYSIS:")
        
        # Check for security bypasses
        security_bypasses = []
        for result in self.test_results:
            if not result["success"] and "SECURITY ISSUE" in result["details"]:
                security_bypasses.append(result["test"])
        
        if security_bypasses:
            print(f"❌ CRITICAL SECURITY ISSUES: {len(security_bypasses)} security bypasses detected:")
            for bypass in security_bypasses:
                print(f"   - {bypass}")
        else:
            print("✅ NO SECURITY BYPASSES: KYC enforcement working correctly")
        
        # Check authentication issues
        auth_issues = []
        for result in self.test_results:
            if not result["success"] and ("authentication" in result["details"].lower() or 
                                        "login failed" in result["details"].lower()):
                auth_issues.append(result["test"])
        
        if auth_issues:
            print(f"🔐 AUTHENTICATION ISSUES: {len(auth_issues)} authentication problems:")
            for issue in auth_issues:
                print(f"   - {issue}")
        
        print(f"\n📝 CONCLUSION:")
        if success_rate >= 90:
            print("✅ EXCELLENT: KYC enforcement system is working correctly")
            print("   Security gaps are closed, businesses properly controlled")
        elif success_rate >= 70:
            print("⚠️ GOOD: KYC enforcement mostly working with minor issues")
            print("   Core security implemented but some edge cases need attention")
        elif success_rate >= 50:
            print("⚠️ WARNING: KYC enforcement has significant issues")
            print("   Some security gaps remain - needs immediate attention")
        else:
            print("❌ CRITICAL: KYC enforcement system is NOT WORKING")
            print("   Major security vulnerabilities detected - urgent fixes required")

if __name__ == "__main__":
    tester = KYCEnforcementTester()
    tester.run_all_tests()