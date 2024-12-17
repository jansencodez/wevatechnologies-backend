from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import create_user, get_user

router = APIRouter()

# Route to register a new user
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    return await create_user(user)

# Route to get a user by ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(user_id: str):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
