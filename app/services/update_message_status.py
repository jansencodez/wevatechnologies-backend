from app.db.connection import db
from fastapi import HTTPException

async def update_message_status(message_id: str, read: bool):
    # Example database update logic
    result = await db.messages_database.messages.update_one(
        {"_id": message_id},  # Match the message by ID
        {"$set": {"read": read}}  # Update the "read" status
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update message status")