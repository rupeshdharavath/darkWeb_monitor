"""
Alert service - handles alert operations
"""

from typing import Any, Dict, List
from bson import ObjectId
from bson.errors import InvalidId

from app.database import DatabaseManager


class AlertService:
    """Service for handling alert operations"""

    @staticmethod
    async def get_alerts() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get recent alerts (last 100)
        
        Returns:
            Dictionary containing list of alerts
            
        Raises:
            Exception: If database connection fails
        """
        db_manager = DatabaseManager()
        if db_manager.alerts is None:
            raise Exception("Database connection failed")

        try:
            # Get recent alerts (last 100)
            alerts = list(db_manager.alerts.find().sort("timestamp", -1).limit(100))

            # Convert ObjectId to string
            for alert in alerts:
                alert["_id"] = str(alert["_id"])

            return {"alerts": alerts}

        finally:
            db_manager.close()

    @staticmethod
    async def acknowledge_alert(alert_id: str) -> Dict[str, str]:
        """
        Mark an alert as acknowledged
        
        Args:
            alert_id: MongoDB ObjectId of the alert
            
        Returns:
            Dictionary with success message
            
        Raises:
            ValueError: If alert ID is invalid
            FileNotFoundError: If alert not found
            Exception: If database connection fails
        """
        db_manager = DatabaseManager()
        if db_manager.alerts is None:
            raise Exception("Database connection failed")

        try:
            try:
                obj_id = ObjectId(alert_id)
            except InvalidId:
                raise ValueError("Invalid alert ID")

            result = db_manager.alerts.update_one(
                {"_id": obj_id}, {"$set": {"status": "acknowledged"}}
            )

            if result.modified_count > 0:
                return {"message": "Alert acknowledged"}
            else:
                raise FileNotFoundError("Alert not found")

        finally:
            db_manager.close()
