"""
HTML Parser
Extracts titles, links, keywords from scraped content
"""

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
import re
from app.utils import logger


MAX_LINKS = 200


def parse_html(html_content, base_url=None):

    if not html_content:
        return None

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else "No title"

        # Extract links
        links = []
        for link in soup.find_all("a", href=True)[:MAX_LINKS]:
            href = link["href"]

            if base_url:
                href = urljoin(base_url, href)

            link_text = link.get_text(strip=True)

            links.append({
                "url": href,
                "text": link_text if link_text else None
            })

        # Extract text content
        text_content = soup.get_text(separator=" ", strip=True)

        # Extract keywords
        keywords = extract_keywords(text_content)

        parsed_data = {
            "title": title_text,
            "links": links,
            "keywords": keywords,
            "text_preview": text_content[:500]
        }

        logger.info(f"Successfully parsed HTML - Title: {title_text}")
        return parsed_data

    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return None


def extract_keywords(text, top_n=10):

    words = re.findall(r"\b[a-z]{3,}\b", text.lower())

    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all",
        "can", "her", "was", "one", "our", "out", "this",
        "that", "with", "from", "have", "has", "had"
    }

    filtered_words = [word for word in words if word not in stop_words]

    word_freq = Counter(filtered_words)

    return [word for word, _ in word_freq.most_common(top_n)]