#!/usr/bin/env python3
"""
Comprehensive Courier Panel API Testing
Tests all new courier panel endpoints as requested in the review.
"""

import requests
import json
import time
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class CourierPanelTester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://kuryecini-delivery-1.preview.emergentagent.com')
        if not self.base_url.endswith('/api'):
            self.base_url = f"{self.base_url}/api"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Test credentials
        self.admin_token = None
        self.courier_token = None
        self.customer_token = None
        self.business_token = None
        
        # Test data
        self.test_courier_id = None
        self.test_order_id = None
        self.test_notification_id = None
        
        # Results tracking
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_data:
            result["response"] = response_data
            
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def make_request(self, method: str, endpoint: str, data: dict = None, token: str = None, params: dict = None) -> tuple:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}
            
            return response.status_code < 400, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def setup_authentication(self):
        """Setup authentication tokens for testing"""
        print("🔐 Setting up authentication...")
        
        # Admin login (password: 6851)
        success, response = self.make_request('POST', '/auth/login', {
            'email': 'admin@test.com',
            'password': '6851'
        })
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log_result("Admin Authentication", True, "Admin login successful")
        else:
            self.log_result("Admin Authentication", False, f"Admin login failed: {response}")
            return False
        
        # Try to find existing courier or create one
        success, response = self.make_request('POST', '/register/courier', {
            'email': 'testcourier@courier.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Courier',
            'iban': 'TR330006100519786457841326',
            'vehicle_type': 'motor',
            'vehicle_model': 'Honda CB150R',
            'license_class': 'A2',
            'license_number': 'TEST123456',
            'city': 'İstanbul'
        })
        
        if success and 'access_token' in response:
            self.courier_token = response['access_token']
            self.test_courier_id = response.get('user_data', {}).get('id')
            self.log_result("Courier Registration/Login", True, "Courier authentication successful")
        else:
            # Try login if registration failed (user might already exist)
            success, response = self.make_request('POST', '/auth/login', {
                'email': 'testcourier@courier.com',
                'password': 'test123'
            })
            
            if success and 'access_token' in response:
                self.courier_token = response['access_token']
                self.test_courier_id = response.get('user_data', {}).get('id')
                self.log_result("Courier Login", True, "Existing courier login successful")
            else:
                self.log_result("Courier Authentication", False, f"Courier auth failed: {response}")
                return False
        
        # Approve courier for KYC (using admin token)
        if self.test_courier_id:
            success, response = self.make_request('PATCH', f'/admin/couriers/{self.test_courier_id}/kyc', 
                                                {'status': 'approved', 'notes': 'Test approval'}, 
                                                self.admin_token)
            if success:
                self.log_result("Courier KYC Approval", True, "Courier approved for testing")
            else:
                # Try alternative approval endpoint
                success, response = self.make_request('PATCH', f'/admin/users/{self.test_courier_id}/approve', 
                                                    {}, self.admin_token)
                if success:
                    self.log_result("Courier KYC Approval (Alternative)", True, "Courier approved via alternative endpoint")
                else:
                    self.log_result("Courier KYC Approval", False, f"Failed to approve courier: {response}")
        
        # Create test customer and business for order creation
        success, response = self.make_request('POST', '/register/customer', {
            'email': 'testcustomer@test.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Customer',
            'city': 'İstanbul'
        })
        
        if success and 'access_token' in response:
            self.customer_token = response['access_token']
            self.log_result("Customer Registration", True, "Customer created for testing")
        else:
            # Try login
            success, response = self.make_request('POST', '/auth/login', {
                'email': 'testcustomer@test.com',
                'password': 'test123'
            })
            if success:
                self.customer_token = response['access_token']
                self.log_result("Customer Login", True, "Existing customer login successful")
        
        # Create test business
        success, response = self.make_request('POST', '/register/business', {
            'email': 'testbusiness@test.com',
            'password': 'test123',
            'business_name': 'Test Restaurant',
            'tax_number': '1234567890',
            'address': 'Test Address, İstanbul',
            'city': 'İstanbul',
            'business_category': 'gida',
            'description': 'Test restaurant for courier testing'
        })
        
        if success and 'access_token' in response:
            self.business_token = response['access_token']
            business_id = response.get('user_data', {}).get('id')
            
            # Approve business
            if business_id:
                success, response = self.make_request('PATCH', f'/admin/users/{business_id}/approve', 
                                                    {}, self.admin_token)
                if success:
                    self.log_result("Business Setup", True, "Business created and approved")
                else:
                    self.log_result("Business Approval", False, f"Failed to approve business: {response}")
        else:
            # Try login
            success, response = self.make_request('POST', '/auth/login', {
                'email': 'testbusiness@test.com',
                'password': 'test123'
            })
            if success:
                self.business_token = response['access_token']
                self.log_result("Business Login", True, "Existing business login successful")
        
        return True

    def create_test_order(self):
        """Create a test order for courier testing"""
        print("📦 Creating test order...")
        
        if not self.business_token:
            self.log_result("Test Order Creation", False, "No business token available")
            return False
        
        # First create a product
        success, response = self.make_request('POST', '/products', {
            'name': 'Test Pizza',
            'description': 'Test pizza for courier testing',
            'price': 50.0,
            'category': 'pizza',
            'preparation_time_minutes': 20,
            'is_available': True
        }, self.business_token)
        
        if success:
            product_id = response.get('id')
            self.log_result("Test Product Creation", True, f"Product created: {product_id}")
            
            # Now create an order with customer token
            if self.customer_token and product_id:
                success, response = self.make_request('POST', '/orders', {
                    'delivery_address': 'Test Delivery Address, İstanbul',
                    'delivery_lat': 41.0082,
                    'delivery_lng': 28.9784,
                    'items': [{
                        'product_id': product_id,
                        'product_name': 'Test Pizza',
                        'product_price': 50.0,
                        'quantity': 1,
                        'subtotal': 50.0
                    }],
                    'total_amount': 50.0,
                    'notes': 'Test order for courier panel testing'
                }, self.customer_token)
                
                if success:
                    self.test_order_id = response.get('id')
                    self.log_result("Test Order Creation", True, f"Order created: {self.test_order_id}")
                    return True
                else:
                    self.log_result("Test Order Creation", False, f"Order creation failed: {response}")
        else:
            self.log_result("Test Product Creation", False, f"Product creation failed: {response}")
        
        return False

    def test_courier_orders_available(self):
        """Test GET /api/courier/orders/available"""
        print("🔍 Testing available orders endpoint...")
        
        # Test without authentication
        success, response = self.make_request('GET', '/courier/orders/available')
        if not success and response.get('detail') in ['Not authenticated', 'Could not validate credentials']:
            self.log_result("Available Orders - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Available Orders - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('GET', '/courier/orders/available', token=self.courier_token)
        if success:
            orders = response.get('orders', [])
            total_available = response.get('total_available', 0)
            message = response.get('message', '')
            
            self.log_result("Available Orders - Authenticated", True, 
                          f"Retrieved {total_available} available orders. Message: {message}")
        else:
            self.log_result("Available Orders - Authenticated", False, 
                          f"Failed to get available orders: {response}")
        
        # Test with non-courier user (should fail)
        if self.customer_token:
            success, response = self.make_request('GET', '/courier/orders/available', token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Available Orders - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Available Orders - Wrong Role", False, "Should reject non-courier users")

    def test_courier_toggle_status(self):
        """Test POST /api/courier/status/toggle"""
        print("🔄 Testing courier status toggle...")
        
        # Test without authentication
        success, response = self.make_request('POST', '/courier/status/toggle')
        if not success:
            self.log_result("Status Toggle - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Status Toggle - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('POST', '/courier/status/toggle', token=self.courier_token)
        if success:
            is_online = response.get('is_online')
            message = response.get('message', '')
            self.log_result("Status Toggle - First Toggle", True, 
                          f"Status toggled to: {'online' if is_online else 'offline'}. Message: {message}")
            
            # Toggle again to test both states
            success, response = self.make_request('POST', '/courier/status/toggle', token=self.courier_token)
            if success:
                is_online_2 = response.get('is_online')
                message_2 = response.get('message', '')
                self.log_result("Status Toggle - Second Toggle", True, 
                              f"Status toggled to: {'online' if is_online_2 else 'offline'}. Message: {message_2}")
                
                # Verify status actually changed
                if is_online != is_online_2:
                    self.log_result("Status Toggle - State Change", True, "Status correctly changed between toggles")
                else:
                    self.log_result("Status Toggle - State Change", False, "Status did not change between toggles")
            else:
                self.log_result("Status Toggle - Second Toggle", False, f"Second toggle failed: {response}")
        else:
            self.log_result("Status Toggle - First Toggle", False, f"Status toggle failed: {response}")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('POST', '/courier/status/toggle', token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Status Toggle - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Status Toggle - Wrong Role", False, "Should reject non-courier users")

    def test_courier_accept_order(self):
        """Test POST /api/courier/orders/{order_id}/accept"""
        print("✅ Testing order acceptance...")
        
        if not self.test_order_id:
            self.log_result("Order Accept - No Test Order", False, "No test order available for acceptance testing")
            return
        
        # Test without authentication
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/accept')
        if not success:
            self.log_result("Order Accept - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Order Accept - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/accept', 
                                            token=self.courier_token)
        if success:
            message = response.get('message', '')
            order_id = response.get('order_id', '')
            self.log_result("Order Accept - Valid Request", True, 
                          f"Order accepted successfully. Message: {message}, Order ID: {order_id}")
        else:
            self.log_result("Order Accept - Valid Request", False, f"Order acceptance failed: {response}")
        
        # Test accepting already accepted order (should fail)
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/accept', 
                                            token=self.courier_token)
        if not success and ('bulunamadı' in str(response) or 'not found' in str(response).lower()):
            self.log_result("Order Accept - Already Accepted", True, "Correctly rejected already accepted order")
        else:
            self.log_result("Order Accept - Already Accepted", False, "Should reject already accepted orders")
        
        # Test with invalid order ID
        success, response = self.make_request('POST', '/courier/orders/invalid-order-id/accept', 
                                            token=self.courier_token)
        if not success:
            self.log_result("Order Accept - Invalid ID", True, "Correctly rejected invalid order ID")
        else:
            self.log_result("Order Accept - Invalid ID", False, "Should reject invalid order IDs")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/accept', 
                                                token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Order Accept - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Order Accept - Wrong Role", False, "Should reject non-courier users")

    def test_courier_update_order_status(self):
        """Test POST /api/courier/orders/{order_id}/update-status"""
        print("📋 Testing order status updates...")
        
        if not self.test_order_id:
            self.log_result("Order Status Update - No Test Order", False, "No test order available")
            return
        
        # Test without authentication
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/update-status', 
                                            {'status': 'picked_up'})
        if not success:
            self.log_result("Order Status - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Order Status - No Auth", False, "Should reject unauthenticated request")
        
        # Test updating to picked_up
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/update-status', 
                                            {'status': 'picked_up', 'notes': 'Order picked up for testing'}, 
                                            self.courier_token)
        if success:
            message = response.get('message', '')
            status = response.get('status', '')
            self.log_result("Order Status - Picked Up", True, 
                          f"Status updated to picked_up. Message: {message}, Status: {status}")
        else:
            self.log_result("Order Status - Picked Up", False, f"Failed to update to picked_up: {response}")
        
        # Test updating to delivered
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/update-status', 
                                            {'status': 'delivered', 'notes': 'Order delivered successfully'}, 
                                            self.courier_token)
        if success:
            message = response.get('message', '')
            status = response.get('status', '')
            self.log_result("Order Status - Delivered", True, 
                          f"Status updated to delivered. Message: {message}, Status: {status}")
        else:
            self.log_result("Order Status - Delivered", False, f"Failed to update to delivered: {response}")
        
        # Test invalid status
        success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/update-status', 
                                            {'status': 'invalid_status'}, self.courier_token)
        if not success and 'Invalid status' in str(response):
            self.log_result("Order Status - Invalid Status", True, "Correctly rejected invalid status")
        else:
            self.log_result("Order Status - Invalid Status", False, "Should reject invalid status values")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('POST', f'/courier/orders/{self.test_order_id}/update-status', 
                                                {'status': 'picked_up'}, self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Order Status - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Order Status - Wrong Role", False, "Should reject non-courier users")

    def test_courier_order_history(self):
        """Test GET /api/courier/orders/history"""
        print("📚 Testing courier order history...")
        
        # Test without authentication
        success, response = self.make_request('GET', '/courier/orders/history')
        if not success:
            self.log_result("Order History - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Order History - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('GET', '/courier/orders/history', token=self.courier_token)
        if success:
            orders = response.get('orders', [])
            pagination = response.get('pagination', {})
            summary = response.get('summary', {})
            
            self.log_result("Order History - Basic Request", True, 
                          f"Retrieved {len(orders)} orders. Total earnings: {summary.get('total_earnings', 0)}")
        else:
            self.log_result("Order History - Basic Request", False, f"Failed to get order history: {response}")
        
        # Test with pagination
        success, response = self.make_request('GET', '/courier/orders/history', 
                                            params={'page': 1, 'limit': 5}, token=self.courier_token)
        if success:
            pagination = response.get('pagination', {})
            self.log_result("Order History - Pagination", True, 
                          f"Pagination working. Page: {pagination.get('page')}, Limit: {pagination.get('limit')}")
        else:
            self.log_result("Order History - Pagination", False, f"Pagination failed: {response}")
        
        # Test with status filter
        success, response = self.make_request('GET', '/courier/orders/history', 
                                            params={'status_filter': 'delivered'}, token=self.courier_token)
        if success:
            orders = response.get('orders', [])
            self.log_result("Order History - Status Filter", True, 
                          f"Status filter working. Found {len(orders)} delivered orders")
        else:
            self.log_result("Order History - Status Filter", False, f"Status filter failed: {response}")
        
        # Test with date filter
        success, response = self.make_request('GET', '/courier/orders/history', 
                                            params={'date_filter': 'today'}, token=self.courier_token)
        if success:
            orders = response.get('orders', [])
            self.log_result("Order History - Date Filter", True, 
                          f"Date filter working. Found {len(orders)} orders today")
        else:
            self.log_result("Order History - Date Filter", False, f"Date filter failed: {response}")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('GET', '/courier/orders/history', token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Order History - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Order History - Wrong Role", False, "Should reject non-courier users")

    def test_courier_notifications(self):
        """Test GET /api/courier/notifications"""
        print("🔔 Testing courier notifications...")
        
        # Test without authentication
        success, response = self.make_request('GET', '/courier/notifications')
        if not success:
            self.log_result("Notifications - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Notifications - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('GET', '/courier/notifications', token=self.courier_token)
        if success:
            notifications = response.get('notifications', [])
            unread_count = response.get('unread_count', 0)
            
            self.log_result("Notifications - Basic Request", True, 
                          f"Retrieved {len(notifications)} notifications. Unread: {unread_count}")
            
            # Store first notification ID for read testing
            if notifications:
                self.test_notification_id = notifications[0].get('id')
        else:
            self.log_result("Notifications - Basic Request", False, f"Failed to get notifications: {response}")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('GET', '/courier/notifications', token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Notifications - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Notifications - Wrong Role", False, "Should reject non-courier users")

    def test_courier_mark_notification_read(self):
        """Test POST /api/courier/notifications/{notification_id}/read"""
        print("✅ Testing mark notification as read...")
        
        # Create a test notification first using admin messaging
        if self.admin_token and self.test_courier_id:
            success, response = self.make_request('POST', '/admin/courier/message', {
                'courier_ids': [self.test_courier_id],
                'title': 'Test Notification',
                'message': 'This is a test notification for read testing'
            }, self.admin_token)
            
            if success:
                self.log_result("Test Notification Creation", True, "Test notification created for read testing")
                
                # Get notifications to find the new one
                success, response = self.make_request('GET', '/courier/notifications', token=self.courier_token)
                if success and response.get('notifications'):
                    self.test_notification_id = response['notifications'][0].get('id')
            else:
                self.log_result("Test Notification Creation", False, f"Failed to create test notification: {response}")
        
        if not self.test_notification_id:
            self.log_result("Mark Notification Read - No Test Notification", False, "No test notification available")
            return
        
        # Test without authentication
        success, response = self.make_request('POST', f'/courier/notifications/{self.test_notification_id}/read')
        if not success:
            self.log_result("Mark Read - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Mark Read - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('POST', f'/courier/notifications/{self.test_notification_id}/read', 
                                            token=self.courier_token)
        if success:
            message = response.get('message', '')
            self.log_result("Mark Read - Valid Request", True, f"Notification marked as read. Message: {message}")
        else:
            self.log_result("Mark Read - Valid Request", False, f"Failed to mark notification as read: {response}")
        
        # Test with invalid notification ID
        success, response = self.make_request('POST', '/courier/notifications/invalid-id/read', 
                                            token=self.courier_token)
        if not success:
            self.log_result("Mark Read - Invalid ID", True, "Correctly rejected invalid notification ID")
        else:
            self.log_result("Mark Read - Invalid ID", False, "Should reject invalid notification IDs")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('POST', f'/courier/notifications/{self.test_notification_id}/read', 
                                                token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Mark Read - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Mark Read - Wrong Role", False, "Should reject non-courier users")

    def test_courier_messages(self):
        """Test GET /api/courier/messages"""
        print("💬 Testing courier messages...")
        
        # Test without authentication
        success, response = self.make_request('GET', '/courier/messages')
        if not success:
            self.log_result("Messages - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Messages - No Auth", False, "Should reject unauthenticated request")
        
        # Test with courier authentication
        success, response = self.make_request('GET', '/courier/messages', token=self.courier_token)
        if success:
            messages = response.get('messages', [])
            self.log_result("Messages - Basic Request", True, f"Retrieved {len(messages)} messages")
        else:
            self.log_result("Messages - Basic Request", False, f"Failed to get messages: {response}")
        
        # Test with non-courier user
        if self.customer_token:
            success, response = self.make_request('GET', '/courier/messages', token=self.customer_token)
            if not success and 'Courier access required' in str(response):
                self.log_result("Messages - Wrong Role", True, "Correctly rejected non-courier user")
            else:
                self.log_result("Messages - Wrong Role", False, "Should reject non-courier users")

    def test_admin_courier_message(self):
        """Test POST /api/admin/courier/message"""
        print("📢 Testing admin courier messaging...")
        
        # Test without authentication
        success, response = self.make_request('POST', '/admin/courier/message', {
            'courier_ids': [],
            'title': 'Test Message',
            'message': 'This is a test message'
        })
        if not success:
            self.log_result("Admin Message - No Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_result("Admin Message - No Auth", False, "Should reject unauthenticated request")
        
        # Test with admin authentication - broadcast message
        success, response = self.make_request('POST', '/admin/courier/message', {
            'courier_ids': [],  # Empty array = broadcast to all
            'title': 'Broadcast Test',
            'message': 'This is a broadcast test message to all couriers'
        }, self.admin_token)
        
        if success:
            recipients = response.get('recipients', 0)
            message = response.get('message', '')
            self.log_result("Admin Message - Broadcast", True, 
                          f"Broadcast message sent. Recipients: {recipients}, Message: {message}")
        else:
            self.log_result("Admin Message - Broadcast", False, f"Broadcast message failed: {response}")
        
        # Test with specific courier ID
        if self.test_courier_id:
            success, response = self.make_request('POST', '/admin/courier/message', {
                'courier_ids': [self.test_courier_id],
                'title': 'Direct Test Message',
                'message': 'This is a direct test message to specific courier'
            }, self.admin_token)
            
            if success:
                recipients = response.get('recipients', 0)
                message = response.get('message', '')
                self.log_result("Admin Message - Direct", True, 
                              f"Direct message sent. Recipients: {recipients}, Message: {message}")
            else:
                self.log_result("Admin Message - Direct", False, f"Direct message failed: {response}")
        
        # Test with empty message (should fail)
        success, response = self.make_request('POST', '/admin/courier/message', {
            'courier_ids': [],
            'title': 'Empty Message Test',
            'message': ''
        }, self.admin_token)
        
        if not success and 'Message text required' in str(response):
            self.log_result("Admin Message - Empty Message", True, "Correctly rejected empty message")
        else:
            self.log_result("Admin Message - Empty Message", False, "Should reject empty messages")
        
        # Test with non-admin user
        if self.courier_token:
            success, response = self.make_request('POST', '/admin/courier/message', {
                'courier_ids': [],
                'title': 'Unauthorized Test',
                'message': 'This should fail'
            }, self.courier_token)
            
            if not success and 'Admin access required' in str(response):
                self.log_result("Admin Message - Wrong Role", True, "Correctly rejected non-admin user")
            else:
                self.log_result("Admin Message - Wrong Role", False, "Should reject non-admin users")

    def run_all_tests(self):
        """Run all courier panel tests"""
        print("🚀 Starting Courier Panel API Testing...")
        print("=" * 60)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot continue with tests.")
            return
        
        # Create test data
        self.create_test_order()
        
        # Run all tests
        print("\n" + "=" * 60)
        print("🧪 Running Courier Panel API Tests...")
        print("=" * 60)
        
        self.test_courier_orders_available()
        self.test_courier_toggle_status()
        self.test_courier_accept_order()
        self.test_courier_update_order_status()
        self.test_courier_order_history()
        self.test_courier_notifications()
        self.test_courier_mark_notification_read()
        self.test_courier_messages()
        self.test_admin_courier_message()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COURIER PANEL API TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        # Group results by test category
        categories = {}
        for result in self.results:
            category = result['test'].split(' - ')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, tests in categories.items():
            passed = sum(1 for test in tests if test['success'])
            total = len(tests)
            print(f"\n{category}: {passed}/{total} passed")
            
            for test in tests:
                status_icon = "✅" if test['success'] else "❌"
                print(f"  {status_icon} {test['test']}")
                if test['details']:
                    print(f"     {test['details']}")
        
        print("\n" + "=" * 60)
        
        # Identify critical failures
        critical_failures = [r for r in self.results if not r['success'] and 'Wrong Role' not in r['test'] and 'No Auth' not in r['test']]
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES FOUND:")
            for failure in critical_failures:
                print(f"❌ {failure['test']}: {failure['details']}")
        else:
            print("✅ NO CRITICAL ISSUES FOUND")
        
        print("=" * 60)

if __name__ == "__main__":
    tester = CourierPanelTester()
    tester.run_all_tests()