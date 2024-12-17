from app.db.connection import db
from app.schemas.user import UserCreate
from bson import ObjectId
from passlib.context import CryptContext

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Create a new user
async def create_user(user: UserCreate):
    hashed_password = hash_password(user.password)
    user_dict = user.model_dump()
    user_dict["password"] = hashed_password
    result = await db.users_database.users.insert_one(user_dict)
    return {**user_dict, "id": str(result.inserted_id)}

# Get a user by ID
async def get_user(user_id: str):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        return {**user, "id": str(user["_id"])}
    return None
