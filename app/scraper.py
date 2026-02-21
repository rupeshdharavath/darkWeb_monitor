"""
Web Scraping Logic
Handles fetching content from dark web sites
"""

import time
import random
from app.config import REQUEST_TIMEOUT, DELAY_BETWEEN_REQUESTS
from app.utils import logger


MAX_RETRIES = 3


def scrape_url(session, url):
    """
    Scrape content from a given URL using the provided session
    """

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Scraping URL: {url} (Attempt {attempt+1})")

            response = session.get(url, timeout=REQUEST_TIMEOUT)
            logger.info(f"Status Code: {response.status_code}")

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")

            if "text/html" not in content_type:
                logger.warning(f"Non-HTML content at {url}")
                return None

            logger.info(f"Successfully scraped {url}")
            return response.text

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
            else:
                logger.error(f"Failed after {MAX_RETRIES} attempts")

    return None


def scrape_multiple_urls(session, url_list):
    """
    Scrape multiple URLs with delay between requests
    """

    results = {}

    for url in url_list:
        content = scrape_url(session, url)
        results[url] = content

        # Randomized delay to reduce detection
        sleep_time = random.uniform(
            DELAY_BETWEEN_REQUESTS,
            DELAY_BETWEEN_REQUESTS + 3
        )
        time.sleep(sleep_time)

    logger.info(f"Completed scraping {len(url_list)} URLs")
    return results