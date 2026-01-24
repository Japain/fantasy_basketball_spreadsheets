#!/usr/bin/env python3
"""
Investigate if Yahoo API provides team schedule information.
"""

from datetime import datetime, timezone
from src.yahoo_data_fetcher import create_fetcher
from config import Config

# Validate config
is_valid, errors = Config.validate()
if not is_valid:
    print("✗ Configuration validation failed:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# Create fetcher
fetcher = create_fetcher()

# Get league data to find a player
league_data = fetcher.extract_league_data()

# Find a benched player
test_player = None
for team in league_data.teams:
    for player in team.roster:
        if player.roster_position == "BN" and player.nba_team:
            test_player = player
            break
    if test_player:
        break

if not test_player:
    print("No benched players found")
    exit(1)

print(f"Test Player: {test_player.name}")
print(f"NBA Team: {test_player.nba_team}")
print(f"Player Key: {test_player.player_key}")
print("=" * 80)

today = datetime.now(timezone.utc)
check_date = today.strftime('%Y-%m-%d')

print(f"\nChecking data for date: {check_date}")
print("=" * 80)

# Get player stats
try:
    player_data = fetcher.yahoo_query.get_player_stats_by_date(
        test_player.player_key,
        chosen_date=check_date
    )

    print("\nAvailable attributes on player_data:")
    for attr in dir(player_data):
        if not attr.startswith('_'):
            print(f"  - {attr}")

    # Check player_stats
    if hasattr(player_data, 'player_stats'):
        print("\nplayer_stats attributes:")
        player_stats = player_data.player_stats
        for attr in dir(player_stats):
            if not attr.startswith('_'):
                value = getattr(player_stats, attr, None)
                print(f"  - {attr}: {value}")

    # Check for other useful attributes
    if hasattr(player_data, 'player_points'):
        print(f"\nplayer_points: {player_data.player_points}")

    if hasattr(player_data, 'player_key'):
        print(f"\nplayer_key: {player_data.player_key}")

    # Try to get player info (might have team schedule)
    print("\n" + "=" * 80)
    print("Trying get_player_stats (without date)...")
    print("=" * 80)

    player_info = fetcher.yahoo_query.get_player_stats(test_player.player_key)

    print("\nAvailable attributes on player_info:")
    for attr in dir(player_info):
        if not attr.startswith('_'):
            print(f"  - {attr}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
