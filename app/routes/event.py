from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, UploadFile, Form
from typing import List
from cloudinary.uploader import upload as cloudinary_upload
from app.crud.event import create_event, get_all_events, update_event, delete_event, get_event_by_id
from app.schemas.event import EventSchema, EventResponseSchema

router = APIRouter()

@router.post("/", response_model=EventResponseSchema)
async def create_event_route(
    event_name: str = Form(...),
    event_date: str = Form(...),  # Ensure this is formatted as a string (e.g., "2024-12-13T00:00:00")
    event_location: str = Form(...),
    event_description: str = Form(...),
    files: List[UploadFile] = Form(...),
    event_link: str = Form(...),
):
    # Validate event_date format
    try:
        event_date = datetime.fromisoformat(event_date)  # Convert string to datetime
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")

    image_urls = []
    for file in files:
        if file.content_type.startswith("image/"):
            result = cloudinary_upload(file.file)
            image_url = result.get("secure_url")
            image_urls.append(image_url)
        else:
            raise HTTPException(status_code=400, detail="Only image files are allowed")

    event_data = EventSchema(
        event_name=event_name,
        event_date=event_date,
        event_location=event_location,
        event_description=event_description,
        images=image_urls,
        event_link=event_link,
    )

    created_event = await create_event(event_data, image_urls)
    return created_event


@router.get("/", response_model=List[EventResponseSchema])
async def get_events_route(limit: int = Query(10), skip: int = Query(0, ge=0)):
    try:
        events = await get_all_events(limit, skip)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=EventResponseSchema)
async def get_event_route(event_id: str):
    try:
        event = await get_event_by_id(event_id)
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_id}", response_model=EventResponseSchema)
async def update_event_route(
    event_id: str,
    event_name: str = Form(...),
    event_date: str = Form(...),
    event_location: str = Form(...),
    event_description: str = Form(...),
    files: List[UploadFile] = Form(...),
    event_link: str = Form(...),
):
    # Validate event_date format
    try:
        event_date = datetime.fromisoformat(event_date)  # Convert string to datetime
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")

    image_urls = []
    for file in files:
        if file.content_type.startswith("image/"):
            result = cloudinary_upload(file.file)
            image_url = result.get("secure_url")
            image_urls.append(image_url)
        else:
            raise HTTPException(status_code=400, detail="Only image files are allowed")

    updated_data = EventSchema(
        event_name=event_name,
        event_date=event_date,
        event_location=event_location,
        event_description=event_description,
        images=image_urls,
        event_link=event_link,
    )

    try:
        updated_event = await update_event(event_id, updated_data, image_urls)
        return updated_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}", response_model=dict)
async def delete_event_route(event_id: str):
    try:
        response = await delete_event(event_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
