"""
Tor proxy session setup.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.utils import logger


TOR_TEST_URL = "https://check.torproject.org"


def create_tor_session() -> requests.Session:
    """Create a requests session configured to use Tor proxy."""
    session = requests.Session()

    # Apply Tor proxy and headers
    session.proxies.update(settings.tor_proxy)
    session.headers.update(settings.headers)

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logger.info("Tor session created successfully")
    return session


def test_tor_connection(session: requests.Session) -> bool:
    """Test if Tor connection is working."""
    try:
        response = session.get(TOR_TEST_URL, timeout=settings.request_timeout)
        response.raise_for_status()

        if "Congratulations" in response.text:
            logger.info("Tor connection verified successfully")
            return True

        logger.warning("Tor connection may not be working properly")
        return False
    except Exception as exc:
        logger.error(f"Error testing Tor connection: {exc}")
        return False
