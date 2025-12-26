"""
User Model
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import IntEnum


class OnboardingStep(IntEnum):
    """Onboarding step enum."""
    NOT_STARTED = 0
    NAME_COLLECTED = 1
    GENDER_COLLECTED = 2
    AGE_COLLECTED = 3
    GOALS_COLLECTED = 4
    DIAGNOSTIC_COLLECTED = 5
    COMPLETED = 6


class OnboardingState(BaseModel):
    """User onboarding state."""
    completed: bool = False
    current_step: int = Field(default=0, ge=0, le=6)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class UserPreferences(BaseModel):
    """User preferences."""
    language: str = "en"
    notification_time: Optional[str] = None


class User(BaseModel):
    """User document model."""
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    health_goals: List[str] = Field(default_factory=list)
    known_conditions: List[str] = Field(default_factory=list)
    onboarding: OnboardingState = Field(default_factory=OnboardingState)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create from MongoDB document."""
        return cls(**data)
    
    def get_profile_summary(self) -> str:
        """Get a summary of user profile for LLM context."""
        parts = []
        
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.age:
            parts.append(f"Age: {self.age}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.weight_kg:
            parts.append(f"Weight: {self.weight_kg}kg")
        if self.height_cm:
            parts.append(f"Height: {self.height_cm}cm")
        if self.health_goals:
            parts.append(f"Health Goals: {', '.join(self.health_goals)}")
        if self.known_conditions:
            parts.append(f"Known Conditions: {', '.join(self.known_conditions)}")
        
        if not parts:
            return "No profile information available yet."
        
        return "\n".join(parts)
