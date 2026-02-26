"""
History-related API routes
"""

from fastapi import APIRouter, HTTPException
from app.schemas.history import HistoryListResponse, HistoryDetailResponse
from app.services.history_service import HistoryService

router = APIRouter()


@router.get("/history", response_model=HistoryListResponse, tags=["History"])
async def get_history():
    """
    Get all scan history sorted by newest first
    """
    try:
        result = await HistoryService.get_history()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.get("/history/{entry_id}", response_model=HistoryDetailResponse, tags=["History"])
async def get_history_entry(entry_id: str):
    """
    Get specific scan entry by ID
    
    - **entry_id**: MongoDB ObjectId of the scan entry
    """
    try:
        result = await HistoryService.get_history_entry(entry_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
