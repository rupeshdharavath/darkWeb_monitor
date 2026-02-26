"""
Alert-related Pydantic schemas
"""

from typing import Any, Dict, List
from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Single alert details"""
    _id: str
    # Add other alert fields as needed
    # Based on your alert structure in MongoDB


class AlertListResponse(BaseModel):
    """List of alerts"""
    alerts: List[Dict[str, Any]]


class AcknowledgeResponse(BaseModel):
    """Response after acknowledging an alert"""
    message: str
