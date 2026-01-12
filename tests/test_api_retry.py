"""
Test API retry logic with exponential backoff.

This script tests the retry module by simulating various API error scenarios:
1. Successful API call (no retry needed)
2. Rate limit errors (429) with eventual success
3. Server errors (5xx) with eventual success
4. Max retries exhausted
5. Non-retryable errors (4xx)
"""

from unittest.mock import Mock
from googleapiclient.errors import HttpError
from src.api_retry import api_call_with_retry, APICallCounter
from src.logger import get_logger
import time

logger = get_logger(__name__)


def create_http_error(status_code: int, message: str = "Test error"):
    """
    Create a mock HttpError for testing.

    Args:
        status_code: HTTP status code
        message: Error message

    Returns:
        HttpError instance
    """
    resp = Mock()
    resp.status = status_code
    return HttpError(resp=resp, content=message.encode())


def test_successful_call():
    """Test 1: Successful API call with no retries."""
    print("\n" + "=" * 80)
    print("TEST 1: Successful API call (no retry needed)")
    print("=" * 80)

    call_count = [0]

    def mock_api_call():
        call_count[0] += 1
        return {"success": True, "data": "test"}

    result = api_call_with_retry(mock_api_call, operation_name="test successful call")

    assert result == {"success": True, "data": "test"}
    assert call_count[0] == 1, f"Expected 1 call, got {call_count[0]}"
    print("✓ Test passed: Successful call without retry")


def test_rate_limit_with_retry():
    """Test 2: Rate limit error (429) that succeeds after retries."""
    print("\n" + "=" * 80)
    print("TEST 2: Rate limit (429) with successful retry")
    print("=" * 80)

    call_count = [0]

    def mock_api_call_with_rate_limit():
        call_count[0] += 1
        if call_count[0] < 3:
            # Fail first 2 attempts with rate limit
            raise create_http_error(429, "Rate limit exceeded")
        return {"success": True, "data": "test"}

    start_time = time.time()
    result = api_call_with_retry(
        mock_api_call_with_rate_limit,
        max_retries=5,
        max_backoff=4,  # Lower for faster testing
        operation_name="test rate limit"
    )
    elapsed = time.time() - start_time

    assert result == {"success": True, "data": "test"}
    assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"
    assert elapsed >= 1.0, f"Expected at least 1s delay from backoff, got {elapsed:.2f}s"
    print(f"✓ Test passed: Succeeded after 2 retries (total time: {elapsed:.2f}s)")


def test_server_error_with_retry():
    """Test 3: Server error (503) that succeeds after retries."""
    print("\n" + "=" * 80)
    print("TEST 3: Server error (503) with successful retry")
    print("=" * 80)

    call_count = [0]

    def mock_api_call_with_server_error():
        call_count[0] += 1
        if call_count[0] < 2:
            # Fail first attempt with server error
            raise create_http_error(503, "Service unavailable")
        return {"success": True, "data": "test"}

    result = api_call_with_retry(
        mock_api_call_with_server_error,
        max_retries=5,
        max_backoff=4,
        operation_name="test server error"
    )

    assert result == {"success": True, "data": "test"}
    assert call_count[0] == 2, f"Expected 2 calls, got {call_count[0]}"
    print("✓ Test passed: Succeeded after 1 retry")


def test_max_retries_exhausted():
    """Test 4: Rate limit that exhausts max retries."""
    print("\n" + "=" * 80)
    print("TEST 4: Max retries exhausted")
    print("=" * 80)

    call_count = [0]

    def mock_api_call_always_fails():
        call_count[0] += 1
        raise create_http_error(429, "Rate limit exceeded")

    try:
        api_call_with_retry(
            mock_api_call_always_fails,
            max_retries=3,
            max_backoff=2,
            operation_name="test max retries"
        )
        assert False, "Should have raised HttpError"
    except HttpError as e:
        assert e.resp.status == 429
        assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"
        print(f"✓ Test passed: Max retries (3) exhausted as expected")


def test_non_retryable_error():
    """Test 5: Non-retryable error (404) should fail immediately."""
    print("\n" + "=" * 80)
    print("TEST 5: Non-retryable error (404)")
    print("=" * 80)

    call_count = [0]

    def mock_api_call_not_found():
        call_count[0] += 1
        raise create_http_error(404, "Not found")

    try:
        api_call_with_retry(
            mock_api_call_not_found,
            max_retries=5,
            operation_name="test non-retryable"
        )
        assert False, "Should have raised HttpError"
    except HttpError as e:
        assert e.resp.status == 404
        assert call_count[0] == 1, f"Expected 1 call (no retries), got {call_count[0]}"
        print("✓ Test passed: Non-retryable error failed immediately without retry")


def test_api_call_counter():
    """Test 6: API call counter tracking."""
    print("\n" + "=" * 80)
    print("TEST 6: API call counter")
    print("=" * 80)

    with APICallCounter() as counter:
        # Simulate API calls
        counter.increment("read")
        counter.increment("read")
        counter.increment("write")
        counter.increment("read")

        assert counter.count == 4
        assert counter.read_count == 3
        assert counter.write_count == 1

    print("✓ Test passed: API call counter tracked correctly")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "API RETRY LOGIC TESTS" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        test_successful_call()
        test_rate_limit_with_retry()
        test_server_error_with_retry()
        test_max_retries_exhausted()
        test_non_retryable_error()
        test_api_call_counter()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  • Successful calls work without retry")
        print("  • Rate limits (429) trigger exponential backoff")
        print("  • Server errors (5xx) are retried automatically")
        print("  • Max retries are enforced correctly")
        print("  • Non-retryable errors (4xx) fail immediately")
        print("  • API call counter tracks usage accurately")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    main()
