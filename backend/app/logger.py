"""
Professional Logging System for DarkWeb Monitor
Implements rotating file handlers for system logs and alerts
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create main logger
logger = logging.getLogger("darkweb_monitor")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if logger is reloaded
if not logger.handlers:
    
    # ===================================
    # SYSTEM LOG HANDLER (All Events)
    # ===================================
    system_handler = RotatingFileHandler(
        "logs/system.log",
        maxBytes=5 * 1024 * 1024,   # 5MB per file
        backupCount=3,               # Keep 3 backup files
        encoding='utf-8'
    )
    system_handler.setLevel(logging.DEBUG)
    
    # ===================================
    # ALERT LOG HANDLER (Warnings + Errors Only)
    # ===================================
    alert_handler = RotatingFileHandler(
        "logs/alerts.log",
        maxBytes=2 * 1024 * 1024,    # 2MB per file
        backupCount=2,                # Keep 2 backup files
        encoding='utf-8'
    )
    alert_handler.setLevel(logging.WARNING)  # Only WARNING, ERROR, CRITICAL
    
    # ===================================
    # CONSOLE HANDLER (User Visibility)
    # ===================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # ===================================
    # LOG FORMAT
    # ===================================
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Apply formatter to all handlers
    system_handler.setFormatter(log_formatter)
    alert_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)
    
    # Add handlers to logger
    logger.addHandler(system_handler)
    logger.addHandler(alert_handler)
    logger.addHandler(console_handler)


# Convenience functions for specific event types
def log_url_status(url, status, response_time=None):
    """Log URL status with consistent format"""
    if response_time:
        message = f"{url} is {status} (Response time: {response_time:.2f}s)"
    else:
        message = f"{url} is {status}"
    
    if status == "ONLINE":
        logger.info(message)
    elif status == "TIMEOUT":
        logger.warning(message)
    elif status == "OFFLINE":
        logger.error(message)
    else:
        logger.warning(message)


def log_threat_detection(url, threat_score, category, risk_level):
    """Log threat detection events"""
    message = f"Threat detected - {url} | Score: {threat_score} | Category: {category} | Risk: {risk_level}"
    
    if threat_score > 70:
        logger.warning(message)
    elif threat_score > 50:
        logger.info(message)
    else:
        logger.debug(message)


def log_ioc_reuse(ioc_type, ioc_value, reuse_count):
    """Log IOC reuse detection"""
    logger.warning(f"IOC REUSE DETECTED - {ioc_type.upper()}: {ioc_value} (found on {reuse_count} URLs)")


def log_content_change(url):
    """Log content change detection"""
    logger.warning(f"CONTENT CHANGE DETECTED - {url}")


def log_malware_detected(url, malware_info):
    """Log malware detection"""
    logger.critical(f"MALWARE DETECTED - {url} | Details: {malware_info}")
