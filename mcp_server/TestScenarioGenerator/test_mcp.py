import os
import sys
import json
import pytest
from dotenv import load_dotenv

# Add project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from test_scenario_generator import (
    generate_test_scenarios,
    generate_test_scenarios_from_description,
    get_metersphere_test_case_json
)

@pytest.mark.asyncio
async def test_generate_test_scenarios():
    """Test generating test scenarios from a query"""
    query = "Test the login API that accepts username and password"
    result = await generate_test_scenarios(query)
    
    # Parse result as JSON
    scenarios = json.loads(result)
    assert "test_scenarios" in scenarios
    assert len(scenarios["test_scenarios"]) > 0

@pytest.mark.asyncio
async def test_generate_test_scenarios_from_description():
    """Test generating test scenarios from API description"""
    api_description = """
    Login API that accepts:
    - username (string): User's email or username
    - password (string): User's password
    Returns:
    - 200 OK with access token on success
    - 401 Unauthorized on invalid credentials
    - 400 Bad Request on invalid input
    """
    api_path = "/api/v1/auth/login"
    
    result = await generate_test_scenarios_from_description(
        api_description=api_description,
        api_path=api_path
    )
    
    assert "api_path" in result
    assert "scenarios" in result
    assert len(result["scenarios"]) > 0

def test_get_metersphere_test_case_json():
    """Test converting scenario to Metersphere format"""
    scenario = {
        "name": "Test Login Success",
        "description": "Test successful login with valid credentials",
        "api_path": "/api/v1/auth/login",
        "request": {
            "method": "POST",
            "body": {
                "username": "test@example.com",
                "password": "password123"
            }
        },
        "expected_response": {
            "status_code": 200,
            "body": {
                "access_token": "string"
            }
        }
    }
    
    result = get_metersphere_test_case_json(scenario)
    assert "name" in result
    assert "priority" in result
    assert "type" in result
    assert result["type"] == "API"

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 