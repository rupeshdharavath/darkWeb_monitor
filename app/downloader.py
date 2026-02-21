"""
Downloader Module
Downloads files from URLs via Tor session with safety limits
"""

import os
import hashlib
from urllib.parse import urljoin, urlparse
from app.utils import logger

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DOWNLOAD_TIMEOUT = 30
DOWNLOADS_DIR = "data/downloads"


def get_safe_filename(url, content_type=""):
    """Generate safe filename from URL"""
    parsed = urlparse(url)
    filename = parsed.path.split("/")[-1]
    
    if not filename or filename == "":
        # Generate hash-based name if no filename in URL
        filename = hashlib.md5(url.encode()).hexdigest()[:12]
    
    # Remove potentially dangerous characters
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    return filename[:100]  # Limit filename length


def download_file(session, url, base_url=None):
    """
    Download file via Tor session with safety checks
    
    Args:
        session: Requests session with Tor proxy
        url: File URL to download
        base_url: Base URL for relative links
    
    Returns:
        dict: {
            "success": bool,
            "filename": str,
            "filepath": str,
            "file_size": int,
            "content_type": str,
            "file_hash": str,
            "error": str (if failed)
        }
    """
    
    try:
        # Resolve relative URLs
        if base_url:
            url = urljoin(base_url, url)
        
        logger.info(f"📥 Downloading file from {url}")
        
        # HEAD request to check file size first
        try:
            head_response = session.head(
                url,
                timeout=DOWNLOAD_TIMEOUT,
                allow_redirects=True
            )
            content_length = head_response.headers.get('content-length', 0)
            
            try:
                content_length = int(content_length)
            except (ValueError, TypeError):
                content_length = 0
            
            # Check file size limit
            if content_length > MAX_FILE_SIZE:
                logger.warning(f"⚠️ File too large: {content_length / (1024*1024):.2f} MB (limit: {MAX_FILE_SIZE / (1024*1024):.0f} MB)")
                return {
                    "success": False,
                    "error": f"File too large: {content_length / (1024*1024):.2f} MB"
                }
        
        except Exception as e:
            logger.warning(f"⚠️ Could not verify file size: {e}")
        
        # Download file
        response = session.get(
            url,
            timeout=DOWNLOAD_TIMEOUT,
            allow_redirects=True,
            stream=True
        )
        
        response.raise_for_status()
        
        # Create downloads directory if needed
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        
        content_type = response.headers.get('content-type', 'application/octet-stream')
        filename = get_safe_filename(url, content_type)
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        
        # Download with size limit check
        file_hash = hashlib.sha256()
        total_size = 0
        chunk_size = 8192
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    total_size += len(chunk)
                    
                    # Check size limit during download
                    if total_size > MAX_FILE_SIZE:
                        logger.warning(f"⚠️ Download exceeded size limit during transfer")
                        f.close()
                        os.remove(filepath)
                        return {
                            "success": False,
                            "error": f"File exceeded size limit during download"
                        }
                    
                    f.write(chunk)
                    file_hash.update(chunk)
        
        logger.info(f"✅ Downloaded {filename} ({total_size / 1024:.2f} KB)")
        
        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "file_size": total_size,
            "content_type": content_type,
            "file_hash": file_hash.hexdigest(),
            "error": None
        }
    
    except Exception as e:
        logger.error(f"❌ Error downloading file: {e}")
        return {
            "success": False,
            "error": str(e)
        }
