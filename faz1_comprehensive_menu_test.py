#!/usr/bin/env python3
"""
FAZ 1 - COMPREHENSIVE BUSINESS MENU CRUD TESTING
==============================================

Testing Business Menu CRUD system with existing business users
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://kurye-express-2.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_test(test_name):
    print(f"\n{Colors.CYAN}🧪 {test_name}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.WHITE}ℹ️  {message}{Colors.END}")

# Test Results Tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "details": []
}

def record_test(test_name, success, message=""):
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
        print_success(f"{test_name}: {message}")
    else:
        test_results["failed"] += 1
        print_error(f"{test_name}: {message}")
    
    test_results["details"].append({
        "test": test_name,
        "success": success,
        "message": message
    })

# Global variables for test data
session = requests.Session()
business_user_id = None
created_menu_items = []

def test_business_authentication():
    """Test business authentication with existing users"""
    global business_user_id, session
    
    print_test("Business Authentication Testing")
    
    # Try existing business users
    test_business_users = [
        {"email": "testbusiness@example.com", "password": "test123"},
        {"email": "business@kuryecini.com", "password": "test123"},
        {"email": "testbusiness@kuryecini.com", "password": "test123"}
    ]
    
    for user in test_business_users:
        try:
            response = session.post(f"{BASE_URL}/auth/login", json=user, headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    user_data = data.get("user", {})
                    business_user_id = user_data.get("id")
                    role = user_data.get("role")
                    
                    if role == "business":
                        record_test("Business Login", True, f"Authenticated business user: {user_data.get('email')} (ID: {business_user_id})")
                        return True
                    else:
                        print_info(f"User {user['email']} is not a business user (role: {role})")
                        
        except Exception as e:
            print_info(f"Failed to login with {user['email']}: {str(e)}")
    
    record_test("Business Login", False, "No business user could be authenticated")
    return False

def test_menu_endpoints_access():
    """Test access to menu endpoints"""
    print_test("Menu Endpoints Access Testing")
    
    if not business_user_id:
        record_test("Menu Access", False, "No authenticated business user")
        return
    
    # Test GET /api/business/menu
    try:
        response = session.get(f"{BASE_URL}/business/menu", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            record_test("Get Business Menu", True, f"Retrieved {len(data) if isinstance(data, list) else 'data'} menu items")
            return True
        elif response.status_code == 403:
            record_test("Get Business Menu", False, "Access denied (403) - Business user may not be KYC approved")
            return False
        else:
            record_test("Get Business Menu", False, f"Unexpected status: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        record_test("Get Business Menu", False, f"Error: {str(e)}")
        return False

def test_menu_item_creation():
    """Test menu item creation"""
    print_test("Menu Item Creation Testing")
    
    # Test valid menu item creation
    valid_menu_data = {
        "name": "Test Adana Kebap",
        "description": "Test Adana kebabı lavash ekmek ile",
        "price": 75.50,
        "currency": "TRY",
        "category": "Yemek",
        "tags": ["test", "kebap"],
        "image_url": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd",
        "is_available": True,
        "vat_rate": 0.18,
        "preparation_time": 20,
        "options": [
            {"name": "Ekstra acı", "price": 5.0}
        ]
    }
    
    try:
        response = session.post(f"{BASE_URL}/business/menu", json=valid_menu_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            item_id = data.get("id")
            if item_id:
                created_menu_items.append(item_id)
                record_test("Menu Item Creation", True, f"Created menu item: {data.get('name')} (ID: {item_id})")
            else:
                record_test("Menu Item Creation", False, "No item ID returned")
        elif response.status_code == 403:
            record_test("Menu Item Creation", False, "Access denied (403) - Business user may not be KYC approved")
        else:
            record_test("Menu Item Creation", False, f"Status: {response.status_code} - {response.text}")
            
    except Exception as e:
        record_test("Menu Item Creation", False, f"Error: {str(e)}")

def test_menu_item_validation():
    """Test menu item validation"""
    print_test("Menu Item Validation Testing")
    
    # Test invalid category
    invalid_category_data = {
        "name": "Test Item",
        "price": 50.0,
        "category": "InvalidCategory"
    }
    
    try:
        response = session.post(f"{BASE_URL}/business/menu", json=invalid_category_data, headers=HEADERS)
        
        if response.status_code == 422:
            record_test("Invalid Category Validation", True, "Invalid category correctly rejected (422)")
        elif response.status_code == 403:
            record_test("Invalid Category Validation", False, "Access denied (403) - Cannot test validation without approved business")
        else:
            record_test("Invalid Category Validation", False, f"Expected 422, got: {response.status_code}")
            
    except Exception as e:
        record_test("Invalid Category Validation", False, f"Error: {str(e)}")
    
    # Test invalid VAT rate
    invalid_vat_data = {
        "name": "Test Item",
        "price": 50.0,
        "category": "Yemek",
        "vat_rate": 0.25
    }
    
    try:
        response = session.post(f"{BASE_URL}/business/menu", json=invalid_vat_data, headers=HEADERS)
        
        if response.status_code == 422:
            record_test("Invalid VAT Rate Validation", True, "Invalid VAT rate correctly rejected (422)")
        elif response.status_code == 403:
            record_test("Invalid VAT Rate Validation", False, "Access denied (403) - Cannot test validation without approved business")
        else:
            record_test("Invalid VAT Rate Validation", False, f"Expected 422, got: {response.status_code}")
            
    except Exception as e:
        record_test("Invalid VAT Rate Validation", False, f"Error: {str(e)}")

def test_menu_item_update():
    """Test menu item update"""
    print_test("Menu Item Update Testing")
    
    if not created_menu_items:
        record_test("Menu Item Update", False, "No menu items available for update")
        return
    
    item_id = created_menu_items[0]
    update_data = {
        "price": 85.50,
        "is_available": False
    }
    
    try:
        response = session.patch(f"{BASE_URL}/business/menu/{item_id}", json=update_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("price") == 85.50 and data.get("is_available") == False:
                record_test("Menu Item Update", True, "Successfully updated menu item")
            else:
                record_test("Menu Item Update", False, "Update values not reflected correctly")
        elif response.status_code == 403:
            record_test("Menu Item Update", False, "Access denied (403) - Business user may not be KYC approved")
        else:
            record_test("Menu Item Update", False, f"Status: {response.status_code} - {response.text}")
            
    except Exception as e:
        record_test("Menu Item Update", False, f"Error: {str(e)}")

def test_menu_item_deletion():
    """Test menu item deletion"""
    print_test("Menu Item Deletion Testing")
    
    if not created_menu_items:
        record_test("Menu Item Deletion", False, "No menu items available for deletion")
        return
    
    item_id = created_menu_items[0]
    
    try:
        response = session.delete(f"{BASE_URL}/business/menu/{item_id}?soft_delete=true", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                record_test("Menu Item Soft Delete", True, "Successfully soft deleted menu item")
            else:
                record_test("Menu Item Soft Delete", False, "Unexpected response format")
        elif response.status_code == 403:
            record_test("Menu Item Soft Delete", False, "Access denied (403) - Business user may not be KYC approved")
        else:
            record_test("Menu Item Soft Delete", False, f"Status: {response.status_code} - {response.text}")
            
    except Exception as e:
        record_test("Menu Item Soft Delete", False, f"Error: {str(e)}")

def test_public_endpoints():
    """Test public customer endpoints"""
    print_test("Public Endpoints Testing")
    
    if not business_user_id:
        record_test("Public Menu Access", False, "No business user ID available")
        return
    
    # Test public business menu access
    try:
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/business/{business_user_id}/menu", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            record_test("Public Menu Access", True, f"Retrieved {len(data) if isinstance(data, list) else 'data'} menu items without authentication")
        else:
            record_test("Public Menu Access", False, f"Status: {response.status_code} - {response.text}")
            
    except Exception as e:
        record_test("Public Menu Access", False, f"Error: {str(e)}")
    
    # Test public single menu item access
    if created_menu_items:
        item_id = created_menu_items[0]
        try:
            public_session = requests.Session()
            response = public_session.get(f"{BASE_URL}/business/menu/{item_id}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                record_test("Public Single Item Access", True, f"Retrieved menu item: {data.get('name', 'Unknown')}")
            else:
                record_test("Public Single Item Access", False, f"Status: {response.status_code} - {response.text}")
                
        except Exception as e:
            record_test("Public Single Item Access", False, f"Error: {str(e)}")

def test_authentication_security():
    """Test authentication and security"""
    print_test("Authentication Security Testing")
    
    # Test unauthenticated access
    try:
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/business/menu", headers=HEADERS)
        
        if response.status_code in [401, 403]:
            record_test("Unauthenticated Access Block", True, f"Unauthenticated access correctly denied ({response.status_code})")
        else:
            record_test("Unauthenticated Access Block", False, f"Expected 401/403, got: {response.status_code}")
            
    except Exception as e:
        record_test("Unauthenticated Access Block", False, f"Error: {str(e)}")

def test_system_health():
    """Test system health endpoints"""
    print_test("System Health Testing")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            record_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
        else:
            record_test("Health Check", False, f"Status: {response.status_code}")
    except Exception as e:
        record_test("Health Check", False, f"Error: {str(e)}")

def print_final_results():
    """Print comprehensive test results"""
    print_header("COMPREHENSIVE BUSINESS MENU CRUD TEST RESULTS")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT: Business Menu CRUD system is working excellently!{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}✅ GOOD: Business Menu CRUD system is working well with minor issues.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  MODERATE: Business Menu CRUD system has some issues that need attention.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL: Business Menu CRUD system has major issues requiring immediate attention.{Colors.END}")
    
    # Print failed tests details
    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ FAILED TESTS DETAILS:{Colors.END}")
        for result in test_results["details"]:
            if not result["success"]:
                print(f"   {Colors.RED}• {result['test']}: {result['message']}{Colors.END}")
    
    # Print successful tests summary
    if passed > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SUCCESSFUL TESTS SUMMARY:{Colors.END}")
        for result in test_results["details"]:
            if result["success"]:
                print(f"   {Colors.GREEN}• {result['test']}: {result['message']}{Colors.END}")

def main():
    """Main test execution"""
    print_header("FAZ 1 - COMPREHENSIVE BUSINESS MENU CRUD TESTING")
    print_info("Testing Business Menu CRUD system with existing business users")
    print_info(f"API Base URL: {BASE_URL}")
    
    # Execute test scenarios in order
    try:
        # 1. Test Business Authentication
        business_authenticated = test_business_authentication()
        
        # 2. Test Menu Endpoints Access
        menu_access = test_menu_endpoints_access()
        
        # 3. Test Menu Item Creation
        test_menu_item_creation()
        
        # 4. Test Menu Item Validation
        test_menu_item_validation()
        
        # 5. Test Menu Item Update
        test_menu_item_update()
        
        # 6. Test Menu Item Deletion
        test_menu_item_deletion()
        
        # 7. Test Public Endpoints
        test_public_endpoints()
        
        # 8. Test Authentication Security
        test_authentication_security()
        
        # 9. Test System Health
        test_system_health()
        
        if not business_authenticated:
            print_warning("No authenticated business user - limited testing performed")
        elif not menu_access:
            print_warning("Business user not KYC approved - CRUD testing limited")
            
    except KeyboardInterrupt:
        print_warning("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {str(e)}")
    finally:
        # Print final results
        print_final_results()

if __name__ == "__main__":
    main()