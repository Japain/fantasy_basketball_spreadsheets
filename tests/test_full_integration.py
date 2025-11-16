"""
Full integration test: Extract Yahoo data and generate Google Doc.

This script tests the complete flow:
1. Extract league data from Yahoo Fantasy API
2. Generate a Google Doc with all team rosters and salaries
"""

from src.yahoo_data_fetcher import YahooDataFetcher
from src.sheet_generator import generate_league_report
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run the full integration test."""
    print("=" * 80)
    print("FULL INTEGRATION TEST")
    print("=" * 80)
    print()

    # Step 1: Extract league data from Yahoo
    print("STEP 1: Extracting league data from Yahoo Fantasy API...")
    print("-" * 80)
    try:
        fetcher = YahooDataFetcher(browser_callback=False)
        league_data = fetcher.extract_league_data()

        print(f"✓ Successfully extracted league data")
        print(f"  League: {league_data.league_name}")
        print(f"  Season: {league_data.season}")
        print(f"  Teams: {league_data.num_teams}")
        print(f"  Total Players: {league_data.get_total_players()}")
        print()

        # Display team summary
        print("Team Summary:")
        print("-" * 80)
        for team in sorted(league_data.teams, key=lambda t: t.team_name):
            print(f"  {team.team_name} ({team.manager_name})")
            print(f"    Players: {len(team.roster)}, Salary: ${team.total_salary}, FAAB: ${team.faab_remaining}")
        print()

    except Exception as e:
        print(f"✗ Failed to extract league data: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Generate Google Sheet
    print("STEP 2: Generating Google Sheet report...")
    print("-" * 80)
    try:
        sheet_url = generate_league_report(league_data)

        print()
        print("=" * 80)
        print("✓ INTEGRATION TEST SUCCESSFUL!")
        print("=" * 80)
        print()
        print(f"Google Sheets URL: {sheet_url}")
        print()
        print("Summary:")
        print(f"  - {league_data.num_teams} teams processed")
        print(f"  - {league_data.get_total_players()} total players")
        stats = league_data.get_league_stats()
        print(f"  - ${stats['total_salary_spent']} total salary spent")
        print(f"  - ${stats['avg_salary_per_team']:.2f} average team salary")
        print()
        print("Open the URL above to view the generated report!")
        print("=" * 80)
        print()

        return True

    except Exception as e:
        print(f"✗ Failed to generate Google Sheet: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
