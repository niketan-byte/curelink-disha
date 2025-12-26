"""
Chat Orchestrator Service - Main orchestration for chat flow
"""
import logging
import time
import re
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from bson import ObjectId

from app.database import get_messages_collection, get_users_collection
from app.models.user import User, OnboardingState
from app.models.message import Message, MessageRole, MessageMetadata
from app.services.llm import get_llm_provider
from app.services.memory_manager import MemoryManager
from app.services.protocol_matcher import ProtocolMatcher
from app.services.context_builder import ContextBuilder
from app.api.routes.websocket import send_typing_indicator
from app.services.onboarding import OnboardingService

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """
    Main orchestrator for the chat flow.
    Coordinates LLM, memory, protocol matching, and context building.
    """
    
    def __init__(self):
        self.messages_collection = get_messages_collection()
        self.users_collection = get_users_collection()
        self.memory_manager = MemoryManager()
        self.protocol_matcher = ProtocolMatcher()
        self.context_builder = ContextBuilder()
    
    async def process_message(
        self,
        user_id: str,
        content: str,
    ) -> Tuple[Message, Message]:
        """
        Process a user message and generate AI response.
        
        Args:
            user_id: User ID
            content: User's message content
            
        Returns:
            Tuple of (user_message, assistant_message)
        """
        start_time = time.time()
        
        # Check for emergency keywords first
        emergency_response = self._check_emergency(content)
        if emergency_response:
            user_message = await self._save_message(
                user_id=user_id,
                role=MessageRole.USER,
                content=content,
            )
            assistant_message = await self._save_message(
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=emergency_response,
            )
            return user_message, assistant_message

        # Get or create user
        user = await self._get_or_create_user(user_id)
        
        # Save user message
        user_message = await self._save_message(
            user_id=user_id,
            role=MessageRole.USER,
            content=content,
        )
        
        # Broadcast typing indicator
        await send_typing_indicator(user_id, True)
        
        # Check if in onboarding
        if not user.onboarding.completed:
            response_content, protocol_matched, options = await self._handle_onboarding(
                user=user,
                user_input=content,
            )
        else:
            response_content, protocol_matched, options = await self._handle_chat(
                user=user,
                user_input=content,
            )
        
        # Stop typing indicator
        await send_typing_indicator(user_id, False)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save assistant message
        assistant_message = await self._save_message(
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_content,
            options=options,
            metadata=MessageMetadata(
                protocol_matched=protocol_matched,
                response_time_ms=response_time_ms,
                model_used=get_llm_provider().get_model_name(),
            ),
        )
        
        # Extract and store memories (async, don't wait)
        if user.onboarding.completed and len(content) > 20:
            try:
                memories_extracted = await self.memory_manager.extract_and_store_memories(
                    user_id=user_id,
                    user_message=content,
                    assistant_message=response_content,
                    source_message_id=user_message.id,
                )
                if memories_extracted > 0:
                    # Update metadata
                    await self.messages_collection.update_one(
                        {"_id": ObjectId(assistant_message.id)},
                        {"$set": {"metadata.memories_extracted": memories_extracted}}
                    )
                    assistant_message.metadata.memories_extracted = memories_extracted
            except Exception as e:
                logger.error(f"Memory extraction failed: {e}")
        
        # Update user last active
        await self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active_at": datetime.utcnow()}}
        )
        
        return user_message, assistant_message
    
    async def _handle_onboarding(
        self,
        user: User,
        user_input: str,
    ) -> Tuple[str, Optional[str]]:
        """Handle onboarding conversation flow."""
        current_step = user.onboarding.current_step
        
        # 1. Update progress based on user's last input
        success = await self._update_onboarding_progress(user, current_step, user_input)
        
        # 2. Get latest user state (crucial after update)
        updated_user = await self._get_or_create_user(user.user_id)
        
        # 3. Build prompts
        system_prompt = self.context_builder.build_system_prompt(user=updated_user)
        
        # Determine the contextual onboarding instruction
        current_onboarding_step = updated_user.onboarding.current_step
        
        # SPECIAL CASE: If name is still missing, force name step
        if not updated_user.name:
            current_onboarding_step = 1
            
        if not success and current_step > 0 and current_onboarding_step == current_step:
            onboarding_context = self.context_builder.build_onboarding_context(
                step=current_step,
                user=updated_user,
                user_input=user_input,
            )
            onboarding_context += f"\n\n**IMPORTANT**: The user's response was: \"{user_input}\". This did NOT contain the required information for the current step. Acknowledge what they said (if relevant) but politely ask for the missing details again."
        else:
            onboarding_context = self.context_builder.build_onboarding_context(
                step=current_onboarding_step,
                user=updated_user,
                user_input=user_input,
            )
            onboarding_context += f"\n\n**CONTEXT**: The user's last message was: \"{user_input}\". Move the conversation forward naturally based on the latest user profile and the current onboarding step instructions above."
            
        full_prompt = system_prompt + onboarding_context
        
        # 4. Get recent history for context
        chat_history = await self._get_recent_messages(user.user_id, limit=10)
        
        # 5. Build messages list for LLM
        messages = self.context_builder.build_messages(
            system_prompt=full_prompt,
            chat_history=chat_history,
            current_message=user_input if current_step > 0 else None,
        )
        
        # 6. Generate AI response
        llm = get_llm_provider()
        response = await llm.generate(messages=messages, temperature=0.7)
        
        # 7. Parse response for options
        options = []
        cta_matches = re.findall(r'\[CTA: (.*?)\]', response.content)
        if cta_matches:
            options = [m.strip() for m in cta_matches]
            response_content = re.sub(r'\[CTA: .*?\]', '', response.content).strip()
        else:
            response_content = response.content
            
        return response_content, None, options
    
    async def _update_onboarding_progress(
        self,
        user: User,
        current_step: int,
        user_input: str,
    ) -> bool:
        """
        Update user data based on onboarding step with 'Greedy Extraction'.
        Scans for all possible info regardless of the current step.
        """
        updates = {}
        
        # 1. Greedy Extraction: Try to find ANY info in the user_input
        name = OnboardingService.extract_name(user_input)
        if name and not user.name:
            updates["name"] = name
            
        gender = OnboardingService.extract_gender(user_input)
        if gender and not user.gender:
            updates["gender"] = gender
            
        age = OnboardingService.extract_age(user_input)
        if age and not user.age:
            updates["age"] = age
            
        goals = OnboardingService.extract_goals(user_input)
        # Only update goals if they aren't 'general wellness' (default) or if user specifically mentioned something
        if goals and (not user.health_goals or goals[0] != "general wellness"):
            updates["health_goals"] = goals
            
        weight, height = OnboardingService.extract_weight_height(user_input)
        if weight: updates["weight_kg"] = weight
        if height: updates["height_cm"] = height

        # 2. State Machine Logic: Decide if the CURRENT step's requirement was met
        # We re-fetch these from updates or existing user to check completion
        current_name = updates.get("name", user.name)
        current_gender = updates.get("gender", user.gender)
        current_age = updates.get("age", user.age)
        current_goals = updates.get("health_goals", user.health_goals)
        current_weight = updates.get("weight_kg", user.weight_kg)
        current_height = updates.get("height_cm", user.height_cm)

        # Logic to determine next step based on what's MISSING (force Name first)
        if not current_name:
            next_step = 1  # ask name
        elif not current_gender:
            next_step = 2
        elif not current_age:
            next_step = 3
        elif not current_goals or (len(current_goals) == 1 and current_goals[0] == "general wellness") or (len(current_goals) == 1 and current_goals[0] == "other_custom"):
            # Stay on goal step if we only got 'other' or nothing meaningful; ask for custom goal
            next_step = 4
        elif any(g in ["weight loss", "muscle gain", "pcos management"] for g in current_goals) and (not current_weight or not current_height):
            next_step = 5
        else:
            # Everything we need is collected
            next_step = 6
            updates["onboarding.completed"] = True
            updates["onboarding.completed_at"] = datetime.now(timezone.utc)

        # 3. Determine Success
        # A step is 'successful' if the next_step is greater than the current_step
        # or if info for the current step was provided.
        success = True
        if current_step == 0 and not current_name: success = False  # first interaction must gather name
        if current_step == 1 and not current_name: success = False
        if current_step == 2 and not current_gender: success = False
        if current_step == 3 and not current_age: success = False
        if current_step == 5 and (not current_weight or not current_height): success = False

        # Only advance step when successful; otherwise stay on current step to retry
        if success:
            updates["onboarding.current_step"] = next_step
        else:
            updates["onboarding.current_step"] = current_step
        updates["updated_at"] = datetime.utcnow()
        
        await self.users_collection.update_one(
            {"user_id": user.user_id},
            {"$set": updates}
        )
        return success
    
    
    async def _handle_chat(
        self,
        user: User,
        user_input: str,
    ) -> Tuple[str, Optional[str]]:
        """Handle regular chat (post-onboarding)."""
        
        # Get memories context
        memories_context = await self.memory_manager.get_memories_context(user.user_id)
        
        # Get protocols context
        protocols_context = await self.protocol_matcher.get_protocols_context(user_input)
        
        # Get matched protocol name for metadata
        matched_protocols = await self.protocol_matcher.match_protocols(user_input, max_matches=1)
        protocol_matched = matched_protocols[0].name if matched_protocols else None
        
        # Build system prompt
        system_prompt = self.context_builder.build_system_prompt(
            user=user,
            memories_context=memories_context,
            protocols_context=protocols_context,
        )
        
        # Get recent messages
        chat_history = await self._get_recent_messages(user.user_id, limit=50)
        
        # Build messages with sliding window
        messages = self.context_builder.build_messages(
            system_prompt=system_prompt,
            chat_history=chat_history,
            current_message=user_input,
        )
        
        # Generate response
        llm = get_llm_provider()
        response = await llm.generate(messages=messages, temperature=0.7)
        
        # Parse options
        options = []
        cta_matches = re.findall(r'\[CTA: (.*?)\]', response.content)
        if cta_matches:
            options = [m.strip() for m in cta_matches]
            response_content = re.sub(r'\[CTA: .*?\]', '', response.content).strip()
        else:
            response_content = response.content
            
        return response_content, protocol_matched, options
    
    def _check_emergency(self, text: str) -> Optional[str]:
        """Check for emergency keywords and return a standard response if found."""
        emergency_keywords = [
            "chest pain", "difficulty breathing", "heart attack", "stroke", 
            "unconscious", "heavy bleeding", "suicide", "self-harm", "kill myself",
            "poison", "emergency", "ambulance", "accident"
        ]
        
        text_lower = text.lower()
        if any(kw in text_lower for kw in emergency_keywords):
            return (
                "🚨 **EMERGENCY NOTICE** 🚨\n\n"
                "I am an AI coach, not a doctor. This sounds like a medical emergency. "
                "Please stop using this chat and immediately:\n"
                "1. **Call 102 or 108** (Ambulance) in India.\n"
                "2. Visit the **nearest hospital emergency room**.\n"
                "3. Contact a family member or friend.\n\n"
                "Your safety is the priority. Please get professional help now."
            )
        return None

    async def _get_or_create_user(self, user_id: str) -> User:
        """Get existing user or create new one."""
        doc = await self.users_collection.find_one({"user_id": user_id})
        
        if doc:
            return User.from_dict(doc)
        
        # Create new user
        user = User(user_id=user_id)
        await self.users_collection.insert_one(user.to_dict())
        
        logger.info(f"Created new user: {user_id}")
        
        return user
    
    async def _save_message(
        self,
        user_id: str,
        role: MessageRole,
        content: str,
        options: Optional[list[str]] = None,
        metadata: Optional[MessageMetadata] = None,
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            user_id=user_id,
            role=role,
            content=content,
            options=options,
            metadata=metadata or MessageMetadata(),
        )
        
        result = await self.messages_collection.insert_one(message.to_dict())
        message.id = str(result.inserted_id)
        
        return message
    
    async def _get_recent_messages(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list:
        """Get recent messages for a user."""
        cursor = self.messages_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", 1).limit(limit)
        
        messages = []
        async for doc in cursor:
            messages.append(Message.from_dict(doc))
        
        return messages
    
    async def get_messages_paginated(
        self,
        user_id: str,
        before_id: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[list, bool, Optional[str]]:
        """
        Get paginated messages (cursor-based).
        
        Args:
            user_id: User ID
            before_id: Get messages before this ID (for loading older)
            limit: Maximum messages to return
            
        Returns:
            Tuple of (messages, has_more, next_cursor)
        """
        query = {"user_id": user_id}
        
        if before_id:
            query["_id"] = {"$lt": ObjectId(before_id)}
        
        # Get one extra to check if there are more
        cursor = self.messages_collection.find(query).sort("_id", -1).limit(limit + 1)
        
        messages = []
        async for doc in cursor:
            if len(messages) < limit:
                messages.append(Message.from_dict(doc))
        
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]
        
        # Reverse to get chronological order
        messages.reverse()
        
        next_cursor = messages[0].id if messages and has_more else None
        
        return messages, has_more, next_cursor
    
    async def get_latest_messages(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list:
        """Get the most recent messages."""
        cursor = self.messages_collection.find(
            {"user_id": user_id}
        ).sort("_id", -1).limit(limit)
        
        messages = []
        async for doc in cursor:
            messages.append(Message.from_dict(doc))
        
        # Reverse to get chronological order
        messages.reverse()
        
        return messages
