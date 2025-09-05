from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "Scorpio AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "scorpio")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Docker Sandbox
    SANDBOX_URL: str = os.getenv("SANDBOX_URL", "http://localhost:8080")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    # MCP Configuration
    MCP_MODEL: str = os.getenv("MCP_MODEL", "gpt-4")
    MCP_API_KEY: str = os.getenv("MCP_API_KEY", "")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
