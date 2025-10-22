#!/usr/bin/env python3
"""
AKSARAY İŞLETME GÖRÜNÜRLÜK PROBLEMİ - KAPSAMLI ANALİZ
Comprehensive investigation of business visibility issues in Aksaray

ANALYSIS SCOPE:
1. Current Business Status Analysis (GET /api/businesses vs GET /api/admin/users)
2. KYC Approval System Check
3. City Filtering Test (/api/businesses?city=Aksaray)
4. Create New Test Business in Aksaray and Test Approval Flow

USER PROBLEM: "işletme Aksaray'da açıldı konum Aksaray adres Aksaray yemek ekledim yok aynı gene"
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://courier-dashboard-3.preview.emergentagent.com/api"
ADMIN_PASSWORD = "6851"
TEST_BUSINESS_EMAIL = f"aksaray-test-{int(time.time())}@example.com"
TEST_BUSINESS_PASSWORD = "test123"

class AksarayBusinessVisibilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.business_token = None
        self.test_business_id = None
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["test_details"].append(test_result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if response_data and isinstance(response_data, dict):
            print(f"    Data: {json.dumps(response_data, indent=2, ensure_ascii=False)[:200]}...")
        print()
    
    def authenticate_admin(self):
        """Authenticate as admin"""
        print("🔐 ADMIN AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": "admin@kuryecini.com",
                "password": "KuryeciniAdmin2024!"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_test(
                    "Admin Authentication",
                    True,
                    f"Admin login successful. Token length: {len(self.admin_token) if self.admin_token else 0} chars"
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication",
                    False,
                    f"Admin login failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Admin Authentication",
                False,
                f"Exception during admin login: {str(e)}"
            )
            return False
    
    def analyze_current_business_status(self):
        """Analyze current business status - customer view vs admin view"""
        print("📊 CURRENT BUSINESS STATUS ANALYSIS")
        print("=" * 50)
        
        # 1. Customer view - GET /api/businesses (what customers see)
        try:
            customer_session = requests.Session()  # No auth for public endpoint
            response = customer_session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                customer_businesses = response.json()
                aksaray_customer_businesses = [b for b in customer_businesses if 
                                             b.get('city', '').lower() == 'aksaray' or 
                                             b.get('city_normalized', '').lower() == 'aksaray']
                
                self.log_test(
                    "Customer View - All Businesses",
                    True,
                    f"Customers see {len(customer_businesses)} total businesses, {len(aksaray_customer_businesses)} in Aksaray",
                    {
                        "total_businesses": len(customer_businesses),
                        "aksaray_businesses": len(aksaray_customer_businesses),
                        "aksaray_business_names": [b.get('name', 'Unknown') for b in aksaray_customer_businesses]
                    }
                )
            else:
                self.log_test(
                    "Customer View - All Businesses",
                    False,
                    f"Failed to get customer businesses. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Customer View - All Businesses",
                False,
                f"Exception during customer business fetch: {str(e)}"
            )
        
        # 2. Admin view - GET /api/admin/users (all business records)
        try:
            if not self.admin_token:
                self.log_test(
                    "Admin View - All Business Records",
                    False,
                    "Admin authentication required"
                )
                return
            
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                all_users = response.json()
                all_businesses = [u for u in all_users if u.get('role') == 'business']
                aksaray_businesses = [b for b in all_businesses if 
                                    b.get('city', '').lower() == 'aksaray' or 
                                    b.get('city_normalized', '').lower() == 'aksaray']
                
                # Analyze KYC status
                kyc_status_breakdown = {}
                for business in aksaray_businesses:
                    kyc_status = business.get('kyc_status', 'unknown')
                    kyc_status_breakdown[kyc_status] = kyc_status_breakdown.get(kyc_status, 0) + 1
                
                self.log_test(
                    "Admin View - All Business Records",
                    True,
                    f"Admin sees {len(all_businesses)} total businesses, {len(aksaray_businesses)} in Aksaray",
                    {
                        "total_businesses": len(all_businesses),
                        "aksaray_businesses": len(aksaray_businesses),
                        "aksaray_kyc_breakdown": kyc_status_breakdown,
                        "aksaray_business_details": [
                            {
                                "name": b.get('business_name', 'Unknown'),
                                "email": b.get('email', 'Unknown'),
                                "kyc_status": b.get('kyc_status', 'unknown'),
                                "city": b.get('city', 'Unknown'),
                                "city_normalized": b.get('city_normalized', 'Unknown')
                            } for b in aksaray_businesses
                        ]
                    }
                )
                
                # Detailed KYC analysis
                pending_count = kyc_status_breakdown.get('pending', 0)
                approved_count = kyc_status_breakdown.get('approved', 0)
                rejected_count = kyc_status_breakdown.get('rejected', 0)
                
                self.log_test(
                    "Aksaray KYC Status Analysis",
                    True,
                    f"Pending: {pending_count}, Approved: {approved_count}, Rejected: {rejected_count}",
                    {
                        "root_cause_identified": pending_count > 0 and approved_count == 0,
                        "issue_description": "Businesses registered but not KYC approved" if pending_count > 0 and approved_count == 0 else "Mixed KYC status"
                    }
                )
                
            else:
                self.log_test(
                    "Admin View - All Business Records",
                    False,
                    f"Failed to get admin business records. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Admin View - All Business Records",
                False,
                f"Exception during admin business fetch: {str(e)}"
            )
    
    def test_city_filtering(self):
        """Test city filtering functionality"""
        print("🏙️ CITY FILTERING TEST")
        print("=" * 50)
        
        # Test various city parameter formats
        city_variations = [
            "Aksaray",
            "aksaray", 
            "AKSARAY",
            "Aksary",  # Common misspelling
            "aksary"   # Common misspelling lowercase
        ]
        
        for city_param in city_variations:
            try:
                customer_session = requests.Session()
                response = customer_session.get(f"{BACKEND_URL}/businesses", params={"city": city_param})
                
                if response.status_code == 200:
                    businesses = response.json()
                    self.log_test(
                        f"City Filter - '{city_param}'",
                        True,
                        f"Found {len(businesses)} businesses for city parameter '{city_param}'",
                        {
                            "city_param": city_param,
                            "business_count": len(businesses),
                            "business_names": [b.get('name', 'Unknown') for b in businesses[:3]]  # First 3
                        }
                    )
                else:
                    self.log_test(
                        f"City Filter - '{city_param}'",
                        False,
                        f"City filtering failed for '{city_param}'. Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"City Filter - '{city_param}'",
                    False,
                    f"Exception during city filtering: {str(e)}"
                )
        
        # Test city normalization working
        try:
            # Check if city normalization is working by testing the normalize function
            from utils.city_normalize import normalize_city_name
            
            test_cities = ["Aksaray", "AKSARAY", "aksaray", "Aksary"]
            normalization_results = {}
            
            for city in test_cities:
                try:
                    normalized = normalize_city_name(city)
                    normalization_results[city] = normalized
                except Exception as e:
                    normalization_results[city] = f"Error: {str(e)}"
            
            self.log_test(
                "City Normalization Function",
                True,
                "City normalization function working",
                normalization_results
            )
            
        except ImportError:
            self.log_test(
                "City Normalization Function",
                False,
                "City normalization module not found - may need to check utils/city_normalize.py"
            )
        except Exception as e:
            self.log_test(
                "City Normalization Function",
                False,
                f"Exception testing city normalization: {str(e)}"
            )
    
    def test_kyc_approval_system(self):
        """Test KYC approval system functionality"""
        print("✅ KYC APPROVAL SYSTEM TEST")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test(
                "KYC Approval System",
                False,
                "Admin authentication required"
            )
            return
        
        # 1. Get pending KYC businesses
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users")
            
            if response.status_code == 200:
                all_users = response.json()
                pending_businesses = [u for u in all_users if 
                                    u.get('role') == 'business' and 
                                    u.get('kyc_status') == 'pending' and
                                    (u.get('city', '').lower() == 'aksaray' or 
                                     u.get('city_normalized', '').lower() == 'aksaray')]
                
                self.log_test(
                    "Get Pending Aksaray Businesses",
                    True,
                    f"Found {len(pending_businesses)} pending Aksaray businesses",
                    {
                        "pending_count": len(pending_businesses),
                        "business_details": [
                            {
                                "id": b.get('id'),
                                "name": b.get('business_name'),
                                "email": b.get('email'),
                                "kyc_status": b.get('kyc_status')
                            } for b in pending_businesses[:3]  # First 3
                        ]
                    }
                )
                
                # 2. Test KYC approval endpoint if we have pending businesses
                if pending_businesses:
                    test_business = pending_businesses[0]
                    business_id = test_business.get('id')
                    
                    if business_id:
                        try:
                            # Test approval
                            approval_data = {
                                "status": "approved",
                                "notes": "Test approval for visibility investigation"
                            }
                            
                            response = self.session.patch(
                                f"{BACKEND_URL}/admin/users/{business_id}/approve"
                            )
                            
                            if response.status_code == 200:
                                self.log_test(
                                    "KYC Approval Endpoint Test",
                                    True,
                                    f"Successfully approved business {business_id}",
                                    response.json()
                                )
                                
                                # Verify approval worked by checking customer view
                                time.sleep(1)  # Brief delay
                                customer_session = requests.Session()
                                customer_response = customer_session.get(f"{BACKEND_URL}/businesses")
                                
                                if customer_response.status_code == 200:
                                    customer_businesses = customer_response.json()
                                    approved_business = next((b for b in customer_businesses if 
                                                           b.get('name') == test_business.get('business_name')), None)
                                    
                                    self.log_test(
                                        "KYC Approval Verification",
                                        approved_business is not None,
                                        f"Approved business {'now visible' if approved_business else 'still not visible'} to customers",
                                        {"business_found": approved_business is not None}
                                    )
                                
                            else:
                                self.log_test(
                                    "KYC Approval Endpoint Test",
                                    False,
                                    f"KYC approval failed. Status: {response.status_code}",
                                    response.text
                                )
                        except Exception as e:
                            self.log_test(
                                "KYC Approval Endpoint Test",
                                False,
                                f"Exception during KYC approval: {str(e)}"
                            )
                else:
                    self.log_test(
                        "KYC Approval Test",
                        False,
                        "No pending Aksaray businesses found to test approval"
                    )
                    
            else:
                self.log_test(
                    "Get Pending Aksaray Businesses",
                    False,
                    f"Failed to get users. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "KYC Approval System",
                False,
                f"Exception during KYC system test: {str(e)}"
            )
    
    def create_test_business_aksaray(self):
        """Create a new test business in Aksaray"""
        print("🏪 CREATE TEST BUSINESS IN AKSARAY")
        print("=" * 50)
        
        try:
            business_data = {
                "email": TEST_BUSINESS_EMAIL,
                "password": TEST_BUSINESS_PASSWORD,
                "business_name": f"Aksaray Test Restoranı {int(time.time())}",
                "tax_number": f"1234567{int(time.time()) % 1000:03d}",
                "address": "Aksaray Merkez, Test Sokak No:123",
                "city": "Aksaray",
                "business_category": "gida",
                "description": "Test restoranı - Aksaray görünürlük problemi araştırması için"
            }
            
            # Use a separate session for registration (no auth needed)
            reg_session = requests.Session()
            response = reg_session.post(f"{BACKEND_URL}/register/business", json=business_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_business_id = data.get("user_data", {}).get("id")
                self.business_token = data.get("access_token")
                
                self.log_test(
                    "Create Test Business in Aksaray",
                    True,
                    f"Successfully created business '{business_data['business_name']}' with ID: {self.test_business_id}",
                    {
                        "business_id": self.test_business_id,
                        "business_name": business_data['business_name'],
                        "city": business_data['city'],
                        "email": business_data['email']
                    }
                )
                
                # Add some test products to the business
                self.add_test_products()
                
                return True
            else:
                self.log_test(
                    "Create Test Business in Aksaray",
                    False,
                    f"Business creation failed. Status: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Create Test Business in Aksaray",
                False,
                f"Exception during business creation: {str(e)}"
            )
            return False
    
    def add_test_products(self):
        """Add test products to the created business"""
        print("🍽️ ADD TEST PRODUCTS")
        print("=" * 50)
        
        if not self.business_token or not self.test_business_id:
            self.log_test(
                "Add Test Products",
                False,
                "Business authentication required"
            )
            return
        
        # Create session with business token
        business_session = requests.Session()
        business_session.headers.update({
            "Authorization": f"Bearer {self.business_token}"
        })
        
        test_products = [
            {
                "name": "Aksaray Kebabı",
                "description": "Geleneksel Aksaray usulü kebap",
                "price": 45.0,
                "category": "Ana Yemek",
                "preparation_time_minutes": 20,
                "is_available": True
            },
            {
                "name": "Pide",
                "description": "Taze hamurdan yapılmış pide",
                "price": 35.0,
                "category": "Ana Yemek", 
                "preparation_time_minutes": 15,
                "is_available": True
            },
            {
                "name": "Ayran",
                "description": "Ev yapımı ayran",
                "price": 8.0,
                "category": "İçecek",
                "preparation_time_minutes": 2,
                "is_available": True
            }
        ]
        
        created_products = []
        
        for product_data in test_products:
            try:
                response = business_session.post(f"{BACKEND_URL}/products", json=product_data)
                
                if response.status_code == 200:
                    created_product = response.json()
                    created_products.append(created_product)
                    
                    self.log_test(
                        f"Create Product - {product_data['name']}",
                        True,
                        f"Successfully created product '{product_data['name']}' (₺{product_data['price']})",
                        {"product_id": created_product.get("id"), "name": product_data['name']}
                    )
                else:
                    self.log_test(
                        f"Create Product - {product_data['name']}",
                        False,
                        f"Product creation failed. Status: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Create Product - {product_data['name']}",
                    False,
                    f"Exception during product creation: {str(e)}"
                )
        
        self.log_test(
            "Test Products Summary",
            len(created_products) > 0,
            f"Created {len(created_products)} out of {len(test_products)} test products",
            {"created_count": len(created_products), "total_count": len(test_products)}
        )
    
    def test_business_approval_flow(self):
        """Test the complete business approval flow"""
        print("🔄 BUSINESS APPROVAL FLOW TEST")
        print("=" * 50)
        
        if not self.test_business_id or not self.admin_token:
            self.log_test(
                "Business Approval Flow",
                False,
                "Test business and admin authentication required"
            )
            return
        
        # 1. Verify business is initially not visible to customers
        try:
            customer_session = requests.Session()
            response = customer_session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                test_business_visible = any(b.get('id') == self.test_business_id for b in businesses)
                
                self.log_test(
                    "Initial Visibility Check",
                    not test_business_visible,
                    f"Test business {'visible' if test_business_visible else 'not visible'} to customers (expected: not visible)",
                    {"business_visible": test_business_visible}
                )
        except Exception as e:
            self.log_test(
                "Initial Visibility Check",
                False,
                f"Exception during initial visibility check: {str(e)}"
            )
        
        # 2. Approve the business via admin
        try:
            approval_data = {
                "status": "approved",
                "notes": "Approved for Aksaray visibility testing"
            }
            
            response = self.session.patch(
                f"{BACKEND_URL}/admin/users/{self.test_business_id}/approve"
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Admin Business Approval",
                    True,
                    f"Successfully approved test business {self.test_business_id}",
                    response.json()
                )
                
                # 3. Verify business is now visible to customers
                time.sleep(2)  # Brief delay for changes to propagate
                
                customer_session = requests.Session()
                response = customer_session.get(f"{BACKEND_URL}/businesses")
                
                if response.status_code == 200:
                    businesses = response.json()
                    test_business = next((b for b in businesses if b.get('id') == self.test_business_id), None)
                    
                    self.log_test(
                        "Post-Approval Visibility Check",
                        test_business is not None,
                        f"Test business {'now visible' if test_business else 'still not visible'} to customers after approval",
                        {
                            "business_visible": test_business is not None,
                            "business_details": test_business if test_business else None
                        }
                    )
                    
                    # 4. Test city filtering with approved business
                    if test_business:
                        city_response = customer_session.get(f"{BACKEND_URL}/businesses", params={"city": "Aksaray"})
                        
                        if city_response.status_code == 200:
                            aksaray_businesses = city_response.json()
                            test_business_in_filter = any(b.get('id') == self.test_business_id for b in aksaray_businesses)
                            
                            self.log_test(
                                "City Filter with Approved Business",
                                test_business_in_filter,
                                f"Test business {'found' if test_business_in_filter else 'not found'} in Aksaray city filter",
                                {
                                    "aksaray_business_count": len(aksaray_businesses),
                                    "test_business_in_filter": test_business_in_filter
                                }
                            )
                
            else:
                self.log_test(
                    "Admin Business Approval",
                    False,
                    f"Business approval failed. Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test(
                "Business Approval Flow",
                False,
                f"Exception during approval flow: {str(e)}"
            )
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis of Aksaray business visibility issue"""
        print("🚀 AKSARAY İŞLETME GÖRÜNÜRLÜK PROBLEMİ - KAPSAMLI ANALİZ")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Analysis Time: {datetime.now().isoformat()}")
        print(f"User Problem: 'işletme Aksaray'da açıldı konum Aksaray adres Aksaray yemek ekledim yok aynı gene'")
        print("=" * 80)
        print()
        
        # Step 1: Admin Authentication
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with full analysis.")
            return self.generate_final_report()
        
        # Step 2: Current Business Status Analysis
        self.analyze_current_business_status()
        
        # Step 3: City Filtering Test
        self.test_city_filtering()
        
        # Step 4: KYC Approval System Test
        self.test_kyc_approval_system()
        
        # Step 5: Create New Test Business
        if self.create_test_business_aksaray():
            # Step 6: Test Complete Approval Flow
            self.test_business_approval_flow()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 80)
        print("📊 AKSARAY İŞLETME GÖRÜNÜRLÜK ANALİZİ SONUÇLARI")
        print("=" * 80)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Toplam Test: {total}")
        print(f"Başarılı: {passed} ✅")
        print(f"Başarısız: {failed} ❌")
        print(f"Başarı Oranı: {success_rate:.1f}%")
        print()
        
        # Root Cause Analysis
        print("🔍 KÖK NEDEN ANALİZİ:")
        print("-" * 40)
        
        # Look for specific patterns in test results
        kyc_analysis = next((t for t in self.results["test_details"] if "KYC Status Analysis" in t["test"]), None)
        customer_view = next((t for t in self.results["test_details"] if "Customer View" in t["test"]), None)
        admin_view = next((t for t in self.results["test_details"] if "Admin View" in t["test"]), None)
        
        if kyc_analysis and customer_view and admin_view:
            kyc_data = kyc_analysis.get("response_data", {})
            customer_data = customer_view.get("response_data", {})
            admin_data = admin_view.get("response_data", {})
            
            print(f"• Müşteri Görünümü: {customer_data.get('aksaray_businesses', 0)} Aksaray işletmesi")
            print(f"• Admin Görünümü: {admin_data.get('aksaray_businesses', 0)} Aksaray işletmesi")
            print(f"• KYC Durumu: {kyc_data.get('aksaray_kyc_breakdown', {})}")
            
            if kyc_data.get("root_cause_identified"):
                print("• ✅ KÖK NEDEN TESPİT EDİLDİ: İşletmeler kayıtlı ancak KYC onayı bekliyor")
                print("• 💡 ÇÖZÜM: Admin panelinden işletmeleri onaylamak gerekiyor")
            else:
                print("• ⚠️ Karışık KYC durumu - daha detaylı inceleme gerekli")
        
        print()
        
        if failed > 0:
            print("❌ BAŞARISIZ TESTLER:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Recommendations
        print("💡 ÖNERİLER:")
        print("-" * 40)
        print("1. Admin panelinden bekleyen Aksaray işletmelerini onaylayın")
        print("2. KYC onay sürecini hızlandırın")
        print("3. İşletmelere onay durumu hakkında bilgi verin")
        print("4. City normalization çalıştığından emin olun")
        print()
        
        if success_rate >= 90:
            print("🎉 MÜKEMMEL: Sistem çalışıyor, sadece KYC onayları gerekli!")
        elif success_rate >= 75:
            print("✅ İYİ: Sistem çoğunlukla çalışıyor, küçük sorunlar var.")
        elif success_rate >= 50:
            print("⚠️ ORTA: Önemli sorunlar var, dikkat gerekli.")
        else:
            print("❌ KRİTİK: Büyük sorunlar var, acil müdahale gerekli.")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "details": self.results["test_details"],
            "test_business_id": self.test_business_id
        }

def main():
    """Main analysis execution"""
    tester = AksarayBusinessVisibilityTester()
    results = tester.run_comprehensive_analysis()
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues found

if __name__ == "__main__":
    main()