#!/usr/bin/env python3
"""
Fantasy Basketball Roster & Salary Report Generator

Main application entry point. Extracts fantasy basketball league data from Yahoo
and generates a formatted Google Sheets report with team rosters and salaries.
"""

import argparse
import sys
from datetime import datetime

from config import Config
from src.logger import get_logger
from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_generator import generate_league_report

logger = get_logger(__name__)


def print_banner():
    """Print application banner."""
    print()
    print("=" * 80)
    print("Fantasy Basketball Roster & Salary Report Generator")
    print("=" * 80)
    print()


def print_summary(league_data):
    """Print summary of league data."""
    stats = league_data.get_league_stats()

    print()
    print("-" * 80)
    print(f"League: {league_data.league_name}")
    print(f"Season: {league_data.season}")
    print(f"Teams: {league_data.num_teams}")
    print(f"Total Players: {stats['total_players']}")
    print(f"Total Salary Spent: ${stats['total_salary_spent']}")
    print(f"Average Team Salary: ${stats['avg_salary_per_team']:.2f}")
    print(f"Average Roster Size: {stats['avg_roster_size']:.1f}")
    print("-" * 80)
    print()


def main():
    """Main application function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate a Google Sheets report for your fantasy basketball league"
    )
    parser.add_argument(
        '--league-id',
        help='Yahoo league ID (default: from .env NBA_LEAGUE_ID)',
        default=None
    )
    parser.add_argument(
        '--game-id',
        help='Yahoo game ID (default: from .env NBA_GAME_ID)',
        default=None
    )
    parser.add_argument(
        '--title',
        help='Custom spreadsheet title (default: "{League Name} - Rosters & Salaries")',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logger.setLevel('DEBUG')

    # Print banner
    print_banner()

    # Validate configuration
    print("Validating configuration...")
    is_valid, errors = Config.validate()
    if not is_valid:
        print("✗ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please check your .env file and ensure all required variables are set.")
        return 1

    print("✓ Configuration validated")
    print()

    # Step 1: Extract league data from Yahoo
    print("Step 1: Extracting league data from Yahoo Fantasy API...")
    print("-" * 80)
    try:
        fetcher = YahooDataFetcher(
            league_id=args.league_id,
            game_id=args.game_id,
            browser_callback=False
        )

        logger.info("Starting league data extraction...")
        league_data = fetcher.extract_league_data()

        print("✓ League data extracted successfully")
        print_summary(league_data)

    except Exception as e:
        print(f"✗ Failed to extract league data: {e}")
        logger.exception("League data extraction failed")
        return 1

    # Step 2: Generate Google Sheets report
    print("Step 2: Generating Google Sheets report...")
    print("-" * 80)
    try:
        logger.info("Starting spreadsheet generation...")
        sheet_url = generate_league_report(league_data, sheet_title=args.title)

        print("✓ Google Sheets generated successfully")
        print()

    except Exception as e:
        print(f"✗ Failed to generate Google Sheets: {e}")
        logger.exception("Spreadsheet generation failed")
        return 1

    # Print success message
    print("=" * 80)
    print("✓ SUCCESS! Report generated successfully")
    print("=" * 80)
    print()
    print(f"Spreadsheet URL: {sheet_url}")
    print()
    print("Summary:")
    print(f"  - {league_data.num_teams} teams processed")
    print(f"  - {league_data.get_total_players()} total players")
    stats = league_data.get_league_stats()
    print(f"  - ${stats['total_salary_spent']} total salary spent")
    print(f"  - ${stats['avg_salary_per_team']:.2f} average team salary")
    print()
    print("Open the URL above to view your league report!")
    print("=" * 80)
    print()

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
