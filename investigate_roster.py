#!/usr/bin/env python3
"""
Roster Investigation Script

Investigate how to properly access roster players and their salary information.
"""

from src.yahoo_data_fetcher import YahooDataFetcher
from src.logger import logger


def main():
    """Main investigation function."""
    print("=" * 80)
    print("  ROSTER & PLAYER SALARY INVESTIGATION")
    print("=" * 80)

    print("\nInitializing Yahoo API client...")
    fetcher = YahooDataFetcher(browser_callback=False)

    # Get teams
    print("\nFetching teams...")
    teams = fetcher.get_league_teams()
    print(f"Retrieved {len(teams)} teams")

    # Get first team
    first_team = teams[0]
    team_id = first_team.team_id if hasattr(first_team, 'team_id') else first_team.team_key
    team_name = first_team.name if hasattr(first_team, 'name') else "Unknown"

    print(f"\nExamining Team: {team_name} (ID: {team_id})")
    print(f"FAAB Balance: ${first_team.faab_balance if hasattr(first_team, 'faab_balance') else 'N/A'}")

    # Get roster
    print("\nFetching roster...")
    roster = fetcher.get_team_roster(team_id)

    print(f"Roster type: {type(roster)}")
    print(f"Roster attributes: {[attr for attr in dir(roster) if not attr.startswith('_')]}")

    # Access players correctly
    if hasattr(roster, 'players'):
        players = roster.players
        print(f"\nRoster has {len(players)} players")

        print("\n" + "=" * 80)
        print("  PLAYER DETAILS")
        print("=" * 80)

        for i, player in enumerate(players[:5], 1):  # First 5 players
            print(f"\n--- Player {i} ---")
            print(f"Type: {type(player)}")

            # Print player attributes
            attrs = [attr for attr in dir(player) if not attr.startswith('_') and not callable(getattr(player, attr, None))]
            print(f"Attributes: {', '.join(attrs[:20])}")  # First 20 attributes

            # Try to get key info
            name = getattr(player, 'name', None)
            if name:
                print(f"Name: {name.full if hasattr(name, 'full') else name}")

            player_key = getattr(player, 'player_key', 'Unknown')
            print(f"Player Key: {player_key}")

            # Check for position
            if hasattr(player, 'selected_position'):
                selected_position = player.selected_position
                print(f"Selected Position: {selected_position}")

            if hasattr(player, 'display_position'):
                print(f"Display Position: {player.display_position}")

            if hasattr(player, 'eligible_positions'):
                print(f"Eligible Positions: {player.eligible_positions}")

            if hasattr(player, 'primary_position'):
                print(f"Primary Position: {player.primary_position}")

            # Check for salary-related fields
            salary_fields = [
                'salary', 'cost', 'auction_price', 'draft_cost',
                'is_keeper', 'keeper_cost', 'contract'
            ]

            print("Salary-related fields:")
            for field in salary_fields:
                if hasattr(player, field):
                    value = getattr(player, field)
                    print(f"  {field}: {value}")

            # Check ownership
            if hasattr(player, 'ownership'):
                ownership = player.ownership
                print(f"Ownership type: {type(ownership)}")
                if hasattr(ownership, '__dict__'):
                    print(f"Ownership: {ownership.__dict__}")
                else:
                    print(f"Ownership attributes: {[attr for attr in dir(ownership) if not attr.startswith('_')]}")

    # Get draft results to create player_key -> cost mapping
    print("\n" + "=" * 80)
    print("  DRAFT RESULTS - COST MAPPING")
    print("=" * 80)

    draft_results = fetcher.get_league_draft_results()
    print(f"Total draft picks: {len(draft_results)}")

    # Create mapping
    player_cost_map = {}
    for result in draft_results:
        player_key = result.player_key
        cost = result.cost
        team_key = result.team_key
        player_cost_map[player_key] = {
            'cost': cost,
            'team_key': team_key,
            'pick': result.pick,
            'round': result.round
        }

    print("\nSample draft costs (first 10):")
    for i, (player_key, data) in enumerate(list(player_cost_map.items())[:10], 1):
        print(f"  {i}. {player_key}: ${data['cost']} (Pick {data['pick']}, Round {data['round']})")

    # Match roster players with draft costs
    print("\n" + "=" * 80)
    print("  ROSTER WITH SALARIES")
    print("=" * 80)

    if hasattr(roster, 'players'):
        print(f"\nTeam: {team_name}")
        print("-" * 80)

        total_salary = 0
        for player in roster.players:
            player_key = getattr(player, 'player_key', None)

            # Get player name
            name = "Unknown"
            if hasattr(player, 'name'):
                name_obj = player.name
                if hasattr(name_obj, 'full'):
                    name = name_obj.full
                elif hasattr(name_obj, 'ascii_full'):
                    name = name_obj.ascii_full

            # Get position
            position = getattr(player, 'display_position', getattr(player, 'primary_position', 'N/A'))

            # Get salary from draft results
            salary = "N/A"
            if player_key and player_key in player_cost_map:
                salary = f"${player_cost_map[player_key]['cost']}"
                total_salary += player_cost_map[player_key]['cost']

            # Check if keeper
            keeper_status = ""
            if hasattr(player, 'is_keeper'):
                keeper = player.is_keeper
                if isinstance(keeper, dict) and keeper.get('status'):
                    keeper_cost = keeper.get('cost')
                    if keeper_cost:
                        keeper_status = f" [KEEPER: ${keeper_cost}]"
                        salary = f"${keeper_cost}"
                        if player_key in player_cost_map:
                            total_salary = total_salary - player_cost_map[player_key]['cost'] + keeper_cost

            print(f"{name:30s} {position:10s} {salary:10s} {keeper_status}")

        print("-" * 80)
        print(f"{'TOTAL SALARY':41s} ${total_salary}")

        if hasattr(first_team, 'faab_balance'):
            print(f"{'FAAB Remaining':41s} ${first_team.faab_balance}")

    print("\n" + "=" * 80)
    print("Investigation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
