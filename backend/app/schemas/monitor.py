"""
Monitor-related Pydantic schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MonitorCreateRequest(BaseModel):
    """Request to create a new monitor"""
    url: str = Field(..., description="URL to monitor")
    interval: int = Field(5, description="Monitoring interval in minutes", ge=1)


class MonitorCreateResponse(BaseModel):
    """Response after creating a monitor"""
    monitor_id: str
    url: str
    interval: int
    message: str


class LastScanData(BaseModel):
    """Last scan data for a monitor"""
    threat_score: int
    status: str
    risk_level: str
    category: str
    emails_count: int
    urls_count: int
    ips_count: int
    crypto_count: int
    clamav_detected: bool


class MonitorResponse(BaseModel):
    """Single monitor details"""
    monitor_id: str
    url: str
    interval: int
    last_check: Optional[str] = None
    next_check: Optional[str] = None
    created_at: str
    paused: bool = False
    last_scan_data: Optional[LastScanData] = None


class MonitorListResponse(BaseModel):
    """List of monitors"""
    monitors: List[MonitorResponse]


class MonitorDeleteResponse(BaseModel):
    """Response after deleting a monitor"""
    message: str


class MonitorDeleteAllResponse(BaseModel):
    """Response after deleting all monitors"""
    message: str
    count: int


class MonitorActionResponse(BaseModel):
    """Response for monitor pause/resume actions"""
    message: str
