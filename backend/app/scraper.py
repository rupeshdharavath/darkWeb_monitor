"""
Web Scraping Logic
Handles fetching content from dark web sites
"""

import time
import random
import requests
from app.core.config import settings
from app.utils import logger


MAX_RETRIES = 3

# Tor SOCKS5 Proxy Configuration
TOR_PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}


def fetch_url(url):
    """
    Fetch URL with granular status classification.
    Automatically detects if Tor proxy is needed based on URL.
    
    Returns:
        {
            "status": "ONLINE" | "OFFLINE" | "TIMEOUT" | "ERROR",
            "content": response.text or None,
            "response_time": float (seconds),
            "status_code": int or None,
            "response_headers": dict
        }
    """
    start_time = time.time()
    
    # Detect if this is a .onion URL (needs Tor)
    use_tor = ".onion" in url.lower()
    proxies = TOR_PROXIES if use_tor else None
    
    if use_tor:
        logger.debug(f"Using Tor proxy for .onion URL: {url}")
    
    try:
        response = requests.get(
            url,
            proxies=proxies,
                timeout=settings.request_timeout,
            verify=False  # Ignore SSL cert warnings for darkweb
        )
        response_time = time.time() - start_time
        
        # Successful response
        if response.status_code == 200:
            logger.info(f"✅ URL ONLINE: {url} (Time: {response_time:.2f}s)")
            return {
                "status": "ONLINE",
                "content": response.text,
                "response_time": response_time,
                "status_code": response.status_code,
                "response_headers": dict(response.headers)
            }
        else:
            logger.warning(f"⚠️ URL ERROR: {url} (HTTP {response.status_code})")
            return {
                "status": "ERROR",
                "content": None,
                "response_time": response_time,
                "status_code": response.status_code,
                "response_headers": {}
            }
    
    except requests.exceptions.ConnectTimeout:
        response_time = time.time() - start_time
        logger.warning(f"⏱️ URL TIMEOUT: {url} (Time: {response_time:.2f}s)")
        return {
            "status": "TIMEOUT",
            "content": None,
            "response_time": response_time,
            "status_code": None
        }
    
    except requests.exceptions.ReadTimeout:
        response_time = time.time() - start_time
        logger.warning(f"⏱️ URL READ TIMEOUT: {url} (Time: {response_time:.2f}s)")
        return {
            "status": "TIMEOUT",
            "content": None,
            "response_time": response_time,
            "status_code": None
        }
    
    except requests.exceptions.ConnectionError:
        response_time = time.time() - start_time
        logger.warning(f"🔴 URL OFFLINE: {url} (Time: {response_time:.2f}s)")
        return {
            "status": "OFFLINE",
            "content": None,
            "response_time": response_time,
            "status_code": None
        }
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"❌ URL ERROR: {url} - {e} (Time: {response_time:.2f}s)")
        return {
            "status": "ERROR",
            "content": None,
            "response_time": response_time,
            "status_code": None
        }


def scrape_url(session, url):
    """
    Scrape content from a given URL using the provided session.
    Returns Both status and content.
    """
    
    # Use new fetch_url for status detection
    fetch_result = fetch_url(url)
    
    if fetch_result["status"] != "ONLINE":
        # Return empty content with status info
        return None, fetch_result
    
    html_content = fetch_result["content"]
    
    # Special handling for Pastebin to fetch raw content
    if "pastebin.com/" in url and "/raw/" not in url:
        paste_id = url.rstrip("/").split("/")[-1]
        raw_url = f"https://pastebin.com/raw/{paste_id}"
        try:
            logger.info(f"Attempting Pastebin raw URL: {raw_url}")
            raw_result = fetch_url(raw_url)
            if raw_result["status"] == "ONLINE" and raw_result["content"]:
                logger.info(f"Successfully scraped raw Pastebin content: {raw_url}")
                html_content = raw_result["content"]
        except Exception as e:
            logger.warning(f"Pastebin raw fetch failed, falling back to HTML: {e}")
    
    # Check content type if available
    content_type = fetch_result.get("response_headers", {}).get("Content-Type", "").lower()
    
    # Be more lenient - only reject if we KNOW it's binary content
    # Allow empty content_type (some sites don't send it) or text-based types
    if content_type and not any(t in content_type for t in ["text/", "application/json", "application/xml"]):
        logger.warning(f"Non-text content at {url} (Content-Type: {content_type})")
        return None, fetch_result
    
    # Validate we actually have content
    if not html_content or len(html_content.strip()) == 0:
        logger.warning(f"Empty content received from {url}")
        return None, fetch_result
    
    logger.info(f"Successfully processed {url}")
    return html_content, fetch_result


def scrape_multiple_urls(session, url_list):
    """
    Scrape multiple URLs with delay between requests.
    Returns dict with url as key and (content, status_info) tuples as values.
    """

    results = {}

    for url in url_list:
        content, status_info = scrape_url(session, url)
        results[url] = (content, status_info)

        # Randomized delay to reduce detection
            sleep_time = random.uniform(
                settings.delay_between_requests,
                settings.delay_between_requests + 3
        )
        time.sleep(sleep_time)

    logger.info(f"Completed scraping {len(url_list)} URLs")
    return results