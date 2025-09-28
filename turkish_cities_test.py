#!/usr/bin/env python3
"""
DeliverTR Backend API Testing Suite - 81 Turkish Cities Integration
Tests all registration endpoints with the new 81 Turkish cities implementation.

SPECIFIC TESTS:
1. Test business registration with various Turkish cities from the 81 provinces
2. Test courier registration with different cities  
3. Test customer registration with city validation
4. Test specific cities with Turkish characters: İstanbul, Şanlıurfa, Çanakkale, Kırıkkale, Kütahya, etc.
5. Test major cities: İstanbul, Ankara, İzmir, Bursa, Antalya, Gaziantep
6. Test smaller provinces: Ardahan, Bayburt, Tunceli, Kilis, Yalova
7. Verify city field accepts all 81 provinces properly
"""

import requests
import sys
import json
from datetime import datetime
import time
import uuid

class TurkishCitiesAPITester:
    def __init__(self, base_url="https://kuryecini-turk.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # 81 Turkish Cities (Official list)
        self.turkish_cities = [
            "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin",
            "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa",
            "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan",
            "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta",
            "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir",
            "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla",
            "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt",
            "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak",
            "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman",
            "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
        ]
        
        # Special focus cities from the request
        self.major_cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Gaziantep"]
        self.smaller_provinces = ["Ardahan", "Bayburt", "Tunceli", "Kilis", "Yalova"]
        self.turkish_character_cities = ["İstanbul", "Şanlıurfa", "Çanakkale", "Kırıkkale", "Kütahya"]
        
        # Sample test registrations from request
        self.sample_registrations = [
            {"type": "business", "email": "istanbul-biz@test.com", "city": "İstanbul"},
            {"type": "courier", "email": "ankara-courier@test.com", "city": "Ankara"},
            {"type": "customer", "email": "izmir-customer@test.com", "city": "İzmir"},
            {"type": "business", "email": "gaziantep-food@test.com", "city": "Gaziantep"},
            {"type": "courier", "email": "trabzon-courier@test.com", "city": "Trabzon"}
        ]

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    self.log_test(name, True)
                    return True, response_data
                except:
                    response_text = response.text
                    print(f"   Response: {response_text}")
                    self.log_test(name, True)
                    return True, response_text
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    error_msg = f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_test(name, False, error_msg)
            return False, {}

    def test_business_registration_with_turkish_cities(self):
        """Test business registration with all 81 Turkish cities"""
        print("\n🏢 TESTING BUSINESS REGISTRATION WITH 81 TURKISH CITIES")
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(self.turkish_cities):
            print(f"\n   🧪 Testing city {i+1}/81: {city}")
            
            # Create unique email for each test
            test_email = f"business-{city.lower().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')}-{uuid.uuid4().hex[:6]}@test.com"
            
            business_data = {
                "email": test_email,
                "password": "test123",
                "business_name": f"{city} Test İşletmesi",
                "tax_number": f"{1000000000 + i}",
                "address": f"Test Mahallesi, {city}",
                "city": city,
                "business_category": "gida",
                "description": f"{city} şehrinde test işletmesi"
            }
            
            success, response = self.run_test(
                f"Business Registration - {city}",
                "POST",
                "register/business",
                200,
                data=business_data
            )
            
            if success:
                passed_cities.append(city)
                # Verify city is stored correctly
                if response and isinstance(response, dict):
                    user_data = response.get('user_data', {})
                    stored_city = user_data.get('city')
                    if stored_city == city:
                        print(f"   ✅ City '{city}' accepted and stored correctly")
                    else:
                        print(f"   ⚠️  City storage issue: expected '{city}', got '{stored_city}'")
            else:
                failed_cities.append(city)
                print(f"   ❌ City '{city}' rejected")
        
        print(f"\n   📊 Business Registration Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/81 cities")
        print(f"   ❌ Failed: {len(failed_cities)}/81 cities")
        
        if failed_cities:
            print(f"   Failed cities: {', '.join(failed_cities)}")
        
        success_rate = (len(passed_cities) / len(self.turkish_cities)) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Log overall result
        if len(passed_cities) == len(self.turkish_cities):
            self.log_test("Business Registration - All 81 Turkish Cities", True, f"All {len(self.turkish_cities)} cities accepted")
            return True
        else:
            self.log_test("Business Registration - All 81 Turkish Cities", False, f"Only {len(passed_cities)}/{len(self.turkish_cities)} cities accepted")
            return False

    def test_courier_registration_with_turkish_cities(self):
        """Test courier registration with various Turkish cities"""
        print("\n🚴 TESTING COURIER REGISTRATION WITH TURKISH CITIES")
        
        # Test with a representative sample of cities including major, smaller, and special character cities
        test_cities = list(set(self.major_cities + self.smaller_provinces + self.turkish_character_cities + 
                             ["Adana", "Samsun", "Konya", "Eskişehir", "Diyarbakır", "Mersin", "Hatay", "Van"]))
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(test_cities):
            print(f"\n   🧪 Testing courier city {i+1}/{len(test_cities)}: {city}")
            
            # Create unique email for each test
            test_email = f"courier-{city.lower().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')}-{uuid.uuid4().hex[:6]}@test.com"
            
            courier_data = {
                "email": test_email,
                "password": "test123",
                "first_name": f"{city}",
                "last_name": "Kurye",
                "iban": f"TR33000610051978645784{1300 + i:04d}",
                "vehicle_type": "motor",
                "vehicle_model": "Honda PCX 150",
                "license_class": "A2",
                "license_number": f"34{city[:3].upper()}{100 + i}",
                "city": city
            }
            
            success, response = self.run_test(
                f"Courier Registration - {city}",
                "POST",
                "register/courier",
                200,
                data=courier_data
            )
            
            if success:
                passed_cities.append(city)
                # Verify city is stored correctly
                if response and isinstance(response, dict):
                    user_data = response.get('user_data', {})
                    stored_city = user_data.get('city')
                    if stored_city == city:
                        print(f"   ✅ Courier city '{city}' accepted and stored correctly")
                    else:
                        print(f"   ⚠️  Courier city storage issue: expected '{city}', got '{stored_city}'")
            else:
                failed_cities.append(city)
                print(f"   ❌ Courier city '{city}' rejected")
        
        print(f"\n   📊 Courier Registration Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/{len(test_cities)} cities")
        print(f"   ❌ Failed: {len(failed_cities)}/{len(test_cities)} cities")
        
        if failed_cities:
            print(f"   Failed cities: {', '.join(failed_cities)}")
        
        success_rate = (len(passed_cities) / len(test_cities)) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Log overall result
        if len(passed_cities) == len(test_cities):
            self.log_test("Courier Registration - Turkish Cities", True, f"All {len(test_cities)} test cities accepted")
            return True
        else:
            self.log_test("Courier Registration - Turkish Cities", False, f"Only {len(passed_cities)}/{len(test_cities)} cities accepted")
            return False

    def test_customer_registration_with_turkish_cities(self):
        """Test customer registration with various Turkish cities"""
        print("\n👤 TESTING CUSTOMER REGISTRATION WITH TURKISH CITIES")
        
        # Test with a representative sample including all special categories
        test_cities = list(set(self.major_cities + self.smaller_provinces + self.turkish_character_cities + 
                             ["Adana", "Samsun", "Konya", "Malatya", "Elazığ", "Rize", "Sinop", "Muş"]))
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(test_cities):
            print(f"\n   🧪 Testing customer city {i+1}/{len(test_cities)}: {city}")
            
            # Create unique email for each test
            test_email = f"customer-{city.lower().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')}-{uuid.uuid4().hex[:6]}@test.com"
            
            customer_data = {
                "email": test_email,
                "password": "test123",
                "first_name": f"{city}",
                "last_name": "Müşteri",
                "city": city
            }
            
            success, response = self.run_test(
                f"Customer Registration - {city}",
                "POST",
                "register/customer",
                200,
                data=customer_data
            )
            
            if success:
                passed_cities.append(city)
                # Verify city is stored correctly
                if response and isinstance(response, dict):
                    user_data = response.get('user_data', {})
                    stored_city = user_data.get('city')
                    if stored_city == city:
                        print(f"   ✅ Customer city '{city}' accepted and stored correctly")
                    else:
                        print(f"   ⚠️  Customer city storage issue: expected '{city}', got '{stored_city}'")
            else:
                failed_cities.append(city)
                print(f"   ❌ Customer city '{city}' rejected")
        
        print(f"\n   📊 Customer Registration Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/{len(test_cities)} cities")
        print(f"   ❌ Failed: {len(failed_cities)}/{len(test_cities)} cities")
        
        if failed_cities:
            print(f"   Failed cities: {', '.join(failed_cities)}")
        
        success_rate = (len(passed_cities) / len(test_cities)) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Log overall result
        if len(passed_cities) == len(test_cities):
            self.log_test("Customer Registration - Turkish Cities", True, f"All {len(test_cities)} test cities accepted")
            return True
        else:
            self.log_test("Customer Registration - Turkish Cities", False, f"Only {len(passed_cities)}/{len(test_cities)} cities accepted")
            return False

    def test_sample_registrations_from_request(self):
        """Test the specific sample registrations mentioned in the request"""
        print("\n📋 TESTING SAMPLE REGISTRATIONS FROM REQUEST")
        
        all_success = True
        
        for i, sample in enumerate(self.sample_registrations):
            print(f"\n   🧪 Testing sample {i+1}/{len(self.sample_registrations)}: {sample['type']} - {sample['email']} - {sample['city']}")
            
            if sample['type'] == 'business':
                data = {
                    "email": sample['email'],
                    "password": "test123",
                    "business_name": f"{sample['city']} Test Business",
                    "tax_number": f"{2000000000 + i}",
                    "address": f"Test Address, {sample['city']}",
                    "city": sample['city'],
                    "business_category": "gida",
                    "description": f"Sample business in {sample['city']}"
                }
                endpoint = "register/business"
            
            elif sample['type'] == 'courier':
                data = {
                    "email": sample['email'],
                    "password": "test123",
                    "first_name": f"{sample['city']}",
                    "last_name": "Courier",
                    "iban": f"TR33000610051978645784{2000 + i:04d}",
                    "vehicle_type": "motor",
                    "vehicle_model": "Honda PCX 150",
                    "license_class": "A2",
                    "license_number": f"34SAM{100 + i}",
                    "city": sample['city']
                }
                endpoint = "register/courier"
            
            elif sample['type'] == 'customer':
                data = {
                    "email": sample['email'],
                    "password": "test123",
                    "first_name": f"{sample['city']}",
                    "last_name": "Customer",
                    "city": sample['city']
                }
                endpoint = "register/customer"
            
            success, response = self.run_test(
                f"Sample Registration - {sample['type'].title()} {sample['city']}",
                "POST",
                endpoint,
                200,
                data=data
            )
            
            if success:
                # Verify city is stored correctly
                if response and isinstance(response, dict):
                    user_data = response.get('user_data', {})
                    stored_city = user_data.get('city')
                    if stored_city == sample['city']:
                        print(f"   ✅ Sample {sample['type']} registration successful with city '{sample['city']}'")
                    else:
                        print(f"   ⚠️  Sample {sample['type']} city storage issue: expected '{sample['city']}', got '{stored_city}'")
                        all_success = False
                else:
                    print(f"   ⚠️  Sample {sample['type']} registration successful but no response data")
                    all_success = False
            else:
                print(f"   ❌ Sample {sample['type']} registration failed for city '{sample['city']}'")
                all_success = False
        
        if all_success:
            self.log_test("Sample Registrations from Request", True, "All sample registrations successful")
        else:
            self.log_test("Sample Registrations from Request", False, "Some sample registrations failed")
        
        return all_success

    def test_turkish_character_cities_specifically(self):
        """Test cities with Turkish characters specifically"""
        print("\n🔤 TESTING CITIES WITH TURKISH CHARACTERS")
        
        # Extended list of cities with Turkish characters
        turkish_char_cities = [
            "İstanbul", "İzmir", "Şanlıurfa", "Çanakkale", "Kırıkkale", "Kütahya",
            "Afyonkarahisar", "Ağrı", "Çankırı", "Çorum", "Diyarbakır", "Elazığ",
            "Erzincan", "Eskişehir", "Gümüşhane", "Kırklareli", "Kırşehir", "Kahramanmaraş",
            "Muğla", "Muş", "Nevşehir", "Niğde", "Şırnak", "Tekirdağ", "Şanlıurfa",
            "Uşak", "Iğdır"
        ]
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(turkish_char_cities):
            print(f"\n   🧪 Testing Turkish character city {i+1}/{len(turkish_char_cities)}: {city}")
            
            # Test with business registration
            test_email = f"turkchar-{i}-{uuid.uuid4().hex[:6]}@test.com"
            
            business_data = {
                "email": test_email,
                "password": "test123",
                "business_name": f"{city} Türk Karakter Testi",
                "tax_number": f"{3000000000 + i}",
                "address": f"Türk Karakter Test Adresi, {city}",
                "city": city,
                "business_category": "gida",
                "description": f"{city} şehrinde Türkçe karakter testi"
            }
            
            success, response = self.run_test(
                f"Turkish Character City - {city}",
                "POST",
                "register/business",
                200,
                data=business_data
            )
            
            if success:
                passed_cities.append(city)
                # Verify Turkish characters are preserved
                if response and isinstance(response, dict):
                    user_data = response.get('user_data', {})
                    stored_city = user_data.get('city')
                    if stored_city == city:
                        print(f"   ✅ Turkish characters preserved: '{city}' → '{stored_city}'")
                    else:
                        print(f"   ⚠️  Turkish character issue: expected '{city}', got '{stored_city}'")
            else:
                failed_cities.append(city)
                print(f"   ❌ Turkish character city '{city}' rejected")
        
        print(f"\n   📊 Turkish Character Cities Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/{len(turkish_char_cities)} cities")
        print(f"   ❌ Failed: {len(failed_cities)}/{len(turkish_char_cities)} cities")
        
        if failed_cities:
            print(f"   Failed cities: {', '.join(failed_cities)}")
        
        success_rate = (len(passed_cities) / len(turkish_char_cities)) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Log overall result
        if len(passed_cities) == len(turkish_char_cities):
            self.log_test("Turkish Character Cities", True, f"All {len(turkish_char_cities)} Turkish character cities accepted")
            return True
        else:
            self.log_test("Turkish Character Cities", False, f"Only {len(passed_cities)}/{len(turkish_char_cities)} Turkish character cities accepted")
            return False

    def test_major_cities_specifically(self):
        """Test major cities specifically"""
        print("\n🏙️ TESTING MAJOR CITIES")
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(self.major_cities):
            print(f"\n   🧪 Testing major city {i+1}/{len(self.major_cities)}: {city}")
            
            # Test with all three registration types
            registration_types = [
                ("business", {
                    "email": f"major-business-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "business_name": f"{city} Major City Business",
                    "tax_number": f"{4000000000 + i}",
                    "address": f"Major City Address, {city}",
                    "city": city,
                    "business_category": "gida",
                    "description": f"Major city business in {city}"
                }),
                ("courier", {
                    "email": f"major-courier-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "first_name": f"{city}",
                    "last_name": "Major Courier",
                    "iban": f"TR33000610051978645784{3000 + i:04d}",
                    "vehicle_type": "motor",
                    "vehicle_model": "Honda PCX 150",
                    "license_class": "A2",
                    "license_number": f"34MAJ{100 + i}",
                    "city": city
                }),
                ("customer", {
                    "email": f"major-customer-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "first_name": f"{city}",
                    "last_name": "Major Customer",
                    "city": city
                })
            ]
            
            city_success = True
            for reg_type, data in registration_types:
                success, response = self.run_test(
                    f"Major City {city} - {reg_type.title()} Registration",
                    "POST",
                    f"register/{reg_type}",
                    200,
                    data=data
                )
                
                if not success:
                    city_success = False
                    print(f"   ❌ {reg_type.title()} registration failed for major city '{city}'")
                else:
                    # Verify city storage
                    if response and isinstance(response, dict):
                        user_data = response.get('user_data', {})
                        stored_city = user_data.get('city')
                        if stored_city == city:
                            print(f"   ✅ {reg_type.title()} registration successful for major city '{city}'")
                        else:
                            print(f"   ⚠️  {reg_type.title()} city storage issue: expected '{city}', got '{stored_city}'")
                            city_success = False
            
            if city_success:
                passed_cities.append(city)
            else:
                failed_cities.append(city)
        
        print(f"\n   📊 Major Cities Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/{len(self.major_cities)} cities")
        print(f"   ❌ Failed: {len(failed_cities)}/{len(self.major_cities)} cities")
        
        if failed_cities:
            print(f"   Failed cities: {', '.join(failed_cities)}")
        
        # Log overall result
        if len(passed_cities) == len(self.major_cities):
            self.log_test("Major Cities Registration", True, f"All {len(self.major_cities)} major cities accepted")
            return True
        else:
            self.log_test("Major Cities Registration", False, f"Only {len(passed_cities)}/{len(self.major_cities)} major cities accepted")
            return False

    def test_smaller_provinces_specifically(self):
        """Test smaller provinces specifically"""
        print("\n🏘️ TESTING SMALLER PROVINCES")
        
        passed_cities = []
        failed_cities = []
        
        for i, city in enumerate(self.smaller_provinces):
            print(f"\n   🧪 Testing smaller province {i+1}/{len(self.smaller_provinces)}: {city}")
            
            # Test with all three registration types
            registration_types = [
                ("business", {
                    "email": f"small-business-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "business_name": f"{city} Small Province Business",
                    "tax_number": f"{5000000000 + i}",
                    "address": f"Small Province Address, {city}",
                    "city": city,
                    "business_category": "gida",
                    "description": f"Small province business in {city}"
                }),
                ("courier", {
                    "email": f"small-courier-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "first_name": f"{city}",
                    "last_name": "Small Courier",
                    "iban": f"TR33000610051978645784{4000 + i:04d}",
                    "vehicle_type": "bisiklet",
                    "vehicle_model": "Mountain Bike",
                    "license_class": "B",
                    "license_number": f"34SML{100 + i}",
                    "city": city
                }),
                ("customer", {
                    "email": f"small-customer-{city.lower()}-{uuid.uuid4().hex[:6]}@test.com",
                    "password": "test123",
                    "first_name": f"{city}",
                    "last_name": "Small Customer",
                    "city": city
                })
            ]
            
            city_success = True
            for reg_type, data in registration_types:
                success, response = self.run_test(
                    f"Small Province {city} - {reg_type.title()} Registration",
                    "POST",
                    f"register/{reg_type}",
                    200,
                    data=data
                )
                
                if not success:
                    city_success = False
                    print(f"   ❌ {reg_type.title()} registration failed for small province '{city}'")
                else:
                    # Verify city storage
                    if response and isinstance(response, dict):
                        user_data = response.get('user_data', {})
                        stored_city = user_data.get('city')
                        if stored_city == city:
                            print(f"   ✅ {reg_type.title()} registration successful for small province '{city}'")
                        else:
                            print(f"   ⚠️  {reg_type.title()} city storage issue: expected '{city}', got '{stored_city}'")
                            city_success = False
            
            if city_success:
                passed_cities.append(city)
            else:
                failed_cities.append(city)
        
        print(f"\n   📊 Smaller Provinces Results:")
        print(f"   ✅ Passed: {len(passed_cities)}/{len(self.smaller_provinces)} provinces")
        print(f"   ❌ Failed: {len(failed_cities)}/{len(self.smaller_provinces)} provinces")
        
        if failed_cities:
            print(f"   Failed provinces: {', '.join(failed_cities)}")
        
        # Log overall result
        if len(passed_cities) == len(self.smaller_provinces):
            self.log_test("Smaller Provinces Registration", True, f"All {len(self.smaller_provinces)} smaller provinces accepted")
            return True
        else:
            self.log_test("Smaller Provinces Registration", False, f"Only {len(passed_cities)}/{len(self.smaller_provinces)} smaller provinces accepted")
            return False

    def run_all_tests(self):
        """Run all Turkish cities integration tests"""
        print("🇹🇷 STARTING 81 TURKISH CITIES INTEGRATION TESTS")
        print("=" * 80)
        
        test_methods = [
            self.test_sample_registrations_from_request,
            self.test_turkish_character_cities_specifically,
            self.test_major_cities_specifically,
            self.test_smaller_provinces_specifically,
            self.test_business_registration_with_turkish_cities,
            self.test_courier_registration_with_turkish_cities,
            self.test_customer_registration_with_turkish_cities
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(1)  # Brief pause between test suites
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with exception: {str(e)}")
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("🇹🇷 TURKISH CITIES INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = TurkishCitiesAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)