#!/usr/bin/env python3
"""
KYC APPROVAL SYSTEM TESTING
Testing the fixed business and courier KYC approval endpoints.

Test Coverage:
1. Business KYC Approval: PATCH /api/admin/businesses/{business_id}/status
2. Courier KYC Approval: PATCH /api/admin/couriers/{courier_id}/status  
3. Data Fetching: GET /api/admin/businesses?kyc_status=pending and GET /api/admin/couriers?kyc_status=pending
4. Authentication with admin credentials
5. RBAC testing - only admin can approve/reject KYC
6. Database persistence verification
7. Error handling for invalid data
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://kuryecini-auth.preview.emergentagent.com/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
    "courier": {"email": "testkurye@example.com", "password": "test123"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"}
}

class KYCApprovalTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.pending_businesses = []
        self.pending_couriers = []
        
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
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
        
    def authenticate_user(self, role):
        """Authenticate user and get JWT token"""
        try:
            creds = TEST_CREDENTIALS[role]
            response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_data = data.get("user", {})
                self.tokens[role] = token
                
                self.log_test(
                    f"{role.title()} Authentication",
                    True,
                    f"Login successful - Token: {len(token)} chars, Role: {user_data.get('role')}, Email: {user_data.get('email')}"
                )
                return token
            else:
                self.log_test(
                    f"{role.title()} Authentication",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return None
                
        except Exception as e:
            self.log_test(f"{role.title()} Authentication", False, "", str(e))
            return None
    
    def get_pending_businesses(self):
        """Get list of pending businesses for KYC approval"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", headers=headers)
            
            if response.status_code == 200:
                businesses = response.json()  # API returns direct list
                self.pending_businesses = businesses
                
                self.log_test(
                    "Get Pending Businesses",
                    True,
                    f"Found {len(businesses)} pending businesses"
                )
                return businesses
            else:
                self.log_test(
                    "Get Pending Businesses",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Get Pending Businesses", False, "", str(e))
            return []
    
    def get_pending_couriers(self):
        """Get list of pending couriers for KYC approval"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{BACKEND_URL}/admin/couriers?kyc_status=pending", headers=headers)
            
            if response.status_code == 200:
                couriers = response.json()  # API returns direct list
                self.pending_couriers = couriers
                
                self.log_test(
                    "Get Pending Couriers",
                    True,
                    f"Found {len(couriers)} pending couriers"
                )
                return couriers
            else:
                self.log_test(
                    "Get Pending Couriers",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test("Get Pending Couriers", False, "", str(e))
            return []
    
    def approve_business_kyc(self, business_id):
        """Test business KYC approval"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            payload = {"kyc_status": "approved"}
            
            response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"Business KYC Approval - {business_id}",
                    True,
                    f"Business approved successfully - Response: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.log_test(
                    f"Business KYC Approval - {business_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Business KYC Approval - {business_id}", False, "", str(e))
            return False
    
    def reject_business_kyc(self, business_id, rejection_reason="Test rejection"):
        """Test business KYC rejection"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            payload = {"kyc_status": "rejected", "rejection_reason": rejection_reason}
            
            response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"Business KYC Rejection - {business_id}",
                    True,
                    f"Business rejected successfully - Reason: {rejection_reason}"
                )
                return True
            else:
                self.log_test(
                    f"Business KYC Rejection - {business_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Business KYC Rejection - {business_id}", False, "", str(e))
            return False
    
    def approve_courier_kyc(self, courier_id):
        """Test courier KYC approval"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            payload = {"kyc_status": "approved"}
            
            response = requests.patch(
                f"{BACKEND_URL}/admin/couriers/{courier_id}/status",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"Courier KYC Approval - {courier_id}",
                    True,
                    f"Courier approved successfully - Response: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.log_test(
                    f"Courier KYC Approval - {courier_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Courier KYC Approval - {courier_id}", False, "", str(e))
            return False
    
    def reject_courier_kyc(self, courier_id, rejection_reason="Test rejection"):
        """Test courier KYC rejection"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            payload = {"kyc_status": "rejected", "rejection_reason": rejection_reason}
            
            response = requests.patch(
                f"{BACKEND_URL}/admin/couriers/{courier_id}/status",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"Courier KYC Rejection - {courier_id}",
                    True,
                    f"Courier rejected successfully - Reason: {rejection_reason}"
                )
                return True
            else:
                self.log_test(
                    f"Courier KYC Rejection - {courier_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Courier KYC Rejection - {courier_id}", False, "", str(e))
            return False
    
    def verify_business_status_update(self, business_id, expected_status):
        """Verify business status was updated in database"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{BACKEND_URL}/admin/businesses/{business_id}", headers=headers)
            
            if response.status_code == 200:
                business = response.json()  # API returns business data directly
                actual_status = business.get("kyc_status")
                
                if actual_status == expected_status:
                    self.log_test(
                        f"Business Status Verification - {business_id}",
                        True,
                        f"Status correctly updated to '{expected_status}'"
                    )
                    return True
                else:
                    self.log_test(
                        f"Business Status Verification - {business_id}",
                        False,
                        f"Expected: {expected_status}, Got: {actual_status}",
                        "Status not updated in database"
                    )
                    return False
            else:
                self.log_test(
                    f"Business Status Verification - {business_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Business Status Verification - {business_id}", False, "", str(e))
            return False
    
    def verify_courier_status_update(self, courier_id, expected_status):
        """Verify courier status was updated in database"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(f"{BACKEND_URL}/admin/couriers/{courier_id}", headers=headers)
            
            if response.status_code == 200:
                courier = response.json()  # API returns courier data directly
                actual_status = courier.get("kyc_status")
                
                if actual_status == expected_status:
                    self.log_test(
                        f"Courier Status Verification - {courier_id}",
                        True,
                        f"Status correctly updated to '{expected_status}'"
                    )
                    return True
                else:
                    self.log_test(
                        f"Courier Status Verification - {courier_id}",
                        False,
                        f"Expected: {expected_status}, Got: {actual_status}",
                        "Status not updated in database"
                    )
                    return False
            else:
                self.log_test(
                    f"Courier Status Verification - {courier_id}",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(f"Courier Status Verification - {courier_id}", False, "", str(e))
            return False
    
    def test_unauthorized_access(self):
        """Test RBAC - non-admin users should not be able to approve KYC"""
        try:
            # Test with customer token
            if "customer" in self.tokens:
                headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
                payload = {"kyc_status": "approved"}
                
                response = requests.patch(
                    f"{BACKEND_URL}/admin/businesses/test-id/status",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 403:
                    self.log_test(
                        "RBAC - Customer Access Denied",
                        True,
                        "Customer correctly denied access to KYC approval (403 Forbidden)"
                    )
                else:
                    self.log_test(
                        "RBAC - Customer Access Denied",
                        False,
                        f"Expected 403, got {response.status_code}",
                        "Customer should not have access to KYC approval"
                    )
            
            # Test without token
            payload = {"kyc_status": "approved"}
            response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/test-id/status",
                json=payload
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "RBAC - Unauthenticated Access Denied",
                    True,
                    f"Unauthenticated request correctly denied ({response.status_code})"
                )
            else:
                self.log_test(
                    "RBAC - Unauthenticated Access Denied",
                    False,
                    f"Expected 401/403, got {response.status_code}",
                    "Unauthenticated requests should be denied"
                )
                
        except Exception as e:
            self.log_test("RBAC Testing", False, "", str(e))
    
    def test_invalid_data_handling(self):
        """Test error handling for invalid data"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Test invalid business ID
            payload = {"kyc_status": "approved"}
            response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/invalid-id-12345/status",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 404:
                self.log_test(
                    "Invalid Business ID Handling",
                    True,
                    "Invalid business ID correctly returns 404"
                )
            else:
                self.log_test(
                    "Invalid Business ID Handling",
                    False,
                    f"Expected 404, got {response.status_code}",
                    response.text
                )
            
            # Test invalid status value
            if self.pending_businesses:
                business_id = self.pending_businesses[0].get("id")
                payload = {"kyc_status": "invalid_status"}
                response = requests.patch(
                    f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code in [400, 422]:
                    self.log_test(
                        "Invalid Status Value Handling",
                        True,
                        f"Invalid status value correctly returns {response.status_code}"
                    )
                else:
                    self.log_test(
                        "Invalid Status Value Handling",
                        False,
                        f"Expected 400/422, got {response.status_code}",
                        response.text
                    )
            
            # Test missing fields
            if self.pending_businesses:
                business_id = self.pending_businesses[0].get("id")
                payload = {}  # Empty payload
                response = requests.patch(
                    f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code in [400, 422]:
                    self.log_test(
                        "Missing Fields Handling",
                        True,
                        f"Missing fields correctly returns {response.status_code}"
                    )
                else:
                    self.log_test(
                        "Missing Fields Handling",
                        False,
                        f"Expected 400/422, got {response.status_code}",
                        response.text
                    )
                
        except Exception as e:
            self.log_test("Invalid Data Handling", False, "", str(e))
    
    def create_test_data(self):
        """Create test businesses and couriers with pending status"""
        try:
            # Create test business
            business_data = {
                "email": f"test-business-{int(time.time())}@kyc-test.com",
                "password": "testpass123",
                "business_name": "KYC Test Restaurant",
                "tax_number": "1234567890",
                "address": "Test Address, Istanbul",
                "city": "İstanbul",
                "business_category": "gida",
                "description": "Test restaurant for KYC approval testing"
            }
            
            response = requests.post(f"{BACKEND_URL}/register/business", json=business_data)
            if response.status_code == 200:
                self.log_test(
                    "Create Test Business",
                    True,
                    "Test business created successfully for KYC testing"
                )
            
            # Create test courier
            courier_data = {
                "email": f"test-courier-{int(time.time())}@kyc-test.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "Courier",
                "iban": "TR123456789012345678901234",
                "vehicle_type": "motor",
                "vehicle_model": "Honda CBR",
                "license_class": "A2",
                "license_number": "TEST123456",
                "city": "İstanbul"
            }
            
            response = requests.post(f"{BACKEND_URL}/register/courier", json=courier_data)
            if response.status_code == 200:
                self.log_test(
                    "Create Test Courier",
                    True,
                    "Test courier created successfully for KYC testing"
                )
                
        except Exception as e:
            self.log_test("Create Test Data", False, "", str(e))

    def run_comprehensive_test(self):
        """Run comprehensive KYC approval system test"""
        print("🎯 STARTING KYC APPROVAL SYSTEM TESTING")
        print("=" * 60)
        
        # Step 1: Authentication
        print("📋 STEP 1: AUTHENTICATION TESTING")
        admin_token = self.authenticate_user("admin")
        if not admin_token:
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with testing.")
            return
        
        # Also authenticate other users for RBAC testing
        self.authenticate_user("customer")
        self.authenticate_user("business")
        
        # Step 1.5: Create test data
        print("\n📋 STEP 1.5: CREATING TEST DATA")
        self.create_test_data()
        
        # Step 2: Get pending businesses and couriers
        print("\n📋 STEP 2: DATA FETCHING TESTING")
        businesses = self.get_pending_businesses()
        couriers = self.get_pending_couriers()
        
        # Step 3: Test business KYC approval/rejection
        print("\n📋 STEP 3: BUSINESS KYC APPROVAL TESTING")
        if businesses:
            # Test approval of first business
            first_business = businesses[0]
            business_id = first_business.get("id")
            if business_id:
                success = self.approve_business_kyc(business_id)
                if success:
                    self.verify_business_status_update(business_id, "approved")
            
            # Test rejection of second business (if available)
            if len(businesses) > 1:
                second_business = businesses[1]
                business_id = second_business.get("id")
                if business_id:
                    success = self.reject_business_kyc(business_id, "Test rejection for comprehensive testing")
                    if success:
                        self.verify_business_status_update(business_id, "rejected")
        else:
            # If no pending businesses, let's test with existing ones by setting them to pending first
            print("⚠️  No pending businesses found. Testing with existing businesses...")
            self.test_with_existing_businesses()
        
        # Step 4: Test courier KYC approval/rejection
        print("\n📋 STEP 4: COURIER KYC APPROVAL TESTING")
        if couriers:
            # Test approval of first courier
            first_courier = couriers[0]
            courier_id = first_courier.get("id")
            if courier_id:
                success = self.approve_courier_kyc(courier_id)
                if success:
                    self.verify_courier_status_update(courier_id, "approved")
            
            # Test rejection of second courier (if available)
            if len(couriers) > 1:
                second_courier = couriers[1]
                courier_id = second_courier.get("id")
                if courier_id:
                    success = self.reject_courier_kyc(courier_id, "Test rejection for comprehensive testing")
                    if success:
                        self.verify_courier_status_update(courier_id, "rejected")
        else:
            # If no pending couriers, let's test with existing ones
            print("⚠️  No pending couriers found. Testing with existing couriers...")
            self.test_with_existing_couriers()
        
        # Step 5: Test RBAC security
        print("\n📋 STEP 5: RBAC SECURITY TESTING")
        self.test_unauthorized_access()
        
        # Step 6: Test error handling
        print("\n📋 STEP 6: ERROR HANDLING TESTING")
        self.test_invalid_data_handling()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 KYC APPROVAL SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['error']}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}")
            if result["details"]:
                print(f"      Details: {result['details']}")
        
        # Critical issues summary
        critical_failures = [r for r in self.test_results if not r["success"] and any(keyword in r["test"].lower() for keyword in ["authentication", "approval", "rejection"])]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"   🔥 {failure['test']}: {failure['error']}")
        
        print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
    
    def test_with_existing_businesses(self):
        """Test KYC approval with existing businesses by first setting them to pending"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Get all businesses
            response = requests.get(f"{BACKEND_URL}/admin/businesses", headers=headers)
            if response.status_code == 200:
                all_businesses = response.json()
                
                if all_businesses:
                    # Take first business and set it to pending for testing
                    test_business = all_businesses[0]
                    business_id = test_business.get("id")
                    
                    # Set to pending first
                    payload = {"kyc_status": "pending"}
                    response = requests.patch(
                        f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Set Business to Pending - {business_id}",
                            True,
                            f"Business {test_business.get('business_name')} set to pending for testing"
                        )
                        
                        # Now test approval
                        success = self.approve_business_kyc(business_id)
                        if success:
                            self.verify_business_status_update(business_id, "approved")
                        
                        # Test rejection with another business if available
                        if len(all_businesses) > 1:
                            second_business = all_businesses[1]
                            second_id = second_business.get("id")
                            
                            # Set to pending
                            response = requests.patch(
                                f"{BACKEND_URL}/admin/businesses/{second_id}/status",
                                headers=headers,
                                json={"kyc_status": "pending"}
                            )
                            
                            if response.status_code == 200:
                                success = self.reject_business_kyc(second_id, "Test rejection for comprehensive testing")
                                if success:
                                    self.verify_business_status_update(second_id, "rejected")
                    
        except Exception as e:
            self.log_test("Test with Existing Businesses", False, "", str(e))
    
    def test_with_existing_couriers(self):
        """Test KYC approval with existing couriers"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Get all couriers
            response = requests.get(f"{BACKEND_URL}/admin/couriers", headers=headers)
            if response.status_code == 200:
                all_couriers = response.json()
                
                if all_couriers:
                    # Take first courier and set it to pending for testing
                    test_courier = all_couriers[0]
                    courier_id = test_courier.get("id")
                    
                    # Set to pending first
                    payload = {"kyc_status": "pending"}
                    response = requests.patch(
                        f"{BACKEND_URL}/admin/couriers/{courier_id}/status",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        self.log_test(
                            f"Set Courier to Pending - {courier_id}",
                            True,
                            f"Courier {test_courier.get('first_name', '')} {test_courier.get('last_name', '')} set to pending for testing"
                        )
                        
                        # Now test approval
                        success = self.approve_courier_kyc(courier_id)
                        if success:
                            self.verify_courier_status_update(courier_id, "approved")
                else:
                    self.log_test(
                        "No Couriers Available",
                        False,
                        "No couriers found in system for testing",
                        "Consider creating test courier data"
                    )
                    
        except Exception as e:
            self.log_test("Test with Existing Couriers", False, "", str(e))

def main():
    """Main test execution"""
    tester = KYCApprovalTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()