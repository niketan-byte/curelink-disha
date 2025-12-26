"""
User Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class OnboardingStateResponse(BaseModel):
    """Onboarding state response."""
    completed: bool
    current_step: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation request - no fields required, generates UUID."""
    pass


class UserUpdate(BaseModel):
    """User update request."""
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = Field(None, max_length=20)
    health_goals: Optional[List[str]] = None
    known_conditions: Optional[List[str]] = None


class UserResponse(BaseModel):
    """User response."""
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    health_goals: List[str] = Field(default_factory=list)
    known_conditions: List[str] = Field(default_factory=list)
    onboarding: OnboardingStateResponse
    created_at: datetime
    last_active_at: datetime
    
    class Config:
        from_attributes = True
