#!/usr/bin/env python3
"""
ADDRESS AUTHENTICATION DEBUG TEST
Focus: Test different authentication scenarios that might cause "Adres ekleme hatası"
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-stable.preview.emergentagent.com/api"

class AddressAuthDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, details, error=None):
        """Log test result with detailed information"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if error:
            print(f"   🚨 ERROR: {error}")
        print()

    def test_no_auth_token(self):
        """Test address creation without authentication token"""
        print("🚫 TEST: NO AUTHENTICATION TOKEN")
        print("=" * 50)
        
        # Clear any existing auth headers
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        test_address = {
            "label": "No Auth Test",
            "city": "İstanbul",
            "district": "Kadıköy",
            "description": "Test without authentication",
            "lat": 40.9903,
            "lng": 29.0209
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/user/addresses", json=test_address)
            
            if response.status_code == 401:
                self.log_result(
                    "No Auth Token Test",
                    True,
                    "Correctly rejected with 401 Unauthorized"
                )
            elif response.status_code == 403:
                self.log_result(
                    "No Auth Token Test",
                    True,
                    "Correctly rejected with 403 Forbidden"
                )
            else:
                self.log_result(
                    "No Auth Token Test",
                    False,
                    f"Unexpected response - Status: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result("No Auth Token Test", False, "Request failed", e)

    def test_invalid_auth_token(self):
        """Test address creation with invalid authentication token"""
        print("🔒 TEST: INVALID AUTHENTICATION TOKEN")
        print("=" * 50)
        
        # Set invalid auth token
        invalid_tokens = [
            "Bearer invalid_token",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "Bearer expired_token_here",
            "InvalidFormat",
            ""
        ]
        
        test_address = {
            "label": "Invalid Auth Test",
            "city": "İstanbul",
            "district": "Kadıköy",
            "description": "Test with invalid authentication",
            "lat": 40.9903,
            "lng": 29.0209
        }
        
        for i, token in enumerate(invalid_tokens):
            try:
                headers = {"Authorization": token} if token else {}
                response = requests.post(f"{BACKEND_URL}/user/addresses", json=test_address, headers=headers)
                
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"Invalid Auth Token Test #{i+1}",
                        True,
                        f"Correctly rejected with {response.status_code} - Token: {token[:20]}..."
                    )
                else:
                    self.log_result(
                        f"Invalid Auth Token Test #{i+1}",
                        False,
                        f"Unexpected response - Status: {response.status_code} - Token: {token[:20]}...",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(f"Invalid Auth Token Test #{i+1}", False, "Request failed", e)

    def test_different_user_roles(self):
        """Test address creation with different user roles"""
        print("👥 TEST: DIFFERENT USER ROLES")
        print("=" * 50)
        
        # Test users with different roles
        test_users = [
            {"email": "testcustomer@example.com", "password": "test123", "expected_role": "customer", "should_work": True},
            {"email": "testbusiness@example.com", "password": "test123", "expected_role": "business", "should_work": False},
            {"email": "testkurye@example.com", "password": "test123", "expected_role": "courier", "should_work": False},
            {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!", "expected_role": "admin", "should_work": False},
        ]
        
        for user in test_users:
            try:
                # Login as user
                login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if login_response.status_code != 200:
                    self.log_result(
                        f"Role Test - {user['expected_role']} Login",
                        False,
                        f"Login failed - Status: {login_response.status_code}",
                        login_response.text
                    )
                    continue
                
                login_data = login_response.json()
                token = login_data.get("access_token")
                actual_role = login_data.get("user", {}).get("role")
                
                # Test address creation
                test_address = {
                    "label": f"Role Test - {user['expected_role']}",
                    "city": "İstanbul",
                    "district": "Kadıköy",
                    "description": f"Test with {user['expected_role']} role",
                    "lat": 40.9903,
                    "lng": 29.0209
                }
                
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.post(f"{BACKEND_URL}/user/addresses", json=test_address, headers=headers)
                
                if user["should_work"]:
                    if response.status_code in [200, 201]:
                        self.log_result(
                            f"Role Test - {user['expected_role']} Address Creation",
                            True,
                            f"Address creation successful for {actual_role} role"
                        )
                    else:
                        self.log_result(
                            f"Role Test - {user['expected_role']} Address Creation",
                            False,
                            f"Address creation failed for {actual_role} role - Status: {response.status_code}",
                            response.text
                        )
                else:
                    if response.status_code in [403, 401]:
                        self.log_result(
                            f"Role Test - {user['expected_role']} Address Creation",
                            True,
                            f"Address creation correctly rejected for {actual_role} role"
                        )
                    else:
                        self.log_result(
                            f"Role Test - {user['expected_role']} Address Creation",
                            False,
                            f"Address creation should be rejected for {actual_role} role - Status: {response.status_code}",
                            response.text
                        )
                        
            except Exception as e:
                self.log_result(f"Role Test - {user['expected_role']}", False, "Request failed", e)

    def test_malformed_requests(self):
        """Test address creation with malformed requests"""
        print("🔧 TEST: MALFORMED REQUESTS")
        print("=" * 50)
        
        # First login as customer
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        
        if login_response.status_code != 200:
            self.log_result("Malformed Request Setup", False, "Could not login for malformed request tests", login_response.text)
            return
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test malformed requests
        malformed_tests = [
            {"name": "Empty JSON", "data": {}},
            {"name": "Null Data", "data": None},
            {"name": "String Instead of Object", "data": "invalid"},
            {"name": "Array Instead of Object", "data": []},
            {"name": "Invalid JSON Structure", "data": {"nested": {"invalid": "structure"}}},
            {"name": "Very Long Strings", "data": {
                "label": "A" * 1000,
                "city": "B" * 1000,
                "description": "C" * 10000
            }},
            {"name": "Special Characters", "data": {
                "label": "Test<script>alert('xss')</script>",
                "city": "İstanbul'\"<>&",
                "description": "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
            }},
        ]
        
        for test in malformed_tests:
            try:
                if test["data"] is None:
                    # Test with no JSON body
                    response = requests.post(f"{BACKEND_URL}/user/addresses", headers=headers)
                else:
                    response = requests.post(f"{BACKEND_URL}/user/addresses", json=test["data"], headers=headers)
                
                if response.status_code == 422:
                    self.log_result(
                        f"Malformed Request - {test['name']}",
                        True,
                        "Correctly rejected with 422 Validation Error"
                    )
                elif response.status_code == 400:
                    self.log_result(
                        f"Malformed Request - {test['name']}",
                        True,
                        "Correctly rejected with 400 Bad Request"
                    )
                elif response.status_code in [200, 201]:
                    self.log_result(
                        f"Malformed Request - {test['name']}",
                        True,
                        "Request accepted (lenient validation)"
                    )
                else:
                    self.log_result(
                        f"Malformed Request - {test['name']}",
                        False,
                        f"Unexpected response - Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(f"Malformed Request - {test['name']}", False, "Request failed", e)

    def test_concurrent_requests(self):
        """Test concurrent address creation requests"""
        print("⚡ TEST: CONCURRENT REQUESTS")
        print("=" * 50)
        
        # Login first
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        
        if login_response.status_code != 200:
            self.log_result("Concurrent Request Setup", False, "Could not login for concurrent tests", login_response.text)
            return
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple requests quickly
        import threading
        import time
        
        results = []
        
        def create_address(index):
            test_address = {
                "label": f"Concurrent Test {index}",
                "city": "İstanbul",
                "district": "Kadıköy",
                "description": f"Concurrent test address {index}",
                "lat": 40.9903 + (index * 0.001),  # Slightly different coordinates
                "lng": 29.0209 + (index * 0.001)
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/user/addresses", json=test_address, headers=headers)
                results.append({
                    "index": index,
                    "status": response.status_code,
                    "success": response.status_code in [200, 201]
                })
            except Exception as e:
                results.append({
                    "index": index,
                    "status": "error",
                    "success": False,
                    "error": str(e)
                })
        
        # Create 5 concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_address, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful = len([r for r in results if r["success"]])
        total = len(results)
        
        if successful == total:
            self.log_result(
                "Concurrent Requests Test",
                True,
                f"All {total} concurrent requests successful"
            )
        else:
            self.log_result(
                "Concurrent Requests Test",
                False,
                f"Only {successful}/{total} concurrent requests successful",
                str(results)
            )

    def run_all_tests(self):
        """Run all authentication debug tests"""
        print("🚨 ADDRESS AUTHENTICATION DEBUG TESTS")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_no_auth_token()
        self.test_invalid_auth_token()
        self.test_different_user_roles()
        self.test_malformed_requests()
        self.test_concurrent_requests()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🔍 ADDRESS AUTHENTICATION DEBUG SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failures
        failures = [r for r in self.test_results if not r["success"]]
        if failures:
            print("❌ FAILED TESTS:")
            for failure in failures:
                print(f"   • {failure['test']}: {failure['error']}")
            print()
        
        print("=" * 60)

if __name__ == "__main__":
    tester = AddressAuthDebugTester()
    tester.run_all_tests()