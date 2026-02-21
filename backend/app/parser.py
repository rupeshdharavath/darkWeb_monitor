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
DOWNLOADABLE_EXTENSIONS = {
    # Archives
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    # Executables
    ".exe", ".dll", ".so", ".app", ".bin", ".msi",
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".rtf", ".odt",
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
    ".tiff", ".ico", ".psd",
    # Video/Audio
    ".mp4", ".avi", ".mov", ".mkv", ".flv", ".mp3", ".wav",
    ".flac", ".aac", ".ogg",
    # Code
    ".py", ".js", ".java", ".cpp", ".c", ".go", ".rs",
    ".sh", ".bat", ".ps1",
    # Other
    ".iso", ".img", ".dmg", ".apk", ".deb", ".rpm"
}


def detect_file_links(links, base_url=None):
    """Detect downloadable files from link list"""
    file_links = []
    
    for link in links:
        url = link.get("url", "")
        # Check if URL has downloadable extension
        for ext in DOWNLOADABLE_EXTENSIONS:
            if url.lower().endswith(ext):
                file_links.append({
                    "url": url,
                    "text": link.get("text", ""),
                    "extension": ext
                })
                break
    
    return file_links


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

        # Extract text content with proper spacing between block elements
        text_content = soup.get_text("\n")
        text_content = text_content.replace("\n", " ")
        text_content = re.sub(r"\s+", " ", text_content).strip()

        # Include text from code-heavy containers (e.g., Pastebin)
        extra_blocks = []
        for tag in soup.find_all(["textarea", "pre", "code"]):
            block_text = tag.get_text("\n", strip=True)
            if block_text:
                block_text = re.sub(r"\s+", " ", block_text).strip()
                extra_blocks.append(block_text)
        if extra_blocks:
            text_content = f"{text_content} {' '.join(extra_blocks)}"

        # Include link URLs in text content so indicators in hrefs are detected
        link_urls = [link["url"] for link in links if link.get("url")]
        if link_urls:
            text_content = f"{text_content} {' '.join(link_urls)}"

        text_content = re.sub(r"\s+", " ", text_content).strip()

        # Extract keywords
        keywords = extract_keywords(text_content)

        # Extract downloadable file links
        file_links = detect_file_links(links, base_url)

        parsed_data = {
            "title": title_text,
            "links": links,
            "file_links": file_links,  # NEW: Downloaded file links
            "keywords": keywords,
            "text_preview": text_content[:500],
            "text_content": text_content  # FULL TEXT FOR ANALYZER
        }

        logger.info(f"Successfully parsed HTML - Title: {title_text}")
        if file_links:
            logger.info(f"Found {len(file_links)} downloadable files")
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