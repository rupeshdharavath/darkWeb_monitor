"""
Monitor service - handles monitoring job operations
"""

import hashlib
from typing import Any, Dict, List

from app.database import DatabaseManager
from app.monitor import monitor_manager
from app.utils import sanitize_url, logger


class MonitorService:
    """Service for handling monitor operations"""

    @staticmethod
    async def list_monitors() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all active monitors with last scan details
        
        Returns:
            Dictionary containing list of monitors
        """
        monitors = monitor_manager.list_monitors()
        db_manager = DatabaseManager()

        try:
            # Enrich each monitor with last scan data
            enriched_monitors = []
            for monitor_id, monitor_data in monitors.items():
                # Get last scan for this URL
                last_scan = db_manager.collection.find_one(
                    {"url": monitor_data["url"]}, sort=[("timestamp", -1)]
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
                    "last_scan_data": None,
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
                        "clamav_detected": last_scan.get("clamav_detected", False),
                    }

                enriched_monitors.append(monitor_info)

            return {"monitors": enriched_monitors}
        finally:
            db_manager.close()

    @staticmethod
    async def create_monitor(url: str, interval: int = 5) -> Dict[str, Any]:
        """
        Create a new monitoring job
        
        Args:
            url: URL to monitor
            interval: Monitoring interval in minutes
            
        Returns:
            Dictionary containing monitor details
            
        Raises:
            ValueError: If URL is invalid or monitor limit reached
            Exception: If monitor creation fails
        """
        logger.info(f"Received monitor creation request for URL: {url}")

        sanitized_url = sanitize_url(url)

        if not sanitized_url:
            error_msg = f"Invalid URL: '{url}'. URL must start with http:// or https://"
            logger.warning(error_msg)
            raise ValueError(error_msg)

        # Check monitor limit (max 5)
        current_monitors = monitor_manager.list_monitors()
        if len(current_monitors) >= 5:
            raise ValueError(
                "Maximum 5 monitors allowed. Please delete an existing monitor to add a new one."
            )

        # Generate monitor ID
        monitor_id = hashlib.md5(sanitized_url.encode()).hexdigest()[:12]

        logger.info(f"Creating monitor for URL: {sanitized_url} with ID: {monitor_id}")

        success, error_msg = monitor_manager.add_monitor(monitor_id, sanitized_url, interval)

        if success:
            logger.info(f"Monitor created successfully: {monitor_id}")
            return {
                "monitor_id": monitor_id,
                "url": sanitized_url,
                "interval": interval,
                "message": "Monitor created successfully",
            }
        else:
            logger.error(f"Failed to create monitor {monitor_id}: {error_msg}")
            raise ValueError(error_msg or "Failed to create monitor")

    @staticmethod
    async def get_monitor(monitor_id: str) -> Dict[str, Any]:
        """
        Get specific monitor details
        
        Args:
            monitor_id: Unique monitor identifier
            
        Returns:
            Dictionary containing monitor details
            
        Raises:
            FileNotFoundError: If monitor not found
        """
        monitor = monitor_manager.get_monitor(monitor_id)
        if not monitor:
            raise FileNotFoundError("Monitor not found")
        return monitor

    @staticmethod
    async def delete_monitor(monitor_id: str) -> Dict[str, str]:
        """
        Delete a monitor
        
        Args:
            monitor_id: Unique monitor identifier
            
        Returns:
            Dictionary with success message
            
        Raises:
            FileNotFoundError: If monitor not found
        """
        success = monitor_manager.remove_monitor(monitor_id)
        if success:
            return {"message": "Monitor deleted successfully"}
        else:
            raise FileNotFoundError("Monitor not found")

    @staticmethod
    async def delete_all_monitors() -> Dict[str, Any]:
        """
        Delete all monitors (utility endpoint)
        
        Returns:
            Dictionary with count of deleted monitors
        """
        monitors = monitor_manager.list_monitors()
        deleted_count = 0
        for monitor_id in list(monitors.keys()):
            if monitor_manager.remove_monitor(monitor_id):
                deleted_count += 1
        logger.info(f"Deleted {deleted_count} monitors")
        return {"message": f"Deleted {deleted_count} monitors", "count": deleted_count}

    @staticmethod
    async def pause_monitor(monitor_id: str) -> Dict[str, str]:
        """
        Pause a monitor
        
        Args:
            monitor_id: Unique monitor identifier
            
        Returns:
            Dictionary with success message
            
        Raises:
            Exception: If pause operation fails
        """
        success = monitor_manager.pause_monitor(monitor_id)
        if success:
            return {"message": "Monitor paused"}
        else:
            raise Exception("Failed to pause monitor")

    @staticmethod
    async def resume_monitor(monitor_id: str) -> Dict[str, str]:
        """
        Resume a paused monitor
        
        Args:
            monitor_id: Unique monitor identifier
            
        Returns:
            Dictionary with success message
            
        Raises:
            Exception: If resume operation fails
        """
        success = monitor_manager.resume_monitor(monitor_id)
        if success:
            return {"message": "Monitor resumed"}
        else:
            raise Exception("Failed to resume monitor")
