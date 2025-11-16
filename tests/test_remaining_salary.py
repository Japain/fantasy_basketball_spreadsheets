#!/usr/bin/env python3
"""
Quick test to verify the Remaining Salary feature works correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_models import Team, Player, SalarySource, create_team_from_yahoo_data
from config import config

def test_remaining_salary():
    """Test that remaining salary is calculated correctly."""

    print("Testing Remaining Salary Feature")
    print("=" * 60)

    # Test 1: Check config value
    print(f"\n1. Initial Auction Budget from config: ${config.INITIAL_AUCTION_BUDGET}")

    # Test 2: Create a team with some players
    players = [
        Player("p1", "LeBron James", "SF", 50, SalarySource.KEEPER, "LAL", "SF"),
        Player("p2", "Stephen Curry", "PG", 45, SalarySource.DRAFT, "GSW", "PG"),
        Player("p3", "Kevin Durant", "SF", 40, SalarySource.KEEPER, "PHX", "SF"),
        Player("p4", "Giannis Antetokounmpo", "PF", 55, SalarySource.DRAFT, "MIL", "PF"),
        Player("p5", "Joel Embiid", "C", 25, SalarySource.KEEPER, "PHI", "IL"),  # IL player
    ]

    team = create_team_from_yahoo_data(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Test Team",
        manager_name="Test Manager",
        faab_remaining=50,
        initial_budget=config.INITIAL_AUCTION_BUDGET
    )

    # Add players to team
    for player in players:
        team.add_player(player)

    print(f"\n2. Team: {team.team_name}")
    print(f"   Initial Budget: ${team.initial_budget}")
    print(f"   Players: {len(team.roster)}")
    print(f"   Total Salary (excluding IL): ${team.total_salary}")
    print(f"   Remaining Salary: ${team.get_remaining_salary()}")
    print(f"   FAAB Remaining: ${team.faab_remaining}")

    # Test 3: Verify calculation
    expected_total = 50 + 45 + 40 + 55  # Excluding IL player (25)
    expected_remaining = config.INITIAL_AUCTION_BUDGET - expected_total

    print(f"\n3. Verification:")
    print(f"   Expected Total Salary: ${expected_total}")
    print(f"   Actual Total Salary: ${team.total_salary}")
    print(f"   Expected Remaining: ${expected_remaining}")
    print(f"   Actual Remaining: ${team.get_remaining_salary()}")

    assert team.total_salary == expected_total, f"Total salary mismatch! Expected {expected_total}, got {team.total_salary}"
    assert team.get_remaining_salary() == expected_remaining, f"Remaining salary mismatch! Expected {expected_remaining}, got {team.get_remaining_salary()}"

    print("\n✓ All tests passed!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        test_remaining_salary()
        print("\n✓ Remaining Salary feature is working correctly!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
