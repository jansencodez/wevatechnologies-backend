from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse

# Store API usage counts
api_usage = defaultdict(int)

# Middleware to track API usage
async def track_api_usage(request: Request, call_next):
    endpoint = str(request.url.path)
    api_usage[endpoint] += 1
    response = await call_next(request)
    return response

# Endpoint to fetch the API usage data
async def get_api_usage():
    usage_data = [{"endpoint": endpoint, "calls": count} for endpoint, count in api_usage.items()]
    return JSONResponse(content=usage_data)

# Clear all API usage counts
def reset_all_api_usage():
    api_usage.clear()  # Clear the usage data

