"""
Configuration management for TED Bot.

Loads environment variables and provides typed configuration.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    api_key: str = Field(default="", alias="API_KEY")
    
    # TED API
    ted_api_url: str = Field(..., alias="TED_API_URL")
    ted_api_key: str = Field(default="", alias="TED_API_KEY")  # Optional
    
    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    
    # Ollama Cloud
    ollama_api_url: str = Field(..., alias="OLLAMA_API_URL")
    ollama_api_key: str = Field(..., alias="OLLAMA_API_KEY")
    ollama_chat_model: str = Field(default="llama3.1", alias="OLLAMA_CHAT_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")
    ollama_verify_ssl: bool = Field(default=True, alias="OLLAMA_VERIFY_SSL")
    
    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields (like frontend env vars)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
