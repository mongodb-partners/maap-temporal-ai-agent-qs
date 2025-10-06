"""Utilities for handling MongoDB Decimal128 values in Python."""

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Union, Optional, Any
from bson import Decimal128
import json

# Set precision for financial calculations
getcontext().prec = 34  # Decimal128 supports 34 decimal digits

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal and Decimal128 types."""

    def default(self, obj):
        if isinstance(obj, (Decimal, Decimal128)):
            return str(obj)
        return super().default(obj)

def to_decimal128(value: Union[float, int, str, Decimal, Decimal128]) -> Decimal128:
    """
    Convert various numeric types to MongoDB Decimal128.

    Args:
        value: Numeric value to convert

    Returns:
        Decimal128 object suitable for MongoDB storage
    """
    if isinstance(value, Decimal128):
        return value

    if isinstance(value, (float, int)):
        # Convert to string first to avoid floating point precision issues
        decimal_value = Decimal(str(value))
    elif isinstance(value, str):
        decimal_value = Decimal(value)
    elif isinstance(value, Decimal):
        decimal_value = value
    else:
        raise TypeError(f"Cannot convert {type(value)} to Decimal128")

    return Decimal128(decimal_value)

def from_decimal128(value: Union[Decimal128, Any]) -> Decimal:
    """
    Convert MongoDB Decimal128 to Python Decimal for calculations.

    Args:
        value: Decimal128 or other numeric value

    Returns:
        Python Decimal object
    """
    if isinstance(value, Decimal128):
        return value.to_decimal()
    elif isinstance(value, Decimal):
        return value
    elif isinstance(value, (float, int, str)):
        return Decimal(str(value))
    else:
        return Decimal(str(value))

def decimal_to_float(value: Union[Decimal, Decimal128]) -> float:
    """
    Convert Decimal or Decimal128 to float for API responses.

    Warning: This may lose precision and should only be used for display purposes.

    Args:
        value: Decimal or Decimal128 value

    Returns:
        Float representation
    """
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    elif isinstance(value, Decimal):
        return float(value)
    else:
        return float(value)

def round_money(value: Union[Decimal, Decimal128], places: int = 2) -> Decimal:
    """
    Round monetary value to specified decimal places using banker's rounding.

    Args:
        value: Monetary value to round
        places: Number of decimal places (default: 2)

    Returns:
        Rounded Decimal value
    """
    decimal_value = from_decimal128(value)
    quantize_value = Decimal(10) ** -places
    return decimal_value.quantize(quantize_value, rounding=ROUND_HALF_UP)

def add_money(*values: Union[Decimal, Decimal128, float, int, str]) -> Decimal128:
    """
    Add multiple monetary values with proper precision.

    Args:
        *values: Monetary values to add

    Returns:
        Sum as Decimal128
    """
    total = Decimal('0')
    for value in values:
        total += from_decimal128(value)
    return to_decimal128(total)

def subtract_money(
    minuend: Union[Decimal, Decimal128, float, int, str],
    subtrahend: Union[Decimal, Decimal128, float, int, str]
) -> Decimal128:
    """
    Subtract monetary values with proper precision.

    Args:
        minuend: Value to subtract from
        subtrahend: Value to subtract

    Returns:
        Difference as Decimal128
    """
    result = from_decimal128(minuend) - from_decimal128(subtrahend)
    return to_decimal128(result)

def multiply_money(
    value: Union[Decimal, Decimal128, float, int, str],
    factor: Union[Decimal, float, int, str]
) -> Decimal128:
    """
    Multiply monetary value by a factor.

    Args:
        value: Monetary value
        factor: Multiplication factor

    Returns:
        Product as Decimal128
    """
    result = from_decimal128(value) * Decimal(str(factor))
    return to_decimal128(round_money(result))

def compare_money(
    value1: Union[Decimal, Decimal128, float, int, str],
    value2: Union[Decimal, Decimal128, float, int, str]
) -> int:
    """
    Compare two monetary values.

    Args:
        value1: First value
        value2: Second value

    Returns:
        -1 if value1 < value2, 0 if equal, 1 if value1 > value2
    """
    dec1 = from_decimal128(value1)
    dec2 = from_decimal128(value2)

    if dec1 < dec2:
        return -1
    elif dec1 > dec2:
        return 1
    else:
        return 0

def format_money(
    value: Union[Decimal, Decimal128, float, int, str],
    currency: str = "USD",
    include_symbol: bool = True
) -> str:
    """
    Format monetary value for display.

    Args:
        value: Monetary value
        currency: Currency code (default: USD)
        include_symbol: Include currency symbol

    Returns:
        Formatted string
    """
    decimal_value = round_money(from_decimal128(value))

    # Format with thousands separator
    formatted = f"{decimal_value:,.2f}"

    if include_symbol:
        if currency == "USD":
            return f"${formatted}"
        elif currency == "EUR":
            return f"€{formatted}"
        elif currency == "GBP":
            return f"£{formatted}"
        else:
            return f"{formatted} {currency}"
    else:
        return formatted

def validate_positive_amount(value: Union[Decimal, Decimal128, float, int, str]) -> bool:
    """
    Validate that an amount is positive.

    Args:
        value: Amount to validate

    Returns:
        True if positive, False otherwise
    """
    return from_decimal128(value) > 0

def validate_amount_range(
    value: Union[Decimal, Decimal128, float, int, str],
    min_value: Optional[Union[Decimal, float, int, str]] = None,
    max_value: Optional[Union[Decimal, float, int, str]] = None
) -> bool:
    """
    Validate that an amount is within a specified range.

    Args:
        value: Amount to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        True if within range, False otherwise
    """
    decimal_value = from_decimal128(value)

    if min_value is not None and decimal_value < Decimal(str(min_value)):
        return False

    if max_value is not None and decimal_value > Decimal(str(max_value)):
        return False

    return True