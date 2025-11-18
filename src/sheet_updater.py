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
        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

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


def update_team_sheet(service: Any, spreadsheet_id: str, team: Team) -> None:
    """
    Update an existing team sheet with new roster data.

    If the sheet doesn't exist (e.g., new team added to league), it will be created.
    The update process:
    1. Find the sheet by team name
    2. If not found, create a new sheet
    3. Clear existing data
    4. Write new data
    5. Apply formatting

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        team: Team object with current roster data.

    Raises:
        SheetUpdateError: If update fails.
    """
    logger.info(f"Updating sheet for team: {team.team_name}")

    try:
        # Find the sheet by team name
        sheet_id = _find_sheet_id_by_name(service, spreadsheet_id, team.team_name)

        # If sheet doesn't exist, create it
        if sheet_id is None:
            logger.info(f"Sheet for '{team.team_name}' not found. Creating new sheet...")
            create_team_sheet(service, spreadsheet_id, team)
            logger.info(f"✓ Created new sheet for: {team.team_name}")
            return

        # Clear existing data in the sheet
        clear_range = f"'{team.team_name}'!A1:Z1000"
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=clear_range
        ).execute()
        logger.debug(f"Cleared existing data in '{team.team_name}'")

        # Generate new data
        values = _create_team_sheet_data(team)

        # Write new data to the sheet
        range_name = f"'{team.team_name}'!A1"
        body = {'values': values}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        logger.debug(f"Wrote new data to '{team.team_name}'")

        # Apply formatting
        num_players = len(team.roster)
        format_requests = _create_team_sheet_formatting(sheet_id, num_players)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': format_requests}
        ).execute()
        logger.debug(f"Applied formatting to '{team.team_name}'")

        logger.info(f"✓ Updated sheet for: {team.team_name} ({num_players} players, ${team.total_salary})")

    except Exception as e:
        error_msg = f"Failed to update team sheet for {team.team_name}: {e}"
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
