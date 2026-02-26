"""
Scan-related Pydantic schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Request body for scanning a URL"""
    url: str = Field(..., description="URL to scan (must include http:// or https://)")


class ThreatIndicators(BaseModel):
    """Threat indicators detected"""
    pass  # Can be extended based on specific indicators


class CategoryDistribution(BaseModel):
    """Category distribution"""
    name: str
    value: int


class ThreatBreakdown(BaseModel):
    """Threat breakdown metrics"""
    label: str
    value: int


class Timeline(BaseModel):
    """Timeline data point"""
    time: str
    value: float


class ClamavInfo(BaseModel):
    """ClamAV scan information"""
    status: Optional[str] = None
    detected: bool = False
    details: List[Any] = []


class LinkInfo(BaseModel):
    """Link information"""
    url: str
    text: Optional[str] = None


class ScanResponse(BaseModel):
    """Response from scanning a URL"""
    status: str
    threatScore: int
    category: str
    riskLevel: str
    confidence: int
    threatIndicators: Dict[str, Any] = {}
    pgpDetected: bool
    emails: List[str]
    cryptoAddresses: List[str]
    contentChanged: bool
    contentHash: str
    title: str
    textPreview: str
    keywords: List[str]
    links: List[Dict[str, Optional[str]]]
    fileLinks: List[Dict[str, Any]]
    fileAnalysis: List[Dict[str, Any]]
    clamav: ClamavInfo
    responseTime: Optional[float] = None
    statusCode: Optional[int] = None
    timestamp: str
    categoryDistribution: List[CategoryDistribution]
    threatBreakdown: List[ThreatBreakdown]
    timeline: List[Timeline]
