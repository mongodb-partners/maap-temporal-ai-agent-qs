"""Starter script to initiate money transfer workflows."""

import asyncio
import sys
import uuid
from temporalio.client import Client
from shared import PaymentDetails, MONEY_TRANSFER_TASK_QUEUE_NAME
from workflows import MoneyTransfer

async def main() -> None:
    """Start a money transfer workflow with the given parameters."""
    # You can override these default values via positional command-line params
    source_account = "A123"
    target_account = "B456"
    amount = 25000  # value is specified in cents to avoid rounding errors
    reference_id = f"REF{uuid.uuid4().hex[:6].upper()}"

    if len(sys.argv) >= 2:
        source_account = sys.argv[1]

    if len(sys.argv) >= 3:
        target_account = sys.argv[2]

    if len(sys.argv) >= 4:
        amount = int(sys.argv[3])

    if len(sys.argv) >= 5:
        reference_id = sys.argv[4]

    payment_details = PaymentDetails(
        source_account=source_account,
        target_account=target_account,
        amount=amount,
        reference_id=reference_id
    )

    client = await Client.connect("localhost:7233", namespace="default")
    
    workflow_id = f"money-transfer-{reference_id}"
    
    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Transfer: ${amount / 100:.2f} from {source_account} to {target_account}")
    
    handle = await client.start_workflow(
        MoneyTransfer.run,
        payment_details,
        id=workflow_id,
        task_queue=MONEY_TRANSFER_TASK_QUEUE_NAME,
    )
    
    print(f"Initiated transfer, Workflow ID: {handle.id}, run ID: {handle.result_run_id}")
    
    try:
        result = await handle.result()
        print(f"✓ Transfer success: {result}")
    except Exception as e:
        print(f"✗ Transfer failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
