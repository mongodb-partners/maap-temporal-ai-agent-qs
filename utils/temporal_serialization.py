"""Serialization utilities for Temporal workflows."""

from typing import Any, Dict, List, Union
from bson import Decimal128
from decimal import Decimal


def sanitize_for_json(data: Any) -> Any:
    """
    Recursively convert Decimal128 and Decimal values to strings for JSON serialization.

    This is necessary for Temporal workflows which need to serialize data to JSON.

    Args:
        data: Any data structure that might contain Decimal128 values

    Returns:
        Data with all Decimal128/Decimal values converted to strings
    """
    if isinstance(data, Decimal128):
        return str(data.to_decimal())
    elif isinstance(data, Decimal):
        return str(data)
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_for_json(item) for item in data)
    else:
        return data


def prepare_activity_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare an activity result for return to Temporal workflow.

    Ensures all values are JSON-serializable.

    Args:
        result: The result dictionary from an activity

    Returns:
        Sanitized result safe for Temporal
    """
    return sanitize_for_json(result)