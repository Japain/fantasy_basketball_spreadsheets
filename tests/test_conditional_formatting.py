#!/usr/bin/env python3
"""
Test conditional formatting for Remaining Salary in Google Sheets.

Creates a test spreadsheet with teams having both positive and negative
remaining salaries to verify the green/red highlighting works correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_models import Player, Team, League, SalarySource, create_league_from_yahoo_data, create_team_from_yahoo_data, create_player_from_yahoo_data
from src.sheet_generator import generate_league_report
from config import config

def create_test_league():
    """Create a test league with teams having different remaining salary scenarios."""

    # Create league
    league = create_league_from_yahoo_data(
        league_id="TEST123",
        league_key="466.l.TEST123",
        league_name="Conditional Formatting Test League",
        season="2025",
        num_teams=3
    )

    # Team 1: Positive remaining salary (should be GREEN)
    team1 = create_team_from_yahoo_data(
        team_id="1",
        team_key="466.l.TEST123.t.1",
        team_name="Team With Budget",
        manager_name="Green Manager",
        faab_remaining=100,
        initial_budget=config.INITIAL_AUCTION_BUDGET
    )
    # Add players totaling $150 (leaving $75 remaining)
    team1.add_player(create_player_from_yahoo_data(
        "p1", "LeBron James", "SF", 50, SalarySource.KEEPER, "LAL", "SF"
    ))
    team1.add_player(create_player_from_yahoo_data(
        "p2", "Stephen Curry", "PG", 45, SalarySource.DRAFT, "GSW", "PG"
    ))
    team1.add_player(create_player_from_yahoo_data(
        "p3", "Kevin Durant", "SF", 40, SalarySource.KEEPER, "PHX", "PF"
    ))
    team1.add_player(create_player_from_yahoo_data(
        "p4", "Giannis Antetokounmpo", "PF", 15, SalarySource.FAAB_WAIVER, "MIL", "BN"
    ))
    league.add_team(team1)

    # Team 2: Exactly $0 remaining (should be RED)
    team2 = create_team_from_yahoo_data(
        team_id="2",
        team_key="466.l.TEST123.t.2",
        team_name="Team At Limit",
        manager_name="Zero Manager",
        faab_remaining=50,
        initial_budget=config.INITIAL_AUCTION_BUDGET
    )
    # Add players totaling exactly $225 (leaving $0 remaining)
    team2.add_player(create_player_from_yahoo_data(
        "p5", "Joel Embiid", "C", 60, SalarySource.KEEPER, "PHI", "C"
    ))
    team2.add_player(create_player_from_yahoo_data(
        "p6", "Nikola Jokic", "C", 65, SalarySource.KEEPER, "DEN", "Util"
    ))
    team2.add_player(create_player_from_yahoo_data(
        "p7", "Luka Doncic", "PG", 55, SalarySource.DRAFT, "DAL", "PG"
    ))
    team2.add_player(create_player_from_yahoo_data(
        "p8", "Jayson Tatum", "SF", 45, SalarySource.DRAFT, "BOS", "SF"
    ))
    league.add_team(team2)

    # Team 3: Negative remaining salary (over budget, should be RED)
    team3 = create_team_from_yahoo_data(
        team_id="3",
        team_key="466.l.TEST123.t.3",
        team_name="Team Over Budget",
        manager_name="Red Manager",
        faab_remaining=25,
        initial_budget=config.INITIAL_AUCTION_BUDGET
    )
    # Add players totaling $240 (leaving -$15 remaining)
    team3.add_player(create_player_from_yahoo_data(
        "p9", "Damian Lillard", "PG", 50, SalarySource.KEEPER, "MIL", "PG"
    ))
    team3.add_player(create_player_from_yahoo_data(
        "p10", "Anthony Davis", "PF,C", 60, SalarySource.KEEPER, "LAL", "PF"
    ))
    team3.add_player(create_player_from_yahoo_data(
        "p11", "Devin Booker", "SG", 55, SalarySource.DRAFT, "PHX", "SG"
    ))
    team3.add_player(create_player_from_yahoo_data(
        "p12", "Kawhi Leonard", "SF", 50, SalarySource.DRAFT, "LAC", "SF"
    ))
    team3.add_player(create_player_from_yahoo_data(
        "p13", "Karl-Anthony Towns", "C", 25, SalarySource.FAAB_WAIVER, "NYK", "C"
    ))
    league.add_team(team3)

    return league

def main():
    """Generate test spreadsheet to verify conditional formatting."""

    print("=" * 70)
    print("TESTING CONDITIONAL FORMATTING FOR REMAINING SALARY")
    print("=" * 70)

    # Create test league
    league = create_test_league()

    print(f"\nTest League: {league.league_name}")
    print(f"Initial Budget: ${config.INITIAL_AUCTION_BUDGET}")
    print(f"\nTeams:")

    for team in league.teams:
        remaining = team.get_remaining_salary()
        status = "GREEN ✓" if remaining > 0 else "RED ✗"
        print(f"  {team.team_name}:")
        print(f"    Total Salary: ${team.total_salary}")
        print(f"    Remaining: ${remaining} ({status})")

    # Generate spreadsheet
    print(f"\nGenerating Google Sheets...")
    try:
        url = generate_league_report(league, sheet_title="Conditional Formatting Test")
        print("\n" + "=" * 70)
        print("✓ TEST SPREADSHEET CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nSpreadsheet URL: {url}")
        print("\nEXPECTED RESULTS:")
        print("  - 'Team With Budget': Remaining Salary should be GREEN ($75)")
        print("  - 'Team At Limit': Remaining Salary should be RED ($0)")
        print("  - 'Team Over Budget': Remaining Salary should be RED (-$15)")
        print("\nPlease open the spreadsheet and verify the colors!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Failed to generate spreadsheet: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
