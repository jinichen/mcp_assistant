#!/usr/bin/env python3
"""
Math expression calculation tool server
Processes mathematical expressions and returns the calculated results
"""
import sys
import json
import re
import math
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("math-tool")

def process_math_query(query: str) -> str:
    """
    Process math queries, extract mathematical expressions and calculate results
    
    Args:
        query: User query
        
    Returns:
        Calculation result
    """
    logger.info(f"Processing math query: {query}")
    
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
    else:
        # Try other patterns
        expression = None
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                expression = match.group(1)
                logger.info(f"Extracted expression: {expression}")
                break
                
        if not expression:
            # If no expression matched, try to extract math expression directly from query
            expression = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', ' ', query)
            logger.info(f"No clear expression found, after cleaning: {expression}")
    
    # Clean the expression, keeping only numbers and operators
    expression = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', '', expression)
    expression = expression.replace('^', '**')  # Convert ^ to Python's ** operator
    expression = expression.strip()
    
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

def main():
    """
    Main function, reads input from stdin, processes it and writes to stdout
    """
    logger.info("Starting math tool server...")
    
    while True:
        try:
            # Read a line of input
            input_line = sys.stdin.readline()
            if not input_line:
                logger.warning("Received empty input, exiting")
                break
                
            logger.info(f"Received input: {input_line.strip()}")
            
            # Parse JSON input
            try:
                input_json = json.loads(input_line)
                query = input_json.get("query", "")
                
                # Process the query
                result = process_math_query(query)
                
                # Return the result
                response = {"result": result}
                response_json = json.dumps(response)
                logger.info(f"Output result: {response_json}")
                
                sys.stdout.write(response_json + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                error_msg = "Input is not valid JSON format"
                logger.error(error_msg)
                sys.stdout.write(json.dumps({"error": error_msg}) + "\n")
                sys.stdout.flush()
                
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            logger.error(traceback.format_exc())
            try:
                sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
                sys.stdout.flush()
            except:
                pass

if __name__ == "__main__":
    main() 