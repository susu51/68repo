#!/usr/bin/env python3
"""
Production Readiness Testing for Kuryecini Platform
Testing newly implemented and updated endpoints (Madde 1-10)
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
import tempfile

# Configuration
BACKEND_URL = "https://order-platform-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_CREDENTIALS = {
    "admin": {"email": "admin@test.com", "password": "6851"},
    "customer": {"email": "testcustomer@example.com", "password": "test123"},
    "business": {"email": "testbusiness@example.com", "password": "test123"},
    "courier": {"email": "testkurye@example.com", "password": "test123"}
}

class ProductionReadinessTest:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def authenticate_users(self):
        """Authenticate all test users"""
        print("\n🔐 AUTHENTICATION TESTING")
        print("=" * 50)
        
        for user_type, creds in TEST_CREDENTIALS.items():
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[user_type] = data.get("access_token")
                    user_info = data.get("user", {})
                    self.log_result(
                        f"{user_type.title()} Login",
                        True,
                        f"Token obtained, Role: {user_info.get('role', 'unknown')}",
                        response_time
                    )
                else:
                    self.log_result(
                        f"{user_type.title()} Login",
                        False,
                        f"Status: {response.status_code}, Response: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(f"{user_type.title()} Login", False, f"Exception: {str(e)}")
    
    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n🏥 HEALTH ENDPOINTS TESTING")
        print("=" * 50)
        
        health_endpoints = [
            ("/api/healthz", "Primary Health Check")
        ]
        
        for endpoint, description in health_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    self.log_result(
                        description,
                        status == "ok",
                        f"Status: {status}, Response time: {response_time:.2f}s",
                        response_time
                    )
                else:
                    self.log_result(
                        description,
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result(description, False, f"Exception: {str(e)}")
    
    def test_public_menu_system(self):
        """Test public menu system with approved restaurants"""
        print("\n🍽️ PUBLIC MENU SYSTEM TESTING")
        print("=" * 50)
        
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/businesses", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                businesses = response.json()
                
                self.log_result(
                    "Public Business Endpoint",
                    True,
                    f"Found {len(businesses)} approved businesses",
                    response_time
                )
                
                # Test business structure
                if businesses:
                    business = businesses[0]
                    required_fields = ["id", "name", "category", "rating", "location"]
                    missing_fields = [field for field in required_fields if field not in business]
                    
                    self.log_result(
                        "Business Data Structure",
                        len(missing_fields) == 0,
                        f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                    )
                else:
                    self.log_result(
                        "Business Availability",
                        False,
                        "No approved businesses found - may need to approve test businesses"
                    )
            else:
                self.log_result(
                    "Public Business Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Public Business System", False, f"Exception: {str(e)}")
    
    def test_kyc_file_upload(self):
        """Test KYC file upload functionality"""
        print("\n📄 KYC FILE UPLOAD TESTING")
        print("=" * 50)
        
        if "courier" not in self.tokens:
            self.log_result("KYC File Upload", False, "Courier authentication required")
            return
        
        # Create temporary test files
        try:
            # Create a small test image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                # Write minimal JPEG header
                temp_file.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00')
                temp_file.write(b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f')
                temp_file.write(b'\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa\xff\xd9')
                license_file_path = temp_file.name
            
            # Test KYC upload
            headers = {"Authorization": f"Bearer {self.tokens['courier']}"}
            
            with open(license_file_path, 'rb') as license_file:
                files = {
                    'license_photo': ('test_license.jpg', license_file, 'image/jpeg')
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/couriers/kyc",
                    files=files,
                    headers=headers,
                    timeout=15
                )
                response_time = time.time() - start_time
            
            # Clean up temp file
            os.unlink(license_file_path)
            
            if response.status_code == 200:
                data = response.json()
                uploaded_docs = data.get("uploaded_documents", {})
                self.log_result(
                    "KYC File Upload",
                    True,
                    f"Upload successful, Documents: {list(uploaded_docs.keys())}",
                    response_time
                )
            else:
                self.log_result(
                    "KYC File Upload",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                
        except Exception as e:
            self.log_result("KYC File Upload", False, f"Exception: {str(e)}")
    
    def test_address_management(self):
        """Test address management CRUD operations"""
        print("\n🏠 ADDRESS MANAGEMENT TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Address Management", False, "Customer authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        test_address_id = None
        
        # Test 1: Get addresses (initially empty)
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/addresses", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                addresses = response.json()
                self.log_result(
                    "Get Addresses",
                    True,
                    f"Retrieved {len(addresses)} addresses",
                    response_time
                )
            else:
                self.log_result(
                    "Get Addresses",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Get Addresses", False, f"Exception: {str(e)}")
        
        # Test 2: Create new address
        try:
            new_address = {
                "title": "Test Ev Adresi",
                "address_line": "Kadıköy Mah. Test Sok. No:123",
                "district": "Kadıköy",
                "city": "İstanbul",
                "postal_code": "34710",
                "is_default": True
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/addresses",
                json=new_address,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                test_address_id = data.get("id")
                self.log_result(
                    "Create Address",
                    True,
                    f"Address created with ID: {test_address_id}",
                    response_time
                )
            else:
                self.log_result(
                    "Create Address",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Create Address", False, f"Exception: {str(e)}")
        
        # Test 3: Update address (if created successfully)
        if test_address_id:
            try:
                updated_address = {
                    "title": "Test Ev Adresi (Güncellenmiş)",
                    "address_line": "Kadıköy Mah. Test Sok. No:456",
                    "district": "Kadıköy",
                    "city": "İstanbul",
                    "postal_code": "34710",
                    "is_default": True
                }
                
                start_time = time.time()
                response = self.session.put(
                    f"{API_BASE}/addresses/{test_address_id}",
                    json=updated_address,
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Update Address",
                        True,
                        "Address updated successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Update Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Update Address", False, f"Exception: {str(e)}")
        
        # Test 4: Set default address
        if test_address_id:
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/addresses/{test_address_id}/set-default",
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Set Default Address",
                        True,
                        "Default address set successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Set Default Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Set Default Address", False, f"Exception: {str(e)}")
        
        # Test 5: Delete address
        if test_address_id:
            try:
                start_time = time.time()
                response = self.session.delete(
                    f"{API_BASE}/addresses/{test_address_id}",
                    headers=headers,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(
                        "Delete Address",
                        True,
                        "Address deleted successfully",
                        response_time
                    )
                else:
                    self.log_result(
                        "Delete Address",
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}",
                        response_time
                    )
            except Exception as e:
                self.log_result("Delete Address", False, f"Exception: {str(e)}")
    
    def test_commission_system(self):
        """Test commission system and PriceBreakdown in order creation"""
        print("\n💰 COMMISSION SYSTEM TESTING")
        print("=" * 50)
        
        if "customer" not in self.tokens:
            self.log_result("Commission System", False, "Customer authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        
        # Test order creation with commission calculation
        try:
            test_order = {
                "delivery_address": "Test Delivery Address, İstanbul",
                "delivery_lat": 41.0082,
                "delivery_lng": 28.9784,
                "items": [
                    {
                        "product_id": "test-product-1",
                        "product_name": "Test Burger",
                        "product_price": 45.0,
                        "quantity": 2,
                        "subtotal": 90.0
                    },
                    {
                        "product_id": "test-product-2", 
                        "product_name": "Test Drink",
                        "product_price": 15.0,
                        "quantity": 1,
                        "subtotal": 15.0
                    }
                ],
                "total_amount": 105.0,
                "notes": "Test order for commission testing"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/orders",
                json=test_order,
                headers=headers,
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                commission_amount = data.get("commission_amount", 0)
                total_amount = data.get("total_amount", 0)
                price_breakdown = data.get("price_breakdown")
                
                # Verify commission calculation (3% as per code)
                expected_commission = total_amount * 0.03
                commission_correct = abs(commission_amount - expected_commission) < 0.01
                
                self.log_result(
                    "Order Creation with Commission",
                    True,
                    f"Order created, Commission: ₺{commission_amount:.2f} (Expected: ₺{expected_commission:.2f})",
                    response_time
                )
                
                self.log_result(
                    "Commission Calculation",
                    commission_correct,
                    f"Commission: ₺{commission_amount:.2f}, Expected: ₺{expected_commission:.2f}"
                )
                
                if price_breakdown:
                    self.log_result(
                        "PriceBreakdown Structure",
                        True,
                        f"PriceBreakdown present with fields: {list(price_breakdown.keys())}"
                    )
                else:
                    self.log_result(
                        "PriceBreakdown Structure",
                        False,
                        "PriceBreakdown not found in order response"
                    )
                    
            else:
                self.log_result(
                    "Commission System",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
                
        except Exception as e:
            self.log_result("Commission System", False, f"Exception: {str(e)}")
    
    def test_admin_config_system(self):
        """Test admin configuration system for commission parameters"""
        print("\n⚙️ ADMIN CONFIG SYSTEM TESTING")
        print("=" * 50)
        
        if "admin" not in self.tokens:
            self.log_result("Admin Config System", False, "Admin authentication required")
            return
        
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test 1: Get current configuration
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/admin/config", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                config = response.json()
                self.log_result(
                    "Get Admin Config",
                    True,
                    f"Retrieved {len(config)} configuration items",
                    response_time
                )
                
                # Check for commission-related config
                commission_configs = [item for item in config if 'commission' in item.get('key', '').lower()]
                self.log_result(
                    "Commission Config Items",
                    len(commission_configs) > 0,
                    f"Found {len(commission_configs)} commission-related config items"
                )
                
            else:
                self.log_result(
                    "Get Admin Config",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Get Admin Config", False, f"Exception: {str(e)}")
        
        # Test 2: Update configuration
        try:
            params = {
                "config_key": "platform_commission_rate",
                "config_value": 0.05,
                "description": "Platform commission rate (5%)"
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/admin/config/update",
                params=params,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result(
                    "Update Admin Config",
                    True,
                    "Configuration updated successfully",
                    response_time
                )
            else:
                self.log_result(
                    "Update Admin Config",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time
                )
        except Exception as e:
            self.log_result("Update Admin Config", False, f"Exception: {str(e)}")
    
    def test_cors_functionality(self):
        """Test CORS configuration"""
        print("\n🌐 CORS FUNCTIONALITY TESTING")
        print("=" * 50)
        
        try:
            # Test preflight request
            headers = {
                'Origin': 'https://order-platform-1.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            start_time = time.time()
            response = self.session.options(f"{API_BASE}/auth/login", headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                self.log_result(
                    "CORS Preflight Request",
                    True,
                    f"CORS headers present: {list(cors_headers.keys())}",
                    response_time
                )
            else:
                self.log_result(
                    "CORS Preflight Request",
                    False,
                    f"HTTP {response.status_code}: Preflight failed",
                    response_time
                )
        except Exception as e:
            self.log_result("CORS Functionality", False, f"Exception: {str(e)}")
    
    def test_turkish_error_messages(self):
        """Test Turkish error message formatting"""
        print("\n🇹🇷 TURKISH ERROR MESSAGES TESTING")
        print("=" * 50)
        
        # Test invalid login for Turkish error message
        try:
            invalid_creds = {"email": "invalid@test.com", "password": "wrongpassword"}
            
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/auth/login", json=invalid_creds, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                
                # Check if error message is in Turkish
                turkish_keywords = ["yanlış", "hata", "geçersiz", "bulunamadı"]
                is_turkish = any(keyword in error_detail.lower() for keyword in turkish_keywords)
                
                self.log_result(
                    "Turkish Error Messages",
                    is_turkish,
                    f"Error message: '{error_detail}', Turkish: {is_turkish}",
                    response_time
                )
            else:
                self.log_result(
                    "Turkish Error Messages",
                    False,
                    f"Expected 400 error, got {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log_result("Turkish Error Messages", False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 PRODUCTION READINESS TEST REPORT")
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
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ CRITICAL SUCCESS CRITERIA CHECK:")
        critical_tests = [
            "Primary Health Check",
            "Public Business Endpoint",
            "Admin Login",
            "Customer Login",
            "Business Login",
            "Courier Login"
        ]
        
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"   {status} {test_name}")
            else:
                print(f"   ⚠️ {test_name} - Not tested")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": self.test_results
        }

def main():
    """Run production readiness tests"""
    print("🚀 KURYECINI PRODUCTION READINESS TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start Time: {datetime.now().isoformat()}")
    
    tester = ProductionReadinessTest()
    
    # Run all tests
    tester.authenticate_users()
    tester.test_health_endpoints()
    tester.test_public_menu_system()
    tester.test_kyc_file_upload()
    tester.test_address_management()
    tester.test_commission_system()
    tester.test_admin_config_system()
    tester.test_cors_functionality()
    tester.test_turkish_error_messages()
    
    # Generate final report
    report = tester.generate_report()
    
    return report

if __name__ == "__main__":
    main()