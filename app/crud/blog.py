import datetime
from bson import ObjectId
from fastapi import HTTPException
from pymongo import DESCENDING
from app.schemas.blog import BlogSchema
from typing import List
from app.db.connection import db  # Assuming you have a MongoDB model for Blog
import slugify
from app.utils.delete_images import delete_images_from_cloudinary

# Create a new blog post
async def create_blog(blog_data: BlogSchema, images: List[str]):
    blog_dict = blog_data.model_dump()
    blog_dict["images"] = images
    blog_dict["slug"] = slugify.slugify(blog_data.title)

    result = await db.blogs_database.blogs.insert_one(blog_dict)
    blog_dict["id"] = str(result.inserted_id)

    return blog_dict

# Get all blog posts with pagination
async def get_all_blogs(limit: int, skip: int):
    blogs_cursor = db.blogs_database.blogs.find().skip(skip).limit(limit).sort("created_at", DESCENDING)
    blogs = []
    async for blog in blogs_cursor:
        blog["created_at"] = blog["_id"].generation_time
        blog["updated_at"] = blog.get("updated_at", None)
        blog["id"] = str(blog["_id"])
        del blog["_id"]
        blogs.append(blog)
    return blogs

# Update an existing blog post by its ID
async def update_blog(blog_id: str, updated_data: BlogSchema, images: List[str]):
    # Find the blog post by ID
    blog = await db.blogs_database.blogs.find_one({"_id": ObjectId(blog_id)})
    if not blog:
        raise ValueError("Blog post not found")

    # Update the fields provided in updated_data
    updated_data_dict = updated_data.model_dump()
    updated_data_dict["images"] = images
    updated_data_dict["updated_at"] = datetime.datetime.now(datetime.timezone.utc)  # Update timestamp

    # Update the blog in the database
    result = await db.blogs_database.blogs.update_one(
        {"_id": ObjectId(blog_id)},
        {"$set": updated_data_dict}
    )

    if result.modified_count == 0:
        raise ValueError("Failed to update the blog post")

    # Fetch the updated blog post and return it
    updated_blog = await db.blogs_database.blogs.find_one({"_id": ObjectId(blog_id)})
    updated_blog["id"] = str(updated_blog["_id"])
    del updated_blog["_id"]
    return updated_blog

# Delete a blog post by its ID
async def delete_blog(blog_id: str):
    try:
        # Validate the blog ID
        if not ObjectId.is_valid(blog_id):
            raise HTTPException(status_code=400, detail="Invalid blog ID format")

        # Find the blog post by ID
        blog = await db.blogs_database.blogs.find_one({"_id": ObjectId(blog_id)})
        if not blog:
            raise HTTPException(status_code=404, detail="Blog post not found")

        # Delete images from Cloudinary
        try:
            await delete_images_from_cloudinary(blog["images"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting images: {str(e)}")

        # Delete the blog post
        result = await db.blogs_database.blogs.delete_one({"_id": ObjectId(blog_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete the blog post")

        return {"id": blog_id, "message": "Blog post deleted successfully"}

    except HTTPException as e:
        raise e  # Re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting blog post: {str(e)}")