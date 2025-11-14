"""Google Sheets generation module.

This module provides functions to create and format Google Sheets with league data,
including team rosters, player information, and salary details.
"""

from typing import List, Optional, Any
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.data_models import League, Team, Player
from src.google_auth import get_google_sheets_service

logger = get_logger(__name__)


class SheetGenerationError(Exception):
    """Exception raised for sheet generation errors."""
    pass


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

        # Prepare data for the summary sheet
        values = [
            [f"{league.league_name} - League Summary"],
            [],
            ["League Information"],
            ["Season", league.season],
            ["Number of Teams", league.num_teams],
            ["Total Players", stats['total_players']],
            ["Average Roster Size", f"{stats['avg_roster_size']:.1f}"],
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
            ["Team Name", "Manager", "Players", "Total Salary", "FAAB Remaining"],
        ]

        # Add team rows sorted by name
        for team in sorted(league.teams, key=lambda t: t.team_name):
            values.append([
                team.team_name,
                team.manager_name,
                len(team.roster),
                f"${team.total_salary}",
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
            # Format title (row 1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
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
            # Format section headers (rows 3, 9, 14, 19)
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
            # Format team table header (row 20)
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
                        'endIndex': 5
                    }
                }
            }
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        logger.info("✓ Summary sheet created and formatted")

    except Exception as e:
        error_msg = f"Failed to create summary sheet: {e}"
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

        # Prepare roster data
        values = [
            [f"{team.team_name} ({team.manager_name})"],
            [],
            ["Player Name", "Position", "NBA Team", "Salary", "Source"],
        ]

        # Sort roster by salary (descending)
        sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

        # Add player rows
        for player in sorted_roster:
            source_text = player.source.name.replace('_', ' ')
            values.append([
                player.name,
                player.position,
                player.nba_team or "",
                player.salary,
                source_text
            ])

        # Add summary rows
        values.append([])
        values.append(["TOTAL SALARY", "", "", team.total_salary, ""])
        values.append(["FAAB REMAINING", "", "", team.faab_remaining, ""])

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
        summary_row = num_players + 4  # Header + blank + table header + players + blank

        format_requests = [
            # Format title (row 1)
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
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
            # Format salary column as currency
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 3,
                        'endRowIndex': 3 + num_players,
                        'startColumnIndex': 3,
                        'endColumnIndex': 4
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
                        'endRowIndex': summary_row + 2
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
            # Format summary salary values as currency
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': summary_row,
                        'endRowIndex': summary_row + 2,
                        'startColumnIndex': 3,
                        'endColumnIndex': 4
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
            # Auto-resize columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 5
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
            }
        ]

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
        logger.info(f"Sheets created: 1 summary + {len(sorted_teams)} team sheets")
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
