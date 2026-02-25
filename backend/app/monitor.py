"""
Automated Monitoring System
Manages scheduled scans and threat alerts for onion URLs
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import threading
from app.database import DatabaseManager
from app.tor_proxy import create_tor_session, test_tor_connection
from app.scraper import scrape_url
from app.parser import parse_html
from app.analyzer import analyze_content
from app.utils import logger, get_timestamp
from app.downloader import download_file
from app.file_analyzer import analyze_file


class MonitorManager:
    """Manages automated monitoring jobs for onion URLs"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one scheduler instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the monitoring manager"""
        if self._initialized:
            return
            
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._initialized = True
        self.active_monitors = {}
        logger.info("✅ Monitor Manager initialized")
    
    def add_monitor(self, monitor_id: str, url: str, interval_minutes: int = 5):
        """
        Add a new monitoring job
        
        Args:
            monitor_id: Unique identifier for the monitor
            url: Onion URL to monitor
            interval_minutes: Scan interval in minutes (default: 5)
        """
        if monitor_id in self.active_monitors:
            logger.warning(f"Monitor {monitor_id} already exists")
            return False
        
        try:
            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._scan_and_compare,
                trigger=IntervalTrigger(minutes=interval_minutes),
                args=[monitor_id, url],
                id=monitor_id,
                name=f"Monitor: {url}",
                replace_existing=True
            )
            
            self.active_monitors[monitor_id] = {
                "url": url,
                "interval": interval_minutes,
                "created_at": get_timestamp(),
                "last_scan": None,
                "scan_count": 0,
                "job_id": job.id
            }
            
            # Perform initial scan immediately
            self._scan_and_compare(monitor_id, url)
            
            logger.info(f"🔍 Monitor added: {url} (every {interval_minutes} min)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add monitor: {e}")
            return False
    
    def _scan_and_compare(self, monitor_id: str, url: str):
        """
        Perform scan and compare with previous results
        
        Args:
            monitor_id: Monitor identifier
            url: URL to scan
        """
        logger.info(f"🔄 Scanning monitored URL: {url}")
        
        db_manager = DatabaseManager()
        session = None
        
        try:
            # Get previous scan data
            previous_scan = db_manager.collection.find_one(
                {"url": url},
                sort=[("timestamp", -1)]
            )
            
            previous_threat_score = previous_scan.get("threat_score", 0) if previous_scan else 0
            
            # Create Tor session
            session = create_tor_session()
            if not test_tor_connection(session):
                logger.error(f"Tor connection failed for {url}")
                return
            
            # Perform scan
            html_content, status_info = scrape_url(session, url)
            url_status = status_info.get("status", "UNKNOWN")
            response_time = status_info.get("response_time")
            status_code = status_info.get("status_code")
            
            if not html_content:
                logger.warning(f"No content retrieved from {url}")
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
                return
            
            # Parse content
            parsed_data = parse_html(html_content, base_url=url)
            if not parsed_data:
                logger.warning(f"Failed to parse content from {url}")
                return
            
            # Analyze files
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
            
            # Analyze content
            analysis_result = analyze_content(
                parsed_data.get("text_content", ""),
                parsed_data.get("keywords", []),
                clamav_detected
            )
            parsed_data.update(analysis_result)
            
            if file_analysis_results:
                parsed_data["file_analysis"] = file_analysis_results
            
            # Insert new scan
            db_manager.insert_scraped_data(
                url,
                parsed_data,
                url_status=url_status,
                response_time=response_time,
                status_code=status_code
            )
            
            # Get current threat score
            current_threat_score = parsed_data.get("threat_score", 0)
            
            # Check for threat score increase
            if current_threat_score > previous_threat_score:
                score_increase = current_threat_score - previous_threat_score
                logger.warning(f"🚨 THREAT INCREASE DETECTED: {url}")
                logger.warning(f"   Previous: {previous_threat_score} → Current: {current_threat_score} (+{score_increase})")
                
                # Create alert
                db_manager.insert_alert({
                    "url": url,
                    "monitor_id": monitor_id,
                    "reason": "Threat Score Increase",
                    "threat_score": current_threat_score,
                    "previous_score": previous_threat_score,
                    "score_increase": score_increase,
                    "category": parsed_data.get("category", "Unknown"),
                    "severity": parsed_data.get("risk_level", "LOW"),
                    "details": {
                        "content_changed": parsed_data.get("content_changed", False),
                        "malware_detected": clamav_detected,
                        "new_emails": len(parsed_data.get("emails_found", [])),
                        "new_crypto": len(parsed_data.get("crypto_addresses", []))
                    }
                })
            
            # Update monitor stats
            if monitor_id in self.active_monitors:
                self.active_monitors[monitor_id]["last_scan"] = get_timestamp()
                self.active_monitors[monitor_id]["scan_count"] += 1
            
            logger.info(f"✅ Scan completed for {url} (Score: {current_threat_score})")
            
        except Exception as e:
            logger.error(f"Error scanning {url}: {e}")
        finally:
            if session:
                session.close()
            db_manager.close()
    
    def remove_monitor(self, monitor_id: str):
        """
        Remove a monitoring job
        
        Args:
            monitor_id: Monitor identifier to remove
        """
        if monitor_id not in self.active_monitors:
            logger.warning(f"Monitor {monitor_id} not found")
            return False
        
        try:
            self.scheduler.remove_job(monitor_id)
            del self.active_monitors[monitor_id]
            logger.info(f"🗑️ Monitor removed: {monitor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove monitor: {e}")
            return False
    
    def get_monitor(self, monitor_id: str):
        """Get monitor details"""
        return self.active_monitors.get(monitor_id)
    
    def list_monitors(self):
        """List all active monitors"""
        return self.active_monitors
    
    def pause_monitor(self, monitor_id: str):
        """Pause a monitoring job"""
        try:
            self.scheduler.pause_job(monitor_id)
            logger.info(f"⏸️ Monitor paused: {monitor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause monitor: {e}")
            return False
    
    def resume_monitor(self, monitor_id: str):
        """Resume a paused monitoring job"""
        try:
            self.scheduler.resume_job(monitor_id)
            logger.info(f"▶️ Monitor resumed: {monitor_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume monitor: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("🛑 Monitor Manager shut down")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")


# Global monitor manager instance
monitor_manager = MonitorManager()
