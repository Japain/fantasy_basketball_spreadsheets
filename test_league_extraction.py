#!/usr/bin/env python3
"""
Test script to extract complete league data and validate it.

Outputs comprehensive results to league_extraction_results.txt for investigation.
"""

import json
from datetime import datetime
from src.yahoo_data_fetcher import YahooDataFetcher
from src.data_processor import (
    validate_league_data,
    get_league_summary,
    calculate_team_totals,
    sort_teams,
    sort_players,
    get_top_salaries,
    SortOrder
)
from src.logger import logger


def write_separator(f, title="", char="=", width=80):
    """Write a separator line to the file."""
    if title:
        f.write(f"\n{char * width}\n")
        f.write(f"{title.center(width)}\n")
        f.write(f"{char * width}\n")
    else:
        f.write(f"{char * width}\n")


def main():
    """Extract and validate league data, output results to file."""
    output_file = "league_extraction_results.txt"

    print(f"Starting league data extraction test...")
    print(f"Results will be written to: {output_file}")

    try:
        # Initialize data fetcher
        print("\n1. Initializing Yahoo Data Fetcher...")
        fetcher = YahooDataFetcher(browser_callback=False)

        # Extract complete league data
        print("2. Extracting complete league data (this may take a moment)...")
        league = fetcher.extract_league_data()

        print(f"   ✓ Extracted data for {len(league.teams)} teams")

        # Validate the data
        print("3. Validating league data...")
        validation_result = validate_league_data(league, strict=False)

        if validation_result['valid']:
            print("   ✓ Validation passed!")
        else:
            print(f"   ⚠ Validation found {len(validation_result['errors'])} error(s)")

        # Generate summary statistics
        print("4. Generating summary statistics...")
        summary = get_league_summary(league)

        # Sort teams by salary
        teams_by_salary = sort_teams(league.teams, by="salary", order=SortOrder.DESCENDING)

        # Get top salaries
        top_salaries = get_top_salaries(league, n=20)

        # Write results to file
        print(f"5. Writing results to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            write_separator(f, f"FANTASY BASKETBALL LEAGUE DATA EXTRACTION RESULTS")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"League: {league.league_name}\n")
            f.write(f"Season: {league.season}\n")

            # Validation Results
            write_separator(f, "VALIDATION RESULTS")
            f.write(f"Status: {'PASSED ✓' if validation_result['valid'] else 'FAILED ✗'}\n")
            f.write(f"Teams Found: {validation_result['num_teams']}\n")
            f.write(f"Total Players: {validation_result['total_players']}\n")

            if validation_result['errors']:
                f.write(f"\nErrors ({len(validation_result['errors'])}):\n")
                for error in validation_result['errors']:
                    f.write(f"  ✗ {error}\n")

            if validation_result['warnings']:
                f.write(f"\nWarnings ({len(validation_result['warnings'])}):\n")
                for warning in validation_result['warnings']:
                    f.write(f"  ⚠ {warning}\n")

            # League Summary Statistics
            write_separator(f, "LEAGUE SUMMARY STATISTICS")
            f.write(f"Number of Teams: {summary['league_info']['num_teams']}\n")
            f.write(f"Total Players: {summary['basic_stats']['total_players']}\n")
            f.write(f"Average Roster Size: {summary['basic_stats']['avg_roster_size']:.1f}\n")
            f.write(f"\nSalary Statistics:\n")
            f.write(f"  Total Salary Spent: ${summary['basic_stats']['total_salary_spent']}\n")
            f.write(f"  Average Per Team: ${summary['basic_stats']['avg_salary_per_team']:.2f}\n")
            f.write(f"  Min Team Salary: ${summary['team_salary_range']['min']}\n")
            f.write(f"  Max Team Salary: ${summary['team_salary_range']['max']}\n")
            f.write(f"  Player Salary Range: ${summary['salary_stats']['min']} - ${summary['salary_stats']['max']}\n")
            f.write(f"  Average Player Salary: ${summary['salary_stats']['avg']:.2f}\n")

            f.write(f"\nFAAB Statistics:\n")
            f.write(f"  Total FAAB Remaining: ${summary['basic_stats']['total_faab_remaining']}\n")
            f.write(f"  Average FAAB Remaining: ${summary['basic_stats']['avg_faab_remaining']:.2f}\n")

            f.write(f"\nPlayers by Acquisition Source:\n")
            for source, count in summary['players_by_source'].items():
                f.write(f"  {source}: {count}\n")

            # Top 20 Highest Salaries
            write_separator(f, "TOP 20 HIGHEST SALARIES")
            f.write(f"{'Rank':<6} {'Player Name':<25} {'Pos':<8} {'NBA Team':<8} {'Salary':<8} {'Source':<15} {'Fantasy Team':<20}\n")
            f.write("-" * 120 + "\n")
            for idx, player_info in enumerate(top_salaries, 1):
                f.write(
                    f"{idx:<6} "
                    f"{player_info['name']:<25} "
                    f"{player_info['position']:<8} "
                    f"{player_info['nba_team'] or 'N/A':<8} "
                    f"${player_info['salary']:<7} "
                    f"{player_info['source']:<15} "
                    f"{player_info['fantasy_team']:<20}\n"
                )

            # Detailed Team Rosters
            write_separator(f, "DETAILED TEAM ROSTERS (Sorted by Total Salary)")

            for rank, team in enumerate(teams_by_salary, 1):
                write_separator(f, "", char="-")
                f.write(f"\n#{rank} - {team.team_name}\n")
                f.write(f"Manager: {team.manager_name}\n")
                f.write(f"Total Salary: ${team.total_salary}\n")
                f.write(f"FAAB Remaining: ${team.faab_remaining}\n")
                f.write(f"Roster Size: {len(team.roster)}\n")

                # Team totals breakdown
                totals = calculate_team_totals(team)
                f.write(f"\nSalary Breakdown by Source:\n")
                for source, amount in totals['salary_by_source'].items():
                    count = totals['players_by_source'][source]
                    f.write(f"  {source}: ${amount} ({count} players)\n")

                # Sort players by salary for this team
                team_players = sort_players(team.roster, by="salary", order=SortOrder.DESCENDING)

                f.write(f"\nRoster:\n")
                f.write(f"  {'Player Name':<25} {'Pos':<8} {'NBA Team':<8} {'Salary':<8} {'Source':<15}\n")
                f.write("  " + "-" * 75 + "\n")

                for player in team_players:
                    f.write(
                        f"  {player.name:<25} "
                        f"{player.position:<8} "
                        f"{player.nba_team or 'N/A':<8} "
                        f"${player.salary:<7} "
                        f"{player.source.value:<15}\n"
                    )

            # Footer
            write_separator(f, "END OF REPORT")

        print(f"\n✓ Results successfully written to {output_file}")

        # Print summary to console
        print("\n" + "=" * 60)
        print("EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"League: {league.league_name}")
        print(f"Teams: {len(league.teams)}")
        print(f"Total Players: {summary['basic_stats']['total_players']}")
        print(f"Total Salary Spent: ${summary['basic_stats']['total_salary_spent']}")
        print(f"Validation: {'PASSED ✓' if validation_result['valid'] else 'FAILED ✗'}")

        if validation_result['errors']:
            print(f"\nErrors: {len(validation_result['errors'])}")
            for error in validation_result['errors'][:5]:  # Show first 5
                print(f"  ✗ {error}")

        if validation_result['warnings']:
            print(f"\nWarnings: {len(validation_result['warnings'])}")
            for warning in validation_result['warnings'][:5]:  # Show first 5
                print(f"  ⚠ {warning}")

        print("\n" + "=" * 60)
        print(f"Full details available in: {output_file}")
        print("=" * 60)

        return league

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n✗ Test failed with error: {e}")
        print(f"Check logs for details")
        raise


if __name__ == "__main__":
    main()
