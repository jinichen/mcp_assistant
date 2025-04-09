import os
import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get LLM provider configuration
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai").lower()

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Default models
DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4-turbo")
DEFAULT_GOOGLE_MODEL = os.getenv("DEFAULT_GOOGLE_MODEL", "gemini-pro")
DEFAULT_ANTHROPIC_MODEL = os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-opus-20240229")

class LLMProvider:
    """Class to handle different LLM provider interactions"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM provider
        
        Args:
            provider: The LLM provider to use (openai, google, or anthropic)
                     If None, uses the DEFAULT_LLM_PROVIDER from env vars
        """
        self.provider = provider.lower() if provider else DEFAULT_LLM_PROVIDER
        self._check_api_keys()
    
    def _check_api_keys(self):
        """Check if the required API keys are available"""
        if self.provider == "openai" and not OPENAI_API_KEY:
            raise ValueError(f"OpenAI API密钥未配置。请在.env文件中设置OPENAI_API_KEY。当前值: {OPENAI_API_KEY}")
        elif self.provider == "openai" and OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OpenAI API密钥使用了默认值。请在.env文件中设置有效的OPENAI_API_KEY。")
        elif self.provider == "google" and not GOOGLE_API_KEY:
            raise ValueError(f"Google API密钥未配置。请在.env文件中设置GOOGLE_API_KEY。当前值: {GOOGLE_API_KEY}")
        elif self.provider == "google" and GOOGLE_API_KEY == "your_google_api_key_here":
            raise ValueError("Google API密钥使用了默认值。请在.env文件中设置有效的GOOGLE_API_KEY。")
        elif self.provider == "anthropic" and not ANTHROPIC_API_KEY:
            raise ValueError(f"Anthropic API密钥未配置。请在.env文件中设置ANTHROPIC_API_KEY。当前值: {ANTHROPIC_API_KEY}")
        elif self.provider == "anthropic" and ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
            raise ValueError("Anthropic API密钥使用了默认值。请在.env文件中设置有效的ANTHROPIC_API_KEY。")
    
    async def generate_from_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate content directly from a prompt using LLM
        
        Args:
            prompt: The text prompt to send to the LLM
            
        Returns:
            List of generated items (typically test scenarios)
        """
        try:
            if self.provider == "openai":
                return await self._generate_with_openai_prompt(prompt)
            elif self.provider == "google":
                return await self._generate_with_google_prompt(prompt)
            elif self.provider == "anthropic":
                return await self._generate_with_anthropic_prompt(prompt)
            else:
                raise ValueError(f"不支持的LLM提供商: {self.provider}")
        except Exception as e:
            # Provide more detailed error information
            error_msg = str(e)
            if "invalid_api_key" in error_msg or "API key" in error_msg:
                if self.provider == "openai":
                    raise ValueError(f"OpenAI API密钥无效或未设置。请检查.env文件中的OPENAI_API_KEY配置。错误: {error_msg}")
                elif self.provider == "google":
                    raise ValueError(f"Google API密钥无效或未设置。请检查.env文件中的GOOGLE_API_KEY配置。错误: {error_msg}")
                elif self.provider == "anthropic":
                    raise ValueError(f"Anthropic API密钥无效或未设置。请检查.env文件中的ANTHROPIC_API_KEY配置。错误: {error_msg}")
            raise ValueError(f"使用{self.provider}生成内容时出错: {error_msg}")
    
    async def _generate_with_openai_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate content using OpenAI from a direct prompt"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_API_KEY}"
                    },
                    json={
                        "model": DEFAULT_OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "您是一位精通API测试的QA工程师，擅长创建全面的测试场景。请使用中文回复。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                
                try:
                    # Parse the JSON content
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
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
                    raise Exception(f"无法解析OpenAI响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(f"OpenAI API密钥无效或未设置。请检查.env文件中的OPENAI_API_KEY配置。")
            raise Exception(f"OpenAI API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用OpenAI API时出错: {str(e)}")
    
    async def _generate_with_google_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate content using Google's Gemini API from a direct prompt"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/{DEFAULT_GOOGLE_MODEL}:generateContent",
                    headers={
                        "Content-Type": "application/json"
                    },
                    params={
                        "key": GOOGLE_API_KEY
                    },
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Google API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                
                try:
                    # Extract the JSON part from the response text
                    # Google API might return markdown with JSON embedded
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
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
                    raise Exception(f"无法解析Google响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and "API key" in e.response.text:
                raise ValueError(f"Google API密钥无效或未设置。请检查.env文件中的GOOGLE_API_KEY配置。")
            raise Exception(f"Google API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用Google API时出错: {str(e)}")
    
    async def _generate_with_anthropic_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate content using Anthropic's Claude API from a direct prompt"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": DEFAULT_ANTHROPIC_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "system": "您是一位精通API测试的QA工程师，擅长创建全面的测试场景。请使用中文回复，并始终返回有效的JSON。"
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Anthropic API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "{}")
                
                try:
                    # Extract the JSON part from the response text
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
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
                    raise Exception(f"无法解析Anthropic响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(f"Anthropic API密钥无效或未设置。请检查.env文件中的ANTHROPIC_API_KEY配置。")
            raise Exception(f"Anthropic API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用Anthropic API时出错: {str(e)}")
    
    async def generate_test_scenarios(self, 
                                     api_spec: Dict[str, Any],
                                     api_path: str,
                                     method: str) -> List[Dict[str, Any]]:
        """
        Generate test scenarios using LLM
        
        Args:
            api_spec: The API specification dictionary
            api_path: The API path
            method: The HTTP method
            
        Returns:
            List of test scenario dictionaries
        """
        try:
            if self.provider == "openai":
                return await self._generate_with_openai(api_spec, api_path, method)
            elif self.provider == "google":
                return await self._generate_with_google(api_spec, api_path, method)
            elif self.provider == "anthropic":
                return await self._generate_with_anthropic(api_spec, api_path, method)
            else:
                raise ValueError(f"不支持的LLM提供商: {self.provider}")
        except Exception as e:
            # 提供更详细的错误信息
            error_msg = str(e)
            if "invalid_api_key" in error_msg or "API key" in error_msg:
                if self.provider == "openai":
                    raise ValueError(f"OpenAI API密钥无效或未设置。请检查.env文件中的OPENAI_API_KEY配置。错误: {error_msg}")
                elif self.provider == "google":
                    raise ValueError(f"Google API密钥无效或未设置。请检查.env文件中的GOOGLE_API_KEY配置。错误: {error_msg}")
                elif self.provider == "anthropic":
                    raise ValueError(f"Anthropic API密钥无效或未设置。请检查.env文件中的ANTHROPIC_API_KEY配置。错误: {error_msg}")
            raise ValueError(f"使用{self.provider}生成测试场景时出错: {error_msg}")
    
    def _get_prompt(self, api_spec: Dict[str, Any], api_path: str, method: str) -> str:
        """
        Generate a prompt for the LLM
        
        Args:
            api_spec: The API specification dictionary
            api_path: The API path
            method: The HTTP method
            
        Returns:
            Prompt text for the LLM
        """
        # Extract relevant information from API spec for this path/method
        path_info = api_spec.get("paths", {}).get(api_path, {})
        method_info = path_info.get(method.lower(), {})
        
        # Get request body schema reference
        request_body_ref = None
        request_schema = {}
        for param in method_info.get("parameters", []):
            if param.get("in") == "body":
                request_body_ref = param.get("schema", {}).get("$ref")
                if request_body_ref:
                    schema_name = request_body_ref.split("/")[-1]
                    request_schema = api_spec.get("definitions", {}).get(schema_name, {})
        
        # Get response schema
        response_schema = {}
        success_response = method_info.get("responses", {}).get("200", {})
        response_ref = success_response.get("schema", {}).get("$ref")
        if response_ref:
            schema_name = response_ref.split("/")[-1]
            response_schema = api_spec.get("definitions", {}).get(schema_name, {})
        
        # Build the prompt
        prompt = f"""作为一名QA工程师，为以下API端点生成全面的测试场景:

API路径: {api_path}
HTTP方法: {method.upper()}
概述: {method_info.get('summary', 'N/A')}
描述: {method_info.get('description', 'N/A')}

请求Schema:
{json.dumps(request_schema, indent=2, ensure_ascii=False)}

响应Schema:
{json.dumps(response_schema, indent=2, ensure_ascii=False)}

可能的响应代码:
"""
        
        # Add response codes
        for status_code, response in method_info.get("responses", {}).items():
            prompt += f"- {status_code}: {response.get('description', 'N/A')}\n"
        
        prompt += """
生成至少5个测试场景，包括:
1. 一个应该成功的正常情况
2. 边缘情况(例如，空数组，最小/最大值)
3. 错误情况(例如，无效输入，缺少必需参数)
4. 认证/授权情况

对于每个场景，提供:
1. 描述性名称
2. 详细描述
3. 请求体/参数
4. 预期响应(状态码和响应体)

请将您的响应格式化为JSON数组的测试场景。
每个场景应该是具有以下字段的JSON对象:
- name: 字符串
- description: 字符串
- request: 对象(请求体)
- expected_response: 具有status_code(数字)和body(对象)的对象

示例格式:
[
  {
    "name": "正常操作",
    "description": "使用有效参数测试正常操作",
    "request": { "param1": "value1" },
    "expected_response": {
      "status_code": 200,
      "body": { "result": "success" }
    }
  }
]

请确保返回的是有效的JSON格式，并且使用中文进行描述。
"""
        
        return prompt
    
    async def _generate_with_openai(self, 
                                   api_spec: Dict[str, Any],
                                   api_path: str, 
                                   method: str) -> List[Dict[str, Any]]:
        """Generate test scenarios using OpenAI"""
        prompt = self._get_prompt(api_spec, api_path, method)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_API_KEY}"
                    },
                    json={
                        "model": DEFAULT_OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "您是一位精通API测试的QA工程师，擅长创建全面的测试场景。请使用中文回复。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                
                try:
                    # The content should be a JSON string with a "scenarios" field
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
                    elif "scenarios" in parsed:
                        return parsed["scenarios"]
                    else:
                        return list(parsed.values())[0] if parsed else []
                except json.JSONDecodeError as e:
                    raise Exception(f"无法解析OpenAI响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(f"OpenAI API密钥无效或未设置。请检查.env文件中的OPENAI_API_KEY配置。")
            raise Exception(f"OpenAI API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用OpenAI API时出错: {str(e)}")
    
    async def _generate_with_google(self, 
                                   api_spec: Dict[str, Any],
                                   api_path: str, 
                                   method: str) -> List[Dict[str, Any]]:
        """Generate test scenarios using Google's Gemini API"""
        prompt = self._get_prompt(api_spec, api_path, method)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/{DEFAULT_GOOGLE_MODEL}:generateContent",
                    headers={
                        "Content-Type": "application/json"
                    },
                    params={
                        "key": GOOGLE_API_KEY
                    },
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Google API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                
                try:
                    # Extract the JSON part from the response text
                    # Google API might return markdown with JSON embedded
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
                    elif "scenarios" in parsed:
                        return parsed["scenarios"]
                    else:
                        return list(parsed.values())[0] if parsed else []
                except json.JSONDecodeError as e:
                    raise Exception(f"无法解析Google响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and "API key" in e.response.text:
                raise ValueError(f"Google API密钥无效或未设置。请检查.env文件中的GOOGLE_API_KEY配置。")
            raise Exception(f"Google API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用Google API时出错: {str(e)}")
    
    async def _generate_with_anthropic(self, 
                                      api_spec: Dict[str, Any],
                                      api_path: str, 
                                      method: str) -> List[Dict[str, Any]]:
        """Generate test scenarios using Anthropic's Claude API"""
        prompt = self._get_prompt(api_spec, api_path, method)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": DEFAULT_ANTHROPIC_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "system": "您是一位精通API测试的QA工程师，擅长创建全面的测试场景。请使用中文回复，并始终返回有效的JSON。"
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Anthropic API错误(状态码 {response.status_code}): {response.text}")
                
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "{}")
                
                try:
                    # Extract the JSON part from the response text
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    parsed = json.loads(content)
                    # Check if it's directly an array or if it has a wrapper object
                    if isinstance(parsed, list):
                        return parsed
                    elif "scenarios" in parsed:
                        return parsed["scenarios"]
                    else:
                        return list(parsed.values())[0] if parsed else []
                except json.JSONDecodeError as e:
                    raise Exception(f"无法解析Anthropic响应: {e}\n响应内容: {content}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(f"Anthropic API密钥无效或未设置。请检查.env文件中的ANTHROPIC_API_KEY配置。")
            raise Exception(f"Anthropic API调用错误: {str(e)}")
        except Exception as e:
            raise Exception(f"调用Anthropic API时出错: {str(e)}")

# Helper function to get the default LLM provider instance
def get_llm_provider(provider: Optional[str] = None) -> LLMProvider:
    """
    Get a configured LLM provider instance
    
    Args:
        provider: Optional provider override, if None uses default from env
        
    Returns:
        LLMProvider instance
    """
    return LLMProvider(provider) 