"""
MongoDB Atlas Database Connection
Handles storing and retrieving scraped data
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from app.config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME
from app.utils import logger, get_timestamp


class DatabaseManager:
    """Manages MongoDB Atlas connection and operations"""

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB Atlas"""
        try:
            self.client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=15000,  # Increased to 15 seconds
                connectTimeoutMS=15000,
                socketTimeoutMS=15000,
                retryWrites=True
            )

            # Test connection
            self.client.admin.command("ping")

            self.db = self.client[DATABASE_NAME]
            self.collection = self.db[COLLECTION_NAME]

            logger.info("Successfully connected to MongoDB Atlas")
            return True

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {e}")
            return False

    def insert_scraped_data(self, url, parsed_data):
        """Insert scraped and parsed data into database"""

        if self.collection is None:
            logger.error("Database not connected")
            return False

        try:
            document = {
                "url": url,
                "timestamp": get_timestamp(),
                "title": parsed_data.get("title"),
                "links": parsed_data.get("links"),
                "keywords": parsed_data.get("keywords"),
                "text_preview": parsed_data.get("text_preview"),
            }

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
        """Retrieve recent entries from database"""

        if self.collection is None:
            logger.error("Database not connected")
            return []

        try:
            entries = (
                list(
                    self.collection
                    .find()
                    .sort("timestamp", -1)
                    .limit(limit)
                )
            )

            logger.info(f"Retrieved {len(entries)} entries from database")
            return entries

        except Exception as e:
            logger.error(f"Error retrieving entries: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")