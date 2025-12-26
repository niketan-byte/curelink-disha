"""
Memory Model - Long-term user memories
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class MemoryCategory(str, Enum):
    """Memory category enum."""
    HEALTH_CONDITION = "HEALTH_CONDITION"
    PREFERENCE = "PREFERENCE"
    GOAL = "GOAL"
    MEDICATION = "MEDICATION"
    PERSONAL = "PERSONAL"
    ALLERGY = "ALLERGY"
    LIFESTYLE = "LIFESTYLE"


class Memory(BaseModel):
    """Long-term memory document model."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    category: MemoryCategory
    content: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_message_id: Optional[str] = None
    embedding: Optional[List[float]] = None  # For future semantic search
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        data = self.model_dump(exclude={"id"})
        data["category"] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        """Create from MongoDB document."""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("category"), str):
            data["category"] = MemoryCategory(data["category"])
        return cls(**data)
    
    def to_context_string(self) -> str:
        """Convert to string for LLM context."""
        return f"[{self.category.value}] {self.content}"


def memories_to_context(memories: List[Memory]) -> str:
    """Convert list of memories to context string for LLM."""
    if not memories:
        return "No stored memories for this user."
    
    grouped = {}
    for memory in memories:
        category = memory.category.value
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(memory.content)
    
    parts = []
    for category, items in grouped.items():
        category_name = category.replace("_", " ").title()
        parts.append(f"**{category_name}:**")
        for item in items:
            parts.append(f"  - {item}")
    
    return "\n".join(parts)
