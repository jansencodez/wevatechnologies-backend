from fastapi import APIRouter, HTTPException, Query, UploadFile, Form, Path
from typing import List
from cloudinary.uploader import upload as cloudinary_upload
from app.crud.announcement import create_announcement, get_all_announcements, update_announcement, delete_announcement
from app.schemas.announcement import AnnouncementSchema, AnnouncementResponseSchema

router = APIRouter()

# Create a new announcement
@router.post("/", response_model=AnnouncementResponseSchema)
async def create_announcement_route(
    title: str = Form(...),
    content: str = Form(...),
    announcement_date: str = Form(...),
    tags: str = Form(...),
    link: str = Form(...),
    files: List[UploadFile] = Form(...),
):
    # Parse and validate tags
    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # Validate images and upload to Cloudinary
    image_urls = []
    for file in files:
        if file.content_type.startswith("image/"):
            result = cloudinary_upload(file.file)
            image_url = result.get("secure_url")
            image_urls.append(image_url)
        else:
            raise HTTPException(status_code=400, detail="Only image files are allowed")

    # Create announcement object
    announcement_data = AnnouncementSchema(
        title=title,
        content=content,
        announcement_date=announcement_date,
        tags=tags_list,
        link=link,
        images=image_urls,
    )

    # Save to MongoDB
    created_announcement = await create_announcement(announcement_data, image_urls)
    return created_announcement

# Get all announcements with pagination
@router.get("/", response_model=List[AnnouncementResponseSchema])
async def get_announcements_route(limit: int = Query(10), skip: int = Query(0, ge=0)):
    try:
        announcements = await get_all_announcements(limit, skip)
        return announcements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update an existing announcement
@router.put("/{announcement_id}", response_model=AnnouncementResponseSchema)
async def update_announcement_route(
    announcement_id: str = Path(..., description="The ID of the announcement to be updated"),
    title: str = Form(None),
    content: str = Form(None),
    announcement_date: str = Form(None),
    tags: str = Form(None),
    link: str = Form(None),
    files: List[UploadFile] = Form(None),
):
    # Fetch the current announcement data
    try:
        announcement = await get_all_announcements(announcement_id=announcement_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Prepare the updated fields
    updated_data = {}
    
    if title:
        updated_data["title"] = title
    if content:
        updated_data["content"] = content
    if announcement_date:
        updated_data["announcement_date"] = announcement_date
    if tags:
        updated_data["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if link:
        updated_data["link"] = link

    # Handle images if provided
    if files:
        image_urls = []
        for file in files:
            if file.content_type.startswith("image/"):
                result = cloudinary_upload(file.file)
                image_url = result.get("secure_url")
                image_urls.append(image_url)
            else:
                raise HTTPException(status_code=400, detail="Only image files are allowed")
        updated_data["images"] = image_urls

    try:
        # Update announcement data in DB
        updated_announcement = await update_announcement(announcement_id, updated_data)
        return updated_announcement
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete an announcement by its ID
@router.delete("/{announcement_id}", response_model=AnnouncementResponseSchema)
async def delete_announcement_route(announcement_id: str = Path(..., description="The ID of the announcement to be deleted")):
    try:
        # Delete the announcement from DB
        deleted_announcement = await delete_announcement(announcement_id)
        return deleted_announcement
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
