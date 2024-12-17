# app/crud/insight.py
from pymongo import DESCENDING
from app.schemas.insight import InsightsSchema
from typing import List
from app.db.connection import db

async def create_insight(insight_data: InsightsSchema, images: List[str]):
    insight_dict = insight_data.model_dump()
    insight_dict["images"] = images
    insight_dict["link"] = f"/announcements/{insight_data.insight_link}"

    result = await db.insights_database.insights.insert_one(insight_dict)
    insight_dict["id"] = str(result.inserted_id)
    return insight_dict

async def get_all_insights(limit: int, skip: int):
    insights_cursor = db.insights_database.insights.find().skip(skip).limit(limit).sort("created_at", DESCENDING)

    # Convert cursor to list of dicts and add 'id' field for each blog
    insights = []
    async for insight in insights_cursor:
        insight["created_at"] = insight["_id"].generation_time
        insight["updated_at"] = insight.get("updated_at", None)
        
        insight["id"] = str(insight["_id"])  
        del insight["_id"]
        
        insights.append(insight)
    return insights
