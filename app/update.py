from pymongo import MongoClient
from db.connection import db

# Connect to MongoDB (update the URI as needed)
client = MongoClient("mongodb://localhost:27017")
db = db.admins_database.admins
admins_collection = db

# Update the existing admin document, adding the `role` field
admins_collection.update_one(
    {"email": "jansencodez@gmail.com"},  # Query to find the admin by email (or another unique field)
    {"$set": {"role": "superadmin"}}  # Add or update the role field (change to "superadmin" if needed)
)

print("Admin role updated successfully.")
