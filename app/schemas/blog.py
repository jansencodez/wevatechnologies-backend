from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field


class BlogSchema(BaseModel):
    title: str
    description: str
    content: str
    category: str
    tags: List[str] = []
    status: str = Field(..., pattern="^(draft|published|archived)$")
    slug: str
    link: Optional[str] = None
    images: List[str] = []

class BlogResponseSchema(BlogSchema):
    id: str
    created_at: datetime
    updated_at: datetime|None

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }
