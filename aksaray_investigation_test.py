#!/usr/bin/env python3
"""
AKSARAY İŞLETME VİSİBİLİTY SORUNU İNCELEME
Kullanıcı Aksaray'da bir işletme kaydı oluşturmuş ama müşteri tarafında görünmüyor.

ARAŞTIRMA ALANLARI:
1. İşletme Kayıtları İnceleme - GET /api/businesses, GET /api/admin/businesses
2. KYC Durumu Kontrolü - kyc_status='approved' kontrolü
3. Şehir Normalizasyonu Testi - 'Aksaray' vs 'aksaray' karşılaştırması
4. Yeni Test İşletmesi Oluşturma - Aksaray'da onaylı test işletmesi
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

class AksarayBusinessVisibilityTester:
    """
    AKSARAY İŞLETME VİSİBİLİTY SORUNU İNCELEME
    Kullanıcı Aksaray'da bir işletme kaydı oluşturmuş ama müşteri tarafında görünmüyor.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.backend_url = "https://kuryecini-ai-tools.preview.emergentagent.com/api"
        self.admin_token = None
        self.customer_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        if data and isinstance(data, dict):
            print(f"    Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()
    
    def authenticate_admin(self):
        """Admin authentication for business management"""
        print("🔐 ADMIN AUTHENTICATION")
        print("=" * 50)
        
        try:
            # Try multiple admin credentials
            admin_credentials = [
                {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"},
                {"email": "admin@test.com", "password": "6851"},
                {"email": "admin@delivertr.com", "password": "6851"}
            ]
            
            for creds in admin_credentials:
                response = self.session.post(f"{self.backend_url}/auth/login", json=creds)
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("access_token")
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    
                    self.log_result(
                        "Admin Authentication",
                        True,
                        f"Admin login successful with {creds['email']}",
                        {"email": creds["email"], "role": data.get("user", {}).get("role")}
                    )
                    return True
            
            self.log_result("Admin Authentication", False, "All admin login attempts failed")
            return False
            
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def authenticate_customer(self):
        """Customer authentication for visibility testing"""
        print("👤 CUSTOMER AUTHENTICATION")
        print("=" * 50)
        
        try:
            creds = {"email": "testcustomer@example.com", "password": "test123"}
            response = self.session.post(f"{self.backend_url}/auth/login", json=creds)
            
            if response.status_code == 200:
                data = response.json()
                self.customer_token = data.get("access_token")
                
                self.log_result(
                    "Customer Authentication",
                    True,
                    f"Customer login successful",
                    {"email": creds["email"], "user_id": data.get("user", {}).get("id")}
                )
                return True
            else:
                self.log_result("Customer Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Customer Authentication", False, f"Exception: {str(e)}")
            return False
    
    def investigate_all_businesses(self):
        """1. İşletme Kayıtları İnceleme - GET /api/businesses"""
        print("🏪 İŞLETME KAYITLARI İNCELEME")
        print("=" * 50)
        
        try:
            # Test public businesses endpoint (customer view)
            response = self.session.get(f"{self.backend_url}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                aksaray_businesses = [b for b in businesses if 'aksaray' in b.get('city', '').lower() or 'aksaray' in b.get('city_normalized', '').lower()]
                
                self.log_result(
                    "GET /api/businesses - Tüm İşletmeler",
                    True,
                    f"Toplam {len(businesses)} işletme bulundu, Aksaray: {len(aksaray_businesses)}",
                    {
                        "total_businesses": len(businesses),
                        "aksaray_businesses": len(aksaray_businesses),
                        "aksaray_business_details": aksaray_businesses[:3] if aksaray_businesses else []
                    }
                )
                
                # Analyze city distribution
                cities = {}
                for business in businesses:
                    city = business.get('city', 'Unknown')
                    city_normalized = business.get('city_normalized', 'Unknown')
                    cities[city] = cities.get(city, 0) + 1
                
                self.log_result(
                    "Şehir Dağılımı Analizi",
                    True,
                    f"Farklı şehirler: {len(cities)}",
                    {"city_distribution": cities}
                )
                
            else:
                self.log_result(
                    "GET /api/businesses",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_result("İşletme Kayıtları İnceleme", False, f"Exception: {str(e)}")
    
    def investigate_admin_businesses(self):
        """Admin panelinden işletme durumları"""
        print("👨‍💼 ADMIN PANELİ İŞLETME DURUMU")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Admin Panel İşletmeler", False, "Admin authentication required")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{self.backend_url}/admin/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                businesses = [u for u in users if u.get('role') == 'business']
                aksaray_businesses = [b for b in businesses if 'aksaray' in b.get('city', '').lower()]
                
                # Analyze KYC status
                kyc_stats = {}
                for business in businesses:
                    kyc_status = business.get('kyc_status', business.get('business_status', 'unknown'))
                    kyc_stats[kyc_status] = kyc_stats.get(kyc_status, 0) + 1
                
                self.log_result(
                    "GET /api/admin/users - İşletme Durumları",
                    True,
                    f"Toplam {len(businesses)} işletme, Aksaray: {len(aksaray_businesses)}",
                    {
                        "total_businesses": len(businesses),
                        "aksaray_businesses": len(aksaray_businesses),
                        "kyc_status_distribution": kyc_stats,
                        "aksaray_business_details": aksaray_businesses
                    }
                )
                
                # Check specifically for Aksaray businesses
                if aksaray_businesses:
                    for business in aksaray_businesses:
                        kyc_status = business.get('kyc_status', business.get('business_status', 'unknown'))
                        self.log_result(
                            f"Aksaray İşletmesi - {business.get('business_name', 'Unknown')}",
                            True,
                            f"KYC Status: {kyc_status}, Email: {business.get('email')}",
                            {
                                "business_name": business.get('business_name'),
                                "email": business.get('email'),
                                "city": business.get('city'),
                                "city_normalized": business.get('city_normalized'),
                                "kyc_status": kyc_status,
                                "is_active": business.get('is_active'),
                                "created_at": business.get('created_at')
                            }
                        )
                else:
                    self.log_result(
                        "Aksaray İşletmesi Bulunamadı",
                        False,
                        "Admin panelinde Aksaray şehrinde kayıtlı işletme bulunamadı"
                    )
                    
            else:
                self.log_result(
                    "GET /api/admin/users",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_result("Admin Panel İşletme Durumu", False, f"Exception: {str(e)}")
    
    def test_city_normalization(self):
        """3. Şehir Normalizasyonu Testi"""
        print("🏙️ ŞEHİR NORMALİZASYONU TESTİ")
        print("=" * 50)
        
        try:
            # Test city normalization function
            from utils.city_normalize import normalize_city_name
            
            test_cases = [
                "Aksaray",
                "aksaray", 
                "AKSARAY",
                "Aksary",  # Common misspelling
                "aksary"
            ]
            
            for test_city in test_cases:
                try:
                    normalized = normalize_city_name(test_city)
                    self.log_result(
                        f"Şehir Normalizasyonu - '{test_city}'",
                        True,
                        f"'{test_city}' → '{normalized}'",
                        {"original": test_city, "normalized": normalized}
                    )
                except Exception as e:
                    self.log_result(
                        f"Şehir Normalizasyonu - '{test_city}'",
                        False,
                        f"Normalization failed: {str(e)}"
                    )
                    
        except ImportError:
            self.log_result(
                "Şehir Normalizasyonu Modülü",
                False,
                "utils.city_normalize modülü bulunamadı"
            )
        except Exception as e:
            self.log_result("Şehir Normalizasyonu Testi", False, f"Exception: {str(e)}")
    
    def create_test_business_aksaray(self):
        """4. Yeni Test İşletmesi Oluşturma - Aksaray'da onaylı işletme"""
        print("🆕 AKSARAY TEST İŞLETMESİ OLUŞTURMA")
        print("=" * 50)
        
        try:
            # Create test business in Aksaray
            business_data = {
                "email": f"aksaray-test-{int(time.time())}@test.com",
                "password": "test123",
                "business_name": "Aksaray Test Restoranı",
                "tax_number": "1234567890",
                "address": "Aksaray Merkez, Test Sokak No:1",
                "city": "Aksaray",
                "business_category": "gida",
                "description": "Test amaçlı oluşturulan Aksaray restoranı"
            }
            
            response = self.session.post(f"{self.backend_url}/register/business", json=business_data)
            
            if response.status_code == 200:
                data = response.json()
                business_id = data.get("user_data", {}).get("id")
                
                self.log_result(
                    "Aksaray Test İşletmesi Kaydı",
                    True,
                    f"İşletme başarıyla kaydedildi, ID: {business_id}",
                    {
                        "business_id": business_id,
                        "business_name": business_data["business_name"],
                        "city": business_data["city"],
                        "email": business_data["email"]
                    }
                )
                
                # Now approve the business if we have admin access
                if self.admin_token and business_id:
                    self.approve_test_business(business_id, business_data["email"])
                
                return business_id
                
            else:
                self.log_result(
                    "Aksaray Test İşletmesi Kaydı",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return None
                
        except Exception as e:
            self.log_result("Aksaray Test İşletmesi Oluşturma", False, f"Exception: {str(e)}")
            return None
    
    def approve_test_business(self, business_id, business_email):
        """Approve test business for visibility"""
        print("✅ TEST İŞLETMESİ ONAYLAMA")
        print("=" * 50)
        
        try:
            # First, let's try to find and update the business in the database
            # Since we don't have direct database access, we'll simulate approval
            
            # Login as the business to get its token
            business_creds = {"email": business_email, "password": "test123"}
            response = self.session.post(f"{self.backend_url}/auth/login", json=business_creds)
            
            if response.status_code == 200:
                business_data = response.json()
                business_token = business_data.get("access_token")
                
                self.log_result(
                    "Test İşletmesi Login",
                    True,
                    f"İşletme login başarılı",
                    {"business_id": business_id, "email": business_email}
                )
                
                # Create test products for the business
                self.create_test_products(business_token, business_id)
                
            else:
                self.log_result(
                    "Test İşletmesi Login",
                    False,
                    f"Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Test İşletmesi Onaylama", False, f"Exception: {str(e)}")
    
    def create_test_products(self, business_token, business_id):
        """Create test products for the business"""
        print("🍽️ TEST ÜRÜNLERİ OLUŞTURMA")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {business_token}"}
        
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
                "name": "Aksaray Pidesi",
                "description": "Özel hamur ile hazırlanan pide",
                "price": 35.0,
                "category": "Ana Yemek", 
                "preparation_time_minutes": 15,
                "is_available": True
            },
            {
                "name": "Ayran",
                "description": "Taze ayran",
                "price": 8.0,
                "category": "İçecek",
                "preparation_time_minutes": 2,
                "is_available": True
            }
        ]
        
        created_products = []
        
        for product_data in test_products:
            try:
                response = self.session.post(
                    f"{self.backend_url}/products",
                    json=product_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    product = response.json()
                    created_products.append(product)
                    
                    self.log_result(
                        f"Ürün Oluşturma - {product_data['name']}",
                        True,
                        f"Ürün başarıyla oluşturuldu, ID: {product.get('id')}",
                        {"product_name": product_data["name"], "price": product_data["price"]}
                    )
                else:
                    self.log_result(
                        f"Ürün Oluşturma - {product_data['name']}",
                        False,
                        f"Status: {response.status_code}, Response: {response.text[:100]}"
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Ürün Oluşturma - {product_data['name']}",
                    False,
                    f"Exception: {str(e)}"
                )
        
        self.log_result(
            "Test Ürünleri Toplam",
            len(created_products) > 0,
            f"{len(created_products)}/{len(test_products)} ürün başarıyla oluşturuldu"
        )
    
    def test_customer_visibility(self):
        """Test if businesses are visible to customers"""
        print("👁️ MÜŞTERİ GÖRÜNÜRLÜĞÜ TESTİ")
        print("=" * 50)
        
        try:
            # Test without authentication (public endpoint)
            response = self.session.get(f"{self.backend_url}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                aksaray_businesses = [b for b in businesses if 'aksaray' in b.get('city', '').lower()]
                
                self.log_result(
                    "Müşteri Tarafı İşletme Görünürlüğü",
                    len(aksaray_businesses) > 0,
                    f"Müşteri tarafında {len(aksaray_businesses)} Aksaray işletmesi görünüyor",
                    {
                        "total_visible_businesses": len(businesses),
                        "aksaray_businesses": len(aksaray_businesses),
                        "aksaray_business_names": [b.get('name', 'Unknown') for b in aksaray_businesses]
                    }
                )
                
                # Check KYC status of visible businesses
                for business in aksaray_businesses:
                    kyc_status = business.get('kyc_status', 'unknown')
                    self.log_result(
                        f"Görünür Aksaray İşletmesi - {business.get('name', 'Unknown')}",
                        kyc_status == 'approved',
                        f"KYC Status: {kyc_status}",
                        business
                    )
                    
            else:
                self.log_result(
                    "Müşteri Tarafı İşletme Görünürlüğü",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_result("Müşteri Görünürlüğü Testi", False, f"Exception: {str(e)}")
    
    def run_investigation(self):
        """Run complete Aksaray business visibility investigation"""
        print("🔍 AKSARAY İŞLETME VİSİBİLİTY SORUNU İNCELEME")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Investigation Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate
        admin_auth = self.authenticate_admin()
        customer_auth = self.authenticate_customer()
        
        # Step 2: Investigate all businesses
        self.investigate_all_businesses()
        
        # Step 3: Admin panel investigation
        if admin_auth:
            self.investigate_admin_businesses()
        
        # Step 4: Test city normalization
        self.test_city_normalization()
        
        # Step 5: Create test business in Aksaray
        test_business_id = self.create_test_business_aksaray()
        
        # Step 6: Test customer visibility
        self.test_customer_visibility()
        
        # Generate report
        return self.generate_investigation_report()
    
    def generate_investigation_report(self):
        """Generate investigation report"""
        print("\n" + "=" * 80)
        print("📋 AKSARAY İŞLETME VİSİBİLİTY SORUNU RAPORU")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Toplam Test: {total_tests}")
        print(f"Başarılı: {passed_tests} ✅")
        print(f"Başarısız: {failed_tests} ❌")
        print()
        
        # Key findings
        print("🔍 ANA BULGULAR:")
        
        # Find Aksaray businesses
        aksaray_findings = [r for r in self.test_results if 'aksaray' in r['test'].lower()]
        if aksaray_findings:
            for finding in aksaray_findings:
                status = "✅" if finding["success"] else "❌"
                print(f"   {status} {finding['test']}: {finding['details']}")
        
        print()
        
        # Recommendations
        print("💡 ÖNERİLER:")
        
        # Check if any Aksaray businesses were found
        has_aksaray_businesses = any(
            'aksaray_businesses' in str(r.get('data', {})) and 
            r.get('data', {}).get('aksaray_businesses', 0) > 0 
            for r in self.test_results
        )
        
        if not has_aksaray_businesses:
            print("   1. Aksaray'da kayıtlı işletme bulunamadı - yeni işletme kaydı gerekli")
            print("   2. Mevcut işletmelerin KYC onay durumunu kontrol edin")
            print("   3. Şehir normalizasyonu çalışıyor mu kontrol edin")
        else:
            print("   1. Aksaray işletmeleri bulundu - KYC onay durumlarını kontrol edin")
            print("   2. kyc_status='approved' olan işletmeler müşteri tarafında görünmelidir")
            print("   3. city_normalized alanının doğru çalıştığını doğrulayın")
        
        print("\n" + "=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "results": self.test_results
        }

def main():
    """Run Aksaray business visibility investigation"""
    investigator = AksarayBusinessVisibilityTester()
    return investigator.run_investigation()

if __name__ == "__main__":
    # Run the Aksaray investigation
    main()