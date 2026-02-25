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
from app.utils import sanitize_url, logger
from app.downloader import download_file
from app.file_analyzer import analyze_file
from app.monitor import monitor_manager


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


@app.route("/monitors", methods=["GET"])
def list_monitors() -> Any:
    """Get all active monitors with last scan details"""
    monitors = monitor_manager.list_monitors()
    db_manager = DatabaseManager()
    
    try:
        # Enrich each monitor with last scan data
        enriched_monitors = []
        for monitor_id, monitor_data in monitors.items():
            # Get last scan for this URL
            last_scan = db_manager.collection.find_one(
                {"url": monitor_data["url"]},
                sort=[("timestamp", -1)]
            )
            
            # Check if monitor is paused
            try:
                job = monitor_manager.scheduler.get_job(monitor_id)
                is_paused = job is not None and job.next_run_time is None
            except:
                is_paused = False
            
            monitor_info = {
                "monitor_id": monitor_id,
                **monitor_data,
                "paused": is_paused,
                "last_scan_data": None
            }
            
            if last_scan:
                monitor_info["last_scan_data"] = {
                    "threat_score": last_scan.get("threat_score", 0),
                    "status": last_scan.get("url_status", "UNKNOWN"),
                    "risk_level": last_scan.get("risk_level", "LOW"),
                    "category": last_scan.get("category", "Unknown"),
                    "emails_count": len(last_scan.get("emails_found", [])),
                    "urls_count": len(last_scan.get("urls_found", [])),
                    "ips_count": len(last_scan.get("ip_addresses", [])),
                    "crypto_count": len(last_scan.get("crypto_addresses", [])),
                    "clamav_detected": last_scan.get("clamav_detected", False)
                }
            
            enriched_monitors.append(monitor_info)
            
        return jsonify({"monitors": enriched_monitors})
    finally:
        db_manager.close()


@app.route("/monitors", methods=["POST"])
def create_monitor() -> Any:
    """Create a new monitoring job"""
    try:
        payload = request.get_json(silent=True) or {}
        raw_url = payload.get("url")
        logger.info(f"Received monitor creation request for URL: {raw_url}")
        
        url = sanitize_url(raw_url)
        interval = payload.get("interval", 5)  # default 5 minutes
        
        if not url:
            error_msg = f"Invalid URL: '{raw_url}'. URL must start with http:// or https://"
            logger.warning(error_msg)
            return jsonify({"detail": error_msg}), 400
        
        # Check monitor limit (max 5)
        current_monitors = monitor_manager.list_monitors()
        if len(current_monitors) >= 5:
            return jsonify({"detail": "Maximum 5 monitors allowed. Please delete an existing monitor to add a new one."}), 400
        
        # Generate monitor ID
        import hashlib
        monitor_id = hashlib.md5(url.encode()).hexdigest()[:12]
        
        logger.info(f"Creating monitor for URL: {url} with ID: {monitor_id}")
        
        success, error_msg = monitor_manager.add_monitor(monitor_id, url, interval)
        
        if success:
            logger.info(f"Monitor created successfully: {monitor_id}")
            return jsonify({
                "monitor_id": monitor_id,
                "url": url,
                "interval": interval,
                "message": "Monitor created successfully"
            }), 201
        else:
            logger.error(f"Failed to create monitor {monitor_id}: {error_msg}")
            return jsonify({"detail": error_msg or "Failed to create monitor"}), 500
    except Exception as e:
        logger.error(f"Unexpected error creating monitor: {str(e)}", exc_info=True)
        return jsonify({"detail": f"Internal server error: {str(e)}"}), 500


@app.route("/monitors/<monitor_id>", methods=["GET"])
def get_monitor(monitor_id: str) -> Any:
    """Get specific monitor details"""
    monitor = monitor_manager.get_monitor(monitor_id)
    if not monitor:
        return jsonify({"detail": "Monitor not found"}), 404
    return jsonify(monitor)


@app.route("/monitors/<monitor_id>", methods=["DELETE"])
def delete_monitor(monitor_id: str) -> Any:
    """Delete a monitor"""
    success = monitor_manager.remove_monitor(monitor_id)
    if success:
        return jsonify({"message": "Monitor deleted successfully"})
    else:
        return jsonify({"detail": "Monitor not found"}), 404


@app.route("/monitors/all", methods=["DELETE"])
def delete_all_monitors() -> Any:
    """Delete all monitors (utility endpoint)"""
    try:
        monitors = monitor_manager.list_monitors()
        deleted_count = 0
        for monitor_id in list(monitors.keys()):
            if monitor_manager.remove_monitor(monitor_id):
                deleted_count += 1
        logger.info(f"Deleted {deleted_count} monitors")
        return jsonify({"message": f"Deleted {deleted_count} monitors", "count": deleted_count})
    except Exception as e:
        logger.error(f"Failed to delete all monitors: {str(e)}")
        return jsonify({"detail": str(e)}), 500


@app.route("/monitors/<monitor_id>/pause", methods=["POST"])
def pause_monitor(monitor_id: str) -> Any:
    """Pause a monitor"""
    success = monitor_manager.pause_monitor(monitor_id)
    if success:
        return jsonify({"message": "Monitor paused"})
    else:
        return jsonify({"detail": "Failed to pause monitor"}), 500


@app.route("/monitors/<monitor_id>/resume", methods=["POST"])
def resume_monitor(monitor_id: str) -> Any:
    """Resume a paused monitor"""
    success = monitor_manager.resume_monitor(monitor_id)
    if success:
        return jsonify({"message": "Monitor resumed"})
    else:
        return jsonify({"detail": "Failed to resume monitor"}), 500


@app.route("/alerts", methods=["GET"])
def get_alerts() -> Any:
    """Get recent alerts"""
    db_manager = DatabaseManager()
    if db_manager.alerts is None:
        return jsonify({"detail": "Database connection failed"}), 500
    
    try:
        # Get recent alerts (last 100)
        alerts = list(
            db_manager.alerts
            .find()
            .sort("timestamp", -1)
            .limit(100)
        )
        
        # Convert ObjectId to string
        for alert in alerts:
            alert["_id"] = str(alert["_id"])
        
        return jsonify({"alerts": alerts})
    finally:
        db_manager.close()


@app.route("/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id: str) -> Any:
    """Mark an alert as acknowledged"""
    from bson import ObjectId
    from bson.errors import InvalidId
    
    db_manager = DatabaseManager()
    if db_manager.alerts is None:
        return jsonify({"detail": "Database connection failed"}), 500
    
    try:
        try:
            obj_id = ObjectId(alert_id)
        except InvalidId:
            return jsonify({"detail": "Invalid alert ID"}), 400
        
        result = db_manager.alerts.update_one(
            {"_id": obj_id},
            {"$set": {"status": "acknowledged"}}
        )
        
        if result.modified_count > 0:
            return jsonify({"message": "Alert acknowledged"})
        else:
            return jsonify({"detail": "Alert not found"}), 404
    finally:
        db_manager.close()


@app.route("/compare/<url_hash>", methods=["GET"])
def compare_scans(url_hash: str) -> Any:
    """Compare last two scans for a URL"""
    import urllib.parse
    
    db_manager = DatabaseManager()
    if db_manager.collection is None:
        return jsonify({"detail": "Database connection failed"}), 500
    
    try:
        # URL is URL-encoded in the path
        decoded_url = urllib.parse.unquote(url_hash)
        # Get limit parameter
        limit = request.args.get("limit", 2, type=int)
        
        # Find scans by exact URL match
        scans = list(
            db_manager.collection
            .find({"url": decoded_url})
            .sort("timestamp", -1)
            .limit(limit)
        )
        
        if len(scans) < 2:
            return jsonify({"detail": "Not enough scans to compare"}), 404
        
        current = scans[0]
        previous = scans[1]
        
        comparison = {
            "current": {
                "timestamp": current.get("timestamp"),
                "threat_score": current.get("threat_score", 0),
                "risk_level": current.get("risk_level", "LOW"),
                "category": current.get("category", "Unknown"),
                "url_status": current.get("url_status", "UNKNOWN"),
                "content_changed": current.get("content_changed", False),
                "emails": len(current.get("emails_found", [])),
                "crypto": len(current.get("crypto_addresses", []))
            },
            "previous": {
                "timestamp": previous.get("timestamp"),
                "threat_score": previous.get("threat_score", 0),
                "risk_level": previous.get("risk_level", "LOW"),
                "category": previous.get("category", "Unknown"),
                "url_status": previous.get("url_status", "UNKNOWN"),
                "content_changed": previous.get("content_changed", False),
                "emails": len(previous.get("emails_found", [])),
                "crypto": len(previous.get("crypto_addresses", []))
            },
            "changes": {
                "threat_score_delta": current.get("threat_score", 0) - previous.get("threat_score", 0),
                "risk_level_changed": current.get("risk_level") != previous.get("risk_level"),
                "category_changed": current.get("category") != previous.get("category"),
                "status_changed": current.get("url_status") != previous.get("url_status"),
                "new_emails": len(current.get("emails_found", [])) - len(previous.get("emails_found", [])),
                "new_crypto": len(current.get("crypto_addresses", [])) - len(previous.get("crypto_addresses", []))
            }
        }
        
        return jsonify(comparison)
    finally:
        db_manager.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
