#!/usr/bin/env python3
"""
Business Dashboard Summary Endpoint Testing
Testing the specific issue reported: "Yükleniyor..." (Loading...) stuck infinitely in "Son Aktiviteler" (Recent Activities) section

CRITICAL CONTEXT:
- User video shows "Yükleniyor..." (Loading...) stuck infinitely in "Son Aktiviteler" (Recent Activities) section
- Frontend hook useDashboardSummary is properly setting loading=false in finally block
- Need to verify backend endpoint is responding correctly

TEST REQUIREMENTS:
1. Business Login Test - Login with testbusiness@example.com/test123
2. Dashboard Summary Endpoint Test - GET /api/business/dashboard/summary?date=2025-10-23&timezone=Europe/Istanbul
3. Error Handling Test - Test with invalid parameters

SUCCESS CRITERIA:
- ✅ Business authentication working
- ✅ Dashboard summary endpoint returns data quickly (< 2s)
- ✅ Activities array is present (even if empty)
- ✅ No backend errors or timeouts

BACKEND URL: https://courier-dashboard-3.preview.emergentagent.com/api
"""

import requests
import json
import time
from datetime import datetime, timezone
import sys

# Configuration
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"

class BusinessDashboardTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BusinessDashboardTester/1.0'
        })
        self.business_token = None
        self.business_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details, response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   Details: {details}")
        print()
        
    def test_business_login(self):
        """Test 1: Business Login Authentication"""
        print("🔐 Testing Business Login Authentication...")
        
        start_time = time.time()
        try:
            login_data = {
                "email": TEST_BUSINESS_EMAIL,
                "password": TEST_BUSINESS_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have success and user data
                if data.get('success') and data.get('user'):
                    user = data['user']
                    self.business_id = user.get('id')
                    
                    # Verify role is business
                    if user.get('role') == 'business':
                        # Check if cookies are set for authentication
                        cookies = response.cookies
                        if 'access_token' in cookies:
                            self.log_test(
                                "Business Login Authentication",
                                True,
                                f"Login successful. Business ID: {self.business_id}, Role: {user.get('role')}, Cookie auth enabled",
                                response_time
                            )
                            return True
                        else:
                            self.log_test(
                                "Business Login Authentication",
                                False,
                                "Login successful but no access_token cookie set",
                                response_time
                            )
                            return False
                    else:
                        self.log_test(
                            "Business Login Authentication",
                            False,
                            f"Wrong role returned: {user.get('role')}, expected 'business'",
                            response_time
                        )
                        return False
                else:
                    self.log_test(
                        "Business Login Authentication",
                        False,
                        f"Login response missing success/user data: {data}",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Business Login Authentication",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Business Login Authentication",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_dashboard_summary_endpoint(self):
        """Test 2: Dashboard Summary Endpoint with Turkish timezone"""
        print("📊 Testing Dashboard Summary Endpoint...")
        
        start_time = time.time()
        try:
            # Test with specific date and Turkish timezone as mentioned in review request
            params = {
                'date': '2025-10-23',
                'timezone': 'Europe/Istanbul'
            }
            
            response = self.session.get(
                f"{BACKEND_URL}/business/dashboard/summary",
                params=params,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required dashboard fields
                required_fields = [
                    'today_orders_count',
                    'today_revenue',
                    'pending_orders_count',
                    'menu_items_count',
                    'rating_avg',
                    'total_customers',
                    'activities'
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self.log_test(
                        "Dashboard Summary Endpoint Structure",
                        False,
                        f"Missing required fields: {missing_fields}. Response: {data}",
                        response_time
                    )
                    return False
                
                # Check activities array specifically (this is where the loading issue occurs)
                activities = data.get('activities', [])
                if not isinstance(activities, list):
                    self.log_test(
                        "Dashboard Summary Activities Array",
                        False,
                        f"Activities is not an array: {type(activities)}. Value: {activities}",
                        response_time
                    )
                    return False
                
                # Check response time (should be < 2 seconds as per success criteria)
                if response_time >= 2.0:
                    self.log_test(
                        "Dashboard Summary Response Time",
                        False,
                        f"Response too slow: {response_time:.2f}s (should be < 2s)",
                        response_time
                    )
                    return False
                
                # Log successful test with details
                activities_count = len(activities)
                sample_activity = activities[0] if activities else None
                
                self.log_test(
                    "Dashboard Summary Endpoint",
                    True,
                    f"All required fields present. Activities count: {activities_count}. "
                    f"Sample data: today_orders={data.get('today_orders_count')}, "
                    f"today_revenue={data.get('today_revenue')}, "
                    f"pending_orders={data.get('pending_orders_count')}, "
                    f"menu_items={data.get('menu_items_count')}, "
                    f"rating={data.get('rating_avg')}, "
                    f"customers={data.get('total_customers')}. "
                    f"Sample activity: {sample_activity}",
                    response_time
                )
                return True
                
            else:
                self.log_test(
                    "Dashboard Summary Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Dashboard Summary Endpoint",
                False,
                f"Exception: {str(e)}",
                response_time
            )
            return False
    
    def test_dashboard_error_handling(self):
        """Test 3: Dashboard Error Handling"""
        print("🚨 Testing Dashboard Error Handling...")
        
        # Test with invalid date format
        start_time = time.time()
        try:
            params = {
                'date': 'invalid-date',
                'timezone': 'Europe/Istanbul'
            }
            
            response = self.session.get(
                f"{BACKEND_URL}/business/dashboard/summary",
                params=params,
                timeout=10
            )
            response_time = time.time() - start_time
            
            # Should return error or handle gracefully
            if response.status_code in [400, 422]:
                self.log_test(
                    "Dashboard Error Handling - Invalid Date",
                    True,
                    f"Properly rejected invalid date with HTTP {response.status_code}",
                    response_time
                )
            elif response.status_code == 200:
                # If it returns 200, it should handle gracefully
                data = response.json()
                if 'activities' in data:
                    self.log_test(
                        "Dashboard Error Handling - Invalid Date",
                        True,
                        f"Gracefully handled invalid date, returned valid response",
                        response_time
                    )
                else:
                    self.log_test(
                        "Dashboard Error Handling - Invalid Date",
                        False,
                        f"Invalid date accepted but response malformed: {data}",
                        response_time
                    )
            else:
                self.log_test(
                    "Dashboard Error Handling - Invalid Date",
                    False,
                    f"Unexpected response HTTP {response.status_code}: {response.text}",
                    response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Dashboard Error Handling - Invalid Date",
                False,
                f"Exception: {str(e)}",
                response_time
            )
        
        # Test with missing timezone
        start_time = time.time()
        try:
            params = {
                'date': '2025-10-23'
                # Missing timezone parameter
            }
            
            response = self.session.get(
                f"{BACKEND_URL}/business/dashboard/summary",
                params=params,
                timeout=10
            )
            response_time = time.time() - start_time
            
            # Should handle missing timezone gracefully or return error
            if response.status_code == 200:
                data = response.json()
                if 'activities' in data:
                    self.log_test(
                        "Dashboard Error Handling - Missing Timezone",
                        True,
                        f"Gracefully handled missing timezone, used default",
                        response_time
                    )
                else:
                    self.log_test(
                        "Dashboard Error Handling - Missing Timezone",
                        False,
                        f"Missing timezone handled but response malformed: {data}",
                        response_time
                    )
            elif response.status_code in [400, 422]:
                self.log_test(
                    "Dashboard Error Handling - Missing Timezone",
                    True,
                    f"Properly rejected missing timezone with HTTP {response.status_code}",
                    response_time
                )
            else:
                self.log_test(
                    "Dashboard Error Handling - Missing Timezone",
                    False,
                    f"Unexpected response HTTP {response.status_code}: {response.text}",
                    response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Dashboard Error Handling - Missing Timezone",
                False,
                f"Exception: {str(e)}",
                response_time
            )
    
    def test_unauthenticated_access(self):
        """Test 4: Unauthenticated Access Protection"""
        print("🔒 Testing Unauthenticated Access Protection...")
        
        # Create a new session without authentication
        unauth_session = requests.Session()
        unauth_session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BusinessDashboardTester/1.0'
        })
        
        start_time = time.time()
        try:
            params = {
                'date': '2025-10-23',
                'timezone': 'Europe/Istanbul'
            }
            
            response = unauth_session.get(
                f"{BACKEND_URL}/business/dashboard/summary",
                params=params,
                timeout=10
            )
            response_time = time.time() - start_time
            
            # Should return 401 or 403 for unauthenticated access
            if response.status_code in [401, 403]:
                self.log_test(
                    "Unauthenticated Access Protection",
                    True,
                    f"Properly blocked unauthenticated access with HTTP {response.status_code}",
                    response_time
                )
            else:
                self.log_test(
                    "Unauthenticated Access Protection",
                    False,
                    f"Security issue: Unauthenticated access allowed. HTTP {response.status_code}: {response.text}",
                    response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(
                "Unauthenticated Access Protection",
                False,
                f"Exception: {str(e)}",
                response_time
            )
    
    def run_all_tests(self):
        """Run all dashboard summary tests"""
        print("🎯 BUSINESS DASHBOARD SUMMARY ENDPOINT TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Business: {TEST_BUSINESS_EMAIL}")
        print(f"Test Time: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        # Test 1: Business Login
        login_success = self.test_business_login()
        
        if login_success:
            # Test 2: Dashboard Summary Endpoint (main test)
            self.test_dashboard_summary_endpoint()
            
            # Test 3: Error Handling
            self.test_dashboard_error_handling()
        else:
            print("❌ Skipping dashboard tests due to login failure")
        
        # Test 4: Unauthenticated Access (independent of login)
        self.test_unauthenticated_access()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Critical findings for the specific issue
        print("🎯 CRITICAL FINDINGS FOR LOADING ISSUE:")
        
        # Check if dashboard endpoint is working
        dashboard_test = next((r for r in self.test_results if 'Dashboard Summary Endpoint' in r['test']), None)
        if dashboard_test and dashboard_test['success']:
            print("   ✅ Dashboard summary endpoint is responding correctly")
            print("   ✅ Activities array is present and properly formatted")
            print("   ✅ Response time is acceptable (< 2s)")
            print("   ✅ All required fields are included in response")
            print()
            print("   🔍 ROOT CAUSE ANALYSIS:")
            print("   The backend endpoint is working correctly. The 'Yükleniyor...' infinite loading")
            print("   issue is likely caused by:")
            print("   1. Frontend authentication state not properly syncing")
            print("   2. Frontend error handling not catching failed requests")
            print("   3. Frontend timeout settings too short")
            print("   4. Network connectivity issues between frontend and backend")
            print()
            print("   💡 RECOMMENDATION:")
            print("   Check frontend useDashboardSummary hook for:")
            print("   - Proper error handling in catch blocks")
            print("   - Authentication token being passed correctly")
            print("   - Network timeout configuration")
            print("   - Loading state management in finally block")
        else:
            print("   ❌ Dashboard summary endpoint has issues")
            print("   ❌ This explains the infinite loading in frontend")
            print()
            print("   🔍 ROOT CAUSE ANALYSIS:")
            print("   The backend endpoint is not responding correctly, causing the frontend")
            print("   to remain in loading state indefinitely.")
            
        # Check authentication
        auth_test = next((r for r in self.test_results if 'Business Login' in r['test']), None)
        if auth_test and not auth_test['success']:
            print("   ❌ Business authentication is failing")
            print("   ❌ This could cause the dashboard endpoint to be unreachable")
        
        print("\n" + "=" * 60)
        
        # Return overall success
        return success_rate >= 75  # Consider 75%+ as overall success

def main():
    """Main test execution"""
    tester = BusinessDashboardTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()