# app/schemas/insight.py
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class InsightsSchema(BaseModel):
    insight_title: str
    insight_date: datetime
    insight_content: str
    author: str
    images: List[str] = []
    insight_link: Optional[str] = None

class InsightsResponseSchema(InsightsSchema):
    id: str
    created_at: datetime
    updated_at: datetime|None

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }