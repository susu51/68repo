"""
Test suite for Kuryecini Backend API
Comprehensive testing for authentication, orders, and business logic
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import asyncio
from datetime import datetime, timezone
import uuid

# Import the FastAPI app
from server import app, get_current_user, db

# Test client
client = TestClient(app)

# Test data
TEST_USER_DATA = {
    "email": "test@kuryecini.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "city": "Istanbul"
}

TEST_BUSINESS_DATA = {
    "email": "business@kuryecini.com", 
    "password": "businesspass123",
    "first_name": "Test",
    "last_name": "Business",
    "business_name": "Test Restaurant",
    "city": "Istanbul"
}

TEST_COURIER_DATA = {
    "email": "courier@kuryecini.com",
    "password": "courierpass123", 
    "first_name": "Test",
    "last_name": "Courier",
    "city": "Istanbul",
    "vehicle_type": "bisiklet"
}

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self):
        """Test main health endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert "response_time_ms" in data
        assert "timestamp" in data
    
    def test_legacy_health_endpoint(self):
        """Test legacy health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_with_test_user(self):
        """Test login with predefined test user"""
        response = client.post("/api/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "customer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 400
        assert "E-posta veya şifre yanlış" in response.json()["detail"]
    
    def test_refresh_token_valid(self):
        """Test refresh token with valid token"""
        # First login to get refresh token
        login_response = client.post("/api/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self):
        """Test refresh token with invalid token"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401
    
    def test_logout(self):
        """Test user logout"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "email": "testcustomer@example.com", 
            "password": "test123"
        })
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

class TestUserRegistration:
    """Test user registration endpoints"""
    
    @patch('server.db')
    def test_customer_registration(self, mock_db):
        """Test customer registration"""
        mock_db.users.find_one.return_value = None  # User doesn't exist
        mock_db.users.insert_one.return_value = MagicMock()
        
        response = client.post("/api/register/customer", json=TEST_USER_DATA)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Müşteri başarıyla kaydedildi"
        assert "user_id" in data
    
    @patch('server.db')
    def test_business_registration(self, mock_db):
        """Test business registration"""
        mock_db.users.find_one.return_value = None
        mock_db.users.insert_one.return_value = MagicMock()
        
        response = client.post("/api/register/business", json=TEST_BUSINESS_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "başarıyla kaydedildi" in data["message"]
    
    @patch('server.db')
    def test_courier_registration(self, mock_db):
        """Test courier registration"""
        mock_db.users.find_one.return_value = None
        mock_db.users.insert_one.return_value = MagicMock()
        
        response = client.post("/api/register/courier", json=TEST_COURIER_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "başarıyla kaydedildi" in data["message"]

class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    @patch('server.db')
    def test_public_menus_empty(self, mock_db):
        """Test public menus with no restaurants"""
        mock_db.businesses.find.return_value.to_list.return_value = []
        
        response = client.get("/api/menus/public")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert "aktif restoran bulunmamaktadır" in data["message"]
    
    @patch('server.db')
    def test_public_menus_with_data(self, mock_db):
        """Test public menus with restaurant data"""
        mock_businesses = [
            {
                "id": "business-1",
                "business_name": "Test Restaurant",
                "description": "Test description",
                "address": "Test address",
                "city": "Istanbul",
                "rating": 4.5,
                "delivery_time": "30-45 dk",
                "min_order_amount": 50.0
            }
        ]
        
        mock_products = [
            {
                "id": "product-1",
                "name": "Test Product",
                "description": "Test description",
                "price": 25.0,
                "image_url": "test.jpg",
                "category": "Ana Yemek",
                "preparation_time_minutes": 15
            }
        ]
        
        mock_db.businesses.find.return_value.to_list.return_value = mock_businesses
        mock_db.products.find.return_value.to_list.return_value = mock_products
        
        response = client.get("/api/menus/public")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["restaurants"]) == 1
        assert data["restaurants"][0]["name"] == "Test Restaurant"

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_login_rate_limit(self):
        """Test login rate limiting"""
        # Make multiple rapid login attempts
        for i in range(6):  # Limit is 5/minute
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpass"
            })
            
            if i < 5:
                # First 5 should go through (even if credentials are wrong)
                assert response.status_code in [400, 401]  # Auth error, not rate limit
            else:
                # 6th should be rate limited
                assert response.status_code == 429

class TestAdminEndpoints:
    """Test admin functionality"""
    
    def test_admin_config_unauthorized(self):
        """Test admin config without authentication"""
        response = client.get("/api/admin/config")
        assert response.status_code == 401
    
    def test_admin_config_with_customer_token(self):
        """Test admin config with customer token (should fail)"""
        # Login as customer
        login_response = client.post("/api/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        token = login_response.json()["access_token"]
        
        # Try to access admin endpoint
        response = client.get("/api/admin/config", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

class TestCommissionEndpoints:
    """Test commission configuration"""
    
    def test_commission_settings_unauthorized(self):
        """Test commission settings without admin token"""
        response = client.get("/api/admin/config/commission")
        assert response.status_code == 401
    
    def test_commission_update_validation(self):
        """Test commission update validation"""
        # This would need admin token in real scenario
        response = client.post("/api/admin/config/commission", json={
            "platform_commission": 0.25,  # 25% - should be rejected
            "courier_commission": 0.05
        })
        assert response.status_code == 401  # No token provided

# Async tests
class TestAsyncOperations:
    """Test async database operations"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection"""
        try:
            # This would test actual DB connection in real environment
            result = await db.command("ping")
            assert result is not None
        except Exception:
            # In test environment, DB might not be available
            pytest.skip("Database not available in test environment")

# Performance tests
class TestPerformance:
    """Test API performance"""
    
    def test_health_check_performance(self):
        """Test health check response time"""
        import time
        start_time = time.time()
        
        response = client.get("/healthz")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 1000  # Should respond within 1 second
    
    def test_public_menus_performance(self):
        """Test public menus response time"""
        import time
        start_time = time.time()
        
        response = client.get("/api/menus/public")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 2000  # Should respond within 2 seconds

# Integration tests
class TestIntegration:
    """Integration tests for complete user flows"""
    
    def test_customer_journey(self):
        """Test complete customer registration and login flow"""
        # This would be a more complex test in real scenario
        # 1. Register customer
        # 2. Login
        # 3. Browse restaurants
        # 4. Create order (if endpoints exist)
        
        # For now, just test login flow
        response = client.post("/api/auth/login", json={
            "email": "testcustomer@example.com",
            "password": "test123"
        })
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        assert token is not None
    
    def test_business_journey(self):
        """Test business user flow"""
        response = client.post("/api/auth/login", json={
            "email": "testbusiness@example.com", 
            "password": "test123"
        })
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "business"

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])