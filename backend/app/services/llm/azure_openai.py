"""
Azure OpenAI LLM Provider
"""
import logging
from typing import List, Dict, Optional

from openai import AsyncAzureOpenAI
import tiktoken

from app.services.llm.base import LLMProvider, LLMResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""
    
    def __init__(self):
        settings = get_settings()
        
        if not settings.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required for Azure provider")
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure provider")
        if not settings.azure_openai_deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is required for Azure provider")
        
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.deployment = settings.azure_openai_deployment
        self.timeout = settings.llm_timeout_seconds
        
        # Initialize tokenizer (cl100k_base works for most Azure deployments)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Initialized Azure OpenAI provider with deployment: {self.deployment}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response using Azure OpenAI."""
        try:
            # Handle newer models that require max_completion_tokens instead of max_tokens
            completion_args = {
                "model": self.deployment,
                "messages": messages,
                "temperature": temperature,
                "timeout": self.timeout,
            }
            
            # Newer models (like o1 or newer Azure deployments) might prefer max_completion_tokens
            if "o1" in self.deployment.lower() or "gpt-5" in self.deployment.lower():
                completion_args["max_completion_tokens"] = max_tokens or 1024
            else:
                completion_args["max_tokens"] = max_tokens or 1024

            response = await self.client.chat.completions.create(**completion_args)
            
            content = response.choices[0].message.content or ""
            
            tokens_used = None
            if response.usage:
                tokens_used = response.usage.total_tokens
            
            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self.deployment,
                finish_reason=response.choices[0].finish_reason,
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI generation error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def get_model_name(self) -> str:
        """Get the deployment name."""
        return self.deployment
