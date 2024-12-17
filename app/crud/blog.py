from typing import List
from app.schemas.blog import BlogSchema
from app.db.connection import db
from pymongo import DESCENDING
from fastapi import HTTPException

# Function to create a new blog with error handling
async def create_blog(blog_data: BlogSchema, image_urls: List[str]):
    try:
        blog_dict = blog_data.model_dump()  # Convert Pydantic model to dict
        blog_dict["images"] = image_urls
        blog_dict["link"] = f"/blogs/{blog_data.slug}"

        # Insert the blog into the MongoDB collection
        result = await db.blogs_database.blogs.insert_one(blog_dict)
        blog_dict["id"] = str(result.inserted_id)
        return blog_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating blog: {str(e)}")

# Function to get all blogs with error handling
async def get_all_blogs(limit: int = 10, skip: int = 0):
    try:
        blogs_cursor = db.blogs_database.blogs.find().skip(skip).limit(limit).sort("created_at", DESCENDING)

        # Convert cursor to list of dicts and add 'id' field for each blog
        blogs = []
        async for blog in blogs_cursor:
            blog["created_at"] = blog["_id"].generation_time
            blog["updated_at"] = blog.get("updated_at", None)

            blog["id"] = str(blog["_id"])  
            del blog["_id"]
            
            blogs.append(blog)
           
            

        return blogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching blogs: {str(e)}")
