#!/usr/bin/env python3
"""
Integration test for incremental update functionality.

This script tests the complete incremental update workflow:
1. Create initial spreadsheet with timestamp
2. Update with no new transactions (summary only)
3. Update with transactions (only affected teams)
4. Force full update (all teams)
5. Verify timestamp management

This is a comprehensive integration test that requires:
- Valid Yahoo OAuth credentials
- Valid Google OAuth credentials
- Network access to both APIs
"""

from datetime import datetime, timedelta
from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_generator import generate_league_report
from src.sheet_reader import read_last_run_timestamp, extract_spreadsheet_id_from_url
from src.sheet_updater import update_summary_sheet, update_team_sheet
from src.transaction_tracker import get_transactions_since, get_affected_team_ids
from src.google_auth import get_google_sheets_service
from src.logger import get_logger
import time

logger = get_logger(__name__)


def test_create_initial_spreadsheet(fetcher):
    """Test creating initial spreadsheet with timestamp."""
    print("\n" + "=" * 80)
    print("TEST 1: Create Initial Spreadsheet")
    print("=" * 80)

    try:
        # Extract league data
        print("Extracting league data...")
        league_data = fetcher.extract_league_data()

        print(f"✓ League data extracted: {league_data.league_name}")
        print(f"  Teams: {league_data.num_teams}")
        print(f"  Total Players: {league_data.get_total_players()}")

        # Generate spreadsheet
        print("\nGenerating spreadsheet...")
        sheet_url = generate_league_report(
            league_data,
            sheet_title="Incremental Update Test"
        )

        spreadsheet_id = extract_spreadsheet_id_from_url(sheet_url)

        print(f"✓ Spreadsheet created successfully")
        print(f"  URL: {sheet_url}")
        print(f"  ID: {spreadsheet_id}")

        # Verify timestamp was stored
        print("\nVerifying timestamp storage...")
        service = get_google_sheets_service()
        timestamp = read_last_run_timestamp(service, spreadsheet_id)

        if timestamp:
            print(f"✓ Timestamp stored: {timestamp.isoformat()}")
            # Verify it's recent (within last minute)
            time_diff = datetime.now() - timestamp.replace(tzinfo=None)
            if time_diff.total_seconds() < 60:
                print(f"  Timestamp is recent (created {time_diff.total_seconds():.0f} seconds ago)")
            else:
                print(f"  ⚠ Warning: Timestamp seems old ({time_diff})")
        else:
            print("✗ Failed: No timestamp found in spreadsheet")
            return None, None

        return spreadsheet_id, league_data

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_update_no_transactions(spreadsheet_id, fetcher, league_data):
    """Test update when no transactions have occurred."""
    print("\n" + "=" * 80)
    print("TEST 2: Update With No New Transactions")
    print("=" * 80)

    try:
        service = get_google_sheets_service()

        # Read last timestamp (should be very recent)
        print("Reading last update timestamp...")
        last_timestamp = read_last_run_timestamp(service, spreadsheet_id)

        if not last_timestamp:
            print("✗ Failed: Could not read timestamp")
            return False

        print(f"  Last updated: {last_timestamp.isoformat()}")

        # Check for transactions since last run (should be none or very few)
        print("\nChecking for new transactions...")
        last_timestamp_unix = int(last_timestamp.timestamp())
        transactions = get_transactions_since(fetcher, last_timestamp_unix)

        print(f"  Found {len(transactions)} transactions since last run")

        # Update summary sheet only (simulating the no-transaction update)
        print("\nUpdating summary sheet...")
        update_summary_sheet(service, spreadsheet_id, league_data)

        print("✓ Summary updated successfully")

        # Verify new timestamp is stored and is more recent
        print("\nVerifying timestamp was updated...")
        new_timestamp = read_last_run_timestamp(service, spreadsheet_id)

        if new_timestamp and new_timestamp > last_timestamp:
            print(f"✓ Timestamp updated: {new_timestamp.isoformat()}")
            time_diff = (new_timestamp - last_timestamp).total_seconds()
            print(f"  Time difference: {time_diff:.1f} seconds")
        else:
            print("✗ Failed: Timestamp was not updated")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_with_transactions(spreadsheet_id, fetcher, league_data):
    """Test update when transactions have occurred."""
    print("\n" + "=" * 80)
    print("TEST 3: Update With Transactions")
    print("=" * 80)

    try:
        service = get_google_sheets_service()

        # Use a timestamp from 7 days ago to catch real transactions
        print("Simulating update after 7 days...")
        one_week_ago = datetime.now() - timedelta(days=7)
        simulated_last_run = int(one_week_ago.timestamp())

        print(f"  Simulated last run: {one_week_ago.strftime('%Y-%m-%d %H:%M:%S')}")

        # Get transactions since simulated last run
        print("\nFetching transactions...")
        transactions = get_transactions_since(fetcher, simulated_last_run)

        print(f"✓ Found {len(transactions)} transactions in the last 7 days")

        if len(transactions) == 0:
            print("  ⚠ No transactions to test with (league may be inactive)")
            print("  Skipping transaction-based update test")
            return True  # Not a failure, just no data

        # Identify affected teams
        print("\nIdentifying affected teams...")
        affected_team_ids = get_affected_team_ids(transactions)

        print(f"✓ Identified {len(affected_team_ids)} affected teams")

        # Get team objects for affected teams
        affected_teams = [
            team for team in league_data.teams
            if team.team_id in affected_team_ids
        ]

        print(f"\nAffected teams:")
        for team in affected_teams:
            trans_count = sum(1 for t in transactions if t.team_id == team.team_id)
            print(f"  - {team.team_name}: {trans_count} transactions")

        # Update only affected teams
        print(f"\nUpdating {len(affected_teams)} team sheets...")
        for team in affected_teams:
            print(f"  Updating: {team.team_name}")
            update_team_sheet(service, spreadsheet_id, team)

        print(f"✓ Updated {len(affected_teams)} team sheets")

        # Update summary
        print("\nUpdating summary sheet...")
        update_summary_sheet(service, spreadsheet_id, league_data)

        print("✓ Summary updated")

        # Verify skipped teams (teams not in affected list)
        skipped_teams = [
            team for team in league_data.teams
            if team.team_id not in affected_team_ids
        ]

        print(f"\n✓ Skipped {len(skipped_teams)} teams (no changes)")
        if len(skipped_teams) > 0:
            print(f"  Example skipped teams: {', '.join(t.team_name for t in skipped_teams[:3])}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_force_full_update(spreadsheet_id, league_data):
    """Test force full update (all teams regardless of transactions)."""
    print("\n" + "=" * 80)
    print("TEST 4: Force Full Update")
    print("=" * 80)

    try:
        service = get_google_sheets_service()

        print("Updating ALL teams (force full update)...")

        # Update all teams
        for i, team in enumerate(league_data.teams, 1):
            print(f"  [{i}/{len(league_data.teams)}] Updating: {team.team_name}")
            update_team_sheet(service, spreadsheet_id, team)

        print(f"✓ Updated all {len(league_data.teams)} teams")

        # Update summary
        print("\nUpdating summary sheet...")
        update_summary_sheet(service, spreadsheet_id, league_data)

        print("✓ Full update completed successfully")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timestamp_persistence(spreadsheet_id):
    """Test that timestamp persists across multiple reads."""
    print("\n" + "=" * 80)
    print("TEST 5: Timestamp Persistence")
    print("=" * 80)

    try:
        service = get_google_sheets_service()

        print("Reading timestamp multiple times...")

        timestamps = []
        for i in range(3):
            ts = read_last_run_timestamp(service, spreadsheet_id)
            if ts:
                timestamps.append(ts)
                print(f"  Read {i+1}: {ts.isoformat()}")
            else:
                print(f"  ✗ Read {i+1}: Failed")
                return False

            if i < 2:
                time.sleep(0.5)  # Small delay between reads

        # All timestamps should be identical
        if len(set(t.isoformat() for t in timestamps)) == 1:
            print("✓ Timestamp is persistent and consistent")
            return True
        else:
            print("✗ Failed: Timestamps are inconsistent")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all incremental update integration tests."""
    print("\n" + "=" * 80)
    print("INCREMENTAL UPDATE INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    print("This test suite validates the complete incremental update workflow:")
    print("  1. Creating spreadsheets with timestamps")
    print("  2. Updating when no transactions occurred")
    print("  3. Updating only affected teams when transactions occurred")
    print("  4. Force updating all teams")
    print("  5. Timestamp persistence")
    print()

    results = {}

    # Initialize Yahoo fetcher once for all tests
    try:
        print("Initializing Yahoo Data Fetcher...")
        fetcher = YahooDataFetcher(browser_callback=False)
        print("✓ Yahoo API initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize Yahoo API: {e}")
        return 1

    # Test 1: Create initial spreadsheet
    spreadsheet_id, league_data = test_create_initial_spreadsheet(fetcher)
    results["Create Initial Spreadsheet"] = (spreadsheet_id is not None)

    if not spreadsheet_id:
        print("\n✗ Cannot continue tests without valid spreadsheet")
        return 1

    # Wait a moment before next test
    print("\nWaiting 3 seconds before next test...")
    time.sleep(3)

    # Test 2: Update with no transactions
    results["Update With No Transactions"] = test_update_no_transactions(
        spreadsheet_id, fetcher, league_data
    )

    # Wait a moment before next test
    print("\nWaiting 2 seconds before next test...")
    time.sleep(2)

    # Test 3: Update with transactions
    results["Update With Transactions"] = test_update_with_transactions(
        spreadsheet_id, fetcher, league_data
    )

    # Wait a moment before next test
    print("\nWaiting 2 seconds before next test...")
    time.sleep(2)

    # Test 4: Force full update
    results["Force Full Update"] = test_force_full_update(
        spreadsheet_id, league_data
    )

    # Test 5: Timestamp persistence
    results["Timestamp Persistence"] = test_timestamp_persistence(
        spreadsheet_id
    )

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

    print("\n" + "=" * 80)
    print(f"Test Spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print("=" * 80)
    print()
    print("Manual verification steps:")
    print("1. Open the test spreadsheet URL above")
    print("2. Check Summary sheet for recent timestamp in F1:G1")
    print("3. Verify team sheets have current data")
    print("4. Check that formatting is preserved across updates")
    print()

    if passed == total:
        print("🎉 ALL INCREMENTAL UPDATE TESTS PASSED!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
