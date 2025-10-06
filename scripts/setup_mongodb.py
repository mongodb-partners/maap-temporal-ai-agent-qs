"""Complete MongoDB setup script with comprehensive test data for all scenarios."""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import random
import uuid
import json
from typing import List, Dict, Any
from bson import Decimal128
from utils.config import config
from utils.decimal_utils import to_decimal128
from database.schemas import (
    Customer, Rule, RuleStatus, Transaction, TransactionDecision,
    HumanReview, Notification, AuditEvent, SystemMetric,
    TransactionType, TransactionStatus, DecisionType, RiskLevel
)
from services.rule_engine import RuleEngine
from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_collections():
    """Create MongoDB collections and indexes."""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        
        logger.info("Connected to MongoDB Atlas")
        
        # Create collections if they don't exist
        collections_to_create = [
            config.CUSTOMERS_COLLECTION,
            config.TRANSACTIONS_COLLECTION,
            config.DECISIONS_COLLECTION,
            config.HUMAN_REVIEWS_COLLECTION,
            config.AUDIT_EVENTS_COLLECTION,
            config.NOTIFICATIONS_COLLECTION,
            config.SYSTEM_METRICS_COLLECTION,
            config.RULES_COLLECTION,
            config.ACCOUNTS_COLLECTION,
            config.JOURNAL_COLLECTION,
            config.BALANCE_UPDATES_COLLECTION,
            config.HOLDS_COLLECTION
        ]
        
        existing_collections = await db.list_collection_names()
        
        for collection_name in collections_to_create:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
        
        # Create indexes
        await create_indexes(db)
        
        # Create vector search index
        await create_vector_search_index(db)
        
        # Insert sample data
        await insert_sample_data(db)
        
        logger.info("MongoDB setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error setting up MongoDB: {e}")
        raise
    finally:
        client.close()

async def create_indexes(db):
    """Create all necessary indexes."""
    logger.info("Creating indexes...")
    
    # Customer indexes
    await db[config.CUSTOMERS_COLLECTION].create_index([("customer_id", 1)], unique=True)
    await db[config.CUSTOMERS_COLLECTION].create_index([("legal_name", 1)])
    await db[config.CUSTOMERS_COLLECTION].create_index([("status", 1)])
    
    # Transaction indexes
    await db[config.TRANSACTIONS_COLLECTION].create_index([("transaction_id", 1)], unique=True)
    await db[config.TRANSACTIONS_COLLECTION].create_index([("status", 1), ("created_at", -1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([("transaction_type", 1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([("amount", 1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([("sender.customer_id", 1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([("created_at", -1)])

    # Additional indexes for hybrid search and graph traversal
    await db[config.TRANSACTIONS_COLLECTION].create_index([
        ("transaction_type", 1),
        ("amount", 1),
        ("sender.country", 1),
        ("recipient.country", 1)
    ], name="hybrid_search_index")

    # Indexes for graph traversal
    await db[config.TRANSACTIONS_COLLECTION].create_index([("sender.account_number", 1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([("recipient.account_number", 1)])
    await db[config.TRANSACTIONS_COLLECTION].create_index([
        ("sender.account_number", 1),
        ("timestamp", -1)
    ], name="graph_sender_time_index")
    await db[config.TRANSACTIONS_COLLECTION].create_index([
        ("recipient.account_number", 1),
        ("timestamp", -1)
    ], name="graph_recipient_time_index")
    
    # Decision indexes
    await db[config.DECISIONS_COLLECTION].create_index([("transaction_id", 1)])
    await db[config.DECISIONS_COLLECTION].create_index([("decision", 1), ("created_at", -1)])
    await db[config.DECISIONS_COLLECTION].create_index([("confidence_score", 1)])
    await db[config.DECISIONS_COLLECTION].create_index([("risk_score", 1)])
    
    # Rule indexes
    await db[config.RULES_COLLECTION].create_index([("rule_id", 1)], unique=True)
    await db[config.RULES_COLLECTION].create_index([("status", 1), ("priority", -1)])
    await db[config.RULES_COLLECTION].create_index([("category", 1)])
    
    # Human review indexes
    await db[config.HUMAN_REVIEWS_COLLECTION].create_index([("transaction_id", 1)])
    await db[config.HUMAN_REVIEWS_COLLECTION].create_index([("status", 1), ("priority", -1)])
    await db[config.HUMAN_REVIEWS_COLLECTION].create_index([("assigned_to", 1)])
    await db[config.HUMAN_REVIEWS_COLLECTION].create_index([("sla_deadline", 1)])
    
    # Notification indexes
    await db[config.NOTIFICATIONS_COLLECTION].create_index([("notification_id", 1)], unique=True)
    await db[config.NOTIFICATIONS_COLLECTION].create_index([("status", 1), ("created_at", 1)])
    await db[config.NOTIFICATIONS_COLLECTION].create_index([("transaction_id", 1)])
    
    # Audit indexes
    await db[config.AUDIT_EVENTS_COLLECTION].create_index([("timestamp", -1)])
    await db[config.AUDIT_EVENTS_COLLECTION].create_index([("transaction_id", 1)])
    await db[config.AUDIT_EVENTS_COLLECTION].create_index([("event_type", 1)])
    
    # Metrics indexes with TTL (30 days)
    await db[config.SYSTEM_METRICS_COLLECTION].create_index(
        [("timestamp", 1)],
        expireAfterSeconds=2592000
    )
    await db[config.SYSTEM_METRICS_COLLECTION].create_index([("metric_name", 1), ("timestamp", -1)])

    # Account indexes
    await db[config.ACCOUNTS_COLLECTION].create_index([("account_number", 1)], unique=True)
    await db[config.ACCOUNTS_COLLECTION].create_index([("customer_id", 1)])
    await db[config.ACCOUNTS_COLLECTION].create_index([("status", 1)])

    # Journal indexes for ACID transactions
    await db[config.JOURNAL_COLLECTION].create_index([("journal_id", 1)], unique=True)
    await db[config.JOURNAL_COLLECTION].create_index([("transaction_id", 1)])
    await db[config.JOURNAL_COLLECTION].create_index([("account_number", 1), ("timestamp", -1)])
    await db[config.JOURNAL_COLLECTION].create_index([("status", 1)])

    # Balance update indexes
    await db[config.BALANCE_UPDATES_COLLECTION].create_index([("update_id", 1)], unique=True)
    await db[config.BALANCE_UPDATES_COLLECTION].create_index([("account_number", 1), ("timestamp", -1)])
    await db[config.BALANCE_UPDATES_COLLECTION].create_index([("transaction_id", 1)])

    # Hold indexes
    await db[config.HOLDS_COLLECTION].create_index([("hold_id", 1)], unique=True)
    await db[config.HOLDS_COLLECTION].create_index([("account_number", 1), ("status", 1)])
    await db[config.HOLDS_COLLECTION].create_index([("transaction_id", 1)])
    await db[config.HOLDS_COLLECTION].create_index([("expires_at", 1)])

    logger.info("All indexes created successfully")

async def create_vector_search_index(db):
    """Create Atlas Vector Search index."""
    try:
        from pymongo.operations import SearchIndexModel
        import asyncio
        
        # Get the collection
        collection = db[config.TRANSACTIONS_COLLECTION]
        
        # Define the search index model
        index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": config.VECTOR_DIMENSION,
                        "similarity": "cosine"
                    },
                    {
                        "type": "filter",
                        "path": "transaction_type"
                    },
                    {
                        "type": "filter",
                        "path": "status"
                    }
                ]
            },
            name=config.VECTOR_SEARCH_INDEX,
            type="vectorSearch"
        )
        
        # Check if index already exists
        existing_indexes = await collection.list_search_indexes().to_list()
        index_exists = any(idx.get("name") == config.VECTOR_SEARCH_INDEX for idx in existing_indexes)
        
        if index_exists:
            logger.info(f"Vector search index '{config.VECTOR_SEARCH_INDEX}' already exists.")
            return
        
        # Create the search index
        result = await collection.create_search_index(model=index_model)
        logger.info(f"New search index '{result}' is building.")
        
        # Poll to check if the index is ready
        logger.info("Polling to check if the index is ready. This may take up to a minute.")
        poll_interval = 5  # seconds
        max_wait_time = 120  # 2 minutes max wait
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            indices = await collection.list_search_indexes(result).to_list()
            if indices and indices[0].get("queryable"):
                logger.info(f"Vector search index '{result}' is ready for querying.")
                return
            
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval
            
        logger.warning(f"Vector search index '{result}' is still building after {max_wait_time} seconds.")
        
    except Exception as e:
        logger.error(f"Error creating vector search index: {e}")
        logger.info("Note: You may need to create this index manually in MongoDB Atlas UI")
        
        # Log the index configuration for manual creation
        vector_index_config = {
            "name": config.VECTOR_SEARCH_INDEX,
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": config.VECTOR_DIMENSION,
                        "similarity": "cosine"
                    },
                    {
                        "type": "filter",
                        "path": "transaction_type"
                    },
                    {
                        "type": "filter",
                        "path": "status"
                    }
                ]
            }
        }
        logger.info(f"Manual index configuration: {vector_index_config}")

async def insert_sample_data(db):
    """Insert comprehensive sample data for all scenarios."""

    # Check if we already have sample data
    existing_customers = await db[config.CUSTOMERS_COLLECTION].count_documents({})
    if existing_customers > 0:
        logger.info("Sample data already exists, skipping...")
        return

    logger.info("Creating comprehensive test data for all scenarios...")
    
    # Comprehensive customer profiles for all test scenarios
    customers = await create_test_customers()

    # Insert customers
    customer_docs = [c.model_dump() for c in customers]
    await db[config.CUSTOMERS_COLLECTION].insert_many(customer_docs)
    logger.info(f"Inserted {len(customers)} customers")

    # Create accounts for customers
    accounts = await create_test_accounts(customers)
    await db[config.ACCOUNTS_COLLECTION].insert_many(accounts)
    logger.info(f"Inserted {len(accounts)} accounts")

    # Insert default rules
    default_rules = RuleEngine.get_default_rules()
    rule_docs = [r.model_dump() for r in default_rules]
    await db[config.RULES_COLLECTION].insert_many(rule_docs)
    logger.info(f"Inserted {len(default_rules)} default rules")

    # Create comprehensive test transactions for all scenarios
    test_transactions = await create_comprehensive_test_transactions(customers)
    test_decisions = await create_test_decisions(test_transactions)
    test_reviews = await create_test_human_reviews(test_transactions)
    test_notifications = await create_test_notifications(test_transactions)
    test_audit_events = await create_test_audit_events(test_transactions)
    test_metrics = await create_test_system_metrics()

    # Insert all test data
    if test_transactions:
        await db[config.TRANSACTIONS_COLLECTION].insert_many(test_transactions)
        logger.info(f"Inserted {len(test_transactions)} test transactions")

    if test_decisions:
        await db[config.DECISIONS_COLLECTION].insert_many(test_decisions)
        logger.info(f"Inserted {len(test_decisions)} test decisions")

    if test_reviews:
        await db[config.HUMAN_REVIEWS_COLLECTION].insert_many(test_reviews)
        logger.info(f"Inserted {len(test_reviews)} human reviews")

    if test_notifications:
        await db[config.NOTIFICATIONS_COLLECTION].insert_many(test_notifications)
        logger.info(f"Inserted {len(test_notifications)} notifications")

    if test_audit_events:
        await db[config.AUDIT_EVENTS_COLLECTION].insert_many(test_audit_events)
        logger.info(f"Inserted {len(test_audit_events)} audit events")

    if test_metrics:
        await db[config.SYSTEM_METRICS_COLLECTION].insert_many(test_metrics)
        logger.info(f"Inserted {len(test_metrics)} system metrics")

    logger.info("Comprehensive test data creation completed")


async def create_test_customers() -> List[Customer]:
    """Create diverse customer profiles for testing."""
    return [
        # Low-risk business customers
        Customer(
            customer_id="CUST_LOWRISK_001",
            legal_name="TechStartup Inc",
            display_name="TechStartup",
            customer_type="business",
            country="US",
            risk_profile={
                "risk_level": "low",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                "compliance_rating": "excellent",
                "sanctions_check": "clear"
            },
            behavior_profile={
                "avg_transaction_amount": 5000,
                "transaction_frequency": "weekly",
                "common_recipients": ["Cloud Services Provider", "Software Vendor"],
                "established_relationships": True,
                "transaction_patterns": "regular"
            },
            accounts=[
                {"account_number": "ACC_TS_001", "account_type": "checking", "balance": 500000}
            ]
        ),
        Customer(
            customer_id="CUST_MEDIUMRISK_001",
            legal_name="Manufacturing Corp",
            display_name="ManufacturingCorp",
            customer_type="business",
            country="US",
            risk_profile={
                "risk_level": "medium",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                "compliance_rating": "good",
                "sanctions_check": "clear"
            },
            behavior_profile={
                "avg_transaction_amount": 75000,
                "transaction_frequency": "monthly",
                "common_recipients": ["Equipment Supplier GmbH", "Raw Materials Ltd"],
                "established_relationships": True,
                "transaction_patterns": "seasonal"
            },
            accounts=[
                {"account_number": "ACC_MC_001", "account_type": "business", "balance": 2000000}
            ]
        ),
        Customer(
            customer_id="CUST_HIGHRISK_001",
            legal_name="High Risk Trader LLC",
            display_name="HR Trader",
            customer_type="business",
            country="US",
            risk_profile={
                "risk_level": "high",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                "compliance_rating": "requires_monitoring",
                "sanctions_check": "pending"
            },
            behavior_profile={
                "avg_transaction_amount": 150000,
                "transaction_frequency": "daily",
                "common_recipients": [],
                "established_relationships": False,
                "transaction_patterns": "irregular"
            },
            accounts=[
                {"account_number": "ACC_HR_001", "account_type": "business", "balance": 1000000}
            ]
        ),
        # Individual customers for different scenarios
        Customer(
            customer_id="CUST_INDIVIDUAL_001",
            legal_name="John Smith",
            display_name="John Smith",
            customer_type="individual",
            country="US",
            risk_profile={
                "risk_level": "low",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                "compliance_rating": "excellent",
                "sanctions_check": "clear"
            },
            behavior_profile={
                "avg_transaction_amount": 2500,
                "transaction_frequency": "monthly",
                "common_recipients": ["Jane Doe", "Family Trust"],
                "established_relationships": True,
                "transaction_patterns": "regular"
            },
            accounts=[
                {"account_number": "ACC_JS_001", "account_type": "checking", "balance": 50000}
            ]
        ),
        Customer(
            customer_id="CUST_SUSPICIOUS_001",
            legal_name="Suspicious Entity Inc",
            display_name="Suspicious Entity",
            customer_type="business",
            country="US",
            risk_profile={
                "risk_level": "very_high",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "compliance_rating": "high_risk",
                "sanctions_check": "flagged"
            },
            behavior_profile={
                "avg_transaction_amount": 99999,
                "transaction_frequency": "irregular",
                "common_recipients": [],
                "established_relationships": False,
                "transaction_patterns": "suspicious"
            },
            accounts=[
                {"account_number": "ACC_SUSPECT_001", "account_type": "business", "balance": 200000}
            ]
        ),
        # International customers
        Customer(
            customer_id="CUST_INTERNATIONAL_001",
            legal_name="Global Supplies Ltd",
            display_name="Global Supplies",
            customer_type="business",
            country="GB",
            risk_profile={
                "risk_level": "low",
                "kyc_status": "approved",
                "last_review_date": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
                "compliance_rating": "good",
                "sanctions_check": "clear"
            },
            behavior_profile={
                "avg_transaction_amount": 25000,
                "transaction_frequency": "weekly",
                "common_recipients": ["US Importers", "European Suppliers"],
                "established_relationships": True,
                "transaction_patterns": "regular"
            },
            accounts=[
                {"account_number": "ACC_GS_001", "account_type": "business", "balance": 750000}
            ]
        )
    ]


async def create_test_accounts(customers: List[Customer]) -> List[Dict[str, Any]]:
    """Create account records for customers."""
    accounts = []
    for customer in customers:
        for account_info in customer.accounts:
            account = {
                "account_number": account_info["account_number"],
                "customer_id": customer.customer_id,
                "customer_name": customer.legal_name,
                "account_type": account_info["account_type"],
                "balance": to_decimal128(account_info["balance"]),
                "available_balance": to_decimal128(account_info["balance"]),  # Initially same as balance
                "currency": "USD",
                "status": "active",
                "daily_withdrawal_limit": to_decimal128(10000.0),
                "daily_transfer_limit": to_decimal128(50000.0),
                "overdraft_limit": to_decimal128(0.0),
                "total_deposits": to_decimal128(0.0),
                "total_withdrawals": to_decimal128(0.0),
                "transaction_count": 0,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "kyc_verified": True,
                "risk_score": 0.0,
                "holds": []
            }
            accounts.append(account)
    return accounts


async def create_comprehensive_test_transactions(customers: List[Customer]) -> List[Dict[str, Any]]:
    """Create comprehensive test transactions covering all scenarios."""
    transactions = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    # Scenario 1: Normal ACH payments (should approve)
    for i in range(10):
        txn = {
            "transaction_id": f"TXN_NORMAL_ACH_{i+1:03d}",
            "transaction_type": "ach",
            "amount": to_decimal128(random.uniform(1000, 10000)),
            "currency": "USD",
            "sender": {
                "name": "TechStartup Inc",
                "account_number": "ACC_TS_001",
                "customer_id": "CUST_LOWRISK_001",
                "country": "US"
            },
            "recipient": {
                "name": random.choice(["Cloud Services Provider", "Software Vendor", "Office Supplies Inc"]),
                "account_number": f"ACC_VENDOR_{i+1:03d}",
                "country": "US"
            },
            "status": "approved",
            "created_at": base_time + timedelta(days=i, hours=random.randint(9, 17)),
            "reference_number": f"INV-2024-{i+1:03d}",
            "description": "Regular business payment",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "time_of_day": "business_hours",
                "recurring": True,
                "established_recipient": True
            },
            "risk_flags": []
        }
        transactions.append(txn)

    # Scenario 2: Large wire transfers requiring manager approval
    for i in range(5):
        txn = {
            "transaction_id": f"TXN_LARGE_WIRE_{i+1:03d}",
            "transaction_type": "wire_transfer",
            "amount": to_decimal128(random.uniform(60000, 100000)),
            "currency": "USD",
            "sender": {
                "name": "Manufacturing Corp",
                "account_number": "ACC_MC_001",
                "customer_id": "CUST_MEDIUMRISK_001",
                "country": "US"
            },
            "recipient": {
                "name": "Equipment Supplier GmbH",
                "account_number": f"ACC_ES_{i+1:03d}",
                "country": "DE"
            },
            "status": "pending_manager_approval",
            "created_at": base_time + timedelta(days=i*2, hours=random.randint(9, 17)),
            "reference_number": f"PO-2024-{i+1:03d}",
            "description": "Equipment purchase",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "time_of_day": "business_hours",
                "high_value": True,
                "cross_border": True
            },
            "risk_flags": ["high_amount", "cross_border"]
        }
        transactions.append(txn)

    # Scenario 3: Suspicious transactions (should reject/escalate)
    suspicious_scenarios = [
        {
            "type": "suspicious_round_amount",
            "amount": to_decimal128(99999.00),
            "recipient_country": "KY",
            "flags": ["suspicious_amount", "offshore_jurisdiction"]
        },
        {
            "type": "high_risk_country",
            "amount": to_decimal128(50000.00),
            "recipient_country": "AF",
            "flags": ["high_risk_country", "unusual_destination"]
        },
        {
            "type": "after_hours_large",
            "amount": to_decimal128(75000.00),
            "recipient_country": "US",
            "flags": ["unusual_time", "high_amount"]
        }
    ]

    for i, scenario in enumerate(suspicious_scenarios):
        txn = {
            "transaction_id": f"TXN_SUSPICIOUS_{i+1:03d}",
            "transaction_type": "wire_transfer",
            "amount": scenario["amount"],
            "currency": "USD",
            "sender": {
                "name": "Suspicious Entity Inc",
                "account_number": "ACC_SUSPECT_001",
                "customer_id": "CUST_SUSPICIOUS_001",
                "country": "US"
            },
            "recipient": {
                "name": "Offshore Holdings Ltd",
                "account_number": f"ACC_OFF_{i+1:03d}",
                "country": scenario["recipient_country"]
            },
            "status": "rejected" if "suspicious_amount" in scenario["flags"] else "escalated",
            "created_at": base_time + timedelta(days=i*3, hours=22 if "unusual_time" in scenario["flags"] else 14),
            "reference_number": f"URGENT-{i+1:03d}",
            "description": "Investment opportunity",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "time_of_day": "after_hours" if "unusual_time" in scenario["flags"] else "business_hours",
                "first_time_recipient": True,
                "unusual_pattern": True
            },
            "risk_flags": scenario["flags"]
        }
        transactions.append(txn)

    # Scenario 4: International transfers with enhanced due diligence
    for i in range(3):
        txn = {
            "transaction_id": f"TXN_INTERNATIONAL_{i+1:03d}",
            "transaction_type": "international",
            "amount": to_decimal128(random.uniform(100000, 300000)),
            "currency": "USD",
            "sender": {
                "name": "Global Supplies Ltd",
                "account_number": "ACC_GS_001",
                "customer_id": "CUST_INTERNATIONAL_001",
                "country": "GB"
            },
            "recipient": {
                "name": random.choice(["Dubai Trading Company", "Singapore Imports Ltd", "Tokyo Electronics"]),
                "account_number": f"ACC_INTL_{i+1:03d}",
                "country": random.choice(["AE", "SG", "JP"])
            },
            "status": "pending_review",
            "created_at": base_time + timedelta(days=i*5, hours=random.randint(9, 17)),
            "reference_number": f"EXPORT-2024-{i+1:03d}",
            "description": "Trade settlement",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "time_of_day": "business_hours",
                "trade_finance": True,
                "high_value": True,
                "cross_border": True
            },
            "risk_flags": ["high_amount", "international", "enhanced_due_diligence"]
        }
        transactions.append(txn)

    # Scenario 5: Velocity/pattern detection
    velocity_base_time = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(4):  # 4 transactions in 2 hours
        txn = {
            "transaction_id": f"TXN_VELOCITY_{i+1:03d}",
            "transaction_type": "ach",
            "amount": to_decimal128(25000.00),
            "currency": "USD",
            "sender": {
                "name": "High Risk Trader LLC",
                "account_number": "ACC_HR_001",
                "customer_id": "CUST_HIGHRISK_001",
                "country": "US"
            },
            "recipient": {
                "name": f"Quick Recipient {i+1}",
                "account_number": f"ACC_QUICK_{i+1:03d}",
                "country": "US"
            },
            "status": "escalated",
            "created_at": velocity_base_time + timedelta(minutes=i*30),
            "reference_number": f"RAPID-{i+1:03d}",
            "description": "Rapid transaction",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "velocity_1h": 3 if i >= 2 else i+1,
                "total_amount_1h": to_decimal128((i+1) * 25000),
                "rapid_succession": True
            },
            "risk_flags": ["velocity_pattern", "rapid_succession"]
        }
        transactions.append(txn)

    # Scenario 6: Human review queue scenarios
    review_scenarios = [
        {"priority": "high", "reason": "compliance_flag"},
        {"priority": "medium", "reason": "unusual_pattern"},
        {"priority": "low", "reason": "routine_check"}
    ]

    for i, scenario in enumerate(review_scenarios):
        txn = {
            "transaction_id": f"TXN_REVIEW_{i+1:03d}",
            "transaction_type": "wire_transfer",
            "amount": to_decimal128(random.uniform(30000, 80000)),
            "currency": "USD",
            "sender": {
                "name": "Manufacturing Corp",
                "account_number": "ACC_MC_001",
                "customer_id": "CUST_MEDIUMRISK_001",
                "country": "US"
            },
            "recipient": {
                "name": f"Review Recipient {i+1}",
                "account_number": f"ACC_REV_{i+1:03d}",
                "country": "CA"
            },
            "status": "pending_review",
            "created_at": base_time + timedelta(days=i, hours=random.randint(9, 17)),
            "reference_number": f"REV-2024-{i+1:03d}",
            "description": f"Transaction requiring {scenario['priority']} priority review",
            "embedding": [random.random() for _ in range(config.VECTOR_DIMENSION)],
            "ml_features": {
                "review_priority": scenario["priority"],
                "review_reason": scenario["reason"]
            },
            "risk_flags": [scenario["reason"]]
        }
        transactions.append(txn)

    return transactions


async def create_test_decisions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create test decisions for transactions."""
    decisions = []

    decision_mapping = {
        "approved": {"decision": "approve", "confidence": (90, 99), "risk": (10, 30)},
        "rejected": {"decision": "reject", "confidence": (85, 95), "risk": (70, 95)},
        "escalated": {"decision": "escalate", "confidence": (60, 80), "risk": (40, 70)},
        "pending_review": {"decision": "escalate", "confidence": (50, 75), "risk": (45, 65)},
        "pending_manager_approval": {"decision": "approve", "confidence": (80, 90), "risk": (20, 40)}
    }

    for txn in transactions:
        status = txn["status"]
        if status in decision_mapping:
            mapping = decision_mapping[status]
            decision = {
                "decision_id": f"DEC_{txn['transaction_id'][4:]}",  # Remove TXN_ prefix
                "transaction_id": txn["transaction_id"],
                "decision": mapping["decision"],
                "confidence_score": random.uniform(*mapping["confidence"]),
                "risk_score": random.uniform(*mapping["risk"]),
                "model_version": "claude-3-sonnet-bedrock",
                "processing_time_ms": random.randint(500, 3000),
                "created_at": txn["created_at"] + timedelta(seconds=random.randint(1, 30)),
                "reasoning": {
                    "primary_reasoning": f"Automated decision based on {status} status",
                    "risk_factors": txn.get("risk_flags", []),
                    "compliance_checks": ["kyc_verified", "sanctions_screening"],
                    "pattern_analysis": "normal" if status == "approved" else "flagged"
                },
                "rules_triggered": txn.get("risk_flags", []),
                "similar_cases": [
                    {"transaction_id": f"SIMILAR_{i}", "similarity_score": random.uniform(0.7, 0.9)}
                    for i in range(random.randint(1, 3))
                ]
            }
            decisions.append(decision)

    return decisions


async def create_test_human_reviews(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create test human review records."""
    reviews = []
    reviewers = ["analyst1@company.com", "analyst2@company.com", "manager@company.com"]

    review_statuses = ["pending", "in_progress", "completed"]

    for txn in transactions:
        if txn["status"] in ["pending_review", "escalated", "pending_manager_approval"]:
            status = random.choice(review_statuses)
            review = {
                "review_id": f"REV_{txn['transaction_id'][4:]}",
                "transaction_id": txn["transaction_id"],
                "assigned_to": random.choice(reviewers),
                "priority": txn.get("ml_features", {}).get("review_priority", "medium"),
                "status": status,
                "created_at": txn["created_at"] + timedelta(minutes=random.randint(5, 30)),
                "assigned_at": txn["created_at"] + timedelta(minutes=random.randint(10, 60)),
                "sla_deadline": txn["created_at"] + timedelta(hours=24 if txn.get("ml_features", {}).get("review_priority") == "high" else 72),
                "ai_recommendation": {
                    "recommended_action": "escalate" if "suspicious" in txn["transaction_id"] else "approve",
                    "confidence": random.uniform(60, 85),
                    "key_concerns": txn.get("risk_flags", [])
                }
            }

            if status == "completed":
                review["completed_at"] = review["assigned_at"] + timedelta(hours=random.randint(1, 24))
                review["human_decision"] = {
                    "decision": random.choice(["approve", "reject", "escalate"]),
                    "reasoning": "Manual review completed",
                    "reviewer_notes": "Standard compliance review"
                }

            reviews.append(review)

    return reviews


async def create_test_notifications(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create test notification records."""
    notifications = []

    notification_types = {
        "approved": "transaction_approved",
        "rejected": "transaction_rejected",
        "escalated": "transaction_escalated",
        "pending_review": "review_required"
    }

    for txn in transactions:
        if txn["status"] in notification_types:
            notification = {
                "notification_id": f"NOTIF_{txn['transaction_id'][4:]}",
                "transaction_id": txn["transaction_id"],
                "notification_type": notification_types[txn["status"]],
                "priority": "high" if "suspicious" in txn["transaction_id"] else "medium",
                "status": random.choice(["sent", "delivered", "acknowledged"]),
                "subject": f"Transaction {txn['status'].replace('_', ' ').title()}: {txn['transaction_id']}",
                "message": f"Transaction {txn['transaction_id']} has been {txn['status']}",
                "recipients": [
                    {"email": "compliance@company.com", "type": "primary"},
                    {"email": "alerts@company.com", "type": "secondary"}
                ],
                "created_at": txn["created_at"] + timedelta(minutes=random.randint(1, 10)),
                "sent_at": txn["created_at"] + timedelta(minutes=random.randint(2, 15)),
                "metadata": {
                    "amount": txn["amount"],
                    "sender": txn["sender"]["name"],
                    "recipient": txn["recipient"]["name"]
                }
            }
            notifications.append(notification)

    return notifications


async def create_test_audit_events(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create test audit events."""
    events = []

    event_types = [
        "transaction_created", "transaction_processed", "decision_made",
        "rule_triggered", "review_assigned", "status_changed"
    ]

    for txn in transactions:
        # Create multiple audit events per transaction
        base_time = txn["created_at"]

        # Transaction created event
        events.append({
            "event_id": f"EVT_{txn['transaction_id'][4:]}_001",
            "transaction_id": txn["transaction_id"],
            "event_type": "transaction_created",
            "event_category": "transaction_lifecycle",
            "severity": "info",
            "timestamp": base_time,
            "event_data": {
                "amount": txn["amount"],
                "type": txn["transaction_type"],
                "sender": txn["sender"]["customer_id"]
            },
            "context": {
                "source": "api",
                "user_agent": "transaction-processor/1.0"
            }
        })

        # Decision made event
        events.append({
            "event_id": f"EVT_{txn['transaction_id'][4:]}_002",
            "transaction_id": txn["transaction_id"],
            "event_type": "decision_made",
            "event_category": "ai_decision",
            "severity": "warning" if txn["status"] in ["rejected", "escalated"] else "info",
            "timestamp": base_time + timedelta(seconds=30),
            "event_data": {
                "decision": txn["status"],
                "risk_flags": txn.get("risk_flags", []),
                "processing_time_ms": random.randint(500, 3000)
            },
            "context": {
                "model": "claude-3-sonnet-bedrock",
                "workflow_id": f"workflow-{txn['transaction_id']}"
            }
        })

    return events


async def create_test_system_metrics() -> List[Dict[str, Any]]:
    """Create test system metrics."""
    metrics = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)

    metric_types = [
        {"name": "transaction_processing_time", "unit": "ms", "range": (500, 3000)},
        {"name": "ai_model_response_time", "unit": "ms", "range": (200, 1500)},
        {"name": "database_query_time", "unit": "ms", "range": (50, 500)},
        {"name": "approval_rate", "unit": "percentage", "range": (75, 95)},
        {"name": "false_positive_rate", "unit": "percentage", "range": (2, 8)},
        {"name": "queue_depth", "unit": "count", "range": (0, 50)}
    ]

    # Generate hourly metrics for the past 24 hours
    for hour in range(24):
        timestamp = base_time + timedelta(hours=hour)

        for metric_type in metric_types:
            metric = {
                "metric_id": f"MET_{hour:02d}_{metric_type['name']}",
                "timestamp": timestamp,
                "metric_type": "performance",
                "metric_name": metric_type["name"],
                "value": random.uniform(*metric_type["range"]),
                "unit": metric_type["unit"],
                "dimensions": {
                    "environment": "development",
                    "service": "transaction-processor",
                    "hour_of_day": hour
                }
            }
            metrics.append(metric)

    return metrics
    

if __name__ == "__main__":
    asyncio.run(setup_collections())