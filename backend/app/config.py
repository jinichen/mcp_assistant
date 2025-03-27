from pydantic_settings import BaseSettings
import os
from typing import Optional
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, Field

"""Application settings"""
# API keys
class AppSettings(BaseModel):
    openai_api_key: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY"))
    nvidia_api_key: Optional[str] = Field(default=os.getenv("NVIDIA_API_KEY"))
    google_api_key: Optional[str] = Field(default=os.getenv("GOOGLE_API_KEY"))
    
    # MCP configuration
    mcp_enabled: bool = Field(default=os.getenv("USE_MCP", "false").lower() == "true")
    mcp_config_path: Optional[str] = Field(default=os.getenv("MCP_CONFIG_PATH", "./config/mcp_config.json"))
    
    # Other configuration options
    default_provider: str = Field(default=os.getenv("DEFAULT_PROVIDER", "google"))
    
    # In Pydantic v2, use model_config instead of Config inner class
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"  # Allow extra fields
    }

"""Get the singleton instance of application settings"""
def get_settings() -> AppSettings:
    return AppSettings()