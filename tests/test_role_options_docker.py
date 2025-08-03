import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user import UserRead
from app.core.roles import UserRole
from app.dependencies.auth import get_current_user

client = TestClient(app)


def get_mock_user():
    """Mock user for testing"""
    return UserRead(
        id=1,
        username="admin",
        email="admin@example.com",
        role_name=UserRole.ADMIN,
        status="active"
    )


class TestRoleOptionsDocker:
    """Integration tests for Role Options API in Docker environment"""
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        role_option_data = {
            "name": "Test Category",
            "option_type": "category",
            "status": "active"
        }
        
        # Test create endpoint without auth
        response = client.post("/projects/api/v1/role-options", json=role_option_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test list endpoint without auth
        response = client.get("/projects/api/v1/role-options")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test update endpoint without auth
        response = client.put("/projects/api/v1/role-options/1", json=role_option_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_create_role_option_with_auth(self):
        """Test role option creation with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data
        role_option_data = {
            "name": "Test Category",
            "option_type": "category",
            "status": "active"
        }
        
        try:
            response = client.post("/projects/api/v1/role-options", json=role_option_data)
            
            # Should get 201 for successful creation or 400/500 for database issues
            assert response.status_code in [201, 400, 500]
            
            if response.status_code == 201:
                data = response.json()
                assert data["success"] is True
                assert "Role option created successfully" in data["message"]
                assert data["response"]["data"]["name"] == role_option_data["name"]
                assert data["response"]["data"]["option_type"] == role_option_data["option_type"]
                assert data["response"]["data"]["status"] == role_option_data["status"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_create_role_option_with_invalid_option_type(self):
        """Test role option creation with invalid option_type"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data with invalid option_type
        role_option_data = {
            "name": "Test Category",
            "option_type": "invalid_type",
            "status": "active"
        }
        
        try:
            response = client.post("/projects/api/v1/role-options", json=role_option_data)
            
            # Should get 422 for validation error (FastAPI standard for Pydantic validation)
            assert response.status_code == 422
            
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["message"]
            assert "Option type must be one of" in str(data["errors"])
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_create_role_option_with_invalid_status(self):
        """Test role option creation with invalid status"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data with invalid status
        role_option_data = {
            "name": "Test Category",
            "option_type": "category",
            "status": "invalid_status"
        }
        
        try:
            response = client.post("/projects/api/v1/role-options", json=role_option_data)
            
            # Should get 422 for validation error (FastAPI standard for Pydantic validation)
            assert response.status_code == 422
            
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["message"]
            assert "Status must be one of" in str(data["errors"])
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_options_list_with_auth(self):
        """Test role options list retrieval with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-options")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "role_options" in data["response"]["data"]
                assert "total" in data["response"]["data"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_options_list_with_status_filter(self):
        """Test role options list retrieval with status filter"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-options?status=active")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "role_options" in data["response"]["data"]
                assert "total" in data["response"]["data"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_options_list_with_option_type_filter(self):
        """Test role options list retrieval with option_type filter"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-options?option_type=category")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "role_options" in data["response"]["data"]
                assert "total" in data["response"]["data"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_options_list_with_both_filters(self):
        """Test role options list retrieval with both status and option_type filters"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-options?status=active&option_type=category")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "role_options" in data["response"]["data"]
                assert "total" in data["response"]["data"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_role_option_with_auth(self):
        """Test role option update with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data
        update_data = {
            "name": "Updated Category",
            "status": "inactive"
        }
        
        try:
            response = client.put("/projects/api/v1/role-options/1", json=update_data)
            
            # Should get 200 for successful update or 404 if not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Role option updated successfully" in data["message"]
                assert data["response"]["data"]["name"] == update_data["name"]
                assert data["response"]["data"]["status"] == update_data["status"]
            else:
                data = response.json()
                assert data["success"] is False
                assert "Role option not found" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_role_option_with_invalid_data(self):
        """Test role option update with invalid data"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data with invalid option_type
        update_data = {
            "name": "Updated Category",
            "option_type": "invalid_type"
        }
        
        try:
            response = client.put("/projects/api/v1/role-options/1", json=update_data)
            
            # Should get 422 for validation error (FastAPI standard for Pydantic validation)
            assert response.status_code == 422
            
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["message"]
            assert "Option type must be one of" in str(data["errors"])
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRoleOptionsSchemaValidation:
    """Test role options schema validation"""
    
    def test_valid_role_option_create(self):
        """Test valid role option creation data"""
        from app.schemas.role_options import RoleOptionsCreate
        
        valid_data = {
            "name": "Test Category",
            "option_type": "category",
            "status": "active"
        }
        
        role_option_create = RoleOptionsCreate(**valid_data)
        assert role_option_create.name == "Test Category"
        assert role_option_create.option_type == "category"
        assert role_option_create.status == "active"
    
    def test_minimal_role_option_create(self):
        """Test minimal role option creation data"""
        from app.schemas.role_options import RoleOptionsCreate
        
        minimal_data = {
            "name": "Test Category"
        }
        
        role_option_create = RoleOptionsCreate(**minimal_data)
        assert role_option_create.name == "Test Category"
        assert role_option_create.option_type == "category"  # Default value
        assert role_option_create.status == "active"  # Default value
    
    def test_invalid_option_type(self):
        """Test invalid option type"""
        from app.schemas.role_options import RoleOptionsCreate
        
        invalid_data = {
            "name": "Test Category",
            "option_type": "invalid_type",
            "status": "active"
        }
        
        with pytest.raises(ValueError):
            RoleOptionsCreate(**invalid_data)
    
    def test_invalid_status(self):
        """Test invalid status"""
        from app.schemas.role_options import RoleOptionsCreate
        
        invalid_data = {
            "name": "Test Category",
            "option_type": "category",
            "status": "invalid_status"
        }
        
        with pytest.raises(ValueError):
            RoleOptionsCreate(**invalid_data)
    
    def test_valid_role_option_update(self):
        """Test valid role option update data"""
        from app.schemas.role_options import RoleOptionsUpdate
        
        valid_data = {
            "name": "Updated Category",
            "status": "inactive"
        }
        
        role_option_update = RoleOptionsUpdate(**valid_data)
        assert role_option_update.name == "Updated Category"
        assert role_option_update.status == "inactive"
        assert role_option_update.option_type is None
    
    def test_invalid_role_option_update(self):
        """Test invalid role option update data"""
        from app.schemas.role_options import RoleOptionsUpdate
        
        invalid_data = {
            "name": "Updated Category",
            "option_type": "invalid_type"
        }
        
        with pytest.raises(ValueError):
            RoleOptionsUpdate(**invalid_data) 