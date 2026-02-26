"""
Scan service - handles URL scanning and comparison logic
"""

import urllib.parse
from typing import Any, Dict, List, Optional

from app.tor_proxy import create_tor_session, test_tor_connection
from app.scraper import scrape_url
from app.parser import parse_html
from app.analyzer import analyze_content
from app.database import DatabaseManager
from app.utils import sanitize_url, logger
from app.downloader import download_file
from app.file_analyzer import analyze_file


class ScanService:
    """Service for handling URL scanning operations"""

    @staticmethod
    def _build_category_distribution(category: str) -> List[Dict[str, Any]]:
        """Build category distribution for response"""
        if not category:
            return []
        return [{"name": category, "value": 1}]

    @staticmethod
    def _build_threat_breakdown(
        emails: List[str], crypto_addresses: List[str], threat_score: int
    ) -> List[Dict[str, Any]]:
        """Build threat breakdown metrics"""
        return [
            {"label": "Emails", "value": len(emails)},
            {"label": "Crypto", "value": len(crypto_addresses)},
            {"label": "Threat", "value": threat_score},
        ]

    @staticmethod
    def _build_timeline(status_history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Build timeline from status history"""
        if not status_history:
            return []
        timeline = []
        for entry in status_history[-12:]:
            timeline.append(
                {"time": entry.get("timestamp", ""), "value": entry.get("response_time") or 0}
            )
        return timeline

    @staticmethod
    def _trim_list(items: Optional[List[Any]], limit: int = 8) -> List[Any]:
        """Trim list to specified limit"""
        if not items:
            return []
        return items[:limit]

    @staticmethod
    def _trim_links(
        links: Optional[List[Dict[str, Any]]], limit: int = 8
    ) -> List[Dict[str, Any]]:
        """Trim and format links"""
        if not links:
            return []
        return [{"url": link.get("url", ""), "text": link.get("text")} for link in links[:limit]]

    @staticmethod
    def _detect_pgp(text: str) -> bool:
        """Detect PGP content in text"""
        lowered = (text or "").lower()
        return "pgp" in lowered or "-----begin pgp" in lowered

    @staticmethod
    def _create_session_for_url(url: str):
        """Create appropriate session for URL"""
        if ".onion" in url.lower():
            session = create_tor_session()
            if not test_tor_connection(session):
                session.close()
                return None, "Tor connection failed"
            return session, None
        return create_tor_session(), None

    @staticmethod
    def _store_minimal_entry(
        db_manager: DatabaseManager,
        url: str,
        url_status: str,
        response_time: Optional[float],
        status_code: Optional[int],
    ):
        """Store minimal entry when full scraping fails"""
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
                "file_links": [],
            },
            url_status=url_status,
            response_time=response_time,
            status_code=status_code,
        )

    @staticmethod
    def _format_scan_response(latest: Dict[str, Any]) -> Dict[str, Any]:
        """Format scan data into response structure"""
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
            "url": latest.get("url", ""),
            "threatScore": threat_score,
            "category": category,
            "riskLevel": risk_level,
            "confidence": confidence,
            "threatIndicators": threat_indicators,
            "pgpDetected": ScanService._detect_pgp(text_content),
            "emails": emails,
            "cryptoAddresses": crypto_addresses,
            "contentChanged": latest.get("content_changed", False),
            "contentHash": content_hash,
            "title": title,
            "textPreview": text_content,
            "keywords": ScanService._trim_list(keywords, 12),
            "links": ScanService._trim_links(links, 8),
            "fileLinks": ScanService._trim_list(file_links, 8),
            "fileAnalysis": ScanService._trim_list(file_analysis, 8),
            "clamav": {
                "status": clamav_status,
                "detected": clamav_detected,
                "details": ScanService._trim_list(clamav_details, 5),
            },
            "responseTime": response_time,
            "statusCode": status_code,
            "timestamp": timestamp,
            "categoryDistribution": ScanService._build_category_distribution(category),
            "threatBreakdown": ScanService._build_threat_breakdown(
                emails, crypto_addresses, threat_score
            ),
            "timeline": ScanService._build_timeline(latest.get("status_history", [])),
        }
        return response

    @staticmethod
    async def scan_url(url: str) -> Dict[str, Any]:
        """
        Scan a URL and return threat analysis
        
        Args:
            url: URL to scan
            
        Returns:
            Dictionary containing scan results
            
        Raises:
            ValueError: If URL is invalid
            ConnectionError: If connection fails
        """
        url = sanitize_url(url)
        if not url:
            raise ValueError("Invalid URL. Include http:// or https://")

        db_manager = DatabaseManager()
        if db_manager.collection is None:
            raise ConnectionError("Database connection failed")

        session = None
        try:
            session, session_error = ScanService._create_session_for_url(url)
            if session_error:
                raise ConnectionError(session_error)

            html_content, status_info = scrape_url(session, url)
            url_status = status_info.get("status", "UNKNOWN")
            response_time = status_info.get("response_time")
            status_code = status_info.get("status_code")

            if not html_content:
                ScanService._store_minimal_entry(
                    db_manager, url, url_status, response_time, status_code
                )
            else:
                parsed_data = parse_html(html_content, base_url=url)
                if not parsed_data:
                    ScanService._store_minimal_entry(
                        db_manager, url, url_status, response_time, status_code
                    )
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
                                file_analysis_results.append(
                                    {
                                        "file_url": file_url,
                                        "file_name": download_result.get("filename"),
                                        "file_size": download_result.get("file_size"),
                                        "file_hash": download_result.get("file_hash"),
                                        "content_type": download_result.get("content_type"),
                                        "analysis": analysis_result,
                                    }
                                )
                        except Exception:
                            continue

                    analysis_result = analyze_content(
                        parsed_data.get("text_content", ""),
                        parsed_data.get("keywords", []),
                        clamav_detected,
                    )
                    parsed_data.update(analysis_result)

                    if file_analysis_results:
                        parsed_data["file_analysis"] = file_analysis_results

                    db_manager.insert_scraped_data(
                        url,
                        parsed_data,
                        url_status=url_status,
                        response_time=response_time,
                        status_code=status_code,
                    )

            latest = db_manager.collection.find_one({"url": url}, sort=[("timestamp", -1)])
            if not latest:
                raise Exception("Failed to store scan result")

            return ScanService._format_scan_response(latest)

        finally:
            if session:
                session.close()
            db_manager.close()

    @staticmethod
    async def compare_scans(url: str) -> Dict[str, Any]:
        """
        Compare current scan with baseline (first) scan for a URL
        
        Args:
            url: URL to compare scans for
            
        Returns:
            Dictionary containing comparison data
            
        Raises:
            ValueError: If URL parameter is missing
            FileNotFoundError: If not enough scans to compare
        """
        if not url:
            raise ValueError("URL parameter missing")

        db_manager = DatabaseManager()
        if db_manager.collection is None:
            raise ConnectionError("Database connection failed")

        try:
            decoded_url = urllib.parse.unquote(url)

            # Find all scans for this URL, sorted by timestamp ascending (oldest first)
            scans = list(
                db_manager.collection.find({"url": decoded_url}).sort("timestamp", 1)
            )

            if len(scans) < 2:
                raise FileNotFoundError(
                    f"Not enough scan data to compare. URL has been scanned {len(scans)} time(s). "
                    "At least 2 scans are required for comparison. "
                    "Rescan the URL to generate a second baseline for comparison."
                )

            # Baseline is the FIRST/OLDEST scan, current is the LATEST scan
            baseline = scans[0]
            current = scans[-1]

            # Calculate differences
            current_emails = len(current.get("emails_found", []))
            baseline_emails = len(baseline.get("emails_found", []))
            new_emails = current_emails - baseline_emails

            current_crypto = len(current.get("crypto_addresses", []))
            baseline_crypto = len(baseline.get("crypto_addresses", []))
            new_crypto = current_crypto - baseline_crypto

            current_threat = current.get("threat_score", 0)
            baseline_threat = baseline.get("threat_score", 0)
            threat_delta = current_threat - baseline_threat

            current_risk = current.get("risk_level", "LOW")
            baseline_risk = baseline.get("risk_level", "LOW")

            current_status = current.get("url_status", "UNKNOWN")
            baseline_status = baseline.get("url_status", "UNKNOWN")

            current_category = current.get("category", "Unknown")
            baseline_category = baseline.get("category", "Unknown")

            # Check for file analysis threats
            baseline_files = baseline.get("file_analysis", []) or []
            current_files = current.get("file_analysis", []) or []
            baseline_malicious = sum(
                1 for f in baseline_files if f.get("analysis", {}).get("clamav_detected")
            )
            current_malicious = sum(
                1 for f in current_files if f.get("analysis", {}).get("clamav_detected")
            )
            new_malicious = current_malicious - baseline_malicious

            # Build detailed reasons for changes
            reasons = []

            if new_emails > 0:
                reasons.append(f"🚨 {new_emails} new email(s) discovered")

            if new_crypto > 0:
                reasons.append(f"💰 {new_crypto} new crypto address(es) found")

            if current.get("content_changed") and not baseline.get("content_changed"):
                reasons.append("📝 Content has changed since baseline")

            if current_risk != baseline_risk:
                reasons.append(f"⚠️ Risk level changed from {baseline_risk} to {current_risk}")

            if current_status != baseline_status:
                reasons.append(
                    f"🌐 URL status changed from {baseline_status} to {current_status}"
                )

            if current_category != baseline_category:
                reasons.append(
                    f"📂 Category changed from {baseline_category} to {current_category}"
                )

            if new_malicious > 0:
                reasons.append(f"🦠 {new_malicious} malicious file(s) detected")

            if threat_delta > 0 and not reasons:
                reasons.append(f"📊 Threat increased by {threat_delta} points")

            comparison = {
                "scan_count": len(scans),
                "current": {
                    "timestamp": current.get("timestamp"),
                    "threat_score": current_threat,
                    "risk_level": current_risk,
                    "category": current_category,
                    "url_status": current_status,
                    "content_changed": current.get("content_changed", False),
                    "emails": current_emails,
                    "crypto": current_crypto,
                },
                "previous": {
                    "timestamp": baseline.get("timestamp"),
                    "threat_score": baseline_threat,
                    "risk_level": baseline_risk,
                    "category": baseline_category,
                    "url_status": baseline_status,
                    "content_changed": baseline.get("content_changed", False),
                    "emails": baseline_emails,
                    "crypto": baseline_crypto,
                },
                "changes": {
                    "threat_score_delta": threat_delta,
                    "risk_level_changed": current_risk != baseline_risk,
                    "category_changed": current_category != baseline_category,
                    "status_changed": current_status != baseline_status,
                    "new_emails": new_emails,
                    "new_crypto": new_crypto,
                    "new_malicious_files": new_malicious,
                },
                "reasons": reasons,
            }

            return comparison

        finally:
            db_manager.close()
