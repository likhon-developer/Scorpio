"""
Configuration management for Scorpio AI Agent System
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "Scorpio AI Agent System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )

    # Database - MongoDB
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        env="MONGODB_URL"
    )
    MONGODB_DATABASE: str = Field(
        default="scorpio",
        env="MONGODB_DATABASE"
    )

    # Cache - Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )

    # LLM Providers
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Docker
    DOCKER_SOCKET_PATH: str = Field(
        default="/var/run/docker.sock",
        env="DOCKER_SOCKET_PATH"
    )
    SANDBOX_IMAGE: str = Field(
        default="scorpio-sandbox:latest",
        env="SANDBOX_IMAGE"
    )

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = Field(
        default=60,
        env="SESSION_TIMEOUT_MINUTES"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # MCP Configuration
    MCP_ENABLED: bool = Field(default=True, env="MCP_ENABLED")
    MCP_SERVER_URL: Optional[str] = Field(default=None, env="MCP_SERVER_URL")

    # Sandbox Configuration
    SANDBOX_BASE_URL: str = Field(
        default="http://localhost:8080",
        env="SANDBOX_BASE_URL"
    )
    SANDBOX_VNC_PORT: int = Field(default=5900, env="SANDBOX_VNC_PORT")
    SANDBOX_CDP_PORT: int = Field(default=9222, env="SANDBOX_CDP_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
