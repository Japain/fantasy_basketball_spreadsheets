"""API retry utilities with exponential backoff.

This module provides retry logic for Google Sheets API calls to handle
rate limiting (429 errors) and transient server errors (5xx) gracefully.

Uses exponential backoff strategy as recommended by Google:
- Wait time = min((2^n + random_ms), max_backoff)
- Random component prevents thundering herd problem
- Configurable max retries and backoff time
"""

import time
import random
from typing import Callable, TypeVar, Any
from googleapiclient.errors import HttpError

from src.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def api_call_with_retry(
    api_function: Callable[[], T],
    max_retries: int = 5,
    max_backoff: float = 64.0,
    operation_name: str = "API call"
) -> T:
    """
    Execute Google Sheets API call with exponential backoff retry.

    Automatically retries on:
    - 429: Rate limit exceeded
    - 500, 502, 503, 504: Server errors

    Args:
        api_function: Function that makes the API call (should be a lambda or callable
                     that takes no arguments and returns the API response)
        max_retries: Maximum number of retry attempts (default: 5)
        max_backoff: Maximum backoff time in seconds (default: 64)
        operation_name: Descriptive name for logging (e.g., "read timestamp",
                       "update team sheet")

    Returns:
        The result of the API call

    Raises:
        HttpError: If all retries are exhausted or for non-retryable errors

    Examples:
        >>> result = api_call_with_retry(
        ...     lambda: service.spreadsheets().values().get(
        ...         spreadsheetId=spreadsheet_id,
        ...         range='Summary!G1'
        ...     ).execute(),
        ...     operation_name="read timestamp"
        ... )

        >>> result = api_call_with_retry(
        ...     lambda: service.spreadsheets().batchUpdate(
        ...         spreadsheetId=spreadsheet_id,
        ...         body={'requests': requests}
        ...     ).execute(),
        ...     operation_name="batch update formatting"
        ... )
    """
    for attempt in range(max_retries):
        try:
            result = api_function()
            if attempt > 0:
                logger.info(f"✓ {operation_name} succeeded after {attempt} retr{'y' if attempt == 1 else 'ies'}")
            return result

        except HttpError as e:
            # Check if error is retryable
            status = e.resp.status
            is_retryable = status in [429, 500, 502, 503, 504]

            if not is_retryable:
                # Non-retryable error (e.g., 400 Bad Request, 404 Not Found)
                logger.error(f"Non-retryable error for {operation_name}: HTTP {status}")
                raise

            # Check if this was the last attempt
            if attempt == max_retries - 1:
                logger.error(
                    f"Max retries ({max_retries}) exhausted for {operation_name}. "
                    f"Last error: HTTP {status}"
                )
                raise

            # Calculate exponential backoff with jitter
            # Formula: min((2^n + random(0-1000ms)), max_backoff)
            base_wait = 2 ** attempt
            jitter = random.randint(0, 1000) / 1000  # 0-1000 milliseconds
            wait_time = min(base_wait + jitter, max_backoff)

            # Log retry with clear message
            if status == 429:
                logger.warning(
                    f"Rate limit hit for {operation_name}. "
                    f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                )
            else:
                logger.warning(
                    f"Server error (HTTP {status}) for {operation_name}. "
                    f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                )

            # Wait before retrying
            time.sleep(wait_time)

    # This should never be reached due to the raise in the loop
    raise HttpError(
        resp=type('obj', (object,), {'status': 0}),
        content=f"Max retries ({max_retries}) exceeded for {operation_name}"
    )


def create_retry_wrapper(operation_name: str, max_retries: int = 5, max_backoff: float = 64.0):
    """
    Create a reusable retry wrapper with predefined settings.

    Useful for creating operation-specific retry functions.

    Args:
        operation_name: Descriptive name for the operation
        max_retries: Maximum number of retry attempts (default: 5)
        max_backoff: Maximum backoff time in seconds (default: 64)

    Returns:
        Function that wraps API calls with retry logic

    Example:
        >>> retry_read = create_retry_wrapper("read sheet data")
        >>> result = retry_read(lambda: service.spreadsheets().values().get(...).execute())
    """
    def wrapper(api_function: Callable[[], T]) -> T:
        return api_call_with_retry(
            api_function,
            max_retries=max_retries,
            max_backoff=max_backoff,
            operation_name=operation_name
        )
    return wrapper


class APICallCounter:
    """
    Context manager to track API call counts during operations.

    Useful for monitoring and optimizing API usage.

    Example:
        >>> with APICallCounter() as counter:
        ...     # Make API calls
        ...     result1 = service.spreadsheets().get(...).execute()
        ...     result2 = service.spreadsheets().values().get(...).execute()
        ...     print(f"Made {counter.count} API calls")
    """

    def __init__(self):
        self.count = 0
        self.read_count = 0
        self.write_count = 0

    def increment(self, call_type: str = "unknown"):
        """
        Increment API call counter.

        Args:
            call_type: Type of call ('read', 'write', or 'unknown')
        """
        self.count += 1
        if call_type == "read":
            self.read_count += 1
        elif call_type == "write":
            self.write_count += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(
            f"API call summary: {self.count} total "
            f"({self.read_count} reads, {self.write_count} writes)"
        )
        return False

    def __str__(self):
        return (
            f"APICallCounter(total={self.count}, "
            f"reads={self.read_count}, writes={self.write_count})"
        )
