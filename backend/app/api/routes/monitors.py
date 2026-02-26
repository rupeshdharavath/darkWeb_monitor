"""
Monitor management API routes
"""

from fastapi import APIRouter, HTTPException
from app.schemas.monitor import (
    MonitorCreateRequest,
    MonitorCreateResponse,
    MonitorListResponse,
    MonitorResponse,
    MonitorDeleteResponse,
    MonitorDeleteAllResponse,
    MonitorActionResponse
)
from app.services.monitor_service import MonitorService

router = APIRouter()


@router.get("/monitors", response_model=MonitorListResponse, tags=["Monitors"])
async def list_monitors():
    """
    Get all active monitors with last scan details
    """
    try:
        result = await MonitorService.list_monitors()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/monitors", response_model=MonitorCreateResponse, status_code=201, tags=["Monitors"])
async def create_monitor(request: MonitorCreateRequest):
    """
    Create a new monitoring job
    
    - **url**: URL to monitor
    - **interval**: Monitoring interval in minutes (default: 5)
    """
    try:
        result = await MonitorService.create_monitor(request.url, request.interval)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/monitors/{monitor_id}", response_model=MonitorResponse, tags=["Monitors"])
async def get_monitor(monitor_id: str):
    """
    Get specific monitor details
    
    - **monitor_id**: Unique monitor identifier
    """
    try:
        result = await MonitorService.get_monitor(monitor_id)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/monitors/all", response_model=MonitorDeleteAllResponse, tags=["Monitors"])
async def delete_all_monitors():
    """
    Delete all monitors (utility endpoint)
    """
    try:
        result = await MonitorService.delete_all_monitors()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/monitors/{monitor_id}", response_model=MonitorDeleteResponse, tags=["Monitors"])


@router.post("/monitors/{monitor_id}/pause", response_model=MonitorActionResponse, tags=["Monitors"])
async def pause_monitor(monitor_id: str):
    """
    Pause a monitor
    
    - **monitor_id**: Unique monitor identifier
    """
    try:
        result = await MonitorService.pause_monitor(monitor_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to pause monitor")


@router.post("/monitors/{monitor_id}/resume", response_model=MonitorActionResponse, tags=["Monitors"])
async def resume_monitor(monitor_id: str):
    """
    Resume a paused monitor
    
    - **monitor_id**: Unique monitor identifier
    """
    try:
        result = await MonitorService.resume_monitor(monitor_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resume monitor")
