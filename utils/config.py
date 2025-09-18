"""Configuration management for the application."""

import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "transaction_ai_poc")
    
    # Temporal
    TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
    TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
    TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "transaction-processing-queue")
    
    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # AI Model Configuration
    BEDROCK_MODEL_VERSION = os.getenv("BEDROCK_MODEL_VERSION", "us.anthropic.claude-opus-4-1-20250805-v1:0")
    
    # Collections
    CUSTOMERS_COLLECTION = "customers"
    TRANSACTIONS_COLLECTION = "transactions"
    DECISIONS_COLLECTION = "transaction_decisions"
    HUMAN_REVIEWS_COLLECTION = "human_reviews"
    AUDIT_EVENTS_COLLECTION = "audit_events"
    NOTIFICATIONS_COLLECTION = "notifications"
    SYSTEM_METRICS_COLLECTION = "system_metrics"
    RULES_COLLECTION = "rules"
    ACCOUNTS_COLLECTION = "accounts"
    JOURNAL_COLLECTION = "transaction_journal"
    BALANCE_UPDATES_COLLECTION = "balance_updates"
    HOLDS_COLLECTION = "balance_holds"
    
    # AI Settings
    CONFIDENCE_THRESHOLD_APPROVE = float(os.getenv("CONFIDENCE_THRESHOLD_APPROVE", 85))
    CONFIDENCE_THRESHOLD_ESCALATE = float(os.getenv("CONFIDENCE_THRESHOLD_ESCALATE", 70))
    AUTO_APPROVAL_LIMIT = float(os.getenv("AUTO_APPROVAL_LIMIT", 50000))
    
    # High Risk Countries
    HIGH_RISK_COUNTRIES: List[str] = ["RU","IR", "KP", "SY", "AF", "YE"]
    
    # Vector Search Settings
    VECTOR_SEARCH_INDEX = "transaction_vector_index"
    VECTOR_DIMENSION = 1024  # Cohere embedding dimension
    MAX_SIMILAR_CASES = 10
    SIMILARITY_THRESHOLD = 0.75
    
    # Application Settings
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # Use "http://api:8000/api" for Docker, "http://localhost:8000/api" for local
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

config = Config()