from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union


class EventSchema(BaseModel):
    event_name: str
    event_date: datetime
    event_location: str
    event_description: str
    images: List[str] = []
    event_link: Optional[str] = None

class EventResponseSchema(EventSchema):
    id: str
    created_at: datetime
    updated_at: datetime|None

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }
