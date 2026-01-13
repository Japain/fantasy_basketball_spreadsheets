"""Google Sheets updater module.

This module provides functions to update existing Google Sheets rather than
creating new ones. It works in conjunction with sheet_generator.py to enable
incremental updates of team rosters and league statistics.

Key Features:
- Update individual team sheets with new roster data
- Update summary sheet with current league statistics
- Update timestamps to track last update time
- Preserve existing sheet structure and formatting
"""

from typing import Any, Optional, List
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.data_models import League, Team
from src.google_auth import get_google_sheets_service
from src.api_retry import api_call_with_retry
from src.sheet_generator import (
    _create_team_sheet_data,
    _create_team_sheet_formatting,
    _get_current_timestamp,
    _format_timestamp_for_display,
    create_team_sheet
)

logger = get_logger(__name__)


class SheetUpdateError(Exception):
    """Exception raised for sheet update errors."""
    pass


def _find_sheet_id_by_name(service: Any, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
    """
    Find the sheet ID for a sheet with the given name.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        sheet_name: The name of the sheet to find.

    Returns:
        Optional[int]: The sheet ID if found, None otherwise.

    Raises:
        SheetUpdateError: If API call fails.
    """
    try:
        # Get spreadsheet metadata with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name=f"find sheet by name '{sheet_name}'"
        )

        # Search for sheet by name
        sheets = spreadsheet.get('sheets', [])
        for sheet in sheets:
            properties = sheet.get('properties', {})
            if properties.get('title') == sheet_name:
                sheet_id = properties.get('sheetId')
                logger.debug(f"Found sheet '{sheet_name}' with ID: {sheet_id}")
                return sheet_id

        logger.debug(f"Sheet '{sheet_name}' not found in spreadsheet")
        return None

    except HttpError as e:
        error_msg = f"Failed to find sheet '{sheet_name}': {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def _build_sheet_metadata_cache(service: Any, spreadsheet_id: str) -> dict:
    """
    Build a cache of team_id to (sheet_id, sheet_title) mappings using batch read.

    Uses values().batchGet() to read all A1 cells in a SINGLE API call instead of
    reading each sheet individually. This is critical for staying within Google's
    60 reads/minute quota limit.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.

    Returns:
        dict: Mapping of team_id (str) to tuple of (sheet_id, sheet_title).
              Example: {"1": (123456, "Team Name"), "2": (789012, "Another Team")}
              Sheets without valid team_id metadata are excluded.

    Raises:
        SheetUpdateError: If API call fails.

    Performance:
        - Before (v2.4): 1 + N API calls (1 for sheet list, N for individual reads)
        - After (v2.5): 1 + 1 API calls (1 for sheet list, 1 batch read)
        - For 16 teams: 17 → 2 API calls (88% reduction)
    """
    try:
        # Get all sheets in the spreadsheet with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="build sheet metadata cache"
        )

        sheets = spreadsheet.get('sheets', [])

        # Build list of ranges to batch read and track sheet info
        ranges = []
        sheet_info = []  # List of (sheet_id, sheet_title) tuples

        for sheet in sheets:
            properties = sheet.get('properties', {})
            sheet_id = properties.get('sheetId')
            sheet_title = properties.get('title')

            # Skip Summary sheet
            if sheet_title == 'Summary':
                continue

            ranges.append(f"'{sheet_title}'!A1")
            sheet_info.append((sheet_id, sheet_title))

        # Handle empty case (no team sheets)
        if not ranges:
            logger.debug("No team sheets found (only Summary sheet)")
            return {}

        # Batch read all A1 cells in a SINGLE API call
        logger.debug(f"Batch reading {len(ranges)} sheet(s) metadata in 1 API call")
        result = api_call_with_retry(
            lambda: service.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id,
                ranges=ranges
            ).execute(),
            operation_name="batch read sheet metadata"
        )

        # Process batch results
        metadata_cache = {}
        value_ranges = result.get('valueRanges', [])

        for i, value_range in enumerate(value_ranges):
            sheet_id, sheet_title = sheet_info[i]
            values = value_range.get('values', [])

            if values and values[0]:
                cell_value = str(values[0][0])

                # Check if cell contains team_id metadata
                if cell_value.startswith('TEAM_ID:'):
                    team_id = cell_value.split(':', 1)[1].strip()
                    metadata_cache[team_id] = (sheet_id, sheet_title)
                    logger.debug(f"Cached metadata: team_id={team_id}, sheet='{sheet_title}' (ID: {sheet_id})")
                else:
                    logger.debug(f"Sheet '{sheet_title}' has no team_id metadata in A1")
            else:
                logger.debug(f"Sheet '{sheet_title}' has empty cell A1")

        logger.debug(f"Built metadata cache with {len(metadata_cache)} entries using batch read")
        return metadata_cache

    except HttpError as e:
        error_msg = f"Failed to build sheet metadata cache: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def _build_sheet_metadata_cache_legacy(service: Any, spreadsheet_id: str) -> dict:
    """
    LEGACY: Build metadata cache using individual reads (kept for rollback).

    This is the original implementation that reads each sheet's A1 cell individually.
    Kept for backwards compatibility and rollback if batch read causes issues.

    ⚠️ WARNING: Makes N+1 API calls (1 for sheet list + N individual reads).
    Use _build_sheet_metadata_cache() instead for production.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.

    Returns:
        dict: Mapping of team_id (str) to tuple of (sheet_id, sheet_title).

    Raises:
        SheetUpdateError: If API call fails.
    """
    try:
        # Get all sheets in the spreadsheet with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="build sheet metadata cache"
        )

        sheets = spreadsheet.get('sheets', [])
        metadata_cache = {}

        for sheet in sheets:
            properties = sheet.get('properties', {})
            sheet_id = properties.get('sheetId')
            sheet_title = properties.get('title')

            # Skip Summary sheet
            if sheet_title == 'Summary':
                continue

            # Read cell A1 to get team_id metadata with retry logic
            try:
                result = api_call_with_retry(
                    lambda: service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range=f"'{sheet_title}'!A1"
                    ).execute(),
                    operation_name=f"read metadata from '{sheet_title}'"
                )

                values = result.get('values', [])
                if values and values[0]:
                    cell_value = str(values[0][0])

                    # Check if cell contains team_id metadata
                    if cell_value.startswith('TEAM_ID:'):
                        team_id = cell_value.split(':', 1)[1].strip()
                        metadata_cache[team_id] = (sheet_id, sheet_title)
                        logger.debug(f"Cached metadata: team_id={team_id}, sheet='{sheet_title}' (ID: {sheet_id})")
                    else:
                        logger.debug(f"Sheet '{sheet_title}' has no team_id metadata in A1")
                else:
                    logger.debug(f"Sheet '{sheet_title}' has empty cell A1")

            except HttpError as e:
                # Non-critical error - log and continue
                logger.warning(f"Could not read metadata from sheet '{sheet_title}': {e}")
                continue

        logger.debug(f"Built metadata cache with {len(metadata_cache)} entries (legacy mode)")
        return metadata_cache

    except HttpError as e:
        error_msg = f"Failed to build sheet metadata cache: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def _find_sheet_by_team_id(service: Any, spreadsheet_id: str, team_id: str) -> Optional[tuple]:
    """
    Find a sheet by its team_id metadata stored in cell A1.

    This is the primary method for identifying team sheets, replacing name-based
    lookups which fail when teams are renamed.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        team_id: The Yahoo team ID to search for.

    Returns:
        Optional[tuple]: (sheet_id, sheet_title) if found, None otherwise.

    Raises:
        SheetUpdateError: If API call fails.
    """
    try:
        # Build metadata cache for all sheets
        metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)

        # Lookup by team_id
        if team_id in metadata_cache:
            sheet_id, sheet_title = metadata_cache[team_id]
            logger.debug(f"Found sheet by team_id={team_id}: '{sheet_title}' (ID: {sheet_id})")
            return (sheet_id, sheet_title)

        logger.debug(f"No sheet found for team_id={team_id}")
        return None

    except SheetUpdateError:
        # Re-raise SheetUpdateError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to find sheet by team_id={team_id}: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def _detect_team_rename(current_sheet_title: str, current_team_name: str) -> bool:
    """
    Detect if a team has been renamed by comparing sheet title with current name.

    Args:
        current_sheet_title: The current title of the sheet in Google Sheets.
        current_team_name: The current team name from Yahoo API.

    Returns:
        bool: True if team was renamed (names don't match), False otherwise.
    """
    # Simple string comparison - if they don't match, team was renamed
    return current_sheet_title != current_team_name


def _rename_sheet(service: Any, spreadsheet_id: str, sheet_id: int, new_title: str) -> None:
    """
    Rename a sheet to match the current team name.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        sheet_id: The sheet ID to rename.
        new_title: The new title for the sheet.

    Raises:
        SheetUpdateError: If rename fails (non-critical - logged but doesn't stop update).
    """
    try:
        # Truncate title to Google Sheets 100-character limit
        truncated_title = new_title[:100]

        # Create rename request
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'title': truncated_title
                },
                'fields': 'title'
            }
        }]

        # Execute rename
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        logger.info(f"✓ Renamed sheet (ID: {sheet_id}) to: '{truncated_title}'")

    except HttpError as e:
        # Log error but don't fail the update - rename is cosmetic
        error_msg = f"Failed to rename sheet (ID: {sheet_id}) to '{new_title}': {e}"
        logger.error(error_msg)
        # Don't raise - allow update to continue


def _migrate_sheet_to_id_based(service: Any, spreadsheet_id: str, sheet_id: int, team: Team) -> None:
    """
    Migrate an existing sheet to ID-based tracking by adding team_id metadata to cell A1.

    This function handles backwards compatibility with sheets created before the
    team_id metadata feature was added. It reads existing data, inserts the team_id
    in column A, writes back the data, and applies invisible formatting to A1.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        sheet_id: The sheet ID to migrate.
        team: Team object with team_id and team_name.

    Raises:
        SheetUpdateError: If migration fails.
    """
    try:
        logger.info(f"Migrating sheet '{team.team_name}' (team_id={team.team_id}) to ID-based tracking...")

        # Read existing data from the sheet
        sheet_name = team.team_name[:100]  # Use truncated name for range
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1:Z1000"
        ).execute()

        existing_data = result.get('values', [])

        if not existing_data:
            logger.warning(f"Sheet '{sheet_name}' has no data to migrate")
            return

        # Insert team_id metadata in column A of first row
        if len(existing_data) > 0:
            existing_data[0].insert(0, f"TEAM_ID:{team.team_id}")
        else:
            existing_data.append([f"TEAM_ID:{team.team_id}"])

        # Write back the data with metadata
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': existing_data}
        ).execute()

        # Apply invisible formatting to A1 (white text on white background)
        format_request = {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                            'fontSize': 1
                        },
                        'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [format_request]}
        ).execute()

        logger.info(f"✓ Migration complete for '{team.team_name}' (team_id={team.team_id})")

    except Exception as e:
        error_msg = f"Failed to migrate sheet for team {team.team_name} (team_id={team.team_id}): {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def cleanup_orphaned_sheets(service: Any, spreadsheet_id: str, current_team_ids: set, current_team_names: set, metadata_cache: dict = None) -> int:
    """
    Identify and delete sheets for teams that no longer exist in the league.

    Orphaned sheets occur when teams are renamed (old sheet remains) or removed
    from the league. This function safely identifies true orphans:
    1. Sheets with team_id metadata not matching current team IDs (removed teams)
    2. Duplicate sheets where the current team name already has a sheet (rename leftovers)

    IMPORTANT: Only deletes sheets when we're certain they're orphaned. Does NOT
    delete old-format sheets if they might be the only sheet for a current team.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        current_team_ids: Set of team IDs currently in the league.
        current_team_names: Set of team names currently in the league.
        metadata_cache: Optional pre-built metadata cache from _build_sheet_metadata_cache().
                       If provided, avoids redundant API calls to read cell A1 data.
                       If None, will build cache internally.

    Returns:
        int: Number of sheets deleted.

    Raises:
        SheetUpdateError: If cleanup fails (non-critical - logged but doesn't stop update).
    """
    try:
        # Use provided metadata cache or build it if not provided
        if metadata_cache is None:
            logger.debug("No metadata cache provided, building cache...")
            metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)
        else:
            logger.debug("Using provided metadata cache (avoiding redundant API calls)")

        # Get all sheets in the spreadsheet with retry logic
        spreadsheet = api_call_with_retry(
            lambda: service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute(),
            operation_name="cleanup orphaned sheets"
        )
        sheets = spreadsheet.get('sheets', [])

        # Build sets of sheets with/without metadata using the cache
        sheets_with_metadata = metadata_cache.copy()  # team_id -> (sheet_id, sheet_title)
        sheets_without_metadata = []  # [(sheet_id, sheet_title)]
        sheets_by_name = {}  # sheet_title -> (sheet_id, has_metadata)

        # Build reverse lookup and identify sheets without metadata
        for team_id, (sheet_id, sheet_title) in sheets_with_metadata.items():
            sheets_by_name[sheet_title] = (sheet_id, True)

        # Identify sheets that are NOT in the metadata cache (old format or no team_id)
        for sheet in sheets:
            properties = sheet.get('properties', {})
            sheet_id = properties.get('sheetId')
            sheet_title = properties.get('title')

            # Skip Summary sheet
            if sheet_title == 'Summary':
                continue

            # If sheet is not in metadata cache, it's an old-format sheet
            if sheet_title not in sheets_by_name:
                sheets_without_metadata.append((sheet_id, sheet_title))
                sheets_by_name[sheet_title] = (sheet_id, False)
                logger.debug(f"Found sheet without metadata: '{sheet_title}'")

        orphaned_sheets = []

        # Rule 1: Sheets with metadata for teams not in current league (removed teams)
        for team_id, (sheet_id, sheet_title) in sheets_with_metadata.items():
            if team_id not in current_team_ids:
                orphaned_sheets.append((sheet_id, sheet_title, f"removed team (team_id={team_id})"))
                logger.debug(f"Identified orphan: '{sheet_title}' - team_id={team_id} not in league")

        # Rule 2: Old-format sheets that are DUPLICATES of current team names
        # Only delete if the current team name already has a sheet (meaning this is a leftover)
        for sheet_id, sheet_title in sheets_without_metadata:
            # Check if this sheet name doesn't match any current team
            if sheet_title not in current_team_names:
                # Check if ANY current team already has a sheet with metadata
                # If all current teams have metadata sheets, this old sheet is truly orphaned
                # But if some current teams are missing sheets, this might be one of them

                # Count how many current teams already have sheets
                teams_with_sheets = len(sheets_with_metadata)
                teams_without_sheets = len(current_team_ids) - teams_with_sheets

                if teams_without_sheets == 0:
                    # All teams have sheets with metadata, so this is truly orphaned
                    orphaned_sheets.append((sheet_id, sheet_title, "old format, all teams accounted for"))
                    logger.debug(f"Identified orphan: '{sheet_title}' - old format and all teams have sheets")
                else:
                    # Some teams don't have sheets yet, so this might be one of them (renamed)
                    # Don't delete it - it will be migrated
                    logger.debug(f"Keeping '{sheet_title}' - might be renamed sheet for team without sheet yet")

        if not orphaned_sheets:
            logger.debug("No orphaned sheets found")
            return 0

        # Print user-friendly summary before deletion
        print(f"→ Found {len(orphaned_sheets)} orphaned sheet(s) from removed teams:")
        for _, sheet_title, reason in orphaned_sheets:
            print(f"  • {sheet_title} ({reason})")
        print("  Deleting orphaned sheets...")

        # Create batch delete requests
        delete_requests = []
        for sheet_id, sheet_title, reason in orphaned_sheets:
            delete_requests.append({
                'deleteSheet': {'sheetId': sheet_id}
            })
            logger.info(f"Deleting orphaned sheet: '{sheet_title}' ({reason}, sheet_id={sheet_id})")

        # Execute batch deletion
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': delete_requests}
        ).execute()

        logger.info(f"✓ Deleted {len(orphaned_sheets)} orphaned sheet(s)")
        return len(orphaned_sheets)

    except Exception as e:
        error_msg = f"Failed to cleanup orphaned sheets: {e}"
        logger.error(error_msg)
        # Log error but don't raise - cleanup is non-critical
        return 0


def update_team_sheet(service: Any, spreadsheet_id: str, team: Team) -> None:
    """
    Update an existing team sheet with new roster data.

    If the sheet doesn't exist (e.g., new team added to league), it will be created.
    The update process:
    1. Find the sheet by team_id (primary) or team name (backwards compatibility)
    2. Detect and handle team renames
    3. If not found, create a new sheet
    4. Clear existing data
    5. Write new data
    6. Apply formatting

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        team: Team object with current roster data.

    Raises:
        SheetUpdateError: If update fails.
    """
    logger.info(f"Updating sheet for team: {team.team_name} (team_id={team.team_id})")

    try:
        # Try to find sheet by team_id (ID-based lookup)
        result = _find_sheet_by_team_id(service, spreadsheet_id, team.team_id)

        if result is None:
            # Backwards compatibility: fallback to name-based lookup
            logger.debug(f"No sheet found by team_id={team.team_id}, trying name-based lookup...")
            sheet_id = _find_sheet_id_by_name(service, spreadsheet_id, team.team_name)

            if sheet_id is not None:
                # Found by name - migrate to ID-based tracking
                logger.info(f"Migrating sheet '{team.team_name}' to ID-based tracking...")
                _migrate_sheet_to_id_based(service, spreadsheet_id, sheet_id, team)
                sheet_title = team.team_name
            else:
                # Sheet doesn't exist - create new one
                logger.info(f"Sheet for '{team.team_name}' (team_id={team.team_id}) not found. Creating new sheet...")
                create_team_sheet(service, spreadsheet_id, team)
                logger.info(f"✓ Created new sheet for: {team.team_name}")
                return
        else:
            # Found by team_id
            sheet_id, sheet_title = result
            logger.debug(f"Found sheet by team_id={team.team_id}: '{sheet_title}' (sheet_id={sheet_id})")

            # Check if team was renamed
            if _detect_team_rename(sheet_title, team.team_name):
                logger.info(f"Team renamed: '{sheet_title}' → '{team.team_name}' (team_id={team.team_id})")
                _rename_sheet(service, spreadsheet_id, sheet_id, team.team_name)
                sheet_title = team.team_name  # Update for subsequent operations

        # Clear existing data in the sheet
        # Use current sheet_title for range (might be old name if rename failed, but that's okay)
        clear_range = f"'{sheet_title}'!A1:Z1000"
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=clear_range
        ).execute()
        logger.debug(f"Cleared existing data in '{sheet_title}'")

        # Generate new data (includes team_id metadata)
        values = _create_team_sheet_data(team)

        # Write new data to the sheet
        # Note: If rename succeeded, use new name; if failed, use old name
        range_name = f"'{sheet_title}'!A1"
        body = {'values': values}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        logger.debug(f"Wrote new data to '{sheet_title}'")

        # Apply formatting
        num_players = len(team.roster)
        format_requests = _create_team_sheet_formatting(sheet_id, num_players)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': format_requests}
        ).execute()
        logger.debug(f"Applied formatting to '{sheet_title}'")

        logger.info(f"✓ Updated sheet for: {team.team_name} ({num_players} players, ${team.total_salary})")

    except Exception as e:
        error_msg = f"Failed to update team sheet for {team.team_name} (team_id={team.team_id}): {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def update_summary_sheet(service: Any, spreadsheet_id: str, league: League) -> None:
    """
    Update the Summary sheet with current league statistics and timestamp.

    The update process:
    1. Find the Summary sheet (should always exist)
    2. Clear existing data
    3. Generate new summary data with updated statistics and timestamp
    4. Write new data

    Note: Formatting is preserved from original sheet creation, so we don't
    need to reapply it.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        league: League object with current team and player data.

    Raises:
        SheetUpdateError: If update fails.
    """
    logger.info("Updating Summary sheet...")

    try:
        # Get current timestamp
        current_timestamp = _get_current_timestamp()
        human_readable_timestamp = _format_timestamp_for_display(current_timestamp)

        # Calculate league statistics
        stats = league.get_league_stats()
        avg_player_salary = stats['total_salary_spent'] / stats['total_players'] if stats['total_players'] > 0 else 0

        # Prepare summary data with updated timestamp
        values = [
            [f"{league.league_name} - League Summary", "", "", "", "", "Last Updated (Timestamp)", current_timestamp],
            [],
            ["League Information"],
            ["Season", league.season],
            ["Number of Teams", league.num_teams],
            ["Total Players", stats['total_players']],
            ["Average Roster Size", f"{stats['avg_roster_size']:.1f}"],
            ["Last Updated", human_readable_timestamp],
            [],
            ["Salary Information"],
            ["Total Salary Spent", f"${stats['total_salary_spent']}"],
            ["Average Team Salary", f"${stats['avg_salary_per_team']:.2f}"],
            ["Average Player Salary", f"${avg_player_salary:.2f}"],
            [],
            ["FAAB Information"],
            ["Total FAAB Remaining", f"${stats['total_faab_remaining']}"],
            ["Average FAAB Remaining", f"${stats['avg_faab_remaining']:.2f}"],
            [],
            [],
            ["Team Summary"],
            ["Team Name", "Manager", "Players", "Total Salary", "Remaining Salary", "FAAB Remaining"],
        ]

        # Add team rows sorted by name
        for team in sorted(league.teams, key=lambda t: t.team_name):
            values.append([
                team.team_name,
                team.manager_name,
                len(team.roster),
                f"${team.total_salary}",
                f"${team.get_remaining_salary()}",
                f"${team.faab_remaining}"
            ])

        # Clear existing data and write new data
        # Note: We don't clear formatting, just values
        clear_range = "Summary!A1:Z1000"
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=clear_range
        ).execute()
        logger.debug("Cleared existing Summary sheet data")

        # Write new data
        body = {'values': values}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Summary!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        logger.info(f"✓ Summary sheet updated (Timestamp: {human_readable_timestamp})")

    except Exception as e:
        error_msg = f"Failed to update summary sheet: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e


def update_timestamp(service: Any, spreadsheet_id: str) -> None:
    """
    Update only the timestamp in the Summary sheet.

    This is a lightweight update that only changes:
    - Cell G1: Machine-readable ISO 8601 timestamp
    - Cell B8: Human-readable timestamp in League Information section

    Use this when you want to mark the sheet as updated without regenerating
    all the data (e.g., when no data changed but you want to track last check time).

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.

    Raises:
        SheetUpdateError: If update fails.
    """
    logger.info("Updating timestamp in Summary sheet...")

    try:
        # Get current timestamp
        current_timestamp = _get_current_timestamp()
        human_readable_timestamp = _format_timestamp_for_display(current_timestamp)

        # Update both timestamp locations
        # G1: Machine-readable timestamp
        # B8: Human-readable timestamp
        data = [
            {
                'range': 'Summary!G1',
                'values': [[current_timestamp]]
            },
            {
                'range': 'Summary!B8',
                'values': [[human_readable_timestamp]]
            }
        ]

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

        logger.info(f"✓ Timestamp updated: {human_readable_timestamp}")

    except Exception as e:
        error_msg = f"Failed to update timestamp: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e
