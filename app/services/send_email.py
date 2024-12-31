import os
from fastapi import HTTPException
import requests

EMAIL_API = os.getenv("EMAIL_WEB_URL")

async def send_email(user: dict, email_type: str, response_message: str = None):
    try:
        # Prepare the payload for the email request
        payload = {
            "email": user["email"],
            "name": user["name"],
            "type": email_type
        }
        
        # Include the response message if the email type is "email response"
        if email_type == "email response":
            if not response_message:
                raise HTTPException(status_code=400, detail="Response message is required for email response type.")
            payload["responseMessage"] = response_message
        
        # Send the email request
        response = requests.post(EMAIL_API, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")
