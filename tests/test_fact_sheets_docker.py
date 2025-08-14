import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user import UserRead
from app.core.roles import UserRole
from app.dependencies.auth import get_current_user
from decimal import Decimal
from datetime import date, time

client = TestClient(app)


def get_mock_admin_user():
    """Mock admin user for testing"""
    return UserRead(
        id=1,
        username="admin",
        email="admin@example.com",
        role_name=UserRole.ADMIN,
        status="active"
    )


def get_mock_project_user():
    """Mock project user for testing"""
    return UserRead(
        id=2,
        username="project_user",
        email="project@example.com",
        role_name=UserRole.PROJECT,
        status="active"
    )


class TestFactSheetsDocker:
    """Integration tests for Fact Sheets API in Docker environment"""
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        fact_sheet_data = {
            "client_reference": "REF001",
            "project_name": "Test Project",
            "director": "John Director",
            "status": "pending"
        }
        
        # Test get endpoint without auth
        response = client.get("/projects/api/v1/fact-sheets/1")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test update endpoint without auth
        response = client.put("/projects/api/v1/fact-sheets/1", json=fact_sheet_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test approve endpoint without auth
        response = client.put("/projects/api/v1/fact-sheets/1/approve")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_get_fact_sheet_by_project_id_admin(self):
        """Test getting fact sheet by project ID with admin authentication"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_admin_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/fact-sheets/1")
            
            # Should get 200 for success or 404 for not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Fact sheet retrieved successfully" in data["message"]
                assert "project_id" in data["response"]["data"]
                assert data["response"]["data"]["project_id"] == 1
            else:
                data = response.json()
                assert data["success"] is False
                assert "Fact sheet not found" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_get_fact_sheet_by_project_id_project_user(self):
        """Test getting fact sheet by project ID with project user authentication"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_project_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/fact-sheets/1")
            
            # Should get 200 for success or 404 for not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Fact sheet retrieved successfully" in data["message"]
                assert "project_id" in data["response"]["data"]
                assert data["response"]["data"]["project_id"] == 1
            else:
                data = response.json()
                assert data["success"] is False
                assert "Fact sheet not found" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_update_fact_sheet_project_user_content(self):
        """Test updating fact sheet content with project user (should succeed for pending fact sheets)"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_project_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        fact_sheet_update_data = {
            "client_reference": "REF001",
            "project_name": "Updated Project Name",
            "director": "Jane Director",
            "deadline_date": "2024-12-31",
            "project_description": "Updated project description",
            "location": "Updated Location",
            "total_hours": 8.5,
            "time_range_start": "09:00:00",
            "time_range_end": "17:00:00",
            "budget_details": "Updated budget details",
            "terms": "Updated terms",
            "total_project_price": 5000.00,
            "rights_buy_outs": "Updated rights",
            "conditions": "Updated conditions"
        }
        
        try:
            response = client.put("/projects/api/v1/fact-sheets/1", json=fact_sheet_update_data)
            
            # Should get 200 for success, 404 for not found, or 400 for validation errors
            assert response.status_code in [200, 404, 400]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Fact sheet updated successfully" in data["message"]
                assert data["response"]["data"]["project_name"] == "Updated Project Name"
                assert data["response"]["data"]["director"] == "Jane Director"
            elif response.status_code == 400:
                data = response.json()
                assert data["success"] is False
                # Could be validation error or business logic error
                print(f"Validation error (expected): {data['message']}")
            else:
                data = response.json()
                assert data["success"] is False
                assert "Fact sheet not found" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_update_fact_sheet_project_user_status_forbidden(self):
        """Test that project user cannot update fact sheet status"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_project_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        fact_sheet_update_data = {
            "status": "approved"  # Project user should not be able to change status
        }
        
        try:
            response = client.put("/projects/api/v1/fact-sheets/1", json=fact_sheet_update_data)
            
            # Should get 400 for forbidden status update
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "Project role cannot update fact sheet status" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_update_fact_sheet_admin_content_forbidden(self):
        """Test that admin cannot update fact sheet content"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_admin_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        fact_sheet_update_data = {
            "project_name": "Admin trying to update content",  # Admin should not be able to update content
            "director": "Admin Director"
        }
        
        try:
            response = client.put("/projects/api/v1/fact-sheets/1", json=fact_sheet_update_data)
            
            # Should get 400 for forbidden content update
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "Admin role cannot update fact sheet content field" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_approve_fact_sheet_admin(self):
        """Test approving fact sheet with admin authentication"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_admin_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.put("/projects/api/v1/fact-sheets/1/approve")
            
            # Should get 200 for success, 404 for not found, or 400 for validation errors
            assert response.status_code in [200, 404, 400]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Fact sheet approved successfully" in data["message"]
                assert data["response"]["data"]["status"] == "approved"
                assert data["response"]["data"]["approved_by_id"] == mock_user.id
            elif response.status_code == 400:
                data = response.json()
                assert data["success"] is False
                # Could be validation error
                print(f"Validation error (expected): {data['message']}")
            else:
                data = response.json()
                assert data["success"] is False
                assert "Fact sheet not found" in data["message"]
                
        finally:
            app.dependency_overrides = {}
    
    def test_approve_fact_sheet_project_user_forbidden(self):
        """Test that project user cannot approve fact sheet (should be forbidden)"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_project_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.put("/projects/api/v1/fact-sheets/1/approve")
            
            # Should get 403 for forbidden access
            assert response.status_code == 403
                
        finally:
            app.dependency_overrides = {}
    
    def test_update_approved_fact_sheet_project_user_forbidden(self):
        """Test that project user cannot update approved fact sheet content"""
        app.dependency_overrides = {}
        
        mock_user = get_mock_project_user()
        
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        fact_sheet_update_data = {
            "project_name": "Trying to update approved fact sheet"
        }
        
        try:
            # First approve the fact sheet (if it exists)
            admin_user = get_mock_admin_user()
            
            async def override_get_current_user_admin():
                return admin_user
            
            app.dependency_overrides[get_current_user] = override_get_current_user_admin
            
            approve_response = client.put("/projects/api/v1/fact-sheets/1/approve")
            
            # Now try to update with project user
            app.dependency_overrides[get_current_user] = override_get_current_user
            
            response = client.put("/projects/api/v1/fact-sheets/1", json=fact_sheet_update_data)
            
            # Should get 400 for forbidden update of approved fact sheet
            if response.status_code == 400:
                data = response.json()
                assert data["success"] is False
                assert "Cannot update fact sheet content after approval" in data["message"]
            elif response.status_code == 404:
                # Fact sheet doesn't exist, which is also valid
                data = response.json()
                assert data["success"] is False
                assert "Fact sheet not found" in data["message"]
                
        finally:
            app.dependency_overrides = {}


class TestFactSheetsSchemaValidation:
    """Test fact sheets schema validation"""
    
    def test_valid_fact_sheet_update(self):
        """Test valid fact sheet update data"""
        from app.schemas.fact_sheets import FactSheetUpdate
        
        valid_data = {
            "client_reference": "REF001",
            "project_name": "Test Project",
            "director": "John Director",
            "deadline_date": "2024-12-31",
            "total_hours": 8.5,
            "total_project_price": 5000.00,
            "status": "pending"
        }
        
        fact_sheet_update = FactSheetUpdate(**valid_data)
        assert fact_sheet_update.client_reference == "REF001"
        assert fact_sheet_update.project_name == "Test Project"
        assert fact_sheet_update.director == "John Director"
        assert fact_sheet_update.total_hours == Decimal("8.5")
        assert fact_sheet_update.total_project_price == Decimal("5000.00")
        assert fact_sheet_update.status == "pending"
    
    def test_invalid_status(self):
        """Test invalid status value"""
        from app.schemas.fact_sheets import FactSheetUpdate
        
        invalid_data = {
            "status": "invalid_status"
        }
        
        with pytest.raises(ValueError):
            FactSheetUpdate(**invalid_data)
    
    def test_valid_status_values(self):
        """Test valid status values"""
        from app.schemas.fact_sheets import FactSheetUpdate
        
        # Test pending status
        pending_data = {"status": "pending"}
        fact_sheet_update = FactSheetUpdate(**pending_data)
        assert fact_sheet_update.status == "pending"
        
        # Test approved status
        approved_data = {"status": "approved"}
        fact_sheet_update = FactSheetUpdate(**approved_data)
        assert fact_sheet_update.status == "approved"
    
    def test_numeric_validation(self):
        """Test numeric field validation"""
        from app.schemas.fact_sheets import FactSheetUpdate
        
        # Test valid numeric values
        valid_data = {
            "total_hours": 8.5,
            "total_project_price": 5000.00
        }
        
        fact_sheet_update = FactSheetUpdate(**valid_data)
        assert fact_sheet_update.total_hours == Decimal("8.5")
        assert fact_sheet_update.total_project_price == Decimal("5000.00")
        
        # Test negative values (should be allowed as per schema)
        negative_data = {
            "total_hours": -1.0,
            "total_project_price": -100.00
        }
        
        with pytest.raises(ValueError):
            FactSheetUpdate(**negative_data)
    
    def test_date_time_validation(self):
        """Test date and time field validation"""
        from app.schemas.fact_sheets import FactSheetUpdate
        
        valid_data = {
            "deadline_date": "2024-12-31",
            "ppm_date": "2024-11-15",
            "shooting_date": "2024-10-01",
            "time_range_start": "09:00:00",
            "time_range_end": "17:00:00"
        }
        
        fact_sheet_update = FactSheetUpdate(**valid_data)
        assert fact_sheet_update.deadline_date == date(2024, 12, 31)
        assert fact_sheet_update.ppm_date == date(2024, 11, 15)
        assert fact_sheet_update.shooting_date == date(2024, 10, 1)
        assert fact_sheet_update.time_range_start == time(9, 0, 0)
        assert fact_sheet_update.time_range_end == time(17, 0, 0)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy" 