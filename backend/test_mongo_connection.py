"""
Quick test to diagnose MongoDB connectivity issues
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    print("❌ MONGODB_URI not found in .env file")
    exit(1)

print(f"Testing connection to MongoDB...")
print(f"URI (redacted): mongodb+srv://***:***@{MONGODB_URI.split('@')[1]}")

try:
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
    )
    
    # Try to ping
    client.admin.command("ping")
    print("✅ MongoDB connection successful!")
    
    # Show databases
    dbs = client.list_database_names()
    print(f"Available databases: {dbs}")
    
    client.close()
    
except ConnectionFailure as e:
    print(f"❌ Connection failed: {e}")
    print("\nPossible causes:")
    print("1. MongoDB Atlas cluster is paused")
    print("2. Network/firewall blocking the connection")
    print("3. IP whitelist not set to 0.0.0.0/0 in MongoDB Atlas")
    print("4. DNS resolution failing")
    exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
