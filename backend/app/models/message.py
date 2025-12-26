"""
Message Model
"""
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageMetadata(BaseModel):
    """Message metadata."""
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    protocol_matched: Optional[str] = None
    response_time_ms: Optional[int] = None
    memories_extracted: int = 0


class Message(BaseModel):
    """Message document model."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    options: Optional[list[str]] = None
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    
    class Config:
        populate_by_name = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        data = self.model_dump(exclude={"id"})
        data["role"] = self.role.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from MongoDB document."""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("role"), str):
            data["role"] = MessageRole(data["role"])
        return cls(**data)
    
    def to_llm_format(self) -> dict:
        """Convert to format suitable for LLM API."""
        return {
            "role": self.role.value,
            "content": self.content
        }
