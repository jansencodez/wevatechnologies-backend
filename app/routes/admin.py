import datetime
from datetime import timedelta, timezone, datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from app.db.connection import db
from app.schemas.admin import AdminCreate, AdminLoginRequest
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.crud.admin import create_admin, authenticate_admin, get_admin_by_email, get_message_by_id
from app.auth import create_access_token, create_refresh_token, verify_refresh_token, verify_token
from fastapi.security import OAuth2PasswordBearer
from googleapiclient.errors import HttpError 
from pydantic import BaseModel
import logging
from app.utils.uptime import server_start_time
from app.services.send_email import send_email
from app.services.update_message_status import update_message_status


# Add logging to capture more details
logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

class EmailResponse(BaseModel):
    response: str

class UsersResponse(BaseModel):
    users: list[dict]

class UpdateUserStatusRequest(BaseModel):
    is_active: bool

# Create a new admin
@router.post("/create")
async def create_admin_route(admin: AdminCreate):
    # Check if an admin with the same email already exists
    existing_admin = await get_admin_by_email(admin.email)
    if (existing_admin):
        raise HTTPException(status_code=400, detail="Admin with this email already exists")
    
    # Create the new admin
    new_admin = await create_admin(admin)
    

    return {"message": "Admin created successfully", "admin": new_admin}


# Admin login
@router.post("/login")
async def login_admin(request: AdminLoginRequest):
    admin = await get_admin_by_email(request.email)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    token = await authenticate_admin(request.email, request.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create refresh token
    refresh_token = create_refresh_token({"sub": admin.email, "role": admin.role})
    
    return {"access_token": token["access_token"], "refresh_token": refresh_token, "admin": admin}




@router.post("/messages/{message_id}/respond")
async def respond_to_message(message_id: str, email_response: EmailResponse, background_tasks: BackgroundTasks):
    # Retrieve the message details by ID
    message = await get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    recipient_email = message["email"]
    recipient_name = message["name"]
    response_message = email_response.response

    # Send the email in the background
    try:
        background_tasks.add_task(
            send_email,
            {"email": recipient_email, "name": recipient_name},
            "email response",
            response_message
        )

        await update_message_status(message_id, read=True)

        return {"detail": f"Email sent successfully to {recipient_email}"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(error)}")




async def get_current_admin(token: str = Depends(oauth2_scheme)):
    # Verify the token
    payload = verify_token(token)
    
    if not payload:
        logger.error("Invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract the email (sub field in the payload)
    email = payload.get("sub")
    if not email:
        logger.error(f"Invalid token payload: missing email. Payload: {payload}")
        raise HTTPException(status_code=400, detail="Invalid token payload: missing email")

    # Fetch admin details based on the email
    admin = await get_admin_by_email(email)
    if not admin:
        logger.error(f"Admin not found for email: {email}")
        raise HTTPException(status_code=404, detail="Admin not found")

    return admin



# Protected route to return admin details
@router.get("/protected")
async def protected_route(admin=Depends(get_current_admin)):
    # Return only safe data (e.g., name, email, role)
    return {"name": admin.name, "email": admin.email, "role": admin.role, "phone": admin.phone}



@router.post("/refresh")
async def refresh_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    refresh_token = auth_header.split(" ")[1]
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Create a new access token
    new_access_token = create_access_token({"sub": payload["sub"], "role": payload["role"]})
    return {"access_token": new_access_token}


@router.get("/users")
async def get_all_users():
    users = await db.users_database.users.find().to_list(length=None)
    for user in users:
        user["id"] = str(user["_id"])
        del user["password"]
        del user["_id"]
    return users


@router.patch("/users/{user_id}")
async def update_user_by_id(user_id: str, request: UpdateUserStatusRequest):
    user = await db.users_database.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": request.is_active}},
        return_document=True
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["id"] = str(user["_id"])
    del user["_id"]
    return user

@router.get("/dashboard-stats")
async def get_dashboard_stats():
    # Get the count of active users
    active_users_count = await db.users_database.users.count_documents({"is_active": True})
    
    # Get the count of current projects
    current_projects_count = await db.projects_database.projects.count_documents({})
    
    # Server uptime (this is a static value for demonstration purposes)
    current_time = datetime.now(timezone.utc)
    uptime_duration = current_time - server_start_time
    uptime_seconds = int(uptime_duration.total_seconds())
    uptime_days, remainder = divmod(uptime_seconds, 86400)
    uptime_hours, remainder = divmod(remainder, 3600)
    uptime_minutes, uptime_seconds = divmod(remainder, 60)
    server_uptime = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
    
     # Get the count of new sign-ups (using generation_time of ObjectId)
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    new_signups_count = await db.users_database.users.count_documents({
        "_id": {"$gte": ObjectId.from_datetime(one_day_ago)}
    })

    recent_activities=[]

    # Example: Fetch recent user registrations
    recent_users = await db.users_database.users.find(
        {"_id": {"$gte": ObjectId.from_datetime(one_day_ago)}}
    ).to_list(length=5)
    for user in recent_users:
        recent_activities.append({
            "activity": "New user registration",
            "timestamp": user["_id"].generation_time.isoformat()
        })

    # Example: Fetch recent projects (assuming you have a created_at field)
    recent_projects = await db.projects_database.projects.find(
        {"created_at": {"$gte": one_day_ago}}
    ).to_list(length=5)
    for project in recent_projects:
        recent_activities.append({
            "activity": f"New project launched: {project['name']}",
            "timestamp": project["created_at"].isoformat()
        })

   
    
    recent_activities.extend([
        {"activity": "System update completed", "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
        {"activity": "New API request spike", "timestamp": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()}
    ])
    
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "active_users": active_users_count,
        "current_projects": current_projects_count,
        "server_uptime": server_uptime,
        "new_signups": new_signups_count,
        "recent_activities": recent_activities
    }


from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, admin=Depends(get_current_admin)):
    project_dict = project.model_dump()
    project_dict["created_by"] = admin.email
    project_dict["created_at"] = datetime.now(timezone.utc)
    project_dict["updated_at"] = datetime.now(timezone.utc)
    result = await db.projects_database.projects.insert_one(project_dict)
    project_dict["id"] = str(result.inserted_id)

    if result.acknowledged:
        return ProjectResponse(**project_dict)

    raise HTTPException(status_code=500, detail="Failed to create project")

@router.get("/projects/completion", response_model=list[ProjectResponse])
async def get_projects_with_completion(admin=Depends(get_current_admin)):
    projects = await db.projects_database.projects.find().to_list(length=None)
    current_time = datetime.now(timezone.utc)
    
    for project in projects:
        project["id"] = str(project["_id"])
        del project["_id"]
        
        # Ensure start_date and end_date are offset-aware
        if project["start_date"]:
            project["start_date"] = project["start_date"].replace(tzinfo=timezone.utc)
        if project["end_date"]:
            project["end_date"] = project["end_date"].replace(tzinfo=timezone.utc)
        
        # Calculate completion percentage
        if project["start_date"] and project["end_date"]:
            start_date = project["start_date"]
            end_date = project["end_date"]
            total_duration = (end_date - start_date).total_seconds()
            elapsed_duration = (current_time - start_date).total_seconds()
            completion_percentage = min(max(elapsed_duration / total_duration * 100, 0), 100)
            project["completion_percentage"] = completion_percentage
        else:
            project["completion_percentage"] = 0

    return [ProjectResponse(**project) for project in projects]

@router.get("/projects/{project_id}")
async def get_project(project_id: str, admin=Depends(get_current_admin)):
    project = await db.projects_database.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["id"] = str(project["_id"])
    del project["_id"]
    return project

@router.patch("/projects/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate, admin=Depends(get_current_admin)):
    update_data = {k: v for k, v in project.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin.email
    result = await db.projects_database.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": update_data}
    )
    if result.modified_count == 1:
        return {"message": "Project updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Project not found or no changes made")

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, admin=Depends(get_current_admin)):
    result = await db.projects_database.projects.delete_one({"_id": ObjectId(project_id)})
    if result.deleted_count == 1:
        return {"message": "Project deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Project not found")
    
@router.get("/projects", response_model=list[ProjectResponse])
async def get_projects(admin=Depends(get_current_admin)):
    projects = await db.projects_database.projects.find().to_list(length=None)
    for project in projects:
        project["id"] = str(project["_id"])
        del project["_id"]
    return [ProjectResponse(**project) for project in projects]


