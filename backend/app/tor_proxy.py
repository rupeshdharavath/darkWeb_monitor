"""
Tor Proxy Session Setup
Handles connection to Tor network for anonymous scraping
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.config import TOR_PROXY, REQUEST_TIMEOUT, USER_AGENT
from app.utils import logger


TOR_TEST_URL = "https://check.torproject.org"


def create_tor_session():
    """
    Create a requests session configured to use Tor proxy
    """

    session = requests.Session()

    # Apply Tor proxy
    session.proxies.update(TOR_PROXY)
    session.headers.update({"User-Agent": USER_AGENT})

    # Retry strategy
    retry_strategy = Retry(
        total=3,
from app.core.config import settings
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logger.info("Tor session created successfully")
    return session


    session.proxies.update(settings.tor_proxy)
    session.headers.update(settings.headers)
    Test if Tor connection is working
    """

    try:
        response = session.get(TOR_TEST_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        if "Congratulations" in response.text:
            logger.info("Tor connection verified successfully")
            return True
        else:
            logger.warning("Tor connection may not be working properly")
            return False

    except Exception as e:
        logger.error(f"Error testing Tor connection: {e}")
        return False