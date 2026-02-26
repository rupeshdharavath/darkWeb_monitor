"""
History service - handles scan history operations
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.errors import InvalidId

from app.database import DatabaseManager


class HistoryService:
    """Service for handling scan history operations"""

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
    async def get_history() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all scan history sorted by newest first
        
        Returns:
            Dictionary containing list of history items
            
        Raises:
            Exception: If database connection fails
        """
        db_manager = DatabaseManager()
        if db_manager.collection is None:
            raise Exception("Database connection failed")

        try:
            # Get all unique URLs with their latest scan
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$group": {"_id": "$url", "latest_scan": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$latest_scan"}},
                {"$sort": {"timestamp": -1}},
                {"$limit": 100},
            ]

            entries = list(db_manager.collection.aggregate(pipeline))

            history = []
            for entry in entries:
                history.append(
                    {
                        "id": str(entry.get("_id")),
                        "url": entry.get("url"),
                        "title": entry.get("title") or "Unknown",
                        "threat_score": entry.get("threat_score") or 0,
                        "risk_level": entry.get("risk_level") or "LOW",
                        "category": entry.get("category") or "Unknown",
                        "timestamp": entry.get("timestamp"),
                        "url_status": entry.get("url_status") or "UNKNOWN",
                    }
                )

            return {"history": history}

        finally:
            db_manager.close()

    @staticmethod
    async def get_history_entry(entry_id: str) -> Dict[str, Any]:
        """
        Get specific scan entry by ID
        
        Args:
            entry_id: MongoDB ObjectId of the scan entry
            
        Returns:
            Dictionary containing detailed scan entry
            
        Raises:
            ValueError: If entry ID is invalid
            FileNotFoundError: If entry not found
            Exception: If database connection fails
        """
        db_manager = DatabaseManager()
        if db_manager.collection is None:
            raise Exception("Database connection failed")

        try:
            try:
                obj_id = ObjectId(entry_id)
            except InvalidId:
                raise ValueError("Invalid entry ID")

            entry = db_manager.collection.find_one({"_id": obj_id})
            if not entry:
                raise FileNotFoundError("Entry not found")

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
                "pgpDetected": HistoryService._detect_pgp(text_content),
                "emails": emails,
                "cryptoAddresses": crypto_addresses,
                "contentChanged": entry.get("content_changed", False),
                "contentHash": content_hash,
                "title": title,
                "textPreview": text_content,
                "keywords": HistoryService._trim_list(keywords, 12),
                "links": HistoryService._trim_links(links, 8),
                "fileLinks": HistoryService._trim_list(file_links, 8),
                "fileAnalysis": HistoryService._trim_list(file_analysis, 8),
                "clamav": {
                    "status": clamav_status,
                    "detected": clamav_detected,
                    "details": HistoryService._trim_list(clamav_details, 5),
                },
                "responseTime": response_time,
                "statusCode": status_code,
                "timestamp": timestamp,
                "categoryDistribution": HistoryService._build_category_distribution(category),
                "threatBreakdown": HistoryService._build_threat_breakdown(
                    emails, crypto_addresses, threat_score
                ),
                "timeline": HistoryService._build_timeline(entry.get("status_history", [])),
            }
            return response

        finally:
            db_manager.close()
