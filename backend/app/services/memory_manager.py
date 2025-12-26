"""
Memory Manager Service - Mem0-inspired long-term memory management
"""
import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId

from app.database import get_memories_collection
from app.models.memory import Memory, MemoryCategory, memories_to_context
from app.services.llm import get_llm_provider

logger = logging.getLogger(__name__)

# Prompt for extracting memories from conversation
MEMORY_EXTRACTION_PROMPT = """Analyze this conversation and extract important facts about the user that should be remembered long-term.

ONLY extract explicit information that the user has stated. Do NOT infer or assume anything.

Categories:
- HEALTH_CONDITION: Health issues/conditions (e.g., "has diabetes", "high blood pressure", "PCOS")
- ALLERGY: Allergies (e.g., "allergic to peanuts", "lactose intolerant")
- MEDICATION: Medications being taken (e.g., "takes metformin", "on thyroid medication")
- PREFERENCE: Health/lifestyle preferences (e.g., "vegetarian", "prefers morning workouts")
- GOAL: Health goals (e.g., "wants to lose 10kg", "trying to manage stress")
- LIFESTYLE: Lifestyle facts (e.g., "works night shifts", "sedentary job")
- PERSONAL: Personal info (e.g., "name is Rahul", "32 years old")

Conversation:
{conversation}

Return ONLY a valid JSON array. If no facts found, return empty array: []
Format: [{"category": "CATEGORY", "content": "fact about user", "confidence": 0.9}]

Examples of good extractions:
- User says "I have diabetes" → {"category": "HEALTH_CONDITION", "content": "has diabetes", "confidence": 1.0}
- User says "I'm trying to lose weight" → {"category": "GOAL", "content": "wants to lose weight", "confidence": 0.9}
- User says "I take metformin every morning" → {"category": "MEDICATION", "content": "takes metformin daily", "confidence": 1.0}

JSON array:"""


class MemoryManager:
    """
    Mem0-inspired memory manager for extracting and storing long-term user memories.
    """
    
    def __init__(self):
        self.collection = get_memories_collection()
    
    async def get_user_memories(
        self,
        user_id: str,
        categories: Optional[List[MemoryCategory]] = None,
        limit: int = 20,
    ) -> List[Memory]:
        """
        Get active memories for a user.
        
        Args:
            user_id: User ID
            categories: Optional list of categories to filter
            limit: Maximum memories to return
            
        Returns:
            List of Memory objects
        """
        query = {"user_id": user_id, "active": True}
        
        if categories:
            query["category"] = {"$in": [c.value for c in categories]}
        
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        
        memories = []
        async for doc in cursor:
            memories.append(Memory.from_dict(doc))
        
        return memories
    
    async def get_memories_context(self, user_id: str) -> str:
        """
        Get formatted memory context string for LLM.
        
        Args:
            user_id: User ID
            
        Returns:
            Formatted string of memories
        """
        memories = await self.get_user_memories(user_id)
        return memories_to_context(memories)
    
    async def add_memory(
        self,
        user_id: str,
        category: MemoryCategory,
        content: str,
        confidence: float = 1.0,
        source_message_id: Optional[str] = None,
    ) -> Memory:
        """
        Add a new memory for a user.
        
        Args:
            user_id: User ID
            category: Memory category
            content: Memory content
            confidence: Confidence score (0-1)
            source_message_id: Optional source message ID
            
        Returns:
            Created Memory object
        """
        # Check for duplicate
        existing = await self.collection.find_one({
            "user_id": user_id,
            "category": category.value,
            "content": {"$regex": f"^{re.escape(content)}$", "$options": "i"},
            "active": True,
        })
        
        if existing:
            logger.debug(f"Duplicate memory skipped: {content}")
            return Memory.from_dict(existing)
        
        memory = Memory(
            user_id=user_id,
            category=category,
            content=content,
            confidence=confidence,
            source_message_id=source_message_id,
        )
        
        result = await self.collection.insert_one(memory.to_dict())
        memory.id = str(result.inserted_id)
        
        logger.info(f"Added memory for user {user_id}: [{category.value}] {content}")
        
        return memory
    
    async def extract_and_store_memories(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        source_message_id: Optional[str] = None,
    ) -> int:
        """
        Extract memories from a conversation turn and store them.
        
        Args:
            user_id: User ID
            user_message: User's message
            assistant_message: Assistant's response
            source_message_id: Optional message ID for reference
            
        Returns:
            Number of memories extracted
        """
        # Skip short messages
        if len(user_message) < 20:
            return 0
        
        try:
            llm = get_llm_provider()
            
            conversation = f"User: {user_message}\nAssistant: {assistant_message}"
            
            prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation)
            
            response = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
            )
            
            # Parse JSON response
            extracted = self._parse_extraction_response(response.content)
            
            if not extracted:
                return 0
            
            # Store each extracted memory
            count = 0
            for item in extracted:
                try:
                    category = MemoryCategory(item.get("category", "").upper())
                    content = item.get("content", "").strip()
                    confidence = float(item.get("confidence", 0.8))
                    
                    if content and len(content) > 3:
                        await self.add_memory(
                            user_id=user_id,
                            category=category,
                            content=content,
                            confidence=confidence,
                            source_message_id=source_message_id,
                        )
                        count += 1
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid memory item: {item}, error: {e}")
                    continue
            
            return count
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return 0
    
    def _parse_extraction_response(self, response: str) -> List[dict]:
        """Parse LLM response to extract memory items."""
        try:
            # Try to find JSON array in response
            response = response.strip()
            
            # Find JSON array
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start == -1 or end == 0:
                return []
            
            json_str = response[start:end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse memory extraction response: {e}")
            return []
    
    async def deactivate_memory(self, memory_id: str) -> bool:
        """Deactivate a memory (soft delete)."""
        result = await self.collection.update_one(
            {"_id": ObjectId(memory_id)},
            {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0
    
    async def clear_user_memories(self, user_id: str) -> int:
        """Clear all memories for a user (soft delete)."""
        result = await self.collection.update_many(
            {"user_id": user_id, "active": True},
            {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count
