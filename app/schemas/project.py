from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by:Optional[str] = None
    updated_by:Optional[str] = None
    updated_at:Optional[datetime] = None
    status: Optional[str] = "Not Started"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at:Optional[datetime] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    updated_at:Optional[datetime] = None
    status: Optional[str] = None
    completion_percentage:Optional[float] = None

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }