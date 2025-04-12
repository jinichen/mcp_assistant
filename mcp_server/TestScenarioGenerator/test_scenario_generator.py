import json
import os
import sys
import glob
import requests
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from mcp.server.fastmcp import FastMCP
from llm_provider import get_llm_provider

# Load environment variables from the current directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root directory to sys.path to resolve import issues
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Set uploads directory
UPLOADS_DIR = os.path.join(backend_dir, os.getenv('UPLOAD_DIR', 'uploads/documents'))

# Set API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")

# Create MCP instance
mcp = FastMCP("TestScenarioGenerator")

def get_llm_provider_instance():
    """Get the LLM provider instance"""
    try:
        provider = get_llm_provider()
        logger.info(f"Using LLM provider: {provider.provider}")
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {str(e)}")
        raise

def get_api_token():
    """
    Get the API token for requests.
    
    Attempts to get the token from various possible sources:
    - API_TOKEN environment variable
    - .env file
    - Session file
    
    Returns:
        str: API token or empty string
    """
    # First check environment variable
    token = os.getenv("API_TOKEN", "")
    if token:
        return token
    
    # Try loading from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("API_TOKEN", "")
        if token:
            return token
    except ImportError:
        pass
    
    # Try finding session file
    try:
        session_file = os.path.join(os.path.expanduser("~"), ".ia_session")
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                return session_data.get("token", "")
    except Exception as e:
        logger.warning(f"Failed to read session file: {str(e)}")
    
    return ""

def find_uploaded_file(filename):
    """
    Get the actual path of the uploaded file, prioritizing API mapping relationships
    
    Args:
        filename: Original filename or file path
        
    Returns:
        Complete file path if found, or None
    """
    # If a complete path is provided and the file exists, return it directly
    if os.path.exists(filename):
        return filename
    
    # Extract filename from path
    base_filename = os.path.basename(filename)
    
    # 1. First try to get the file path through API
    try:
        # Get API token
        token = get_api_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Call files API to get file list
        response = requests.get(
            f"{API_BASE_URL}/api/v1/files", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            files_data = response.json()
            
            # Check if there's a data field
            if isinstance(files_data, dict) and "data" in files_data:
                files = files_data["data"]
            else:
                files = files_data  # Assuming it's directly returning file list
            
            logger.info(f"Retrieved {len(files)} files from API")
            
            # 1.1 Find matching file
            for file in files:
                # File object structure might be: {"id": "...", "filename": "...", "filepath": "...", "original_filename": "..."}
                # Adjust based on actual API response structure
                
                # Check original filename match
                original_name = file.get("original_filename", "") or file.get("originalFilename", "")
                if original_name and (original_name == base_filename or base_filename in original_name):
                    # Get actual storage path
                    file_path = file.get("filepath", "") or file.get("filePath", "")
                    if file_path and os.path.exists(file_path):
                        logger.info(f"Found file via API original filename match: {file_path}")
                        return file_path
                
                # Check current filename match
                current_name = file.get("filename", "") or file.get("fileName", "")
                if current_name and (current_name == base_filename or base_filename in current_name):
                    file_path = file.get("filepath", "") or file.get("filePath", "")
                    if file_path and os.path.exists(file_path):
                        logger.info(f"Found file via API current filename match: {file_path}")
                        return file_path
                
                # Try finding by ID
                file_id = file.get("id", "")
                filename_without_ext = os.path.splitext(base_filename)[0]
                if file_id and filename_without_ext and filename_without_ext in file_id:
                    file_path = file.get("filepath", "") or file.get("filePath", "")
                    if file_path and os.path.exists(file_path):
                        logger.info(f"Found file via API ID match: {file_path}")
                        return file_path
    except requests.RequestException as e:
        logger.warning(f"API request failed: {str(e)}")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse API response: {str(e)}")
    except Exception as e:
        logger.warning(f"Failed to get file mapping from API: {str(e)}")
    
    # 2. If API query fails, fall back to file system search
    logger.info("Falling back to file system search")
    
    # 2.1 Check if main uploads directory exists
    if not os.path.exists(UPLOADS_DIR):
        logger.warning(f"Uploads directory {UPLOADS_DIR} does not exist")
        return None
    
    # 2.2 First check main uploads directory for matching
    direct_match = os.path.join(UPLOADS_DIR, base_filename)
    if os.path.exists(direct_match):
        logger.info(f"Found direct match in main uploads directory: {direct_match}")
        return direct_match
    
    # 2.3 Find all user ID subdirectories
    user_dirs = []
    for item in os.listdir(UPLOADS_DIR):
        item_path = os.path.join(UPLOADS_DIR, item)
        if os.path.isdir(item_path):
            user_dirs.append(item_path)
    
    logger.info(f"Found {len(user_dirs)} user directories to search")
    
    # 2.4 Search for file in each user directory
    for user_dir in user_dirs:
        # 2.4.1 Check exact match
        user_file_path = os.path.join(user_dir, base_filename)
        if os.path.exists(user_file_path):
            logger.info(f"Found exact match in user directory: {user_file_path}")
            return user_file_path
        
        # 2.4.2 Find all JSON files
        all_json_files = glob.glob(os.path.join(user_dir, "*.json"))
        
        # 2.4.3 Check if file name contains original file name
        for file_path in all_json_files:
            file_name = os.path.basename(file_path)
            # Check if file name contains original file name (without extension)
            if base_filename.split('.')[0] in file_name:
                logger.info(f"Found partial match in user directory: {file_path}")
                return file_path
        
        # 2.4.4 If none found but there's a JSON file, use the most recent
        if all_json_files:
            newest_file = max(all_json_files, key=os.path.getctime)
            logger.info(f"Using most recent JSON file in user directory: {newest_file}")
            return newest_file
    
    # 2.5 If user directories don't find it, try searching all JSON files in main uploads directory
    all_json_files = glob.glob(os.path.join(UPLOADS_DIR, "*.json"))
    
    # 2.5.1 Check if file name contains original file name
    for file_path in all_json_files:
        file_name = os.path.basename(file_path)
        if base_filename.split('.')[0] in file_name:
            logger.info(f"Found partial match in main directory: {file_path}")
            return file_path
    
    # 2.5.2 If none found but there's a JSON file, use the most recent
    if all_json_files:
        newest_file = max(all_json_files, key=os.path.getctime)
        logger.info(f"Using most recent JSON file in main directory: {newest_file}")
        return newest_file
    
    logger.warning(f"Could not find file {filename} in any location")
    return None

@mcp.tool()
async def generate_test_scenarios(query: str) -> str:
    """
    Generate test scenarios based on the provided query.
    
    Args:
        query: A description of the functionality to generate test scenarios for
        
    Returns:
        JSON string containing generated test scenarios
    """
    try:
        # Prepare prompt for the LLM
        prompt = f"""
        Generate comprehensive test scenarios for the following functionality:
        {query}
        
        For each test scenario, provide:
        1. A descriptive name
        2. A detailed description of the test case
        3. Test steps with expected results
        
        Format the output as a JSON object with a "test_scenarios" key containing an array of scenario objects.
        """
        
        # Get LLM provider instance
        llm_provider = get_llm_provider_instance()
        
        # Generate scenarios using LLM
        scenarios = await llm_provider.generate_from_prompt(prompt)
        
        # Format the response
        result = {"test_scenarios": scenarios}
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error generating test scenarios: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
async def generate_test_scenarios_from_description(api_description: str, api_path: str, 
                                          application_id: Optional[str] = None,
                                          interface_id: Optional[str] = None,
                                          llm_provider: Optional[str] = None) -> Dict:
    """
    Generate test scenarios for a specific API path using a textual description.
    
    Args:
        api_description: Textual description of the API
        api_path: API path to generate test scenarios for
        application_id: Optional application ID for Metersphere integration
        interface_id: Optional interface ID for Metersphere integration
        llm_provider: Optional LLM provider to use (default: uses DEFAULT_LLM_PROVIDER from env)
        
    Returns:
        Dictionary containing test scenarios
    """
    logger.info(f"Generating test scenarios from description for {api_path}")
    
    try:
        # Prepare prompt for the LLM
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
        
        Format the output as a JSON object with a "scenarios" key containing an array of scenario objects.
        """
        
        # Get LLM provider instance
        llm_provider_instance = get_llm_provider_instance()
        
        # Generate scenarios using LLM
        scenarios = await llm_provider_instance.generate_from_prompt(prompt)
        
        # Add metadata
        result = {
            "api_path": api_path,
            "scenarios": scenarios
        }
        
        if application_id:
            result["application_id"] = application_id
        if interface_id:
            result["interface_id"] = interface_id
            
        return result
    except Exception as e:
        error_msg = f"Error generating test scenarios from description: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def get_metersphere_test_case_json(scenario: Dict[str, Any], application_id: Optional[str] = None,
                                 interface_id: Optional[str] = None) -> Dict:
    """
    Convert a test scenario to Metersphere test case format.
    
    Args:
        scenario: Test scenario to convert
        application_id: Optional application ID for Metersphere integration
        interface_id: Optional interface ID for Metersphere integration
        
    Returns:
        Metersphere formatted test case
    """
    logger.info(f"Converting scenario '{scenario.get('name', 'Unknown')}' to Metersphere format")
    
    try:
        # Default values
        app_id = application_id or os.getenv("METERSPHERE_APP_ID", "default")
        interface_id = interface_id or os.getenv("METERSPHERE_INTERFACE_ID", "default")
        
        # Convert to Metersphere format
        ms_case = {
            "name": scenario.get("name", "Generated Test Case"),
            "priority": "P0",
            "type": "API",
            "method": "POST",  # Default method
            "path": scenario.get("api_path", ""),
            "applicationId": app_id,
            "moduleId": interface_id,
            "tags": ["auto-generated", "API-test"],
            "description": scenario.get("description", ""),
            "steps": [
                {
                    "name": "Request",
                    "description": "API request details",
                    "request": scenario.get("request", {})
                },
                {
                    "name": "Expected Response",
                    "description": "Expected API response",
                    "assertions": [
                        {
                            "type": "STATUS_CODE",
                            "value": str(scenario.get("expected_response", {}).get("status", 200))
                        },
                        {
                            "type": "RESPONSE_BODY",
                            "value": json.dumps(scenario.get("expected_response", {}).get("body", {}))
                        }
                    ]
                }
            ]
        }
        
        return ms_case
    except Exception as e:
        error_msg = f"Error converting to Metersphere format: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def generate_test_script(scenarios: Dict[str, List[Dict[str, Any]]], api_path: str, 
                       output_file: Optional[str] = None) -> str:
    """
    Generate a Python test script from test scenarios.
    
    Args:
        scenarios: Dictionary containing test scenarios 
        api_path: API path the scenarios are for
        output_file: Optional file to save the generated script to
        
    Returns:
        Generated test script as string
    """
    logger.info(f"Generating test script for {api_path}")
    
    try:
        api_scenarios = scenarios.get("scenarios", [])
        
        # Generate script header
        script = """
import unittest
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
API_TOKEN = os.getenv("API_TOKEN", "")

class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup common headers
        cls.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}"
        }
    
"""
        
        # Generate test method for each scenario
        for i, scenario in enumerate(api_scenarios):
            # Clean name for use as method name
            method_name = scenario.get("name", f"test_scenario_{i+1}")
            method_name = "test_" + "".join(c if c.isalnum() else "_" for c in method_name.lower())
            
            # Add method comments
            script += f"    def {method_name}(self):\n"
            script += f'        """{scenario.get("description", "Test scenario")}"""\n'
            
            # Request body
            request_data = scenario.get("request", {})
            script += f"        # Prepare request data\n"
            script += f"        request_data = {json.dumps(request_data, indent=8)}\n\n"
            
            # API call
            script += f"        # Call API\n"
            script += f'        response = requests.post(f"{{API_BASE_URL}}{api_path}", headers=self.headers, json=request_data)\n\n'
            
            # Assertions
            expected_response = scenario.get("expected_response", {})
            expected_status = expected_response.get("status", 200)
            
            script += f"        # Assertions\n"
            script += f"        self.assertEqual({expected_status}, response.status_code)\n"
            
            if "body" in expected_response:
                script += f"        response_data = response.json()\n"
                expected_body = expected_response.get("body", {})
                
                if isinstance(expected_body, dict):
                    for key, value in expected_body.items():
                        script += f"        self.assertIn('{key}', response_data)\n"
                        if isinstance(value, (int, float, bool)):
                            script += f"        self.assertEqual({value}, response_data['{key}'])\n"
                        else:
                            script += f"        self.assertEqual('{value}', response_data['{key}'])\n"
            
            script += "\n"
        
        # Add main section
        script += """
if __name__ == "__main__":
    unittest.main()
"""
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(script)
                logger.info(f"Test script saved to {output_file}")
            except Exception as e:
                logger.error(f"Failed to write test script to file: {str(e)}")
        
        return script
    except Exception as e:
        error_msg = f"Error generating test script: {str(e)}"
        logger.error(error_msg)
        return f"# Error generating test script\n# {error_msg}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 