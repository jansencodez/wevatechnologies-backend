import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Depends
from app.db.connection import db
from app.schemas.admin import AdminCreate, AdminLoginRequest
from app.crud.admin import create_admin, authenticate_admin, get_admin_by_email
from app.auth import create_access_token, create_refresh_token, verify_refresh_token, verify_token
from fastapi.security import OAuth2PasswordBearer
from googleapiclient.errors import HttpError
from app.utils.oauth2 import get_gmail_service  
from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.crud.admin import get_message_by_id, send_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

class EmailResponse(BaseModel):
    response: str

# Create a new admin
@router.post("/create")
async def create_admin_route(admin: AdminCreate):
    # Check if an admin with the same email already exists
    existing_admin = await get_admin_by_email(admin.email)
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin with this email already exists")
    
    # Create the new admin
    new_admin = await create_admin(admin)
    

    return {"message": "Admin created successfully", "admin": new_admin}


# Admin login
@router.post("/login")
async def login_admin(request: AdminLoginRequest):
    admin = await get_admin_by_email(request.email)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    token = await authenticate_admin(request.email, request.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create refresh token
    refresh_token = create_refresh_token({"sub": admin.email, "role": admin.role})
    
    return {"access_token": token["access_token"], "refresh_token": refresh_token, "admin": admin}




@router.post("/messages/{message_id}/respond")
async def respond_to_message(message_id: str, email_response: EmailResponse, background_tasks: BackgroundTasks):
    # Fetch the message by ID using the CRUD function
    collection = db.messages_database.messages
    message = await get_message_by_id(message_id, collection)

    sender_email = message["email"]
    response_message = email_response.response
    message_text = message["message"]

    # Prepare the email content
    email_body = {
        "sender_email": sender_email,
        "response_message": response_message,
    }

    # Send the email in the background
    try:
        service = get_gmail_service()  # Get the Gmail service
        message = create_message(sender_email, message_text, email_body["response_message"])
        send_email(background_tasks, service, message)
        return {"detail": f"Email sent successfully to {sender_email}"}
    except HttpError as error:
        return {"detail": f"An error occurred: {error}"}

def create_message(sender_email, subject, message_text):
    """Create a message for the Gmail API."""
    message = MIMEMultipart()
    message['to'] = sender_email
    message['from'] = 'me'
    message['subject'] = subject
    msg = MIMEText(message_text)
    message.attach(msg)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(background_tasks, service, message):
    """Send the email using Gmail API."""
    background_tasks.add_task(service.users().messages().send, userId="me", body=message)



import logging

# Add logging to capture more details
logger = logging.getLogger(__name__)

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    # Verify the token
    payload = verify_token(token)
    
    if not payload:
        logger.error("Invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract the email (sub field in the payload)
    email = payload.get("sub")
    if not email:
        logger.error(f"Invalid token payload: missing email. Payload: {payload}")
        raise HTTPException(status_code=400, detail="Invalid token payload: missing email")

    # Fetch admin details based on the email
    admin = await get_admin_by_email(email)
    if not admin:
        logger.error(f"Admin not found for email: {email}")
        raise HTTPException(status_code=404, detail="Admin not found")

    return admin



# Protected route to return admin details
@router.get("/protected")
async def protected_route(admin=Depends(get_current_admin)):
    # Return only safe data (e.g., name, email, role)
    return {"name": admin.name, "email": admin.email, "role": admin.role, "phone": admin.phone}



@router.post("/refresh")
async def refresh_token(refresh_token: str):
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Create a new access token
    new_access_token = create_access_token({"sub": payload["sub"], "role": payload["role"]})
    return {"access_token": new_access_token}
