import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve environment variables
CLOUD_NAME = os.getenv("CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUD_API_SECRET")

# Debugging: Print environment variables to ensure they are loaded
print("CLOUD_NAME:", CLOUD_NAME)
print("CLOUD_API_KEY:", CLOUD_API_KEY)
print("CLOUD_API_SECRET:", CLOUD_API_SECRET)

# Configure Cloudinary with the loaded credentials
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=CLOUD_API_KEY,
    api_secret=CLOUD_API_SECRET
)

# Function to upload a file to Cloudinary
def upload(file):
    # Upload the file and return the result
    result = cloudinary.uploader.upload(file)
    return result
