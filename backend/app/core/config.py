import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Dict, Optional, Any

class Settings(BaseSettings):
    # Database settings
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    APP_NAME: str
    APP_VERSION: str
    
    # Security settings
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Provider Settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_OPENAI_MODEL: str = "gpt-3.5-turbo"
    DEFAULT_GOOGLE_MODEL: str = "gemini-pro"
    DEFAULT_ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    DEFAULT_NVIDIA_MODEL: str = "mixtral_8x7b"
    
    # LLM API keys
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = "https://api.openai.com/v1"
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: Optional[str] = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    # LangChain settings
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_ENDPOINT: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None
    LANGCHAIN_TRACING_V2: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_app_settings() -> Settings:
    return Settings() 