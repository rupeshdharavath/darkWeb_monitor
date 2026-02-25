"""
Flask server exposing /scan endpoint for the frontend dashboard.
"""

from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

from app.tor_proxy import create_tor_session, test_tor_connection
from app.scraper import scrape_url
from app.parser import parse_html
from app.analyzer import analyze_content
from app.database import DatabaseManager
from app.utils import sanitize_url
from app.downloader import download_file
from app.file_analyzer import analyze_file


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


def _trim_list(items: Optional[List[Any]], limit: int = 8) -> List[Any]:
    if not items:
        return []
    return items[:limit]


def _trim_links(links: Optional[List[Dict[str, Any]]], limit: int = 8) -> List[Dict[str, Any]]:
    if not links:
        return []
    return [
        {"url": link.get("url", ""), "text": link.get("text")}
        for link in links[:limit]
    ]


def detect_pgp(text: str) -> bool:
    lowered = (text or "").lower()
    return "pgp" in lowered or "-----begin pgp" in lowered


def create_session_for_url(url: str):
    if ".onion" in url.lower():
        session = create_tor_session()
        if not test_tor_connection(session):
            session.close()
            return None, "Tor connection failed"
        return session, None
    return create_tor_session(), None


app = Flask(__name__)
CORS(app)


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


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"})


@app.route("/history", methods=["GET"])
def get_history() -> Any:
    """Get all scan history sorted by newest first"""
    db_manager = DatabaseManager()
    if db_manager.collection is None:
        return jsonify({"detail": "Database connection failed"}), 500
    
    try:
        # Get all unique URLs with their latest scan
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$url",
                "latest_scan": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_scan"}},
            {"$sort": {"timestamp": -1}},
            {"$limit": 100}
        ]
        
        entries = list(db_manager.collection.aggregate(pipeline))
        
        history = []
        for entry in entries:
            history.append({
                "id": str(entry.get("_id")),
                "url": entry.get("url"),
                "title": entry.get("title") or "Unknown",
                "threat_score": entry.get("threat_score") or 0,
                "risk_level": entry.get("risk_level") or "LOW",
                "category": entry.get("category") or "Unknown",
                "timestamp": entry.get("timestamp"),
                "url_status": entry.get("url_status") or "UNKNOWN"
            })
        
        return jsonify({"history": history})
    
    finally:
        db_manager.close()


@app.route("/history/<entry_id>", methods=["GET"])
def get_history_entry(entry_id: str) -> Any:
    """Get specific scan entry by ID"""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    db_manager = DatabaseManager()
    if db_manager.collection is None:
        return jsonify({"detail": "Database connection failed"}), 500
    
    try:
        try:
            obj_id = ObjectId(entry_id)
        except InvalidId:
            return jsonify({"detail": "Invalid entry ID"}), 400
        
        entry = db_manager.collection.find_one({"_id": obj_id})
        if not entry:
            return jsonify({"detail": "Entry not found"}), 404
        
        # Format response same as /scan endpoint
        emails = entry.get("emails_found") or []
        crypto_addresses = entry.get("crypto_addresses") or []
        threat_score = entry.get("threat_score") or 0
        category = entry.get("category") or "Unknown"
        text_content = entry.get("text_preview", "")
        risk_level = entry.get("risk_level") or "LOW"
        confidence = entry.get("confidence") or 0
        threat_indicators = entry.get("threat_indicators") or {}
        response_time = entry.get("response_time")
        status_code = entry.get("status_code")
        title = entry.get("title") or "Unknown"
        keywords = entry.get("keywords") or []
        links = entry.get("links") or []
        file_links = entry.get("file_links") or []
        file_analysis = entry.get("file_analysis") or []
        clamav_status = entry.get("clamav_status")
        clamav_detected = entry.get("clamav_detected", False)
        clamav_details = entry.get("clamav_details") or []
        content_hash = entry.get("content_hash") or ""
        timestamp = entry.get("timestamp") or ""
        url = entry.get("url") or ""

        response = {
            "status": entry.get("url_status", "UNKNOWN"),
            "url": url,
            "threatScore": threat_score,
            "category": category,
            "riskLevel": risk_level,
            "confidence": confidence,
            "threatIndicators": threat_indicators,
            "pgpDetected": detect_pgp(text_content),
            "emails": emails,
            "cryptoAddresses": crypto_addresses,
            "contentChanged": entry.get("content_changed", False),
            "contentHash": content_hash,
            "title": title,
            "textPreview": text_content,
            "keywords": _trim_list(keywords, 12),
            "links": _trim_links(links, 8),
            "fileLinks": _trim_list(file_links, 8),
            "fileAnalysis": _trim_list(file_analysis, 8),
            "clamav": {
                "status": clamav_status,
                "detected": clamav_detected,
                "details": _trim_list(clamav_details, 5)
            },
            "responseTime": response_time,
            "statusCode": status_code,
            "timestamp": timestamp,
            "categoryDistribution": build_category_distribution(category),
            "threatBreakdown": build_threat_breakdown(emails, crypto_addresses, threat_score),
            "timeline": build_timeline(entry.get("status_history", []))
        }
        return jsonify(response)
    
    finally:
        db_manager.close()


@app.route("/scan", methods=["POST"])
def scan_url() -> Any:
    payload = request.get_json(silent=True) or {}
    url = sanitize_url(payload.get("url"))
    if not url:
        return jsonify({"detail": "Invalid URL. Include http:// or https://"}), 400

    db_manager = DatabaseManager()
    if db_manager.collection is None:
        return jsonify({"detail": "Database connection failed"}), 500

    session = None
    try:
        session, session_error = create_session_for_url(url)
        if session_error:
            return jsonify({"detail": session_error}), 503
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
                file_links = parsed_data.get("file_links", [])
                file_analysis_results = []
                clamav_detected = False

                for file_link in file_links:
                    try:
                        file_url = file_link.get("url")
                        download_result = download_file(session, file_url, base_url=url)
                        if download_result.get("success"):
                            analysis_result = analyze_file(download_result.get("filepath"))
                            if analysis_result.get("clamav_detected"):
                                clamav_detected = True
                            file_analysis_results.append({
                                "file_url": file_url,
                                "file_name": download_result.get("filename"),
                                "file_size": download_result.get("file_size"),
                                "file_hash": download_result.get("file_hash"),
                                "content_type": download_result.get("content_type"),
                                "analysis": analysis_result
                            })
                    except Exception:
                        continue

                analysis_result = analyze_content(
                    parsed_data.get("text_content", ""),
                    parsed_data.get("keywords", []),
                    clamav_detected
                )
                parsed_data.update(analysis_result)

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
            return jsonify({"detail": "Failed to store scan result"}), 500

        emails = latest.get("emails_found") or []
        crypto_addresses = latest.get("crypto_addresses") or []
        threat_score = latest.get("threat_score") or 0
        category = latest.get("category") or "Unknown"
        text_content = latest.get("text_preview", "")
        risk_level = latest.get("risk_level") or "LOW"
        confidence = latest.get("confidence") or 0
        threat_indicators = latest.get("threat_indicators") or {}
        response_time = latest.get("response_time")
        status_code = latest.get("status_code")
        title = latest.get("title") or "Unknown"
        keywords = latest.get("keywords") or []
        links = latest.get("links") or []
        file_links = latest.get("file_links") or []
        file_analysis = latest.get("file_analysis") or []
        clamav_status = latest.get("clamav_status")
        clamav_detected = latest.get("clamav_detected", False)
        clamav_details = latest.get("clamav_details") or []
        content_hash = latest.get("content_hash") or ""
        timestamp = latest.get("timestamp") or ""

        response = {
            "status": latest.get("url_status", "UNKNOWN"),
            "threatScore": threat_score,
            "category": category,
            "riskLevel": risk_level,
            "confidence": confidence,
            "threatIndicators": threat_indicators,
            "pgpDetected": detect_pgp(text_content),
            "emails": emails,
            "cryptoAddresses": crypto_addresses,
            "contentChanged": latest.get("content_changed", False),
            "contentHash": content_hash,
            "title": title,
            "textPreview": text_content,
            "keywords": _trim_list(keywords, 12),
            "links": _trim_links(links, 8),
            "fileLinks": _trim_list(file_links, 8),
            "fileAnalysis": _trim_list(file_analysis, 8),
            "clamav": {
                "status": clamav_status,
                "detected": clamav_detected,
                "details": _trim_list(clamav_details, 5)
            },
            "responseTime": response_time,
            "statusCode": status_code,
            "timestamp": timestamp,
            "categoryDistribution": build_category_distribution(category),
            "threatBreakdown": build_threat_breakdown(emails, crypto_addresses, threat_score),
            "timeline": build_timeline(latest.get("status_history", []))
        }
        return jsonify(response)

    finally:
        if session:
            session.close()
        db_manager.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
