"""Google Docs document generation module.

This module provides functions to create and format Google Docs with league data,
including team rosters, player information, and salary details.
"""

from typing import List, Dict, Any, Optional
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.data_models import League, Team, Player, SalarySource
from src.google_auth import get_google_docs_service

logger = get_logger(__name__)


class DocumentGenerationError(Exception):
    """Exception raised for document generation errors."""
    pass


def create_document(title: str) -> tuple[Any, str]:
    """
    Create a new Google Doc with the specified title.

    Args:
        title: The title for the new document.

    Returns:
        tuple: (service object, document_id)

    Raises:
        DocumentGenerationError: If document creation fails.
    """
    logger.info(f"Creating Google Doc: '{title}'")

    try:
        service = get_google_docs_service()

        # Create the document
        doc = service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')

        logger.info(f"✓ Document created successfully. ID: {doc_id}")
        logger.info(f"  URL: https://docs.google.com/document/d/{doc_id}/edit")

        return service, doc_id

    except HttpError as e:
        error_msg = f"Failed to create document: {e}"
        logger.error(error_msg)
        raise DocumentGenerationError(error_msg) from e


def batch_update(service: Any, doc_id: str, requests: List[Dict[str, Any]]) -> None:
    """
    Execute a batch update on a Google Doc.

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        requests: List of update requests to execute.

    Raises:
        DocumentGenerationError: If batch update fails.
    """
    if not requests:
        logger.debug("No requests to process in batch update")
        return

    try:
        logger.debug(f"Executing batch update with {len(requests)} requests")
        service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        logger.debug("✓ Batch update successful")

    except HttpError as e:
        error_msg = f"Batch update failed: {e}"
        logger.error(error_msg)
        raise DocumentGenerationError(error_msg) from e


def add_title(service: Any, doc_id: str, title_text: str, index: int = 1) -> int:
    """
    Add a formatted title to the document.

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        title_text: The title text.
        index: Position to insert the title (default: 1, start of document).

    Returns:
        int: The new index position after insertion.

    Raises:
        DocumentGenerationError: If title insertion fails.
    """
    logger.debug(f"Adding title: '{title_text}' at index {index}")

    requests = [
        # Insert the title text
        {
            'insertText': {
                'location': {'index': index},
                'text': title_text + '\n'
            }
        },
        # Format as heading 1
        {
            'updateParagraphStyle': {
                'range': {
                    'startIndex': index,
                    'endIndex': index + len(title_text) + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'TITLE',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        }
    ]

    batch_update(service, doc_id, requests)
    return index + len(title_text) + 1


def add_subtitle(service: Any, doc_id: str, subtitle_text: str, index: int) -> int:
    """
    Add a formatted subtitle to the document.

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        subtitle_text: The subtitle text.
        index: Position to insert the subtitle.

    Returns:
        int: The new index position after insertion.

    Raises:
        DocumentGenerationError: If subtitle insertion fails.
    """
    logger.debug(f"Adding subtitle: '{subtitle_text}' at index {index}")

    requests = [
        # Insert the subtitle text
        {
            'insertText': {
                'location': {'index': index},
                'text': subtitle_text + '\n'
            }
        },
        # Format as subtitle
        {
            'updateParagraphStyle': {
                'range': {
                    'startIndex': index,
                    'endIndex': index + len(subtitle_text) + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'SUBTITLE',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        }
    ]

    batch_update(service, doc_id, requests)
    return index + len(subtitle_text) + 1


def add_heading(service: Any, doc_id: str, heading_text: str, index: int, level: int = 1) -> int:
    """
    Add a formatted heading to the document.

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        heading_text: The heading text.
        index: Position to insert the heading.
        level: Heading level (1, 2, or 3).

    Returns:
        int: The new index position after insertion.

    Raises:
        DocumentGenerationError: If heading insertion fails.
    """
    style_map = {
        1: 'HEADING_1',
        2: 'HEADING_2',
        3: 'HEADING_3'
    }

    style = style_map.get(level, 'HEADING_1')
    logger.debug(f"Adding {style}: '{heading_text}' at index {index}")

    requests = [
        {
            'insertText': {
                'location': {'index': index},
                'text': heading_text + '\n'
            }
        },
        {
            'updateParagraphStyle': {
                'range': {
                    'startIndex': index,
                    'endIndex': index + len(heading_text) + 1
                },
                'paragraphStyle': {
                    'namedStyleType': style
                },
                'fields': 'namedStyleType'
            }
        }
    ]

    batch_update(service, doc_id, requests)
    return index + len(heading_text) + 1


def create_team_roster_table(service: Any, doc_id: str, team: Team, index: int) -> int:
    """
    Create a formatted table for a team's roster.

    Table structure:
    - Headers: Player Name | Position | Salary | Source
    - Player rows
    - Total salary row
    - FAAB remaining row

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        team: Team object with roster data.
        index: Position to insert the table.

    Returns:
        int: The new index position after insertion.

    Raises:
        DocumentGenerationError: If table creation fails.
    """
    logger.debug(f"Creating roster table for team: {team.team_name}")

    # Calculate table dimensions
    # Rows: 1 header + N players + 1 total + 1 FAAB = N + 3
    num_rows = len(team.roster) + 3
    num_cols = 4

    # Sort roster by salary (descending) for better readability
    sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

    requests = []

    # Insert the table
    requests.append({
        'insertTable': {
            'rows': num_rows,
            'columns': num_cols,
            'location': {'index': index}
        }
    })

    batch_update(service, doc_id, requests)

    # Now we need to populate the table
    # Get the document to find table start location
    doc = service.documents().get(documentId=doc_id).execute()

    # Find the table we just created (it should be at or near our index)
    table_start_index = None
    for element in doc.get('body', {}).get('content', []):
        if 'table' in element:
            # Check if this table is at our expected location
            start = element.get('startIndex', 0)
            if start >= index:
                table_start_index = start
                table = element['table']
                break

    if table_start_index is None:
        raise DocumentGenerationError("Failed to locate created table")

    # Build requests to populate table cells
    populate_requests = []

    # Helper to get cell start index
    def get_cell_index(row_idx: int, col_idx: int) -> int:
        """Calculate the text insertion index for a table cell."""
        cell = table['tableRows'][row_idx]['tableCells'][col_idx]
        # Content starts at startIndex + 1 (after cell marker)
        return cell['content'][0]['startIndex']

    # Row 0: Headers
    headers = ['Player Name', 'Position', 'Salary', 'Source']
    for col_idx, header in enumerate(headers):
        cell_idx = get_cell_index(0, col_idx)
        populate_requests.append({
            'insertText': {
                'location': {'index': cell_idx},
                'text': header
            }
        })
        # Bold the header
        populate_requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': cell_idx,
                    'endIndex': cell_idx + len(header)
                },
                'textStyle': {
                    'bold': True,
                    'fontSize': {'magnitude': 11, 'unit': 'PT'}
                },
                'fields': 'bold,fontSize'
            }
        })

    # Rows 1 to N: Player data
    for row_idx, player in enumerate(sorted_roster, start=1):
        # Column 0: Player Name
        cell_idx = get_cell_index(row_idx, 0)
        populate_requests.append({
            'insertText': {
                'location': {'index': cell_idx},
                'text': player.name
            }
        })

        # Column 1: Position
        cell_idx = get_cell_index(row_idx, 1)
        populate_requests.append({
            'insertText': {
                'location': {'index': cell_idx},
                'text': player.position
            }
        })

        # Column 2: Salary
        cell_idx = get_cell_index(row_idx, 2)
        salary_text = f"${player.salary}"
        populate_requests.append({
            'insertText': {
                'location': {'index': cell_idx},
                'text': salary_text
            }
        })

        # Column 3: Source
        cell_idx = get_cell_index(row_idx, 3)
        source_text = player.source.name.replace('_', ' ')
        populate_requests.append({
            'insertText': {
                'location': {'index': cell_idx},
                'text': source_text
            }
        })

    # Row N+1: Total Salary
    total_row_idx = len(sorted_roster) + 1
    cell_idx = get_cell_index(total_row_idx, 0)
    populate_requests.append({
        'insertText': {
            'location': {'index': cell_idx},
            'text': 'TOTAL SALARY'
        }
    })
    populate_requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': cell_idx,
                'endIndex': cell_idx + len('TOTAL SALARY')
            },
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    })

    cell_idx = get_cell_index(total_row_idx, 2)
    total_text = f"${team.total_salary}"
    populate_requests.append({
        'insertText': {
            'location': {'index': cell_idx},
            'text': total_text
        }
    })
    populate_requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': cell_idx,
                'endIndex': cell_idx + len(total_text)
            },
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    })

    # Row N+2: FAAB Remaining
    faab_row_idx = len(sorted_roster) + 2
    cell_idx = get_cell_index(faab_row_idx, 0)
    populate_requests.append({
        'insertText': {
            'location': {'index': cell_idx},
            'text': 'FAAB REMAINING'
        }
    })
    populate_requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': cell_idx,
                'endIndex': cell_idx + len('FAAB REMAINING')
            },
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    })

    cell_idx = get_cell_index(faab_row_idx, 2)
    faab_text = f"${team.faab_remaining}"
    populate_requests.append({
        'insertText': {
            'location': {'index': cell_idx},
            'text': faab_text
        }
    })
    populate_requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': cell_idx,
                'endIndex': cell_idx + len(faab_text)
            },
            'textStyle': {'bold': True},
            'fields': 'bold'
        }
    })

    # Execute all population requests
    batch_update(service, doc_id, populate_requests)

    # Calculate new index (after the table)
    # Table takes up considerable space, need to get updated document
    doc = service.documents().get(documentId=doc_id).execute()
    for element in doc.get('body', {}).get('content', []):
        if 'table' in element and element.get('startIndex') == table_start_index:
            return element.get('endIndex', index) + 1

    # Fallback: estimate based on table size
    return index + (num_rows * num_cols * 10) + 100


def add_team_section(service: Any, doc_id: str, team: Team, index: int) -> int:
    """
    Add a complete team section with heading and roster table.

    Args:
        service: Google Docs API service object.
        doc_id: The document ID.
        team: Team object with roster data.
        index: Position to insert the team section.

    Returns:
        int: The new index position after insertion.

    Raises:
        DocumentGenerationError: If section creation fails.
    """
    logger.info(f"Adding team section for: {team.team_name} ({team.manager_name})")

    # Add team heading
    heading_text = f"{team.team_name} ({team.manager_name})"
    index = add_heading(service, doc_id, heading_text, index, level=2)

    # Add roster table
    index = create_team_roster_table(service, doc_id, team, index)

    # Add spacing after table
    batch_update(service, doc_id, [{
        'insertText': {
            'location': {'index': index},
            'text': '\n'
        }
    }])

    return index + 1


def generate_league_report(league: League, doc_title: Optional[str] = None) -> str:
    """
    Generate a complete Google Doc report for the fantasy basketball league.

    Creates a formatted document with:
    - League title and metadata
    - Summary statistics
    - Team sections with roster tables for each team

    Args:
        league: League object with all team and player data.
        doc_title: Optional custom document title.
                  Default: "{league_name} - Rosters & Salaries"

    Returns:
        str: The Google Docs URL for the created document.

    Raises:
        DocumentGenerationError: If report generation fails.
    """
    if doc_title is None:
        doc_title = f"{league.league_name} - Rosters & Salaries"

    logger.info("=" * 80)
    logger.info(f"Generating league report: {doc_title}")
    logger.info("=" * 80)

    try:
        # Create the document
        service, doc_id = create_document(doc_title)

        # Starting index (after document title)
        index = 1

        # Add main title
        title_text = f"{league.league_name} - Rosters & Salaries"
        index = add_title(service, doc_id, title_text, index)

        # Add subtitle with season and metadata
        subtitle_text = f"Season {league.season} | {league.num_teams} Teams"
        index = add_subtitle(service, doc_id, subtitle_text, index)

        # Add summary statistics
        stats = league.get_league_stats()

        summary_text = (
            f"League Summary:\n"
            f"Total Players: {stats['total_players']}\n"
            f"Total Salary Spent: ${stats['total_salary']}\n"
            f"Average Team Salary: ${stats['avg_team_salary']:.2f}\n"
            f"Average Player Salary: ${stats['avg_player_salary']:.2f}\n\n"
        )

        batch_update(service, doc_id, [{
            'insertText': {
                'location': {'index': index},
                'text': summary_text
            }
        }])
        index += len(summary_text)

        # Sort teams by name for consistent ordering
        sorted_teams = sorted(league.teams, key=lambda t: t.team_name)

        # Add each team section
        for team in sorted_teams:
            index = add_team_section(service, doc_id, team, index)

        # Generate document URL
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        logger.info("=" * 80)
        logger.info("✓ League report generated successfully!")
        logger.info("=" * 80)
        logger.info(f"Document URL: {doc_url}")
        logger.info(f"Teams included: {len(sorted_teams)}")
        logger.info(f"Total players: {stats['total_players']}")
        logger.info("=" * 80)

        return doc_url

    except Exception as e:
        error_msg = f"Failed to generate league report: {e}"
        logger.error(error_msg)
        raise DocumentGenerationError(error_msg) from e


if __name__ == "__main__":
    # Test document generation with mock data
    from src.data_models import Player, Team, League, SalarySource

    print("Testing document generation...")

    # Create sample data
    players = [
        Player("player1", "LeBron James", "SF", 63, SalarySource.KEEPER, "LAL"),
        Player("player2", "Stephen Curry", "PG", 45, SalarySource.DRAFT, "GSW"),
        Player("player3", "Giannis Antetokounmpo", "PF", 50, SalarySource.KEEPER, "MIL"),
    ]

    team = Team("team1", "Test Team", "Test Manager", players, 158, 92)
    league = League("test_league", "Test League", "2025", 1, [team])

    try:
        url = generate_league_report(league)
        print(f"\n✓ Test document created: {url}")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
