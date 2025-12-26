"""
Token Counter Utility - Centralized token counting for different providers
"""
import logging
from typing import List, Dict, Any
import tiktoken

logger = logging.getLogger(__name__)

def count_tokens_openai(text: str, model: str = "gpt-4o") -> int:
    """Count tokens using tiktoken for OpenAI models."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens with tiktoken: {e}")
        # Rough approximation: 4 chars per token
        return len(text) // 4

def count_tokens_gemini(text: str) -> int:
    """Approximate token count for Gemini."""
    # Gemini's count_tokens is usually an API call, but we can approximate
    # or use the provider's implementation. For now, we approximate.
    return len(text) // 4

def count_message_tokens(messages: List[Dict[str, Any]], model: str = "gpt-4o") -> int:
    """Count tokens for a list of messages."""
    num_tokens = 0
    for message in messages:
        num_tokens += 3  # For every message
        for key, value in message.items():
            if isinstance(value, str):
                num_tokens += count_tokens_openai(value, model)
    num_tokens += 3  # For every response
    return num_tokens
