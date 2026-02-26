"""
API Route modules
"""

from .health import router as health_router
from .scan import router as scan_router
from .monitors import router as monitors_router
from .alerts import router as alerts_router
from .history import router as history_router

__all__ = [
    "health_router",
    "scan_router",
    "monitors_router",
    "alerts_router",
    "history_router",
]
