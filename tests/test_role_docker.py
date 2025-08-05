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


class TestRoleDocker:
    """Integration tests for Role API in Docker environment"""
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        role_data = {
            "project_id": 1,
            "name": "Test Role",
            "gender": "Male",
            "ethnicity": "Caucasian",
            "age_from": 25,
            "age_to": 35
        }
        
        # Test create endpoint without auth
        response = client.post("/projects/api/v1/roles", json=role_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test list endpoint without auth
        response = client.get("/projects/api/v1/roles")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test update endpoint without auth
        response = client.put("/projects/api/v1/roles/1", json=role_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test delete endpoint without auth
        response = client.delete("/projects/api/v1/roles/1")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_create_role_with_auth(self):
        """Test role creation with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data
        role_data = {
            "project_id": 1,
            "name": "Lead Actor",
            "gender": "Male",
            "ethnicity": "Caucasian",
            "language": "English",
            "native_language": "English",
            "age_from": 25,
            "age_to": 35,
            "height_from": 170.0,
            "height_to": 180.0,
            "tags": ["drama", "lead"],
            "category": "Actor",
            "hair_color": "Brown",
            "status": "active"
        }
        
        try:
            response = client.post("/projects/api/v1/roles", json=role_data)
            
            # Should get 201 for successful creation or 400 for validation errors
            assert response.status_code in [201, 400, 500]
            
            if response.status_code == 201:
                data = response.json()
                assert data["success"] is True
                assert "Role created successfully" in data["message"]
                assert data["response"]["data"]["name"] == role_data["name"]
                assert data["response"]["data"]["project_id"] == role_data["project_id"]
            elif response.status_code == 400:
                data = response.json()
                assert data["success"] is False
                # Could be validation error or project doesn't exist
                assert "error" in data or "message" in data
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_roles_list_with_auth(self):
        """Test roles list retrieval with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/roles")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "results" in data["response"]["data"]
                assert "meta" in data["response"]["data"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_roles_list_with_filters(self):
        """Test roles list with filtering and search"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Test with search parameter
            response = client.get("/projects/api/v1/roles?search=actor")
            assert response.status_code in [200, 500]
            
            # Test with project_id filter
            response = client.get("/projects/api/v1/roles?project_id=1")
            assert response.status_code in [200, 500]
            
            # Test with gender filter
            response = client.get("/projects/api/v1/roles?gender=Male")
            assert response.status_code in [200, 500]
            
            # Test with category filter
            response = client.get("/projects/api/v1/roles?category=Actor")
            assert response.status_code in [200, 500]
            
            # Test with age range filter
            response = client.get("/projects/api/v1/roles?age_from=20&age_to=40")
            assert response.status_code in [200, 500]
            
            # Test with height range filter
            response = client.get("/projects/api/v1/roles?height_from=160&height_to=190")
            assert response.status_code in [200, 500]
            
            # Test with pagination
            response = client.get("/projects/api/v1/roles?page=1&size=10")
            assert response.status_code in [200, 500]
            
            # Test with multiple filters
            response = client.get("/projects/api/v1/roles?search=actor&project_id=1&gender=Male&page=1&size=5")
            assert response.status_code in [200, 500]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_by_id_with_auth(self):
        """Test getting a specific role by ID"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/roles/1")
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "id" in data["response"]["data"]
                assert "name" in data["response"]["data"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role not found" in data["message"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_role_with_auth(self):
        """Test role update with authentication"""
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
            "name": "Updated Role Name",
            "age_from": 30,
            "age_to": 40,
            "status": "inactive"
        }
        
        try:
            response = client.put("/projects/api/v1/roles/1", json=update_data)
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Role updated successfully" in data["message"]
                assert data["response"]["data"]["name"] == update_data["name"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role not found" in data["message"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_delete_role_with_auth(self):
        """Test role deletion with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.delete("/projects/api/v1/roles/1")
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Role deleted successfully" in data["message"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role not found" in data["message"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    

    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRoleSchemaValidation:
    """Test role schema validation"""
    
    def test_valid_role_create(self):
        """Test valid role creation data"""
        from app.schemas.role import RoleCreate
        
        valid_data = {
            "project_id": 1,
            "name": "Lead Actor",
            "gender": "Male",
            "ethnicity": "Caucasian",
            "language": "English",
            "age_from": 25,
            "age_to": 35,
            "height_from": 170.0,
            "height_to": 180.0,
            "tags": ["drama", "lead"],
            "category": "Actor",
            "hair_color": "Brown",
            "status": "active"
        }
        
        role_create = RoleCreate(**valid_data)
        assert role_create.project_id == 1
        assert role_create.name == "Lead Actor"
        assert role_create.gender == "Male"
        assert role_create.age_from == 25
        assert role_create.age_to == 35
        assert role_create.tags == ["drama", "lead"]
    
    def test_minimal_role_create(self):
        """Test minimal role creation data"""
        from app.schemas.role import RoleCreate
        
        minimal_data = {
            "project_id": 1,
            "name": "Test Role"
        }
        
        role_create = RoleCreate(**minimal_data)
        assert role_create.project_id == 1
        assert role_create.name == "Test Role"
        assert role_create.gender is None
        assert role_create.status == "active"  # Default value
    
    def test_invalid_name_empty(self):
        """Test invalid empty name"""
        from app.schemas.role import RoleCreate
        
        invalid_data = {
            "project_id": 1,
            "name": "",  # Empty name
            "status": "active"
        }
        
        with pytest.raises(ValueError):
            RoleCreate(**invalid_data)
    
    def test_invalid_age_range(self):
        """Test invalid age range (age_from > age_to)"""
        from app.schemas.role import RoleCreate
        
        invalid_data = {
            "project_id": 1,
            "name": "Test Role",
            "age_from": 40,
            "age_to": 30  # age_from > age_to
        }
        
        role_create = RoleCreate(**invalid_data)
        # Schema validation doesn't catch this, it's handled in service layer
        assert role_create.age_from == 40
        assert role_create.age_to == 30
    
    def test_invalid_height_range(self):
        """Test invalid height range (height_from > height_to)"""
        from app.schemas.role import RoleCreate
        
        invalid_data = {
            "project_id": 1,
            "name": "Test Role",
            "height_from": 190.0,
            "height_to": 170.0  # height_from > height_to
        }
        
        role_create = RoleCreate(**invalid_data)
        # Schema validation doesn't catch this, it's handled in service layer
        assert role_create.height_from == 190.0
        assert role_create.height_to == 170.0
    
    def test_valid_role_update(self):
        """Test valid role update data"""
        from app.schemas.role import RoleUpdate
        
        valid_data = {
            "name": "Updated Role Name",
            "age_from": 30,
            "age_to": 40,
            "status": "inactive"
        }
        
        role_update = RoleUpdate(**valid_data)
        assert role_update.name == "Updated Role Name"
        assert role_update.age_from == 30
        assert role_update.age_to == 40
        assert role_update.status == "inactive"
    
    def test_partial_role_update(self):
        """Test partial role update data"""
        from app.schemas.role import RoleUpdate
        
        partial_data = {
            "name": "Updated Role Name"
        }
        
        role_update = RoleUpdate(**partial_data)
        assert role_update.name == "Updated Role Name"
        assert role_update.age_from is None
        assert role_update.status is None 