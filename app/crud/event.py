# app/crud/event.py
from fastapi import HTTPException
from pymongo import DESCENDING
from app.schemas.event import EventSchema
from typing import List
from app.db.connection import db  # Assuming you have a MongoDB model for Event

async def create_event(event_data: EventSchema, images: List[str]):
    try:
        event_dict = event_data.model_dump()
        event_dict["images"] = images
        event_dict["event_link"] = f"/events/{event_data.event_link}"

        result = await db.events_database.events.insert_one(event_dict)
        event_dict["id"] = str(result.inserted_id)
        return event_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

async def get_all_events(limit: int, skip: int):
    events_cursor = db.events_database.events.find().skip(skip).limit(limit).sort("created_at", DESCENDING)
    
    # Convert cursor to list of dicts and add 'id' field for each blog
    events = []
    async for event in events_cursor:

        event["created_at"] = event["_id"].generation_time
        event["updated_at"] = event.get("updated_at", None)
        
        event["id"] = str(event["_id"])  
        del event["_id"]
        

        events.append(event)
    return events
