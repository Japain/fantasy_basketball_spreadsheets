#!/usr/bin/env python3
"""
Test script for transaction tracking functionality.

Tests the transaction_tracker module with real league data and edge cases.
"""

from datetime import datetime, timedelta
from src.yahoo_data_fetcher import YahooDataFetcher
from src.transaction_tracker import (
    get_transactions_since,
    get_affected_team_ids,
    parse_transaction_timestamp
)
from src.logger import get_logger

logger = get_logger(__name__)


def test_all_transactions():
    """Test retrieving all transactions from Yahoo API."""
    print("\n" + "=" * 80)
    print("TEST 1: Retrieve All Transactions")
    print("=" * 80)

    try:
        # Initialize fetcher
        print("Initializing Yahoo Data Fetcher...")
        fetcher = YahooDataFetcher(browser_callback=False)

        # Get all transactions
        print("Retrieving all transactions...")
        transactions = get_transactions_since(fetcher, last_run_timestamp=None)

        print(f"✓ Retrieved {len(transactions)} total transactions")

        # Show sample transactions
        if transactions:
            print("\nSample transactions (first 5):")
            for trans in transactions[:5]:
                print(f"  - {trans}")

            # Count by type
            type_counts = {}
            for trans in transactions:
                trans_type = trans.transaction_type.value
                type_counts[trans_type] = type_counts.get(trans_type, 0) + 1

            print("\nTransaction breakdown by type:")
            for trans_type, count in sorted(type_counts.items()):
                print(f"  - {trans_type}: {count}")

            # FAAB transactions
            faab_transactions = [t for t in transactions if t.faab_bid is not None and t.faab_bid > 0]
            print(f"\nFAAB waiver claims: {len(faab_transactions)}")
            if faab_transactions:
                total_faab = sum(t.faab_bid for t in faab_transactions)
                avg_faab = total_faab / len(faab_transactions)
                max_faab = max(t.faab_bid for t in faab_transactions)
                print(f"  - Total FAAB spent: ${total_faab}")
                print(f"  - Average bid: ${avg_faab:.2f}")
                print(f"  - Highest bid: ${max_faab}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_transactions_since_timestamp():
    """Test retrieving transactions since a specific timestamp."""
    print("\n" + "=" * 80)
    print("TEST 2: Retrieve Transactions Since Timestamp")
    print("=" * 80)

    try:
        # Initialize fetcher
        fetcher = YahooDataFetcher(browser_callback=False)

        # Get timestamp from 7 days ago
        seven_days_ago = datetime.now() - timedelta(days=7)
        timestamp = int(seven_days_ago.timestamp())

        print(f"Retrieving transactions since: {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Timestamp: {timestamp}")

        # Get filtered transactions
        transactions = get_transactions_since(fetcher, last_run_timestamp=timestamp)

        print(f"✓ Found {len(transactions)} transactions in the last 7 days")

        # Show most recent transactions
        if transactions:
            # Sort by timestamp (most recent first)
            sorted_trans = sorted(transactions, key=lambda t: t.timestamp, reverse=True)

            print("\nMost recent transactions:")
            for trans in sorted_trans[:5]:
                trans_time = datetime.fromtimestamp(trans.timestamp)
                print(f"  - [{trans_time.strftime('%Y-%m-%d %H:%M')}] {trans}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_affected_teams():
    """Test identifying affected teams from transactions."""
    print("\n" + "=" * 80)
    print("TEST 3: Identify Affected Teams")
    print("=" * 80)

    try:
        # Initialize fetcher
        fetcher = YahooDataFetcher(browser_callback=False)

        # Get transactions from last 14 days
        two_weeks_ago = datetime.now() - timedelta(days=14)
        timestamp = int(two_weeks_ago.timestamp())

        print(f"Analyzing transactions from the last 14 days...")

        # Get transactions
        transactions = get_transactions_since(fetcher, last_run_timestamp=timestamp)
        print(f"Found {len(transactions)} transactions")

        # Get affected teams
        affected_team_ids = get_affected_team_ids(transactions)

        print(f"\n✓ Identified {len(affected_team_ids)} affected teams")
        print(f"Team IDs: {sorted(affected_team_ids)}")

        # Show transaction breakdown by team
        if transactions:
            print("\nTransaction count by team:")
            team_trans_count = {}
            team_names = {}

            for trans in transactions:
                team_trans_count[trans.team_id] = team_trans_count.get(trans.team_id, 0) + 1
                team_names[trans.team_id] = trans.team_name

            for team_id in sorted(affected_team_ids):
                count = team_trans_count.get(team_id, 0)
                name = team_names.get(team_id, "Unknown")
                print(f"  - Team {team_id} ({name}): {count} transactions")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 80)
    print("TEST 4: Edge Cases")
    print("=" * 80)

    try:
        # Test 1: Empty transaction list
        print("\n1. Testing with empty transaction list...")
        affected = get_affected_team_ids([])
        assert len(affected) == 0, "Empty list should return empty set"
        print("   ✓ Empty list handled correctly")

        # Test 2: Very old timestamp (should get all transactions)
        print("\n2. Testing with very old timestamp (1 year ago)...")
        fetcher = YahooDataFetcher(browser_callback=False)
        one_year_ago = datetime.now() - timedelta(days=365)
        timestamp = int(one_year_ago.timestamp())

        transactions = get_transactions_since(fetcher, last_run_timestamp=timestamp)
        print(f"   ✓ Retrieved {len(transactions)} transactions from the entire season")

        # Test 3: Future timestamp (should get no transactions)
        print("\n3. Testing with future timestamp...")
        future = datetime.now() + timedelta(days=1)
        future_timestamp = int(future.timestamp())

        transactions = get_transactions_since(fetcher, last_run_timestamp=future_timestamp)
        print(f"   ✓ Retrieved {len(transactions)} transactions (should be 0 or very few)")

        # Test 4: Timestamp parsing
        print("\n4. Testing timestamp parsing...")
        raw_transactions = fetcher.get_all_transactions()
        if raw_transactions:
            sample_trans = raw_transactions[0]
            parsed_timestamp = parse_transaction_timestamp(sample_trans)
            trans_datetime = datetime.fromtimestamp(parsed_timestamp)
            print(f"   ✓ Parsed timestamp: {parsed_timestamp}")
            print(f"     Date: {trans_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("   ⚠ No transactions available to test parsing")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def test_transaction_details():
    """Test detailed transaction information extraction."""
    print("\n" + "=" * 80)
    print("TEST 5: Transaction Details")
    print("=" * 80)

    try:
        fetcher = YahooDataFetcher(browser_callback=False)

        # Get recent transactions
        one_week_ago = datetime.now() - timedelta(days=7)
        timestamp = int(one_week_ago.timestamp())

        transactions = get_transactions_since(fetcher, last_run_timestamp=timestamp)
        print(f"Analyzing {len(transactions)} transactions from the last week...")

        if not transactions:
            print("⚠ No recent transactions to analyze")
            return True

        # Test different transaction types
        adds = [t for t in transactions if t.transaction_type.value == 'add']
        drops = [t for t in transactions if t.transaction_type.value == 'drop']
        trades = [t for t in transactions if t.transaction_type.value == 'trade']
        add_drops = [t for t in transactions if t.transaction_type.value == 'add/drop']

        print(f"\n✓ Transaction type breakdown:")
        print(f"  - Adds: {len(adds)}")
        print(f"  - Drops: {len(drops)}")
        print(f"  - Trades: {len(trades)}")
        print(f"  - Add/Drops: {len(add_drops)}")

        # Show examples of each type
        if adds:
            print(f"\n  Example ADD transaction:")
            print(f"    {adds[0]}")

        if drops:
            print(f"\n  Example DROP transaction:")
            print(f"    {drops[0]}")

        if add_drops:
            print(f"\n  Example ADD/DROP transaction:")
            print(f"    {add_drops[0]}")

        # Validate data completeness
        print(f"\n✓ Data completeness check:")
        for i, trans in enumerate(transactions[:10]):  # Check first 10
            assert trans.transaction_id, f"Transaction {i} missing ID"
            assert trans.timestamp > 0, f"Transaction {i} has invalid timestamp"
            assert trans.team_id, f"Transaction {i} missing team_id"
            assert trans.team_name, f"Transaction {i} missing team_name"
            assert trans.player_name, f"Transaction {i} missing player_name"

        print(f"  - All checked transactions have complete data")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        logger.exception("Test failed")
        return False


def main():
    """Run all transaction tracker tests."""
    print("\n" + "=" * 80)
    print("TRANSACTION TRACKER TEST SUITE")
    print("=" * 80)

    tests = [
        ("All Transactions", test_all_transactions),
        ("Transactions Since Timestamp", test_transactions_since_timestamp),
        ("Affected Teams", test_affected_teams),
        ("Edge Cases", test_edge_cases),
        ("Transaction Details", test_transaction_details),
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
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
