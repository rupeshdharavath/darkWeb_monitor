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
    
    # MongoDB Configuration
    mongodb_uri: Optional[str] = None
    database_name: str = "darkweb_monitor"
    collection_name: str = "scraped_data"
    
    # Tor Configuration
    tor_proxy_http: str = "socks5h://127.0.0.1:9050"
    tor_proxy_https: str = "socks5h://127.0.0.1:9050"
    
    # Scraping Settings
    request_timeout: int = 30
    delay_between_requests: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Logging Settings
    log_file: str = "logs/app.log"
    log_level: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env
    )
    
    @property
    def tor_proxy(self) -> dict:
        """Get Tor proxy configuration"""
        return {
            "http": self.tor_proxy_http,
            "https": self.tor_proxy_https,
        }
    
    @property
    def headers(self) -> dict:
        """Get default headers"""
        return {"User-Agent": self.user_agent}


settings = Settings()
