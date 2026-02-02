"""
Test team rename detection and handling.

This script tests the fix for the bug where teams that were renamed but had
no transactions would never get their sheets renamed.

Bug scenario:
- Team is renamed in Yahoo (e.g., "Mark's Young Ant Dick" -> "Hooked on Phonics")
- Team has no transactions since last update
- Before fix: Sheet kept old name forever
- After fix: Sheet is renamed even without transactions
"""

from unittest.mock import Mock, MagicMock, patch
from src.data_models import Team
from src.sheet_updater import (
    ensure_all_team_sheets_exist_and_renamed,
    _detect_team_rename
)
from src.logger import get_logger

logger = get_logger(__name__)


def test_detect_team_rename():
    """Test 1: Rename detection logic."""
    print("\n" + "=" * 80)
    print("TEST 1: Team rename detection")
    print("=" * 80)

    # Same name - no rename
    result = _detect_team_rename("Team Alpha", "Team Alpha")
    assert result is False, "Should not detect rename when names match"
    print("  ✓ Same name: no rename detected")

    # Different name - renamed
    result = _detect_team_rename("Old Name", "New Name")
    assert result is True, "Should detect rename when names differ"
    print("  ✓ Different name: rename detected")

    # Case sensitive
    result = _detect_team_rename("Team Alpha", "team alpha")
    assert result is True, "Should detect rename (case sensitive)"
    print("  ✓ Case sensitivity: rename detected")

    print("✓ Test 1 passed\n")


def test_ensure_all_team_sheets_handles_renames():
    """Test 2: Renamed teams get their sheets renamed even without transactions."""
    print("=" * 80)
    print("TEST 2: Handle team renames")
    print("=" * 80)

    # Mock service and spreadsheet ID
    mock_service = MagicMock()
    spreadsheet_id = "test_spreadsheet_id"

    # Create test teams
    team1 = Team(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="New Team Name",  # This team was renamed
        manager_name="Manager 1",
        roster=[],
        total_salary=100,
        faab_remaining=125,
        initial_budget=225
    )
    team2 = Team(
        team_id="2",
        team_key="466.l.68958.t.2",
        team_name="Unchanged Team",
        manager_name="Manager 2",
        roster=[],
        total_salary=150,
        faab_remaining=75,
        initial_budget=225
    )

    teams = [team1, team2]

    # Mock metadata cache (simulates existing sheets)
    metadata_cache = {
        "1": (123, "Old Team Name"),  # Sheet exists with old name
        "2": (456, "Unchanged Team")  # Sheet exists with correct name
    }

    # Mock the rename function
    with patch('src.sheet_updater._rename_sheet') as mock_rename:
        result = ensure_all_team_sheets_exist_and_renamed(
            mock_service, spreadsheet_id, teams, metadata_cache
        )

        # Should have renamed 1 sheet (team1)
        assert result['renamed'] == 1, f"Expected 1 rename, got {result['renamed']}"
        assert result['created'] == 0, f"Expected 0 created, got {result['created']}"
        assert result['migrated'] == 0, f"Expected 0 migrated, got {result['migrated']}"
        print("  ✓ Detected 1 renamed team")

        # Should have called _rename_sheet for team1
        mock_rename.assert_called_once_with(
            mock_service, spreadsheet_id, 123, "New Team Name"
        )
        print("  ✓ Rename function called with correct arguments")

    print("✓ Test 2 passed\n")


def test_ensure_all_team_sheets_creates_missing_sheets():
    """Test 3: Missing team sheets are created."""
    print("=" * 80)
    print("TEST 3: Create missing sheets")
    print("=" * 80)

    # Mock service and spreadsheet ID
    mock_service = MagicMock()
    spreadsheet_id = "test_spreadsheet_id"

    # Create test team
    team = Team(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="New Team",
        manager_name="Manager 1",
        roster=[],
        total_salary=100,
        faab_remaining=125,
        initial_budget=225
    )

    teams = [team]

    # Empty metadata cache (no sheets exist)
    metadata_cache = {}

    # Mock _find_sheet_id_by_name to return None (sheet doesn't exist)
    with patch('src.sheet_updater._find_sheet_id_by_name', return_value=None):
        with patch('src.sheet_updater.create_team_sheet') as mock_create:
            result = ensure_all_team_sheets_exist_and_renamed(
                mock_service, spreadsheet_id, teams, metadata_cache
            )

            # Should have created 1 sheet
            assert result['created'] == 1, f"Expected 1 created, got {result['created']}"
            assert result['renamed'] == 0, f"Expected 0 renamed, got {result['renamed']}"
            assert result['migrated'] == 0, f"Expected 0 migrated, got {result['migrated']}"
            print("  ✓ Created 1 missing sheet")

            # Should have called create_team_sheet
            mock_create.assert_called_once()
            print("  ✓ Create function called")

    print("✓ Test 3 passed\n")


def test_ensure_all_team_sheets_migrates_old_format():
    """Test 4: Old-format sheets (no team_id metadata) are migrated."""
    print("=" * 80)
    print("TEST 4: Migrate old-format sheets")
    print("=" * 80)

    # Mock service and spreadsheet ID
    mock_service = MagicMock()
    spreadsheet_id = "test_spreadsheet_id"

    # Create test team
    team = Team(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Team Alpha",
        manager_name="Manager 1",
        roster=[],
        total_salary=100,
        faab_remaining=125,
        initial_budget=225
    )

    teams = [team]

    # Empty metadata cache (sheet exists but has no team_id metadata)
    metadata_cache = {}

    # Mock _find_sheet_id_by_name to return a sheet_id (found by name)
    with patch('src.sheet_updater._find_sheet_id_by_name', return_value=789):
        with patch('src.sheet_updater._migrate_sheet_to_id_based') as mock_migrate:
            result = ensure_all_team_sheets_exist_and_renamed(
                mock_service, spreadsheet_id, teams, metadata_cache
            )

            # Should have migrated 1 sheet
            assert result['migrated'] == 1, f"Expected 1 migrated, got {result['migrated']}"
            assert result['created'] == 0, f"Expected 0 created, got {result['created']}"
            assert result['renamed'] == 0, f"Expected 0 renamed, got {result['renamed']}"
            print("  ✓ Migrated 1 old-format sheet")

            # Should have called _migrate_sheet_to_id_based
            mock_migrate.assert_called_once_with(
                mock_service, spreadsheet_id, 789, team
            )
            print("  ✓ Migration function called")

    print("✓ Test 4 passed\n")


def test_bug_scenario_renamed_team_no_transactions():
    """
    Test 5: The specific bug scenario.

    Bug scenario:
    - Team is renamed in Yahoo (e.g., "Mark's Young Ant Dick" -> "Hooked on Phonics")
    - Team has no transactions
    - Sheet should still be renamed

    This was the bug: teams without transactions never got their sheets renamed
    because update_team_sheet() was only called for teams in teams_to_update,
    which only included teams with recent transactions.
    """
    print("=" * 80)
    print("TEST 5: Bug scenario - renamed team with no transactions")
    print("=" * 80)

    # Mock service and spreadsheet ID
    mock_service = MagicMock()
    spreadsheet_id = "test_spreadsheet_id"

    # Create team with new name from Yahoo
    team = Team(
        team_id="14",
        team_key="466.l.68958.t.14",
        team_name="Hooked on Phonics",  # New name in Yahoo
        manager_name="Manager",
        roster=[],
        total_salary=143,
        faab_remaining=82,
        initial_budget=225
    )

    teams = [team]

    # Metadata cache shows sheet exists with old name
    metadata_cache = {
        "14": (1573287471, "Mark's Young Ant Dick")  # Old name in spreadsheet
    }

    # Mock the rename function
    with patch('src.sheet_updater._rename_sheet') as mock_rename:
        result = ensure_all_team_sheets_exist_and_renamed(
            mock_service, spreadsheet_id, teams, metadata_cache
        )

        # Should detect the rename and fix it
        assert result['renamed'] == 1, f"Expected 1 rename, got {result['renamed']}"
        print("  ✓ Detected rename despite no transactions")

        # Should rename from old name to new name
        mock_rename.assert_called_once_with(
            mock_service,
            spreadsheet_id,
            1573287471,  # sheet_id
            "Hooked on Phonics"  # new name
        )
        print("  ✓ Sheet renamed from 'Mark's Young Ant Dick' to 'Hooked on Phonics'")

    print("✓ Test 5 passed (bug fixed!)\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TEAM RENAME DETECTION TESTS")
    print("=" * 80)
    print("\nTesting fix for bug: teams renamed without transactions")
    print("Bug: Sheet names were not updated if team had no recent transactions")
    print("Fix: ensure_all_team_sheets_exist_and_renamed() checks all teams")

    try:
        test_detect_team_rename()
        test_ensure_all_team_sheets_handles_renames()
        test_ensure_all_team_sheets_creates_missing_sheets()
        test_ensure_all_team_sheets_migrates_old_format()
        test_bug_scenario_renamed_team_no_transactions()

        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  • Rename detection works correctly")
        print("  • Renamed teams get sheets updated even without transactions")
        print("  • Missing sheets are created automatically")
        print("  • Old-format sheets are migrated to ID-based tracking")
        print("  • Bug fix verified: 'Hooked on Phonics' rename scenario works")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    main()
