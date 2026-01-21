"""Google Sheets generation module.

This module provides functions to create and format Google Sheets with league data,
including team rosters, player information, and salary details.
"""

from typing import List, Optional, Any
from datetime import datetime, timezone
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.data_models import League, Team, Player
from src.google_auth import get_google_sheets_service
from config import Config

logger = get_logger(__name__)


class SheetGenerationError(Exception):
    """Exception raised for sheet generation errors."""
    pass


def _create_sheet_protection_request(sheet_id: int, sheet_name: str, owner_email: str) -> dict:
    """
    Create a request to protect a sheet with owner-only edit access.

    Args:
        sheet_id: The Google Sheets sheet ID to protect.
        sheet_name: The name of the sheet (for warning message).
        owner_email: Email address of the owner who can edit (e.g., "user@gmail.com").

    Returns:
        dict: Protection request for batchUpdate API.
    """
    return {
        'addProtectedRange': {
            'protectedRange': {
                'range': {
                    'sheetId': sheet_id
                },
                'description': f'Protected sheet: {sheet_name}',
                'warningOnly': False,
                'editors': {
                    'users': [owner_email]
                }
            }
        }
    }


def _get_current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.

    Returns:
        str: Current timestamp in ISO 8601 format (e.g., "2025-11-15T10:30:00Z")
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_timestamp_for_display(timestamp: str) -> str:
    """
    Format ISO 8601 timestamp for human-readable display.

    Args:
        timestamp: ISO 8601 timestamp string (e.g., "2025-11-15T10:30:00Z")

    Returns:
        str: Human-readable timestamp (e.g., "November 15, 2025 at 10:30 AM UTC")
             Returns original string if parsing fails.
    """
    try:
        # Parse ISO 8601 timestamp
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        # Format as human-readable string
        return dt.strftime("%B %d, %Y at %I:%M %p UTC")
    except ValueError as e:
        logger.warning(f"Failed to parse timestamp '{timestamp}': {e}")
        return timestamp


def create_spreadsheet(title: str) -> tuple[Any, str]:
    """
    Create a new Google Sheet with the specified title.

    Args:
        title: The title for the new spreadsheet.

    Returns:
        tuple: (service object, spreadsheet_id)

    Raises:
        SheetGenerationError: If spreadsheet creation fails.
    """
    logger.info(f"Creating Google Sheet: '{title}'")

    try:
        service = get_google_sheets_service()

        # Create the spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            }
        }

        spreadsheet = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()

        spreadsheet_id = spreadsheet.get('spreadsheetId')

        logger.info(f"✓ Spreadsheet created successfully. ID: {spreadsheet_id}")
        logger.info(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

        return service, spreadsheet_id

    except HttpError as e:
        error_msg = f"Failed to create spreadsheet: {e}"
        logger.error(error_msg)
        raise SheetGenerationError(error_msg) from e


def create_summary_sheet(service: Any, spreadsheet_id: str, league: League) -> None:
    """
    Create a summary sheet with league-wide statistics.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        league: League object with all team and player data.

    Raises:
        SheetGenerationError: If sheet creation fails.
    """
    logger.info("Creating summary sheet...")

    try:
        stats = league.get_league_stats()
        avg_player_salary = stats['total_salary_spent'] / stats['total_players'] if stats['total_players'] > 0 else 0

        # Get current timestamp
        current_timestamp = _get_current_timestamp()
        human_readable_timestamp = _format_timestamp_for_display(current_timestamp)

        # Prepare data for the summary sheet
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

        # Update the default "Sheet1" with summary data
        body = {
            'values': values
        }

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        # Format the summary sheet
        requests = [
            # Rename Sheet1 to Summary
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'title': 'Summary'
                    },
                    'fields': 'title'
                }
            },
            # Format title (row 1, columns A-E)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 14
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
                }
            },
            # Format timestamp label (F1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 5,
                        'endColumnIndex': 6
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 9,
                                'italic': True
                            },
                            'horizontalAlignment': 'RIGHT',
                            'backgroundColor': {
                                'red': 0.95,
                                'green': 0.95,
                                'blue': 0.95
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment,backgroundColor)'
                }
            },
            # Format timestamp value (G1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 6,
                        'endColumnIndex': 7
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'fontSize': 9,
                                'italic': True
                            },
                            'horizontalAlignment': 'LEFT',
                            'backgroundColor': {
                                'red': 0.95,
                                'green': 0.95,
                                'blue': 0.95
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment,backgroundColor)'
                }
            },
            # Format "League Information" header (row 3, index 2)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 2,
                        'endRowIndex': 3
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Format "Salary Information" header (row 10, index 9)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 9,
                        'endRowIndex': 10
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Format "FAAB Information" header (row 15, index 14)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 14,
                        'endRowIndex': 15
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Format "Team Summary" header (row 20, index 19)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 19,
                        'endRowIndex': 20
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Format team table header with column names (row 21, index 20)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 20,
                        'endRowIndex': 21
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.4,
                                'blue': 0.7
                            },
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                },
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Auto-resize columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 6
                    }
                }
            },
            # Conditional formatting for Remaining Salary column (green if > 0)
            {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': 0,
                            'startRowIndex': 21,  # Team data starts at row 22 (index 21)
                            'endRowIndex': 21 + league.num_teams,
                            'startColumnIndex': 4,  # Column E (Remaining Salary)
                            'endColumnIndex': 5
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'NUMBER_GREATER',
                                'values': [{'userEnteredValue': '0'}]
                            },
                            'format': {
                                'backgroundColor': {
                                    'red': 0.7,
                                    'green': 0.9,
                                    'blue': 0.7
                                }
                            }
                        }
                    },
                    'index': 0
                }
            },
            # Conditional formatting for Remaining Salary column (red if <= 0)
            {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': 0,
                            'startRowIndex': 21,  # Team data starts at row 22 (index 21)
                            'endRowIndex': 21 + league.num_teams,
                            'startColumnIndex': 4,  # Column E (Remaining Salary)
                            'endColumnIndex': 5
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'NUMBER_LESS_THAN_EQ',
                                'values': [{'userEnteredValue': '0'}]
                            },
                            'format': {
                                'backgroundColor': {
                                    'red': 0.95,
                                    'green': 0.7,
                                    'blue': 0.7
                                }
                            }
                        }
                    },
                    'index': 1
                }
            }
        ]

        # Add protection if owner email is configured
        if Config.OWNER_EMAIL:
            logger.debug(f"Adding protection to Summary sheet (owner: {Config.OWNER_EMAIL})")
            requests.append(_create_sheet_protection_request(0, 'Summary', Config.OWNER_EMAIL))

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        logger.info("✓ Summary sheet created and formatted")

    except Exception as e:
        error_msg = f"Failed to create summary sheet: {e}"
        logger.error(error_msg)
        raise SheetGenerationError(error_msg) from e


def _get_team_id_cell_formatting(sheet_id: int) -> dict:
    """
    Create formatting request for team_id metadata cell (A1).

    Makes the cell invisible by applying white text on white background with 1pt font.
    This allows us to store team_id metadata without it being visible to users.

    Args:
        sheet_id: The Google Sheets sheet ID.

    Returns:
        dict: Formatting request for batchUpdate to make cell A1 invisible.
    """
    return {
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


def _create_team_sheet_data(team: Team) -> List[List[Any]]:
    """
    Create the data array for a team sheet.

    Args:
        team: Team object with roster data.

    Returns:
        List[List[Any]]: 2D array of values for the team sheet, including:
            - Title row with team_id metadata (invisible) and team name/manager
            - Blank row
            - Header row with column names
            - Player rows (sorted by salary, descending)
            - Blank row
            - Summary rows (total salary, remaining salary, FAAB)
    """
    # Prepare roster data with team_id metadata in column A
    # Row 1: Team_id (A1) and team name (B1)
    values = [
        [f"TEAM_ID:{team.team_id}", f"{team.team_name} ({team.manager_name})"],
        [""],  # Row 2: Empty cell in A2 to maintain alignment
        ["", "Player Name", "Position", "Slot", "Salary", "Source"],  # Row 3: Empty A3, then headers in B-F
    ]

    # Sort roster by salary (descending)
    sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

    # Add player rows (empty cell in column A to maintain alignment)
    for player in sorted_roster:
        source_text = player.source.name.replace('_', ' ')
        values.append([
            "",  # Empty cell in column A
            player.name,
            player.position,
            player.roster_position or "",
            player.salary,
            source_text
        ])

    # Add summary rows (empty cell in column A to maintain alignment)
    values.append([""])  # Blank row
    values.append(["", "TOTAL SALARY", "", "", team.total_salary, ""])
    values.append(["", "REMAINING SALARY", "", "", team.get_remaining_salary(), ""])
    values.append(["", "FAAB REMAINING", "", "", team.faab_remaining, ""])

    return values


def _create_team_sheet_formatting(sheet_id: int, num_players: int) -> List[dict]:
    """
    Create formatting requests for a team sheet.

    Args:
        sheet_id: The Google Sheets sheet ID for this team sheet.
        num_players: The number of players on the team roster.

    Returns:
        List[dict]: List of formatting requests for batchUpdate, including:
            - Team_id metadata cell invisible formatting (A1)
            - Title formatting (row 1, column B)
            - Header row formatting (row 3)
            - Salary column currency formatting
            - Summary rows formatting
            - Column auto-resize
            - Frozen header rows
            - Conditional formatting for remaining salary
    """
    summary_row = num_players + 4  # Header + blank + table header + players + blank

    format_requests = [
        # Format team_id metadata cell (A1) - make it invisible
        _get_team_id_cell_formatting(sheet_id),

        # Format title (row 1, column B onwards)
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 1  # Start from column B (skip A which has team_id)
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 12
                        },
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
            }
        },
        # Format table header (row 3)
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 2,
                    'endRowIndex': 3
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.4,
                            'blue': 0.7
                        },
                        'textFormat': {
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            },
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        },
        # Format salary column as currency (column E, index 4)
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 3,
                    'endRowIndex': 3 + num_players,
                    'startColumnIndex': 4,  # Column E (was D before adding team_id column)
                    'endColumnIndex': 5
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'CURRENCY',
                            'pattern': '$#,##0'
                        }
                    }
                },
                'fields': 'userEnteredFormat(numberFormat)'
            }
        },
        # Format summary rows (bold)
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': summary_row,
                    'endRowIndex': summary_row + 3
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {
                            'red': 0.95,
                            'green': 0.95,
                            'blue': 0.95
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        },
        # Format summary salary values as currency (column E, index 4)
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': summary_row,
                    'endRowIndex': summary_row + 3,
                    'startColumnIndex': 4,  # Column E (was D before adding team_id column)
                    'endColumnIndex': 5
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'CURRENCY',
                            'pattern': '$#,##0'
                        }
                    }
                },
                'fields': 'userEnteredFormat(numberFormat)'
            }
        },
        # Auto-resize columns (now includes column A for team_id)
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6  # Now 6 columns (A-F) instead of 5
                }
            }
        },
        # Freeze header row
        {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 3
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        },
        # Conditional formatting for REMAINING SALARY (green if > 0)
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': sheet_id,
                        'startRowIndex': summary_row + 1,  # REMAINING SALARY row
                        'endRowIndex': summary_row + 2,
                        'startColumnIndex': 4,  # Column E (value column, was D before team_id)
                        'endColumnIndex': 5
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'NUMBER_GREATER',
                            'values': [{'userEnteredValue': '0'}]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 0.7,
                                'green': 0.9,
                                'blue': 0.7
                            }
                        }
                    }
                },
                'index': 0
            }
        },
        # Conditional formatting for REMAINING SALARY (red if <= 0)
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': sheet_id,
                        'startRowIndex': summary_row + 1,  # REMAINING SALARY row
                        'endRowIndex': summary_row + 2,
                        'startColumnIndex': 4,  # Column E (value column, was D before team_id)
                        'endColumnIndex': 5
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'NUMBER_LESS_THAN_EQ',
                            'values': [{'userEnteredValue': '0'}]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 0.95,
                                'green': 0.7,
                                'blue': 0.7
                            }
                        }
                    }
                },
                'index': 1
            }
        }
    ]

    return format_requests


def create_draft_picks_sheet(service: Any, spreadsheet_id: str) -> None:
    """
    Create a blank "Draft Picks" sheet for manual tracking.

    This sheet is positioned after the Summary sheet and is intended for
    manual data entry. It will be:
    - Skipped during normal updates (content preserved)
    - Cleared during force full updates (reset to blank)

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.

    Raises:
        SheetGenerationError: If sheet creation fails.
    """
    logger.info("Creating Draft Picks sheet...")

    try:
        # Create a new sheet for draft picks at position 1 (after Summary)
        requests = [{
            'addSheet': {
                'properties': {
                    'title': 'Draft Picks',
                    'index': 1  # Position after Summary (which is at index 0)
                }
            }
        }]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        logger.info("✓ Draft Picks sheet created (blank)")

    except Exception as e:
        error_msg = f"Failed to create Draft Picks sheet: {e}"
        logger.error(error_msg)
        raise SheetGenerationError(error_msg) from e


def create_team_sheet(service: Any, spreadsheet_id: str, team: Team) -> None:
    """
    Create a sheet for a team's roster.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        team: Team object with roster data.

    Raises:
        SheetGenerationError: If sheet creation fails.
    """
    logger.info(f"Creating sheet for team: {team.team_name}")

    try:
        # Create a new sheet for the team
        requests = [{
            'addSheet': {
                'properties': {
                    'title': team.team_name[:100]  # Google Sheets title limit
                }
            }
        }]

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

        # Generate team sheet data
        values = _create_team_sheet_data(team)

        # Calculate number of players for formatting
        sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

        # Write data to the sheet
        range_name = f"'{team.team_name[:100]}'!A1"
        body = {'values': values}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        # Format the team sheet
        num_players = len(sorted_roster)
        format_requests = _create_team_sheet_formatting(sheet_id, num_players)

        # Add protection if owner email is configured
        if Config.OWNER_EMAIL:
            logger.debug(f"Adding protection to team sheet '{team.team_name}' (owner: {Config.OWNER_EMAIL})")
            format_requests.append(_create_sheet_protection_request(sheet_id, team.team_name, Config.OWNER_EMAIL))

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': format_requests}
        ).execute()

        logger.info(f"✓ Team sheet created: {team.team_name}")

    except Exception as e:
        error_msg = f"Failed to create team sheet for {team.team_name}: {e}"
        logger.error(error_msg)
        raise SheetGenerationError(error_msg) from e


def generate_league_report(league: League, sheet_title: Optional[str] = None) -> str:
    """
    Generate a complete Google Sheets report for the fantasy basketball league.

    Creates a spreadsheet with:
    - Summary sheet with league statistics
    - Individual sheets for each team with roster details

    Args:
        league: League object with all team and player data.
        sheet_title: Optional custom spreadsheet title.
                    Default: "{league_name} - Rosters & Salaries"

    Returns:
        str: The Google Sheets URL for the created spreadsheet.

    Raises:
        SheetGenerationError: If report generation fails.
    """
    if sheet_title is None:
        sheet_title = f"{league.league_name} - Rosters & Salaries"

    logger.info("=" * 80)
    logger.info(f"Generating league report: {sheet_title}")
    logger.info("=" * 80)

    try:
        # Create the spreadsheet
        service, spreadsheet_id = create_spreadsheet(sheet_title)

        # Create summary sheet (replaces default Sheet1)
        create_summary_sheet(service, spreadsheet_id, league)

        # Create Draft Picks sheet (positioned after Summary)
        create_draft_picks_sheet(service, spreadsheet_id)

        # Create a sheet for each team
        sorted_teams = sorted(league.teams, key=lambda t: t.team_name)
        for team in sorted_teams:
            create_team_sheet(service, spreadsheet_id, team)

        # Generate spreadsheet URL
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        logger.info("=" * 80)
        logger.info("✓ League report generated successfully!")
        logger.info("=" * 80)
        logger.info(f"Spreadsheet URL: {sheet_url}")
        logger.info(f"Sheets created: 1 summary + 1 draft picks + {len(sorted_teams)} team sheets")
        stats = league.get_league_stats()
        logger.info(f"Total players: {stats['total_players']}")
        logger.info("=" * 80)

        return sheet_url

    except Exception as e:
        error_msg = f"Failed to generate league report: {e}"
        logger.error(error_msg)
        raise SheetGenerationError(error_msg) from e


if __name__ == "__main__":
    # Test sheet generation with mock data
    from src.data_models import Player, Team, League, SalarySource

    print("Testing sheet generation...")

    # Create sample data
    players = [
        Player("player1", "LeBron James", "SF", 63, SalarySource.KEEPER, "LAL"),
        Player("player2", "Stephen Curry", "PG", 45, SalarySource.DRAFT, "GSW"),
        Player("player3", "Giannis Antetokounmpo", "PF", 50, SalarySource.KEEPER, "MIL"),
        Player("player4", "Luka Doncic", "PG", 40, SalarySource.FAAB_WAIVER, "DAL"),
        Player("player5", "Nikola Jokic", "C", 55, SalarySource.KEEPER, "DEN"),
    ]

    team = Team(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Test Team",
        manager_name="Test Manager",
        roster=players,
        total_salary=253,
        faab_remaining=97
    )

    league = League(
        league_id="68958",
        league_key="466.l.68958",
        league_name="Test League",
        season="2025",
        num_teams=1,
        teams=[team]
    )

    try:
        url = generate_league_report(league)
        print(f"\n✓ Test spreadsheet created: {url}")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
