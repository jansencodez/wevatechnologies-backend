from pydantic import BaseModel, HttpUrl
from typing import List

class ServiceCreate(BaseModel):
    title: str
    imageUrls: List[str] = [] # List of image URLs
    description: str

    class Config:
        orm_mode = True


class ServiceResponse(BaseModel):
    id: str
    title: str
    imageUrls: List[str] = []
    description: str

    
    class Config:
        orm_mode = True
