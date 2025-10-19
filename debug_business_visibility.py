#!/usr/bin/env python3
"""
DEBUG BUSINESS VISIBILITY ISSUE
Detailed investigation of the business visibility pipeline
"""

import requests
import json

BACKEND_URL = "https://food-dash-87.preview.emergentagent.com/api"

# Get admin token
admin_creds = {"email": "admin@kuryecini.com", "password": "KuryeciniAdmin2024!"}
response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_creds)
admin_token = response.json()["access_token"]

# Get customer token  
customer_creds = {"email": "testcustomer@example.com", "password": "test123"}
response = requests.post(f"{BACKEND_URL}/auth/login", json=customer_creds)
customer_token = response.json()["access_token"]

print("🔍 DEBUGGING BUSINESS VISIBILITY PIPELINE")
print("=" * 60)

# 1. Check admin businesses
print("1. ADMIN VIEW - All Businesses:")
headers = {"Authorization": f"Bearer {admin_token}"}
response = requests.get(f"{BACKEND_URL}/admin/businesses", headers=headers)
if response.status_code == 200:
    businesses = response.json()
    print(f"   Total businesses: {len(businesses)}")
    for i, business in enumerate(businesses[:5]):  # Show first 5
        print(f"   {i+1}. {business.get('business_name', 'No name')} - KYC: {business.get('kyc_status', 'No status')} - ID: {business.get('id', 'No ID')}")
else:
    print(f"   ERROR: {response.status_code} - {response.text}")

print()

# 2. Check customer restaurants endpoint
print("2. CUSTOMER VIEW - /api/restaurants:")
response = requests.get(f"{BACKEND_URL}/restaurants")
if response.status_code == 200:
    restaurants = response.json()
    print(f"   Total restaurants: {len(restaurants)}")
    for i, restaurant in enumerate(restaurants[:5]):  # Show first 5
        print(f"   {i+1}. {restaurant.get('business_name', restaurant.get('name', 'No name'))} - KYC: {restaurant.get('kyc_status', 'No status')}")
else:
    print(f"   ERROR: {response.status_code} - {response.text}")

print()

# 3. Check if there's a different endpoint for customer restaurants
print("3. CUSTOMER VIEW - /api/businesses (alternative endpoint):")
response = requests.get(f"{BACKEND_URL}/businesses")
if response.status_code == 200:
    businesses = response.json()
    print(f"   Total businesses: {len(businesses)}")
    for i, business in enumerate(businesses[:5]):  # Show first 5
        print(f"   {i+1}. {business.get('business_name', business.get('name', 'No name'))} - KYC: {business.get('kyc_status', 'No status')}")
else:
    print(f"   ERROR: {response.status_code} - {response.text}")

print()

# 4. Check with customer authentication
print("4. CUSTOMER AUTHENTICATED VIEW - /api/restaurants:")
headers = {"Authorization": f"Bearer {customer_token}"}
response = requests.get(f"{BACKEND_URL}/restaurants", headers=headers)
if response.status_code == 200:
    restaurants = response.json()
    print(f"   Total restaurants: {len(restaurants)}")
    for i, restaurant in enumerate(restaurants[:5]):  # Show first 5
        print(f"   {i+1}. {restaurant.get('business_name', restaurant.get('name', 'No name'))} - KYC: {restaurant.get('kyc_status', 'No status')}")
else:
    print(f"   ERROR: {response.status_code} - {response.text}")

print()

# 5. Look for target businesses specifically
print("5. SEARCHING FOR TARGET BUSINESSES:")
target_names = ["Test Restoranı", "Pizza Palace İstanbul"]

# Check in admin businesses
print("   In admin businesses:")
response = requests.get(f"{BACKEND_URL}/admin/businesses", headers={"Authorization": f"Bearer {admin_token}"})
if response.status_code == 200:
    businesses = response.json()
    for target in target_names:
        found = [b for b in businesses if target in b.get('business_name', '')]
        if found:
            for business in found:
                print(f"   ✅ Found '{target}': ID={business.get('id')}, KYC={business.get('kyc_status')}")
        else:
            print(f"   ❌ '{target}' not found in admin businesses")

# Check in customer restaurants
print("   In customer restaurants:")
response = requests.get(f"{BACKEND_URL}/restaurants")
if response.status_code == 200:
    restaurants = response.json()
    for target in target_names:
        found = [r for r in restaurants if target in r.get('business_name', r.get('name', ''))]
        if found:
            for restaurant in found:
                print(f"   ✅ Found '{target}': KYC={restaurant.get('kyc_status')}")
        else:
            print(f"   ❌ '{target}' not found in customer restaurants")

print()
print("=" * 60)
print("🎯 CONCLUSION:")
print("If target businesses are in admin view but not customer view,")
print("there's a filtering issue in the customer endpoint.")