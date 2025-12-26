"""
LLM Provider Factory
"""
import logging
from functools import lru_cache
from typing import Optional

from app.services.llm.base import LLMProvider
from app.config import get_settings

logger = logging.getLogger(__name__)

# Cache for provider instance
_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider instance.
    
    Uses singleton pattern to reuse the same provider instance.
    
    Returns:
        LLMProvider instance based on configuration
    """
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    settings = get_settings()
    provider_name = settings.llm_provider.lower()
    
    logger.info(f"Initializing LLM provider: {provider_name}")
    
    if provider_name == "gemini":
        from app.services.llm.gemini import GeminiProvider
        _provider_instance = GeminiProvider()
    
    elif provider_name == "openai":
        from app.services.llm.openai_provider import OpenAIProvider
        _provider_instance = OpenAIProvider()
    
    elif provider_name == "azure":
        from app.services.llm.azure_openai import AzureOpenAIProvider
        _provider_instance = AzureOpenAIProvider()
    
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            "Supported providers: gemini, openai, azure"
        )
    
    return _provider_instance


def reset_provider() -> None:
    """Reset the cached provider instance (useful for testing)."""
    global _provider_instance
    _provider_instance = None
