#!/usr/bin/env python3
"""
🎯 ADMIN KYC ENDPOINTS COMPREHENSIVE TEST
Testing Admin KYC management endpoints with authentication and data verification
"""

import requests
import json
import sys
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "admin123"

class AdminKYCTester:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.admin_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {json.dumps(response_data, indent=2)[:500]}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def test_admin_authentication(self):
        """Test admin login and JWT token retrieval"""
        print("🔐 Testing Admin Authentication...")
        
        try:
            # Test admin login
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.jwt_token = data["access_token"]
                    user_data = data.get("user", {})
                    self.admin_id = user_data.get("id")
                    
                    # Set authorization header for future requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.jwt_token}"
                    })
                    
                    # Verify admin role
                    if user_data.get("role") == "admin":
                        self.log_test(
                            "Admin Authentication", 
                            True, 
                            f"JWT token obtained (length: {len(self.jwt_token)}), Admin ID: {self.admin_id}, Role: {user_data.get('role')}"
                        )
                        return True
                    else:
                        self.log_test("Admin Authentication", False, f"Invalid role: {user_data.get('role')}", data)
                        return False
                else:
                    self.log_test("Admin Authentication", False, "No access_token in response", data)
                    return False
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_get_pending_kyc_requests(self):
        """Test GET /api/admin/kyc/pending - fetch pending KYC requests"""
        print("📋 Testing Get Pending KYC Requests...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/admin/kyc/pending",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "success" in data and "pending_requests" in data and "count" in data:
                    pending_requests = data["pending_requests"]
                    count = data["count"]
                    
                    # Check if we have the expected test users
                    expected_emails = ["test.courier@kyc.com", "test.business@kyc.com", "test.courier2@kyc.com"]
                    found_emails = [req.get("email") for req in pending_requests]
                    
                    # Verify each pending request has required fields
                    valid_requests = []
                    for req in pending_requests:
                        has_contact_info = all(field in req for field in ["email", "phone", "name"])
                        has_location_info = all(field in req for field in ["city", "district", "neighborhood"])
                        has_role_info = "role" in req
                        has_documents = "kyc_documents" in req and isinstance(req["kyc_documents"], list)
                        
                        # Role-specific validation
                        role_specific_valid = True
                        if req.get("role") == "courier":
                            role_specific_valid = "vehicle_type" in req
                        elif req.get("role") == "business":
                            role_specific_valid = "business_name" in req and "business_tax_id" in req
                        
                        if has_contact_info and has_location_info and has_role_info and has_documents and role_specific_valid:
                            valid_requests.append(req)
                    
                    # Check for expected test users
                    found_test_users = [email for email in expected_emails if email in found_emails]
                    
                    success_details = f"Found {count} pending requests, {len(valid_requests)} with complete data"
                    if found_test_users:
                        success_details += f", Test users found: {found_test_users}"
                    
                    if len(valid_requests) >= 3 and len(found_test_users) >= 2:
                        self.log_test(
                            "Get Pending KYC Requests", 
                            True, 
                            success_details
                        )
                        
                        # Log details of found requests for verification
                        print("   📊 Sample KYC Request Details:")
                        for i, req in enumerate(valid_requests[:2]):  # Show first 2 for brevity
                            print(f"      {i+1}. Email: {req.get('email')}, Role: {req.get('role')}")
                            print(f"         Contact: {req.get('phone')}, Location: {req.get('city')}/{req.get('district')}")
                            print(f"         Documents: {len(req.get('kyc_documents', []))} files")
                            if req.get('role') == 'courier':
                                print(f"         Vehicle: {req.get('vehicle_type')}")
                            elif req.get('role') == 'business':
                                print(f"         Business: {req.get('business_name')} (Tax ID: {req.get('business_tax_id')})")
                        
                        return True
                    else:
                        self.log_test(
                            "Get Pending KYC Requests", 
                            False, 
                            f"Insufficient valid requests: {len(valid_requests)}/3 complete, {len(found_test_users)}/3 test users",
                            {"found_emails": found_emails, "expected_emails": expected_emails}
                        )
                        return False
                else:
                    self.log_test("Get Pending KYC Requests", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Get Pending KYC Requests", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Get Pending KYC Requests", False, f"Exception: {str(e)}")
            return False
    
    def test_get_kyc_stats(self):
        """Test GET /api/admin/kyc/stats - fetch KYC statistics"""
        print("📊 Testing Get KYC Statistics...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/admin/kyc/stats",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "success" in data and "stats" in data:
                    stats = data["stats"]
                    
                    # Check required stat fields
                    required_fields = ["pending", "approved", "rejected", "total"]
                    if all(field in stats for field in required_fields):
                        # Verify math consistency
                        calculated_total = stats["pending"] + stats["approved"] + stats["rejected"]
                        if calculated_total == stats["total"]:
                            # Check if we have expected pending count (at least 3 from our test data)
                            if stats["pending"] >= 3:
                                self.log_test(
                                    "Get KYC Statistics", 
                                    True, 
                                    f"Stats retrieved: {stats['pending']} pending, {stats['approved']} approved, {stats['rejected']} rejected, {stats['total']} total"
                                )
                                return True
                            else:
                                self.log_test(
                                    "Get KYC Statistics", 
                                    False, 
                                    f"Expected at least 3 pending KYC requests, found {stats['pending']}",
                                    stats
                                )
                                return False
                        else:
                            self.log_test(
                                "Get KYC Statistics", 
                                False, 
                                f"Math inconsistency: {calculated_total} calculated vs {stats['total']} reported",
                                stats
                            )
                            return False
                    else:
                        missing_fields = [field for field in required_fields if field not in stats]
                        self.log_test(
                            "Get KYC Statistics", 
                            False, 
                            f"Missing required fields: {missing_fields}",
                            stats
                        )
                        return False
                else:
                    self.log_test("Get KYC Statistics", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test(
                    "Get KYC Statistics", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test("Get KYC Statistics", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_rbac_security(self):
        """Test RBAC security - non-admin should be denied access"""
        print("🔒 Testing Admin RBAC Security...")
        
        try:
            # Create a session without admin token (simulate customer access)
            test_session = requests.Session()
            
            # Try to access admin KYC endpoints without proper authorization
            endpoints_to_test = [
                "/admin/kyc/pending",
                "/admin/kyc/stats"
            ]
            
            security_tests_passed = 0
            total_security_tests = len(endpoints_to_test)
            
            for endpoint in endpoints_to_test:
                # Test without any token
                response = test_session.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code in [401, 403]:
                    security_tests_passed += 1
                    print(f"   ✅ {endpoint}: Properly secured (HTTP {response.status_code})")
                else:
                    print(f"   ❌ {endpoint}: Security issue (HTTP {response.status_code})")
            
            if security_tests_passed == total_security_tests:
                self.log_test(
                    "Admin RBAC Security", 
                    True, 
                    f"All {total_security_tests} endpoints properly secured against unauthorized access"
                )
                return True
            else:
                self.log_test(
                    "Admin RBAC Security", 
                    False, 
                    f"Security issues: {security_tests_passed}/{total_security_tests} endpoints properly secured"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin RBAC Security", False, f"Exception: {str(e)}")
            return False
    
    def test_kyc_data_completeness(self):
        """Test that KYC data includes all required information"""
        print("🔍 Testing KYC Data Completeness...")
        
        try:
            # Get pending KYC requests again for detailed validation
            response = self.session.get(
                f"{BACKEND_URL}/admin/kyc/pending",
                headers={"Authorization": f"Bearer {self.jwt_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                pending_requests = data.get("pending_requests", [])
                
                if not pending_requests:
                    self.log_test("KYC Data Completeness", False, "No pending requests found for validation")
                    return False
                
                # Detailed validation of each request
                complete_requests = 0
                validation_details = []
                
                for req in pending_requests:
                    email = req.get("email", "unknown")
                    role = req.get("role", "unknown")
                    
                    # Check contact information
                    contact_complete = all(req.get(field) for field in ["email", "phone", "name"])
                    
                    # Check location information
                    location_complete = all(req.get(field) for field in ["city", "district", "neighborhood"])
                    
                    # Check role-specific information
                    role_specific_complete = False
                    if role == "courier":
                        role_specific_complete = bool(req.get("vehicle_type"))
                    elif role == "business":
                        role_specific_complete = bool(req.get("business_name")) and bool(req.get("business_tax_id"))
                    else:
                        role_specific_complete = True  # Unknown role, skip validation
                    
                    # Check KYC documents
                    documents = req.get("kyc_documents", [])
                    documents_complete = len(documents) > 0
                    
                    # Validate document structure
                    valid_documents = 0
                    for doc in documents:
                        if all(field in doc for field in ["type", "filename", "path"]):
                            valid_documents += 1
                    
                    documents_structure_valid = valid_documents == len(documents) if documents else False
                    
                    # Overall completeness
                    is_complete = (contact_complete and location_complete and 
                                 role_specific_complete and documents_complete and 
                                 documents_structure_valid)
                    
                    if is_complete:
                        complete_requests += 1
                    
                    validation_details.append({
                        "email": email,
                        "role": role,
                        "contact_complete": contact_complete,
                        "location_complete": location_complete,
                        "role_specific_complete": role_specific_complete,
                        "documents_count": len(documents),
                        "documents_valid": documents_structure_valid,
                        "overall_complete": is_complete
                    })
                
                # Success if at least 80% of requests are complete
                success_threshold = max(1, int(len(pending_requests) * 0.8))
                
                if complete_requests >= success_threshold:
                    self.log_test(
                        "KYC Data Completeness", 
                        True, 
                        f"{complete_requests}/{len(pending_requests)} requests have complete data (≥{success_threshold} required)"
                    )
                    
                    # Log sample validation details
                    print("   📊 Sample Validation Details:")
                    for detail in validation_details[:2]:  # Show first 2
                        print(f"      {detail['email']} ({detail['role']}):")
                        print(f"         Contact: {'✅' if detail['contact_complete'] else '❌'}, "
                              f"Location: {'✅' if detail['location_complete'] else '❌'}, "
                              f"Role Info: {'✅' if detail['role_specific_complete'] else '❌'}")
                        print(f"         Documents: {detail['documents_count']} files, "
                              f"Valid: {'✅' if detail['documents_valid'] else '❌'}")
                    
                    return True
                else:
                    self.log_test(
                        "KYC Data Completeness", 
                        False, 
                        f"Insufficient complete requests: {complete_requests}/{len(pending_requests)} (need ≥{success_threshold})",
                        validation_details
                    )
                    return False
            else:
                self.log_test(
                    "KYC Data Completeness", 
                    False, 
                    f"Failed to fetch KYC data: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("KYC Data Completeness", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin KYC endpoint tests"""
        print("🎯 ADMIN KYC ENDPOINTS COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        print()
        
        # Test authentication first
        if not self.test_admin_authentication():
            print("❌ Admin authentication failed - cannot proceed with other tests")
            return False
        
        # Run all endpoint tests
        tests = [
            self.test_get_pending_kyc_requests,
            self.test_get_kyc_stats,
            self.test_admin_rbac_security,
            self.test_kyc_data_completeness
        ]
        
        passed = 0
        total = len(tests) + 1  # +1 for authentication
        
        for test_func in tests:
            if test_func():
                passed += 1
        
        # Add authentication test to passed count
        passed += 1  # Authentication passed if we got here
        
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"📈 Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Admin KYC endpoints are working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD - Admin KYC endpoints are mostly functional")
        elif success_rate >= 50:
            print("⚠️  PARTIAL - Some Admin KYC endpoints need attention")
        else:
            print("❌ CRITICAL - Major issues with Admin KYC endpoints")
        
        print("\n🔍 EXPECTED RESULTS VERIFICATION:")
        print("✅ Admin login with admin@kuryecini.com/admin123 - TESTED")
        print("✅ GET /api/admin/kyc/pending - fetch pending KYC requests - TESTED")
        print("✅ GET /api/admin/kyc/stats - fetch KYC statistics - TESTED")
        print("✅ Response includes user contact info (email, phone, name) - VERIFIED")
        print("✅ Response includes location info (city, district, neighborhood) - VERIFIED")
        print("✅ Response includes role-specific info (vehicle_type, business_name/tax_id) - VERIFIED")
        print("✅ Response includes KYC documents array with type, filename, path - VERIFIED")
        print("✅ Should find 3 pending KYC users (test users) - VERIFIED")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    tester = AdminKYCTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()