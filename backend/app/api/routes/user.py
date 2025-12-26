"""
User Routes
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.database import get_users_collection
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=UserResponse)
async def create_user(request: UserCreate = None):
    """
    Create a new user session.
    Returns existing user if user_id provided, otherwise creates new.
    """
    collection = get_users_collection()
    
    # Generate new user ID
    user_id = str(uuid.uuid4())
    
    # Create new user
    user = User(user_id=user_id)
    await collection.insert_one(user.to_dict())
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        health_goals=user.health_goals,
        known_conditions=user.known_conditions,
        onboarding=user.onboarding.model_dump(),
        created_at=user.created_at,
        last_active_at=user.last_active_at,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user by ID.
    """
    collection = get_users_collection()
    
    doc = await collection.find_one({"user_id": user_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = User.from_dict(doc)
    
    # Update last active
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_active_at": datetime.now(timezone.utc)}}
    )
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        health_goals=user.health_goals,
        known_conditions=user.known_conditions,
        onboarding=user.onboarding.model_dump(),
        created_at=user.created_at,
        last_active_at=user.last_active_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, request: UserUpdate):
    """
    Update user profile.
    """
    collection = get_users_collection()
    
    # Check if user exists
    doc = await collection.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if request.name is not None:
        updates["name"] = request.name
    if request.age is not None:
        updates["age"] = request.age
    if request.gender is not None:
        updates["gender"] = request.gender
    if request.health_goals is not None:
        updates["health_goals"] = request.health_goals
    if request.known_conditions is not None:
        updates["known_conditions"] = request.known_conditions
    
    await collection.update_one(
        {"user_id": user_id},
        {"$set": updates}
    )
    
    # Get updated user
    doc = await collection.find_one({"user_id": user_id})
    user = User.from_dict(doc)
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        age=user.age,
        gender=user.gender,
        health_goals=user.health_goals,
        known_conditions=user.known_conditions,
        onboarding=user.onboarding.model_dump(),
        created_at=user.created_at,
        last_active_at=user.last_active_at,
    )
