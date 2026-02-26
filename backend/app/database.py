"""
MongoDB Atlas Database Connection
Handles storing and retrieving scraped data
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from app.core.config import settings
from app.utils import logger, get_timestamp


class DatabaseManager:
    """Manages MongoDB Atlas connection and operations"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.alerts = None
        self.iocs = None
        self.monitors = None

        if not settings.mongodb_uri:
            raise ValueError("❌ MONGODB_URI not found in environment variables (.env file)")

        self.connect()

    def connect(self):
        """Establish connection to MongoDB Atlas"""
        try:
            self.client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=15000,  # Increased to 15 seconds
                connectTimeoutMS=15000,
                socketTimeoutMS=15000,
                retryWrites=True
            )

            # Test connection
            self.client.admin.command("ping")

            self.db = self.client[settings.database_name]
            self.collection = self.db[settings.collection_name]
            self.alerts = self.db["alerts"]  # Alert collection for threat notifications
            self.iocs = self.db["iocs"]      # IOC collection for indicators tracking
            self.monitors = self.db["monitors"]  # Monitors collection for active monitoring jobs

            logger.info("Successfully connected to MongoDB Atlas")
            return True

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {e}")
            return False

    def insert_scraped_data(self, url, parsed_data, url_status=None, response_time=None, status_code=None):
        """Insert scraped and parsed data into database with content change detection and URL status tracking"""

        if self.collection is None:
            logger.error("Database not connected")
            return False

        try:
            # Step 1: Fetch latest document for the same URL
            previous_entry = self.collection.find_one(
                {"url": url},
                sort=[("timestamp", -1)]
            )

            # Step 2 & 3: Compare hashes and mark content change
            content_changed = False
            current_hash = parsed_data.get("content_hash")
            
            if previous_entry and current_hash:
                previous_hash = previous_entry.get("content_hash")
                if previous_hash and previous_hash != current_hash:
                    content_changed = True
                    logger.warning(f"⚠️ Content changed detected for {url}")
                    logger.info(f"Previous hash: {previous_hash[:16]}...")
                    logger.info(f"Current hash: {current_hash[:16]}...")
            
            # Step 4: Increment threat score if content changed
            threat_score = parsed_data.get("threat_score", 0)
            if content_changed:
                threat_score = min(threat_score + 15, 100)  # Add 15 points, cap at 100
                logger.warning(f"🚨 Threat score increased to {threat_score} due to content change")

            # Extract ClamAV results from file_analysis
            # Aggregate malware detection status from all analyzed files
            file_analysis = parsed_data.get("file_analysis")
            clamav_status = None
            clamav_detected = False
            clamav_details = []
            
            if file_analysis:
                for file_result in file_analysis:
                    analysis = file_result.get("analysis", {})
                    status = analysis.get("clamav_status")
                    detected = analysis.get("clamav_detected", False)
                    
                    if status:
                        clamav_status = status
                    
                    # If any file shows malware detection, mark as detected
                    if detected:
                        clamav_detected = True
                        if analysis.get("clamav"):
                            clamav_details.append({
                                "file": file_result.get("file_name"),
                                "threats": analysis.get("clamav", {}).get("threats", [])
                            })

            # Build status history entry
            status_history_entry = {
                "timestamp": get_timestamp(),
                "url_status": url_status or "UNKNOWN",
                "response_time": response_time,
                "status_code": status_code
            }
            
            # Initialize or extend status history
            previous_status_history = []
            if previous_entry and "status_history" in previous_entry:
                previous_status_history = previous_entry.get("status_history", [])

            # Create document with ALL fields from parsed_data
            document = {
                "url": url,
                "timestamp": get_timestamp(),
                "title": parsed_data.get("title"),
                "links": parsed_data.get("links"),
                "keywords": parsed_data.get("keywords"),
                "text_preview": parsed_data.get("text_preview"),
                # Analyzer fields
                "content_hash": current_hash,
                "emails_found": parsed_data.get("emails_found"),
                "crypto_addresses": parsed_data.get("crypto_addresses"),
                "threat_score": threat_score,
                "category": parsed_data.get("category"),
                "risk_level": parsed_data.get("risk_level"),
                # Change detection field
                "content_changed": content_changed,
                # File analysis fields
                "file_analysis": file_analysis,
                "file_links": parsed_data.get("file_links"),
                # ClamAV malware detection fields
                "clamav_status": clamav_status,
                "clamav_detected": clamav_detected,
                "clamav_details": clamav_details if clamav_details else None,
                # URL Status fields
                "url_status": url_status or "UNKNOWN",
                "response_time": response_time,
                "status_code": status_code,
                "status_history": previous_status_history + [status_history_entry],
            }

            # Step 5: Insert updated document
            result = self.collection.insert_one(document)

            logger.info(f"Inserted document with ID: {result.inserted_id}")
            return True

        except OperationFailure as e:
            logger.error(f"Database operation failed: {e}")
            return False

        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            return False

    def get_recent_entries(self, limit=10):
        """Retrieve recent entries from database sorted by newest first"""

        if self.collection is None:
            logger.error("Database not connected")
            return []

        try:
            # Use -1 for descending order (newest first)
            entries = (
                list(
                    self.collection
                    .find()
                    .sort("timestamp", -1)
                    .limit(limit)
                )
            )

            logger.info(f"Retrieved {len(entries)} entries from database (newest first)")
            return entries

        except Exception as e:
            logger.error(f"Error retrieving entries: {e}")
            return []

    def insert_alert(self, alert_data):
        """
        Insert alert into alerts collection
        
        Args:
            alert_data: dict with alert information
                {
                    "url": str,
                    "reason": str,
                    "threat_score": int,
                    "category": str,
                    "severity": "LOW" | "MEDIUM" | "HIGH",
                    "details": dict
                }
        
        Returns:
            bool: True if successful
        """
        if self.alerts is None:
            logger.error("Alerts collection not connected")
            return False
        
        try:
            alert_data["timestamp"] = get_timestamp()
            alert_data["status"] = "new"  # Track alert status
            
            result = self.alerts.insert_one(alert_data)
            logger.warning(f"🚨 ALERT TRIGGERED: {alert_data.get('reason')} - {alert_data.get('url')}")
            logger.info(f"Alert stored with ID: {result.inserted_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error inserting alert: {e}")
            return False

    def check_ioc_reuse(self, ioc_value, ioc_type):
        """
        Check if IOC (Indicator of Compromise) has been seen before
        
        Args:
            ioc_value: str - The indicator value (email, crypto address, hash, etc.)
            ioc_type: str - Type of indicator ("email", "crypto", "file_hash")
        
        Returns:
            dict: {
                "exists": bool,
                "first_seen": str or None,
                "urls": list,
                "reuse_count": int
            }
        """
        if self.iocs is None:
            logger.error("IOCs collection not connected")
            return {"exists": False, "urls": []}
        
        try:
            existing = self.iocs.find_one({"ioc_value": ioc_value, "ioc_type": ioc_type})
            
            if existing:
                # Get all URLs this IOC has been seen on
                all_occurrences = list(
                    self.iocs.find({"ioc_value": ioc_value, "ioc_type": ioc_type})
                )
                urls = [occ.get("url") for occ in all_occurrences if "url" in occ]
                
                logger.info(f"🔄 IOC REUSE DETECTED: {ioc_type} reused across {len(urls)} URLs")
                
                return {
                    "exists": True,
                    "first_seen": existing.get("timestamp"),
                    "urls": urls,
                    "reuse_count": len(urls)
                }
            
            return {"exists": False, "urls": []}
        
        except Exception as e:
            logger.error(f"Error checking IOC reuse: {e}")
            return {"exists": False, "urls": []}

    def insert_ioc(self, ioc_value, ioc_type, url):
        """
        Insert or update IOC in tracking collection
        
        Args:
            ioc_value: str - The indicator value
            ioc_type: str - Type ("email", "crypto", "file_hash")
            url: str - URL where this IOC was found
        
        Returns:
            dict: Reuse information if it exists
        """
        if self.iocs is None:
            logger.error("IOCs collection not connected")
            return None
        
        try:
            # Check if IOC already exists
            reuse_info = self.check_ioc_reuse(ioc_value, ioc_type)
            
            # Insert new occurrence
            self.iocs.insert_one({
                "ioc_value": ioc_value,
                "ioc_type": ioc_type,
                "url": url,
                "timestamp": get_timestamp()
            })
            
            return reuse_info if reuse_info["exists"] else None
        
        except Exception as e:
            logger.error(f"Error inserting IOC: {e}")
            return None

    def save_monitor(self, monitor_id: str, url: str, interval: int, status: str = "active"):
        """
        Save or update a monitor in the database
        
        Args:
            monitor_id: Unique identifier for the monitor
            url: URL being monitored
            interval: Scan interval in minutes
            status: Monitor status ("active", "paused", "inactive")
        
        Returns:
            bool: Success status
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return False
        
        try:
            self.monitors.update_one(
                {"monitor_id": monitor_id},
                {
                    "$set": {
                        "monitor_id": monitor_id,
                        "url": url,
                        "interval": interval,
                        "status": status,
                        "updated_at": get_timestamp()
                    },
                    "$setOnInsert": {
                        "created_at": get_timestamp(),
                        "scan_count": 0,
                        "last_scan": None
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving monitor: {e}")
            return False

    def get_active_monitors(self):
        """
        Get all active monitors from the database
        
        Returns:
            list: List of active monitor documents
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return []
        
        try:
            monitors = list(self.monitors.find({"status": "active"}))
            return monitors
        except Exception as e:
            logger.error(f"Error fetching active monitors: {e}")
            return []

    def update_monitor_status(self, monitor_id: str, status: str):
        """
        Update monitor status
        
        Args:
            monitor_id: Monitor identifier
            status: New status ("active", "paused", "inactive")
        
        Returns:
            bool: Success status
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return False
        
        try:
            result = self.monitors.update_one(
                {"monitor_id": monitor_id},
                {"$set": {"status": status, "updated_at": get_timestamp()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating monitor status: {e}")
            return False

    def update_monitor_scan_info(self, monitor_id: str, last_scan: str, scan_count: int):
        """
        Update monitor scan information
        
        Args:
            monitor_id: Monitor identifier
            last_scan: Timestamp of last scan
            scan_count: Total number of scans
        
        Returns:
            bool: Success status
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return False
        
        try:
            self.monitors.update_one(
                {"monitor_id": monitor_id},
                {
                    "$set": {
                        "last_scan": last_scan,
                        "scan_count": scan_count,
                        "updated_at": get_timestamp()
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating monitor scan info: {e}")
            return False

    def delete_monitor(self, monitor_id: str):
        """
        Delete a monitor from the database (set status to inactive)
        
        Args:
            monitor_id: Monitor identifier
        
        Returns:
            bool: Success status
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return False
        
        try:
            result = self.monitors.update_one(
                {"monitor_id": monitor_id},
                {"$set": {"status": "inactive", "updated_at": get_timestamp()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting monitor: {e}")
            return False

    def delete_all_monitors(self):
        """
        Delete all monitors (set all to inactive)
        
        Returns:
            bool: Success status
        """
        if self.monitors is None:
            logger.error("Monitors collection not connected")
            return False
        
        try:
            self.monitors.update_many(
                {},
                {"$set": {"status": "inactive", "updated_at": get_timestamp()}}
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting all monitors: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")