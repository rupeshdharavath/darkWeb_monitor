"""
Utility Functions
Helper functions for timestamps, logging, etc.
"""

import logging
import os
from datetime import datetime
from app.config import LOG_FILE, LOG_LEVEL


# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


# Configure logging only once
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)


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