"""
Message Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageMetadataResponse(BaseModel):
    """Message metadata response."""
    protocol_matched: Optional[str] = None
    memories_extracted: int = 0


class MessageCreate(BaseModel):
    """Message creation request."""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Message response."""
    id: str
    role: str
    content: str
    timestamp: datetime
    options: Optional[list[str]] = None
    metadata: Optional[MessageMetadataResponse] = None
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    messages: List[MessageResponse]
    has_more: bool
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None
