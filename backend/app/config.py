"""
Curelink Mini AI Health Coach - Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    database_name: str = Field(default="curelink_health_coach")
    
    # LLM Provider: "gemini", "openai", or "azure"
    llm_provider: str = Field(default="gemini")
    
    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-2.0-flash-exp")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    
    # Azure OpenAI
    azure_openai_api_key: Optional[str] = Field(default=None)
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_deployment: Optional[str] = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-02-15-preview")
    
    # LLM Settings
    max_context_tokens: int = Field(default=8000)
    llm_timeout_seconds: int = Field(default=30)
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=10)
    
    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    
    # Environment
    environment: str = Field(default="development")

    # WhatsApp Business API
    wa_access_token: Optional[str] = Field(default=None)
    wa_phone_number_id: Optional[str] = Field(default=None)
    wa_verify_token: Optional[str] = Field(default=None)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
