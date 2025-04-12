import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Langchain imports for version 0.3.x
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get LLM provider configuration
DEFAULT_LLM_PROVIDER = os.getenv("TEST_GENERATOR_DEFAULT_LLM_PROVIDER", "openai").lower()

# API keys
OPENAI_API_KEY = os.getenv("TEST_GENERATOR_OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("TEST_GENERATOR_OPENAI_BASE_URL", "https://api.openai.com/v1")
GOOGLE_API_KEY = os.getenv("TEST_GENERATOR_GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("TEST_GENERATOR_ANTHROPIC_API_KEY", "")

# Default models
DEFAULT_OPENAI_MODEL = os.getenv("TEST_GENERATOR_DEFAULT_OPENAI_MODEL", "gpt-4-turbo")
DEFAULT_GOOGLE_MODEL = os.getenv("TEST_GENERATOR_DEFAULT_GOOGLE_MODEL", "gemini-pro")
DEFAULT_ANTHROPIC_MODEL = os.getenv("TEST_GENERATOR_DEFAULT_ANTHROPIC_MODEL", "claude-3-opus-20240229")

# LLM Parameters
LLM_TEMPERATURE = float(os.getenv("TEST_GENERATOR_LLM_TEMPERATURE", "0.2"))
LLM_REQUEST_TIMEOUT = int(os.getenv("TEST_GENERATOR_LLM_REQUEST_TIMEOUT", "60"))

class LLMProvider:
    """Class to handle different LLM provider interactions using Langchain"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM provider
        
        Args:
            provider: The LLM provider to use (openai, google, or anthropic)
                     If None, uses the DEFAULT_LLM_PROVIDER from env vars
        """
        self.provider = provider.lower() if provider else DEFAULT_LLM_PROVIDER
        self._check_api_keys()
        self._initialize_models()
    
    def _check_api_keys(self):
        """Check if the required API keys are available"""
        if self.provider == "openai" and not OPENAI_API_KEY:
            raise ValueError(f"OpenAI API key not configured. Please set TEST_GENERATOR_OPENAI_API_KEY in .env file. Current value: {OPENAI_API_KEY}")
        elif self.provider == "openai" and OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OpenAI API key is using default value. Please set a valid TEST_GENERATOR_OPENAI_API_KEY in .env file.")
        elif self.provider == "google" and not GOOGLE_API_KEY:
            raise ValueError(f"Google API key not configured. Please set TEST_GENERATOR_GOOGLE_API_KEY in .env file. Current value: {GOOGLE_API_KEY}")
        elif self.provider == "google" and GOOGLE_API_KEY == "your_google_api_key_here":
            raise ValueError("Google API key is using default value. Please set a valid TEST_GENERATOR_GOOGLE_API_KEY in .env file.")
        elif self.provider == "anthropic" and not ANTHROPIC_API_KEY:
            raise ValueError(f"Anthropic API key not configured. Please set TEST_GENERATOR_ANTHROPIC_API_KEY in .env file. Current value: {ANTHROPIC_API_KEY}")
        elif self.provider == "anthropic" and ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
            raise ValueError("Anthropic API key is using default value. Please set a valid TEST_GENERATOR_ANTHROPIC_API_KEY in .env file.")
    
    def _initialize_models(self):
        """Initialize Langchain models based on the selected provider"""
        callbacks = [StdOutCallbackHandler()]
        
        if self.provider == "openai":
            self.chat_model = ChatOpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL,
                model=DEFAULT_OPENAI_MODEL,
                temperature=LLM_TEMPERATURE,
                callbacks=callbacks,
                streaming=False,
                request_timeout=LLM_REQUEST_TIMEOUT
            )
        elif self.provider == "google":
            try:
                self.chat_model = ChatGoogleGenerativeAI(
                    api_key=GOOGLE_API_KEY,
                    model=DEFAULT_GOOGLE_MODEL,
                    temperature=LLM_TEMPERATURE,
                    callbacks=callbacks,
                    request_timeout=LLM_REQUEST_TIMEOUT
                )
            except ImportError:
                logger.warning("langchain_google_genai not installed. Falling back to OpenAI")
                self.provider = "openai"
                self.chat_model = ChatOpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    model=DEFAULT_OPENAI_MODEL,
                    temperature=LLM_TEMPERATURE,
                    callbacks=callbacks,
                    request_timeout=LLM_REQUEST_TIMEOUT
                )
        elif self.provider == "anthropic":
            try:
                self.chat_model = ChatAnthropic(
                    api_key=ANTHROPIC_API_KEY,
                    model=DEFAULT_ANTHROPIC_MODEL,
                    temperature=LLM_TEMPERATURE,
                    callbacks=callbacks,
                    request_timeout=LLM_REQUEST_TIMEOUT
                )
            except ImportError:
                logger.warning("langchain_anthropic not installed. Falling back to OpenAI")
                self.provider = "openai"
                self.chat_model = ChatOpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    model=DEFAULT_OPENAI_MODEL,
                    temperature=LLM_TEMPERATURE,
                    callbacks=callbacks,
                    request_timeout=LLM_REQUEST_TIMEOUT
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def generate_from_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate content directly from a prompt using LLM
        
        Args:
            prompt: The text prompt to send to the LLM
            
        Returns:
            List of generated items (typically test scenarios)
        """
        try:
            # Create messages for Langchain
            messages = [
                SystemMessage(content="You are a QA engineer specializing in API testing, skilled at creating comprehensive test scenarios. Please respond with valid JSON."),
                HumanMessage(content=prompt)
            ]
            
            # Set appropriate response format for JSON
            response_format = None
            if self.provider == "openai":
                # For OpenAI, use response_format parameter
                response_format = {"type": "json_object"}
            
            # Invoke the model
            if response_format:
                response = await self.chat_model.ainvoke(messages, response_format=response_format)
            else:
                response = await self.chat_model.ainvoke(messages)
            
            content = response.content
            
            # Extract JSON from markdown code blocks if needed
            content = content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
            
            try:
                # Parse the JSON content
                parsed = json.loads(content)
                # Check if it's directly an array or if it has a wrapper object
                if isinstance(parsed, list):
                    return parsed
                elif "test_scenarios" in parsed:
                    return parsed["test_scenarios"]
                elif "scenarios" in parsed:
                    return parsed["scenarios"]
                elif "testcases" in parsed:
                    return parsed["testcases"]
                else:
                    # Try to find any list in the object
                    for key, value in parsed.items():
                        if isinstance(value, list):
                            return value
                    # If no list is found, return empty list
                    return []
            except json.JSONDecodeError as e:
                # Try to extract JSON from the text response
                import re
                json_pattern = r'\{[^{}]*\}'
                matches = re.findall(json_pattern, content)
                if matches:
                    # Try each match until we find valid JSON
                    for match in matches:
                        try:
                            parsed = json.loads(match)
                            if isinstance(parsed, dict):
                                if "test_scenarios" in parsed:
                                    return parsed["test_scenarios"]
                                elif "scenarios" in parsed:
                                    return parsed["scenarios"]
                                elif "testcases" in parsed:
                                    return parsed["testcases"]
                                else:
                                    # Try to find any list in the object
                                    for key, value in parsed.items():
                                        if isinstance(value, list):
                                            return value
                        except json.JSONDecodeError:
                            continue
                
                # If no valid JSON found, create a structured format from the text
                return [{
                    "name": "Generated Scenario",
                    "description": content,
                    "steps": []
                }]
                
        except Exception as e:
            # Provide more detailed error information
            error_msg = str(e)
            if "invalid_api_key" in error_msg or "API key" in error_msg:
                if self.provider == "openai":
                    raise ValueError(f"OpenAI API key invalid or not set. Please check TEST_GENERATOR_OPENAI_API_KEY in .env file. Error: {error_msg}")
                elif self.provider == "google":
                    raise ValueError(f"Google API key invalid or not set. Please check TEST_GENERATOR_GOOGLE_API_KEY in .env file. Error: {error_msg}")
                elif self.provider == "anthropic":
                    raise ValueError(f"Anthropic API key invalid or not set. Please check TEST_GENERATOR_ANTHROPIC_API_KEY in .env file. Error: {error_msg}")
            raise ValueError(f"Error generating content with {self.provider}: {error_msg}")
    
    async def generate_test_scenarios(self, 
                                     api_spec: Dict[str, Any],
                                     api_path: str,
                                     method: str) -> List[Dict[str, Any]]:
        """
        Generate test scenarios from API specification
        
        Args:
            api_spec: The OpenAPI specification
            api_path: The API path to generate scenarios for
            method: The HTTP method to generate scenarios for
            
        Returns:
            List of test scenarios
        """
        prompt = self._get_prompt(api_spec, api_path, method)
        return await self.generate_from_prompt(prompt)
    
    def _get_prompt(self, api_spec: Dict[str, Any], api_path: str, method: str) -> str:
        """Generate a prompt for scenario generation based on API spec"""
        # Get path details
        path_spec = api_spec.get("paths", {}).get(api_path, {})
        method_spec = path_spec.get(method.lower(), {})
        
        # Get API information
        api_title = api_spec.get("info", {}).get("title", "Unknown API")
        api_description = api_spec.get("info", {}).get("description", "No description")
        operation_id = method_spec.get("operationId", f"{method} {api_path}")
        operation_summary = method_spec.get("summary", "No summary")
        operation_description = method_spec.get("description", "No detailed description")
        
        # Get parameters
        parameters = method_spec.get("parameters", [])
        
        # Get request body details
        request_body = method_spec.get("requestBody", {})
        request_content = request_body.get("content", {})
        request_schema = None
        for content_type, content_details in request_content.items():
            if "schema" in content_details:
                request_schema = content_details["schema"]
                break
        
        # Get response details
        responses = method_spec.get("responses", {})
        
        # Create the prompt
        prompt = f"""Based on the following API specification, generate comprehensive test scenarios for {method.upper()} {api_path} interface:

API Information:
- Title: {api_title}
- Description: {api_description}

Operation Information:
- Operation ID: {operation_id}
- Summary: {operation_summary}
- Description: {operation_description}
"""

        # Add parameters information
        if parameters:
            prompt += "\nParameter Information:"
            for param in parameters:
                param_name = param.get("name", "Unknown parameter")
                param_in = param.get("in", "Unknown location")  # path, query, header, cookie
                param_required = "Yes" if param.get("required", False) else "No"
                param_type = param.get("schema", {}).get("type", "Unknown type")
                param_format = param.get("schema", {}).get("format", "None")
                param_description = param.get("description", "No description")
                
                prompt += f"""
- {param_name} ({param_in})
  - Required: {param_required}
  - Type: {param_type}
  - Format: {param_format}
  - Description: {param_description}"""
        
        # Add request body information
        if request_schema:
            prompt += "\n\nRequest Body:"
            prompt += f"\n```json\n{json.dumps(request_schema, ensure_ascii=False, indent=2)}\n```"
        
        # Add response information
        if responses:
            prompt += "\n\nResponse Information:"
            for status_code, response_details in responses.items():
                response_description = response_details.get("description", "No description")
                prompt += f"\n- {status_code}: {response_description}"
                
                # Add response schema if available
                response_content = response_details.get("content", {})
                for content_type, content_details in response_content.items():
                    if "schema" in content_details:
                        response_schema = content_details["schema"]
                        prompt += f"\n  Content Type: {content_type}"
                        prompt += f"\n  Schema:\n```json\n{json.dumps(response_schema, ensure_ascii=False, indent=2)}\n```"
        
        prompt += """

Please create comprehensive test scenarios for this API, including positive tests, negative tests, boundary tests, etc.
For each scenario, provide the following information:
1. Scenario name
2. Scenario description
3. Preconditions
4. Test steps
5. Expected results
6. Request parameters/examples (JSON format)
7. Test priority (P0-P3)
8. Applicable environments

Based on the API specification above, please return 5-10 test scenarios in the following JSON format:

```json
[
  {
    "name": "Scenario name",
    "description": "Scenario description",
    "preconditions": "Preconditions",
    "steps": ["Step 1", "Step 2", "..."],
    "expected_result": "Expected result",
    "request_example": {},
    "priority": "P0-P3",
    "environment": ["Development", "Testing", "Production"]
  }
]
```

Please ensure the scenarios are comprehensive and focus on potential security issues, performance considerations, and boundary conditions.
"""
        return prompt
    
def get_llm_provider(provider: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get an LLM provider instance
    
    Args:
        provider: The LLM provider to use. If None, uses the DEFAULT_LLM_PROVIDER from env vars
        
    Returns:
        An instance of LLMProvider
    """
    return LLMProvider(provider) 