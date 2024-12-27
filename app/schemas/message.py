from bson import ObjectId
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

class MessageCreate(BaseModel):
    name: str
    email: EmailStr
    message: str
    category: str
    read: bool = False


class MessageResponse(MessageCreate):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }
