from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.schemas.message import MessageCreate, MessageResponse
from app.crud.message import create_message, get_messages, delete_message

router = APIRouter()

# Route to create a new message
@router.post("/", response_model=MessageResponse)
async def send_message(message: MessageCreate):
    return await create_message(message)

# Route to get all messages
@router.get("/", response_model=List[MessageResponse])
async def get_all_messages(limit: int = Query(10), skip: int = Query(0, ge=0)):
    return await get_messages(limit=limit, skip=skip)

# Route to delete a message by ID
@router.delete("/{message_id}")
async def delete_message_route(message_id: str):
    result = await delete_message(message_id)
    if result.get("message") == "Message deleted successfully":
        return result
    raise HTTPException(status_code=404, detail="Message not found")
