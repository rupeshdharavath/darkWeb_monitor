"""
Common Pydantic schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str


class ScanData(BaseModel):
    """Scan data for comparison"""
    timestamp: Optional[str] = None
    threat_score: int
    risk_level: str
    category: str
    url_status: str
    content_changed: bool
    emails: int
    crypto: int


class ChangeData(BaseModel):
    """Change details between scans"""
    threat_score_delta: int
    risk_level_changed: bool
    category_changed: bool
    status_changed: bool
    new_emails: int
    new_crypto: int
    new_malicious_files: int


class ComparisonResponse(BaseModel):
    """Comparison between two scans"""
    current: ScanData
    previous: ScanData
    changes: ChangeData
    reasons: List[str]
