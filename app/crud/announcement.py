# app/crud/announcement.py
from pymongo import DESCENDING
from app.schemas.announcement import AnnouncementSchema
from typing import List
from app.db.connection import db  # Assuming you have a MongoDB model for Announcement
import slugify

async def create_announcement(announcement_data: AnnouncementSchema, images: List[str]):
    announcement_dict = announcement_data.model_dump()
    announcement_dict["images"] = images
    announcement_dict["link"] = f"/announcements/{announcement_data.title}"

    result = await db.announcements_database.announcements.insert_one(announcement_dict)
    announcement_dict["id"] = str(result.inserted_id)

    return announcement_dict

from pymongo import DESCENDING

async def get_all_announcements(limit: int, skip: int):
    # Fetch announcements from the database, sorted by created_at in descending order
    announcements_cursor = db.announcements_database.announcements.find().skip(skip).limit(limit).sort("created_at", DESCENDING)

    # Convert cursor to list of dicts and add 'id' field for each announcement
    announcements = []
    async for announcement in announcements_cursor:
        announcement["created_at"] = announcement["_id"].generation_time 
        announcement["updated_at"] = announcement.get("updated_at", None)
        
        announcement["id"] = str(announcement["_id"])  
        del announcement["_id"]  
        announcements.append(announcement)
        
            
    
    return announcements

