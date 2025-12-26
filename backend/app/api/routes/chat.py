"""
Chat Routes
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.message import MessageResponse, MessageListResponse, MessageMetadataResponse
from app.services.chat_orchestrator import ChatOrchestrator
from app.database import get_users_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["Chat"])


def _message_to_response(message) -> MessageResponse:
    """Convert Message model to MessageResponse schema."""
    return MessageResponse(
        id=message.id,
        role=message.role.value,
        content=message.content,
        timestamp=message.timestamp,
        options=message.options,
        metadata=MessageMetadataResponse(
            protocol_matched=message.metadata.protocol_matched,
            memories_extracted=message.metadata.memories_extracted,
        ) if message.metadata else None,
    )


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response.
    
    This is the main chat endpoint. It:
    1. Saves the user message
    2. Generates AI response using LLM
    3. Optionally matches health protocols
    4. Extracts and stores long-term memories
    5. Returns both messages
    """
    # Validate content
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    
    if len(content) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Message too long. Please keep messages under 5000 characters."
        )
    
    try:
        orchestrator = ChatOrchestrator()
        
        user_message, assistant_message = await orchestrator.process_message(
            user_id=request.user_id,
            content=content,
        )
        
        # Check onboarding status
        users_collection = get_users_collection()
        user_doc = await users_collection.find_one({"user_id": request.user_id})
        onboarding_complete = user_doc.get("onboarding", {}).get("completed", False) if user_doc else False
        
        return ChatResponse(
            user_message=_message_to_response(user_message),
            assistant_message=_message_to_response(assistant_message),
            onboarding_complete=onboarding_complete,
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble responding right now. Please try again."
        )


@router.get("", response_model=MessageListResponse)
async def get_messages(
    user_id: str = Query(..., description="User ID"),
    before: Optional[str] = Query(None, description="Get messages before this ID (cursor)"),
    limit: int = Query(20, ge=1, le=100, description="Number of messages to return"),
):
    """
    Get paginated message history (cursor-based).
    
    Use this for infinite scroll - pass the oldest message ID as 'before'
    to load older messages.
    """
    try:
        orchestrator = ChatOrchestrator()
        
        messages, has_more, next_cursor = await orchestrator.get_messages_paginated(
            user_id=user_id,
            before_id=before,
            limit=limit,
        )
        
        return MessageListResponse(
            messages=[_message_to_response(m) for m in messages],
            has_more=has_more,
            next_cursor=next_cursor,
        )
        
    except Exception as e:
        logger.error(f"Get messages error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load messages")


@router.get("/latest", response_model=MessageListResponse)
async def get_latest_messages(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
):
    """
    Get the most recent messages.
    
    Use this for initial page load to get the latest conversation.
    """
    try:
        orchestrator = ChatOrchestrator()
        
        messages = await orchestrator.get_latest_messages(
            user_id=user_id,
            limit=limit,
        )
        
        return MessageListResponse(
            messages=[_message_to_response(m) for m in messages],
            has_more=len(messages) >= limit,
            next_cursor=messages[0].id if messages else None,
        )
        
    except Exception as e:
        logger.error(f"Get latest messages error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load messages")
