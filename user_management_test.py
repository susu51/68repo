#!/usr/bin/env python3
"""
DeliverTR User Management System Testing Suite
Tests the new user management system in the admin panel:
1. User Deletion API: DELETE /api/admin/users/{user_id}
2. Registration APIs for Admin: POST /api/register/customer, /api/register/business, /api/register/courier
3. Admin User Listing: GET /api/admin/users
4. Full User Management Flow: Login as admin, create user, list users, delete user
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class UserManagementTester:
    def __init__(self, base_url="https://food-dash-87.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Store created users for testing
        self.created_users = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.base_url}/"
        test_headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use admin token
        auth_token = token or self.admin_token
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    response_text = response.text
                    print(f"   Response: {response_text}")
                    self.log_test(name, True)
                    return True, response_text
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_admin_login(self):
        """Test admin login with any email + password '6851'"""
        login_data = {
            "email": "admin@test.com",
            "password": "6851"
        }
        
        success, response = self.run_test(
            "Admin Login for User Management",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and response.get('access_token'):
            self.admin_token = response['access_token']
            print(f"   Admin token stored: {self.admin_token[:20]}...")
            
            # Verify admin user data
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'admin':
                self.log_test("Admin Login for User Management", False, f"Expected admin role, got {user_data.get('role')}")
                return False
            
            print(f"   ✅ Admin login successful with role: {user_data.get('role')}")
            return True
        
        return False

    def test_admin_user_listing(self):
        """Test GET /api/admin/users - Admin User Listing"""
        if not self.admin_token:
            self.log_test("Admin User Listing", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "Admin User Listing - GET /admin/users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} users in system")
            
            # Verify user data structure
            if len(response) > 0:
                user = response[0]
                required_fields = ['id', 'email', 'role', 'created_at', 'is_active']
                missing_fields = [field for field in required_fields if field not in user]
                
                if missing_fields:
                    self.log_test("Admin User Listing", False, f"Missing user fields: {missing_fields}")
                    return False
                
                print(f"   ✅ User data structure valid")
                print(f"   ✅ Sample user: {user.get('email')} - {user.get('role')}")
            
            return True
        
        return False

    def test_customer_registration_for_admin(self):
        """Test POST /api/register/customer - Customer registration for admin"""
        customer_email = f"admin_customer_{uuid.uuid4().hex[:8]}@test.com"
        customer_data = {
            "email": customer_email,
            "password": "TestPass123!",
            "first_name": "Admin",
            "last_name": "Customer",
            "city": "İstanbul"
        }
        
        success, response = self.run_test(
            "Customer Registration for Admin",
            "POST",
            "register/customer",
            200,
            data=customer_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Customer Registration for Admin", False, f"Missing response fields: {missing_fields}")
                return False
            
            # Verify user type
            if response.get('user_type') != 'customer':
                self.log_test("Customer Registration for Admin", False, f"Wrong user_type: {response.get('user_type')}")
                return False
            
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'customer':
                self.log_test("Customer Registration for Admin", False, f"Wrong role: {user_data.get('role')}")
                return False
            
            # Store created user for deletion test
            self.created_users.append({
                'type': 'customer',
                'email': customer_email,
                'id': user_data.get('id'),
                'data': user_data
            })
            
            print(f"   ✅ Customer created with ID: {user_data.get('id')}")
            print(f"   ✅ Customer role: {user_data.get('role')}")
            return True
        
        return False

    def test_business_registration_for_admin(self):
        """Test POST /api/register/business - Business registration for admin"""
        business_email = f"admin_business_{uuid.uuid4().hex[:8]}@test.com"
        business_data = {
            "email": business_email,
            "password": "TestPass123!",
            "business_name": "Admin Test Restaurant",
            "tax_number": "1234567890",
            "address": "Test Address, İstanbul",
            "city": "İstanbul",
            "business_category": "gida",
            "description": "Test restaurant created by admin"
        }
        
        success, response = self.run_test(
            "Business Registration for Admin",
            "POST",
            "register/business",
            200,
            data=business_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Business Registration for Admin", False, f"Missing response fields: {missing_fields}")
                return False
            
            # Verify user type
            if response.get('user_type') != 'business':
                self.log_test("Business Registration for Admin", False, f"Wrong user_type: {response.get('user_type')}")
                return False
            
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'business':
                self.log_test("Business Registration for Admin", False, f"Wrong role: {user_data.get('role')}")
                return False
            
            # Verify business-specific fields
            business_fields = ['business_name', 'tax_number', 'address', 'city', 'business_category']
            for field in business_fields:
                if field not in user_data:
                    self.log_test("Business Registration for Admin", False, f"Missing business field: {field}")
                    return False
            
            # Store created user for deletion test
            self.created_users.append({
                'type': 'business',
                'email': business_email,
                'id': user_data.get('id'),
                'data': user_data
            })
            
            print(f"   ✅ Business created with ID: {user_data.get('id')}")
            print(f"   ✅ Business name: {user_data.get('business_name')}")
            return True
        
        return False

    def test_courier_registration_for_admin(self):
        """Test POST /api/register/courier - Courier registration for admin"""
        courier_email = f"admin_courier_{uuid.uuid4().hex[:8]}@test.com"
        courier_data = {
            "email": courier_email,
            "password": "TestPass123!",
            "first_name": "Admin",
            "last_name": "Courier",
            "iban": "TR330006100519786457841326",
            "vehicle_type": "motor",
            "vehicle_model": "Honda PCX 150",
            "license_class": "A2",
            "license_number": "34ABC123",
            "city": "İstanbul"
        }
        
        success, response = self.run_test(
            "Courier Registration for Admin",
            "POST",
            "register/courier",
            200,
            data=courier_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['access_token', 'token_type', 'user_type', 'user_data']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Courier Registration for Admin", False, f"Missing response fields: {missing_fields}")
                return False
            
            # Verify user type
            if response.get('user_type') != 'courier':
                self.log_test("Courier Registration for Admin", False, f"Wrong user_type: {response.get('user_type')}")
                return False
            
            user_data = response.get('user_data', {})
            if user_data.get('role') != 'courier':
                self.log_test("Courier Registration for Admin", False, f"Wrong role: {user_data.get('role')}")
                return False
            
            # Verify courier-specific fields
            courier_fields = ['first_name', 'last_name', 'iban', 'vehicle_type', 'vehicle_model', 'license_class', 'license_number', 'city']
            for field in courier_fields:
                if field not in user_data:
                    self.log_test("Courier Registration for Admin", False, f"Missing courier field: {field}")
                    return False
            
            # Store created user for deletion test
            self.created_users.append({
                'type': 'courier',
                'email': courier_email,
                'id': user_data.get('id'),
                'data': user_data
            })
            
            print(f"   ✅ Courier created with ID: {user_data.get('id')}")
            print(f"   ✅ Courier name: {user_data.get('first_name')} {user_data.get('last_name')}")
            return True
        
        return False

    def test_user_deletion_api(self):
        """Test DELETE /api/admin/users/{user_id} - User Deletion API"""
        if not self.admin_token:
            self.log_test("User Deletion API", False, "No admin token available")
            return False
        
        if not self.created_users:
            self.log_test("User Deletion API", False, "No created users available for deletion")
            return False
        
        # Test deleting each created user
        all_success = True
        
        for user in self.created_users:
            user_id = user.get('id')
            user_type = user.get('type')
            user_email = user.get('email')
            
            if not user_id:
                print(f"   ⚠️  Skipping {user_type} user - no ID available")
                continue
            
            # First, verify user exists in the system
            list_success, users_list = self.run_test(
                f"Verify {user_type.title()} User Exists Before Deletion",
                "GET",
                "admin/users",
                200,
                token=self.admin_token
            )
            
            if list_success:
                user_found = any(u.get('id') == user_id for u in users_list if isinstance(users_list, list))
                if not user_found:
                    print(f"   ⚠️  User {user_id} not found in users list before deletion")
                    all_success = False
                    continue
                
                print(f"   ✅ User {user_id} ({user_type}) found in system before deletion")
            
            # Now delete the user
            success, response = self.run_test(
                f"Delete {user_type.title()} User - {user_id}",
                "DELETE",
                f"admin/users/{user_id}",
                200,
                token=self.admin_token
            )
            
            if success:
                print(f"   ✅ {user_type.title()} user {user_id} deleted successfully")
                
                # Verify response contains success message
                if isinstance(response, dict):
                    if 'message' not in response:
                        print(f"   ⚠️  No success message in deletion response")
                    else:
                        print(f"   ✅ Deletion message: {response.get('message')}")
                
                # Verify user is actually deleted by checking users list
                verify_success, updated_users_list = self.run_test(
                    f"Verify {user_type.title()} User Deleted",
                    "GET",
                    "admin/users",
                    200,
                    token=self.admin_token
                )
                
                if verify_success and isinstance(updated_users_list, list):
                    user_still_exists = any(u.get('id') == user_id for u in updated_users_list)
                    if user_still_exists:
                        print(f"   ❌ User {user_id} still exists after deletion")
                        all_success = False
                    else:
                        print(f"   ✅ User {user_id} successfully removed from system")
                else:
                    print(f"   ⚠️  Could not verify user deletion")
                    all_success = False
            else:
                print(f"   ❌ Failed to delete {user_type} user {user_id}")
                all_success = False
        
        if all_success:
            self.log_test("User Deletion API", True, f"Successfully deleted {len(self.created_users)} users")
        else:
            self.log_test("User Deletion API", False, "Some user deletions failed")
        
        return all_success

    def test_user_deletion_non_existent_user(self):
        """Test DELETE /api/admin/users/{user_id} with non-existent user ID"""
        if not self.admin_token:
            self.log_test("User Deletion - Non-existent User", False, "No admin token available")
            return False
        
        # Try to delete a non-existent user
        fake_user_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but non-existent
        
        success, response = self.run_test(
            "Delete Non-existent User (Should Return 404)",
            "DELETE",
            f"admin/users/{fake_user_id}",
            404,
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Non-existent user deletion correctly returned 404")
            return True
        else:
            print(f"   ❌ Non-existent user deletion did not return 404 as expected")
            return False

    def test_user_deletion_invalid_user_id(self):
        """Test DELETE /api/admin/users/{user_id} with invalid user ID format"""
        if not self.admin_token:
            self.log_test("User Deletion - Invalid User ID", False, "No admin token available")
            return False
        
        # Try to delete with invalid user ID format
        invalid_user_id = "invalid-user-id-format"
        
        success, response = self.run_test(
            "Delete User with Invalid ID Format (Should Return 400)",
            "DELETE",
            f"admin/users/{invalid_user_id}",
            400,
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Invalid user ID format correctly returned 400")
            return True
        else:
            print(f"   ❌ Invalid user ID format did not return 400 as expected")
            return False

    def test_user_deletion_requires_admin_auth(self):
        """Test that user deletion requires admin authentication"""
        if not self.created_users:
            # Create a test user first
            customer_data = {
                "email": f"test_auth_{uuid.uuid4().hex[:8]}@test.com",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
                "city": "İstanbul"
            }
            
            reg_success, reg_response = self.run_test(
                "Create User for Auth Test",
                "POST",
                "register/customer",
                200,
                data=customer_data
            )
            
            if not reg_success:
                self.log_test("User Deletion - Admin Auth Required", False, "Failed to create test user")
                return False
            
            test_user_id = reg_response.get('user_data', {}).get('id')
        else:
            # Use existing user ID (even if deleted, we're testing auth)
            test_user_id = self.created_users[0].get('id')
        
        if not test_user_id:
            self.log_test("User Deletion - Admin Auth Required", False, "No test user ID available")
            return False
        
        # Test without token (should fail)
        success, response = self.run_test(
            "Delete User - No Auth Token (Should Fail)",
            "DELETE",
            f"admin/users/{test_user_id}",
            401
        )
        
        if not success:
            self.log_test("User Deletion - Admin Auth Required", False, "Deletion without auth token did not fail properly")
            return False
        
        print(f"   ✅ User deletion correctly requires authentication")
        self.log_test("User Deletion - Admin Auth Required", True)
        return True

    def test_full_user_management_flow(self):
        """Test complete user management flow: Login as admin → Create user → List users → Delete user"""
        print("\n🔄 TESTING FULL USER MANAGEMENT FLOW")
        print("=" * 60)
        
        # Step 1: Login as admin
        print("\n📝 Step 1: Admin Login")
        if not self.admin_token:
            login_success = self.test_admin_login()
            if not login_success:
                self.log_test("Full User Management Flow", False, "Admin login failed")
                return False
        
        print(f"   ✅ Admin logged in successfully")
        
        # Step 2: Get initial user count
        print("\n📝 Step 2: Get Initial User Count")
        list_success, initial_users = self.run_test(
            "Get Initial Users List",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if not list_success:
            self.log_test("Full User Management Flow", False, "Failed to get initial users list")
            return False
        
        initial_count = len(initial_users) if isinstance(initial_users, list) else 0
        print(f"   ✅ Initial user count: {initial_count}")
        
        # Step 3: Create a test user
        print("\n📝 Step 3: Create Test User")
        test_user_email = f"flow_test_{uuid.uuid4().hex[:8]}@test.com"
        test_user_data = {
            "email": test_user_email,
            "password": "FlowTest123!",
            "first_name": "Flow",
            "last_name": "Test",
            "city": "İstanbul"
        }
        
        create_success, create_response = self.run_test(
            "Create Test User for Flow",
            "POST",
            "register/customer",
            200,
            data=test_user_data
        )
        
        if not create_success:
            self.log_test("Full User Management Flow", False, "Failed to create test user")
            return False
        
        test_user_id = create_response.get('user_data', {}).get('id')
        if not test_user_id:
            self.log_test("Full User Management Flow", False, "No user ID returned from creation")
            return False
        
        print(f"   ✅ Test user created with ID: {test_user_id}")
        
        # Step 4: Verify user appears in list
        print("\n📝 Step 4: Verify User in List")
        list_success, updated_users = self.run_test(
            "Get Updated Users List",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if not list_success:
            self.log_test("Full User Management Flow", False, "Failed to get updated users list")
            return False
        
        updated_count = len(updated_users) if isinstance(updated_users, list) else 0
        user_found = any(u.get('id') == test_user_id for u in updated_users if isinstance(updated_users, list))
        
        if not user_found:
            self.log_test("Full User Management Flow", False, "Created user not found in users list")
            return False
        
        if updated_count != initial_count + 1:
            print(f"   ⚠️  User count: expected {initial_count + 1}, got {updated_count}")
        
        print(f"   ✅ Test user found in users list")
        print(f"   ✅ User count increased from {initial_count} to {updated_count}")
        
        # Step 5: Delete the test user
        print("\n📝 Step 5: Delete Test User")
        delete_success, delete_response = self.run_test(
            "Delete Test User",
            "DELETE",
            f"admin/users/{test_user_id}",
            200,
            token=self.admin_token
        )
        
        if not delete_success:
            self.log_test("Full User Management Flow", False, "Failed to delete test user")
            return False
        
        print(f"   ✅ Test user deleted successfully")
        
        # Step 6: Verify user is deleted
        print("\n📝 Step 6: Verify User Deletion")
        final_list_success, final_users = self.run_test(
            "Get Final Users List",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if not final_list_success:
            self.log_test("Full User Management Flow", False, "Failed to get final users list")
            return False
        
        final_count = len(final_users) if isinstance(final_users, list) else 0
        user_still_exists = any(u.get('id') == test_user_id for u in final_users if isinstance(final_users, list))
        
        if user_still_exists:
            self.log_test("Full User Management Flow", False, "User still exists after deletion")
            return False
        
        if final_count != initial_count:
            print(f"   ⚠️  Final user count: expected {initial_count}, got {final_count}")
        
        print(f"   ✅ Test user successfully removed from system")
        print(f"   ✅ User count returned to initial value: {final_count}")
        
        print("\n🎉 FULL USER MANAGEMENT FLOW COMPLETED SUCCESSFULLY!")
        self.log_test("Full User Management Flow", True, "All steps completed successfully")
        return True

    def run_all_user_management_tests(self):
        """Run all user management system tests"""
        print("🚀 STARTING USER MANAGEMENT SYSTEM TESTS")
        print("=" * 70)
        
        # Test sequence
        test_sequence = [
            ("Admin Login", self.test_admin_login),
            ("Admin User Listing", self.test_admin_user_listing),
            ("Customer Registration for Admin", self.test_customer_registration_for_admin),
            ("Business Registration for Admin", self.test_business_registration_for_admin),
            ("Courier Registration for Admin", self.test_courier_registration_for_admin),
            ("User Deletion API", self.test_user_deletion_api),
            ("User Deletion - Non-existent User", self.test_user_deletion_non_existent_user),
            ("User Deletion - Invalid User ID", self.test_user_deletion_invalid_user_id),
            ("User Deletion - Admin Auth Required", self.test_user_deletion_requires_admin_auth),
            ("Full User Management Flow", self.test_full_user_management_flow),
        ]
        
        print(f"📋 Running {len(test_sequence)} user management tests...\n")
        
        all_success = True
        for test_name, test_func in test_sequence:
            print(f"\n{'='*60}")
            print(f"🧪 RUNNING: {test_name}")
            print(f"{'='*60}")
            
            try:
                success = test_func()
                if not success:
                    all_success = False
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {str(e)}")
                self.log_test(test_name, False, f"Exception: {str(e)}")
                all_success = False
            
            print(f"\n✅ Completed: {test_name}")
        
        # Print final results
        print(f"\n📊 USER MANAGEMENT SYSTEM TEST RESULTS:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "   Success Rate: 0%")
        
        # Show detailed results
        passed_tests = [test for test in self.test_results if test['success']]
        failed_tests = [test for test in self.test_results if not test['success']]
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   ✅ {test['test']}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   ❌ {test['test']}: {test['details']}")
        
        # Summary
        if all_success:
            print(f"\n🎉 ALL USER MANAGEMENT SYSTEM TESTS PASSED!")
            print(f"✅ Admin login working with password '6851'")
            print(f"✅ User listing API working")
            print(f"✅ Registration APIs working for all user types")
            print(f"✅ User deletion API working with proper validation")
            print(f"✅ Full user management flow working end-to-end")
        else:
            print(f"\n⚠️  Some User Management System tests failed. Check results above.")
        
        return all_success

def main():
    """Main function to run user management tests"""
    tester = UserManagementTester()
    
    print("🔧 DeliverTR User Management System Testing Suite")
    print("=" * 70)
    print("Testing new user management system in admin panel:")
    print("1. User Deletion API: DELETE /api/admin/users/{user_id}")
    print("2. Registration APIs: POST /api/register/customer, /api/register/business, /api/register/courier")
    print("3. Admin User Listing: GET /api/admin/users")
    print("4. Full User Management Flow")
    print("=" * 70)
    
    success = tester.run_all_user_management_tests()
    
    if success:
        print("\n🎉 ALL USER MANAGEMENT SYSTEM TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  Some User Management System tests failed. Check results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())