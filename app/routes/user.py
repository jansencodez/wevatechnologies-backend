from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLoginRequest, UserTokensResponse
from app.auth import create_access_token, create_refresh_token, verify_refresh_token, verify_token
from app.crud.user import create_user, get_user_by_email, update_user, authenticate_user, get_user
from app.db.connection import db
from app.utils.cloudinary import upload as cloudinary_upload
from app.utils.cloudinary import delete as cloudinary_delete
from bson import ObjectId
from dotenv import load_dotenv
from app.utils.get_refresh import get_refresh_token_from_cookie

load_dotenv()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# Route to register a new user
@router.post("/register", response_model=UserTokensResponse)
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

@router.post("/login", response_model=UserTokensResponse)
async def login_user(email: str = Form(...), password: str = Form(...)):
    try:
        tokens = await authenticate_user(email, password)
        is_production = os.getenv("ENV", "development") == "production"

        response = JSONResponse(content={
            "access_token": tokens["access_token"],
            "token_type": "bearer"})

        response.set_cookie(
            key="refresh_token", 
            value=tokens["refresh_token"],
            httponly=True, secure=is_production,
            samesite="strict",
            max_age=3600)
        
        return response
    
    except HTTPException as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")


def init_oauth_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS,  # Path to the downloaded Google client secrets file.
        scopes=["openid", "profile", "email"],
        redirect_uri=REDIRECT_URI
    )

@router.get("/google-login")
async def google_login():
    # Initialize OAuth flow
    flow = init_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    return JSONResponse({"authorization_url": authorization_url})

@router.get("/google-callback")
async def google_callback(code: str):
    try:
        # Initialize OAuth flow and fetch token
        flow = init_oauth_flow()  # Same flow object, make sure it's initialized correctly
        flow.fetch_token(
            authorization_response=f"{REDIRECT_URI}?code={code}",
            client_secret=CLIENT_SECRET,
        )

        # Get user info using the access token
        credentials = flow.credentials
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

        # Get the user's info
        user_info = credentials.id_token
        email = user_info.get("email")
        name = user_info.get("name")
        profile_image_url = user_info.get("picture")
        phone = user_info.get("phone_number")

        # Check if the user already exists
        user = await get_user_by_email(email)
        if user:
            # User exists, proceed to login (create new tokens)
            access_token = create_access_token(data={"sub": email})
            refresh_token = create_refresh_token(data={"sub": email})

            response = JSONResponse(content={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            })
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,  # Set secure cookies in production
                samesite="strict",
                max_age=3600
            )
            return response

        # If user doesn't exist, create a new user and log them in
        new_user = UserCreate(
            name=name,
            email=email,
            phone=phone or None,
            profile_picture=profile_image_url or None,
            bio=None
        )

        # Insert the new user into the database
        await db.users_database.users.insert_one(new_user.model_dump())

        # Create tokens for the newly created user
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})

        response = JSONResponse(content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        })
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set secure cookies in production
            samesite="strict",
            max_age=3600
        )

        return response


    except Exception as e:
        raise HTTPException(status_code=400, detail="Google OAuth Error: " + str(e))

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


@router.post("/logout")
async def logout_user(request: Request):
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie(key="refresh_token")
    return response

@router.post("/refresh", response_model=UserTokensResponse)
async def refresh_token(request: Request, refresh_token: str = Depends(get_refresh_token_from_cookie)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    new_access_token = create_access_token({"sub": payload["sub"], "role": payload["role"]})
    return {"access_token": new_access_token}