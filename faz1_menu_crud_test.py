#!/usr/bin/env python3
"""
FAZ 1 - COMPREHENSIVE BUSINESS MENU CRUD TESTING
==============================================

Testing newly implemented Business Menu CRUD system with:
- Authentication & Authorization (KYC approved business users)
- Menu Item Creation with validation
- Menu Item Retrieval 
- Menu Item Updates
- Menu Item Deletion (soft vs hard delete)
- Public Customer Endpoints
- Dual Collection Verification
- Security & Ownership Tests

Based on review request requirements.
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://kuryecini-admin-1.preview.emergentagent.com/api"
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
business_token = None
business_user_id = None
non_approved_business_token = None
created_menu_items = []

def authenticate_business_user():
    """Test 1.1 & 1.2: Business login and KYC approval verification"""
    global business_token, business_user_id
    
    print_test("Test 1.1: Business Authentication")
    
    # Try to find an existing approved business user or create one
    login_data = {
        "email": "testbusiness@kuryecini.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            business_token = data.get("access_token")
            user_data = data.get("user", {})
            business_user_id = user_data.get("id")
            
            # Check if user is KYC approved
            kyc_status = user_data.get("kyc_status", "pending")
            
            if kyc_status == "approved":
                record_test("Business Login", True, f"Authenticated approved business user: {user_data.get('email')}")
                return True
            else:
                record_test("Business Login", False, f"Business user not KYC approved (status: {kyc_status})")
                return False
        else:
            # Try to register a new business user
            print_info("Existing business not found, creating new business user...")
            return create_and_approve_business_user()
            
    except Exception as e:
        record_test("Business Login", False, f"Authentication failed: {str(e)}")
        return False

def create_and_approve_business_user():
    """Create and approve a new business user for testing"""
    global business_token, business_user_id
    
    # Generate unique email for testing
    unique_id = str(uuid.uuid4())[:8]
    business_email = f"testbusiness_{unique_id}@kuryecini.com"
    
    # Register new business
    registration_data = {
        "email": business_email,
        "password": "test123",
        "business_name": f"Test Restaurant {unique_id}",
        "tax_number": f"123456789{unique_id[:2]}",
        "address": "Test Address, Test District",
        "city": "İstanbul",
        "district": "Kadıköy",
        "business_category": "gida",
        "description": "Test restaurant for menu CRUD testing"
    }
    
    try:
        # Register business
        response = requests.post(f"{BASE_URL}/register/business", json=registration_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            business_token = data.get("access_token")
            user_data = data.get("user_data", {})
            business_user_id = user_data.get("id")
            
            print_info(f"Business registered: {business_email}")
            
            # Now we need to approve this business via admin
            # First login as admin
            admin_login = {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!"
            }
            
            admin_response = requests.post(f"{BASE_URL}/auth/login", json=admin_login, headers=HEADERS)
            
            if admin_response.status_code == 200:
                admin_data = admin_response.json()
                admin_token = admin_data.get("access_token")
                
                # Approve the business
                admin_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {admin_token}"
                }
                
                approval_data = {
                    "kyc_status": "approved"
                }
                
                approval_response = requests.patch(
                    f"{BASE_URL}/admin/businesses/{business_user_id}/status",
                    json=approval_data,
                    headers=admin_headers
                )
                
                if approval_response.status_code == 200:
                    record_test("Business Registration & Approval", True, f"Created and approved business: {business_email}")
                    return True
                else:
                    record_test("Business Approval", False, f"Failed to approve business: {approval_response.text}")
                    return False
            else:
                record_test("Admin Login", False, f"Failed to login as admin: {admin_response.text}")
                return False
                
        else:
            record_test("Business Registration", False, f"Failed to register business: {response.text}")
            return False
            
    except Exception as e:
        record_test("Business Registration", False, f"Registration failed: {str(e)}")
        return False

def test_non_approved_business_access():
    """Test 1.3: Test menu endpoint access with non-approved business user"""
    global non_approved_business_token
    
    print_test("Test 1.3: Non-Approved Business Access Control")
    
    # Create a non-approved business user
    unique_id = str(uuid.uuid4())[:8]
    non_approved_email = f"nonapproved_{unique_id}@kuryecini.com"
    
    registration_data = {
        "email": non_approved_email,
        "password": "test123",
        "business_name": f"Non-Approved Restaurant {unique_id}",
        "tax_number": f"987654321{unique_id[:2]}",
        "address": "Test Address",
        "city": "Ankara",
        "district": "Çankaya",
        "business_category": "gida",
        "description": "Non-approved test restaurant"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register/business", json=registration_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            non_approved_business_token = data.get("access_token")
            
            # Try to access menu endpoints with non-approved business
            non_approved_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {non_approved_business_token}"
            }
            
            # Test GET /api/business/menu
            menu_response = requests.get(f"{BASE_URL}/business/menu", headers=non_approved_headers)
            
            if menu_response.status_code == 403:
                record_test("Non-Approved Business Access Block", True, "Non-approved business correctly denied access (403)")
            else:
                record_test("Non-Approved Business Access Block", False, f"Non-approved business should be denied access, got: {menu_response.status_code}")
                
        else:
            record_test("Non-Approved Business Registration", False, f"Failed to register non-approved business: {response.text}")
            
    except Exception as e:
        record_test("Non-Approved Business Test", False, f"Test failed: {str(e)}")

def test_menu_item_creation():
    """Test 2: Menu Item Creation with various validation scenarios"""
    global business_token, created_menu_items
    
    if not business_token:
        print_error("No business token available for menu creation tests")
        return
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {business_token}"
    }
    
    # Test 2.1: Valid Creation (Yemek category)
    print_test("Test 2.1: Valid Menu Item Creation (Yemek)")
    
    valid_yemek_data = {
        "name": "Adana Kebap",
        "description": "Geleneksel Adana kebabı lavash ekmek ile",
        "price": 85.50,
        "currency": "TRY",
        "category": "Yemek",
        "tags": ["acılı", "et yemeği"],
        "image_url": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd",
        "is_available": True,
        "vat_rate": 0.18,
        "preparation_time": 25,
        "options": [
            {"name": "Ekstra acı", "price": 5.0},
            {"name": "Porsiyon büyütme", "price": 15.0}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/business/menu", json=valid_yemek_data, headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            created_menu_items.append(data.get("id"))
            record_test("Valid Yemek Creation", True, f"Created menu item: {data.get('name')} (ID: {data.get('id')})")
        else:
            record_test("Valid Yemek Creation", False, f"Failed to create menu item: {response.text}")
            
    except Exception as e:
        record_test("Valid Yemek Creation", False, f"Creation failed: {str(e)}")
    
    # Test 2.2: Valid Creation (İçecek category)
    print_test("Test 2.2: Valid Menu Item Creation (İçecek)")
    
    valid_icecek_data = {
        "name": "Ayran",
        "description": "Ev yapımı ayran",
        "price": 10.0,
        "currency": "TRY",
        "category": "İçecek",
        "tags": ["soğuk", "geleneksel"],
        "vat_rate": 0.08,
        "preparation_time": 2,
        "options": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/business/menu", json=valid_icecek_data, headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            created_menu_items.append(data.get("id"))
            record_test("Valid İçecek Creation", True, f"Created menu item: {data.get('name')} (ID: {data.get('id')})")
        else:
            record_test("Valid İçecek Creation", False, f"Failed to create menu item: {response.text}")
            
    except Exception as e:
        record_test("Valid İçecek Creation", False, f"Creation failed: {str(e)}")
    
    # Test 2.3: Invalid Category
    print_test("Test 2.3: Invalid Category Validation")
    
    invalid_category_data = {
        "name": "Test Item",
        "price": 50.0,
        "category": "InvalidCategory"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/business/menu", json=invalid_category_data, headers=auth_headers)
        
        if response.status_code == 422:
            record_test("Invalid Category Validation", True, "Invalid category correctly rejected (422)")
        else:
            record_test("Invalid Category Validation", False, f"Expected 422 for invalid category, got: {response.status_code}")
            
    except Exception as e:
        record_test("Invalid Category Validation", False, f"Validation test failed: {str(e)}")
    
    # Test 2.4: Invalid VAT Rate
    print_test("Test 2.4: Invalid VAT Rate Validation")
    
    invalid_vat_data = {
        "name": "Test Item",
        "price": 50.0,
        "category": "Yemek",
        "vat_rate": 0.25
    }
    
    try:
        response = requests.post(f"{BASE_URL}/business/menu", json=invalid_vat_data, headers=auth_headers)
        
        if response.status_code == 422:
            record_test("Invalid VAT Rate Validation", True, "Invalid VAT rate correctly rejected (422)")
        else:
            record_test("Invalid VAT Rate Validation", False, f"Expected 422 for invalid VAT rate, got: {response.status_code}")
            
    except Exception as e:
        record_test("Invalid VAT Rate Validation", False, f"Validation test failed: {str(e)}")
    
    # Test 2.5: Negative Price
    print_test("Test 2.5: Negative Price Validation")
    
    negative_price_data = {
        "name": "Test Item",
        "price": -10.0,
        "category": "Yemek"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/business/menu", json=negative_price_data, headers=auth_headers)
        
        if response.status_code == 422:
            record_test("Negative Price Validation", True, "Negative price correctly rejected (422)")
        else:
            record_test("Negative Price Validation", False, f"Expected 422 for negative price, got: {response.status_code}")
            
    except Exception as e:
        record_test("Negative Price Validation", False, f"Validation test failed: {str(e)}")

def test_menu_item_retrieval():
    """Test 3: Menu Item Retrieval"""
    global business_token
    
    if not business_token:
        print_error("No business token available for menu retrieval tests")
        return
    
    print_test("Test 3.1: Get Business Menu Items")
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {business_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/business/menu", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                record_test("Menu Retrieval", True, f"Retrieved {len(data)} menu items")
                
                # Check field presence in first item if available
                if data:
                    first_item = data[0]
                    required_fields = ["id", "name", "description", "price", "currency", "category", "tags", "vat_rate", "options", "preparation_time"]
                    missing_fields = [field for field in required_fields if field not in first_item]
                    
                    if not missing_fields:
                        record_test("Menu Item Fields", True, "All required fields present in menu items")
                    else:
                        record_test("Menu Item Fields", False, f"Missing fields: {missing_fields}")
                        
                    # Check backward compatibility (old 'title' field should map to 'name')
                    if first_item.get("name"):
                        record_test("Backward Compatibility", True, "Name field properly mapped from title")
                    else:
                        record_test("Backward Compatibility", False, "Name field missing or not mapped")
            else:
                record_test("Menu Retrieval", False, f"Expected array, got: {type(data)}")
        else:
            record_test("Menu Retrieval", False, f"Failed to retrieve menu: {response.text}")
            
    except Exception as e:
        record_test("Menu Retrieval", False, f"Retrieval failed: {str(e)}")

def test_menu_item_update():
    """Test 4: Menu Item Update"""
    global business_token, created_menu_items
    
    if not business_token or not created_menu_items:
        print_error("No business token or menu items available for update tests")
        return
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {business_token}"
    }
    
    item_id = created_menu_items[0]  # Use first created item
    
    # Test 4.1: Partial Update
    print_test("Test 4.1: Partial Menu Item Update")
    
    partial_update_data = {
        "price": 95.50,
        "is_available": False
    }
    
    try:
        response = requests.patch(f"{BASE_URL}/business/menu/{item_id}", json=partial_update_data, headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("price") == 95.50 and data.get("is_available") == False:
                record_test("Partial Update", True, f"Successfully updated price and availability")
            else:
                record_test("Partial Update", False, f"Update values not reflected correctly")
        else:
            record_test("Partial Update", False, f"Failed to update menu item: {response.text}")
            
    except Exception as e:
        record_test("Partial Update", False, f"Update failed: {str(e)}")
    
    # Test 4.2: Full Update with Options
    print_test("Test 4.2: Full Menu Item Update with Options")
    
    full_update_data = {
        "name": "Adana Kebap Spesyal",
        "description": "Premium Adana kebabı",
        "price": 110.0,
        "category": "Yemek",
        "tags": ["premium", "acılı", "et yemeği"],
        "vat_rate": 0.18,
        "options": [
            {"name": "Ekstra acı", "price": 5.0},
            {"name": "İkili porsiyon", "price": 90.0}
        ]
    }
    
    try:
        response = requests.patch(f"{BASE_URL}/business/menu/{item_id}", json=full_update_data, headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("name") == "Adana Kebap Spesyal" and 
                data.get("price") == 110.0 and 
                len(data.get("options", [])) == 2):
                record_test("Full Update with Options", True, f"Successfully updated all fields including options")
            else:
                record_test("Full Update with Options", False, f"Update values not reflected correctly")
        else:
            record_test("Full Update with Options", False, f"Failed to update menu item: {response.text}")
            
    except Exception as e:
        record_test("Full Update with Options", False, f"Update failed: {str(e)}")
    
    # Test 4.3: Invalid Category Update
    print_test("Test 4.3: Invalid Category Update Validation")
    
    invalid_update_data = {
        "category": "InvalidCategory"
    }
    
    try:
        response = requests.patch(f"{BASE_URL}/business/menu/{item_id}", json=invalid_update_data, headers=auth_headers)
        
        if response.status_code == 422:
            record_test("Invalid Category Update", True, "Invalid category update correctly rejected (422)")
        else:
            record_test("Invalid Category Update", False, f"Expected 422 for invalid category update, got: {response.status_code}")
            
    except Exception as e:
        record_test("Invalid Category Update", False, f"Validation test failed: {str(e)}")

def test_menu_item_deletion():
    """Test 5: Menu Item Deletion"""
    global business_token, created_menu_items
    
    if not business_token or len(created_menu_items) < 2:
        print_error("Need at least 2 menu items for deletion tests")
        return
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {business_token}"
    }
    
    # Test 5.1: Soft Delete (default)
    print_test("Test 5.1: Soft Delete Menu Item")
    
    soft_delete_item_id = created_menu_items[0]
    
    try:
        response = requests.delete(f"{BASE_URL}/business/menu/{soft_delete_item_id}?soft_delete=true", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "soft delete" in data.get("message", "").lower():
                record_test("Soft Delete", True, "Menu item soft deleted successfully")
                
                # Verify item still exists but is_available=False
                check_response = requests.get(f"{BASE_URL}/business/menu", headers=auth_headers)
                if check_response.status_code == 200:
                    menu_items = check_response.json()
                    soft_deleted_item = next((item for item in menu_items if item["id"] == soft_delete_item_id), None)
                    
                    if soft_deleted_item and not soft_deleted_item.get("is_available"):
                        record_test("Soft Delete Verification", True, "Item still exists but is_available=False")
                    else:
                        record_test("Soft Delete Verification", False, "Item not found or still available after soft delete")
            else:
                record_test("Soft Delete", False, f"Unexpected response: {data}")
        else:
            record_test("Soft Delete", False, f"Failed to soft delete: {response.text}")
            
    except Exception as e:
        record_test("Soft Delete", False, f"Soft delete failed: {str(e)}")
    
    # Test 5.2: Hard Delete
    print_test("Test 5.2: Hard Delete Menu Item")
    
    if len(created_menu_items) > 1:
        hard_delete_item_id = created_menu_items[1]
        
        try:
            response = requests.delete(f"{BASE_URL}/business/menu/{hard_delete_item_id}?soft_delete=false", headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "permanently deleted" in data.get("message", "").lower():
                    record_test("Hard Delete", True, "Menu item permanently deleted successfully")
                    
                    # Verify item no longer exists
                    check_response = requests.get(f"{BASE_URL}/business/menu", headers=auth_headers)
                    if check_response.status_code == 200:
                        menu_items = check_response.json()
                        hard_deleted_item = next((item for item in menu_items if item["id"] == hard_delete_item_id), None)
                        
                        if not hard_deleted_item:
                            record_test("Hard Delete Verification", True, "Item permanently removed from menu")
                        else:
                            record_test("Hard Delete Verification", False, "Item still exists after hard delete")
                else:
                    record_test("Hard Delete", False, f"Unexpected response: {data}")
            else:
                record_test("Hard Delete", False, f"Failed to hard delete: {response.text}")
                
        except Exception as e:
            record_test("Hard Delete", False, f"Hard delete failed: {str(e)}")

def test_public_customer_endpoints():
    """Test 6: Public Customer Endpoints"""
    global business_user_id
    
    if not business_user_id:
        print_error("No business user ID available for public endpoint tests")
        return
    
    # Test 6.1: GET /api/business/{business_id}/menu
    print_test("Test 6.1: Public Business Menu Access")
    
    try:
        response = requests.get(f"{BASE_URL}/business/{business_user_id}/menu", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                # Check that only available items are shown
                available_items = [item for item in data if item.get("is_available", True)]
                
                if len(available_items) == len(data):
                    record_test("Public Menu Access", True, f"Retrieved {len(data)} available menu items without authentication")
                else:
                    record_test("Public Menu Access", False, f"Some unavailable items returned: {len(data) - len(available_items)}")
                    
                # Check sorting (by category then name)
                if data:
                    is_sorted = all(
                        data[i].get("category", "") <= data[i+1].get("category", "") 
                        for i in range(len(data)-1)
                    )
                    
                    if is_sorted:
                        record_test("Public Menu Sorting", True, "Menu items properly sorted by category")
                    else:
                        record_test("Public Menu Sorting", False, "Menu items not properly sorted")
            else:
                record_test("Public Menu Access", False, f"Expected array, got: {type(data)}")
        else:
            record_test("Public Menu Access", False, f"Failed to access public menu: {response.text}")
            
    except Exception as e:
        record_test("Public Menu Access", False, f"Public access failed: {str(e)}")
    
    # Test 6.2: GET /api/business/{business_id}/menu?category=Yemek
    print_test("Test 6.2: Public Menu Category Filter")
    
    try:
        response = requests.get(f"{BASE_URL}/business/{business_user_id}/menu?category=Yemek", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                # Check that all items are in Yemek category
                yemek_items = [item for item in data if item.get("category") == "Yemek"]
                
                if len(yemek_items) == len(data):
                    record_test("Public Menu Category Filter", True, f"Category filter working: {len(data)} Yemek items")
                else:
                    record_test("Public Menu Category Filter", False, f"Category filter not working properly")
            else:
                record_test("Public Menu Category Filter", False, f"Expected array, got: {type(data)}")
        else:
            record_test("Public Menu Category Filter", False, f"Failed to filter by category: {response.text}")
            
    except Exception as e:
        record_test("Public Menu Category Filter", False, f"Category filter failed: {str(e)}")
    
    # Test 6.3: GET /api/business/menu/{item_id}
    print_test("Test 6.3: Public Single Menu Item Access")
    
    if created_menu_items:
        item_id = created_menu_items[0] if len(created_menu_items) > 0 else None
        
        if item_id:
            try:
                response = requests.get(f"{BASE_URL}/business/menu/{item_id}", headers=HEADERS)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("id") == item_id:
                        record_test("Public Single Item Access", True, f"Retrieved single menu item: {data.get('name')}")
                    else:
                        record_test("Public Single Item Access", False, f"Item ID mismatch")
                else:
                    record_test("Public Single Item Access", False, f"Failed to access single item: {response.text}")
                    
            except Exception as e:
                record_test("Public Single Item Access", False, f"Single item access failed: {str(e)}")

def test_dual_collection_verification():
    """Test 7: Dual Collection Verification"""
    global business_token, created_menu_items
    
    print_test("Test 7: Dual Collection Management Verification")
    
    # This test would require direct database access to verify both collections
    # For now, we'll test the behavior indirectly by checking consistency
    
    if not business_token:
        print_warning("Cannot verify dual collection without business token")
        return
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {business_token}"
    }
    
    # Create a test item and verify it appears in both business and public endpoints
    test_item_data = {
        "name": "Dual Collection Test Item",
        "description": "Testing dual collection management",
        "price": 25.0,
        "category": "Yemek",
        "vat_rate": 0.18
    }
    
    try:
        # Create item
        create_response = requests.post(f"{BASE_URL}/business/menu", json=test_item_data, headers=auth_headers)
        
        if create_response.status_code == 200:
            created_item = create_response.json()
            item_id = created_item.get("id")
            created_menu_items.append(item_id)
            
            # Check if item appears in business menu
            business_menu_response = requests.get(f"{BASE_URL}/business/menu", headers=auth_headers)
            
            # Check if item appears in public menu
            public_menu_response = requests.get(f"{BASE_URL}/business/{business_user_id}/menu", headers=HEADERS)
            
            if (business_menu_response.status_code == 200 and 
                public_menu_response.status_code == 200):
                
                business_items = business_menu_response.json()
                public_items = public_menu_response.json()
                
                business_item = next((item for item in business_items if item["id"] == item_id), None)
                public_item = next((item for item in public_items if item["id"] == item_id), None)
                
                if business_item and public_item:
                    record_test("Dual Collection Creation", True, "Item appears in both business and public endpoints")
                else:
                    record_test("Dual Collection Creation", False, f"Item missing from endpoints - Business: {bool(business_item)}, Public: {bool(public_item)}")
            else:
                record_test("Dual Collection Creation", False, "Failed to retrieve menus for verification")
                
        else:
            record_test("Dual Collection Creation", False, f"Failed to create test item: {create_response.text}")
            
    except Exception as e:
        record_test("Dual Collection Creation", False, f"Dual collection test failed: {str(e)}")

def test_security_and_ownership():
    """Test 8: Security & Ownership Tests"""
    global business_token, business_user_id, created_menu_items
    
    print_test("Test 8: Security & Ownership Verification")
    
    if not business_token or not created_menu_items:
        print_warning("Cannot test security without business token and menu items")
        return
    
    # Create a second business user to test cross-business access
    unique_id = str(uuid.uuid4())[:8]
    second_business_email = f"testbusiness2_{unique_id}@kuryecini.com"
    
    registration_data = {
        "email": second_business_email,
        "password": "test123",
        "business_name": f"Second Test Restaurant {unique_id}",
        "tax_number": f"555666777{unique_id[:2]}",
        "address": "Second Test Address",
        "city": "Ankara",
        "district": "Çankaya",
        "business_category": "gida",
        "description": "Second test restaurant for security testing"
    }
    
    try:
        # Register second business
        response = requests.post(f"{BASE_URL}/register/business", json=registration_data, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            second_business_token = data.get("access_token")
            
            # Approve second business
            admin_login = {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!"
            }
            
            admin_response = requests.post(f"{BASE_URL}/auth/login", json=admin_login, headers=HEADERS)
            
            if admin_response.status_code == 200:
                admin_data = admin_response.json()
                admin_token = admin_data.get("access_token")
                
                admin_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {admin_token}"
                }
                
                second_business_user_id = data.get("user_data", {}).get("id")
                
                approval_data = {"kyc_status": "approved"}
                
                approval_response = requests.patch(
                    f"{BASE_URL}/admin/businesses/{second_business_user_id}/status",
                    json=approval_data,
                    headers=admin_headers
                )
                
                if approval_response.status_code == 200:
                    # Test 8.1: Business A creates item, Business B tries to update it
                    print_test("Test 8.1: Cross-Business Update Prevention")
                    
                    second_business_headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {second_business_token}"
                    }
                    
                    item_id = created_menu_items[0]
                    update_data = {"price": 999.99}
                    
                    cross_update_response = requests.patch(
                        f"{BASE_URL}/business/menu/{item_id}",
                        json=update_data,
                        headers=second_business_headers
                    )
                    
                    if cross_update_response.status_code == 404:
                        record_test("Cross-Business Update Prevention", True, "Business B correctly denied access to Business A's menu item (404)")
                    else:
                        record_test("Cross-Business Update Prevention", False, f"Expected 404, got: {cross_update_response.status_code}")
                    
                    # Test 8.2: Business A creates item, Business B tries to delete it
                    print_test("Test 8.2: Cross-Business Delete Prevention")
                    
                    cross_delete_response = requests.delete(
                        f"{BASE_URL}/business/menu/{item_id}",
                        headers=second_business_headers
                    )
                    
                    if cross_delete_response.status_code == 404:
                        record_test("Cross-Business Delete Prevention", True, "Business B correctly denied access to delete Business A's menu item (404)")
                    else:
                        record_test("Cross-Business Delete Prevention", False, f"Expected 404, got: {cross_delete_response.status_code}")
                        
                else:
                    record_test("Second Business Approval", False, "Failed to approve second business for security testing")
            else:
                record_test("Admin Login for Security Test", False, "Failed to login as admin for security testing")
        else:
            record_test("Second Business Registration", False, f"Failed to register second business: {response.text}")
            
    except Exception as e:
        record_test("Security Testing", False, f"Security test failed: {str(e)}")

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
    print_info("Testing Business Menu CRUD system with comprehensive validation")
    print_info(f"API Base URL: {BASE_URL}")
    
    # Execute test scenarios in order
    try:
        # 1. Authentication & Authorization Tests
        if authenticate_business_user():
            test_non_approved_business_access()
            
            # 2. Menu Item Creation Tests
            test_menu_item_creation()
            
            # 3. Menu Item Retrieval Tests
            test_menu_item_retrieval()
            
            # 4. Menu Item Update Tests
            test_menu_item_update()
            
            # 5. Menu Item Deletion Tests
            test_menu_item_deletion()
            
            # 6. Public Customer Endpoints Tests
            test_public_customer_endpoints()
            
            # 7. Dual Collection Verification Tests
            test_dual_collection_verification()
            
            # 8. Security & Ownership Tests
            test_security_and_ownership()
        else:
            print_error("Authentication failed - skipping remaining tests")
            
    except KeyboardInterrupt:
        print_warning("\nTesting interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error during testing: {str(e)}")
    finally:
        # Print final results
        print_final_results()

if __name__ == "__main__":
    main()