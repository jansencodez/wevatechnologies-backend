from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

# Helper to convert ObjectId to string
class MongoBaseModel(BaseModel):
    id: str

    class Config:
        # Automatically convert ObjectId to string
        json_encoders = {
            ObjectId: str
        }

# Model for creating a new admin
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    role: str = Field("admin", description="The role of the user, default is 'admin'. Can be 'superadmin'.")

    class Config:
        orm_mode = True

# Response model for returning admin information
class AdminResponse(MongoBaseModel):
    name: str
    email: EmailStr
    phone: str
    role: str  # Include role in the response

    class Config:
        orm_mode = True

# Request model for admin login
class AdminLoginRequest(BaseModel):
    email: str
    password: str
