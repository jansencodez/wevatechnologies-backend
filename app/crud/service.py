from app.db.connection import db
from app.schemas.service import ServiceCreate
from bson import ObjectId

# Create a new service
async def create_service(service: ServiceCreate):
    service_dict = service.model_dump()
    result = await db.services_database.services.insert_one(service_dict)
    return {**service_dict, "id": str(result.inserted_id)}

# Get all services
async def get_services():
    services = await db.services.find().to_list(100)  # Fetch up to 100 services
    return [{"id": str(service["_id"]), **service} for service in services]

# Delete a service by its ID
async def delete_service(service_id: str):
    result = await db.services.delete_one({"_id": ObjectId(service_id)})
    if result.deleted_count == 1:
        return {"message": "Service deleted successfully"}
    return {"message": "Service not found"}
