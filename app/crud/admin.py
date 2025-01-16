from fastapi import HTTPException
from app.db.connection import db
from app.schemas.admin import AdminCreate, AdminResponse
from bson import ObjectId
from app.auth import create_access_token, get_password_hash, verify_password, create_refresh_token
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to fetch a message by its ID from the database
async def get_message_by_id(message_id: str, collection=db.messages_database.messages):
    try:
        # Ensure the message_id is a valid ObjectId
        message_id = ObjectId(message_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    message = await collection.find_one({"_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

# Create a new admin
async def create_admin(admin: AdminCreate):
    hashed_password = get_password_hash(admin.password)
    admin_dict = admin.model_dump()
    admin_dict["password"] = hashed_password

    # Insert the new admin into the database
    result = await db.admins_database.admins.insert_one(admin_dict)
    admin_dict["id"] = str(result.inserted_id)
    del admin_dict["_id"]

    return admin_dict

# Get an admin by email
async def get_admin_by_email(email: str):
    # Fetch the admin document from the database
    admin = await db.admins_database.admins.find_one({"email": email})
    
    if admin:
        admin["id"] = str(admin["_id"]) 
        return AdminResponse(**admin)  
        
    return None

# Authenticate admin and return a JWT token
async def authenticate_admin(email: str, password: str):
    # Fetch raw admin data from the database
    admin_data = await db.admins_database.admins.find_one({"email": email})
    
    if admin_data:
        # Verify the password
        if verify_password(password, admin_data["password"]):  # Access the password from raw admin_data
            # Convert _id to string and add it to admin_data as 'id'
            admin_data["id"] = str(admin_data["_id"])
            # Remove the _id field to avoid duplication with 'id'
            del admin_data["_id"]
            
            # Create an access token
            refresh_token = create_refresh_token(data={
                "sub": admin_data["email"],
                "role": admin_data["role"],
            })

            access_token = create_access_token(data={
                "sub": admin_data["email"],
                "role": admin_data["role"],
            })
            
            # Return only the access token with token type
            return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    
    # If admin not found or password is incorrect, raise an error
    raise HTTPException(status_code=401, detail="Invalid credentials")