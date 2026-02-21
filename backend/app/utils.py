"""
Utility Functions
Helper functions for timestamps, logging, etc.
"""

import os
from datetime import datetime
from app.logger import logger


def get_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def format_timestamp(timestamp_str):
    """Format timestamp string for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str


def sanitize_url(url):
    """Sanitize and validate URL"""

    if not url:
        return None

    url = url.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        logger.warning(f"Invalid URL scheme: {url}")
        return None

    return url


def log_error(error_msg, exception=None):
    """Log error with optional exception details"""

    if exception:
        logger.error(f"{error_msg}: {str(exception)}", exc_info=True)
    else:
        logger.error(error_msg)