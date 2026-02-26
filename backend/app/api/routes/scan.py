"""
Scan-related API routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from app.schemas.scan import ScanRequest, ScanResponse
from app.schemas.common import ComparisonResponse
from app.services.scan_service import ScanService

router = APIRouter()


@router.post("/scan", response_model=ScanResponse, tags=["Scan"])
async def scan_url(request: ScanRequest):
    """
    Scan a URL and return threat analysis
    
    - **url**: URL to scan (must include http:// or https://)
    """
    try:
        result = await ScanService.scan_url(request.url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/compare", response_model=ComparisonResponse, tags=["Scan"])
async def compare_scans(url: str):
    """
    Compare current scan with baseline (first) scan for a URL
    
    - **url**: URL to compare scans for
    """
    try:
        result = await ScanService.compare_scans(url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
