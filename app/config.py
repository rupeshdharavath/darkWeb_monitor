"""
Configuration settings for DarkWeb Monitor
Includes Tor proxy settings, database configuration, scraping settings,
and logging configuration.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==============================
# Tor Configuration
# ==============================

TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}


# ==============================
# MongoDB Configuration
# ==============================

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "darkweb_monitor")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "scraped_data")

if not MONGODB_URI:
    raise ValueError("❌ MONGODB_URI not found in environment variables (.env file)")


# ==============================
# Scraping Settings
# ==============================

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
DELAY_BETWEEN_REQUESTS = int(os.getenv("DELAY_BETWEEN_REQUESTS", 5))

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT
}


# ==============================
# Logging Configuration
# ==============================

LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

LOG_LEVEL = getattr(
    logging,
    os.getenv("LOG_LEVEL", "INFO").upper(),
    logging.INFO
)