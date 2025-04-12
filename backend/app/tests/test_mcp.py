import pytest
import asyncio
import os
from dotenv import load_dotenv
from app.mcp.service import initialize_mcp, cleanup_mcp, get_available_tools, handle_mcp_complete
from app.schemas.message import ChatRequest, MessageBase
from app.core.config import Settings

# Load environment variables from TestScenarioGenerator's .env file
env_path = os.path.join(os.path.dirname(__file__), "..", "tools", "TestScenarioGenerator", ".env")
load_dotenv(env_path)

@pytest.mark.asyncio
async def test_scenario_generation():
    """Test scenario generation tool with real LLM service"""
    try:
        # Initialize MCP with real LLM service
        settings = Settings()  # This will use environment variables
        await initialize_mcp(settings)
        
        # Create a chat request for test scenario generation
        request = ChatRequest(
            conversation_id="test-1",
            messages=[
                MessageBase(
                    role="user",
                    content="Generate a test scenario for a login function that validates username and password"
                )
            ]
        )
        
        # Get response from real LLM service
        response = await handle_mcp_complete(request)
        print("\nTest Scenario Generation Response:")
        print(response)
        
        # Verify response
        assert response is not None, "No response received"
        assert "messages" in response, "No messages in response"
        assert len(response["messages"]) > 0, "Empty response messages"
        
        # Print the response content
        content = response["messages"][-1]["content"]
        print(f"\nGenerated Test Scenario:\n{content}")
        
    finally:
        # Clean up
        await cleanup_mcp()

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_scenario_generation()) 