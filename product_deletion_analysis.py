#!/usr/bin/env python3
"""
ÜRÜN OTOMATİK SİLME SORUNU ANALİZİ (Product Auto-Delete Issue Analysis)

SORUN: "İşletme kısmında eklenen yemekler otomatik siliniyor"

KAPSAMLI İNCELEME:
1. **Mevcut Ürün Durumu Kontrolü**: başer işletmesinin ürün durumu (daha önce 3 ürün eklemiştik)
2. **Auto-Cleanup Sistemleri**: Cron job'lar, scheduled task'ler, database cleanup routine'leri
3. **Product Creation API Testi**: Yeni ürün ekle, 5 dakika sonra kontrol et
4. **Database Transaction İnceleme**: Product collection'daki delete operations
5. **Business Authentication Test**: İşletme login'i ile ürün ekleme, permission kontrolü

Bu test, ürün silme işleminin root cause'unu bulacak.
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
import uuid
import asyncio
import subprocess
import os

# Configuration
BACKEND_URL = "https://kuryecini-ai.preview.emergentagent.com/api"
TEST_BUSINESS_EMAIL = "testbusiness@example.com"
TEST_BUSINESS_PASSWORD = "test123"

# Başer işletmesi bilgileri (test_result.md'den)
BASER_BUSINESS_INFO = {
    "email": "baser@test.com",  # Tahmin edilen email
    "name": "başer",
    "expected_products": 3  # Daha önce 3 ürün eklenmişti
}

class ProductDeletionAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.jwt_token = None
        self.business_user_id = None
        self.test_product_ids = []
        self.analysis_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "critical_findings": [],
            "test_details": []
        }
        self.start_time = datetime.now()
    
    def log_test(self, test_name, success, details="", response_data=None, is_critical=False):
        """Log test result with critical finding tracking"""
        self.analysis_results["total_tests"] += 1
        if success:
            self.analysis_results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.analysis_results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat(),
            "is_critical": is_critical
        }
        
        self.analysis_results["test_details"].append(test_result)
        
        if is_critical:
            self.analysis_results["critical_findings"].append({
                "finding": test_name,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if is_critical:
            print(f"    🚨 CRITICAL FINDING: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def authenticate_business(self):
        """Test business authentication"""
        print("🔐 TESTING BUSINESS AUTHENTICATION")
        print("=" * 50)
        
        try:
            login_data = {
                "email": TEST_BUSINESS_EMAIL,
                "password": TEST_BUSINESS_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                user_data = data.get("user", {})
                self.business_user_id = user_data.get("id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                self.log_test(
                    "Business Authentication",
                    True,
                    f"Login successful. Business ID: {self.business_user_id}, Token length: {len(self.jwt_token) if self.jwt_token else 0} chars",
                    {"business_id": self.business_user_id, "email": user_data.get("email"), "role": user_data.get("role")}
                )
                return True
            else:
                self.log_test(
                    "Business Authentication",
                    False,
                    f"Login failed. Status: {response.status_code}",
                    response.text,
                    is_critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Business Authentication",
                False,
                f"Exception during login: {str(e)}",
                is_critical=True
            )
            return False
    
    def check_existing_products(self):
        """Check current product status for all businesses"""
        print("📦 CHECKING EXISTING PRODUCTS STATUS")
        print("=" * 50)
        
        try:
            # Get all products for current business
            response = self.session.get(f"{BACKEND_URL}/products/my")
            
            if response.status_code == 200:
                products = response.json()
                self.log_test(
                    "Current Business Products",
                    True,
                    f"Found {len(products)} products for authenticated business",
                    {"product_count": len(products), "products": products[:3] if products else []}
                )
                
                # Check if products have timestamps
                for product in products:
                    created_at = product.get("created_at")
                    if created_at:
                        self.log_test(
                            f"Product Timestamp Analysis - {product.get('name', 'Unknown')}",
                            True,
                            f"Product created at: {created_at}",
                            {"product_id": product.get("id"), "created_at": created_at}
                        )
                
                return products
            else:
                self.log_test(
                    "Current Business Products",
                    False,
                    f"Failed to retrieve products. Status: {response.status_code}",
                    response.text,
                    is_critical=True
                )
                return []
                
        except Exception as e:
            self.log_test(
                "Current Business Products",
                False,
                f"Exception during product retrieval: {str(e)}",
                is_critical=True
            )
            return []
    
    def check_all_businesses_products(self):
        """Check products for all businesses to find başer business"""
        print("🏪 CHECKING ALL BUSINESSES FOR BAŞER")
        print("=" * 50)
        
        try:
            # Get all businesses (public endpoint)
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                self.log_test(
                    "All Businesses Check",
                    True,
                    f"Found {len(businesses)} businesses total",
                    {"business_count": len(businesses)}
                )
                
                # Look for başer business
                baser_business = None
                for business in businesses:
                    business_name = business.get("name", "").lower()
                    if "başer" in business_name or "baser" in business_name:
                        baser_business = business
                        break
                
                if baser_business:
                    business_id = baser_business.get("id")
                    self.log_test(
                        "Başer Business Found",
                        True,
                        f"Found başer business with ID: {business_id}",
                        baser_business,
                        is_critical=True
                    )
                    
                    # Check başer's products
                    products_response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
                    if products_response.status_code == 200:
                        baser_products = products_response.json()
                        self.log_test(
                            "Başer Business Products",
                            True,
                            f"Başer business has {len(baser_products)} products (Expected: {BASER_BUSINESS_INFO['expected_products']})",
                            {"expected": BASER_BUSINESS_INFO['expected_products'], "actual": len(baser_products), "products": baser_products},
                            is_critical=True
                        )
                        
                        if len(baser_products) < BASER_BUSINESS_INFO['expected_products']:
                            self.log_test(
                                "Product Deletion Detected",
                                False,
                                f"PRODUCT DELETION CONFIRMED: Expected {BASER_BUSINESS_INFO['expected_products']} products, found {len(baser_products)}",
                                {"missing_products": BASER_BUSINESS_INFO['expected_products'] - len(baser_products)},
                                is_critical=True
                            )
                    else:
                        self.log_test(
                            "Başer Business Products",
                            False,
                            f"Failed to get başer products. Status: {products_response.status_code}",
                            products_response.text,
                            is_critical=True
                        )
                else:
                    self.log_test(
                        "Başer Business Search",
                        False,
                        "Başer business not found in public businesses list",
                        {"searched_businesses": [b.get("name", "Unknown") for b in businesses[:10]]},
                        is_critical=True
                    )
                
                return businesses
            else:
                self.log_test(
                    "All Businesses Check",
                    False,
                    f"Failed to retrieve businesses. Status: {response.status_code}",
                    response.text
                )
                return []
                
        except Exception as e:
            self.log_test(
                "All Businesses Check",
                False,
                f"Exception during businesses check: {str(e)}"
            )
            return []
    
    def create_test_product(self):
        """Create a test product to monitor for auto-deletion"""
        print("➕ CREATING TEST PRODUCT FOR MONITORING")
        print("=" * 50)
        
        test_product = {
            "name": f"Test Product Auto-Delete Monitor {datetime.now().strftime('%H:%M:%S')}",
            "description": "Bu ürün otomatik silme testinde kullanılıyor. Silinmemeli!",
            "price": 25.50,
            "category": "Test",
            "preparation_time_minutes": 15,
            "is_available": True
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/products", json=test_product)
            
            if response.status_code == 200:
                created_product = response.json()
                product_id = created_product.get("id")
                
                if product_id:
                    self.test_product_ids.append(product_id)
                
                self.log_test(
                    "Test Product Creation",
                    True,
                    f"Created test product '{test_product['name']}' with ID: {product_id}",
                    created_product,
                    is_critical=True
                )
                
                return created_product
            else:
                self.log_test(
                    "Test Product Creation",
                    False,
                    f"Failed to create test product. Status: {response.status_code}",
                    response.text,
                    is_critical=True
                )
                return None
                
        except Exception as e:
            self.log_test(
                "Test Product Creation",
                False,
                f"Exception during product creation: {str(e)}",
                is_critical=True
            )
            return None
    
    def monitor_product_persistence(self, product_id, monitoring_duration=300):
        """Monitor product for auto-deletion over specified duration (default 5 minutes)"""
        print(f"⏱️ MONITORING PRODUCT PERSISTENCE FOR {monitoring_duration} SECONDS")
        print("=" * 50)
        
        start_time = time.time()
        check_interval = 30  # Check every 30 seconds
        checks_performed = 0
        
        while time.time() - start_time < monitoring_duration:
            try:
                # Check if product still exists
                response = self.session.get(f"{BACKEND_URL}/products/my")
                
                if response.status_code == 200:
                    products = response.json()
                    product_exists = any(p.get("id") == product_id for p in products)
                    
                    checks_performed += 1
                    elapsed_time = time.time() - start_time
                    
                    if product_exists:
                        self.log_test(
                            f"Product Persistence Check #{checks_performed}",
                            True,
                            f"Product still exists after {elapsed_time:.0f} seconds",
                            {"elapsed_time": elapsed_time, "product_id": product_id}
                        )
                    else:
                        self.log_test(
                            "Product Auto-Deletion Detected",
                            False,
                            f"PRODUCT DELETED AUTOMATICALLY after {elapsed_time:.0f} seconds!",
                            {"deletion_time": elapsed_time, "product_id": product_id},
                            is_critical=True
                        )
                        return False  # Product was deleted
                else:
                    self.log_test(
                        f"Product Persistence Check #{checks_performed}",
                        False,
                        f"Failed to check products. Status: {response.status_code}",
                        response.text
                    )
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                self.log_test(
                    f"Product Persistence Check #{checks_performed}",
                    False,
                    f"Exception during monitoring: {str(e)}"
                )
                time.sleep(check_interval)
        
        # Final check
        try:
            response = self.session.get(f"{BACKEND_URL}/products/my")
            if response.status_code == 200:
                products = response.json()
                product_exists = any(p.get("id") == product_id for p in products)
                
                self.log_test(
                    "Final Product Persistence Check",
                    product_exists,
                    f"Product {'still exists' if product_exists else 'was deleted'} after {monitoring_duration} seconds",
                    {"monitoring_duration": monitoring_duration, "product_exists": product_exists},
                    is_critical=not product_exists
                )
                
                return product_exists
        except Exception as e:
            self.log_test(
                "Final Product Persistence Check",
                False,
                f"Exception during final check: {str(e)}"
            )
            return False
    
    def check_backend_logs(self):
        """Check backend logs for deletion operations"""
        print("📋 CHECKING BACKEND LOGS FOR DELETION OPERATIONS")
        print("=" * 50)
        
        try:
            # Try to get backend logs (this might not work in production environment)
            log_commands = [
                "tail -n 100 /var/log/supervisor/backend.*.log",
                "grep -i 'delete' /var/log/supervisor/backend.*.log | tail -20",
                "grep -i 'product' /var/log/supervisor/backend.*.log | tail -20"
            ]
            
            for cmd in log_commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        self.log_test(
                            f"Backend Log Check - {cmd.split()[0]}",
                            True,
                            f"Found log entries: {len(result.stdout.splitlines())} lines",
                            {"log_sample": result.stdout.splitlines()[-5:] if result.stdout.splitlines() else []}
                        )
                    else:
                        self.log_test(
                            f"Backend Log Check - {cmd.split()[0]}",
                            False,
                            f"No relevant log entries found or command failed",
                            {"stderr": result.stderr[:200] if result.stderr else ""}
                        )
                except subprocess.TimeoutExpired:
                    self.log_test(
                        f"Backend Log Check - {cmd.split()[0]}",
                        False,
                        "Log check timed out"
                    )
                except Exception as e:
                    self.log_test(
                        f"Backend Log Check - {cmd.split()[0]}",
                        False,
                        f"Exception: {str(e)}"
                    )
                    
        except Exception as e:
            self.log_test(
                "Backend Log Analysis",
                False,
                f"Exception during log analysis: {str(e)}"
            )
    
    def check_database_operations(self):
        """Check for database cleanup operations or scheduled tasks"""
        print("🗄️ CHECKING DATABASE OPERATIONS")
        print("=" * 50)
        
        # This is a placeholder for database operation checks
        # In a real scenario, we would check MongoDB logs, scheduled tasks, etc.
        
        self.log_test(
            "Database Cleanup Check",
            True,
            "No direct database access available in testing environment. Would need to check MongoDB logs for delete operations.",
            {"recommendation": "Check MongoDB logs for product deletion operations, look for scheduled cleanup tasks"}
        )
    
    def test_concurrent_access(self):
        """Test if concurrent access causes product deletion"""
        print("🔄 TESTING CONCURRENT ACCESS SCENARIOS")
        print("=" * 50)
        
        # Create multiple products quickly to test for race conditions
        concurrent_products = []
        
        for i in range(3):
            test_product = {
                "name": f"Concurrent Test Product {i+1}",
                "description": f"Testing concurrent access scenario {i+1}",
                "price": 15.0 + i,
                "category": "Concurrent Test",
                "preparation_time_minutes": 10,
                "is_available": True
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/products", json=test_product)
                if response.status_code == 200:
                    product = response.json()
                    concurrent_products.append(product)
                    self.test_product_ids.append(product.get("id"))
                    
                    self.log_test(
                        f"Concurrent Product Creation {i+1}",
                        True,
                        f"Created concurrent test product {i+1}",
                        {"product_id": product.get("id")}
                    )
                else:
                    self.log_test(
                        f"Concurrent Product Creation {i+1}",
                        False,
                        f"Failed to create concurrent product {i+1}. Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_test(
                    f"Concurrent Product Creation {i+1}",
                    False,
                    f"Exception: {str(e)}"
                )
        
        # Wait a bit and check if all products still exist
        time.sleep(10)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/products/my")
            if response.status_code == 200:
                current_products = response.json()
                concurrent_product_ids = [p.get("id") for p in concurrent_products]
                still_existing = [p for p in current_products if p.get("id") in concurrent_product_ids]
                
                self.log_test(
                    "Concurrent Access Product Persistence",
                    len(still_existing) == len(concurrent_products),
                    f"Created {len(concurrent_products)} concurrent products, {len(still_existing)} still exist",
                    {"created": len(concurrent_products), "existing": len(still_existing)},
                    is_critical=(len(still_existing) < len(concurrent_products))
                )
        except Exception as e:
            self.log_test(
                "Concurrent Access Product Persistence",
                False,
                f"Exception during concurrent access check: {str(e)}"
            )
    
    def cleanup_test_products(self):
        """Clean up test products created during analysis"""
        print("🧹 CLEANING UP TEST PRODUCTS")
        print("=" * 50)
        
        for product_id in self.test_product_ids:
            try:
                response = self.session.delete(f"{BACKEND_URL}/products/{product_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up test product: {product_id}")
                else:
                    print(f"⚠️ Could not clean up test product {product_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error cleaning up test product {product_id}: {str(e)}")
    
    def run_comprehensive_analysis(self):
        """Run comprehensive product deletion analysis"""
        print("🔍 STARTING COMPREHENSIVE PRODUCT AUTO-DELETE ANALYSIS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Analysis Start Time: {self.start_time.isoformat()}")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate business
        if not self.authenticate_business():
            print("❌ CRITICAL: Business authentication failed. Cannot proceed with analysis.")
            return self.generate_final_report()
        
        # Step 2: Check existing products
        existing_products = self.check_existing_products()
        
        # Step 3: Check all businesses for başer
        all_businesses = self.check_all_businesses_products()
        
        # Step 4: Create test product for monitoring
        test_product = self.create_test_product()
        
        if test_product and test_product.get("id"):
            # Step 5: Monitor product for auto-deletion (5 minutes)
            print(f"⏱️ Starting 5-minute monitoring period for product {test_product.get('id')}")
            product_survived = self.monitor_product_persistence(test_product.get("id"), 300)
            
            if not product_survived:
                print("🚨 CRITICAL: Product was automatically deleted during monitoring!")
        
        # Step 6: Test concurrent access scenarios
        self.test_concurrent_access()
        
        # Step 7: Check backend logs
        self.check_backend_logs()
        
        # Step 8: Check database operations
        self.check_database_operations()
        
        # Step 9: Clean up test products
        self.cleanup_test_products()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 80)
        print("📊 PRODUCT AUTO-DELETE ANALYSIS RESULTS")
        print("=" * 80)
        
        total = self.analysis_results["total_tests"]
        passed = self.analysis_results["passed_tests"]
        failed = self.analysis_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical findings
        critical_findings = self.analysis_results["critical_findings"]
        if critical_findings:
            print("🚨 CRITICAL FINDINGS:")
            for finding in critical_findings:
                print(f"  • {finding['finding']}: {finding['details']}")
            print()
        
        # Failed tests
        if failed > 0:
            print("❌ FAILED TESTS:")
            for test in self.analysis_results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Analysis conclusion
        if critical_findings:
            print("🔍 ANALYSIS CONCLUSION:")
            if any("PRODUCT DELETED AUTOMATICALLY" in f["details"] for f in critical_findings):
                print("❌ CONFIRMED: Products are being automatically deleted!")
                print("   Root cause investigation needed for auto-cleanup mechanisms.")
            elif any("Expected" in f["details"] and "found" in f["details"] for f in critical_findings):
                print("⚠️ SUSPECTED: Product count mismatch detected.")
                print("   Products may have been deleted previously.")
            else:
                print("✅ NO IMMEDIATE AUTO-DELETION: Products appear stable during test period.")
        else:
            print("✅ NO CRITICAL ISSUES: No automatic product deletion detected during analysis.")
        
        print("\n" + "=" * 80)
        
        return {
            "success_rate": success_rate,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "critical_findings": critical_findings,
            "details": self.analysis_results["test_details"]
        }

def main():
    """Main analysis execution"""
    analyzer = ProductDeletionAnalyzer()
    results = analyzer.run_comprehensive_analysis()
    
    # Exit with appropriate code
    if results["critical_findings"]:
        sys.exit(1)  # Critical issues found
    elif results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # General failure

if __name__ == "__main__":
    main()