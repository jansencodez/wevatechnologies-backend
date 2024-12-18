from bson import ObjectId
from fastapi import HTTPException
from pymongo import DESCENDING
from app.schemas.announcement import AnnouncementSchema
from app.utils.delete_images import delete_images_from_cloudinary
from typing import List, Dict
from app.db.connection import db  

# Create a new announcement
async def create_announcement(announcement_data: AnnouncementSchema, images: List[str]):
    announcement_dict = announcement_data.model_dump()
    announcement_dict["images"] = images
    announcement_dict["link"] = f"/announcements/{announcement_data.title}"

    result = await db.announcements_database.announcements.insert_one(announcement_dict)
    announcement_dict["id"] = str(result.inserted_id)

    return announcement_dict

# Get all announcements with pagination
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

# Update an existing announcement by its ID
async def update_announcement(announcement_id: str, updated_data: Dict):
    # Find the announcement by ID
    announcement = await db.announcements_database.announcements.find_one({"_id": db.ObjectId(announcement_id)})
    if not announcement:
        raise ValueError("Announcement not found")

    # Update the fields provided in updated_data
    updated_data["updated_at"] = db.datetime.datetime.utcnow()  # Update timestamp
    result = await db.announcements_database.announcements.update_one(
        {"_id": db.ObjectId(announcement_id)},
        {"$set": updated_data}
    )

    if result.modified_count == 0:
        raise ValueError("Failed to update the announcement")

    # Fetch the updated announcement and return it
    updated_announcement = await db.announcements_database.announcements.find_one({"_id": db.ObjectId(announcement_id)})
    updated_announcement["id"] = str(updated_announcement["_id"])
    del updated_announcement["_id"]
    return updated_announcement

# Delete an announcement by its ID
async def delete_announcement(announcement_id: str):
    try:
        # Validate the announcement ID
        if not ObjectId.is_valid(announcement_id):
            raise HTTPException(status_code=400, detail="Invalid announcement ID format")

        # Find the announcement by ID
        announcement = await db.announcements_database.announcements.find_one({"_id": ObjectId(announcement_id)})
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")

        # Delete images from Cloudinary
        try:
            await delete_images_from_cloudinary(announcement["images"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting images: {str(e)}")

        # Delete the announcement
        result = await db.announcements_database.announcements.delete_one({"_id": ObjectId(announcement_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete the announcement")

        return {"id": announcement_id, "message": "Announcement deleted successfully"}

    except HTTPException as e:
        raise e  # Re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting announcement: {str(e)}")