"""
Curelink Mini AI Health Coach - Database Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

# Global database client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """Initialize MongoDB connection."""
    global _client, _database
    
    settings = get_settings()
    
    try:
        _client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        
        # Verify connection
        await _client.admin.command("ping")
        
        _database = _client[settings.database_name]
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"Connected to MongoDB: {settings.database_name}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def create_indexes() -> None:
    """Create database indexes for optimal performance."""
    global _database
    
    if _database is None:
        return
    
    # Messages collection indexes
    await _database.messages.create_index(
        [("user_id", 1), ("timestamp", -1)],
        name="user_messages_idx"
    )
    await _database.messages.create_index(
        [("user_id", 1), ("_id", -1)],
        name="user_messages_cursor_idx"
    )
    
    # Users collection indexes
    await _database.users.create_index(
        [("user_id", 1)],
        unique=True,
        name="user_id_idx"
    )
    
    # Memories collection indexes
    await _database.memories.create_index(
        [("user_id", 1), ("category", 1)],
        name="user_memories_idx"
    )
    await _database.memories.create_index(
        [("user_id", 1), ("active", 1)],
        name="user_active_memories_idx"
    )
    
    # Protocols collection indexes
    await _database.protocols.create_index(
        [("keywords", 1)],
        name="protocol_keywords_idx"
    )
    await _database.protocols.create_index(
        [("category", 1), ("active", 1)],
        name="protocol_category_idx"
    )
    
    logger.info("Database indexes created")


async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global _client, _database
    
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    global _database
    
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    
    return _database


# Collection helpers
def get_users_collection():
    """Get users collection."""
    return get_database().users


def get_messages_collection():
    """Get messages collection."""
    return get_database().messages


def get_memories_collection():
    """Get memories collection."""
    return get_database().memories


def get_protocols_collection():
    """Get protocols collection."""
    return get_database().protocols
