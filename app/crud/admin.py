from fastapi import BackgroundTasks, HTTPException
from app.db.connection import db
from app.schemas.admin import AdminCreate, AdminResponse
from bson import ObjectId
from app.auth import create_access_token, get_password_hash, verify_password
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
import base64
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variable class to hold mail configurations


def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    """Send email in the background using the Gmail API."""
    background_tasks.add_task(send_email, subject, email_to, body)

def send_email(subject: str, email_to: str, body: dict):
    """Function to send the email using Gmail API."""
    creds, _ = google.auth.default()

    try:
        # Create Gmail API client
        service = build("gmail", "v1", credentials=creds)

        # Create the email message
        message = EmailMessage()
        message.set_content(f"Response to your message:\n\n{body['response_message']}")

        # Set email headers
        message["To"] = email_to
        message["From"] = "me"  # The sender's email, typically "me" for the authenticated user
        message["Subject"] = subject

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the message body for the Gmail API
        create_message = {"raw": encoded_message}
        
        # Send the message
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Message sent: {send_message['id']}")
    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"An error occurred: {error}")




# Function to fetch a message by its ID from the database
async def get_message_by_id(message_id: str, collection=db.messages_database.messages):
    message = await collection.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


# Create a new admin
async def create_admin(admin: AdminCreate):
    hashed_password = get_password_hash(admin.password)
    admin_dict = admin.model_dump()
    admin_dict["password"] = hashed_password
    result = await db.admins_database.admins.insert_one(admin_dict)
    return {**admin_dict, "id": str(result.inserted_id)}

# Get an admin by email
from app.schemas.admin import AdminResponse
from bson import ObjectId

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
            access_token = create_access_token(data={
                "sub": admin_data["email"],
                "role": admin_data["role"],
            })
            
            # Return only the access token with token type
            return {"access_token": access_token, "token_type": "bearer"}
    
    # If admin not found or password is incorrect, raise an error
    raise HTTPException(status_code=401, detail="Invalid credentials")






