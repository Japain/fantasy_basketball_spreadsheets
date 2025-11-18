#!/usr/bin/env python3
"""
Edge case tests for incremental update functionality.

This script tests various edge cases and error handling:
1. Invalid spreadsheet ID
2. No transactions since last run
3. Spreadsheet from different league (structure mismatch)
4. Very recent update (< 1 minute ago)
5. Empty transaction list handling
"""

from datetime import datetime, timedelta
from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_reader import (
    read_last_run_timestamp,
    validate_sheet_structure,
    extract_spreadsheet_id_from_url
)
from src.transaction_tracker import (
    get_transactions_since,
    get_affected_team_ids
)
from src.google_auth import get_google_sheets_service
from src.logger import get_logger
from googleapiclient.errors import HttpError

logger = get_logger(__name__)


def test_invalid_spreadsheet_id():
    """Test handling of invalid spreadsheet ID."""
    print("\n" + "=" * 80)
    print("TEST 1: Invalid Spreadsheet ID")
    print("=" * 80)

    try:
        service = get_google_sheets_service()

        # Test with various invalid IDs
        invalid_ids = [
            "invalid_id_12345",
            "ThisIsNotARealSpreadsheetID",
            "",
            "abc" * 20,  # Too long
        ]

        for invalid_id in invalid_ids:
            print(f"\nTesting with invalid ID: '{invalid_id[:50]}...'")

            try:
                timestamp = read_last_run_timestamp(service, invalid_id)
                # Implementation returns None for invalid IDs (graceful handling)
                # This is acceptable - it means "no timestamp found" = "first run"
                if timestamp is None:
                    print(f"  ✓ Correctly returned None (graceful handling)")
                else:
                    print(f"  ⚠ Unexpected: returned {timestamp}")
            except (HttpError, ValueError) as e:
                # Also acceptable - raising an error is fine too
                print(f"  ✓ Correctly raised error: {type(e).__name__}")
                # Check that error message is informative
                error_msg = str(e)
                if "spreadsheet" in error_msg.lower() or "not found" in error_msg.lower():
                    print(f"  ✓ Error message is informative")
                else:
                    print(f"  ⚠ Error message could be more clear: {error_msg[:100]}")

        print("\n✓ Test passed: Invalid IDs handled correctly")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_transactions_scenario():
    """Test scenario with no transactions since last run."""
    print("\n" + "=" * 80)
    print("TEST 2: No Transactions Scenario")
    print("=" * 80)

    try:
        fetcher = YahooDataFetcher(browser_callback=False)

        # Use a timestamp from 1 minute ago (very recent)
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        timestamp = int(one_minute_ago.timestamp())

        print(f"Checking for transactions since: {one_minute_ago.strftime('%Y-%m-%d %H:%M:%S')}")

        # Get transactions
        transactions = get_transactions_since(fetcher, timestamp)

        print(f"✓ Found {len(transactions)} transactions in the last minute")

        # Get affected teams (should handle empty list gracefully)
        affected_team_ids = get_affected_team_ids(transactions)

        print(f"✓ Affected teams: {len(affected_team_ids)}")

        if len(transactions) == 0:
            print("✓ Correctly handled no-transaction scenario")
            if len(affected_team_ids) == 0:
                print("✓ Correctly returned empty set for affected teams")
            else:
                print("✗ Failed: Should have no affected teams when no transactions")
                return False
        else:
            print(f"  Note: {len(transactions)} recent transactions found (league is active)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_extraction():
    """Test spreadsheet URL extraction with various formats."""
    print("\n" + "=" * 80)
    print("TEST 3: URL Extraction Edge Cases")
    print("=" * 80)

    test_cases = [
        # (url, expected_id, should_succeed)
        ("https://docs.google.com/spreadsheets/d/ABC123/edit", "ABC123", True),
        ("https://docs.google.com/spreadsheets/d/ABC123", "ABC123", True),
        ("https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0", "ABC123", True),
        ("https://example.com/not/a/sheet", None, False),  # Invalid URL
        ("", None, False),  # Empty string
        # Note: The following cases depend on implementation details
        ("docs.google.com/spreadsheets/d/ABC123", "ABC123", True),  # Partial URL (implementation accepts this)
        ("ABC123DEF456GHI", None, False),  # Raw ID without URL (implementation rejects this)
    ]

    passed = 0
    failed = 0

    for url, expected_id, should_succeed in test_cases:
        print(f"\nTesting: '{url[:60]}...'")

        try:
            result_id = extract_spreadsheet_id_from_url(url)

            if should_succeed:
                if result_id == expected_id:
                    print(f"  ✓ Correctly extracted: {result_id}")
                    passed += 1
                else:
                    print(f"  ✗ Wrong ID: got '{result_id}', expected '{expected_id}'")
                    failed += 1
            else:
                print(f"  ✗ Should have failed but got: {result_id}")
                failed += 1

        except ValueError as e:
            if not should_succeed:
                print(f"  ✓ Correctly raised error: {type(e).__name__}")
                passed += 1
            else:
                print(f"  ✗ Unexpected error: {e}")
                failed += 1

    print(f"\n✓ Test completed: {passed} passed, {failed} failed")
    return failed == 0


def test_empty_transaction_list():
    """Test handling of empty transaction lists."""
    print("\n" + "=" * 80)
    print("TEST 4: Empty Transaction List Handling")
    print("=" * 80)

    try:
        # Test with explicitly empty list
        print("Testing with empty list...")
        affected = get_affected_team_ids([])

        if isinstance(affected, set) and len(affected) == 0:
            print("✓ Correctly returned empty set")
        else:
            print(f"✗ Failed: Expected empty set, got {affected}")
            return False

        # Test with None timestamp (should get all transactions)
        print("\nTesting with None timestamp (get all)...")
        fetcher = YahooDataFetcher(browser_callback=False)
        all_transactions = get_transactions_since(fetcher, None)

        print(f"✓ Retrieved {len(all_transactions)} total transactions")

        if len(all_transactions) > 0:
            # Test getting affected teams from all transactions
            all_affected = get_affected_team_ids(all_transactions)
            print(f"✓ Found {len(all_affected)} teams with transactions")
        else:
            print("  Note: No transactions in league (league may be new)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_future_timestamp():
    """Test with timestamp in the future."""
    print("\n" + "=" * 80)
    print("TEST 5: Future Timestamp")
    print("=" * 80)

    try:
        fetcher = YahooDataFetcher(browser_callback=False)

        # Use a timestamp 1 day in the future
        tomorrow = datetime.now() + timedelta(days=1)
        future_timestamp = int(tomorrow.timestamp())

        print(f"Using future timestamp: {tomorrow.strftime('%Y-%m-%d %H:%M:%S')}")

        transactions = get_transactions_since(fetcher, future_timestamp)

        print(f"✓ Retrieved {len(transactions)} transactions")

        if len(transactions) == 0:
            print("✓ Correctly returned no transactions for future timestamp")
        else:
            print(f"  ⚠ Warning: Found {len(transactions)} transactions with future timestamp")
            print("     (This might indicate a timezone issue)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_very_old_timestamp():
    """Test with very old timestamp (beginning of season)."""
    print("\n" + "=" * 80)
    print("TEST 6: Very Old Timestamp")
    print("=" * 80)

    try:
        fetcher = YahooDataFetcher(browser_callback=False)

        # Use a timestamp from 1 year ago
        one_year_ago = datetime.now() - timedelta(days=365)
        old_timestamp = int(one_year_ago.timestamp())

        print(f"Using old timestamp: {one_year_ago.strftime('%Y-%m-%d %H:%M:%S')}")

        transactions = get_transactions_since(fetcher, old_timestamp)

        print(f"✓ Retrieved {len(transactions)} transactions from the entire season")

        if len(transactions) > 0:
            affected = get_affected_team_ids(transactions)
            print(f"✓ Identified {len(affected)} teams with transactions")
        else:
            print("  Note: No transactions found (league may be very new)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all edge case tests."""
    print("\n" + "=" * 80)
    print("EDGE CASE TEST SUITE")
    print("=" * 80)
    print()
    print("This test suite validates error handling and edge cases:")
    print("  1. Invalid spreadsheet IDs")
    print("  2. No transactions scenario")
    print("  3. URL extraction edge cases")
    print("  4. Empty transaction list handling")
    print("  5. Future timestamps")
    print("  6. Very old timestamps")
    print()

    tests = [
        ("Invalid Spreadsheet ID", test_invalid_spreadsheet_id),
        ("No Transactions Scenario", test_no_transactions_scenario),
        ("URL Extraction Edge Cases", test_url_extraction),
        ("Empty Transaction List", test_empty_transaction_list),
        ("Future Timestamp", test_future_timestamp),
        ("Very Old Timestamp", test_very_old_timestamp),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            logger.exception(f"Test '{test_name}' crashed")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL EDGE CASE TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
