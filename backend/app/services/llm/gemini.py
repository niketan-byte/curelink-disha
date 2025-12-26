"""
Google Gemini LLM Provider
"""
import logging
from typing import List, Dict, Optional

from google import genai
from google.genai import types

from app.services.llm.base import LLMProvider, LLMResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self):
        settings = get_settings()
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.timeout = settings.llm_timeout_seconds
        
        logger.info(f"Initialized Gemini provider with model: {self.model}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response using Gemini."""
        try:
            # Convert messages to Gemini format
            gemini_contents = self._convert_messages(messages)
            
            # Extract system instruction if present
            system_instruction = None
            if messages and messages[0].get("role") == "system":
                system_instruction = messages[0].get("content")
            
            # Configure generation
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 1024,
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            # Generate response
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=gemini_contents,
                config=config,
            )
            
            # Extract response text
            content = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    content = "".join(
                        part.text for part in candidate.content.parts if hasattr(part, "text")
                    )
            
            # Get token usage if available
            tokens_used = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used = response.usage_metadata.total_token_count
            
            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self.model,
                finish_reason="stop",
            )
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Convert OpenAI-style messages to Gemini format."""
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Skip system messages (handled separately)
            if role == "system":
                continue
            
            # Map roles
            gemini_role = "user" if role == "user" else "model"
            
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part(text=content)]
                )
            )
        
        return contents
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count for Gemini."""
        # Gemini uses similar tokenization to GPT models
        # Rough approximation: ~4 characters per token
        return len(text) // 4 + 1
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model
