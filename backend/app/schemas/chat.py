"""
Chat Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.message import MessageResponse, MessageMetadataResponse


class ChatRequest(BaseModel):
    """Chat message request."""
    user_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    """Chat response with both user and assistant messages."""
    user_message: MessageResponse
    assistant_message: MessageResponse
    onboarding_complete: bool = False


class TypingEvent(BaseModel):
    """Typing indicator event."""
    event: str  # "typing_start" or "typing_end"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    database: str = "connected"
    version: str = "1.0.0"
