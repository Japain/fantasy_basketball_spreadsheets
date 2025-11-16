#!/usr/bin/env python3
"""
Test script to demonstrate the roster position column in the output format.
"""

from src.data_models import (
    Player,
    Team,
    SalarySource,
    create_player_from_yahoo_data,
    create_team_from_yahoo_data
)


def test_roster_output():
    """Test the roster output format with roster position column."""
    print("Testing roster output format with roster position column...\n")

    # Create a team
    team = create_team_from_yahoo_data(
        team_id="1",
        team_key="466.l.68958.t.1",
        team_name="Sample Team",
        manager_name="John Doe",
        faab_remaining=150
    )

    # Add players with various roster positions
    players_data = [
        ("LeBron James", "SF,PF", 63, SalarySource.KEEPER, "LAL", "SF"),
        ("Stephen Curry", "PG", 55, SalarySource.DRAFT, "GSW", "PG"),
        ("Anthony Davis", "PF,C", 48, SalarySource.KEEPER, "LAL", "C"),
        ("Luka Doncic", "PG,SG", 45, SalarySource.DRAFT, "DAL", "G"),
        ("Kawhi Leonard", "SF,PF", 35, SalarySource.FAAB_WAIVER, "LAC", "BN"),
        ("Kevin Durant", "SF,PF", 30, SalarySource.KEEPER, "PHX", "Util"),
        ("Joel Embiid", "C", 25, SalarySource.DRAFT, "PHI", "IL"),
        ("Damian Lillard", "PG", 20, SalarySource.FAAB_WAIVER, "MIL", "IL+"),
    ]

    for name, position, salary, source, nba_team, roster_pos in players_data:
        player = create_player_from_yahoo_data(
            player_key=f"466.p.{len(team.roster)+1}",
            name=name,
            position=position,
            salary=salary,
            source=source,
            nba_team=nba_team,
            roster_position=roster_pos
        )
        team.add_player(player)

    # Sort roster by salary (descending) like the document generator does
    sorted_roster = sorted(team.roster, key=lambda p: p.salary, reverse=True)

    # Display the output format
    print(f"{team.team_name} ({team.manager_name})")
    print("-" * 70)
    print(f"{'Player Name':<30} {'Pos':<5} {'Slot':<6} {'Salary':>8} {'Source':<15}")
    print("-" * 70)

    for player in sorted_roster:
        source_text = player.source.name.replace('_', ' ')
        slot_text = player.roster_position or 'N/A'
        print(
            f"{player.name:<30} {player.position:<5} {slot_text:<6} ${player.salary:>7} {source_text:<15}"
        )

    print("-" * 70)
    print(f"{'TOTAL SALARY':<30} {'':<5} {'':<6} ${team.total_salary:>7}")
    print(f"{'FAAB REMAINING':<30} {'':<5} {'':<6} ${team.faab_remaining:>7}")

    # Show which players are excluded from total salary
    il_players = [p for p in team.roster if p.roster_position in ('IL', 'IL+')]
    active_salary = sum(p.salary for p in team.roster if p.roster_position not in ('IL', 'IL+'))

    print("\n" + "=" * 70)
    print("SALARY CALCULATION NOTES:")
    print("=" * 70)
    print(f"Active Players Salary (excluding IL/IL+): ${active_salary}")
    print(f"Total Salary (from calculate_total_salary): ${team.total_salary}")
    if il_players:
        print(f"\nPlayers on IL/IL+ (excluded from total):")
        for p in il_players:
            print(f"  - {p.name} ({p.roster_position}): ${p.salary}")
    print("=" * 70)


if __name__ == "__main__":
    test_roster_output()
