"""Simplified Google Docs document generation module.

This version uses a text-based approach for better reliability.
"""

from typing import List, Optional, Any
from googleapiclient.errors import HttpError

from src.logger import get_logger
from src.data_models import League, Team, Player
from src.google_auth import get_google_docs_service

logger = get_logger(__name__)


class DocumentGenerationError(Exception):
    """Exception raised for document generation errors."""
    pass


def generate_league_report(league: League, doc_title: Optional[str] = None) -> str:
    """
    Generate a complete Google Doc report for the fantasy basketball league.

    Creates a formatted document with league data using a simple text-based approach.

    Args:
        league: League object with all team and player data.
        doc_title: Optional custom document title.

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
        # Get service and create document
        service = get_google_docs_service()
        doc = service.documents().create(body={'title': doc_title}).execute()
        doc_id = doc.get('documentId')

        logger.info(f"✓ Document created. ID: {doc_id}")

        # Build the complete document content as text
        content_parts = []

        # Title and header
        content_parts.append(f"{league.league_name} - Rosters & Salaries")
        content_parts.append(f"Season {league.season} | {league.num_teams} Teams")
        content_parts.append("")

        # League statistics
        stats = league.get_league_stats()
        avg_player_salary = stats['total_salary_spent'] / stats['total_players'] if stats['total_players'] > 0 else 0
        content_parts.append("LEAGUE SUMMARY")
        content_parts.append("=" * 60)
        content_parts.append(f"Total Players: {stats['total_players']}")
        content_parts.append(f"Total Salary Spent: ${stats['total_salary_spent']}")
        content_parts.append(f"Average Team Salary: ${stats['avg_salary_per_team']:.2f}")
        content_parts.append(f"Average Player Salary: ${avg_player_salary:.2f}")
        content_parts.append("")
        content_parts.append("")

        # Sort teams by name
        sorted_teams = sorted(league.teams, key=lambda t: t.team_name)

        # Add each team
        for team_idx, team in enumerate(sorted_teams, 1):
            # Team header
            content_parts.append(f"{team_idx}. {team.team_name} ({team.manager_name})")
            content_parts.append("-" * 70)

            # Sort roster by salary (descending)
            sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

            # Create roster table as formatted text
            # Header row
            content_parts.append(f"{'Player Name':<30} {'Pos':<5} {'Slot':<6} {'Salary':>8} {'Source':<15}")
            content_parts.append("-" * 70)

            # Player rows
            for player in sorted_roster:
                source_text = player.source.name.replace('_', ' ')
                slot_text = player.roster_position or 'N/A'
                content_parts.append(
                    f"{player.name:<30} {player.position:<5} {slot_text:<6} ${player.salary:>7} {source_text:<15}"
                )

            # Summary rows
            content_parts.append("-" * 70)
            content_parts.append(f"{'TOTAL SALARY':<30} {'':<5} {'':<6} ${team.total_salary:>7}")
            content_parts.append(f"{'FAAB REMAINING':<30} {'':<5} {'':<6} ${team.faab_remaining:>7}")
            content_parts.append("")
            content_parts.append("")

        # Join all content
        full_content = "\n".join(content_parts)

        # Insert the content at the beginning of the document
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': full_content
            }
        }]

        # Apply formatting
        # Title (first line)
        title_end = len(content_parts[0]) + 1
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': 1, 'endIndex': title_end},
                'paragraphStyle': {
                    'namedStyleType': 'TITLE',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        })

        # Subtitle (second line)
        subtitle_start = title_end + 1
        subtitle_end = subtitle_start + len(content_parts[1]) + 1
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': subtitle_start, 'endIndex': subtitle_end},
                'paragraphStyle': {
                    'namedStyleType': 'SUBTITLE',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        })

        # Execute all requests
        service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

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

    except HttpError as e:
        error_msg = f"Failed to generate league report: {e}"
        logger.error(error_msg)
        raise DocumentGenerationError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to generate league report: {e}"
        logger.error(error_msg)
        raise DocumentGenerationError(error_msg) from e


if __name__ == "__main__":
    # Test document generation with mock data
    from src.data_models import Player, Team, League, SalarySource

    print("Testing simplified document generation...")

    # Create sample data
    players = [
        Player("player1", "LeBron James", "SF", 63, SalarySource.KEEPER, "LAL", "SF"),
        Player("player2", "Stephen Curry", "PG", 45, SalarySource.DRAFT, "GSW", "PG"),
        Player("player3", "Giannis Antetokounmpo", "PF", 50, SalarySource.KEEPER, "MIL", "PF"),
        Player("player4", "Luka Doncic", "PG", 40, SalarySource.FAAB_WAIVER, "DAL", "BN"),
        Player("player5", "Nikola Jokic", "C", 55, SalarySource.KEEPER, "DEN", "C"),
    ]

    # Create team properly
    team = Team(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Test Team",
        manager_name="Test Manager",
        roster=players,
        total_salary=253,
        faab_remaining=97
    )

    # Create league properly
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
        print(f"\n✓ Test document created: {url}")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
