"""
Test sheet updater functionality.

This script tests the sheet updater module by:
1. Creating a new spreadsheet with current league data
2. Updating specific team sheets
3. Updating the summary sheet
4. Updating just the timestamp

This is an integration test that requires:
- Valid Yahoo OAuth credentials
- Valid Google OAuth credentials
- Network access to both APIs
"""

from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_generator import generate_league_report
from src.sheet_updater import (
    update_team_sheet,
    update_summary_sheet,
    update_timestamp
)
from src.google_auth import get_google_sheets_service
from src.logger import get_logger
import time

logger = get_logger(__name__)


def main():
    """Run the sheet updater test."""
    print("=" * 80)
    print("SHEET UPDATER TEST")
    print("=" * 80)
    print()

    # Step 1: Create a new spreadsheet
    print("STEP 1: Creating initial spreadsheet with league data...")
    print("-" * 80)
    try:
        fetcher = YahooDataFetcher(browser_callback=False)
        league_data = fetcher.extract_league_data()

        print(f"✓ League data extracted: {league_data.league_name}")
        print(f"  Teams: {league_data.num_teams}")
        print(f"  Total Players: {league_data.get_total_players()}")
        print()

        # Generate initial spreadsheet
        sheet_url = generate_league_report(league_data, sheet_title="Sheet Updater Test")
        spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]

        print(f"✓ Initial spreadsheet created")
        print(f"  URL: {sheet_url}")
        print(f"  ID: {spreadsheet_id}")
        print()

    except Exception as e:
        print(f"✗ Failed to create initial spreadsheet: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Test updating a single team sheet
    print("STEP 2: Testing team sheet update...")
    print("-" * 80)
    try:
        service = get_google_sheets_service()

        # Pick the first team to update
        test_team = sorted(league_data.teams, key=lambda t: t.team_name)[0]
        print(f"Updating sheet for: {test_team.team_name}")

        update_team_sheet(service, spreadsheet_id, test_team)

        print(f"✓ Team sheet updated successfully")
        print()

    except Exception as e:
        print(f"✗ Failed to update team sheet: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Test updating summary sheet
    print("STEP 3: Testing summary sheet update...")
    print("-" * 80)
    try:
        update_summary_sheet(service, spreadsheet_id, league_data)

        print(f"✓ Summary sheet updated successfully")
        print()

    except Exception as e:
        print(f"✗ Failed to update summary sheet: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Test timestamp-only update
    print("STEP 4: Testing timestamp-only update...")
    print("-" * 80)
    try:
        # Wait a moment so timestamp is different
        print("Waiting 2 seconds to ensure timestamp changes...")
        time.sleep(2)

        update_timestamp(service, spreadsheet_id)

        print(f"✓ Timestamp updated successfully")
        print()

    except Exception as e:
        print(f"✗ Failed to update timestamp: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Test updating multiple team sheets
    print("STEP 5: Testing batch team updates (3 teams)...")
    print("-" * 80)
    try:
        # Update the first 3 teams
        teams_to_update = sorted(league_data.teams, key=lambda t: t.team_name)[:3]

        for team in teams_to_update:
            print(f"  Updating: {team.team_name}")
            update_team_sheet(service, spreadsheet_id, team)

        print(f"✓ Batch team update successful")
        print()

    except Exception as e:
        print(f"✗ Failed to batch update teams: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Success!
    print("=" * 80)
    print("✓ ALL SHEET UPDATER TESTS PASSED!")
    print("=" * 80)
    print()
    print(f"Test spreadsheet URL: {sheet_url}")
    print()
    print("Verification steps:")
    print("1. Open the spreadsheet URL above")
    print("2. Check that timestamps in Summary sheet are recent")
    print("3. Check that updated team sheets have current data")
    print("4. Verify formatting is preserved")
    print()

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
