"""Worker that hosts workflow and activity implementations."""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from temporal.activities import TransactionActivities
from temporal.workflows import TransactionProcessingWorkflow
from temporal.shared import TRANSACTION_PROCESSING_TASK_QUEUE
from utils.config import config

async def main() -> None:
    """Start the worker to process workflows and activities."""
    logging.basicConfig(level=logging.INFO)
    
    # Connect to Temporal
    client = await Client.connect(config.TEMPORAL_HOST, namespace=config.TEMPORAL_NAMESPACE)
    
    # Create activities instance
    activities = TransactionActivities()
    
    # Create worker
    worker = Worker(
        client,
        task_queue=TRANSACTION_PROCESSING_TASK_QUEUE,
        workflows=[TransactionProcessingWorkflow],
        activities=[
            activities.validate_and_hold_funds,
            activities.enrich_transaction_data,
            activities.perform_risk_assessment,
            activities.find_similar_transactions,
            activities.analyze_fraud_network,
            activities.ai_decision_analysis,
            activities.store_decision,
            activities.queue_for_human_review,
            activities.send_notification,
            activities.execute_fund_transfer,
            activities.cleanup_hold
        ],
    )
    
    print(f"Starting worker on task queue: {TRANSACTION_PROCESSING_TASK_QUEUE}")
    print(f"Connected to Temporal at: {config.TEMPORAL_HOST}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
