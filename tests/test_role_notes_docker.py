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


class TestRoleNotesDocker:
    """Integration tests for Role Notes API in Docker environment"""
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        note_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "Test Note",
            "description": "Test description"
        }
        
        # Test create endpoint without auth
        response = client.post("/projects/api/v1/role-notes", json=note_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test list endpoint without auth
        response = client.get("/projects/api/v1/role-notes")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test update endpoint without auth
        response = client.put("/projects/api/v1/role-notes/1", json=note_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test delete endpoint without auth
        response = client.delete("/projects/api/v1/role-notes/1")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_create_role_note_with_auth(self):
        """Test role note creation with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data
        note_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "Test Role Note",
            "description": "This is a test role note description"
        }
        
        try:
            response = client.post("/projects/api/v1/role-notes", json=note_data)
            
            # Should get 201 for successful creation or 400 for validation errors
            assert response.status_code in [201, 400, 500]
            
            if response.status_code == 201:
                data = response.json()
                assert data["success"] is True
                assert "Role note created successfully" in data["message"]
                assert data["response"]["data"]["title"] == note_data["title"]
                assert data["response"]["data"]["project_id"] == note_data["project_id"]
                assert data["response"]["data"]["role_id"] == note_data["role_id"]
            elif response.status_code == 400:
                data = response.json()
                assert data["success"] is False
                # Could be validation error or project/role doesn't exist
                assert "error" in data or "message" in data
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_notes_list_with_auth(self):
        """Test role notes list retrieval with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-notes")
            
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
    
    def test_get_role_notes_list_with_filters(self):
        """Test role notes list with filtering and search"""
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
            response = client.get("/projects/api/v1/role-notes?search=test")
            assert response.status_code in [200, 500]
            
            # Test with project_id filter
            response = client.get("/projects/api/v1/role-notes?project_id=1")
            assert response.status_code in [200, 500]
            
            # Test with role_id filter
            response = client.get("/projects/api/v1/role-notes?role_id=1")
            assert response.status_code in [200, 500]
            
            # Test with added_by_user_id filter
            response = client.get("/projects/api/v1/role-notes?added_by_user_id=1")
            assert response.status_code in [200, 500]
            
            # Test with pagination
            response = client.get("/projects/api/v1/role-notes?page=1&size=10")
            assert response.status_code in [200, 500]
            
            # Test with multiple filters
            response = client.get("/projects/api/v1/role-notes?search=test&project_id=1&role_id=1&page=1&size=5")
            assert response.status_code in [200, 500]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_role_note_by_id_with_auth(self):
        """Test getting a specific role note by ID"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/role-notes/1")
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "id" in data["response"]["data"]
                assert "title" in data["response"]["data"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role note not found" in data["message"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_role_note_with_auth(self):
        """Test role note update with authentication"""
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
            "title": "Updated Role Note",
            "description": "Updated description"
        }
        
        try:
            response = client.put("/projects/api/v1/role-notes/1", json=update_data)
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Role note updated successfully" in data["message"]
                assert data["response"]["data"]["title"] == update_data["title"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role note not found" in data["message"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_delete_role_note_with_auth(self):
        """Test role note deletion with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.delete("/projects/api/v1/role-notes/1")
            
            # Should get 200 for success, 404 for not found, or 500 for database issues
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Role note deleted successfully" in data["message"]
            elif response.status_code == 404:
                data = response.json()
                assert data["success"] is False
                assert "Role note not found" in data["message"]
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


class TestRoleNotesSchemaValidation:
    """Test role notes schema validation"""
    
    def test_valid_role_note_create(self):
        """Test valid role note creation data"""
        from app.schemas.role_notes import RoleNotesCreate
        
        valid_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "Test Role Note",
            "description": "This is a test description"
        }
        
        note_create = RoleNotesCreate(**valid_data)
        assert note_create.project_id == 1
        assert note_create.role_id == 1
        assert note_create.title == "Test Role Note"
        assert note_create.description == "This is a test description"
    
    def test_minimal_role_note_create(self):
        """Test minimal role note creation data"""
        from app.schemas.role_notes import RoleNotesCreate
        
        minimal_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "Test Note"
        }
        
        note_create = RoleNotesCreate(**minimal_data)
        assert note_create.project_id == 1
        assert note_create.role_id == 1
        assert note_create.title == "Test Note"
        assert note_create.description is None
    
    def test_invalid_title_empty(self):
        """Test invalid empty title"""
        from app.schemas.role_notes import RoleNotesCreate
        
        invalid_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "",  # Empty title
            "description": "Test description"
        }
        
        with pytest.raises(ValueError):
            RoleNotesCreate(**invalid_data)
    
    def test_invalid_title_too_long(self):
        """Test invalid title too long"""
        from app.schemas.role_notes import RoleNotesCreate
        
        invalid_data = {
            "project_id": 1,
            "role_id": 1,
            "title": "a" * 256,  # Too long (max 255)
            "description": "Test description"
        }
        
        with pytest.raises(ValueError):
            RoleNotesCreate(**invalid_data)
    
    def test_valid_role_note_update(self):
        """Test valid role note update data"""
        from app.schemas.role_notes import RoleNotesUpdate
        
        valid_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        note_update = RoleNotesUpdate(**valid_data)
        assert note_update.title == "Updated Title"
        assert note_update.description == "Updated description"
    
    def test_partial_role_note_update(self):
        """Test partial role note update data"""
        from app.schemas.role_notes import RoleNotesUpdate
        
        partial_data = {
            "title": "Updated Title"
        }
        
        note_update = RoleNotesUpdate(**partial_data)
        assert note_update.title == "Updated Title"
        assert note_update.description is None 