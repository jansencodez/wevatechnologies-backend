# app/routes/announcement.py
from fastapi import APIRouter, HTTPException, Query, UploadFile, Form
from typing import List
from cloudinary.uploader import upload as cloudinary_upload
from app.crud.announcement import create_announcement, get_all_announcements
from app.schemas.announcement import AnnouncementSchema, AnnouncementResponseSchema

router = APIRouter()

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


@router.get("/", response_model=List[AnnouncementResponseSchema])
async def get_announcements_route(limit: int = Query(10), skip: int = Query(0, ge=0)):
    try:
        announcements = await get_all_announcements(limit, skip)
        return announcements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
