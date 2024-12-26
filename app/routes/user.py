from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLoginRequest
from app.auth import create_access_token, create_refresh_token, verify_token
from app.crud.user import create_user, get_user_by_email, update_user, authenticate_user, get_user
from app.db.connection import db
from app.utils.cloudinary import upload as cloudinary_upload
from app.utils.cloudinary import delete as cloudinary_delete
from bson import ObjectId

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# Route to register a new user
@router.post("/register", response_model=UserResponse)
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(None),
    profile_picture: UploadFile = File(None),
    bio: str = Form(None),
    is_active: bool = Form(True),
):
    existing_user = await db.users_database.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    if profile_picture:
        if profile_picture.content_type.startswith("image/"):
            result = cloudinary_upload(profile_picture.file)
            image_url = result.get("secure_url")
            profile_picture = image_url
        else:
            raise HTTPException(status_code=400, detail="Invalid profile picture format")

    user_data = UserCreate(
        name=name,
        email=email,
        password=password,
        phone=phone,
        profile_picture=profile_picture,
        bio=bio,
        is_active=is_active,
    )
    user = await create_user(user_data)

    access_token = create_access_token(data={"sub": user["email"]})
    refresh_token = create_refresh_token(data={"sub": user["email"]})

    return {
        "user": {**user},
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# Route to get a user by ID
@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    user = await get_user_by_email(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



# Route to update a user
@router.put("/details/{user_id}", response_model=UserResponse)
async def update_user_route(
    user_id: str,
    name: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    phone: str = Form(None),
    profile_picture: UploadFile = File(None),
    bio: str = Form(None),
):
    # Fetch the existing user data
    existing_user = await get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_picture_url = None
    if profile_picture:
        if profile_picture.content_type.startswith("image/"):
            if existing_user["profile_picture"]:
                # Delete the existing profile picture from Cloudinary
                try:
                    cloudinary_delete(existing_user["profile_picture"].split("/")[-1].split(".")[0])
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error deleting profile picture: {str(e)}")
            
            result = cloudinary_upload(profile_picture.file)
            profile_picture_url = result.get("secure_url")



        else:
            raise HTTPException(status_code=400, detail="Invalid profile picture format")


    # Update only the provided fields
    user_data = UserCreate(
        name=name if name is not None else existing_user["name"],
        email=email if email is not None else existing_user["email"],
        password=password if password is not None else existing_user["password"],
        phone=phone if phone is not None else existing_user["phone"],
        profile_picture=profile_picture_url if profile_picture_url is not None else existing_user["profile_picture"],
        bio=bio if bio is not None else existing_user["bio"],
    )
    updated_user = await update_user(user_id, user_data)
    return updated_user

@router.post("/login")
async def login_user(email: str = Form(...), password: str = Form(...)):
    try:
        tokens = await authenticate_user(email, password)
        return tokens
    except HTTPException as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.delete("/{user_id}", response_model=dict)
async def delete_user_route(user_id: str):
    try:
        user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    existing_user = await get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.users_database.users.delete_one({"_id": user_id})
    
    if existing_user.get("profile_picture"):
        cloudinary_delete(existing_user["profile_picture"].split("/")[-1].split(".")[0])

    if result.deleted_count == 1:
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")