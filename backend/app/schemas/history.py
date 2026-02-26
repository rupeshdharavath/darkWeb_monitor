"""
History-related Pydantic schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HistoryItemResponse(BaseModel):
    """Single history item in list view"""
    id: str
    url: str
    title: str
    threat_score: int
    risk_level: str
    category: str
    timestamp: Optional[str] = None
    url_status: str


class HistoryListResponse(BaseModel):
    """List of history items"""
    history: List[HistoryItemResponse]


class ClamavInfo(BaseModel):
    """ClamAV scan information"""
    status: Optional[str] = None
    detected: bool = False
    details: List[Any] = []


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


class HistoryDetailResponse(BaseModel):
    """Detailed history entry"""
    status: str
    url: str
    threatScore: int
    category: str
    riskLevel: str
    confidence: int
    threatIndicators: Dict[str, Any]
    pgpDetected: bool
    emails: List[str]
    cryptoAddresses: List[str]
    contentChanged: bool
    contentHash: str
    title: str
    textPreview: str
    keywords: List[str]
    links: List[Dict[str, str]]
    fileLinks: List[Dict[str, Any]]
    fileAnalysis: List[Dict[str, Any]]
    clamav: ClamavInfo
    responseTime: Optional[float] = None
    statusCode: Optional[int] = None
    timestamp: str
    categoryDistribution: List[CategoryDistribution]
    threatBreakdown: List[ThreatBreakdown]
    timeline: List[Timeline]
