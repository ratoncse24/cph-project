#!/bin/bash

# API Testing Script for Project Management API
# Base URL and Admin Token
BASE_URL="http://0.0.0.0:8002"
API_PREFIX="/projects/api/v1"
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsImVtYWlsIjoiYWRtaW5AZ21haWwuY29tIiwiZXhwIjoxNzU3NDcxMjY0LCJpYXQiOjE3NTU2NzEyNjQsImp0aSI6ImU2ZGJjMjYyLWE2ZTctNDhhOC05ZmJjLWU4ZmY5YjU5OWZjZiIsInR5cGUiOiJhY2Nlc3MifQ.P_-QouVIFcS2kqxu9yNrLtH1U81ddFbShid4D_gK0Xg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_result() {
    local endpoint=$1
    local status=$2
    local response=$3
    
    if [[ $status -ge 200 && $status -lt 300 ]]; then
        echo -e "${GREEN}✅ $endpoint - Status: $status${NC}"
    elif [[ $status -ge 400 && $status -lt 500 ]]; then
        echo -e "${YELLOW}⚠️  $endpoint - Status: $status${NC}"
    else
        echo -e "${RED}❌ $endpoint - Status: $status${NC}"
    fi
    
    if [[ -n "$response" ]]; then
        echo -e "${BLUE}Response: $response${NC}"
    fi
    echo "---"
}

echo -e "${BLUE}🚀 Starting API Endpoint Testing${NC}"
echo -e "${BLUE}Base URL: $BASE_URL${NC}"
echo -e "${BLUE}API Prefix: $API_PREFIX${NC}"
echo "=================================="

# Test 1: Health Check (No auth required)
echo -e "${YELLOW}1. Testing Health Check${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/health_response "$BASE_URL/health")
status_code=${response: -3}
response_content=$(cat /tmp/health_response)
print_result "GET /health" "$status_code" "$response_content"

# Test 2: Root endpoint (No auth required)
echo -e "${YELLOW}2. Testing Root Endpoint${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/root_response "$BASE_URL/")
status_code=${response: -3}
response_content=$(cat /tmp/root_response)
print_result "GET /" "$status_code" "$response_content"

# Test 3: Health Check with API prefix
echo -e "${YELLOW}3. Testing Health Check with API Prefix${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/health_api_response "$BASE_URL$API_PREFIX/health")
status_code=${response: -3}
response_content=$(cat /tmp/health_api_response)
print_result "GET $API_PREFIX/health" "$status_code" "$response_content"

# Test 4: Get Users List (Admin only)
echo -e "${YELLOW}4. Testing Get Users List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/users_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/users")
status_code=${response: -3}
response_content=$(cat /tmp/users_response)
print_result "GET $API_PREFIX/users" "$status_code" "$response_content"

# Test 5: Get Clients List (Admin only)
echo -e "${YELLOW}5. Testing Get Clients List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/clients_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/clients")
status_code=${response: -3}
response_content=$(cat /tmp/clients_response)
print_result "GET $API_PREFIX/clients" "$status_code" "$response_content"

# Test 6: Create Client (Admin only)
echo -e "${YELLOW}6. Testing Create Client${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_client_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Client",
        "email": "test@client.com",
        "phone": "+1234567890",
        "address": "123 Test Street",
        "status": "active"
    }' \
    -X POST "$BASE_URL$API_PREFIX/clients")
status_code=${response: -3}
response_content=$(cat /tmp/create_client_response)
print_result "POST $API_PREFIX/clients" "$status_code" "$response_content"

# Extract client ID from response for subsequent tests
CLIENT_ID=$(cat /tmp/create_client_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$CLIENT_ID" ]]; then
    CLIENT_ID=1  # Fallback
fi

# Test 7: Update Client (Admin only)
echo -e "${YELLOW}7. Testing Update Client${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_client_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Updated Test Client",
        "email": "updated@client.com",
        "phone": "+1234567890",
        "address": "456 Updated Street",
        "status": "active"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/clients/$CLIENT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_client_response)
print_result "PUT $API_PREFIX/clients/$CLIENT_ID" "$status_code" "$response_content"

# Test 8: Get Projects List (Admin only)
echo -e "${YELLOW}8. Testing Get Projects List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/projects_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/projects")
status_code=${response: -3}
response_content=$(cat /tmp/projects_response)
print_result "GET $API_PREFIX/projects" "$status_code" "$response_content"

# Test 9: Create Project (Admin only)
echo -e "${YELLOW}9. Testing Create Project${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_project_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Project",
        "username": "testuser",
        "password": "testpassword123",
        "client_id": '$CLIENT_ID',
        "status": "active",
        "deadline": "2024-12-31"
    }' \
    -X POST "$BASE_URL$API_PREFIX/projects")
status_code=${response: -3}
response_content=$(cat /tmp/create_project_response)
print_result "POST $API_PREFIX/projects" "$status_code" "$response_content"

# Extract project ID from response for subsequent tests
PROJECT_ID=$(cat /tmp/create_project_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID=1  # Fallback
fi

# Test 10: Get Project by ID (Admin only)
echo -e "${YELLOW}10. Testing Get Project by ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/get_project_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/projects/$PROJECT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/get_project_response)
print_result "GET $API_PREFIX/projects/$PROJECT_ID" "$status_code" "$response_content"

# Test 11: Update Project (Admin only)
echo -e "${YELLOW}11. Testing Update Project${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_project_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Updated Test Project",
        "description": "An updated test project for API testing",
        "client_id": '$CLIENT_ID',
        "username": "updateduser",
        "status": "active",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/projects/$PROJECT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_project_response)
print_result "PUT $API_PREFIX/projects/$PROJECT_ID" "$status_code" "$response_content"

# Test 12: Get Roles List (Admin only)
echo -e "${YELLOW}12. Testing Get Roles List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/roles_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/roles")
status_code=${response: -3}
response_content=$(cat /tmp/roles_response)
print_result "GET $API_PREFIX/roles" "$status_code" "$response_content"

# Test 13: Create Role (Admin only)
echo -e "${YELLOW}13. Testing Create Role${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_role_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Role",
        "gender": "female",
        "ethnicity": "caucasian",
        "language": "english",
        "category": "model",
        "hair_color": "brown",
        "eye_color": "blue",
        "age": 25,
        "height": 170.5,
        "weight": 60.0,
        "project_id": '$PROJECT_ID',
        "status": "active"
    }' \
    -X POST "$BASE_URL$API_PREFIX/roles")
status_code=${response: -3}
response_content=$(cat /tmp/create_role_response)
print_result "POST $API_PREFIX/roles" "$status_code" "$response_content"

# Extract role ID from response for subsequent tests
ROLE_ID=$(cat /tmp/create_role_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$ROLE_ID" ]]; then
    ROLE_ID=1  # Fallback
fi

# Test 14: Get Role by ID (Admin only)
echo -e "${YELLOW}14. Testing Get Role by ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/get_role_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/roles/$ROLE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/get_role_response)
print_result "GET $API_PREFIX/roles/$ROLE_ID" "$status_code" "$response_content"

# Test 15: Update Role (Admin only)
echo -e "${YELLOW}15. Testing Update Role${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_role_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Updated Test Role",
        "gender": "female",
        "ethnicity": "caucasian",
        "language": "english",
        "category": "model",
        "hair_color": "blonde",
        "eye_color": "green",
        "age": 26,
        "height": 172.0,
        "weight": 58.0,
        "project_id": '$PROJECT_ID',
        "status": "active"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/roles/$ROLE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_role_response)
print_result "PUT $API_PREFIX/roles/$ROLE_ID" "$status_code" "$response_content"

# Test 16: Get Role Options List (Admin only)
echo -e "${YELLOW}16. Testing Get Role Options List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/role_options_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/role-options")
status_code=${response: -3}
response_content=$(cat /tmp/role_options_response)
print_result "GET $API_PREFIX/role-options" "$status_code" "$response_content"

# Test 17: Create Role Option (Admin only)
echo -e "${YELLOW}17. Testing Create Role Option${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_role_option_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Option",
        "type": "category",
        "value": "test_category",
        "description": "A test role option"
    }' \
    -X POST "$BASE_URL$API_PREFIX/role-options")
status_code=${response: -3}
response_content=$(cat /tmp/create_role_option_response)
print_result "POST $API_PREFIX/role-options" "$status_code" "$response_content"

# Extract role option ID from response for subsequent tests
ROLE_OPTION_ID=$(cat /tmp/create_role_option_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$ROLE_OPTION_ID" ]]; then
    ROLE_OPTION_ID=1  # Fallback
fi

# Test 18: Update Role Option (Admin only)
echo -e "${YELLOW}18. Testing Update Role Option${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_role_option_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Updated Test Option",
        "type": "category",
        "value": "updated_test_category",
        "description": "An updated test role option"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/role-options/$ROLE_OPTION_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_role_option_response)
print_result "PUT $API_PREFIX/role-options/$ROLE_OPTION_ID" "$status_code" "$response_content"

# Test 19: Get Project Notes List (Admin only)
echo -e "${YELLOW}19. Testing Get Project Notes List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/project_notes_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/project-notes")
status_code=${response: -3}
response_content=$(cat /tmp/project_notes_response)
print_result "GET $API_PREFIX/project-notes" "$status_code" "$response_content"

# Test 20: Create Project Note (Admin only)
echo -e "${YELLOW}20. Testing Create Project Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_project_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "project_id": '$PROJECT_ID',
        "title": "Test Project Note",
        "content": "This is a test note for the project",
        "note_type": "general"
    }' \
    -X POST "$BASE_URL$API_PREFIX/project-notes")
status_code=${response: -3}
response_content=$(cat /tmp/create_project_note_response)
print_result "POST $API_PREFIX/project-notes" "$status_code" "$response_content"

# Extract project note ID from response for subsequent tests
PROJECT_NOTE_ID=$(cat /tmp/create_project_note_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$PROJECT_NOTE_ID" ]]; then
    PROJECT_NOTE_ID=1  # Fallback
fi

# Test 21: Get Project Note by ID (Admin only)
echo -e "${YELLOW}21. Testing Get Project Note by ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/get_project_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/project-notes/$PROJECT_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/get_project_note_response)
print_result "GET $API_PREFIX/project-notes/$PROJECT_NOTE_ID" "$status_code" "$response_content"

# Test 22: Update Project Note (Admin only)
echo -e "${YELLOW}22. Testing Update Project Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_project_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "project_id": '$PROJECT_ID',
        "title": "Updated Test Project Note",
        "content": "This is an updated test note for the project",
        "note_type": "general"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/project-notes/$PROJECT_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_project_note_response)
print_result "PUT $API_PREFIX/project-notes/$PROJECT_NOTE_ID" "$status_code" "$response_content"

# Test 23: Get Role Notes List (Admin only)
echo -e "${YELLOW}23. Testing Get Role Notes List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/role_notes_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/role-notes")
status_code=${response: -3}
response_content=$(cat /tmp/role_notes_response)
print_result "GET $API_PREFIX/role-notes" "$status_code" "$response_content"

# Test 24: Create Role Note (Admin only)
echo -e "${YELLOW}24. Testing Create Role Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_role_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "project_id": '$PROJECT_ID',
        "role_id": '$ROLE_ID',
        "title": "Test Role Note",
        "description": "This is a test note for the role"
    }' \
    -X POST "$BASE_URL$API_PREFIX/role-notes")
status_code=${response: -3}
response_content=$(cat /tmp/create_role_note_response)
print_result "POST $API_PREFIX/role-notes" "$status_code" "$response_content"

# Extract role note ID from response for subsequent tests
ROLE_NOTE_ID=$(cat /tmp/create_role_note_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$ROLE_NOTE_ID" ]]; then
    ROLE_NOTE_ID=1  # Fallback
fi

# Test 25: Get Role Note by ID (Admin only)
echo -e "${YELLOW}25. Testing Get Role Note by ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/get_role_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/role-notes/$ROLE_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/get_role_note_response)
print_result "GET $API_PREFIX/role-notes/$ROLE_NOTE_ID" "$status_code" "$response_content"

# Test 26: Update Role Note (Admin only)
echo -e "${YELLOW}26. Testing Update Role Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_role_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "role_id": '$ROLE_ID',
        "title": "Updated Test Role Note",
        "content": "This is an updated test note for the role",
        "note_type": "general"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/role-notes/$ROLE_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_role_note_response)
print_result "PUT $API_PREFIX/role-notes/$ROLE_NOTE_ID" "$status_code" "$response_content"

# Test 27: Get Project Favorites List (Admin only)
echo -e "${YELLOW}27. Testing Get Project Favorites List${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/project_favorites_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/project-favorites")
status_code=${response: -3}
response_content=$(cat /tmp/project_favorites_response)
print_result "GET $API_PREFIX/project-favorites" "$status_code" "$response_content"

# Test 28: Create Project Favorite (Admin only)
echo -e "${YELLOW}28. Testing Create Project Favorite${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_project_favorite_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "favoritable_type": "Project",
        "favoritable_id": '$PROJECT_ID'
    }' \
    -X POST "$BASE_URL$API_PREFIX/project-favorites")
status_code=${response: -3}
response_content=$(cat /tmp/create_project_favorite_response)
print_result "POST $API_PREFIX/project-favorites" "$status_code" "$response_content"

# Test 28b: Create Role Favorite (Admin only)
echo -e "${YELLOW}28b. Testing Create Role Favorite${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/create_role_favorite_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "favoritable_type": "Role",
        "favoritable_id": '$ROLE_ID'
    }' \
    -X POST "$BASE_URL$API_PREFIX/project-favorites")
status_code=${response: -3}
response_content=$(cat /tmp/create_role_favorite_response)
print_result "POST $API_PREFIX/project-favorites (Role)" "$status_code" "$response_content"

# Extract project favorite ID from response for subsequent tests
PROJECT_FAVORITE_ID=$(cat /tmp/create_project_favorite_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [[ -z "$PROJECT_FAVORITE_ID" ]]; then
    PROJECT_FAVORITE_ID=1  # Fallback
fi

# Test 29: Get Project Favorite by ID (Admin only)
echo -e "${YELLOW}29. Testing Get Project Favorite by ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/get_project_favorite_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/project-favorites/$PROJECT_FAVORITE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/get_project_favorite_response)
print_result "GET $API_PREFIX/project-favorites/$PROJECT_FAVORITE_ID" "$status_code" "$response_content"

# Test 30: Get Fact Sheets by Project ID (Admin only)
echo -e "${YELLOW}30. Testing Get Fact Sheets by Project ID${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/fact_sheets_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/fact-sheets/$PROJECT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/fact_sheets_response)
print_result "GET $API_PREFIX/fact-sheets/$PROJECT_ID" "$status_code" "$response_content"

# Test 31: Update Fact Sheets (Admin only)
echo -e "${YELLOW}31. Testing Update Fact Sheets${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/update_fact_sheets_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "status": "pending"
    }' \
    -X PUT "$BASE_URL$API_PREFIX/fact-sheets/$PROJECT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/update_fact_sheets_response)
print_result "PUT $API_PREFIX/fact-sheets/$PROJECT_ID" "$status_code" "$response_content"

# Test 32: Approve Fact Sheets (Admin only)
echo -e "${YELLOW}32. Testing Approve Fact Sheets${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/approve_fact_sheets_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X PUT "$BASE_URL$API_PREFIX/fact-sheets/$PROJECT_ID/approve")
status_code=${response: -3}
response_content=$(cat /tmp/approve_fact_sheets_response)
print_result "PUT $API_PREFIX/fact-sheets/$PROJECT_ID/approve" "$status_code" "$response_content"

# Test 33: Delete Project Favorite (Admin only)
echo -e "${YELLOW}33. Testing Delete Project Favorite${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/delete_project_favorite_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X DELETE "$BASE_URL$API_PREFIX/project-favorites/$PROJECT_FAVORITE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/delete_project_favorite_response)
print_result "DELETE $API_PREFIX/project-favorites/$PROJECT_FAVORITE_ID" "$status_code" "$response_content"

# Test 34: Delete Role Note (Admin only)
echo -e "${YELLOW}34. Testing Delete Role Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/delete_role_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X DELETE "$BASE_URL$API_PREFIX/role-notes/$ROLE_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/delete_role_note_response)
print_result "DELETE $API_PREFIX/role-notes/$ROLE_NOTE_ID" "$status_code" "$response_content"

# Test 35: Delete Project Note (Admin only)
echo -e "${YELLOW}35. Testing Delete Project Note${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/delete_project_note_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X DELETE "$BASE_URL$API_PREFIX/project-notes/$PROJECT_NOTE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/delete_project_note_response)
print_result "DELETE $API_PREFIX/project-notes/$PROJECT_NOTE_ID" "$status_code" "$response_content"

# Test 36: Delete Role (Admin only)
echo -e "${YELLOW}36. Testing Delete Role${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/delete_role_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X DELETE "$BASE_URL$API_PREFIX/roles/$ROLE_ID")
status_code=${response: -3}
response_content=$(cat /tmp/delete_role_response)
print_result "DELETE $API_PREFIX/roles/$ROLE_ID" "$status_code" "$response_content"

# Test 37: Delete Project (Admin only)
echo -e "${YELLOW}37. Testing Delete Project${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/delete_project_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -X DELETE "$BASE_URL$API_PREFIX/projects/$PROJECT_ID")
status_code=${response: -3}
response_content=$(cat /tmp/delete_project_response)
print_result "DELETE $API_PREFIX/projects/$PROJECT_ID" "$status_code" "$response_content"

# Test 38: Test My Project endpoint (should fail with admin token - requires PROJECT role)
echo -e "${YELLOW}38. Testing My Project (should fail with admin token)${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/my_project_response \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$BASE_URL$API_PREFIX/my-project")
status_code=${response: -3}
response_content=$(cat /tmp/my_project_response)
print_result "GET $API_PREFIX/my-project" "$status_code" "$response_content"

# Test 39: Test without authentication (should fail)
echo -e "${YELLOW}39. Testing Get Users without Authentication${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/no_auth_response \
    "$BASE_URL$API_PREFIX/users")
status_code=${response: -3}
response_content=$(cat /tmp/no_auth_response)
print_result "GET $API_PREFIX/users (no auth)" "$status_code" "$response_content"

# Test 40: Test with invalid token (should fail)
echo -e "${YELLOW}40. Testing Get Users with Invalid Token${NC}"
response=$(curl -s -w "%{http_code}" -o /tmp/invalid_auth_response \
    -H "Authorization: Bearer invalid_token_here" \
    "$BASE_URL$API_PREFIX/users")
status_code=${response: -3}
response_content=$(cat /tmp/invalid_auth_response)
print_result "GET $API_PREFIX/users (invalid auth)" "$status_code" "$response_content"

# Clean up temporary files
rm -f /tmp/*_response

echo -e "${BLUE}=================================="
echo -e "${BLUE}🎉 API Testing Complete!${NC}"
echo -e "${BLUE}=================================="
echo -e "${GREEN}✅ Green: Success (200-299)${NC}"
echo -e "${YELLOW}⚠️  Yellow: Client Error (400-499)${NC}"
echo -e "${RED}❌ Red: Server Error (500+)${NC}" 