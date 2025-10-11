#!/usr/bin/env python3
"""
Create test products for approved businesses to enable E2E testing
"""

import requests
import json

# Configuration
BACKEND_URL = "https://courier-stable.preview.emergentagent.com/api"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBrdXJ5ZWNpbmkuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzU5NzQ4MTU5LCJ0eXBlIjoiYWNjZXNzIn0.LfLQZ25_9WOV05CJ40n1Ebn6WTsD3sUlJcuFY_d2IIg"

def create_test_products():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}
    
    # Test products for approved businesses
    businesses_products = {
        "6704e226-0d67-4c6b-ad0f-030c026540f3": [  # Fix Test Restaurant
            {"name": "Margherita Pizza", "price": 45.0, "category": "pizza", "description": "Domates sosu, mozzarella, fesleğen", "availability": True},
            {"name": "Chicken Burger", "price": 35.0, "category": "main", "description": "Izgara tavuk, salata, patates", "availability": True},
            {"name": "Caesar Salad", "price": 25.0, "category": "salad", "description": "Marul, parmesan, kruton", "availability": True},
            {"name": "Tiramisu", "price": 20.0, "category": "dessert", "description": "Geleneksel İtalyan tatlısı", "availability": True},
        ],
        "45b3c904-c138-4e3a-acef-832b2c80cd3c": [  # New Test Restaurant  
            {"name": "Döner Kebap", "price": 30.0, "category": "main", "description": "Et döner, lavash, salata", "availability": True},
            {"name": "Lahmacun", "price": 15.0, "category": "main", "description": "İnce hamur, kıyma, sebze", "availability": True},
            {"name": "Ayran", "price": 8.0, "category": "drink", "description": "Soğuk ayran", "availability": True},
        ],
        "23b59e66-0ad3-468c-b3a4-296bd4af63d7": [  # Dönercioo (Aksaray)
            {"name": "Adana Kebap", "price": 40.0, "category": "main", "description": "Acılı Adana kebap", "availability": True},
            {"name": "Urfa Kebap", "price": 38.0, "category": "main", "description": "Acısız Urfa kebap", "availability": True},
            {"name": "Pide", "price": 25.0, "category": "main", "description": "Kaşarlı pide", "availability": True},
        ]
    }
    
    for business_id, products in businesses_products.items():
        print(f"\n🏪 Creating products for business {business_id}")
        
        for product in products:
            try:
                # Create product via admin endpoint
                response = requests.post(
                    f"{BACKEND_URL}/admin/products",
                    json={
                        **product,
                        "business_id": business_id,
                        "id": f"product_{business_id}_{len(products)}_{product['name'].lower().replace(' ', '_')}"
                    },
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Created: {product['name']} - ₺{product['price']}")
                else:
                    print(f"   ❌ Failed to create {product['name']}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error creating {product['name']}: {e}")

if __name__ == "__main__":
    create_test_products()
    print("\n🎉 Test products creation completed!")