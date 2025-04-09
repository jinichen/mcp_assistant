#!/usr/bin/env python3
"""
Weather Query Tool Server
Processes weather queries and returns simulated weather information
"""
import sys
import json
import re
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("weather-tool")

# Simulated weather data
WEATHER_DATA = {
    "Beijing": {
        "temperature": lambda: random.randint(15, 30),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Light Rain", "Overcast"]),
        "humidity": lambda: random.randint(30, 80),
        "wind": lambda: random.randint(0, 30)
    },
    "Shanghai": {
        "temperature": lambda: random.randint(18, 32),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Light Rain", "Thunderstorm"]),
        "humidity": lambda: random.randint(40, 90),
        "wind": lambda: random.randint(0, 25)
    },
    "Guangzhou": {
        "temperature": lambda: random.randint(20, 35),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Shower", "Thunderstorm"]),
        "humidity": lambda: random.randint(50, 95),
        "wind": lambda: random.randint(0, 20)
    },
    "Shenzhen": {
        "temperature": lambda: random.randint(20, 35),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Shower", "Thunderstorm"]),
        "humidity": lambda: random.randint(50, 95),
        "wind": lambda: random.randint(0, 20)
    },
    "Hangzhou": {
        "temperature": lambda: random.randint(15, 30),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Light Rain", "Overcast"]),
        "humidity": lambda: random.randint(40, 85),
        "wind": lambda: random.randint(0, 25)
    },
    "Chengdu": {
        "temperature": lambda: random.randint(15, 28),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Light Rain", "Overcast"]),
        "humidity": lambda: random.randint(45, 85),
        "wind": lambda: random.randint(0, 15)
    },
    "New York": {
        "temperature": lambda: random.randint(10, 25),
        "condition": lambda: random.choice(["Clear", "Cloudy", "Light Rain", "Overcast"]),
        "humidity": lambda: random.randint(30, 70),
        "wind": lambda: random.randint(5, 30)
    },
    "London": {
        "temperature": lambda: random.randint(8, 20),
        "condition": lambda: random.choice(["Cloudy", "Light Rain", "Overcast", "Heavy Rain"]),
        "humidity": lambda: random.randint(50, 90),
        "wind": lambda: random.randint(10, 35)
    }
}

def extract_location(query: str) -> Optional[str]:
    """
    Extract location from the query
    
    Args:
        query: User query
        
    Returns:
        Extracted location, or None if not found
    """
    logger.info(f"Extracting location information, query: {query}")
    
    # Pattern matching for common weather query formats
    patterns = [
        r'weather in (.+)',
        r'what\'s the weather like in (.+)',
        r'temperature in (.+)',
        r'today\'s weather in (.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            location = match.group(1).strip()
            logger.info(f"Extracted location: {location}")
            return location
    
    # If no pattern matched, check if query contains known locations
    for location in WEATHER_DATA.keys():
        if location.lower() in query.lower():
            logger.info(f"Found location in query: {location}")
            return location
    
    logger.warning("Could not extract location information")
    return None

def get_weather(location: str) -> Dict[str, Any]:
    """
    Get weather information for the specified location
    
    Args:
        location: Location
        
    Returns:
        Weather information
    """
    logger.info(f"Getting weather information, location: {location}")
    
    location_data = WEATHER_DATA.get(location)
    if not location_data:
        logger.warning(f"No weather data found for location {location}")
        return {
            "location": location,
            "error": f"No weather information found for {location}"
        }
    
    # Generate random weather data
    current_date = datetime.now().strftime("%Y-%m-%d")
    weather = {
        "location": location,
        "date": current_date,
        "temperature": location_data["temperature"](),
        "condition": location_data["condition"](),
        "humidity": location_data["humidity"](),
        "wind": location_data["wind"](),
    }
    
    logger.info(f"Generated weather data: {weather}")
    return weather

def format_weather_response(weather: Dict[str, Any]) -> str:
    """
    Format weather response
    
    Args:
        weather: Weather data
        
    Returns:
        Formatted response
    """
    if "error" in weather:
        return weather["error"]
    
    response = f"Weather forecast for {weather['location']} ({weather['date']}):\n"
    response += f"🌡️ Temperature: {weather['temperature']}°C\n"
    response += f"🌤️ Condition: {weather['condition']}\n"
    response += f"💧 Humidity: {weather['humidity']}%\n"
    response += f"🌬️ Wind Speed: {weather['wind']} km/h"
    
    return response

def process_weather_query(query: str) -> str:
    """
    Process weather query
    
    Args:
        query: User query
        
    Returns:
        Weather information
    """
    logger.info(f"Processing weather query: {query}")
    
    # Extract location
    location = extract_location(query)
    if not location:
        return "Sorry, I couldn't identify the location in your query. Please specify a city, for example 'weather in Beijing'."
    
    # Get weather data
    weather = get_weather(location)
    
    # Format response
    response = format_weather_response(weather)
    logger.info(f"Weather query result: {response}")
    
    return response

def main():
    """
    Main function, reads input from stdin, processes it, and writes to stdout
    """
    logger.info("Starting weather tool server...")
    
    while True:
        try:
            # Read one line of input
            input_line = sys.stdin.readline()
            if not input_line:
                logger.warning("Received empty input, exiting")
                break
                
            logger.info(f"Received input: {input_line.strip()}")
            
            # Parse JSON input
            try:
                input_json = json.loads(input_line)
                query = input_json.get("query", "")
                
                # Process query
                result = process_weather_query(query)
                
                # Return result
                response = {"result": result}
                response_json = json.dumps(response)
                logger.info(f"Output result: {response_json}")
                
                sys.stdout.write(response_json + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                error_msg = "Input is not a valid JSON format"
                logger.error(error_msg)
                sys.stdout.write(json.dumps({"error": error_msg}) + "\n")
                sys.stdout.flush()
                
        except Exception as e:
            logger.error(f"Error occurred during processing: {e}")
            logger.error(traceback.format_exc())
            try:
                sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
                sys.stdout.flush()
            except:
                pass

if __name__ == "__main__":
    main() 