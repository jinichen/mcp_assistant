#!/usr/bin/env python3
"""
Weather information tool server
Provides weather information for locations around the world
"""
import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("weather-tool")

# 创建FastMCP实例
mcp = FastMCP("Weather")

# 模拟天气数据
MOCK_WEATHER = {
    "beijing": {
        "condition": "晴朗",
        "temperature": "24°C",
        "humidity": "40%",
        "wind": "东北风 3级"
    },
    "shanghai": {
        "condition": "多云",
        "temperature": "26°C",
        "humidity": "65%",
        "wind": "东南风 2级"
    },
    "new york": {
        "condition": "阴天",
        "temperature": "18°C",
        "humidity": "70%",
        "wind": "西风 4级"
    },
    "london": {
        "condition": "小雨",
        "temperature": "15°C",
        "humidity": "85%",
        "wind": "西南风 3级"
    },
    "tokyo": {
        "condition": "晴朗",
        "temperature": "22°C",
        "humidity": "55%",
        "wind": "东风 2级"
    }
}

def get_location_from_query(query: str) -> Optional[str]:
    """
    Extract location name from query
    
    Args:
        query: User query about weather
        
    Returns:
        Location name or None
    """
    query = query.lower()
    for location in MOCK_WEATHER.keys():
        if location in query:
            return location
    
    return None

@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Get weather information for a specific location.
    
    Args:
        location: The name of the city or location
        
    Returns:
        Weather information for the location
    """
    logger.info(f"Getting weather for: {location}")
    
    # If query contains location info, extract it
    if not location or location.strip() == "":
        extracted_location = get_location_from_query(location)
        if extracted_location:
            location = extracted_location
    
    # Normalize location
    location = location.lower().strip()
    
    # Check if we have data for this location
    weather_data = MOCK_WEATHER.get(location)
    if weather_data:
        return format_weather_response(location, weather_data)
    
    # Default response for unknown locations
    return f"抱歉，我没有关于 {location} 的天气信息。请尝试其他城市，如北京、上海、纽约、伦敦或东京。"

def format_weather_response(location: str, weather: Dict[str, Any]) -> str:
    """Format weather data into a readable response"""
    location_map = {
        "beijing": "北京",
        "shanghai": "上海",
        "new york": "纽约",
        "london": "伦敦",
        "tokyo": "东京"
    }
    
    display_name = location_map.get(location, location)
    
    response = f"{display_name}天气信息：\n"
    response += f"天气状况: {weather['condition']}\n"
    response += f"温度: {weather['temperature']}\n"
    response += f"湿度: {weather['humidity']}\n"
    response += f"风力: {weather['wind']}"
    
    return response

if __name__ == "__main__":
    # 启动MCP服务
    mcp.run(transport="stdio") 