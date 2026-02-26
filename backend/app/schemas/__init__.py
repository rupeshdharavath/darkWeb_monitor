"""
Pydantic schemas for request/response validation
"""

from .scan import (
    ScanRequest,
    ScanResponse,
    ClamavInfo,
    ThreatIndicators,
    CategoryDistribution,
    ThreatBreakdown,
    Timeline
)

from .monitor import (
    MonitorCreateRequest,
    MonitorCreateResponse,
    MonitorResponse,
    MonitorListResponse,
    LastScanData
)

from .alert import (
    AlertResponse,
    AlertListResponse,
    AcknowledgeResponse
)

from .history import (
    HistoryItemResponse,
    HistoryListResponse,
    HistoryDetailResponse
)

from .common import (
    HealthResponse,
    ComparisonResponse,
    ScanData,
    ChangeData
)

__all__ = [
    "ScanRequest",
    "ScanResponse",
    "ClamavInfo",
    "ThreatIndicators",
    "CategoryDistribution",
    "ThreatBreakdown",
    "Timeline",
    "MonitorCreateRequest",
    "MonitorCreateResponse",
    "MonitorResponse",
    "MonitorListResponse",
    "LastScanData",
    "AlertResponse",
    "AlertListResponse",
    "AcknowledgeResponse",
    "HealthResponse",
    "ComparisonResponse",
    "ScanData",
    "ChangeData",
    "HistoryItemResponse",
    "HistoryListResponse",
    "HistoryDetailResponse",
]
