#!/usr/bin/env python3
"""
Test script to verify IL/IL+ players are excluded from salary calculations.
"""

from src.data_models import (
    Player,
    Team,
    SalarySource,
    create_player_from_yahoo_data,
    create_team_from_yahoo_data
)


def test_il_exclusion():
    """Test that IL and IL+ players are excluded from total salary calculation."""
    print("Testing IL/IL+ player exclusion from salary calculation...\n")

    # Create a team
    team = create_team_from_yahoo_data(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Test Team",
        manager_name="Test Manager",
        faab_remaining=100
    )

    # Add regular players (should be counted)
    regular_player1 = create_player_from_yahoo_data(
        player_key="466.p.1",
        name="Regular Player 1",
        position="PG",
        salary=50,
        source=SalarySource.KEEPER,
        roster_position="PG"
    )
    team.add_player(regular_player1)

    regular_player2 = create_player_from_yahoo_data(
        player_key="466.p.2",
        name="Regular Player 2",
        position="SG",
        salary=40,
        source=SalarySource.DRAFT,
        roster_position="SG"
    )
    team.add_player(regular_player2)

    # Add bench player (should be counted)
    bench_player = create_player_from_yahoo_data(
        player_key="466.p.3",
        name="Bench Player",
        position="SF",
        salary=30,
        source=SalarySource.FAAB_WAIVER,
        roster_position="BN"
    )
    team.add_player(bench_player)

    # Add IL player (should NOT be counted)
    il_player = create_player_from_yahoo_data(
        player_key="466.p.4",
        name="Injured Player 1",
        position="PF",
        salary=25,
        source=SalarySource.KEEPER,
        roster_position="IL"
    )
    team.add_player(il_player)

    # Add IL+ player (should NOT be counted)
    il_plus_player = create_player_from_yahoo_data(
        player_key="466.p.5",
        name="Injured Player 2",
        position="C",
        salary=20,
        source=SalarySource.DRAFT,
        roster_position="IL+"
    )
    team.add_player(il_plus_player)

    # Calculate expected total (excluding IL and IL+ players)
    expected_total = 50 + 40 + 30  # = 120
    actual_total = team.total_salary

    # Print results
    print("Team Roster:")
    print("-" * 80)
    print(f"{'Player Name':<20} {'Position':<10} {'Roster Slot':<12} {'Salary':<10} {'Counted?'}")
    print("-" * 80)

    for player in team.roster:
        is_counted = player.roster_position not in ('IL', 'IL+')
        counted_str = "✓ Yes" if is_counted else "✗ No (IL)"
        print(
            f"{player.name:<20} {player.position:<10} {player.roster_position or 'N/A':<12} "
            f"${player.salary:<9} {counted_str}"
        )

    print("-" * 80)
    print(f"\nExpected Total Salary (excluding IL/IL+): ${expected_total}")
    print(f"Actual Total Salary:                      ${actual_total}")

    # Verify the calculation
    if actual_total == expected_total:
        print("\n✓ TEST PASSED: IL and IL+ players are correctly excluded from salary calculation!")
        return True
    else:
        print(f"\n✗ TEST FAILED: Expected ${expected_total}, but got ${actual_total}")
        return False


if __name__ == "__main__":
    success = test_il_exclusion()
    exit(0 if success else 1)
