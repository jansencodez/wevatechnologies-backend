# app/routes/insight.py
from fastapi import APIRouter, HTTPException, Query, UploadFile, Form
from typing import List
from cloudinary.uploader import upload as cloudinary_upload
from app.crud.insight import create_insight, get_all_insights
from app.schemas.insight import InsightsSchema, InsightsResponseSchema

router = APIRouter()

@router.post("/", response_model=InsightsResponseSchema)
async def create_insight_route(
    insight_title: str = Form(...),
    insight_date: str = Form(...),
    insight_content: str = Form(...),
    author: str = Form(...),
    files: List[UploadFile] = Form(...),
    insight_link: str = Form(...),
):
    # Validate images and upload to Cloudinary
    image_urls = []
    for file in files:
        if file.content_type.startswith("image/"):
            result = cloudinary_upload(file.file)
            image_url = result.get("secure_url")
            image_urls.append(image_url)
        else:
            raise HTTPException(status_code=400, detail="Only image files are allowed")

    # Create insight object
    insight_data = InsightsSchema(
        insight_title=insight_title,
        insight_date=insight_date,
        insight_content=insight_content,
        author=author,
        images=image_urls,
        insight_link=insight_link,
    )

    # Save to MongoDB
    created_insight = await create_insight(insight_data, image_urls)
    return created_insight


@router.get("/", response_model=List[InsightsResponseSchema])
async def get_insights_route(limit: int = Query(10), skip: int = Query(0, ge=0)):
    try:
        insights = await get_all_insights(limit, skip)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))