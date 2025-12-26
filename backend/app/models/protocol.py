"""
Protocol Model - Health protocols and policies
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ProtocolCategory(str, Enum):
    """Protocol category enum."""
    SYMPTOM = "SYMPTOM"
    DISEASE = "DISEASE"
    WELLNESS = "WELLNESS"
    POLICY = "POLICY"


class ProtocolSeverity(str, Enum):
    """Protocol severity enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Protocol(BaseModel):
    """Health protocol document model."""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    display_name: str
    category: ProtocolCategory
    keywords: List[str] = Field(default_factory=list)
    keywords_hindi: List[str] = Field(default_factory=list)
    content: str
    severity: ProtocolSeverity = ProtocolSeverity.LOW
    doctor_referral_conditions: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=0)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        data = self.model_dump(exclude={"id"})
        data["category"] = self.category.value
        data["severity"] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Protocol":
        """Create from MongoDB document."""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("category"), str):
            data["category"] = ProtocolCategory(data["category"])
        if isinstance(data.get("severity"), str):
            data["severity"] = ProtocolSeverity(data["severity"])
        return cls(**data)
    
    def get_all_keywords(self) -> List[str]:
        """Get all keywords including Hindi."""
        return self.keywords + self.keywords_hindi
    
    def to_context_string(self) -> str:
        """Convert to string for LLM context."""
        return f"## {self.display_name}\n{self.content}"
