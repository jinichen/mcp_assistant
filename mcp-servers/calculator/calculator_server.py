from fastmcp import FastMCP
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Output logs to standard error, avoiding interference with JSONRPC communication
)
logger = logging.getLogger(__name__)

try:
    # Create MCP service
    logger.info("Initializing calculator MCP service...")
    mcp = FastMCP()

    # Define addition tool - using function name
    @mcp.tool(  
        name="add_numbers",  
        description="Add two numbers together and returns the result"
    )
    def add_numbers(a: float, b: float) -> float:
        """
        Adds two numbers and returns the result.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b
        """
        logger.info(f"Adding {a} + {b}")
        result = a + b
        logger.info(f"Result: {result}")
        return result

    @mcp.tool(
        name="multiply_numbers", 
        description="Multiply two numbers together and returns the result"
    )
    def multiply_numbers(a: float, b: float) -> float:
        """
        Multiplies two numbers and returns the result.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The product of a and b
        """
        logger.info(f"Multiplying {a} * {b}")
        result = a * b
        logger.info(f"Result: {result}")
        return result

    # Start MCP service
    if __name__ == "__main__":
        logger.info("Starting calculator MCP service...")
        mcp.run()
        logger.info("Calculator MCP service stopped")

except Exception as e:
    logger.error(f"Error in calculator server: {e}")
    import traceback
    logger.error(traceback.format_exc())
