"""Worker that hosts workflow and activity implementations."""

import asyncio
from temporalio.client import Client
from typing import List, Tuple


async def find_executions(client: Client, filter: str) -> List[Tuple[str, str]]:
    """
    Uses the supplied Client to retrieve all Workflow Executions that
    match the specified filter criteria. This is a generic implementation
    that's intended to be called by other (more descriptively named) 
    functions that return a particular set of results.

    Args:
        client (Client): A Client connected to a Temporal Service
        filter (str): A string that conforms to Temporal's List Filter syntax

    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing the 
        Workflow ID and Run ID of a Workflow Execution that matched the filter
    """
    results: List[Tuple[str, str]] = []
    async for wf_execution in client.list_workflows(filter):
        results.append((wf_execution.id, wf_execution.run_id))
    return results

async def find_all_transfers(client: Client) -> List[Tuple[str, str]]:
    """
    Return a list of all Money Transfer Workflow Executions, whether
    or not they are currently running, and regardless of status.

    Args:
        client (Client): A Client connected to a Temporal Service

    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing the 
        Workflow ID and Run ID of a Workflow Execution that matched the filter
    """
    filter = 'WorkflowType = "MoneyTransfer"'
    return await find_executions(client, filter)


async def find_running_transfers(client: Client) -> List[Tuple[str, str]]:
    """
    Return a list of all Money Transfer Workflow Executions that
    are currently running.

    Args:
        client (Client): A Client connected to a Temporal Service

    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing the 
        Workflow ID and Run ID of a Workflow Execution that matched the filter
    """
    filter = 'WorkflowType = "MoneyTransfer" AND ExecutionStatus = "Running"'
    return await find_executions(client, filter)


async def find_completed_transfers(client: Client) -> List[Tuple[str, str]]:
    """
    Return a list of all Money Transfer Workflow Executions that
    completed successfully.

    Args:
        client (Client): A Client connected to a Temporal Service

    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing the 
        Workflow ID and Run ID of a Workflow Execution that matched the filter
    """
    filter = 'WorkflowType = "MoneyTransfer" AND ExecutionStatus = "Completed"'
    return await find_executions(client, filter)


async def find_failed_transfers(client: Client) -> List[Tuple[str, str]]:
    """
    Return a list of all Money Transfer Workflow Executions that
    completed successfully.

    Args:
        client (Client): A Client connected to a Temporal Service

    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing the 
        Workflow ID and Run ID of a Workflow Execution that matched the filter
    """
    filter = 'WorkflowType = "MoneyTransfer" AND ExecutionStatus = "Failed"'
    return await find_executions(client, filter)
