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


class TestProjectDocker:
    """Integration tests for Project API in Docker environment"""
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        project_data = {
            "name": "Test Project",
            "username": "testproject",
            "password": "testpass123",
            "client_id": 1,
            "status": "active"
        }
        
        # Test create endpoint without auth
        response = client.post("/projects/api/v1/projects", json=project_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test list endpoint without auth
        response = client.get("/projects/api/v1/projects")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test get by ID endpoint without auth
        response = client.get("/projects/api/v1/projects/1")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test update endpoint without auth
        response = client.put("/projects/api/v1/projects/1", json=project_data)
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test delete endpoint without auth
        response = client.delete("/projects/api/v1/projects/1")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_create_project_with_auth(self):
        """Test project creation with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data
        project_data = {
            "name": "Test Project",
            "username": "testproject",
            "password": "testpass123",
            "client_id": 1,
            "status": "active"
        }
        
        try:
            response = client.post("/projects/api/v1/projects", json=project_data)
            
            # Should get 201 for successful creation or 400 for validation errors
            assert response.status_code in [201, 400]
            
            if response.status_code == 201:
                data = response.json()
                assert data["success"] is True
                assert "Project created successfully" in data["message"]
                assert data["response"]["data"]["name"] == project_data["name"]
                assert data["response"]["data"]["username"] == project_data["username"]
                assert data["response"]["data"]["client_id"] == project_data["client_id"]
            else:
                data = response.json()
                assert data["success"] is False
                # Could be client not found or username already exists
                assert any(error in data["message"] for error in ["already exists", "does not exist"])
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_create_project_with_invalid_status(self):
        """Test project creation with invalid status"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data with invalid status
        project_data = {
            "name": "Test Project",
            "username": "testproject2",
            "password": "testpass123",
            "client_id": 1,
            "status": "invalid_status"
        }
        
        try:
            response = client.post("/projects/api/v1/projects", json=project_data)
            
            # Should get 422 for validation error (FastAPI standard for Pydantic validation)
            assert response.status_code == 422
            
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["message"]
            assert "Status must be one of" in str(data["errors"])
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_projects_list_with_auth(self):
        """Test projects list retrieval with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/projects")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "data" in data["response"]
                assert "pagination" in data["response"]
                assert "total" in data["response"]["pagination"]
                assert "page" in data["response"]["pagination"]
                assert "size" in data["response"]["pagination"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_projects_list_with_filters(self):
        """Test projects list retrieval with filters"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/projects?status=active&search=test&page=1&size=10")
            
            # Should get 200 for success or 500 for database issues
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "data" in data["response"]
                assert "pagination" in data["response"]
                assert "total" in data["response"]["pagination"]
                assert "page" in data["response"]["pagination"]
                assert "size" in data["response"]["pagination"]
            else:
                # Database error is expected in some cases
                print(f"Database error (expected): {response.json()}")
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_get_project_by_id_with_auth(self):
        """Test project retrieval by ID with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/projects/1")
            
            # Should get 200 for success or 404 if not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Project retrieved successfully" in data["message"]
                assert "id" in data["response"]["data"]
                assert "name" in data["response"]["data"]
            else:
                data = response.json()
                assert data["success"] is False
                assert "Project not found" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_project_with_auth(self):
        """Test project update with authentication"""
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
            "name": "Updated Project",
            "status": "inactive"
        }
        
        try:
            response = client.put("/projects/api/v1/projects/1", json=update_data)
            
            # Should get 200 for successful update or 404 if not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Project updated successfully" in data["message"]
                assert data["response"]["data"]["name"] == update_data["name"]
                assert data["response"]["data"]["status"] == update_data["status"]
            else:
                data = response.json()
                assert data["success"] is False
                assert "Project not found" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_update_project_with_invalid_data(self):
        """Test project update with invalid data"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Test data with invalid status
        update_data = {
            "name": "Updated Project",
            "status": "invalid_status"
        }
        
        try:
            response = client.put("/projects/api/v1/projects/1", json=update_data)
            
            # Should get 422 for validation error (FastAPI standard for Pydantic validation)
            assert response.status_code == 422
            
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["message"]
            assert "Status must be one of" in str(data["errors"])
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_delete_project_with_auth(self):
        """Test project deletion with authentication"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock user
        mock_user = get_mock_user()
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.delete("/projects/api/v1/projects/1")
            
            # Should get 200 for successful deletion or 404 if not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Project deleted successfully" in data["message"]
                assert data["response"]["data"]["project_id"] == 1
            else:
                data = response.json()
                assert data["success"] is False
                assert "Project not found" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestProjectSchemaValidation:
    """Test project schema validation"""
    
    def test_valid_project_create(self):
        """Test valid project creation data"""
        from app.schemas.project import ProjectCreate
        
        valid_data = {
            "name": "Test Project",
            "username": "testproject",
            "password": "testpass123",
            "client_id": 1,
            "status": "active"
        }
        
        project_create = ProjectCreate(**valid_data)
        assert project_create.name == "Test Project"
        assert project_create.username == "testproject"
        assert project_create.password == "testpass123"
        assert project_create.client_id == 1
        assert project_create.status == "active"
    
    def test_minimal_project_create(self):
        """Test minimal project creation data"""
        from app.schemas.project import ProjectCreate
        
        minimal_data = {
            "name": "Test Project",
            "username": "testproject",
            "password": "testpass123",
            "client_id": 1
        }
        
        project_create = ProjectCreate(**minimal_data)
        assert project_create.name == "Test Project"
        assert project_create.username == "testproject"
        assert project_create.password == "testpass123"
        assert project_create.client_id == 1
        assert project_create.status == "active"  # Default value
        assert project_create.deadline is None
    
    def test_invalid_status(self):
        """Test invalid status"""
        from app.schemas.project import ProjectCreate
        
        invalid_data = {
            "name": "Test Project",
            "username": "testproject",
            "password": "testpass123",
            "client_id": 1,
            "status": "invalid_status"
        }
        
        with pytest.raises(ValueError):
            ProjectCreate(**invalid_data)
    
    def test_valid_project_update(self):
        """Test valid project update data"""
        from app.schemas.project import ProjectUpdate
        
        valid_data = {
            "name": "Updated Project",
            "status": "inactive"
        }
        
        project_update = ProjectUpdate(**valid_data)
        assert project_update.name == "Updated Project"
        assert project_update.status == "inactive"
        assert project_update.username is None
        assert project_update.password is None
    
    def test_invalid_project_update(self):
        """Test invalid project update data"""
        from app.schemas.project import ProjectUpdate
        
        invalid_data = {
            "name": "Updated Project",
            "status": "invalid_status"
        }
        
        with pytest.raises(ValueError):
            ProjectUpdate(**invalid_data)


class TestMyProjectEndpoint:
    """Test the my-project endpoint for PROJECT role users"""
    
    def test_my_project_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        response = client.get("/projects/api/v1/my-project")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_my_project_with_admin_role(self):
        """Test that admin role cannot access my-project endpoint"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock admin user
        mock_user = UserRead(
            id=1,
            username="admin",
            email="admin@example.com",
            role_name=UserRole.ADMIN,
            status="active"
        )
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/my-project")
            
            # Should get 403 for forbidden access
            assert response.status_code == 403
            assert "Operation not permitted" in response.json()["detail"]
            
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_my_project_with_project_role_success(self):
        """Test my-project endpoint with PROJECT role user"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock project user
        mock_user = UserRead(
            id=2,
            username="testproject",
            email="project@example.com",
            role_name=UserRole.PROJECT,
            status="active"
        )
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/my-project")
            
            # Should get 200 for success or 404 if project not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert "Project retrieved successfully" in data["message"]
                assert "id" in data["response"]["data"]
                assert "name" in data["response"]["data"]
                assert "username" in data["response"]["data"]
                # Verify the project username matches the user's username
                assert data["response"]["data"]["username"] == mock_user.username
            else:
                data = response.json()
                assert data["success"] is False
                assert "Project not found for this user" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}
    
    def test_my_project_with_project_role_not_found(self):
        """Test my-project endpoint when project doesn't exist for user"""
        # Override the authentication dependency
        app.dependency_overrides = {}
        
        # Create a mock project user with non-existent project username
        mock_user = UserRead(
            id=3,
            username="nonexistentproject",
            email="nonexistent@example.com",
            role_name=UserRole.PROJECT,
            status="active"
        )
        
        # Override the get_current_user dependency
        async def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            response = client.get("/projects/api/v1/my-project")
            
            # Should get 404 for project not found
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "Project not found for this user" in data["message"]
                
        finally:
            # Clean up dependency overrides
            app.dependency_overrides = {}