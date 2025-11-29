"""Application configuration settings"""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application settings
    APP_NAME: str = Field(default="My Python Project", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="production", description="Environment (development/staging/production)")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (deprecated - use CONSOLE_LOG_LEVEL or FILE_LOG_LEVEL)")
    CONSOLE_LOG_LEVEL: str = Field(default="INFO", description="Console logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    FILE_LOG_LEVEL: str = Field(default="DEBUG", description="File logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    LOG_DIR: str = Field(default="logs", description="Directory for log files")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file name (optional)")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Maximum log file size in bytes (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files to keep")
    LOG_ROTATION_TIMEOUT: int = Field(default=300, description="Log rotation check interval in seconds (default: 300 = 5 minutes)")
    
    # API settings (if needed)
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def __init__(self, **kwargs):
        print("Initializing Settings class")
        super().__init__(**kwargs)
        # Create logs directory if it doesn't exist
        if self.LOG_DIR and not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)"""
    print("Creating global settings instance")
    return Settings()
    print("Global settings instance created")


# Create a global settings instance
settings = get_settings()