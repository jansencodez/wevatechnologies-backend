from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List
from app.schemas.service import ServiceCreate, ServiceResponse
from app.crud.service import create_service, get_services, delete_service
from app.auth import verify_token  # Import the utility to verify the token

router = APIRouter()

# OAuth2PasswordBearer provides a way to extract the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

# Dependency to get the current admin user from the token
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

# Route to create a new service (only accessible to authenticated users)
@router.post("/", response_model=ServiceResponse)
async def create_service_route(service: ServiceCreate, admin=Depends(get_current_admin)):
    return await create_service(service)

# Route to get all services (publicly accessible)
@router.get("/", response_model=List[ServiceResponse])
async def get_services_route():
    return await get_services()

# Route to delete a service by ID (only accessible to authenticated users)
@router.delete("/{service_id}")
async def delete_service_route(service_id: str, admin=Depends(get_current_admin)):
    result = await delete_service(service_id)
    if result.get("message") == "Service deleted successfully":
        return result
    raise HTTPException(status_code=404, detail="Service not found")
