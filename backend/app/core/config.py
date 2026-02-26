"""
Application configuration
"""

from typing import Optional
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "DarkWeb Monitor API"
    app_version: str = "2.0.0"
    api_prefix: str = ""
    
    # CORS Settings
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env
    )


settings = Settings()
