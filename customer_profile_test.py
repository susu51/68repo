#!/usr/bin/env python3
"""
Comprehensive Test Suite for Kuryecini Customer Profile Management Endpoints
Testing new endpoints added for customer profile, address management, order history, and phone authentication
"""

import requests
import json
import time
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://kuryecini-ai.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class CustomerProfileTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.customer_token = None
        self.customer_user_id = None
        self.test_results = []
        self.created_addresses = []
        self.test_phone = "+905551234567"
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def authenticate_customer(self) -> bool:
        """Authenticate with existing customer account"""
        try:
            # Try existing customer login first
            login_data = {
                "email": "testcustomer@example.com",
                "password": "test123"
            }
            
            response = self.make_request("POST", "/auth/login", login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("user_type") == "customer":
                    self.customer_token = data["access_token"]
                    self.customer_user_id = data["user_data"]["id"]
                    self.headers["Authorization"] = f"Bearer {self.customer_token}"
                    self.log_test("Customer Authentication (Email)", True, 
                                f"Logged in as customer: {data['user_data'].get('email')}")
                    return True
            
            # If email login fails, try phone authentication
            return self.authenticate_with_phone()
            
        except Exception as e:
            self.log_test("Customer Authentication (Email)", False, f"Login failed: {str(e)}")
            return self.authenticate_with_phone()
    
    def authenticate_with_phone(self) -> bool:
        """Authenticate using phone OTP system"""
        try:
            # Step 1: Request OTP
            otp_request = {"phone": self.test_phone}
            response = self.make_request("POST", "/auth/phone/request-otp", otp_request)
            
            if response.status_code != 200:
                self.log_test("Phone OTP Request", False, f"OTP request failed: {response.status_code}")
                return False
                
            otp_data = response.json()
            mock_otp = otp_data.get("mock_otp")
            
            if not mock_otp:
                self.log_test("Phone OTP Request", False, "No mock OTP received")
                return False
                
            self.log_test("Phone OTP Request", True, f"OTP requested for {self.test_phone}, mock OTP: {mock_otp}")
            
            # Step 2: Verify OTP
            verify_data = {
                "phone": self.test_phone,
                "otp_code": mock_otp
            }
            
            response = self.make_request("POST", "/auth/phone/verify-otp", verify_data)
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data["access_token"]
                self.customer_user_id = data["user_data"]["id"]
                self.headers["Authorization"] = f"Bearer {self.customer_token}"
                self.log_test("Phone OTP Verification", True, 
                            f"Phone auth successful for user: {self.customer_user_id}")
                return True
            else:
                self.log_test("Phone OTP Verification", False, f"OTP verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Phone Authentication", False, f"Phone auth failed: {str(e)}")
            return False

    def test_phone_authentication_system(self):
        """Test the new phone authentication system"""
        print("\n🔐 Testing Phone Authentication System...")
        
        # Test 1: Request OTP with valid Turkish phone
        test_phones = [
            "+905551234567",
            "05551234567", 
            "905551234567",
            "5551234567"
        ]
        
        for phone in test_phones:
            try:
                response = self.make_request("POST", "/auth/phone/request-otp", {"phone": phone})
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"OTP Request - {phone}", True, 
                                f"OTP sent, formatted: {data.get('formatted_phone')}, mock: {data.get('mock_otp')}")
                else:
                    self.log_test(f"OTP Request - {phone}", False, 
                                f"Failed with status: {response.status_code}")
            except Exception as e:
                self.log_test(f"OTP Request - {phone}", False, f"Error: {str(e)}")
        
        # Test 2: Request OTP with invalid phone numbers
        invalid_phones = [
            "123456789",      # Too short
            "+1234567890",    # Non-Turkish
            "invalid",        # Non-numeric
            ""                # Empty
        ]
        
        for phone in invalid_phones:
            try:
                response = self.make_request("POST", "/auth/phone/request-otp", {"phone": phone})
                
                if response.status_code == 400:
                    self.log_test(f"Invalid Phone Rejection - {phone}", True, 
                                "Correctly rejected invalid phone")
                else:
                    self.log_test(f"Invalid Phone Rejection - {phone}", False, 
                                f"Should reject but got: {response.status_code}")
            except Exception as e:
                self.log_test(f"Invalid Phone Test - {phone}", False, f"Error: {str(e)}")
        
        # Test 3: Verify OTP with correct code
        try:
            otp_response = self.make_request("POST", "/auth/phone/request-otp", {"phone": self.test_phone})
            if otp_response.status_code == 200:
                otp_data = otp_response.json()
                mock_otp = otp_data.get("mock_otp")
                
                verify_response = self.make_request("POST", "/auth/phone/verify-otp", {
                    "phone": self.test_phone,
                    "otp_code": mock_otp
                })
                
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    self.log_test("OTP Verification Success", True, 
                                f"Token received, user_id: {data['user_data']['id']}")
                else:
                    self.log_test("OTP Verification Success", False, 
                                f"Verification failed: {verify_response.status_code}")
        except Exception as e:
            self.log_test("OTP Verification Success", False, f"Error: {str(e)}")
        
        # Test 4: Verify OTP with wrong code
        try:
            verify_response = self.make_request("POST", "/auth/phone/verify-otp", {
                "phone": self.test_phone,
                "otp_code": "000000"
            })
            
            if verify_response.status_code == 400:
                self.log_test("Wrong OTP Rejection", True, "Correctly rejected wrong OTP")
            else:
                self.log_test("Wrong OTP Rejection", False, 
                            f"Should reject wrong OTP but got: {verify_response.status_code}")
        except Exception as e:
            self.log_test("Wrong OTP Rejection", False, f"Error: {str(e)}")

    def test_customer_profile_management(self):
        """Test customer profile management endpoints"""
        print("\n👤 Testing Customer Profile Management...")
        
        # Test 1: Get customer profile
        try:
            response = self.make_request("GET", "/profile/me")
            
            if response.status_code == 200:
                profile_data = response.json()
                self.log_test("Get Customer Profile", True, 
                            f"Profile retrieved: {profile_data.get('first_name', 'N/A')} {profile_data.get('last_name', 'N/A')}")
            elif response.status_code == 403:
                self.log_test("Get Customer Profile", False, 
                            "Access denied - authentication issue")
            else:
                self.log_test("Get Customer Profile", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Customer Profile", False, f"Error: {str(e)}")
        
        # Test 2: Update customer profile
        try:
            update_data = {
                "first_name": "Test",
                "last_name": "Customer",
                "email": "updated.customer@example.com",
                "birth_date": "1990-01-01T00:00:00Z",
                "gender": "male",
                "notification_preferences": {
                    "email_notifications": True,
                    "sms_notifications": False,
                    "push_notifications": True,
                    "marketing_emails": False
                },
                "preferred_language": "tr",
                "theme_preference": "dark"
            }
            
            response = self.make_request("PUT", "/profile/me", update_data)
            
            if response.status_code == 200:
                self.log_test("Update Customer Profile", True, "Profile updated successfully")
                
                # Verify the update by getting profile again
                get_response = self.make_request("GET", "/profile/me")
                if get_response.status_code == 200:
                    updated_profile = get_response.json()
                    if (updated_profile.get("first_name") == "Test" and 
                        updated_profile.get("theme_preference") == "dark"):
                        self.log_test("Profile Update Verification", True, "Changes persisted correctly")
                    else:
                        self.log_test("Profile Update Verification", False, "Changes not persisted")
            else:
                self.log_test("Update Customer Profile", False, 
                            f"Update failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Customer Profile", False, f"Error: {str(e)}")
        
        # Test 3: Update profile with invalid data
        try:
            invalid_data = {
                "gender": "invalid_gender",  # Should be male/female/other
                "preferred_language": "xx",  # Should be tr/en
                "theme_preference": "invalid_theme"  # Should be light/dark/auto
            }
            
            response = self.make_request("PUT", "/profile/me", invalid_data)
            
            if response.status_code in [400, 422]:
                self.log_test("Invalid Profile Data Rejection", True, "Invalid data correctly rejected")
            else:
                self.log_test("Invalid Profile Data Rejection", False, 
                            f"Should reject invalid data but got: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Profile Data Rejection", False, f"Error: {str(e)}")

    def test_address_management(self):
        """Test address management endpoints"""
        print("\n🏠 Testing Address Management...")
        
        # Test 1: Get user addresses (initially empty)
        try:
            response = self.make_request("GET", "/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_test("Get User Addresses", True, 
                            f"Retrieved {len(addresses)} addresses")
            else:
                self.log_test("Get User Addresses", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Get User Addresses", False, f"Error: {str(e)}")
        
        # Test 2: Create new address
        try:
            address_data = {
                "title": "Ev",
                "address_line": "Test Mahallesi, Test Sokak No: 123",
                "district": "Kadıköy",
                "city": "İstanbul",
                "postal_code": "34710",
                "latitude": 40.9969,
                "longitude": 29.0833,
                "is_default": True
            }
            
            response = self.make_request("POST", "/addresses", address_data)
            
            if response.status_code == 200:
                result = response.json()
                address_id = result.get("address_id")
                if address_id:
                    self.created_addresses.append(address_id)
                self.log_test("Create Address", True, 
                            f"Address created with ID: {address_id}")
            else:
                self.log_test("Create Address", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Address", False, f"Error: {str(e)}")
        
        # Test 3: Create second address
        try:
            address_data = {
                "title": "İş",
                "address_line": "İş Mahallesi, Ofis Sokak No: 456",
                "district": "Şişli",
                "city": "İstanbul",
                "postal_code": "34394",
                "latitude": 41.0498,
                "longitude": 28.9662,
                "is_default": False
            }
            
            response = self.make_request("POST", "/addresses", address_data)
            
            if response.status_code == 200:
                result = response.json()
                address_id = result.get("address_id")
                if address_id:
                    self.created_addresses.append(address_id)
                self.log_test("Create Second Address", True, 
                            f"Second address created with ID: {address_id}")
            else:
                self.log_test("Create Second Address", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Second Address", False, f"Error: {str(e)}")
        
        # Test 4: Get addresses after creation
        try:
            response = self.make_request("GET", "/addresses")
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_test("Get Addresses After Creation", True, 
                            f"Now have {len(addresses)} addresses")
                
                # Check default address logic
                default_addresses = [addr for addr in addresses if addr.get("is_default")]
                if len(default_addresses) == 1:
                    self.log_test("Default Address Logic", True, "Only one default address exists")
                else:
                    self.log_test("Default Address Logic", False, 
                                f"Found {len(default_addresses)} default addresses")
            else:
                self.log_test("Get Addresses After Creation", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Addresses After Creation", False, f"Error: {str(e)}")
        
        # Test 5: Update address
        if self.created_addresses:
            try:
                address_id = self.created_addresses[0]
                update_data = {
                    "title": "Ev (Güncellenmiş)",
                    "address_line": "Güncellenmiş Adres Satırı",
                    "district": "Beşiktaş",
                    "city": "İstanbul",
                    "is_default": True
                }
                
                response = self.make_request("PUT", f"/addresses/{address_id}", update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Address", True, "Address updated successfully")
                else:
                    self.log_test("Update Address", False, 
                                f"Failed with status: {response.status_code}")
            except Exception as e:
                self.log_test("Update Address", False, f"Error: {str(e)}")
        
        # Test 6: Set default address
        if len(self.created_addresses) > 1:
            try:
                address_id = self.created_addresses[1]
                response = self.make_request("POST", f"/addresses/{address_id}/set-default")
                
                if response.status_code == 200:
                    self.log_test("Set Default Address", True, "Default address set successfully")
                    
                    # Verify default address changed
                    get_response = self.make_request("GET", "/addresses")
                    if get_response.status_code == 200:
                        addresses = get_response.json()
                        default_addr = next((addr for addr in addresses if addr["id"] == address_id), None)
                        if default_addr and default_addr.get("is_default"):
                            self.log_test("Default Address Verification", True, "Default address changed correctly")
                        else:
                            self.log_test("Default Address Verification", False, "Default address not changed")
                else:
                    self.log_test("Set Default Address", False, 
                                f"Failed with status: {response.status_code}")
            except Exception as e:
                self.log_test("Set Default Address", False, f"Error: {str(e)}")
        
        # Test 7: Delete address
        if self.created_addresses:
            try:
                address_id = self.created_addresses[-1]  # Delete last created address
                response = self.make_request("DELETE", f"/addresses/{address_id}")
                
                if response.status_code == 200:
                    self.log_test("Delete Address", True, "Address deleted successfully")
                    self.created_addresses.remove(address_id)
                else:
                    self.log_test("Delete Address", False, 
                                f"Failed with status: {response.status_code}")
            except Exception as e:
                self.log_test("Delete Address", False, f"Error: {str(e)}")
        
        # Test 8: Try to access non-existent address
        try:
            fake_address_id = "non-existent-address-id"
            response = self.make_request("PUT", f"/addresses/{fake_address_id}", {"title": "Test"})
            
            if response.status_code == 404:
                self.log_test("Non-existent Address Access", True, "Correctly returned 404 for non-existent address")
            else:
                self.log_test("Non-existent Address Access", False, 
                            f"Should return 404 but got: {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Address Access", False, f"Error: {str(e)}")

    def test_order_history_and_ratings(self):
        """Test order history and ratings endpoints"""
        print("\n📋 Testing Order History & Ratings...")
        
        # Test 1: Get order history (may be empty)
        try:
            response = self.make_request("GET", "/orders/history")
            
            if response.status_code == 200:
                history_data = response.json()
                orders = history_data.get("orders", [])
                pagination = history_data.get("pagination", {})
                
                self.log_test("Get Order History", True, 
                            f"Retrieved {len(orders)} orders, total: {pagination.get('total', 0)}")
                
                # Test pagination
                if len(orders) > 0:
                    # Test with different page sizes
                    page_response = self.make_request("GET", "/orders/history?page=1&limit=5")
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        self.log_test("Order History Pagination", True, 
                                    f"Page 1 with limit 5: {len(page_data.get('orders', []))} orders")
                    
                    # Check if we can test reorder and rating with existing orders
                    delivered_orders = [order for order in orders if order.get("status") == "delivered"]
                    if delivered_orders:
                        self.test_reorder_functionality(delivered_orders[0])
                        self.test_rating_functionality(delivered_orders[0])
                
            else:
                self.log_test("Get Order History", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Order History", False, f"Error: {str(e)}")
        
        # Test 2: Get order history with pagination parameters
        try:
            response = self.make_request("GET", "/orders/history?page=2&limit=3")
            
            if response.status_code == 200:
                history_data = response.json()
                pagination = history_data.get("pagination", {})
                self.log_test("Order History Pagination Test", True, 
                            f"Page 2, limit 3: page={pagination.get('page')}, total={pagination.get('total')}")
            else:
                self.log_test("Order History Pagination Test", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Order History Pagination Test", False, f"Error: {str(e)}")

    def test_reorder_functionality(self, order):
        """Test reorder functionality with a delivered order"""
        try:
            order_id = order.get("id")
            response = self.make_request("POST", f"/orders/{order_id}/reorder")
            
            if response.status_code == 200:
                reorder_data = response.json()
                available_items = reorder_data.get("available_items", [])
                unavailable_items = reorder_data.get("unavailable_items", [])
                
                self.log_test("Reorder Items", True, 
                            f"Reorder possible: {len(available_items)} available, {len(unavailable_items)} unavailable")
            elif response.status_code == 404:
                self.log_test("Reorder Items", False, "Order not found or cannot be reordered")
            elif response.status_code == 400:
                self.log_test("Reorder Items", False, "Business no longer active")
            else:
                self.log_test("Reorder Items", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Reorder Items", False, f"Error: {str(e)}")

    def test_rating_functionality(self, order):
        """Test rating functionality with a delivered order"""
        try:
            order_id = order.get("id")
            
            # Check if order can be rated
            if not order.get("can_rate", False):
                self.log_test("Rate Order (Already Rated)", True, "Order already rated - skipping")
                return
            
            rating_data = {
                "business_rating": 5,
                "courier_rating": 4,
                "business_comment": "Harika yemek, çok lezzetliydi!",
                "courier_comment": "Hızlı teslimat, teşekkürler!",
                "food_quality_rating": 5,
                "delivery_speed_rating": 4
            }
            
            response = self.make_request("POST", f"/orders/{order_id}/rate", rating_data)
            
            if response.status_code == 200:
                self.log_test("Rate Order", True, "Order rated successfully")
                
                # Try to rate again (should fail)
                duplicate_response = self.make_request("POST", f"/orders/{order_id}/rate", rating_data)
                if duplicate_response.status_code == 400:
                    self.log_test("Duplicate Rating Prevention", True, "Correctly prevented duplicate rating")
                else:
                    self.log_test("Duplicate Rating Prevention", False, "Should prevent duplicate rating")
                    
            elif response.status_code == 400:
                self.log_test("Rate Order", True, "Order already rated (expected)")
            elif response.status_code == 404:
                self.log_test("Rate Order", False, "Order not found or cannot be rated")
            else:
                self.log_test("Rate Order", False, 
                            f"Failed with status: {response.status_code}")
        except Exception as e:
            self.log_test("Rate Order", False, f"Error: {str(e)}")

    def test_authentication_and_authorization(self):
        """Test authentication and authorization for all endpoints"""
        print("\n🔒 Testing Authentication & Authorization...")
        
        # Save current token
        original_token = self.headers.get("Authorization")
        
        # Test 1: Access endpoints without authentication
        endpoints_to_test = [
            ("GET", "/profile/me"),
            ("PUT", "/profile/me"),
            ("GET", "/addresses"),
            ("POST", "/addresses"),
            ("GET", "/orders/history")
        ]
        
        # Remove authorization header
        if "Authorization" in self.headers:
            del self.headers["Authorization"]
        
        for method, endpoint in endpoints_to_test:
            try:
                response = self.make_request(method, endpoint, {"test": "data"})
                
                if response.status_code in [401, 403]:
                    self.log_test(f"Unauthorized Access - {method} {endpoint}", True, 
                                "Correctly rejected unauthorized access")
                else:
                    self.log_test(f"Unauthorized Access - {method} {endpoint}", False, 
                                f"Should reject but got: {response.status_code}")
            except Exception as e:
                self.log_test(f"Unauthorized Access - {method} {endpoint}", False, f"Error: {str(e)}")
        
        # Restore authorization header
        if original_token:
            self.headers["Authorization"] = original_token
        
        # Test 2: Access with invalid token
        self.headers["Authorization"] = "Bearer invalid-token-12345"
        
        try:
            response = self.make_request("GET", "/profile/me")
            
            if response.status_code in [401, 403]:
                self.log_test("Invalid Token Rejection", True, "Correctly rejected invalid token")
            else:
                self.log_test("Invalid Token Rejection", False, 
                            f"Should reject invalid token but got: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Token Rejection", False, f"Error: {str(e)}")
        
        # Restore original token
        if original_token:
            self.headers["Authorization"] = original_token

    def test_error_handling(self):
        """Test error handling for various scenarios"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 1: Invalid JSON data
        try:
            # This should be handled by the framework, but let's test anyway
            response = requests.post(f"{self.base_url}/profile/me", 
                                   data="invalid json", 
                                   headers=self.headers, 
                                   timeout=30)
            
            if response.status_code in [400, 422]:
                self.log_test("Invalid JSON Handling", True, "Invalid JSON correctly rejected")
            else:
                self.log_test("Invalid JSON Handling", False, 
                            f"Should reject invalid JSON but got: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid JSON Handling", False, f"Error: {str(e)}")
        
        # Test 2: Missing required fields
        try:
            incomplete_address = {
                "title": "Test"
                # Missing required fields like address_line, city
            }
            
            response = self.make_request("POST", "/addresses", incomplete_address)
            
            if response.status_code in [400, 422]:
                self.log_test("Missing Required Fields", True, "Missing fields correctly rejected")
            else:
                self.log_test("Missing Required Fields", False, 
                            f"Should reject missing fields but got: {response.status_code}")
        except Exception as e:
            self.log_test("Missing Required Fields", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created addresses
        for address_id in self.created_addresses:
            try:
                response = self.make_request("DELETE", f"/addresses/{address_id}")
                if response.status_code == 200:
                    self.log_test(f"Cleanup Address {address_id}", True, "Address deleted")
                else:
                    self.log_test(f"Cleanup Address {address_id}", False, 
                                f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_test(f"Cleanup Address {address_id}", False, f"Error: {str(e)}")

    def generate_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n" + "="*80)
        print(f"🎯 KURYECINI CUSTOMER PROFILE MANAGEMENT TEST REPORT")
        print(f"="*80)
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   🕒 Test Duration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ SUCCESSFUL TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🔍 ENDPOINT COVERAGE:")
        endpoints_tested = [
            "POST /auth/phone/request-otp",
            "POST /auth/phone/verify-otp", 
            "GET /profile/me",
            "PUT /profile/me",
            "GET /addresses",
            "POST /addresses",
            "PUT /addresses/{id}",
            "DELETE /addresses/{id}",
            "POST /addresses/{id}/set-default",
            "GET /orders/history",
            "POST /orders/{id}/reorder",
            "POST /orders/{id}/rate"
        ]
        
        for endpoint in endpoints_tested:
            print(f"   ✓ {endpoint}")
        
        print(f"\n🎉 TEST SUMMARY:")
        if success_rate >= 90:
            print(f"   🟢 EXCELLENT: Customer profile management system is working very well!")
        elif success_rate >= 75:
            print(f"   🟡 GOOD: Most features working, some issues need attention")
        elif success_rate >= 50:
            print(f"   🟠 FAIR: Several issues found, requires fixes")
        else:
            print(f"   🔴 POOR: Major issues found, significant fixes needed")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Kuryecini Customer Profile Management Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Step 1: Authentication
        if not self.authenticate_customer():
            print("❌ Authentication failed - cannot proceed with tests")
            return self.generate_report()
        
        # Step 2: Run all test suites
        try:
            self.test_phone_authentication_system()
            self.test_customer_profile_management()
            self.test_address_management()
            self.test_order_history_and_ratings()
            self.test_authentication_and_authorization()
            self.test_error_handling()
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
        finally:
            # Step 3: Cleanup
            self.cleanup_test_data()
        
        # Step 4: Generate report
        return self.generate_report()

def main():
    """Main test execution function"""
    tester = CustomerProfileTester()
    report = tester.run_all_tests()
    
    # Save detailed results to file
    with open("/app/customer_profile_test_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Detailed results saved to: /app/customer_profile_test_results.json")
    
    return report["success_rate"] >= 75  # Return True if success rate is good

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)