from fastapi import APIRouter, HTTPException, Query, UploadFile, Form
from typing import List
from cloudinary.uploader import upload as cloudinary_upload
from app.crud.blog import create_blog, get_all_blogs, update_blog, delete_blog
from app.schemas.blog import BlogResponseSchema, BlogSchema

router = APIRouter()

@router.post("/", response_model=BlogResponseSchema)
async def create_blog_route(
    title: str = Form(...),
    description: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: str = Form(...),
    status: str = Form(...),
    slug: str = Form(...),
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

    # Create blog object
    blog_data = BlogSchema(
        title=title,
        description=description,
        content=content,
        category=category,
        tags=tags_list,
        status=status,
        slug=slug,
        images=image_urls,
    )

    # Save to MongoDB
    created_blog = await create_blog(blog_data, image_urls)
    return created_blog


@router.get("/", response_model=List[BlogResponseSchema])
async def get_blogs_route(limit: int = Query(10), skip: int = Query(0, ge=0)):
    try:
        blogs = await get_all_blogs(limit, skip)
        return blogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{blog_id}", response_model=BlogResponseSchema)
async def update_blog_route(
    blog_id: str,
    title: str = Form(...),
    description: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: str = Form(...),
    status: str = Form(...),
    slug: str = Form(...),
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

    # Create blog object
    updated_blog_data = BlogSchema(
        title=title,
        description=description,
        content=content,
        category=category,
        tags=tags_list,
        status=status,
        slug=slug,
        images=image_urls,
    )

    # Update the blog in the database
    updated_blog = await update_blog(blog_id, updated_blog_data, image_urls)
    return updated_blog


@router.delete("/{blog_id}", response_model=dict)
async def delete_blog_route(blog_id: str):
    try:
        delete_response = await delete_blog(blog_id)
        return delete_response
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
