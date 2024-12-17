import psutil
from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
async def get_system_metrics():
    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get memory usage
    memory = psutil.virtual_memory()
    memory_usage = memory.percent

    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent

    # Return metrics in the same format as expected by the frontend
    metrics = [
        {"name": "CPU Usage", "value": cpu_usage},
        {"name": "Memory Usage", "value": memory_usage},
        {"name": "Disk Space", "value": disk_usage},
    ]
    return metrics
