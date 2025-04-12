#!/usr/bin/env python3
"""
Math expression calculation tool server
Processes mathematical expressions and returns the calculated results
"""
import re
import math
import logging
import traceback
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("math-tool")

# 创建FastMCP实例
mcp = FastMCP("Math")

def extract_math_expression(query: str) -> Optional[str]:
    """
    Extract mathematical expression from query
    
    Args:
        query: User query
        
    Returns:
        Extracted expression or None
    """
    # Try to extract mathematical expressions
    patterns = [
        r'calculate\s*([\d\s\+\-\*\/\^\(\)]+)',
        r'([\d\s\+\-\*\/\^\(\)]+)equals',
        r'([\d\s\+\-\*\/\^\(\)]+)is',
        r'compute\s*([\d\s\+\-\*\/\^\(\)]+)',
        # Chinese patterns
        r'计算\s*([\d\s\+\-\*\/\^\(\)]+)',
        r'([\d\s\+\-\*\/\^\(\)]+)等于多少',
        r'([\d\s\+\-\*\/\^\(\)]+)是多少',
    ]
    
    # Special handling for multiplication expressions
    mult_pattern = r'(\d+)\s*(x|×|times|multiplied by|乘|乘以|乘上|×上)\s*(\d+)'
    mult_match = re.search(mult_pattern, query, re.IGNORECASE)
    if mult_match:
        num1 = mult_match.group(1)
        num2 = mult_match.group(3)  # Group number is 3 because the operator is group 2
        expression = f"{num1} * {num2}"
        logger.info(f"Extracted multiplication expression: {expression}")
        return expression
    
    # Try other patterns
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            expression = match.group(1)
            logger.info(f"Extracted expression: {expression}")
            return expression
            
    # If no expression matched, try to extract math expression directly from query
    expression = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', ' ', query)
    logger.info(f"No clear expression found, after cleaning: {expression}")
    
    # Clean the expression, keeping only numbers and operators
    expression = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', '', expression)
    expression = expression.replace('^', '**')  # Convert ^ to Python's ** operator
    expression = expression.strip()
    
    if not expression:
        return None
    
    return expression

@mcp.tool()
async def calculate(query: str) -> str:
    """
    Calculate the result of a mathematical expression.
    
    Args:
        query: A string containing a mathematical expression or a question with a math problem
        
    Returns:
        The calculation result or an error message
    """
    logger.info(f"Processing math query: {query}")
    
    # Extract expression
    expression = extract_math_expression(query)
    
    logger.info(f"Final expression: {expression}")
    
    if not expression:
        return "Could not extract a valid mathematical expression"
    
    try:
        # Safe evaluation of the expression
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        logger.info(f"Calculation result: {result}")
        
        # Format result
        if isinstance(result, int) or (isinstance(result, float) and result.is_integer()):
            formatted_result = str(int(result))
        else:
            formatted_result = str(round(result, 6)).rstrip('0').rstrip('.')
        
        return f"{expression} = {formatted_result}"
    except Exception as e:
        error_msg = f"Calculation error: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    # 启动MCP服务
    mcp.run(transport="stdio") 