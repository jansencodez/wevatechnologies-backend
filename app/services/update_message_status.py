from bson import ObjectId
from app.db.connection import db
from fastapi import HTTPException

async def update_message_status(message_id: str, read: bool):
    try:
        # Convert message_id to ObjectId
        object_id = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    # Update the message in the database
    result = await db.messages_database.messages.update_one(
        {"_id": object_id},  # Match the message by ObjectId
        {"$set": {"read": read}}  # Update the "read" status
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update message status")