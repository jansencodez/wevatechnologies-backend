import os

from fastapi import HTTPException
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the Cloudinary URL from environment variables
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

# Ensure that the Cloudinary URL is loaded correctly
if not CLOUDINARY_URL:
    raise ValueError("Cloudinary configuration is missing. Please check your .env file.")

# Configure Cloudinary using the CLOUDINARY_URL
cloudinary.config(cloudinary_url=CLOUDINARY_URL)

# Function to upload a file to Cloudinary
def upload(file):
    try:
        result = cloudinary.uploader.upload(file)
        return result
    except cloudinary.exceptions.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def delete(public_id):
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result
    except cloudinary.exceptions.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
