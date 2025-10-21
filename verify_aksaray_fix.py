#!/usr/bin/env python3
"""
VERIFY AKSARAY PRODUCT FIX
Test if the database updates worked and Aksaray businesses now have products
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://courier-connect-14.preview.emergentagent.com/api"

class AksarayFixVerifier:
    def __init__(self):
        self.session = requests.Session()
        
        # Aksaray businesses to test
        self.aksaray_businesses = {
            "68dfd5805b9cea03202ec133": {"name": "başer", "expected_products": 4},
            "68dff078b2a4ee4b6c94e2b0": {"name": "işletmew", "expected_products": 3},
            "68e108702fbb73108f2fddb8": {"name": "Aksaray Kebap Evi", "expected_products": 4},
            "68e108702fbb73108f2fddb9": {"name": "Aksaray Pizza Palace", "expected_products": 4},
        }
    
    def test_business_products(self, business_id, business_name, expected_count):
        """Test products for a specific business"""
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses/{business_id}/products")
            
            if response.status_code == 200:
                products = response.json()
                actual_count = len(products)
                
                success = actual_count == expected_count
                status = "✅" if success else "❌"
                
                print(f"{status} {business_name}: {actual_count}/{expected_count} products")
                
                if actual_count > 0:
                    print(f"   📋 Products:")
                    for product in products:
                        name = product.get('name', 'N/A')
                        price = product.get('price', 0)
                        category = product.get('category', 'N/A')
                        print(f"      - {name} (₺{price}) - {category}")
                else:
                    print(f"   ⚠️ No products found")
                
                print()
                return success, actual_count
            else:
                print(f"❌ {business_name}: API Error {response.status_code}")
                print(f"   Error: {response.text}")
                print()
                return False, 0
        except Exception as e:
            print(f"❌ {business_name}: Exception - {str(e)}")
            print()
            return False, 0
    
    def test_public_business_visibility(self):
        """Test if businesses are visible in public endpoints"""
        print("🌐 TESTING PUBLIC BUSINESS VISIBILITY...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/businesses")
            
            if response.status_code == 200:
                businesses = response.json()
                print(f"   📊 Total public businesses: {len(businesses)}")
                
                # Check if our Aksaray businesses are visible
                aksaray_visible = []
                for business in businesses:
                    business_id = business.get('id')
                    if business_id in self.aksaray_businesses:
                        business_name = self.aksaray_businesses[business_id]['name']
                        aksaray_visible.append(business_name)
                        print(f"   ✅ {business_name} is visible in public list")
                
                if len(aksaray_visible) == 0:
                    print(f"   ⚠️ No Aksaray businesses visible in public list")
                
                print()
                return len(aksaray_visible)
            else:
                print(f"   ❌ Public businesses API error: {response.status_code}")
                print()
                return 0
        except Exception as e:
            print(f"   ❌ Exception testing public visibility: {str(e)}")
            print()
            return 0
    
    def test_customer_restaurant_discovery(self):
        """Test customer restaurant discovery endpoints"""
        print("🔍 TESTING CUSTOMER RESTAURANT DISCOVERY...")
        
        # Test restaurants endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/restaurants")
            
            if response.status_code == 200:
                restaurants = response.json()
                print(f"   📊 Total restaurants: {len(restaurants)}")
                
                # Look for Aksaray restaurants
                aksaray_restaurants = []
                for restaurant in restaurants:
                    city = restaurant.get('city', '').lower()
                    if 'aksaray' in city:
                        aksaray_restaurants.append(restaurant.get('business_name', 'Unknown'))
                
                print(f"   📍 Aksaray restaurants found: {len(aksaray_restaurants)}")
                for restaurant_name in aksaray_restaurants:
                    print(f"      - {restaurant_name}")
                
                print()
                return len(aksaray_restaurants)
            else:
                print(f"   ❌ Restaurants API error: {response.status_code}")
                print()
                return 0
        except Exception as e:
            print(f"   ❌ Exception testing restaurants: {str(e)}")
            print()
            return 0
    
    def run_verification(self):
        """Run complete verification"""
        print("🔍 AKSARAY PRODUCT FIX VERIFICATION")
        print("=" * 50)
        
        total_success = 0
        total_tests = len(self.aksaray_businesses)
        total_products_found = 0
        
        # Test each Aksaray business
        print("📍 TESTING AKSARAY BUSINESS PRODUCTS...")
        print()
        
        for business_id, business_info in self.aksaray_businesses.items():
            business_name = business_info["name"]
            expected_count = business_info["expected_products"]
            
            success, actual_count = self.test_business_products(
                business_id, business_name, expected_count
            )
            
            if success:
                total_success += 1
            
            total_products_found += actual_count
        
        # Test public visibility
        public_visible = self.test_public_business_visibility()
        
        # Test customer discovery
        customer_restaurants = self.test_customer_restaurant_discovery()
        
        # Print summary
        print("=" * 50)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 50)
        
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ BUSINESS PRODUCT TESTS: {total_success}/{total_tests} passed ({success_rate:.1f}%)")
        print(f"📊 TOTAL PRODUCTS FOUND: {total_products_found}")
        print(f"🌐 PUBLIC VISIBILITY: {public_visible} businesses visible")
        print(f"🔍 CUSTOMER DISCOVERY: {customer_restaurants} Aksaray restaurants")
        
        print()
        
        if total_success == total_tests and total_products_found > 0:
            print("🎉 SUCCESS! Aksaray product visibility issue is RESOLVED!")
            print("   ✅ All Aksaray businesses now have products")
            print("   ✅ Products are accessible via API endpoints")
            print("   ✅ Ready for customer frontend integration")
        elif total_products_found > 0:
            print("⚠️ PARTIAL SUCCESS - Some issues remain:")
            if total_success < total_tests:
                print(f"   - {total_tests - total_success} businesses missing expected products")
            if public_visible == 0:
                print("   - Businesses not visible in public endpoints (check KYC status)")
        else:
            print("❌ ISSUE NOT RESOLVED - No products found for Aksaray businesses")
            print("   - Database updates may not have been applied correctly")
            print("   - Check MongoDB connection and product assignments")
        
        print()
        print("🔗 NEXT STEPS:")
        print("   1. Test frontend customer app to verify menu visibility")
        print("   2. Ensure businesses are KYC approved for public visibility")
        print("   3. Test complete order flow from customer perspective")
        
        print("\n" + "=" * 50)

def main():
    verifier = AksarayFixVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()