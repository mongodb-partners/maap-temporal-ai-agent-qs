"""Worker that hosts workflow and activity implementations."""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from activities import BankingActivities
from shared import MONEY_TRANSFER_TASK_QUEUE_NAME
from workflows import MoneyTransfer

async def main() -> None:
    """Start the worker to process workflows and activities."""
    logging.basicConfig(level=logging.INFO)
    
    client = await Client.connect("localhost:7233", namespace="default")
    
    activities = BankingActivities()
    
    worker = Worker(
        client,
        task_queue=MONEY_TRANSFER_TASK_QUEUE_NAME,
        workflows=[MoneyTransfer],
        activities=[activities.withdraw, activities.deposit, activities.refund],
    )
    
    print("Starting worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
