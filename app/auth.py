import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Use the JWT_SECRET_KEY from the environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Refresh token expiration time

# Create a password context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token with expiration date.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    Create a JWT refresh token with a longer expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    """
    Generate a hashed password using bcrypt.
    """
    return pwd_context.hash(password)

def verify_token(token: str):
    """
    Verify the access token and return the decoded payload if valid.
    If the token is expired or invalid, return None.
    """
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Convert the exp timestamp to an offset-aware datetime
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if datetime.now(timezone.utc) > exp_datetime:
            return None
        return payload
    except pyjwt.PyJWTError:
        return None

def verify_refresh_token(token: str):
    """
    Verify the refresh token and return the decoded payload if valid.
    If the refresh token is expired or invalid, return None.
    """
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Convert the exp timestamp to an offset-aware datetime
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if datetime.now(timezone.utc) > exp_datetime:
            return None
        return payload
    except pyjwt.PyJWTError:
        return None
