"""
FastAPI server exposing /scan endpoint for the frontend dashboard.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.tor_proxy import create_tor_session, test_tor_connection
from app.scraper import scrape_url
from app.parser import parse_html
from app.analyzer import analyze_content
from app.database import DatabaseManager
from app.utils import sanitize_url
from app.downloader import download_file


class ScanRequest(BaseModel):
    url: str


def build_category_distribution(category: str) -> List[Dict[str, Any]]:
    if not category:
        return []
    return [{"name": category, "value": 1}]


def build_threat_breakdown(emails: List[str], crypto_addresses: List[str], threat_score: int) -> List[Dict[str, Any]]:
    return [
        {"label": "Emails", "value": len(emails)},
        {"label": "Crypto", "value": len(crypto_addresses)},
        {"label": "Threat", "value": threat_score},
    ]


def build_timeline(status_history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not status_history:
        return []
    timeline = []
    for entry in status_history[-12:]:
        timeline.append({
            "time": entry.get("timestamp", ""),
            "value": entry.get("response_time") or 0
        })
    return timeline


def detect_pgp(text: str) -> bool:
    lowered = (text or "").lower()
    return "pgp" in lowered or "-----begin pgp" in lowered


def create_session_for_url(url: str):
    if ".onion" in url.lower():
        session = create_tor_session()
        if not test_tor_connection(session):
            session.close()
            raise HTTPException(status_code=503, detail="Tor connection failed")
        return session
    return create_tor_session()


app = FastAPI(title="Darkweb Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def _store_minimal_entry(db_manager: DatabaseManager, url: str, url_status: str, response_time: Optional[float], status_code: Optional[int]):
    db_manager.insert_scraped_data(
        url,
        {
            "text_content": "",
            "text_preview": f"Failed to retrieve content - Status: {url_status}",
            "links": [],
            "keywords": [],
            "title": f"[{url_status}] Unable to fetch content",
            "threat_score": 0,
            "category": "Unknown",
            "risk_level": "LOW",
            "confidence": 0,
            "emails_found": [],
            "crypto_addresses": [],
            "content_hash": "",
            "file_links": []
        },
        url_status=url_status,
        response_time=response_time,
        status_code=status_code
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/scan")
def scan_url(payload: ScanRequest) -> Dict[str, Any]:
    url = sanitize_url(payload.url)
    if not url:
        raise HTTPException(status_code=400, detail="Invalid URL. Include http:// or https://")

    db_manager = DatabaseManager()
    if db_manager.collection is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    session = None
    try:
        session = create_session_for_url(url)
        html_content, status_info = scrape_url(session, url)
        url_status = status_info.get("status", "UNKNOWN")
        response_time = status_info.get("response_time")
        status_code = status_info.get("status_code")

        if not html_content:
            _store_minimal_entry(db_manager, url, url_status, response_time, status_code)
        else:
            parsed_data = parse_html(html_content, base_url=url)
            if not parsed_data:
                _store_minimal_entry(db_manager, url, url_status, response_time, status_code)
            else:
                analysis_result = analyze_content(
                    parsed_data.get("text_content", ""),
                    parsed_data.get("keywords", [])
                )
                parsed_data.update(analysis_result)

                file_links = parsed_data.get("file_links", [])
                file_analysis_results = []

                for file_link in file_links:
                    try:
                        file_url = file_link.get("url")
                        download_result = download_file(session, file_url, base_url=url)
                        if download_result.get("success"):
                            file_analysis_results.append({
                                "file_url": file_url,
                                "file_name": download_result.get("filename"),
                                "file_size": download_result.get("file_size"),
                                "file_hash": download_result.get("file_hash"),
                                "content_type": download_result.get("content_type"),
                                "analysis": {}
                            })
                    except Exception:
                        continue

                if file_analysis_results:
                    parsed_data["file_analysis"] = file_analysis_results

                db_manager.insert_scraped_data(
                    url,
                    parsed_data,
                    url_status=url_status,
                    response_time=response_time,
                    status_code=status_code
                )

        latest = db_manager.collection.find_one({"url": url}, sort=[("timestamp", -1)])
        if not latest:
            raise HTTPException(status_code=500, detail="Failed to store scan result")

        emails = latest.get("emails_found") or []
        crypto_addresses = latest.get("crypto_addresses") or []
        threat_score = latest.get("threat_score") or 0
        category = latest.get("category") or "Unknown"
        text_content = latest.get("text_preview", "")

        response = {
            "status": latest.get("url_status", "UNKNOWN"),
            "threatScore": threat_score,
            "category": category,
            "pgpDetected": detect_pgp(text_content),
            "emails": emails,
            "cryptoAddresses": crypto_addresses,
            "contentChanged": latest.get("content_changed", False),
            "categoryDistribution": build_category_distribution(category),
            "threatBreakdown": build_threat_breakdown(emails, crypto_addresses, threat_score),
            "timeline": build_timeline(latest.get("status_history", []))
        }
        return response

    finally:
        if session:
            session.close()
        db_manager.close()
