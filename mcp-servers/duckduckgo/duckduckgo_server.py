#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DuckDuckGo Search MCP Server
Based on LangChain's DuckDuckGo search tool, provides web search functionality
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# MCP imports
from mcp.server.fastmcp import FastMCP

# LangChain tool imports
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import DuckDuckGoSearchResults

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(debug=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create log directory
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_handler = logging.FileHandler(os.path.join(log_dir, f"duckduckgo-{timestamp}.log"))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return log_dir

# Initialize DuckDuckGo search tools
search_tool = DuckDuckGoSearchRun()
search_results_tool = DuckDuckGoSearchResults()

# Create MCP instance
mcp = FastMCP("DuckDuckGo")

@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web for current information about any topic, event, person, or factual question.
    Use this tool whenever you need to find information that might not be in your training data.
    
    Args:
        query: The search query
        
    Returns:
        Summarized search results
    """
    logger.info(f"Performing search: {query}")
    try:
        result = search_tool.invoke(query)
        logger.info(f"Search complete, result length: {len(result) if result else 0}")
        return result
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

@mcp.tool()
async def detailed_web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Get detailed search results from the web including titles, snippets and links.
    Use this when you need multiple sources or detailed information.
    
    Args:
        query: The search query
        num_results: Number of results to return (1-10), defaults to 5
        
    Returns:
        Structured search results list, each result containing title, link and snippet
    """
    logger.info(f"Performing structured search: {query}, result count: {num_results}")
    try:
        # Limit result count to reasonable range
        num_results = max(1, min(10, num_results))
        
        # Call DuckDuckGo search
        results = search_results_tool.invoke({"query": query, "num_results": num_results})
        
        # Convert results to easy-to-process format
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        
        logger.info(f"Structured search complete, found {len(formatted_results)} results")
        return formatted_results
    except Exception as e:
        error_msg = f"Structured search error: {str(e)}"
        logger.error(error_msg)
        return []

def main():
    """Main function to start the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="DuckDuckGo Search MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Setup logging
    log_dir = setup_logging(args.debug)
    
    logger.info("Starting DuckDuckGo Search MCP service...")
    
    try:
        # Start server
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("DuckDuckGo Search MCP service stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running DuckDuckGo Search MCP service: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("DuckDuckGo Search MCP service stopped")

if __name__ == "__main__":
    main() 