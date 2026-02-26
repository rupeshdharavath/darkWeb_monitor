"""
Alert management API routes
"""

from fastapi import APIRouter, HTTPException
from app.schemas.alert import AlertListResponse, AcknowledgeResponse
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse, tags=["Alerts"])
async def get_alerts():
    """
    Get recent alerts (last 100)
    """
    try:
        result = await AlertService.get_alerts()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge", response_model=AcknowledgeResponse, tags=["Alerts"])
async def acknowledge_alert(alert_id: str):
    """
    Mark an alert as acknowledged
    
    - **alert_id**: MongoDB ObjectId of the alert
    """
    try:
        result = await AlertService.acknowledge_alert(alert_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
