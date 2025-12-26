"""
Input Validators
"""
import re
import html
from typing import Optional


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Trim whitespace
    text = text.strip()
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    return text


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID format.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        True if valid
    """
    if not user_id:
        return False
    
    # UUID format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    return bool(re.match(uuid_pattern, user_id.lower()))


def validate_message_content(content: str, max_length: int = 5000) -> tuple:
    """
    Validate message content.
    
    Args:
        content: Message content
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content:
        return False, "Message cannot be empty"
    
    content = content.strip()
    
    if len(content) == 0:
        return False, "Message cannot be empty"
    
    if len(content) > max_length:
        return False, f"Message too long. Maximum {max_length} characters allowed."
    
    return True, None


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
