from fastapi import HTTPException
from app.db.connection import db
from app.schemas.user import UserCreate
from bson import ObjectId
from app.auth import get_password_hash, verify_password, create_access_token, create_refresh_token

# Create a new user
async def create_user(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["password"] = hashed_password
    result = await db.users_database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    del user_dict["password"]
    del user_dict["_id"]
    
    return {**user_dict}

async def get_user_by_email(email: str):
    user = await db.users_database.users.find_one({"email": email})
    if user:
        return {**user, "id": str(user["_id"])}
    raise HTTPException(status_code=404, detail="User not found")


async def get_user(user_id: str):
    try:
        id = ObjectId(user_id)
    except Exception :
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    user = await db.users_database.users.find_one({"_id": id})
    if user:
        return {**user, "id": str(user["_id"])}
    return {"message": "User not found"}

# Update a user
async def update_user(user_id: str, updated_data: dict):
    user_dict = updated_data.model_dump()
    result = await db.users_database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_dict}
    )
    if result.modified_count == 0:
        return {"message": "Failed to update user"}
    updated_user = await db.users_database.users.find_one({"_id": ObjectId(user_id)})
    return {**updated_user, "id": str(updated_user["_id"])}

# Authenticate user and return access token
async def authenticate_user(email: str, password: str):
    user = await db.users_database.users.find_one({"email": email})
    if user and verify_password(password, user["password"]):
        access_token = create_access_token(data={"sub": user["email"]})
        refresh_token = create_refresh_token(data={"sub": user["email"]})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")

