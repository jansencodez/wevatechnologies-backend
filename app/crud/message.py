from pymongo import DESCENDING
from app.db.connection import db
from app.schemas.message import MessageCreate
from bson import ObjectId

# Function to create a new message
async def create_message(message: MessageCreate):
    message_dict = message.model_dump()
    result = await db.messages_database.messages.insert_one(message_dict)
    message_dict["created_at"] = str(result.inserted_id.generation_time)
    message_dict["id"] = str(result.inserted_id)
    
    
    return message_dict

# Function to get all messages
async def get_messages(limit: int, skip: int):
    messages_cursor = db.messages_database.messages.find().skip(skip).limit(limit).sort("created_at", DESCENDING)  # Fetch up to 100 messages
    messages = []
    async for message in messages_cursor:
        message["created_at"] = message["_id"].generation_time

        message["id"] = str(message["_id"])
        del message["_id"]

        
        messages.append(message)
    return messages

# Function to delete a message by its ID
async def delete_message(message_id: str):
    result = await db.messages_database.messages.delete_one({"_id": ObjectId(message_id)})
    if result.deleted_count == 1:
        return {"message": "Message deleted successfully"}
    return {"message": "Message not found"}
