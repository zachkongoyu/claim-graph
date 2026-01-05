"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Claim Graph RCM Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/claim_graph.db"
    
    # Logging
    log_level: str = "INFO"
    
    # LLM (for future integration)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
