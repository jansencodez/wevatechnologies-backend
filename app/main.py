from fastapi import FastAPI
from pydantic import BaseModel
from app.routes.blog import router as blog_router
from app.routes.admin import router as admin_router
from app.routes.user import router as user_router
from app.routes.message import router as message_router
from app.routes.service import router as service_router
from app.routes.event import router as event_router
from app.routes.announcement import router as announcement_router
from app.routes.insight import router as insight_router
from app.routes.system import router as system_router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.routes.usage import track_api_usage, get_api_usage, reset_all_api_usage, api_usage

app = FastAPI()

app.middleware("http")(track_api_usage)


class ResetUsageRequest(BaseModel):
    endpoint: str

@app.get("/api/usage")
async def get_usage_data():
    return await get_api_usage()

@app.post("/api/reset_usage")
async def reset_api_usage(request: ResetUsageRequest):
    endpoint = request.endpoint  # Get the endpoint from the request body
    # Check if the endpoint has a non-default usage count (greater than 0)
    if api_usage[endpoint] > 0:
        api_usage[endpoint] = 0  # Reset the usage count for the endpoint
        return {"message": f"Usage count for {endpoint} reset to 0"}
    return {"message": f"Endpoint {endpoint} not found or no usage recorded"}


@app.post("/api/reset_all_usage")
async def reset_all_usage():
    reset_all_api_usage()  # Call the function to reset all usage counts
    return {"message": "All API usage counts have been reset"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include all the routers
app.include_router(blog_router, prefix="/api/blogs", tags=["blogs"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(message_router, prefix="/api/contact", tags=["messages"])
app.include_router(service_router, prefix="/api/services", tags=["services"])
app.include_router(event_router, prefix="/api/events", tags=["events"])
app.include_router(announcement_router, prefix="/api/announcements", tags=["announcements"])
app.include_router(insight_router, prefix="/api/insights", tags=["insights"])
app.include_router(system_router, prefix="/api/system", tags=["system"])
