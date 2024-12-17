from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class AnnouncementSchema(BaseModel):
    title: str 
    content: str  
    announcement_date: datetime 
    tags: List[str] = []  
    images: List[str] = []  
    link: Optional[str] = None 

class AnnouncementResponseSchema(AnnouncementSchema):
    id: str
    created_at: datetime
    updated_at: datetime|None

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }