"""MongoDB connection management."""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from utils.config import config
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    """Create database connection."""
    try:
        db.client = AsyncIOMotorClient(config.MONGODB_URI)
        db.database = db.client[config.MONGODB_DB_NAME]
        
        # Create indexes
        await create_indexes()
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection."""
    db.client.close()
    logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create necessary indexes."""
    # Transaction indexes
    await db.database[config.TRANSACTIONS_COLLECTION].create_index([("transaction_id", 1)], unique=True)
    await db.database[config.TRANSACTIONS_COLLECTION].create_index([("status", 1), ("created_at", -1)])
    await db.database[config.TRANSACTIONS_COLLECTION].create_index([("transaction_type", 1)])
    await db.database[config.TRANSACTIONS_COLLECTION].create_index([("amount", 1)])
    
    # Decision indexes
    await db.database[config.DECISIONS_COLLECTION].create_index([("transaction_id", 1)])
    await db.database[config.DECISIONS_COLLECTION].create_index([("decision", 1), ("created_at", -1)])
    await db.database[config.DECISIONS_COLLECTION].create_index([("confidence_score", 1)])
    
    # Audit indexes
    await db.database[config.AUDIT_EVENTS_COLLECTION].create_index([("timestamp", -1)])
    await db.database[config.AUDIT_EVENTS_COLLECTION].create_index([("transaction_id", 1)])
    await db.database[config.AUDIT_EVENTS_COLLECTION].create_index([("event_type", 1)])
    
    # Metrics indexes with TTL
    # await db.database[config.SYSTEM_METRICS_COLLECTION].create_index(
    #     [("timestamp", 1)], 
    #     expireAfterSeconds=15552000  # 180 days
    # )

# Global sync client for Temporal activities
_sync_client = None

def get_sync_db():
    """Get synchronous MongoDB client for Temporal activities."""
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(config.MONGODB_URI)
    return _sync_client[config.MONGODB_DB_NAME]
