from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None  # Optional for Google sign-ups
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    googleId: Optional[str] = None  # Google-specific ID
    role: str = Field("user", description="The role of the user, default is 'user'. Can be 'investor'.")
    is_active: bool = True


class UserTokensResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    profile_picture: Optional[str]
    bio: Optional[str]
    role: str
    googleId: Optional[str] = None  # Include Google ID for Google sign-ups

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # Optional for non-password updates
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str
    password: Optional[str] = None  # Optional for Google sign-ups
