import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings

async def reset_user():
    try:
        settings = get_settings()
        # User's phone number as ID
        USER_ID = "919039456792" 
        
        print(f"Connecting to DB: {settings.mongodb_url}...", flush=True)
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        print(f"Resetting user {USER_ID}...", flush=True)
        
        # Delete User
        result = await db.users.delete_one({"id": USER_ID})
        print(f"Users Deleted: {result.deleted_count}", flush=True)
        
        # Delete Messages
        msg_result = await db.messages.delete_many({"user_id": USER_ID})
        print(f"Messages Deleted: {msg_result.deleted_count}", flush=True)
        
        # Delete Memories
        mem_result = await db.memories.delete_many({"user_id": USER_ID})
        print(f"Memories Deleted: {mem_result.deleted_count}", flush=True)
        
        print("User state completely wiped. Next message will trigger Onboarding Step 1.", flush=True)

    except Exception as e:
        print(f"Script Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(reset_user())
