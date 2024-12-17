import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

MONGO_URI =os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client
