"""
Test Scenario Generator Tool

A tool that provides API test scenario generation functionality based on API descriptions or JSON specifications.
Can generate test scenarios, test cases, and test scripts for API endpoints.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add current directory to sys.path to ensure local modules can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Add backend directory to sys.path to ensure app package can be imported
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try default locations
except ImportError:
    pass

# Import required tool functions
try:
    from test_scenario_generator import mcp
except ImportError as e:
    logger.error(f"Failed to import MCP: {str(e)}")
    sys.exit(1)

def main():
    """Main entry point for the MCP server"""
    try:
        # Print startup message with configuration info
        logger.info("Starting TestScenarioGenerator Tool")
        logger.info(f"API Base URL: {os.getenv('API_BASE_URL', 'http://localhost:8000')}")
        logger.info(f"Upload Directory: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads', 'documents'))}")
        
        # Start the MCP server
        logger.info("Starting MCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error starting MCP server: {str(e)}")
        sys.exit(1)

# When run as a script, start the StdIO server
if __name__ == "__main__":
    main() 