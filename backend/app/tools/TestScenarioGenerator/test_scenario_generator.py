import json
import os
import argparse
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from llm_provider import LLMProviderFactory
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test Scenario Generator MCP Service')
parser.add_argument('--port', type=int, default=8000, help='Port number to run the service on')
args = parser.parse_args()

# Initialize MCP service with the specified port
mcp = FastMCP("TestScenarioGenerator", port=args.port)

class APIPathInput(BaseModel):
    api_json_path: str = Field(..., description="Path to the API JSON file")
    api_path: str = Field(..., description="API path to generate test scenarios for")
    llm_provider: Optional[str] = Field(None, description="LLM provider to use (google, openai, etc.)")
    application_id: Optional[str] = Field(None, description="Application ID for Metersphere integration")
    interface_id: Optional[str] = Field(None, description="Interface ID for Metersphere integration")

class ScenarioInput(BaseModel):
    scenario: Dict[str, Any] = Field(..., description="Test scenario to convert to Metersphere format")
    application_id: Optional[str] = Field(None, description="Application ID for Metersphere integration") 
    interface_id: Optional[str] = Field(None, description="Interface ID for Metersphere integration")

class DescriptionInput(BaseModel):
    api_description: str = Field(..., description="API description text")
    api_path: str = Field(..., description="API path to generate test scenarios for")
    llm_provider: Optional[str] = Field(None, description="LLM provider to use (google, openai, etc.)")
    application_id: Optional[str] = Field(None, description="Application ID for Metersphere integration")
    interface_id: Optional[str] = Field(None, description="Interface ID for Metersphere integration")

class GenerateScriptInput(BaseModel):
    scenarios: Dict[str, List[Dict[str, Any]]] = Field(..., description="Test scenarios to generate script for")
    api_path: str = Field(..., description="API path the scenarios are for")
    output_file: Optional[str] = Field(None, description="File to save the generated script to")

@mcp.tool()
async def generate_test_scenarios(api_json_path: str, api_path: str, application_id: Optional[str] = None, 
                               interface_id: Optional[str] = None, llm_provider: Optional[str] = None) -> Dict:
    """
    Generate test scenarios for a specific API path using the provided API JSON file.
    Uses LLM to analyze the API structure and generate comprehensive test scenarios.
    
    Args:
        api_json_path: Path to the API JSON file 
        api_path: API path to generate test scenarios for
        application_id: Optional application ID for Metersphere integration
        interface_id: Optional interface ID for Metersphere integration
        llm_provider: Optional LLM provider to use (default: uses DEFAULT_LLM_PROVIDER from env)
        
    Returns:
        Dictionary containing test scenarios
    """
    logger.info(f"Generating test scenarios for {api_path} using {api_json_path}")
    
    # Load API JSON
    if not os.path.exists(api_json_path):
        error_msg = f"API JSON file not found: {api_json_path}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(api_json_path, 'r', encoding='utf-8') as f:
            api_json = json.load(f)
    except Exception as e:
        error_msg = f"Failed to load API JSON file: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Get the LLM provider
    provider_name = llm_provider or os.getenv("DEFAULT_LLM_PROVIDER", "google")
    llm_provider_instance = LLMProviderFactory.get_provider(provider_name)
    
    if not llm_provider_instance:
        error_msg = f"Failed to initialize LLM provider: {provider_name}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Generate test scenarios using LLM
    try:
        # Find the API endpoint in the JSON
        endpoint_found = False
        endpoint_data = None
        
        # Handle different API JSON formats
        if isinstance(api_json, list):
            # List of endpoints format
            for endpoint in api_json:
                if endpoint.get("path") == api_path:
                    endpoint_found = True
                    endpoint_data = endpoint
                    break
        elif isinstance(api_json, dict):
            # OpenAPI/Swagger format
            if "paths" in api_json:
                if api_path in api_json["paths"]:
                    endpoint_found = True
                    endpoint_data = api_json["paths"][api_path]
        
        if not endpoint_found:
            error_msg = f"API path {api_path} not found in the API JSON file"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Prepare the prompt for the LLM
        prompt = f"""
        Generate comprehensive test scenarios for the API endpoint: {api_path}
        
        API Details:
        {json.dumps(endpoint_data, indent=2)}
        
        For each test scenario, provide:
        1. A descriptive name
        2. A detailed description of the test case
        3. The request data (including headers, path parameters, query parameters, and body as applicable)
        4. The expected response (status code and body)
        
        Include scenarios for:
        - Normal operation with valid input
        - Edge cases (empty arrays, null values, etc.)
        - Error cases (invalid input, missing required fields, etc.)
        - Authorization/authentication issues (if applicable)
        
        Format the output as a JSON object with a "scenarios" key containing an array of scenario objects, each with:
        - name: The name of the scenario
        - description: A description of what the scenario tests
        - request: The request data
        - expected_response: The expected response
        """
        
        # Call the LLM to generate scenarios
        scenarios_text = await llm_provider_instance.generate_text(prompt)
        
        # Try to parse the response as JSON
        try:
            # If the response is already wrapped in a dict with 'scenarios'
            if scenarios_text.strip().startswith('{') and 'scenarios' in json.loads(scenarios_text):
                scenarios = json.loads(scenarios_text)
            else:
                # Extract JSON if it's wrapped in explanatory text
                json_start = scenarios_text.find('{')
                json_end = scenarios_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = scenarios_text[json_start:json_end]
                    scenarios = json.loads(json_str)
                    if 'scenarios' not in scenarios:
                        scenarios = {"scenarios": [scenarios]}
                else:
                    # If no JSON found, create a structured format
                    scenarios = {
                        "scenarios": [{
                            "name": "Generated Scenario",
                            "description": "Generated test scenario from LLM response",
                            "request": {},
                            "expected_response": {}
                        }]
                    }
                    logger.warning("Could not parse LLM response as JSON, using default structure")
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return the raw text if parsing fails
            return {
                "api_path": api_path,
                "method": "post",  # Assuming method is post for the delete endpoint
                "scenarios": [{
                    "name": "Generated Scenario",
                    "description": "Generated test scenario from LLM response",
                    "request": {},
                    "expected_response": {}
                }],
                "raw_response": scenarios_text
            }
        
        # Add metadata
        result = {
            "api_path": api_path,
            "method": "post",  # Assuming method is post for the delete endpoint
            "scenarios": scenarios.get("scenarios", [])
        }
        
        if application_id:
            result["application_id"] = application_id
        if interface_id:
            result["interface_id"] = interface_id
            
        return result
    except Exception as e:
        error_msg = f"Error generating test scenarios: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
async def generate_test_scenarios_rule_based(api_json_path: str, api_path: str, application_id: Optional[str] = None, 
                                          interface_id: Optional[str] = None) -> Dict:
    """
    Generate test scenarios for a specific API path using rule-based approach.
    This is a fallback when LLM generation is not available or fails.
    
    Args:
        api_json_path: Path to the API JSON file 
        api_path: API path to generate test scenarios for
        application_id: Optional application ID for Metersphere integration
        interface_id: Optional interface ID for Metersphere integration
        
    Returns:
        Dictionary containing test scenarios
    """
    logger.info(f"Generating rule-based test scenarios for {api_path} using {api_json_path}")
    
    # Load API JSON
    if not os.path.exists(api_json_path):
        error_msg = f"API JSON file not found: {api_json_path}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    try:
        with open(api_json_path, 'r', encoding='utf-8') as f:
            api_json = json.load(f)
    except Exception as e:
        error_msg = f"Failed to load API JSON file: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
        
    # Logic to generate scenarios based on rules
    # Here's a simplified implementation for /system/user/delete endpoint
    if api_path == "/system/user/delete":
        scenarios = [
            {
                "name": "Normal operation: Delete multiple users",
                "description": "Test deleting multiple users with valid user IDs",
                "request": {
                    "userIds": ["1", "2", "3"]
                },
                "expected_response": {
                    "status": 200,
                    "message": "Operation successful"
                }
            },
            {
                "name": "Normal operation: Delete single user",
                "description": "Test deleting a single user with valid user ID",
                "request": {
                    "userIds": ["1"]
                },
                "expected_response": {
                    "status": 200,
                    "message": "Operation successful"
                }
            },
            {
                "name": "Error operation: Delete non-existent users",
                "description": "Test deleting non-existent user IDs",
                "request": {
                    "userIds": ["999", "1000"]
                },
                "expected_response": {
                    "status": 404,
                    "message": "User does not exist"
                }
            },
            {
                "name": "Error operation: Empty user ID array",
                "description": "Test deletion with an empty array",
                "request": {
                    "userIds": []
                },
                "expected_response": {
                    "status": 400,
                    "message": "User ID list cannot be empty"
                }
            },
            {
                "name": "Error operation: Missing request body",
                "description": "Test with no request body provided",
                "request": {},
                "expected_response": {
                    "status": 400,
                    "message": "Invalid request format"
                }
            },
            {
                "name": "Error operation: Invalid request format",
                "description": "Test with non-JSON request format",
                "request": "userIds=1,2,3",  # Non-JSON format
                "expected_response": {
                    "status": 400,
                    "message": "Invalid request format"
                }
            },
            {
                "name": "Error operation: Insufficient permissions",
                "description": "Test when user doesn't have deletion permissions",
                "request": {
                    "userIds": ["1", "2"],
                    "_auth": "limited_user"  # Special marker for limited permission user
                },
                "expected_response": {
                    "status": 403,
                    "message": "Insufficient permissions"
                }
            }
        ]
    else:
        # Generic rule-based scenarios for other endpoints
        scenarios = [
            {
                "name": "Normal operation test",
                "description": f"Test normal operation of {api_path}",
                "request": {},
                "expected_response": {
                    "status": 200,
                    "message": "Operation successful"
                }
            },
            {
                "name": "Missing parameter test",
                "description": f"Test {api_path} with missing required parameters",
                "request": {},
                "expected_response": {
                    "status": 400,
                    "message": "Invalid request parameters"
                }
            },
            {
                "name": "Insufficient permissions test",
                "description": f"Test {api_path} with insufficient permissions",
                "request": {
                    "_auth": "limited_user"
                },
                "expected_response": {
                    "status": 403,
                    "message": "Insufficient permissions"
                }
            }
        ]
    
    result = {
        "api_path": api_path,
        "method": "post",  # Assuming method is post for the delete endpoint
        "scenarios": scenarios
    }
    
    if application_id:
        result["application_id"] = application_id
    if interface_id:
        result["interface_id"] = interface_id
        
    return result

@mcp.tool()
async def generate_test_scenarios_from_description(api_description: str, api_path: str, 
                                                application_id: Optional[str] = None,
                                                interface_id: Optional[str] = None,
                                                llm_provider: Optional[str] = None) -> Dict:
    """
    Generate test scenarios for a specific API path using the provided API description text.
    Uses LLM to analyze the API description and generate comprehensive test scenarios.
    
    Args:
        api_description: API description text
        api_path: API path to generate test scenarios for
        application_id: Optional application ID for Metersphere integration
        interface_id: Optional interface ID for Metersphere integration
        llm_provider: Optional LLM provider to use (default: uses DEFAULT_LLM_PROVIDER from env)
        
    Returns:
        Dictionary containing test scenarios
    """
    logger.info(f"Generating test scenarios for {api_path} from description")
    
    # Get the LLM provider
    provider_name = llm_provider or os.getenv("DEFAULT_LLM_PROVIDER", "google")
    llm_provider_instance = LLMProviderFactory.get_provider(provider_name)
    
    if not llm_provider_instance:
        error_msg = f"Failed to initialize LLM provider: {provider_name}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Generate test scenarios using LLM
    try:
        # Prepare the prompt for the LLM
        prompt = f"""
        Generate comprehensive test scenarios for the API endpoint: {api_path}
        
        API Description:
        {api_description}
        
        For each test scenario, provide:
        1. A descriptive name
        2. A detailed description of the test case
        3. The request data (including headers, path parameters, query parameters, and body as applicable)
        4. The expected response (status code and body)
        
        Include scenarios for:
        - Normal operation with valid input
        - Edge cases (empty arrays, null values, etc.)
        - Error cases (invalid input, missing required fields, etc.)
        - Authorization/authentication issues (if applicable)
        
        Format the output as a JSON object with a "scenarios" key containing an array of scenario objects, each with:
        - name: The name of the scenario
        - description: A description of what the scenario tests
        - request: The request data
        - expected_response: The expected response
        """
        
        # Call the LLM to generate scenarios
        scenarios_text = await llm_provider_instance.generate_text(prompt)
        
        # Try to parse the response as JSON
        try:
            # If the response is already wrapped in a dict with 'scenarios'
            if scenarios_text.strip().startswith('{') and 'scenarios' in json.loads(scenarios_text):
                scenarios = json.loads(scenarios_text)
            else:
                # Extract JSON if it's wrapped in explanatory text
                json_start = scenarios_text.find('{')
                json_end = scenarios_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = scenarios_text[json_start:json_end]
                    scenarios = json.loads(json_str)
                    if 'scenarios' not in scenarios:
                        scenarios = {"scenarios": [scenarios]}
                else:
                    # If no JSON found, create a structured format
                    scenarios = {
                        "scenarios": [{
                            "name": "Generated Scenario",
                            "description": "Generated test scenario from LLM response",
                            "request": {},
                            "expected_response": {}
                        }]
                    }
                    logger.warning("Could not parse LLM response as JSON, using default structure")
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return the raw text if parsing fails
            return {
                "api_path": api_path,
                "method": "post",  # Assuming method is post for this endpoint
                "scenarios": [{
                    "name": "Generated Scenario",
                    "description": "Generated test scenario from LLM response",
                    "request": {},
                    "expected_response": {}
                }],
                "raw_response": scenarios_text
            }
        
        # Add metadata
        result = {
            "api_path": api_path,
            "method": "post",  # Assuming method is post for this endpoint
            "scenarios": scenarios.get("scenarios", [])
        }
        
        if application_id:
            result["application_id"] = application_id
        if interface_id:
            result["interface_id"] = interface_id
            
        return result
    except Exception as e:
        error_msg = f"Error generating test scenarios: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
async def get_metersphere_test_case_json(scenario: Dict[str, Any], application_id: Optional[str] = None,
                                        interface_id: Optional[str] = None) -> Dict:
    """
    Convert a test scenario to Metersphere test case JSON format.
    
    Args:
        scenario: Test scenario to convert
        application_id: Application ID for Metersphere integration
        interface_id: Interface ID for Metersphere integration
        
    Returns:
        Dictionary containing Metersphere test case JSON
    """
    logger.info(f"Converting scenario to Metersphere format: {scenario.get('name', 'Unnamed scenario')}")
    
    # Check if scenario has required fields
    if not all(k in scenario for k in ['name', 'description', 'request', 'expected_response']):
        error_msg = f"Scenario missing required fields: {scenario}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    try:
        # Convert scenario to Metersphere format
        ms_test_case = {
            "name": scenario.get('name', 'Unnamed Test Case'),
            "priority": "P2",
            "type": "API",
            "method": "POST",  # Assuming method is POST for this endpoint
            "path": scenario.get('request', {}).get('path', ''),
            "tags": [],
            "status": "Prepared",
            "description": scenario.get('description', ''),
            "request": {
                "headers": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "type": "JSON",
                    "raw": json.dumps(scenario.get('request', {}), ensure_ascii=False)
                }
            },
            "assertions": [
                {
                    "type": "Response Status Code",
                    "condition": "equals",
                    "value": str(scenario.get('expected_response', {}).get('status', 200))
                }
            ]
        }
        
        # Add message assertion if present
        if 'message' in scenario.get('expected_response', {}):
            ms_test_case['assertions'].append({
                "type": "Response Body",
                "condition": "contains",
                "value": scenario['expected_response']['message']
            })
        
        # Add application and interface IDs if provided
        if application_id:
            ms_test_case['application_id'] = application_id
        if interface_id:
            ms_test_case['interface_id'] = interface_id
            
        return ms_test_case
    except Exception as e:
        error_msg = f"Error creating Metersphere test case: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
async def generate_test_script(scenarios: Dict[str, List[Dict[str, Any]]], api_path: str, output_file: Optional[str] = None) -> str:
    """
    Generate Python test script from test scenarios.
    
    Args:
        scenarios: Dictionary containing test scenarios (with 'scenarios' key)
        api_path: API path the scenarios are for
        output_file: Optional file path to save the generated script
        
    Returns:
        Generated test script as a string
    """
    logger.info(f"Generating test script for {api_path} with {len(scenarios.get('scenarios', []))} scenarios")
    
    script_content = f"""
import pytest
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL, get from environment variables or use default
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')

# Test case class - {api_path} endpoint
class Test{api_path.replace('/', '_').title()}:
    # Set request headers
    headers = {{
        'Content-Type': 'application/json',
        'Authorization': os.getenv('API_TOKEN', '')
    }}
    
    # API endpoint URL
    api_url = f"{{BASE_URL}}{api_path}"
    
"""
    
    # Generate test method for each scenario
    for i, scenario in enumerate(scenarios.get("scenarios", [])):
        # Clean method name (remove non-ASCII and special characters)
        method_name = f"test_scenario_{i+1}"
        if 'name' in scenario:
            # Extract keywords from name as method name
            clean_name = ''.join(c if c.isalnum() else '_' for c in scenario['name'])
            clean_name = ''.join(c for c in clean_name if c.isascii()).strip('_')
            if clean_name:
                method_name = f"test_{clean_name}"
        
        script_content += f"""    def {method_name}(self):
        \"\"\"
        {scenario.get('name', f'Test scenario {i+1}')}
        
        {scenario.get('description', 'No description')}
        \"\"\"
        # Prepare request data
        request_data = {json.dumps(scenario.get('request', {}), ensure_ascii=False, indent=8)}
        
        # Send request
        response = requests.post(self.api_url, headers=self.headers, json=request_data)
        
        # Expected response
        expected = {json.dumps(scenario.get('expected_response', {}), ensure_ascii=False, indent=8)}
        
        # Assert status code
        assert response.status_code == expected.get('status', 200), f"Status code mismatch: {{response.status_code}} != {{expected.get('status', 200)}}"
        
        # Get response data
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text
            
        # Assert response content (simple example, actual implementations may need more complex comparisons)
        if 'message' in expected:
            assert 'message' in response_data, "Response missing message field"
            assert expected['message'] in response_data['message'], f"Message mismatch: {{response_data['message']}} should contain {{expected['message']}}"
        
        # Other custom assertions can be added as needed
        
"""
    
    script_content += """
if __name__ == "__main__":
    pytest.main(["-v"])
"""
    
    # If output file specified, save the script
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        logger.info(f"Test script saved to: {output_file}")
    
    return script_content

if __name__ == "__main__":
    mcp.run() 