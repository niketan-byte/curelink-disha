"""
Database Seeding Script

Seeds the database with initial protocol data.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_to_mongodb, close_mongodb_connection, get_protocols_collection


async def seed_protocols():
    """Seed protocols from JSON file."""
    # Load protocols from JSON
    protocols_file = Path(__file__).parent.parent / "seeds" / "protocols.json"
    
    if not protocols_file.exists():
        print(f"Error: Protocols file not found at {protocols_file}")
        return False
    
    with open(protocols_file, "r") as f:
        protocols = json.load(f)
    
    print(f"Loaded {len(protocols)} protocols from {protocols_file}")
    
    # Connect to database
    await connect_to_mongodb()
    
    collection = get_protocols_collection()
    
    # Clear existing protocols
    result = await collection.delete_many({})
    print(f"Cleared {result.deleted_count} existing protocols")
    
    # Add created_at to each protocol
    for protocol in protocols:
        protocol["created_at"] = datetime.utcnow()
    
    # Insert protocols
    result = await collection.insert_many(protocols)
    print(f"Inserted {len(result.inserted_ids)} protocols")
    
    # Verify
    count = await collection.count_documents({})
    print(f"Total protocols in database: {count}")
    
    # Close connection
    await close_mongodb_connection()
    
    return True


async def main():
    """Main entry point."""
    print("=" * 50)
    print("Curelink Health Coach - Database Seeding")
    print("=" * 50)
    
    try:
        success = await seed_protocols()
        if success:
            print("\n✅ Database seeding completed successfully!")
        else:
            print("\n❌ Database seeding failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
