from fastapi import HTTPException
from pymongo import DESCENDING
from app.schemas.event import EventSchema
from typing import List
from app.db.connection import db  # Assuming you have a MongoDB model for Event
import datetime
from app.utils.delete_images import delete_images_from_cloudinary


async def create_event(event_data: EventSchema, images: List[str]):
    try:
        # Prepare the event data from the Pydantic schema
        event_dict = event_data.model_dump()
        event_dict["images"] = images
        event_dict["event_link"] = f"/events/{event_data.event_name.replace(' ', '-').lower()}"

        # Insert the event into the MongoDB collection
        result = await db.events_database.events.insert_one(event_dict)
        event_dict["id"] = str(result.inserted_id)
        return event_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")


async def get_all_events(limit: int, skip: int):
    try:
        # Fetch events from the MongoDB collection with pagination
        events_cursor = db.events_database.events.find().skip(skip).limit(limit).sort("event_date", DESCENDING)

        # Convert the cursor to a list of events and add the 'id' field
        events = []
        async for event in events_cursor:
            event["event_date"] = event.get("event_date")
            event["created_at"] = event["_id"].generation_time
            event["updated_at"] = event.get("updated_at", None)
            event["id"] = str(event["_id"])  # Add 'id' as a string
            del event["_id"]  # Remove the '_id' field

            events.append(event)

        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")


async def get_event_by_id(event_id: str):
    try:
        # Fetch a single event by its ID
        event = await db.events_database.events.find_one({"_id": db.ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Add 'id' and remove '_id'
        event["id"] = str(event["_id"])
        del event["_id"]
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event: {str(e)}")


async def update_event(event_id: str, updated_data: EventSchema, images: List[str]):
    try:
        # Find the event to update
        event = await db.events_database.events.find_one({"_id": db.ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Prepare the updated data
        updated_data_dict = updated_data.model_dump()
        updated_data_dict["images"] = images
        updated_data_dict["updated_at"] = datetime.datetime.utcnow()  # Set the updated timestamp

        # Update the event in the database
        result = await db.events_database.events.update_one(
            {"_id": db.ObjectId(event_id)},
            {"$set": updated_data_dict}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the event")

        # Fetch the updated event and return it
        updated_event = await db.events_database.events.find_one({"_id": db.ObjectId(event_id)})
        updated_event["id"] = str(updated_event["_id"])
        del updated_event["_id"]
        return updated_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")


async def delete_event(event_id: str):
    try:
        # Find the event to delete
        event = await db.events_database.events.find_one({"_id": db.ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        await delete_images_from_cloudinary(event["images"])

        # Delete the event from the database
        result = await db.events_database.events.delete_one({"_id": db.ObjectId(event_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete the event")

        return {"id": event_id, "message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")
