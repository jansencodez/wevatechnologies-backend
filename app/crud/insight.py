from bson import ObjectId
from pymongo import DESCENDING
from app.schemas.insight import InsightsSchema
from typing import List
from app.db.connection import db  # Assuming you have a MongoDB model for Insight
import datetime
from fastapi import HTTPException
from app.utils.delete_images import delete_images_from_cloudinary


async def create_insight(insight_data: InsightsSchema, images: List[str]):
    try:
        # Prepare the insight data from the Pydantic schema
        insight_dict = insight_data.model_dump()
        insight_dict["images"] = images
        insight_dict["link"] = f"/insights/{insight_data.insight_link}"

        # Insert the insight into the MongoDB collection
        result = await db.insights_database.insights.insert_one(insight_dict)
        insight_dict["id"] = str(result.inserted_id)
        return insight_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating insight: {str(e)}")


async def get_all_insights(limit: int, skip: int):
    try:
        # Fetch insights from the MongoDB collection with pagination
        insights_cursor = db.insights_database.insights.find().skip(skip).limit(limit).sort("created_at", DESCENDING)

        # Convert the cursor to a list of insights and add the 'id' field
        insights = []
        async for insight in insights_cursor:
            insight["created_at"] = insight["_id"].generation_time
            insight["updated_at"] = insight.get("updated_at", None)
            insight["id"] = str(insight["_id"])  # Add 'id' as a string
            del insight["_id"]  # Remove the '_id' field

            insights.append(insight)

        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching insights: {str(e)}")


async def get_insight_by_id(insight_id: str):
    try:
        # Fetch a single insight by its ID
        insight = await db.insights_database.insights.find_one({"_id": ObjectId(insight_id)})
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        # Add 'id' and remove '_id'
        insight["id"] = str(insight["_id"])
        del insight["_id"]
        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching insight: {str(e)}")


async def update_insight(insight_id: str, updated_data: InsightsSchema, images: List[str]):
    try:
        # Find the insight to update
        insight = await db.insights_database.insights.find_one({"_id": ObjectId(insight_id)})
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        # Prepare the updated data
        updated_data_dict = updated_data.model_dump()
        updated_data_dict["images"] = images
        updated_data_dict["updated_at"] = datetime.datetime.now(datetime.timezone.utc)  # Set the updated timestamp

        # Update the insight in the database
        result = await db.insights_database.insights.update_one(
            {"_id": ObjectId(insight_id)},
            {"$set": updated_data_dict}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the insight")

        # Fetch the updated insight and return it
        updated_insight = await db.insights_database.insights.find_one({"_id": ObjectId(insight_id)})
        updated_insight["id"] = str(updated_insight["_id"])
        del updated_insight["_id"]
        return updated_insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating insight: {str(e)}")


async def delete_insight(insight_id: str):
    try:
        # Validate the insight ID
        if not ObjectId.is_valid(insight_id):
            raise HTTPException(status_code=400, detail="Invalid insight ID format")

        # Find the insight to delete
        insight = await db.insights_database.insights.find_one({"_id": ObjectId(insight_id)})
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        # Delete images from Cloudinary
        try:
            await delete_images_from_cloudinary(insight["images"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting images: {str(e)}")

        # Delete the insight from the database
        result = await db.insights_database.insights.delete_one({"_id": ObjectId(insight_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete the insight")

        return {"id": insight_id, "message": "Insight deleted successfully"}

    except HTTPException as e:
        raise e  # Re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting insight: {str(e)}")