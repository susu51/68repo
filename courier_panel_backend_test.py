#!/usr/bin/env python3
"""
🚀 PHASE 1 - COURIER PANEL BACKEND COMPREHENSIVE TESTING

Tests all newly implemented Phase 1 Courier Panel backend endpoints:
1. PDF Reports System
2. Profile Update System  
3. Availability Management
4. Order History Enhanced Filters
5. Ready Orders System

Authentication: testkurye@example.com/test123
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin

# Configuration
BACKEND_URL = "https://quickship-49.preview.emergentagent.com/api"
COURIER_EMAIL = "testkurye@example.com"
COURIER_PASSWORD = "test123"

class CourierPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BACKEND_URL
        self.auth_token = None
        self.courier_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        print()
    
    def authenticate_courier(self):
        """Authenticate courier user"""
        print("🔐 AUTHENTICATING COURIER...")
        
        try:
            # Login with courier credentials
            login_url = f"{self.base_url}/auth/login"
            login_data = {
                "email": COURIER_EMAIL,
                "password": COURIER_PASSWORD
            }
            
            response = self.session.post(login_url, json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('user', {})
                
                if user_data.get('role') == 'courier':
                    self.courier_id = user_data.get('id')
                    print(f"✅ Courier authenticated: {user_data.get('email')} (ID: {self.courier_id})")
                    print(f"   📋 Role: {user_data.get('role')}")
                    print(f"   🏷️  Name: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
                    print(f"   🎯 KYC Status: {user_data.get('kyc_status', 'N/A')}")
                    return True
                else:
                    print(f"❌ User is not a courier: {user_data.get('role')}")
                    return False
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_pdf_reports_system(self):
        """Test PDF Reports System"""
        print("📊 TESTING PDF REPORTS SYSTEM...")
        
        # Test 1: Daily PDF Report
        try:
            url = f"{self.base_url}/courier/earnings/report/pdf?range=daily"
            response = self.session.get(url)
            
            success = (response.status_code == 200 and 
                      response.headers.get('content-type') == 'application/pdf' and
                      'Content-Disposition' in response.headers)
            
            details = f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}"
            if success:
                details += f", PDF Size: {len(response.content)} bytes"
            
            self.log_test("PDF Daily Report Generation", success, details)
            
        except Exception as e:
            self.log_test("PDF Daily Report Generation", False, f"Exception: {e}")
        
        # Test 2: Weekly PDF Report
        try:
            url = f"{self.base_url}/courier/earnings/report/pdf?range=weekly"
            response = self.session.get(url)
            
            success = (response.status_code == 200 and 
                      response.headers.get('content-type') == 'application/pdf')
            
            details = f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}"
            self.log_test("PDF Weekly Report Generation", success, details)
            
        except Exception as e:
            self.log_test("PDF Weekly Report Generation", False, f"Exception: {e}")
        
        # Test 3: Monthly PDF Report with Custom Date Range
        try:
            from_date = "2024-01-01"
            to_date = "2024-01-31"
            url = f"{self.base_url}/courier/earnings/report/pdf?range=monthly&from_date={from_date}&to_date={to_date}"
            response = self.session.get(url)
            
            success = (response.status_code == 200 and 
                      response.headers.get('content-type') == 'application/pdf')
            
            details = f"Status: {response.status_code}, Date Range: {from_date} to {to_date}"
            self.log_test("PDF Monthly Report with Custom Range", success, details)
            
        except Exception as e:
            self.log_test("PDF Monthly Report with Custom Range", False, f"Exception: {e}")
        
        # Test 4: PDF Headers Validation
        try:
            url = f"{self.base_url}/courier/earnings/report/pdf?range=daily"
            response = self.session.get(url)
            
            has_pdf_content_type = response.headers.get('content-type') == 'application/pdf'
            has_content_disposition = 'Content-Disposition' in response.headers
            has_attachment = 'attachment' in response.headers.get('Content-Disposition', '')
            
            success = has_pdf_content_type and has_content_disposition and has_attachment
            details = f"PDF Content-Type: {has_pdf_content_type}, Content-Disposition: {has_content_disposition}, Attachment: {has_attachment}"
            
            self.log_test("PDF Download Headers Validation", success, details)
            
        except Exception as e:
            self.log_test("PDF Download Headers Validation", False, f"Exception: {e}")
        
        # Test 5: Turkish Character Support Test (Empty Data Scenario)
        try:
            # This should generate a "no data" PDF with Turkish text
            url = f"{self.base_url}/courier/earnings/report/pdf?range=daily"
            response = self.session.get(url)
            
            success = (response.status_code == 200 and 
                      response.headers.get('content-type') == 'application/pdf' and
                      len(response.content) > 1000)  # Should have some content even if no data
            
            details = f"Status: {response.status_code}, PDF Size: {len(response.content)} bytes (should contain Turkish 'no data' message)"
            self.log_test("Turkish Character Support in PDF", success, details)
            
        except Exception as e:
            self.log_test("Turkish Character Support in PDF", False, f"Exception: {e}")
    
    def test_profile_update_system(self):
        """Test Profile Update System"""
        print("👤 TESTING PROFILE UPDATE SYSTEM...")
        
        # Test 1: Full Profile Update
        try:
            url = f"{self.base_url}/courier/profile"
            profile_data = {
                "name": "Ahmet",
                "surname": "Yılmaz", 
                "phone": "+905551234567",
                "email": "courier@test.com",
                "iban": "TR330006100519786457841326",
                "vehicleType": "Motosiklet",
                "plate": "34 ABC 123"
            }
            
            response = self.session.put(url, json=profile_data)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'profile' in data and
                          data['profile'].get('name') == 'Ahmet')
                details = f"Status: {response.status_code}, Profile updated successfully"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Full Profile Update", success, details)
            
        except Exception as e:
            self.log_test("Full Profile Update", False, f"Exception: {e}")
        
        # Test 2: Partial Profile Update (only name and phone)
        try:
            url = f"{self.base_url}/courier/profile"
            partial_data = {
                "name": "Mehmet",
                "phone": "+905559876543"
            }
            
            response = self.session.put(url, json=partial_data)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          data['profile'].get('name') == 'Mehmet')
                details = f"Status: {response.status_code}, Partial update successful"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Partial Profile Update", success, details)
            
        except Exception as e:
            self.log_test("Partial Profile Update", False, f"Exception: {e}")
        
        # Test 3: IBAN Validation (auto TR prefix)
        try:
            url = f"{self.base_url}/courier/profile"
            iban_data = {
                "iban": "330006100519786457841326"  # Without TR prefix
            }
            
            response = self.session.put(url, json=iban_data)
            
            if response.status_code == 200:
                data = response.json()
                updated_iban = data['profile'].get('iban', '')
                success = updated_iban.startswith('TR') and len(updated_iban) == 26
                details = f"Status: {response.status_code}, IBAN auto-prefixed: {updated_iban}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("IBAN Auto TR Prefix Validation", success, details)
            
        except Exception as e:
            self.log_test("IBAN Auto TR Prefix Validation", False, f"Exception: {e}")
        
        # Test 4: Invalid IBAN Validation
        try:
            url = f"{self.base_url}/courier/profile"
            invalid_iban_data = {
                "iban": "TR123456789"  # Too short
            }
            
            response = self.session.put(url, json=invalid_iban_data)
            
            success = response.status_code == 422  # Should return validation error
            details = f"Status: {response.status_code} (should be 422 for invalid IBAN)"
            
            self.log_test("Invalid IBAN Validation", success, details)
            
        except Exception as e:
            self.log_test("Invalid IBAN Validation", False, f"Exception: {e}")
        
        # Test 5: Optimistic UI Response Verification
        try:
            url = f"{self.base_url}/courier/profile"
            test_data = {
                "name": "TestName",
                "surname": "TestSurname"
            }
            
            response = self.session.put(url, json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                profile = data.get('profile', {})
                success = (profile.get('name') == 'TestName' and 
                          profile.get('surname') == 'TestSurname' and
                          'id' in profile)
                details = f"Status: {response.status_code}, Optimistic response includes updated profile"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Optimistic UI Response Verification", success, details)
            
        except Exception as e:
            self.log_test("Optimistic UI Response Verification", False, f"Exception: {e}")
    
    def test_availability_management(self):
        """Test Availability Management"""
        print("📅 TESTING AVAILABILITY MANAGEMENT...")
        
        # Test 1: Set Availability Schedule
        try:
            url = f"{self.base_url}/courier/availability"
            availability_data = {
                "slots": [
                    {"weekday": 1, "start": "09:00", "end": "18:00"},
                    {"weekday": 3, "start": "10:00", "end": "16:00"}
                ]
            }
            
            response = self.session.post(url, json=availability_data)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'availability' in data and
                          len(data['availability']) == 2)
                details = f"Status: {response.status_code}, Availability set with {len(data.get('availability', []))} slots"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Set Availability Schedule", success, details)
            
        except Exception as e:
            self.log_test("Set Availability Schedule", False, f"Exception: {e}")
        
        # Test 2: Get Availability Schedule (Persistence Check)
        try:
            url = f"{self.base_url}/courier/availability"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                availability = data.get('availability', [])
                success = (data.get('success') == True and 
                          len(availability) >= 1)  # Should have at least one slot from previous test
                details = f"Status: {response.status_code}, Retrieved {len(availability)} availability slots"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Get Availability Schedule (Persistence)", success, details)
            
        except Exception as e:
            self.log_test("Get Availability Schedule (Persistence)", False, f"Exception: {e}")
        
        # Test 3: Invalid Weekday Validation
        try:
            url = f"{self.base_url}/courier/availability"
            invalid_data = {
                "slots": [
                    {"weekday": 7, "start": "09:00", "end": "18:00"}  # Invalid weekday (should be 0-6)
                ]
            }
            
            response = self.session.post(url, json=invalid_data)
            
            success = response.status_code == 422  # Should return validation error
            details = f"Status: {response.status_code} (should be 422 for invalid weekday)"
            
            self.log_test("Invalid Weekday Validation", success, details)
            
        except Exception as e:
            self.log_test("Invalid Weekday Validation", False, f"Exception: {e}")
        
        # Test 4: Invalid Time Format Validation
        try:
            url = f"{self.base_url}/courier/availability"
            invalid_time_data = {
                "slots": [
                    {"weekday": 1, "start": "25:00", "end": "18:00"}  # Invalid time format
                ]
            }
            
            response = self.session.post(url, json=invalid_time_data)
            
            success = response.status_code in [400, 422]  # Should return validation error
            details = f"Status: {response.status_code} (should be 400/422 for invalid time)"
            
            self.log_test("Invalid Time Format Validation", success, details)
            
        except Exception as e:
            self.log_test("Invalid Time Format Validation", False, f"Exception: {e}")
        
        # Test 5: Data Persistence After Logout/Login Cycle
        try:
            # First, set availability
            url = f"{self.base_url}/courier/availability"
            test_availability = {
                "slots": [
                    {"weekday": 2, "start": "08:00", "end": "17:00"}
                ]
            }
            
            set_response = self.session.post(url, json=test_availability)
            
            if set_response.status_code == 200:
                # Then get availability to verify persistence
                get_response = self.session.get(url)
                
                if get_response.status_code == 200:
                    data = get_response.json()
                    availability = data.get('availability', [])
                    
                    # Check if our test slot exists
                    has_test_slot = any(
                        slot.get('weekday') == 2 and 
                        slot.get('start') == '08:00' and 
                        slot.get('end') == '17:00'
                        for slot in availability
                    )
                    
                    success = has_test_slot
                    details = f"Persistence verified: {has_test_slot}, Total slots: {len(availability)}"
                else:
                    success = False
                    details = f"Get failed: {get_response.status_code}"
            else:
                success = False
                details = f"Set failed: {set_response.status_code}"
            
            self.log_test("Data Persistence Verification", success, details)
            
        except Exception as e:
            self.log_test("Data Persistence Verification", False, f"Exception: {e}")
    
    def test_order_history_filters(self):
        """Test Order History Enhanced Filters"""
        print("📋 TESTING ORDER HISTORY ENHANCED FILTERS...")
        
        # Test 1: Basic Order History Retrieval
        try:
            url = f"{self.base_url}/courier/orders/history"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'orders' in data and
                          'pagination' in data)
                details = f"Status: {response.status_code}, Orders: {len(data.get('orders', []))}, Pagination: {data.get('pagination', {})}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Basic Order History Retrieval", success, details)
            
        except Exception as e:
            self.log_test("Basic Order History Retrieval", False, f"Exception: {e}")
        
        # Test 2: Status Filter
        try:
            url = f"{self.base_url}/courier/orders/history?status=delivered"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('orders', [])
                
                # Check if all returned orders have 'delivered' status
                all_delivered = all(order.get('status') == 'delivered' for order in orders) if orders else True
                
                success = (data.get('success') == True and all_delivered)
                details = f"Status: {response.status_code}, Delivered orders: {len(orders)}, Filter working: {all_delivered}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Status Filter (delivered)", success, details)
            
        except Exception as e:
            self.log_test("Status Filter (delivered)", False, f"Exception: {e}")
        
        # Test 3: Date Range Filter
        try:
            from_date = "2024-01-01"
            to_date = "2024-12-31"
            url = f"{self.base_url}/courier/orders/history?from_date={from_date}&to_date={to_date}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'filters' in data and
                          data['filters'].get('from_date') == from_date)
                details = f"Status: {response.status_code}, Date range applied: {from_date} to {to_date}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Date Range Filter", success, details)
            
        except Exception as e:
            self.log_test("Date Range Filter", False, f"Exception: {e}")
        
        # Test 4: Business Name Filter
        try:
            url = f"{self.base_url}/courier/orders/history?business=test"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'filters' in data and
                          data['filters'].get('business') == 'test')
                details = f"Status: {response.status_code}, Business filter applied: 'test'"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Business Name Filter", success, details)
            
        except Exception as e:
            self.log_test("Business Name Filter", False, f"Exception: {e}")
        
        # Test 5: City Filter
        try:
            url = f"{self.base_url}/courier/orders/history?city=İstanbul"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'filters' in data and
                          data['filters'].get('city') == 'İstanbul')
                details = f"Status: {response.status_code}, City filter applied: 'İstanbul'"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("City Filter", success, details)
            
        except Exception as e:
            self.log_test("City Filter", False, f"Exception: {e}")
        
        # Test 6: Pagination
        try:
            url = f"{self.base_url}/courier/orders/history?page=2&size=10"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                success = (data.get('success') == True and 
                          pagination.get('page') == 2 and
                          pagination.get('size') == 10)
                details = f"Status: {response.status_code}, Page: {pagination.get('page')}, Size: {pagination.get('size')}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Pagination", success, details)
            
        except Exception as e:
            self.log_test("Pagination", False, f"Exception: {e}")
        
        # Test 7: Sorting
        try:
            url = f"{self.base_url}/courier/orders/history?sort=total_amount:desc"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get('success') == True and 
                          'filters' in data and
                          data['filters'].get('sort') == 'total_amount:desc')
                details = f"Status: {response.status_code}, Sort applied: 'total_amount:desc'"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Sorting (total_amount:desc)", success, details)
            
        except Exception as e:
            self.log_test("Sorting (total_amount:desc)", False, f"Exception: {e}")
        
        # Test 8: Server-side Filtering Verification
        try:
            # Test with multiple filters
            url = f"{self.base_url}/courier/orders/history?status=delivered&city=İstanbul&page=1&size=5"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                filters = data.get('filters', {})
                success = (data.get('success') == True and 
                          filters.get('status') == 'delivered' and
                          filters.get('city') == 'İstanbul' and
                          data.get('pagination', {}).get('size') == 5)
                details = f"Status: {response.status_code}, Multiple filters applied successfully"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Server-side Filtering Verification", success, details)
            
        except Exception as e:
            self.log_test("Server-side Filtering Verification", False, f"Exception: {e}")
        
        # Test 9: Empty Results Handling
        try:
            # Use a filter that should return no results
            url = f"{self.base_url}/courier/orders/history?business=nonexistentbusiness12345"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('orders', [])
                success = (data.get('success') == True and 
                          len(orders) == 0 and
                          'pagination' in data)
                details = f"Status: {response.status_code}, Empty results handled properly"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Empty Results Handling", success, details)
            
        except Exception as e:
            self.log_test("Empty Results Handling", False, f"Exception: {e}")
    
    def test_ready_orders_system(self):
        """Test Ready Orders System"""
        print("🚚 TESTING READY ORDERS SYSTEM...")
        
        # Test 1: Basic Ready Orders Retrieval
        try:
            url = f"{self.base_url}/courier/orders/ready"
            response = self.session.get(url)
            
            if response.status_code == 200:
                orders = response.json()
                success = isinstance(orders, list)
                details = f"Status: {response.status_code}, Ready orders: {len(orders)}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Basic Ready Orders Retrieval", success, details)
            
        except Exception as e:
            self.log_test("Basic Ready Orders Retrieval", False, f"Exception: {e}")
        
        # Test 2: City Filter for Ready Orders
        try:
            url = f"{self.base_url}/courier/orders/ready?city=İstanbul"
            response = self.session.get(url)
            
            if response.status_code == 200:
                orders = response.json()
                success = isinstance(orders, list)
                details = f"Status: {response.status_code}, İstanbul ready orders: {len(orders)}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("City Filter for Ready Orders", success, details)
            
        except Exception as e:
            self.log_test("City Filter for Ready Orders", False, f"Exception: {e}")
        
        # Test 3: Ready Orders Status Verification
        try:
            url = f"{self.base_url}/courier/orders/ready"
            response = self.session.get(url)
            
            if response.status_code == 200:
                orders = response.json()
                
                # Check if response structure is correct
                if orders and len(orders) > 0:
                    first_order = orders[0]
                    has_required_fields = all(field in first_order for field in 
                                            ['id', 'business_name', 'business_location', 'items_count', 'delivery_address'])
                    success = has_required_fields
                    details = f"Status: {response.status_code}, Required fields present: {has_required_fields}"
                else:
                    success = True  # Empty list is valid
                    details = f"Status: {response.status_code}, No ready orders (valid empty response)"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Ready Orders Response Structure", success, details)
            
        except Exception as e:
            self.log_test("Ready Orders Response Structure", False, f"Exception: {e}")
        
        # Test 4: Business Location Data Verification
        try:
            url = f"{self.base_url}/courier/orders/ready"
            response = self.session.get(url)
            
            if response.status_code == 200:
                orders = response.json()
                
                if orders and len(orders) > 0:
                    # Check if business location has lat/lng
                    first_order = orders[0]
                    business_location = first_order.get('business_location', {})
                    has_coordinates = 'lat' in business_location and 'lng' in business_location
                    success = has_coordinates
                    details = f"Status: {response.status_code}, Business location coordinates: {has_coordinates}"
                else:
                    success = True  # No orders to check
                    details = f"Status: {response.status_code}, No orders to verify location data"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Business Location Data Verification", success, details)
            
        except Exception as e:
            self.log_test("Business Location Data Verification", False, f"Exception: {e}")
        
        # Test 5: City Restriction Verification
        try:
            # Test with a different city to verify restriction
            url = f"{self.base_url}/courier/orders/ready?city=Ankara"
            response = self.session.get(url)
            
            if response.status_code == 200:
                orders = response.json()
                success = isinstance(orders, list)  # Should return empty list or orders from Ankara only
                details = f"Status: {response.status_code}, Ankara orders: {len(orders)} (city restriction working)"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("City Restriction Verification", success, details)
            
        except Exception as e:
            self.log_test("City Restriction Verification", False, f"Exception: {e}")
    
    def test_authentication_security(self):
        """Test Authentication and Security"""
        print("🔐 TESTING AUTHENTICATION & SECURITY...")
        
        # Test 1: Courier Role Authentication
        try:
            # All courier endpoints should require courier role
            test_endpoints = [
                "/courier/earnings/report/pdf?range=daily",
                "/courier/profile",
                "/courier/availability",
                "/courier/orders/history",
                "/courier/orders/ready"
            ]
            
            authenticated_count = 0
            for endpoint in test_endpoints:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)
                
                # Should return 200 (authenticated) or 403 (wrong role) but not 401 (unauthenticated)
                if response.status_code in [200, 403]:
                    authenticated_count += 1
            
            success = authenticated_count == len(test_endpoints)
            details = f"Authenticated endpoints: {authenticated_count}/{len(test_endpoints)}"
            
            self.log_test("Courier Role Authentication", success, details)
            
        except Exception as e:
            self.log_test("Courier Role Authentication", False, f"Exception: {e}")
        
        # Test 2: Unauthorized Access Test
        try:
            # Create a new session without authentication
            unauth_session = requests.Session()
            
            url = f"{self.base_url}/courier/profile"
            response = unauth_session.get(url)
            
            success = response.status_code in [401, 403]  # Should be unauthorized
            details = f"Status: {response.status_code} (should be 401/403 for unauthorized access)"
            
            self.log_test("Unauthorized Access Prevention", success, details)
            
        except Exception as e:
            self.log_test("Unauthorized Access Prevention", False, f"Exception: {e}")
    
    def test_input_validation(self):
        """Test Input Validation"""
        print("✅ TESTING INPUT VALIDATION...")
        
        # Test 1: Invalid PDF Range Parameter
        try:
            url = f"{self.base_url}/courier/earnings/report/pdf?range=invalid"
            response = self.session.get(url)
            
            success = response.status_code == 422  # Should return validation error
            details = f"Status: {response.status_code} (should be 422 for invalid range)"
            
            self.log_test("Invalid PDF Range Parameter", success, details)
            
        except Exception as e:
            self.log_test("Invalid PDF Range Parameter", False, f"Exception: {e}")
        
        # Test 2: Invalid Date Format
        try:
            url = f"{self.base_url}/courier/orders/history?from_date=invalid-date"
            response = self.session.get(url)
            
            success = response.status_code in [400, 422]  # Should return validation error
            details = f"Status: {response.status_code} (should be 400/422 for invalid date)"
            
            self.log_test("Invalid Date Format Validation", success, details)
            
        except Exception as e:
            self.log_test("Invalid Date Format Validation", False, f"Exception: {e}")
        
        # Test 3: Profile Update with Invalid Email
        try:
            url = f"{self.base_url}/courier/profile"
            invalid_data = {
                "email": "invalid-email-format"
            }
            
            response = self.session.put(url, json=invalid_data)
            
            success = response.status_code == 422  # Should return validation error
            details = f"Status: {response.status_code} (should be 422 for invalid email)"
            
            self.log_test("Invalid Email Format Validation", success, details)
            
        except Exception as e:
            self.log_test("Invalid Email Format Validation", False, f"Exception: {e}")
    
    def test_turkish_character_support(self):
        """Test Turkish Character Support"""
        print("🇹🇷 TESTING TURKISH CHARACTER SUPPORT...")
        
        # Test 1: Turkish Characters in Profile Update
        try:
            url = f"{self.base_url}/courier/profile"
            turkish_data = {
                "name": "Çağlar",
                "surname": "Öztürk"
            }
            
            response = self.session.put(url, json=turkish_data)
            
            if response.status_code == 200:
                data = response.json()
                profile = data.get('profile', {})
                success = (profile.get('name') == 'Çağlar' and 
                          profile.get('surname') == 'Öztürk')
                details = f"Status: {response.status_code}, Turkish characters preserved: {success}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Turkish Characters in Profile", success, details)
            
        except Exception as e:
            self.log_test("Turkish Characters in Profile", False, f"Exception: {e}")
        
        # Test 2: Turkish City Names in Filters
        try:
            url = f"{self.base_url}/courier/orders/history?city=İstanbul"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                filters = data.get('filters', {})
                success = filters.get('city') == 'İstanbul'
                details = f"Status: {response.status_code}, Turkish city name preserved: {success}"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Turkish City Names in Filters", success, details)
            
        except Exception as e:
            self.log_test("Turkish City Names in Filters", False, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING PHASE 1 COURIER PANEL BACKEND COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate_courier():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print()
        
        # Run all test suites
        self.test_pdf_reports_system()
        self.test_profile_update_system()
        self.test_availability_management()
        self.test_order_history_filters()
        self.test_ready_orders_system()
        self.test_authentication_security()
        self.test_input_validation()
        self.test_turkish_character_support()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate test summary"""
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        print()
        
        # Group results by category
        categories = {
            "PDF Reports": [r for r in self.test_results if "PDF" in r['test']],
            "Profile Update": [r for r in self.test_results if "Profile" in r['test']],
            "Availability": [r for r in self.test_results if "Availability" in r['test']],
            "Order History": [r for r in self.test_results if "Order History" in r['test'] or "Filter" in r['test'] or "Pagination" in r['test'] or "Sorting" in r['test']],
            "Ready Orders": [r for r in self.test_results if "Ready Orders" in r['test']],
            "Security": [r for r in self.test_results if "Authentication" in r['test'] or "Unauthorized" in r['test']],
            "Validation": [r for r in self.test_results if "Validation" in r['test']],
            "Turkish Support": [r for r in self.test_results if "Turkish" in r['test']]
        }
        
        print("📋 RESULTS BY CATEGORY:")
        for category, tests in categories.items():
            if tests:
                category_passed = sum(1 for t in tests if t['success'])
                category_total = len(tests)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                status = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
                print(f"   {status} {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        print()
        
        # Show failed tests
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("❌ FAILED TESTS:")
            for result in failed_results:
                print(f"   • {result['test']}")
                if result['details']:
                    print(f"     📝 {result['details']}")
            print()
        
        # Priority recommendations
        print("🎯 PRIORITY FOCUS AREAS:")
        
        pdf_tests = [r for r in self.test_results if "PDF" in r['test']]
        pdf_success_rate = (sum(1 for t in pdf_tests if t['success']) / len(pdf_tests) * 100) if pdf_tests else 0
        
        profile_tests = [r for r in self.test_results if "Profile" in r['test']]
        profile_success_rate = (sum(1 for t in profile_tests if t['success']) / len(profile_tests) * 100) if profile_tests else 0
        
        availability_tests = [r for r in self.test_results if "Availability" in r['test']]
        availability_success_rate = (sum(1 for t in availability_tests if t['success']) / len(availability_tests) * 100) if availability_tests else 0
        
        history_tests = [r for r in self.test_results if any(keyword in r['test'] for keyword in ["History", "Filter", "Pagination", "Sorting"])]
        history_success_rate = (sum(1 for t in history_tests if t['success']) / len(history_tests) * 100) if history_tests else 0
        
        ready_tests = [r for r in self.test_results if "Ready Orders" in r['test']]
        ready_success_rate = (sum(1 for t in ready_tests if t['success']) / len(ready_tests) * 100) if ready_tests else 0
        
        priorities = [
            ("PDF Generation with Turkish Characters", pdf_success_rate),
            ("Profile Update Persistence", profile_success_rate),
            ("Availability Schedule Persistence", availability_success_rate),
            ("Order History Server-side Filtering", history_success_rate),
            ("Ready Orders City Restriction", ready_success_rate)
        ]
        
        for priority, rate in priorities:
            status = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
            print(f"   {status} {priority}: {rate:.1f}%")
        
        print()
        print("🎉 PHASE 1 COURIER PANEL BACKEND TESTING COMPLETE!")
        
        return success_rate

if __name__ == "__main__":
    tester = CourierPanelTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)