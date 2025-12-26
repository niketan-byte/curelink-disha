"""
OpenAI LLM Provider
"""
import logging
from typing import List, Dict, Optional

from openai import AsyncOpenAI
import tiktoken

from app.services.llm.base import LLMProvider, LLMResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self):
        settings = get_settings()
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.timeout = settings.llm_timeout_seconds
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base for newer models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Initialized OpenAI provider with model: {self.model}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response using OpenAI."""
        try:
            # Handle newer models that require max_completion_tokens instead of max_tokens
            completion_args = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "timeout": self.timeout,
            }
            
            if "o1" in self.model.lower() or "gpt-5" in self.model.lower():
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
                model=self.model,
                finish_reason=response.choices[0].finish_reason,
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model
