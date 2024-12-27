import asyncio
from db.connection import db

async def update_messages():
    # Connect to the MongoDB database
    result = await db.messages_database.messages.update_many(
        {"read": {"$exists": False}},
        {"$set": {"read": False}}
    )

    # Print the result of the update operation
    print(f"Matched {result.matched_count} documents and modified {result.modified_count} documents.")

# Run the update function in an asynchronous context
asyncio.run(update_messages())