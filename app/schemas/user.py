from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    role: str = Field("user", description="The role of the user, default is 'user'. Can be 'investor'.")
    is_active: bool = True


class UserData(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    profile_picture: Optional[str]
    bio: Optional[str]
    role: str
class UserResponse(BaseModel):
    user: UserData
    access_token: str
    refresh_token: str
    token_type: str

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str